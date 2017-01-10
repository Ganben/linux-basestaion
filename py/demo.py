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
import re
#from six.moves import input
#from ftplib import FTP
from func import *
from var import *
#import new dependencies
from depdata import *
from depconfig import *

import logging
from logging.handlers import TimedRotatingFileHandler
#logging.basicConfig(level=logging.DEBUG,
#	datefmt='%a, %d %b %Y %H:%M:%S',
#	format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
#	filename='demo.log',
#	filemode='w')

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
#console_formatter = logging.Formatter('%(name)-5s: %(levelname)-8s %(message)s')
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d %(name)s] - %(message)s')
log_formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d %(name)s] - %(message)s [%(process)d,%(thread)d:%(threadName)s]')
console.setFormatter(console_formatter)
logger = logging.getLogger('demo')
logger.addHandler(console)
#Rthandler = RotatingFileHandler('demo.log',maxBytes=10*1024*1024,backupCount=5)
Trthandler = TimedRotatingFileHandler(filename='demo',when='D',interval=1,backupCount=7)
Trthandler.suffix = "%Y-%m-%d"
#Trthandler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
Trthandler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}$")

Trthandler.setLevel(logging.INFO)
Trthandler.setFormatter(log_formatter)
logger.addHandler(Trthandler)
logger.setLevel(logging.DEBUG)

global stationAlias
global reconnect_count
global reconnect_count_mqtt
global lastDiscoveryTime
global stationMac 
global cameraReviewed 
global dataddd
global ifname
#global alarm_cache
#alarm_cache = {}
dataddd={}
cameraReviewed = False
threads=[]
threadID=1
ifname = get_ifname(MacFilter)
stationMac = get_mac_address(MacFilter,':')
positionQ= Queue.Queue(PositionQueueLength)
commandQ = Queue.Queue(CommandQueueLength)
callQ = Queue.Queue(CallQueueLength)

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
            print"socket reconnect:close error : %s " % (msg,)
            logger.debug("[reconnect]socket reconnect:close error : %s " % (msg,))
	    #logger.debug('
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((depHost,depPort))
        except socket.error as msg:
            #print(msg)
            print"socket reconnect error : %s " % (msg,)
            logger.debug("[reconnect]socket reconnect:connect error : %s " % (msg,))

def reconnect_mqtt():
	global reconnect_count_mqtt
	#global client
	global MQTTServer,MQTTPort,mqttClientKeepAliveTime
	reconnect_count_mqtt += 1
	if reconnect_count_mqtt >=3:
		reconnect_count_mqtt = 0
		try:
			client.disconnect()
		except Exception,e:
			print "mqtt reconnect:disconnect error :%s,%s " % (Exception,e)
			logger.debug("[reconnect_mqtt]mqtt reconnect:close error : %s " % (msg,))
		try:
			client.connect(MQTTServer,MQTTPort,mqttClientKeepAliveTime)
		except Exception,e:
			print "mqtt reconnect error :%s,%s " % (Exception,e)
			logger.debug("[reconnect_mqtt]mqtt reconnect:connect error : %s " % (msg,))
			return False
		else:
			return True

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
		local_ip = get_ip_address(ifname)
		hex_ip = ''.join([hex(int(i)).lstrip('0x').rjust(2,'0') for i in local_ip.split('.')])
		temp = 50
	
		if data['Manufacturer'].startswith(callFlag,6):
			callData=data
			callData['nursecall'] = True
			print "\033[1;31;40m%s\033[0m" % (json.dumps(callData,))
			try:
				client.publish(CALLTITLE,json.dumps(callData))
			except Exception,e:
				print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e))
				reconnect_mqtt()
			lastDiscoveryTime = time.time()
			return 0	
		elif data['Manufacturer'].startswith(outbodyFlag,6):
			outbodyData = data
			#client.publish(COMMONTITLE,json.dumps(outbodyData))
			try:
				client.publish(OUTBODYTITLE,json.dumps(outbodyData))
			
			except Exception,e:
				print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e))
				reconnect_mqtt()
			lastDiscoveryTime = time.time()
			return 0
		#change to send to mqtt immidiately
		#positionQ.put(json.dumps(data))
		try:
			client.publish(POSITIONTITLE,json.dumps(data))
		except Exception,e:
				print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[ScanDelegate.handleDiscovery]\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e))
				reconnect_mqtt()
		print "%s,%s:%s" % (MQTTServer,MQTTPort,json.dumps(data))
		logger.info("[ScanDelegate.handleDiscovery]published.%s,%s:%s" % (MQTTServer,MQTTPort,json.dumps(data)))
		lastDiscoveryTime = time.time()

def on_connect(client,userdata,flags,rc):
	client.subscribe(CMDTITLE)
	print("Connected with resut code " + str(rc))
	logger.info("[MqttClient.on_connect] Mqtt Connected with resut code " + str(rc))

def on_disconnect(client, userdata, rc):      
	print "Mqtt Disconnected..."
	logger.info("[MqttClient.on_disconnect]Mqtt Disconnected...")

