#/usr/bin/python
# -*- coding: utf-8 -*-
import Queue,threading,signal,traceback,os
import time,sys,datetime
import paho.mqtt.client as mqtt
import random
import json
from bluepy.btle import Scanner,DefaultDelegate
import uuid
import socket
import fcntl
import struct
from zeroconf import ServiceBrowser, Zeroconf
import urllib 
import urllib2 
import requests
import picamera
import json
#from six.moves import input
#from ftplib import FTP
from func import *
from var import *
#import new dependencies
from depdata import *
from depconfig import *

import logging
from logging.handlers import RotatingFileHandler

global stationAlias
global reconnect_count
global lastDiscoveryTime
global stationMac 
global cameraReviewed 
global dataddd
#global alarm_cache
#alarm_cache = {}
dataddd={}
cameraReviewed = False
threads=[]
threadID=1
stationMac = get_mac_address()
positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
callQ = Queue.Queue(CallQueueLength)
print "\033[0;32;40m %d\033[0m" % (os.geteuid(),)

class Watcher:
    """this class solves two problems with multithreaded 
    programs in Python, (1) a signal might be delivered 
    to any thread (which is just a malfeature) and (2) if 
    the thread that gets the signal is waiting, the signal 
    is ignored (which is a bug). 
 
    The watcher is a concurrent process (not thread) that 
    waits for a signal and the process that contains the 
    threads.  See Appendix A of The Little Book of Semaphores. 
    http://greenteapress.com/semaphores/ """

    def __init__(self):
        """ Creates a child thread, which returns.  The parent 
            thread waits for a KeyboardInterrupt and then kills 
            the child thread. 
        """
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            # I put the capital B in KeyBoardInterrupt so I can  
            # tell when the Watcher gets the SIGINT  
            print 'KeyBoardInterrupt'
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError: pass


def reconnect():
    #count reconnect counts, if bigger than 200, do reconn
    global reconnect_count
    global s
    reconnect_count += 1
    if reconnect_count>= 3:
        reconnect_count = 0
        try:
            s.close()
        except socket.error as msg:
            print"reconnect error : %s " % (msg,)
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((depHost,depPort))
        except socket.error as msg:
            #print(msg)
            print"reconnect error : %s " % (msg,)

