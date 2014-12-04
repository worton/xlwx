#!/usr/bin/python

from collections import deque
from math import exp, log, pow
import socket
import sys
import time, datetime
import urllib
import urllib2
import threading
import logging


logfile = '/var/log/wx.log'
HOST = 'squire.loopfree.net'
PORT = 4000
ELEVATION = 95.0
rtfreq = 10
softwaretype="AD6XL-WX-0.2"
#add this many mbar to baro raw reading
#barocal = 1.01
#barocal = 2.2
barocal = 2.9
debug = False

logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(message)s')
socket.setdefaulttimeout(rtfreq - 3)

url = 'http://weatherstation.wunderground.com/weatherstation/updateweatherstation.php'
urlrt = 'realtime=1&rtfreq=%d&softwaretype=%s' % (rtfreq, softwaretype)

class TimeAverager(object):
   def __init__(self, s):
      self.secondsToKeep = s
      self.data = deque()

   def AddSample(self, s):
      self.data.append((time.time(), s))

   def GetAvg(self):
      out = 0.0
      for (t, x) in self.data:
         out += x / float(len(self.data))
      return out

   def Age(self):
      if len(self.data):
         age = time.time() - self.data[0][0]
         if age > self.secondsToKeep:
            self.data.popleft()


class TimeCounter(object):
   def __init__(self, s):
      self.secondsToKeep = s
      self.data = deque()

   def AddSample(self, s):
      self.data.append((time.time(), s))

   def GetCount(self):
      "return count of entire history"
      out = 0
      for (t, x) in self.data:
         out += x
      return out

   def GetCountPastN(self, sec):
      "return count of past sec seconds"
      out = 0
      for (t, x) in self.data:
         if time.time() - t <= sec:
            out += x
      return out

   def GetCountSince(self, sincewhen):
      "return count since datetime sincewhen"
      out = 0
      for (t, x) in self.data:
         if datetime.datetime.fromtimestamp(t) >= sincewhen:
            out += x
      return out

   def Age(self):
      if len(self.data):
         age = time.time() - self.data[0][0]
         if age > self.secondsToKeep:
            self.data.popleft()
      

class WxState(object):
   def __init__(self):
      self.internalTemp  = TimeAverager(120)
      self.externalTemp1 = TimeAverager(120)
      self.externalTemp2 = TimeAverager(120)
      self.externalHum1 = TimeAverager(180)
      self.stnPress = TimeAverager(180)
      self.rain = TimeCounter(86400)

   def Age(self):
      self.internalTemp.Age()
      self.externalTemp1.Age()
      self.externalTemp2.Age()
      self.externalHum1.Age()
      self.stnPress.Age()
      self.rain.Age()


def handler(fh):
   fh.close()

t1 = 0.0
t2 = 0.0
t3 = 0.0
rain = 0
hum = 0.0
stnpress = 0.0

def C2F(c):
   return c * 9.0 / 5.0 + 32.0 

def station2sealevel(stnpress, elevation, temp):
   """convert station pressure to sea level pressure"""
   tempK = 273.15 + temp
   return  stnpress / exp(-elevation / (tempK * 29.263))

def station2sealevel2(stnpress, elevation, temp):
   """convert station pressure to sea level pressure, NOAA algorithm"""
   a = (pow(1013.25, 0.190284) * 0.0065) / 288.0
   b = elevation / pow(stnpress - 0.3, 0.190284)
   return (stnpress - 0.3) * pow(1.0 + (a * b), (1.0 / 0.190284))
   
def mb2hg(p):
   return p * 0.0295301

def dewpoint(rh, temp):
   a = 17.271
   b = 237.7
   top = b * (log(rh/100.0) + (a*temp) / (b+temp))
   bottom = a - log(rh/100.0) - (a*temp) / (b+temp)
   return top / bottom

try:
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error, msg:
   sys.stderr.write("[ERROR] %s\n" % msg[1])
   sys.exit(1)

try:
   sock.connect((HOST, PORT))
except socket.error, msg:
   sys.stderr.write("[ERROR] %s\n" % msg[1])
   sys.exit(2)

data = ""
line = ""
state = WxState()
lastupload = datetime.datetime.utcnow()