def on_message(client,userdata,msg):
	print "\033[1;31;40m[get] topic %s , payload:%s\033[0m" % (msg.topic, str(msg.payload))
	logger.debug("[MqttClient.on_message]\033[1;31;40mget topic %s , payload:%s\033[0m" % (msg.topic, str(msg.payload)))
	if msg.topic == CMDTITLE:
		print "\033[1;31;40m[get] %s \033[0m" % (str(msg.payload),)
		logger.debug("[MqttClient.on_meesage]\033[1;31;40m runcmd2 going to deal with %s \033[0m" % (str(msg.payload),))
		runcmd2(str(msg.payload))

class MyListener(object):
	#    def remove_service(self, zeroconf, type, name):
	#	pass

	def add_service(self, zeroconf, type, name):
		global MQTTServer,MQTTPort,client
		info = zeroconf.get_service_info(type, name)
		#log sth
		logger.info("[MyListerner.add_service]Service %s added, service info: %s" % (name, info))
		if info.server 	!= MQTTServer or info.port != MQTTPort:
			#log sth
			print "\033[1;31;40m received new address from zeroconf so need to change to new mqtt server : %s:%s\033[0m" % (info.server,info.port)
			logger.info("[MyListener.add_service]\033[1;31;40m received new address from zeroconf so need to change to new mqtt server : %s:%s\033[0m" % (info.server,info.port))
			MQTTServer = info.server
			MQTTPort = info.port
			res = reconnect_mqtt()
			if res:
				logger.info('[MyListener.add_service]change to new mqtt server suc.')
				try:
					write_conf('MQTT','server',MQTTServer)
					write_conf('MQTT','port',MQTTPort)
				except Exception,e:
					logger.warning('[Mylistener.add_service]Failed to write mqtt new address back to conf file:%s,%s' % (MQTTServer,MQTTPort))
					print "\033[1;31;40m failed to write back new mqtt server : %s:%s\033[0m" % (Exception,e)
			else:
				logger.info('[MyListener.add_service]Failed to reconnect to new mqtt server:%s,%s'% (MQTTServer,MQTTPort))
				print "\033[1;31;40m failed to reconnect to new mqtt server : %s:%s\033[0m" % (Exception,e)
			