class ScanDelegate(DefaultDelegate):
        def __init__(self):
                DefaultDelegate.__init__(self)
	def handleDiscovery(self, dev, isNewDev, isNewData):
		global stationAlias,stationMac
		data = {}
		timestamp = time.time()
		global lastDiscoveryTime
		global s
                global dataddd  #assemble all data before the loop
		try:
			for (adtype,desc,value) in dev.getScanData():
				data[desc]=value
		except UnicodeDecodeError,e:
			pass
                ##::here is new processing using depdata.py codes;
                if (data.has_key('Manufacturer')) and ( manu_filter(data.get('Manufacturer')) ):
                    #if match the manufilter then start new processing:
                    #print('dev+1 %s' % dev.addr )
                    #u just want update minimum fresh data here
                    try:
                        #s.send(bytearray.fromhex('01ab02ab'))
                        dataddd['keyflag']=rawdata_translate(data['Manufacturer'])
                    #    if alarm_update(dev.addr.replace(':',''), dataddd['keyflag']):
                    #        dataddd['keyflag'] = KEY_BINDING
                    #ip need update
                    except:
                        print('dev+1 %s' % dev.addr )
                    if alarm_update(dev.addr.replace(':',''), dataddd['keyflag']):
                        dataddd['keyflag'] = KEY_BINDING
                    #local_ip = get_ip_address(depIfip)
                    #dataddd['ip'] = str(local_ip)
                    #dataddd['hexip'] = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
                    dataddd['bcaddr'] = dev.addr
                    dataddd['bcmac'] = dev.addr.replace(':','')
                    dataddd['rssi'] = hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0')
                    dataddd['srssi'] = dev.rssi*(-1)
                    ## data type 
                    if depProt == 'B':
                    #print('%s' % dataddd)
                        load = gen_bin_data(dataddd)
                    #print('%s' % dataddd)
                    else:
                        load = gen_json_data(dataddd)
                    ## send type
                    #if depNet == 'S':
                    try:
                        s.send(load)
                        print('all xxx sent %s' % load)
                    except socket.error as msg:
                        print('socket error %s' % msg)
                        reconnect()
                    ##Mqtt not processed

                ## below is old codes
                ## below is old codes
                ## below is old codes
                ## below is old codes
                ## below is old codes
		#print "%s，%s" % (data['Manufacturer'],braceletFlag)
		if (not data.has_key('Manufacturer')) or ( not data['Manufacturer'].startswith(braceletFlag)):
			return 0
		data['addr'] = dev.addr
		data['rssi'] = dev.rssi
		data['bsid'] = stationAlias
		data['stationMac'] = stationMac
		data['timestamp'] = timestamp
		data['bcid'] = int(data['Manufacturer'][8:16],16)
		data['data'] = data['Manufacturer'][4:]
		#battery+station ip
		#electricity = data['Manufacturer'][16:18]
		electricity = '64' #fixed
                flag = data['Manufacturer'][6:8]
		local_ip = get_ip_address('wlan0')
		hex_ip = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
		temp = 50
	
		#newdata = 'fefe%s%s%s%s%s%s%s' % (flag,stationMac,hex_ip,dev.addr.replace(':',''),hex(dev.rssi*(-1)).lstrip('0x').rjust(2,'0'),electricity,hex(temp).lstrip('0x').rjust(2,'0'))
		#BinData = bytearray.fromhex(newdata)
		#newBinData= BinData+checksum(BinData)
		#arrs=[]
                #for e in newBinData:
                #    arrs.append(str(e))
                    #arrs.append(str(struct.unpack('B', e[0])[0]))
                #print('-'.join(arrs))
                #newBinData = base64.b16decode(newdata)
		#print "send bin data: %s, last %s" % (newBinData,checksum(BinData))
		#send to where
                #try:
                    #re-use present socket link;
                    #rather than close and open a new socket;
                    #this is only happen every 50 fails 
                    #s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                    #s.connect((socketHost, socketPort))
                   # s.sendall(newBinData)
                  #  print('-'.join(arrs))
                    #s.close()
               # except socket.error as msg:
                    #s.close()
                #    global reconnect_count
                #    print('%s(%s)' % (msg, reconnect_count))
                #    reconnect()

		#rc = s.recv(1024)
		#print rc

		if data['Manufacturer'].startswith(callFlag,6):
			callData=data
			callData['nursecall'] = True
			print "\033[1;31;40m%s\033[0m" % (json.dumps(callData,))
			client.publish(CALLTITLE,json.dumps(callData))
			lastDiscoveryTime = time.time()
			return 0	
		elif data['Manufacturer'].startswith(outbodyFlag,6):
			outbodyData = data
			#client.publish(COMMONTITLE,json.dumps(outbodyData))
			client.publish(POSITIONTITLE,json.dumps(outbodyData))
			lastDiscoveryTime = time.time()
			return 0
		positionQ.put(json.dumps(data))
		print json.dumps(data)
		lastDiscoveryTime = time.time()

def on_connect(client,userdata,flags,rc):
	client.subscribe(CMDTITLE)
	print("Connected with resut code " + str(rc))

def on_disconnect(client, userdata, rc):      
	while rc != 0:
	 	sleep(2)
		print "Reconnecting..."
		rc = client.reconnect()

def on_message(client,userdata,msg):
	print "\033[1;31;40m[get] topic %s , payload:%s\033[0m" % (msg.topic, str(msg.payload))
	if msg.topic == CMDTITLE:
		print "\033[1;31;40m[get] %s \033[0m" % (str(msg.payload),)
		runcmd2(str(msg.payload))
		#commandQ.put(str(msg.payload))

