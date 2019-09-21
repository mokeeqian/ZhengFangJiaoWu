## 正方教务管理系统爬虫-V2.1
登录系统，抓取学生课表、考试安排、选课情况信息、培养计划、等级考试、补考情况
并保存到本地文件中	

### Copyright
Qian Jipeng(C) 2019</br>
Thanks to Google pytesser-ocr</br>
Bugs and suggestion please mail to mokeeqian@qq.com


### 开发环境
Ubuntu + Chrome + Pycharm + vim


### 可用系统平台
+ Linux(Ubuntu) x86-64
	测试ok
+ Windows10 x86-64
	测试ok

### 程序依赖
+ python3
	+ PIL
	+ numpy
	+ libtiff
	+ 一些内置模块
+ google tesseract

### 使用方法

1. Linux
+ 进入根目录zhengfang:
	```
	cd zhengfang/
	```
+ 安装google ocr engine:
	```
	sudo apt install tesseract-ocr
	sudo apt install libtesseract-dev
	```
+ 安装python3依赖库:
	```
	pip install -r requirements.txt
	```
+ config.conf文件是用户配置文件，需要先修改用户配置信息(也可以批量获取信息，批量登录)
+ 执行python3 main.py

2. Windows
Windows配置较为复杂，具体如下：
+ pip 安装相关python依赖，建议使用豆瓣镜像源加速
	```
	cd zhengfang\
	pip install -r requirements.txt
	```

		其间可能会出现报错，说我们缺少vc++组件，导致libtiff模块不能安装，这时需要用wheel文件来安装。
		在我的项目根目录下，有libtiff库的wheel文件，基于 x86-64、Python 3.7的。如果你们的版本和我不一样，请去python官网下载相应的版本，然后执行:
		```
		pip install xxxxxx.wheel
		```
+ 配置google tesseract engine
	在Windows下，只需配置tesseract可执行文件的路径即可，我默认为你们改好路径，如果项目代码路径有改动，请自行配置
+ 配置用户配置文件config.conf
+ cmd命令行执行 `python main.py`

### 可能的问题
1. 路径配置错误
2. python依赖问题
3. 查询成绩需要在内网环境、后期可以反向代理解决
