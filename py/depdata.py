#! /usr/bin/python
# -*- coding: utf-8 -*-

import uuid, time, socket, fcntl
from protobuilder import outputbuilder
from func import *
from var import *
from depconfig import *
#for json type data use : inbetween
#::predefined values::
BCTYPE00 = 'b00' 
BCTYPE01 = 'b01'
#static value of bracelet type
KEY_HEARTBEAT = '01'
KEY_ALARM = '02'
KEY_BINDING = '03'
KEY_LOST = '04'
#static value 4 bracelet state, from proto document
global alarm_cache
alarm_cache = {}

def get_empty_datadict():
    #datadict={keyflag, bsmac, hexip, bcmac, rssi, battery, temp, reserve}
    datadict={}
    datadict['keyflag'] = KEY_HEARTBEAT
    #datadict['bsmac'] = get_mac_address()
    datadict['bsmac'] = get_mac_address(MacFilter)
    #ipname = '%s%s' % (depIfip, get_mac_address())
    ipname = '%s%s' % (depIfip, get_mac_address(MacFilter))
    datadict['ip'] = get_ip_address(ipname)
    
    local_ip = get_ip_address(ipname)
    datadict['hexip'] = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
    datadict['bcmac'] = '010000000000'  #null bc mac;
    datadict['rssi'] = '63' #-99 predefined
    datadict['srssi'] = 99 #99 in int
    datadict['battery'] = '64' #battery level=100
    datadict['temp']= '23' #hex temp 0 -50/ 0x23 = 35/5 = 7
    datadict['reserved'] = '000000000000' #predefined fixed reserved bytes
    #datadict['bsmacfull'] = get_mac_address_full()
    datadict['bsmacfull'] = get_mac_address(MacFilter,':')
    datadict['bcaddr'] = '01:00:00:00:00:00' #predefined null bcaddr for json
    print('datadict built %s' % datadict )
    return datadict

def get_mac_address_full():
    mac=uuid.UUID(int = uuid.getnode()).hex[-12:]
    return ':'.join([mac[e:e+2] for e in range(0,11,2)])

#for bc1.0 count conseq alarm times4 binding flag
def alarm_update(bcid, flag):
    global alarm_cache
#    global position_cache
    #position cache for time, alarm cache for counts for each bcid
    bc = str(bcid)
    f= flag
    if alarm_cache.get(bc) == None:
        alarm_cache[bc] = 0
    #print('alarm_update init')
    if f == KEY_HEARTBEAT:
        try:
            alarm_cache[bc]=0
        except:
            print('cache error')
            return False
        return False
    elif f == KEY_ALARM and alarm_cache[bc] >=3 :
        alarm_cache[bc]=0
        print('binding triggered')
        return True
    elif f == KEY_ALARM and alarm_cache[bc] < 3:
        try:
            alarm_cache[bc] += 1
        except:
            print('cache error')
            return False
        #print('alarmtimes=%s' % alarm_cache[bc])
        return False
    return False

def rawdata_translate(manufdata):
    #this is 4 raw data collect and return a expected data prot
    #as demanded type
    flagdict = {}
    bctype = manu_filter(manufdata)
    if bctype == BCTYPE00:
        keyflag = manufdata[6:8]
        if keyflag == '13':
            flagdict['key'] = KEY_HEARTBEAT
        elif keyflag == '66':
            flagdict['key'] = KEY_ALARM
        elif keyflag == '68':
            flagdict['key'] = KEY_LOST
        elif keyflag == '70':
            flagdict['key'] = KEY_BINDING
        #the alarm update count in later 
    elif bctype == BCTYPE01:
        statflag = manufdata[6:8]
        keyflag = manufdata[8:10]
        if keyflag == '80':
            flagdict['key'] = KEY_ALARM
        elif keyflag == '00' and statflag == '14' :
            flagdict['key'] = KEY_LOST
        else:
            flagdict['key'] = KEY_HEARTBEAT            
    else:
        
        return '01'
    #the alarm update count in later phase
    print('raw translate %s' % flagdict['key'])
    return flagdict['key'] #use plain value

def gen_bin_data(datadict):
    #this generate same bin data type 4 two bc adv version
    #datadict={keyflag, bsmac, hexip, bcmac, rssi, battery, temp, reserve}
    #return 0xfefe____________________________ (checksum)
    #return bytearray.fromhex('ffff01ff01ff')
    try:
        hexdata = 'fefe%s%s%s%s%s%s%s%s' % (datadict['keyflag'], datadict['bsmac'], datadict['hexip'], datadict['bcmac'], datadict['rssi'], datadict['battery'], datadict['temp'], datadict['reserved'])
        bindata = bytearray.fromhex(hexdata)
    except:
        print('bindata = %s' % datadict)
        return bytearray.fromhex('20222733')

    return bindata  + checksum(bindata[2::])

def gen_json_data(datadict):
    #this generate same json data type 4 two bc adv version
    ssdata = outputbuilder(datadict['keyflag'], datadict['bsmacfull'], datadict['bcaddr'], 100, datadict['ip'], datadict['srssi'])

    return ssdata

def manu_filter(manudatabin):
    ##filter only start with 00ff12 4#bc1.0
    ##filter only start with 01ff12 4#sbc1.21
    if manudatabin == None:
        return False

    if manudatabin.startswith('00ff12'):
        return BCTYPE00
    #if matches, return bcmanu = b00/b01
    elif manudatabin.startswith('01ff12'):
        return BCTYPE01
    else:
        return False #if not matches supported bc adv packet