class MyListener(object):
    def remove_service(self, zeroconf, type, name):
	#TODO:?
        #print("Service %s removed" % (name,))
	pass

    def add_service(self, zeroconf, type, name):
	global MQTTServer,MQTTPort,client
        info = zeroconf.get_service_info(type, name)
        #print("Service %s added, service info: %s" % (name, info))
	if info.server 	!= MQTTServer or info.port != MQTTPort:
		print "\033[1;31;40m change to new mqtt server : %s:%s\033[0m" % (info.server,info.port)
		MQTTServer = info.server
		MQTTPort = info.port
		client.disconnect()
		client.connect(MQTTServer,MQTTPort,mqttClientKeepAliveTime)
		#write back to conf file
		#write_conf('MQTT','server',MQTTServer)
		#write_conf('MQTT','port',MQTTPort)

class MqttSender(threading.Thread):
	def __init__(self,threadID,name,title,q,sleeptime):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q
		self.title = title
		self.sleeptime = sleeptime	
		
	def run(self):
		senddata(self.name,self.title,self.q,self.sleeptime)

class MqttListener(threading.Thread):
	def __init__(self,threadID,name,q):
		threading.Thread.__init__(self)
		self.threadID=threadID
		self.name=name
		self.q=q

	def run(self):
		#print('exec ... ' + self.name)
		runcmd(self.name,self.q)

def senddata(threadName,title,q,sleeptime):
	while True:
		while not q.empty():
			data = q.get()
			#print "\033[0;32;40m send data\033[0m"	
			client.publish(title,data)
			print "sended %s " % (data,)
		if sleeptime > 0:
			time.sleep(sleeptime)

def runcmd(threadName,q):
	
	print "\033[0;32;40m runcmd  \033[0m" 
	global MQTTServer,MQTTPort
	while True:
		print "\033[0;32;40m looping in runcmd %s while \033[0m"  % (q,)
		if not q.empty():
			data= q.get()
			print "\033[0;32;40m get %s from queue\033[0m"  % (data,)
			if data.startswith('update'):
				print "\033[0;32;40mget cmd as %s \033[0m" % (data,)
				#parse args update -f[filename]* -m[md5_sum]* -i[ip/domain] -p[port]*  -r[random range] -v[version]*
				ArgsDict = parseArgs2Dict(data.lstrip('update'))
				if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgsDict.has_key('v')) or (not ArgsDict.has_key('m')):
					#shoule rase Exception ,return and exit
					print "Error: lack some para"
					return 
				try:
					if float(ArgsDict['v']) > version:
						print "\033[0;32;40m new version upgrade command received \033[0m"
						if not ArgsDict.has_key('i'):
							ArgsDict['i'] = MQTTServer
						if not ArgsDict.has_key('p'):
							ArgsDict['p'] = 8000 
						if not ArgsDict.has_key('r'):
							ArgsDict['r'] = 600
						update_self(ArgsDict['f'],ArgsDict['m'],ArgsDict['v'],ArgsDict['i'],ArgsDict['p'],int(ArgsDict['r']))	
					else:
						#should log sth
						print "033[0;32;40m current version : %f, order version :%f\033[0m " % (version,ArgsDict['v'])
				except Exception,e:
					print "\033[0;32;40m get %s:%s\033[0m"  % (Exception,e)
			else :
				try:
					cmd = json.loads(data)
				except Exception,e:
					print "\033[0;32;40m cannot conver cmd %s to json\033[0m" % (data,)

				if cmd['cmd'] == 'capture' :
					print "\033[0;32;40m capture cmd received\033[0m"
					#get photo
					if cmd['ap'] == stationAlias :
						print "\033[0;32;40m capture cmd received and going to capture\033[0m"
						print "\033[0;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV))
						now = int(time.time())
						try:
							take_photo('tmp.jpg',picUploadDir,picResolutionV,picResolutionH,hottime)
						except Exception,e:
							print "\033[0;32;40m get %s:%s\033[0m" (Exception,e)
						else:
							send_photo('tmp.jpg',picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
		time.sleep(10.0)

def runcmd2(data):
	
	#print "\033[0;32;40m runcmd2  \033[0m" 
	global MQTTServer,MQTTPort
	global cameraReviewed 
	global hasCamera
	#print "\033[0;32;40m looping in runcmd %s while \033[0m"  % (q,)
	print "\033[0;32;40m runcmd2 get %s \033[0m"  % (data,)
	if data.startswith('update'):
		print "\033[0;32;40mget cmd as %s \033[0m" % (data,)
		#parse args update -f[filename]* -m[md5_sum]* -i[ip/domain] -p[port]*  -r[random range] -v[version]*
		ArgsDict = parseArgs2Dict(data.lstrip('update'))
		if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgsDict.has_key('v')) or (not ArgsDict.has_key('m')):
			#shoule rase Exception ,return and exit
			print "Error: lack some para"
			return 
		try:
			if float(ArgsDict['v']) > version:
				print "\033[0;32;40m new version upgrade command received \033[0m"
				if not ArgsDict.has_key('i'):
					ArgsDict['i'] = MQTTServer
				if not ArgsDict.has_key('p'):
					ArgsDict['p'] = 8000 
				if not ArgsDict.has_key('r'):
					ArgsDict['r'] = 600
				update_self(ArgsDict['f'],ArgsDict['m'],ArgsDict['v'],ArgsDict['i'],ArgsDict['p'],int(ArgsDict['r']))	
			else:
				#should log sth
				print "033[0;32;40m current version : %f, order version :%f\033[0m " % (version,float(ArgsDict['v']))
		except Exception,e:
			print "\033[0;32;40m get %s:%s\033[0m"  % (Exception,e)
	else :
		try:
			cmd = json.loads(data)
		except Exception,e:
			print "\033[0;32;40m cannot conver cmd %s to json\033[0m" % (data,)

		if cmd['cmd'] == 'capture' :
			print "\033[0;32;40m capture cmd2 received\033[0m"
			#get photo
			if cmd['ap'] == stationAlias :
				print "\033[0;32;40m capture cmd2 received and going to capture\033[0m"
				print "\033[0;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV))
				now = int(time.time())
				filename = '%s_%s.jpg' % (cmd['bracelet'],now)
				#take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
				#send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
				#if not cameraReviewed:
				#	cameraReviewed = True
				if hasCamera:
					try:
						take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
						#print "\033[0;32;40m Capture ? %s " % (re,)
					except Exception,e:
						print "\033[0;32;40m Capture get Exception:%s:%s\033[0m" % (Exception,e)
					else:
						#print "\033[0;32;40m Capture ? %s " % (re,)
						#if re:
						send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
						print "\033[0;32;40mtake_photo suc\033[0m"
						if not cameraReviewed:
							cameraReviewed = True
				else:
					#log sth 
					#return sth to server?
					pass

