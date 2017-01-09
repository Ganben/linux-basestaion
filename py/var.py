#! /usr/bin/python
import ConfigParser
import os,sys
from func import cur_file_dir
#def cur_file_dir():
#     path = sys.path[0]
#     if os.path.isdir(path):
#         return path
#     elif os.path.isfile(path):
#         return os.path.dirname(path)
conf = ConfigParser.ConfigParser()
conf.read('%s/%s'% (cur_file_dir(),'t.cnf'))
version = round(float(conf.get('station','version')),1)
MacFilter = conf.get('station','mac_filter')

POSITIONTITLE = conf.get("MQTT","position_t")
CMDTITLE = conf.get("MQTT","cmd_t")
CALLTITLE = conf.get("MQTT","call_t")
COMMONTITLE = conf.get("MQTT","common_t")
OUTBODYTITLE = conf.get('MQTT','outbody_t')
HEARTBEATTITLE = conf.get("MQTT","heartbeat_t")
PositionQueueLength = int(conf.get("queue",'position_l'))
CommandQueueLength = int(conf.get("queue",'cmd_l'))
CallQueueLength = int(conf.get("queue","call_l"))
#global MQTTserver
#global MQTTPort
MQTTServer = conf.get('MQTT','server')
if conf.has_option('MQTT','port'):
	MQTTPort = int(conf.get('MQTT','port'))
else:
	MQTTPort = 1883

stationAlias=conf.get('station','alias')
mqttClientKeepAliveTime = int(conf.get('time','thread_mqtt_keepalive_time'))
mqttClientLoopSleepTime = float(conf.get('time','thread_mqtt_loop_sleeptime'))
mqttClientLoopTimeout = float(conf.get('time','thread_mqtt_loop_timeout'))
heartbeatSleeptime = float(conf.get('time','thread_heartbeat_sleeptime'))
cmdSleepTime = float(conf.get('time','thread_cmd_sleep_time'))
positionSenderSleeptime = float(conf.get('time','thread_mqtt_sender_position_sleeptime'))
scannerScanTime = float(conf.get('time','main_scanner_scantime'))
callFlag= conf.get('BLE','call_manufacturer_flag')
braceletFlag= conf.get('BLE','bracetlet_flag')
outbodyFlag = conf.get('BLE','outbody_manufacturer_flag')
positionFlag= conf.get('BLE','position_manufacturer_flag')
socketHost = conf.get('SOCKET','host')
socketPort = int(conf.get('SOCKET','port'))
if conf.has_option('camera','resolution_h'):
	picResolutionH = int(conf.get('camera','resolution_h'))
else:
	picResolutionH = 1600
if conf.has_option('camera','resolution_v'):
	picResolutionV = int(conf.get('camera','resolution_v'))
else:
	picResolutionH = 1200
print "H:%s, %s ; V:%s, %s" % (picResolutionH,type(picResolutionH),picResolutionV,type(picResolutionV))
picUploadServer = conf.get('camera','upload_host')
picUploadPort = conf.get('camera','upload_port')
picUploadDir = conf.get('camera','tmp_dir')
hottime = float(conf.get('camera','hottime'))
#def write_conf(node,key,value):
#	try:
#		fh = open('t.cnf','w')
#		conf.set(node,key,value)
#		conf.write(fh)
#	except:
#		#log sth
#		return False
#	else:
#		return True
#	finally:
#		fh.close()
		