while 1:
   i = data.find("\n")
   while i == -1:
      data += sock.recv(64)
      i = data.find("\n")

   line = data[0:i]
   data = data[i+1:]

   

   #18.8,18.9,18.7,0,55.1,1009.853
   ready = False
   try:
      (t1, t2, t3, rain, hum, stnpress) = line.split(',')
      t1 = float(t1)
      t2 = float(t2)
      t3 = float(t3)
      rain = int(rain)
      hum = min(float(hum), 100.0)
      stnpress = float(stnpress) + barocal
      ready = True
      if debug:
         print line
   except:
      ready = False

#   if rain > 0:
#      print line

   if ready:
      now = datetime.datetime.utcnow()
      state.internalTemp.AddSample(t1)
      state.externalTemp1.AddSample(t2)
      state.externalTemp2.AddSample(t3)
      state.externalHum1.AddSample(hum)
      state.stnPress.AddSample(stnpress)
      state.rain.AddSample(int(rain))
      if debug:
         print C2F(state.internalTemp.GetAvg())
         print C2F(state.externalTemp1.GetAvg())
         print C2F(state.externalTemp2.GetAvg())
         print state.externalHum1.GetAvg()
         print state.stnPress.GetAvg()
         print station2sealevel(state.stnPress.GetAvg(), ELEVATION, state.internalTemp.GetAvg())
         print mb2hg(station2sealevel(state.stnPress.GetAvg(), ELEVATION, state.internalTemp.GetAvg()))
         print mb2hg(station2sealevel2(state.stnPress.GetAvg(), ELEVATION, state.internalTemp.GetAvg()))
     
#      if rain > 0:
#         print time.ctime()
#         print "rain600: %d" % state.rain.GetCountPastN(600)
#         print "rain3600: %d" % state.rain.GetCountPastN(3600)
#         print "rainall: %d" % state.rain.GetCount()
      rain = 0
      state.Age()


      if (now - lastupload).seconds >= rtfreq:
         midnight = datetime.datetime.combine(datetime.date.today(), datetime.time(0))
         sevenam = datetime.datetime.combine(datetime.date.today(), datetime.time(hour=7))

         timestr = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
#         url = URLBASE + "&dateutc=%s" % timestr
         urldata = 'action=updateraw&ID=KORALBAN28&PASSWORD=le0swu'
         urldata += "&dateutc="+ urllib.quote(timestr)
         urldata += "&baromin=%f" % mb2hg(station2sealevel(state.stnPress.GetAvg(), ELEVATION, state.internalTemp.GetAvg()))
         urldata += "&indoortempf=%f" % C2F(state.internalTemp.GetAvg())
         avgoutdoor = (state.externalTemp1.GetAvg() + state.externalTemp2.GetAvg()) / 2.0
         urldata += "&tempf=%f" % C2F(avgoutdoor)
         urldata += "&humidity=%f" % state.externalHum1.GetAvg()
         urldata += "&dewptf=%f" % C2F(dewpoint(state.externalHum1.GetAvg(), avgoutdoor))
         urldata += "&rainin=%f" % (float(state.rain.GetCountPastN(3600)) / 100.0)
         urldata += "&dailyrainin=%f" % (float(state.rain.GetCountSince(midnight)) / 100.0,)
         lastupload = now

         if debug:
            print url,urldata
         logging.info("tin:%f tout:%f h:%f dp:%f b:%f rhr:%f r24:%f rmidnight:%f" % (C2F(state.internalTemp.GetAvg()),\
                          C2F(avgoutdoor),\
                          state.externalHum1.GetAvg(),\
                          C2F(dewpoint(state.externalHum1.GetAvg(), avgoutdoor)),\
                          mb2hg(station2sealevel(state.stnPress.GetAvg(), ELEVATION, state.internalTemp.GetAvg())),\
                          (float(state.rain.GetCountPastN(3600)) / 100.0),  \
                          (float(state.rain.GetCount() / 100.0)),  \
                          (float(state.rain.GetCountSince(midnight) / 100.0)) ))
                      

         try:
            req = url + "?" + urlrt + urldata
            fh = urllib2.urlopen(req)
            timer = threading.Timer(rtfreq - 2, handler, [fh])
            timer.start()
            results = fh.read()
            timer.cancel()
         except urllib2.HTTPError, e:
            pass
#            sys.stderr.write("urllib2 HTTP error code:%s\n" % str(e.code))
         except urllib2.URLError, e:
            pass
#            sys.stderr.write("urllib2 URL error reason:%s\n" % str(e.reason))
#         except urllib2.HTTPException:
#            pass
#            sys.stderr.write("HTTPException\n")
         except:
            pass
#            sys.stderr.write("Upload failed\n")

sock.close()
sys.exit(0)
