import numpy as np
import pandas as pd
import struct
import sys
#filename = 'tsip10.bin'   #holder for test file
if __name__ == "__main__":
    filename = str(sys.argv[1])  # example until message line argv is working
rdata = open(filename , 'rb')

data = np.fromfile(rdata, dtype=np.uint8)


size = data.size
#print(size)

for index in range(size-1): 
    idata = struct.unpack('>H', data[index+0:index+2]) 
    
    if idata == (4180,) :
        #Report Packet 0x54
        #One Satellite Bias and Bias Rate Report

    #if idata == struct.unpack('>H', data[0+0:0+2]) :    
        offset=index + 2
        satmeters= struct.unpack('>f', data[offset+0:offset+4])
        satmeterssecond = struct.unpack('>f', data[offset+4:offset+8])
        seconds = struct.unpack('>f', data[offset+8:offset+12])
        #print('satmeters=%s'%satmeters,',satmeterssecond=%s'%satmeterssecond,',seconds=%s'%seconds)
        print('0x54,','%x'%index,',Bias,%s'%satmeters,',Bias Rate,%s'%satmeterssecond,',GPS(Seconds),%s'%seconds)
    if idata == (4165,):
        #Report Packet 0x45
        #Receiver Firmware Information Report
        offset=index + 2
        print('0x45,','%x '%index,end='')
        NAVProcMajor = struct.unpack('>c', data[offset+0])
        NAVProcMinor = struct.unpack('>c', data[offset+1])
        NAVProcMonth = struct.unpack('>c', data[offset+2])
        NAVProcDay = struct.unpack('>c', data[offset+3])
        NAVProcYear = struct.unpack('>c', data[offset+4])
        SIGProcMajor = struct.unpack('>c', data[offset+5])
        SIGProcMinor = struct.unpack('>c', data[offset+6])
        SIGProcMonth = struct.unpack('>c', data[offset+7])
        SIGProcDay = struct.unpack('>c', data[offset+8])
        SIGProcYear = struct.unpack('>c', data[offset+9])   
        print(',NAVProc',ord(NAVProcMajor[0]),'.',ord(NAVProcMinor[0]),'Date',ord(NAVProcMonth[0]),'/',ord(NAVProcDay[0]),'/',ord(NAVProcYear[0]),',SIG Proc',ord(SIGProcMajor[0]),'.',ord(SIGProcMinor[0]),'Date',ord(SIGProcMonth[0]),'/',ord(SIGProcDay[0]),'/',ord(SIGProcYear[0])) 
    
    
    if idata == (4166,):
        #Report Packet 0x46
        #Health of Receiver Report
        offset=index + 2
        statuscode= struct.unpack('>c', data[offset+0])
        errorcode = struct.unpack('>c', data[offset+1])
        print('0x46,','%x ,'%index,end='')
        if ord(statuscode[0])==0x00:
            print('statuscode:',hex(ord(statuscode[0])),'Doing position fixes',end='')
        if ord(statuscode[0])==0x01:
            print('statuscode:',hex(ord(statuscode[0])),'Do not have GPS time yet',end='')
        if ord(statuscode[0])==0x02:
            print('statuscode:',hex(ord(statuscode[0])),'Reserved:set to zero',end='')
        if ord(statuscode[0])==0x03:
            print('statuscode:',hex(ord(statuscode[0])),'PDOP is too high',end='')
        if ord(statuscode[0])==0x08:
            print('statuscode:',hex(ord(statuscode[0])),'No usable satellites',end='')
        if ord(statuscode[0])==0x09:
            print('statuscode:',hex(ord(statuscode[0])),'Only 1 usable satellite',end='')
        if ord(statuscode[0])==0x10:
            print('statuscode:',hex(ord(statuscode[0])),'Only 2 usable satellites',end='')    
        if ord(statuscode[0])==0x11:
            print('statuscode:',hex(ord(statuscode[0])),'Only 3 usable satellites',end='')
        if ord(statuscode[0])==0x12:
            print('statuscode:',hex(ord(statuscode[0])),'The chosen satellite is unusable',end='')    
        print(' errorcode:',hex(ord(errorcode[0])))    
            
        #    %s'%statuscode,',%b'%errorcode)
    if idata == (4171,):
        #Report Packet 0x4B
        #Machine / Code ID and Additional Status Report
        #Byte
        # 0 Machine ID     BYTE varies Machine ID for receiver. Values are listed in the product-specific appendices.
        # 1 Status Flags 1 Byte 1 Bit Encoding, Status 1 Flag
        # 2 Status Flags 2 Byte 2 Bit Encoding, Status 2 Flag
        offset=index + 2
        machineID= struct.unpack('>c', data[offset+0])
        statusflag1 = struct.unpack('>c', data[offset+1])
        statusflag2 = struct.unpack('>c', data[offset+2])
        print('0x4B,','%x'%index,', Machine ID:',hex(ord(machineID[0])),',statusflag1:',hex(ord(statusflag1[0])),',statusflag2:',hex(ord(statusflag2[0])))
    if idata == (4164,):
        #Report Packet 0x44
        #Non-Overdetermined Satellite Selection Report
        #Table 3-10
        # Byte #  Item Type   Value/Units  Meaning
        # 0   Mode     BYTE   flag Non-overdetermined mode:
        # 1-4 4SV#s    BYTE
        # 5-8 PDOP     SINGLE PDOP Precision Dilution of Precision
        # 9-12HDOP     SINGLE HDOP Horizontal Dilution of Precision
        # 13-16VDOP    SINGLE VDOP Vertical Dilution of Precision
        # 17-20TDOP    SINGLE TDOP Time Dilution of Precision
        
        offset=index + 2
        mode= struct.unpack('>c', data[offset+0])
        SV1 = struct.unpack('>c', data[offset+1])
        SV2 = struct.unpack('>c', data[offset+2])
        SV3 = struct.unpack('>c', data[offset+3])
        SV4 = struct.unpack('>c', data[offset+4])
        PDOP = struct.unpack('>f', data[offset+4:offset+8])
        HDOP = struct.unpack('>f', data[offset+8:offset+12])
        VDOP = struct.unpack('>f', data[offset+12:offset+16])
        TDOP = struct.unpack('>f', data[offset+17:offset+21])
        statusflag2 = struct.unpack('>c', data[offset+1])
        print('0x44,','%x ,'%index, end='')
        if ord(mode[0])==0x01:
              print(' Mode',hex(ord(mode[0])),',Auto 1-satellite, 0D', end='')
        if ord(mode[0])==0x03:
              print(' Mode',hex(ord(mode[0])),',Auto 3-satellite, 2D', end='')
        if ord(mode[0])==0x04:
              print(' Mode',hex(ord(mode[0])),',Auto 4-satellite, 3D', end='')
        if ord(mode[0])==0x11:
              print(' Mode',hex(ord(mode[0])),',Manual 1-satellite, 0D', end='')
        if ord(mode[0])==0x13:
              print(' Mode',hex(ord(mode[0])),',Manual 3-satellite, 2D', end='')
        if ord(mode[0])==0x14:
              print(' Mode',hex(ord(mode[0])),',Manual 4-satellite, 3D', end='')
                
        print(',SV1:',ord(SV1[0]),',SV2:',ord(SV2[0]),',SV3:',ord(SV3[0]),',SV4:',ord(SV4[0]),end='') 
        print(',PDOP:','%s'%PDOP,',HDOP:%s'%HDOP,',VDOP:%s'%VDOP,',TDOP:%s'%TDOP)
        #print('0x44,','%x'%index,'%s'%mode,',%s'%SV1,',%s'%SV2,',%s'%SV3,',%s'%SV4)
    if idata == (4161,):
        #Table 3-6
        #GPS Time
        #Byte #ItemTypeValue/UnitsMeaning
        #0-3TimeSINGLEsecondsGPS time of week
        #4-5WeekINTEGERweeksGPS week number
        #6-9OffsetSINGLEsecondsUTC/GPS time offset
        offset=index + 2
        seconds = struct.unpack('>f', data[offset+0:offset+4])
        week = struct.unpack('>H', data[offset+4:offset+6])
        #GPS Week mod1024 offset
        week=week[0] % 1024
        offset = struct.unpack('>f', data[offset+7:offset+11])
        print('0x41,','%x'%index,',','Seconds,%s'%seconds,',GPSWeek,%d'%week,',Offset_Sec:,%s'%offset)    
    if idata == (4187,): 
        #Report Packet 0x5B
        #Satellite Ephemeris Status Report
        offset=index + 2
        SVPRN = struct.unpack('>c', data[offset+0])
        CollectionTime = struct.unpack('>f', data[offset+1:offset+5])
        Health = struct.unpack('>c', data[offset+5])
        IODE = struct.unpack('>c', data[offset+6])
        toe = struct.unpack('>f', data[offset+7:offset+11])
        FITFLAG = struct.unpack('>c', data[offset+11])
        URA = struct.unpack('>f', data[offset+12:offset+16])
        print('0x5B,','%x'%index,', SVPRN:',ord(SVPRN[0]),'CollectionTime:%s'%CollectionTime,',health:',hex(ord(Health[0])),'IODE:',hex(ord(IODE[0])),'toe:%s'%toe,'FITFLAG:',hex(ord(FITFLAG[0])),'URA:%s'%URA)
        
    if idata == (4208,):
        #Report 0x70 does not match Reference C doc
        offset=index + 2
        whatever = struct.unpack('>q', data[offset+0:offset+8])
        whatever1 = struct.unpack('>h', data[offset+8:offset+10])
        print('0x70, %x'%index,',unknown0x70',hex(whatever[0]),hex(whatever1[0]))