def runcmd2(data):
	
	#print "\033[0;32;40m runcmd2  \033[0m" 
	global MQTTServer,MQTTPort
	global cameraReviewed 
	global hasCamera
	#print "\033[0;32;40m looping in runcmd %s while \033[0m"  % (q,)
	print "\033[0;32;40m runcmd2 get %s \033[0m"  % (data,)
	if data.startswith('update'):
		print "\033[0;32;40mget cmd as %s \033[0m" % (data,)
		logger.info("[runcmd2]\033[0;32;40mget cmd as %s \033[0m" % (data,))
		#parse args update -f[filename]* -m[md5_sum]* -i[ip/domain] -p[port]*  -r[random range] -v[version]*
		ArgsDict = parseArgs2Dict(data.lstrip('update'))
		if (not ArgsDict.has_key('f')) or (ArgsDict.has_key('i') and (not ArgsDict.has_key('p'))) or (not ArgsDict.has_key('v')) or (not ArgsDict.has_key('m')):
			#shoule rase Exception ,return and exit
			#print "Error: lack some para"
			logger.warning('[runcmd2]update cmd lack some para: %s' % (data,))
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
				print "033[0;32;40m current version : %f, order version :%f\033[0m " % (version,float(ArgsDict['v']))
				logger.debug("[runcmd2]033[0;32;40m current version : %f, order version :%f\033[0m " % (version,float(ArgsDict['v'])))
		except Exception,e:
			print "\033[0;32;40m runcmd2 judging params get %s:%s\033[0m"  % (Exception,e)
			logger.warning('[runcmd2]judging params get %s:%s' % (Exception,e))
	else :
		try:
			cmd = json.loads(data)
		except Exception,e:
			#print "\033[0;32;40m runcmd2 cannot cover cmd %s to json\033[0m" % (data,)
			logger.warning('[runcmd2]cannot loads cmd to json:%s' % (data,))

		if cmd['cmd'] == 'capture' :
			print "\033[0;32;40m runcmd2 capture cmd2 received\033[0m"
			logger.debug('[runcmd2]received capture cmd:%s' % (data,))
			#get photo
			if cmd['ap'] == stationAlias :
				#print "\033[0;32;40m capture cmd2 received and going to capture\033[0m"
				logger.debug('[rumcmd2]demanded to capture')
				#print "\033[0;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV))
				logger.debug("\033[0;32;40m H:%s, %s ; V:%s, %s\033[0m" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV)))
				now = int(time.time())
				filename = '%s_%s.jpg' % (cmd['bracelet'],now)
				#take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
				#send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
				#if not cameraReviewed:
				#	cameraReviewed = True
				if hasCamera:
					print "\033[0;32;40m has Camera and going to capture:\033[0m"
					try:
						take_photo(filename,picUploadDir,picResolutionV,picResolutionH,cameraReviewed,hottime)
						#print "\033[0;32;40m Capture ? %s " % (re,)
					except Exception,e:
						print "\033[0;32;40m Capture get Exception:%s:%s\033[0m" % (Exception,e)
						logger.warning("[runcm2]Capture get Exception:%s:%s" % (Exception,e))
					else:
						#print "\033[0;32;40m Capture ? %s " % (re,)
						#if re:
						logger.debug("[runcmd2]take photo suc")
						if cmd.has_key('url'):
							res = send_photo_url(filename,picUploadDir,cmd['url'],now)	
							if res:
								logger.debug("[send_photo_url]suc")
							else:
								logger.debug("[send_photo_url]suc")
						else:
							res = send_photo(filename,picUploadDir,picUploadServer,picUploadPort,cmd['ap'],cmd['bracelet'],now)
							if res:
								logger.debug("[send_photo]suc")
							else:
								logger.debug("[send_photo]suc")
							
						print "\033[0;32;40msend_photo done\033[0m"
						if not cameraReviewed:
							cameraReviewed = True
				else:
					print "\033[0;32;40m no camera and ignore capture \033[0m"
					#log sth 
					#return sth to server?
					pass

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
		try:
			client.connect(self.server,self.port,self.alivetime)
		except Exception,e:
			#log sth
			print "\033[1;31;40mmqtt connect error (%s,%s) %s:%s\033[0m try reconnect" % (MQTTServer,MQTTPort,Exception,e)
			reconnect_mqtt()
		while True:
			try:
				client.loop(timeout=self.timeout)
			except Exception,e:
				#log sth
				print "\033[1;31;40mmqtt loop error (%s,%s) %s:%s\033[0m try reconnect" % (MQTTServer,MQTTPort,Exception,e)
				reconnect_mqtt()

		
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
		if has_camera():
			hasCamera = True
		else:
			hasCamera =False
		while True:
			nowtime = time.time()
			heartbeat = get_system_info()
			heartbeat['version'] = version
			heartbeat['bsid'] = stationAlias
			heartbeat['script_uptime'] = "%s mins" % (str(round((nowtime-starttime)/60.0,1)),)
			heartbeat['mac'] = stationMac
			heartbeat['ip'] =  get_ip_address(ifname)
			if not heartbeat.has_key('features'):
				heartbeat['features'] = []
			if hasCamera:
				heartbeat['features'].append('camera')
			try:
				client.publish(HEARTBEATTITLE,json.dumps(heartbeat))
				#print "\033[1;31;40mheartbeat  %s\033[0m" % (json.dumps(heartbeat),)
				logger.debug("[heartbeat]\033[1;31;40m%s\033[0m"% (json.dumps(heartbeat)),)
			except Exception,e:
				#print "\033[1;31;40mMqtt Exception:%s\033[0m" % (Exception,e)
				logger.warning("[heartbeat]\033[1;31;40mMqtt Exception:%s,%s\033[0m" % (json.dumps(heartbeat),))
				reconnect_mqtt()
			time.sleep(heartbeatSleeptime)
if __name__=='__main__':
	global starttime
	global hasCamera
	global reconnect_count_mqtt 

	reconnect_count_mqtt =0 
	#global mqttClientKeepAliveTime
	starttime=time.time()
	client = mqtt.Client(client_id=stationAlias,clean_session=False)
	thread1 = MqttClient(1,'thread1',on_connect,on_message,on_disconnect,MQTTServer,MQTTPort,mqttClientKeepAliveTime,mqttClientLoopSleepTime,mqttClientLoopTimeout)
	threads.append(thread1)
	thread4 = heartBeat(4,'thread4',heartbeatSleeptime)
	threads.append(thread4)
	for i in threads:
		i.setDaemon(True)
		i.start()
	#zeroconf : get new mqtt server if exists
	zeroconf = Zeroconf()
	listener = MyListener()
	browser = ServiceBrowser(zeroconf,"_mqtt._tcp.local.", listener)

	global lastDiscoveryTime
	global s

	dataddd = get_empty_datadict()
	s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	try:
		s.connect((depHost,depPort))
		s.setblocking(0)
	except socket.error as msg:
		#print "socket error:%s" % (msg,)
		logger.warning("[main]socket error %s" % (msg,))
	reconnect_count = 0

	lastDiscoveryTime=0
	try:
		callscanner = Scanner().withDelegate(ScanDelegate())
	except Exception,e:
		print "\033[0;32;40m main:BLEscanner init:%s,%s\033[0m"  % (Exception,e)
		logger.warning("[main] BLEScan init error:%s,%s " % (Exception,e))
	count =0
	
	while True:
		try:
			devices = callscanner.scan(scannerScanTime)
			logger.info("[main] log test")
		except Exception,e:
		#print e
			print "\033[0;32;40m main:callscanner:scan %s,%s\033[0m and going to sleep 5s and scan again"  % (Exception,e)
			logger.warning("[main]callscanner:scan %s,%s and going to sleep 5s and scan again" % (Exception,e))
			time.sleep(5)
