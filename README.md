
accuracy
DS1822 2C
DS18B20 0.5C
DS18S20 0.5C
DS1821  1C


I have 
20
20
22
22
B20
B20

bought 5
S20


1820:
R=10 D6 4E 36 0 8 0 F1 P=1 2A 0 4B 46 FF FF 10 10 B4  CRC=B4

18B20's:
R=28 EC 35 31 00 00 00 DB Device is not a DS18S20 family device.
R=28 06 DF 30 00 00 00 D5 Device is not a DS18S20 family device.

10:D6:4E:36:00:08:00:F1:
28:EC:35:31:00:00:00:DB:
28:06:DF:30:00:00:00:D5:


DeviceAddress t1 = { 0x10, 0xD6, 0x4E, 0x36, 0x00, 0x08, 0x00, 0xF1 };
DeviceAddress t2 = { 0x28, 0xEC, 0x35, 0x31, 0x00, 0x00, 0x00, 0xDB };
DeviceAddress t3 = { 0x28, 0x06, 0xDF, 0x30, 0x00, 0x00, 0x00, 0xD5 };



pressure transfer code
Serial.println(pres);
Vout = vs * (.009 * P - .095)
vout/vs =  .009 P - .095
vout/vs + .095 = .009P
P = (vout/vs + .095) / .009


RH transfer
VOUT=(VSUPPLY)(0.00636(sensor RH) + 0.1515)
VOUT=(1024)(0.00636(x) + 0.1515)
x = (analogread/1024 - 0.1515 ) / 0.00636 


1-wire addresses in remote1
DeviceAddress t[] = {{ 0x10,0x57,0xE3,0x3B,0x02,0x08,0x00,0x21 },\
                     { 0x10,0xDF,0xC5,0x3B,0x02,0x08,0x00,0x0E }};


  // PRESSURE
  // get pres in hpa, average 10 samples from each of 2 sensors
  pres  = (analogReadAvg(0,10)/1024.0 + 0.095 ) / 0.0009 / 2.0;
  pres += (analogReadAvg(1,10)/1024.0 + 0.095 ) / 0.0009 / 2.0;
  // print absolute pressure
  Serial.print(pres,3);
//  Serial.print(",");
  // convert station pressure to sea level pressure, assume 20C temp
//  float tempK = 273.15 + 22.0;  // K, FIXME use onboard temp
//  pres = pres / exp(-elevation / (tempK * 29.263));
//  Serial.print(pres);
//  Serial.print(",");
   //convert mb to inches Hg
//  pres *= 0.0295301;
//  Serial.print(pres);
   


KORALBAN28