#def update_self(ip=MQTTServer,port=8000,ran=600,filename,md5_sum,version):
def update_self(filename,md5_sum,version,ip=MQTTServer,port=8000,ran=600):
	global stationAlias
	try:
		rdl = download(filename,md5_sum,ip,port,ran)
	except Exception,e:
		print "download got error : %s, %s " % (Exception,e)
		
	if rdl['status'] == 'OK':
		print "\033[0;32;40mDownload %s Successfully...\033[0m" % (filename,)
		rdp = deploy(filename)
		if rdp['status'] == 'OK':
			print "\033[0;32;40mDeploy Successfully...\nPreparing to remove the %s restart the program...\033[0m" % (filename,)
			if os.path.exists(filename):
				os.remove(filename)
			#write back the alias ID
			write_conf('station','alias',stationAlias)
			restart_raspi()
			#restart_program()
		else:
			#TODO
			#log sth
			pass
	else:
		#log sth
		#TODO
		pass

        #waittime = random.randrange(0,ran)
        #count = 5
	#suc = False
	##print "sleep %f seconds " % (waittime,)
        #time.sleep(waittime)
	##print "sleep done "
        #while not suc and count >= 0:
        #        try :
	#		#print "downloading..."
	#		url = 'http://%s:%s/%s' % (ip,port,filename)
        #                urllib.urlretrieve(url,filename)
	#		#print "set suc to True"
	#		suc = True
        #        except Exception,e:
        #                count-=1
	#		#print "Fail, sleep 10s and retry remain %d times" % (count,)			
	#		time.sleep(10)
	#if suc:			
	#	restart_program()
	#else:
	#	#log sth
	#	pass
			


