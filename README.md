# OLD_Datum9390_GPS_TSIP_Decoder
This program is a Python3 non-standard TSIP parser for serial RS-232 binaries captured from old (1990's) Datum9390-55058 Trimble GPS receiver.
Created this program because receiver does not fully work with Trimble TSIP Rev C and to practice writing binary parsing.

The run the program, use the console command: <b>'python3 tsipdecode.py tsip7.bin'</b>.
The other program datumserial.py reads directly from the serial port. Currently is it set up for 19200 baud with HW hand handshaking. 
The run this use <b>'python3 datumserial.py'.</b> 

The 'datumserial.py' was created using [Perplexity AI ver 3.20](https://www.perplexity.ai/) (https://www.perplexity.ai), accessed on March 11, 2025.

This software is GPL3.0 free to use as-is.

Example serial capture:
```
Report Packet: 0x46: Health Packet: Status Code=0x9, Description=Only 1 usable satellite
Report Packet: 0x4B: Machine/Code ID and Additional Status Report
  Machine ID: 0X19
  Status Flags:
    Battery-powered time clock fault: No
    Acknowledged status: No
    TSIP Superpackets fault: No
    Receiver reset fault: No
    Almanac fault: No
    A-to-D converter fault: No
Report Packet: 0x47: Signal Levels Packet: Number of Satellites=8
  SV PRN=20, Signal Level=-4.09
  SV PRN=13, Signal Level=-4.12
  SV PRN=29, Signal Level=10.20
  SV PRN=11, Signal Level=-3.50
  SV PRN=30, Signal Level=-0.00
  SV PRN=15, Signal Level=4.31
  SV PRN=5, Signal Level=-3.90
  SV PRN=18, Signal Level=-0.00
Report Packet: 0x46: Health Packet: Status Code=0x9, Description=Only 1 usable satellite
Report Packet: 0x4B: Machine/Code ID and Additional Status Report
  Machine ID: 0X19
  Status Flags:
    Battery-powered time clock fault: No
    Acknowledged status: No
    TSIP Superpackets fault: No
    Receiver reset fault: No
    Almanac fault: No
    A-to-D converter fault: No
Report Packet: 0x41: GPS Time
  Time of Week: 437496.031 seconds
  Extended GPS Week: 2357
  UTC Offset: 1.7165681980224717e-39 seconds
  Current UTC Time: 2025-03-14 01:31:36.031250
Report Packet: 0x41: GPS Time
  Time of Week: 437497.688 seconds
  Extended GPS Week: 2357
  UTC Offset: 1.7165681980224717e-39 seconds
  Current UTC Time: 2025-03-14 01:31:37.687500

Enjoy,

James 
