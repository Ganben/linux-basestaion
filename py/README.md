# basestation ble scanner

[参考地址](http://www.orangenarwhals.com/2014/06/bluetooth-low-energy-4-0-on-ubuntu-13-10-advertisements-sending-and-receiving/)

### 程序设计：

- 初始化
	初始化mqtt client；连接本地网关服务器；注册自己的基站编号为alias；
	1. 通过简单服务发现，自动配置mqtt，如果没有发现则不启动mqtt；实现：zeroconf
	2. 自动获取自身MAC和IP，并且发送到预先配置的Socket地址；
	3. 如果出错，重试一段时间后重连；若mqtt和btle任一进程卡死/退出，重试一段时间后重启。
	4. 连上mqtt后发送心跳包；并收取服务器响应包；若响应包版本号更高，采用默认配置更新文件。若监听到升级指令，则从升级指令中读取升级命令。
	5. 配置文件可用sender = S/M 分别代表socket和mqtt
	6. 配置文件用data = B/JS/JM 分别代表BINARY包和JSON4HSKCD和我方JSON
	7. 部署配置文件包括socket地址、默认mqtt地址、报文格式等用于配置的参数。其更新方式，是将整个文件整体更新至服务器ftp目录。
	8. 性能配置文件包括原配置文件的性能配置项。
	9. 分为基础版基站和拍照扩展基站；

- 注册监听事件；
	1. 开启扫描，关闭扫描，
	2. 程序更新，服务器心跳包监听
	3. 拍照基站的拍照监听；

- 开启下列循环：

	1. 扫描ble数据广播包；
	2. 组装数据：为：基站号：手环号：RSSI：手环状态；
	3. 判断是否报警包；
	4. 发送至网关服务器；（同安卓基站的逻辑）

> 在循环中可以通过远程发送命令消息来跳出循环。暂时没做

- 根据广播服务来热切换mqtt 服务器
- 自我更新
需要在监听的mqtt的指令频道发送update命令
```shell
update -i10.8.47.5 -p8000 -m%s -fupgrade.tar -v1.0 -r10
```
- -i:IP
- -p:端口
需要在此服务器，放置更新文件的目录开启http服务
```shell
#mac 调试时使用，仅供参考
sudo apachectl start
python -m SimpleHTTPServer
```
- -m:文件md5值
- -f:tar文件，目前仅支持tar文件部署
- -v:version版本号，基站会和本地t.cnf的文件内的版本号对比，比当前版本新才会执行更新
- -r:随机睡眠时间，缺省为600s

### 环境和依赖：

对Raspberry Pi 3基站来说，安装[blueZ](http://www.bluez.org/download/)，libbluetooth-dev：

	sudo apt-get install libbluetooth-dev
Picamera 模块（Pi Ubuntu Mate 16.04已预装）

安装bluepy
```shell
#python-pip if neccesssary↓
sudo apt-get install python-pip libglib2.0-dev
$ sudo apt-get install git build-essential libglib2.0-dev
$ git clone https://github.com/IanHarvey/bluepy.git
$ cd bluepy
$ python setup.py build
$ python setup.py install
```
安装mqtt client和paho-mqtt
```shell
sudo apt install mosquitto-clients
sudo pip install paho-mqtt #--trusted-host http://pypi.douban.com/
```
安装zeroconf
```shell
sudo pip install zeroconf
```
### OS config

- sudo NOPASSWORD配置便于sudo脚本
- 系统eth0命名的修改地址：
```sudo vi /lib/udev/rules.d/73-usb-net-by-mac.rules
NAME="$env{ID_NET_MAC} -> NAME="eth0"```
- 