class MqttClient(threading.Thread):
	def __init__(self,threadID,name,on_connect,on_message,on_disconnect,server,port,alivetime,sleeptime,timeout):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.on_message = on_message
		self.on_connect = on_connect
		self.on_disconnect = on_disconnect
		self.server = server
		self.port = port
		self.alivetime= alivetime 
		self.sleeptime = sleeptime
		self.timeout = timeout
	def run(self):
		global MQTTServer
		global MQTTPort
		client.on_connect = on_connect
		client.on_message = on_message
		client.connect(self.server,self.port,self.alivetime)
		#client.loop_forever(timeout=self.timeout)
		while True:
			#if MQTTServer != self.server or MQTTPort != self.port:
			#	disconnect()
			#	self.server = MQTTServer
			#	self.port = MQTTPort
			#	client.connect(self.server,self.port,self.alivetime)
			client.loop(timeout=self.timeout)
			#time.sleep(self.sleeptime)

		
class heartBeat(threading.Thread):
	def __init__(self,threadID,name,heartbeatSleeptime):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.heartbeatSleeptime = heartbeatSleeptime
	def run(self):
		global stationAlias
		global version
		global starttime
		global hasCamera
		heartbeat = get_system_info()
		heartbeat['version'] = version
		heartbeat['bsid'] = stationAlias
		if has_camera():
			if not heartbeat.has_key('features'):
				heartbeat['features'] = []
			heartbeat['features'].append('camera')
			hasCamera = True
		else:
			hasCamera =False
		while True:
			nowtime = time.time()
			heartbeat['script_uptime'] = "%s mins" % (str(round((nowtime-starttime)/60.0,1)),)
			client.publish(HEARTBEATTITLE,json.dumps(heartbeat))
			time.sleep(heartbeatSleeptime)
if __name__=='__main__':
	global starttime
	global hasCamera
	print "\033[0;32;40m %d\033[0m" % (os.geteuid(),)
	starttime=time.time()
	#Watcher()
	client = mqtt.Client(client_id=stationAlias,clean_session=False)
	thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
	#thread1.start()
	threads.append(thread1)
	#thread1.join()
	#thread2 = MqttListener(2,'command',commandQ)
	#thread2.start()
	thread3 = MqttSender(3,'thread3',POSITIONTITLE,positionQ,positionSenderSleeptime)
	#thread3.start()
	threads.append(thread3)
	thread4 = heartBeat(4,'thread4',heartbeatSleeptime)
	#thread4.start()
	threads.append(thread4)
	for i in threads:
		i.setDaemon(True)
		i.start()
	#listen to zeroconf to check if mqtt server change

	# just for debug
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf,"_mqtt._tcp.local.", listener)

	global lastDiscoveryTime
	global s

	print "\033[0;32;40mbefore socket\033[0m"

  dataddd = get_empty_datadict()
	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        try:
            s.connect((depHost,depPort))
            s.setblocking(0)
        except socket.error as msg:
	    print "socket error:%s" % (msg,)
            #print(msg)
	print "\033[0;32;40mafter socket\033[0m"
        reconnect_count = 0

	lastDiscoveryTime=0
	try:
		callscanner = Scanner().withDelegate(ScanDelegate())
	except Exception,e:
		print "\033[0;32;40m main:BLEscanner init:%s,%s\033[0m"  % (Exception,e)
	print "\033[0;32;40mafter callscanner\033[0m"
	count =0
	
	while True:
            try:
                devices = callscanner.scan(scannerScanTime)
		#now = time.time()
		#if now - lastDiscoveryTime  > 30 :
		#	result={"status":0,"bsid":stationAlias,"timestamp":now}
		#	print "send common: %s " % (json.dumps(result),)
		#	client.publish(COMMONTITLE,json.dumps(result))
		#	lastDiscoveryTime = now
            except Exception,e:
		#print e
		print "\033[0;32;40m main:callscanner:scan %s,%s\033[0m"  % (Exception,e)
                time.sleep(5)
