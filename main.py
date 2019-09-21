#!/usr/bin/env python3
# encoding=utf-8
# Copyright: Qian Jipeng(C) 2019
"""
TODO:
	数据清洗与进一步解析!
"""



import os
import re
import chardet		# encoding
import urllib.parse

import requests
import numpy as np
import pandas as pd

import config_loader as cfl 	# load config

if os.name == "nt":
	os.sys.path.append(".\\pytesser_v0.0.1")	# for Windows
elif os.name == "posix":
	os.sys.path.append("./pytesser_v0.0.1")

import pytesser as ocr			# google ocr

from html.parser import *
from PIL import Image
from libtiff import TIFF


# 解析html标签
class TagParser(HTMLParser):

	def __init__(self):
		super().__init__()
		self.view_state = list()    # 用来存放viewstate
		self.event_validation = list()
		
	def __del__(self):
		del self.view_state         # 释放资源
		del self.event_validation

	def handle_starttag(self, tag, attrs):
		if tag == 'input':
			attrs = dict(attrs)
			if attrs.__contains__('name'):
				if attrs['name'] == '__VIEWSTATE':
					self.view_state.append(attrs['value'])
				elif attrs['name'] == '__EVENTVALIDATION':
					self.event_valifation.append(attrs['value'])					

	def doParse(self, webData):
		self.feed(data=webData)



class Login:

	# 有参构造
	def __init__(self, uid=cfl.getUserId(), upwd=cfl.getUserPassword()):
		#self.user_id = cfl.getUserId()
		#self.user_pwd = cfl.getUserPassword()	
		self.user_id = uid
		self.user_pwd = upwd
		self.user_name = ""
		self.login_url = cfl.getLoginUrl()
		self.checkcode_url = cfl.getCheckcodeUrl()
		self.cookies = requests.get(self.login_url).cookies
		self.headers = {
				'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
		}

		# self.query_headers = {
		# 	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		# 	'Accept-Encoding': 'gzip, deflate',
		# 	'Accept-Language': 'en-US,en;q=0.9',
		# 	'Connection': 'keep-alive',
		# 	'Content-Type': 'text/html; charset=gb2312',
		# 	'Referer': '',   # cfl.getIndexUrl() + 'xskbcx.aspx?xh=' + self.user_id + "&xm=" + self.user_name + "&gnmkdm=" + kdn_code,
		# 	# 'Referer': website + 'xs_main.aspx?xh=' + userxh,
		# 	'Upgrade-Insecure-Requests': '1',
		# 	'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
		# }

		self.config = {
			'__VIEWSTATE': '',  # viewstate
			'TextBox1': self.user_id,     # userid
			'TextBox2': self.user_pwd,     # password
			'TextBox3': '',  # checkcode
			'RadioButtonList1': '%D1%A7%C9%FA',     # session
			'Button1': "",
			'lbLanguage': '',
		}
		self.tag_parser = TagParser()
		self.tag_parser.doParse(requests.get(self.login_url).text)    # 解析
		

	def setUserId(self, uid):
		self.user_id = uid
	
	def setUserPwd(self, upwd):
		self.user_pwd = upwd

	# 获取并保存验证码图片
	# return: PIL.Image对象
	def getAndSaveCheckCode(self, filename):

		pic = requests.post(url=self.checkcode_url, cookies=self.cookies, headers=self.headers)
		if os.path.exists(filename):
			os.remove(filename)
		# write as byte
		with open(filename, 'wb') as filewriter:
			filewriter.write(pic.content)
		image = Image.open(filename)        # PIL
		#image.show()

		out_tiff = TIFF.open(filename, mode = 'w')		# TTIF
		#img = cv2.imdecode(np.fromstring(pic.content, np.uint8) )
		out_tiff.write_image(np.array(image), compression=None, write_rgb=False)
		out_tiff.close()
		
		return image
	

	# 调用google ocr(Linux) 
	# reutrn: string of the check code
	def getCheckCodeStringLinux(self, filename):
		text = str(ocr.image_file_to_string(filename))
		print("验证码: " + text)
		text = text.strip()     # 去除两边空格!!!

		if os.path.exists(filename):
			os.remove(filename)     # 删除验证码
		return text


	# 获取验证码字符串(Windows)
	# return: string
	def getCheckCodeStringWindows(self, imageObj:Image):
		text = str(ocr.image_to_string(imageObj))
		print("验证码: " + text)
		text = text.strip()
		
		return text


	# 应该在获取验证码后调用
	def updateConfig(self, viewstate, checkcode):
		self.config['__VIEWSTATE'] = viewstate
		self.config['TextBox3'] = checkcode

	# 是否登陆成功
	def checkIfSuccess(self, webContent):
		pattern = r'<title>(.*?)</title>'
		items = re.findall(pattern, webContent.text)
		if items[0] == "欢迎使用正方教务管理系统！请登录":      # 特征匹配
			return False
		else:
			# 抓取名字
			catch = '<span id="xhxm">(.*?)</span></em>'
			name = re.findall(catch, webContent.text)
			name = name[0][:-2]
			# name = name[:-2]
			print(name)
			self.user_name = urllib.parse.quote(name.encode("gb2312"))      # 更新用户姓名
			return True


# 对外接口，用于从csv文件中获取用户配置信息
def getAllUsersFromExcel(filename:str):

	with open(filename, "rb") as f:
		# data_frame = pd.read_csv(f)
		encoding = chardet.detect(f.read())['encoding']
	print(encoding)

	with open(filename, "r", encoding=encoding, errors='replace') as fo:
		data_info = pd.read_csv(fo)

	# print(data_info['学号'])

	return data_info[['学号', '身份证件号']]




# 全局函数，对外接口
# return: true if success
def doLogin(loginobject:Login, filename:str, resultdir:str):

	sep = os.sep		# 文件名分隔符
	
	checkcodeimage = loginobject.getAndSaveCheckCode(filename)
	#checkcode = input("输入验证码: ")

	# 这里非常奇怪，谷歌pytesser引擎在不同系统具有不同的处理逻辑
	# 所以我也做了跨平台的处理，不同系统平台调用不同api
	if os.name == "nt":
		checkcode = loginobject.getCheckCodeStringWindows(checkcodeimage)
	elif os.name == "posix":
		checkcode = loginobject.getCheckCodeStringLinux(filename)

	#print(checkcode)

	loginobject.updateConfig(loginobject.tag_parser.view_state[0], checkcode)
	# print(loginobject.config)
	content = requests.post(url=loginobject.login_url, data=loginobject.config,
	                        headers=loginobject.headers, cookies=loginobject.cookies)

	if loginobject.checkIfSuccess(content):
		print("登陆成功!!!")

		# 检查结果路径
		if not os.path.exists(resultdir):
			os.system("mkdir " + resultdir)
		else:
			for f in os.listdir(resultdir):
				os.remove(resultdir + sep + f)

	else:
		print("登录失败~~~")
		return False

	# query = Query()
	# query.queryCourse()

	print("-------------开始查询----------")
	# 配置区(一般无需修改)
	course_url = cfl.getIndexUrl() + 'xskbcx.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121603"
	exam_url = cfl.getIndexUrl() + 'xskscx.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121604"
	classexam_url = cfl.getIndexUrl() + 'xsdjkscx.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121606"
	plan_url = cfl.getIndexUrl() + 'pyjh.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121607"
	select_course_url = cfl.getIndexUrl() + 'pyjh.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121615"
	add_exam_url = cfl.getIndexUrl() + 'xsbkkscx.aspx?xh=' + loginobject.user_id + "&xm=" + loginobject.user_name + "&gnmkdm=" + "N121613"


	query_config = {
		'__EVENTTARGET': '',
		'__EVENTARGUMENT': '',
		'__VIEWSTATE': '',
	}
	query_headers = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'en-US,en;q=0.9', 'Connection': 'keep-alive',
		'Content-Type': 'text/html; charset=gb2312', 'Referer': '', 'Upgrade-Insecure-Requests': '1',
		'User-Agent': r'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
	# end 配置区

	# ------------------------- 查询课表 ----------------------
	print("开始查询课表...")
	query_headers['Referer'] = course_url
	# 先get一下，获取view_state
	course_html = requests.get(course_url, cookies=loginobject.cookies,
	                    headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, course_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	course = requests.session().get(url=course_url, data=query_config,
	                                headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	course_table = re.findall(catch, course.text)
	del course

	f = open(resultdir + sep + "course_table.txt", "w")
	for each_line in course_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del course_table
	# ------------------------- 课表结束 ------------------------

	# ------------------------- 查询考试安排 -----------------------
	print("开始查询考试安排...")
	query_headers['Referer'] = exam_url
	exam_html = requests.get(exam_url, cookies=loginobject.cookies,
	                           headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, exam_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	exam = requests.session().get(url=exam_url, data=query_config,
	                                headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	exam_table = re.findall(catch, exam.text)
	del exam

	f = open(resultdir + sep + "exam_arrangement.txt", "w")
	for each_line in exam_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del exam_table
	# ----------------------------------- 结束 -----------------------------------------

	# ----------------------------------等级考试成绩查询 --------------------------------
	print("开始查询等级考试成绩...")
	query_headers['Referer'] = classexam_url
	classexam_html = requests.get(classexam_url, cookies=loginobject.cookies,
	                         headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, classexam_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	classexam = requests.session().get(url=classexam_url, data=query_config,
	                              headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	classexam_table = re.findall(catch, classexam.text)
	del classexam

	f = open(resultdir + sep + "class_exam.txt", "w")
	for each_line in classexam_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del classexam_table
	# --------------------------- 结束 --------------------------

	# -------------------- 培养计划查询 ------------------------
	print("开始查询培养计划...")
	query_headers['Referer'] = plan_url
	plan_html = requests.get(plan_url, cookies=loginobject.cookies,
	                         headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, plan_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	plan = requests.session().get(url=plan_url, data=query_config,
	                              headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	plan_table = re.findall(catch, plan.text)
	del plan

	f = open( resultdir + sep + "development_plan.txt", "w")
	for each_line in plan_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del plan_table
	# --------------------- 结束 ----------------------------

	# --------------------- 学生选课情况查询 ------------------------------
	print("开始查询选课情况...")
	query_headers['Referer'] = select_course_url
	select_course_html = requests.get(select_course_url, cookies=loginobject.cookies,
	                         headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, select_course_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	select_course = requests.session().get(url=select_course_url, data=query_config,
	                              headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	select_course_table = re.findall(catch, select_course.text)
	del select_course

	f = open(resultdir + sep + "select_course.txt", "w")
	for each_line in select_course_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del select_course_table
	# --------------------- 结束 ----------------------------

	# ------------------- 补考开始查询 ----------------------
	print("开始查询补考安排...")
	query_headers['Referer'] = add_exam_url
	add_exam_html = requests.get(add_exam_url, cookies=loginobject.cookies,
	                             headers=query_headers)
	catch = '<input type="hidden" name="__VIEWSTATE" value="(.*?)" />'
	query_state = re.findall(catch, add_exam_html.text)[0]
	query_config['__VIEWSTATE'] = query_state
	del query_state
	add_exam = requests.session().get(url=add_exam_url, data=query_config,
	                                  headers=query_headers, cookies=loginobject.cookies)
	# print(course.text)        # 测试ok
	# 写入文件
	catch = '<td>(.*?)</td>'
	add_exam_table = re.findall(catch, add_exam.text)
	del add_exam

	f = open(resultdir + sep + "add_exam.txt", "w")
	for each_line in add_exam_table:
		if "&nbsp" in each_line:
			# TODO: 数据清洗
			pass
		f.write(each_line + "\n")
	f.close()
	del add_exam_table
	# ------------------- 结束 ------------------------

	print("------------查询成功-----------")
	return True


# 学生成绩查询，单独的url, 单独的模块,需要内网支持!!!
def queryScore():
	index_url = "http://211.70.149.134:8080/stud_score/brow_stud_score.aspx"

	request_headers = {
	   'Accept': 'text/html, application/xhtml+xml, application/xml; q=0.9, */*; q=0.8',
	   'Accept-Encoding': 'gzip, deflate',
	   'Accept-Language': 'zh-CN',
	   'Cache-Control': 'max-age=0',
	   'Connection': 'Keep-Alive',
	   'Content-Length': '1979',
	   'Content-Type': 'application/x-www-form-urlencoded',
	   'Host': '211.70.149.134:8080',
	   'Referer': 'http://211.70.149.134:8080/stud_score/brow_stud_score.aspx',
	   'Upgrade-Insecure-Requests': '1',
	   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.18362',
	}

	# pre_content = requests.get(url=index_url, headers=request_headers)
	# tag = TagParser()
	# tag.doParse(pre_content)

	request_body = {
		'__VIEWSTATE': '/wEPDwUKLTc5MTY3NzY2OA9kFgICAw9kFg4CBQ8QZBAVEg09Peivt+mAieaLqT09CTIwMTgtMjAxOQkyMDE3LTIwMTgJMjAxNi0yMDE3CTIwMTUtMjAxNgkyMDE0LTIwMTUJMjAxNC0yMDE1CTIwMTMtMjAxNAkyMDEzLTIwMTQJMjAxMi0yMDEzCTIwMTEtMjAxMwkyMDExLTIwMTIJMjAxMC0yMDExCTIwMDktMjAxMAkyMDA4LTIwMDkJMjAwNy0yMDA4CTIwMDYtMjAwNwkyMDA1LTIwMDYVEgAJMjAxOC0yMDE5CTIwMTctMjAxOAkyMDE2LTIwMTcJMjAxNS0yMDE2CTIwMTQtMjAxNQkyMDE0LTIwMTUJMjAxMy0yMDE0CTIwMTMtMjAxNAkyMDEyLTIwMTMJMjAxMS0yMDEzCTIwMTEtMjAxMgkyMDEwLTIwMTEJMjAwOS0yMDEwCTIwMDgtMjAwOQkyMDA3LTIwMDgJMjAwNi0yMDA3CTIwMDUtMjAwNhQrAxJnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dkZAIHDxBkEBUDDT096K+36YCJ5oupPT0BMgExFQMAATIBMRQrAwNnZ2dkZAIdD2QWAgIFDzwrABEBDBQrAABkAh8PZBYCAgEPPCsAEQEMFCsAAGQCIw9kFgICCQ88KwARAQwUKwAAZAIlD2QWAgIDDxBkZBYBZmQCJw9kFgICAQ88KwARAgEQFgAWABYADBQrAABkGAQFCUdyaWRWaWV3Mw9nZAUJR3JpZFZpZXcxD2dkBQxHcmlkVmlld19jajAPZ2QFC0dyaWRWaWV3X2NqD2dkfgx9G639stk68qu1tbM6nXH+3YdlwZe2JIGSN2ZE088=',		# 提前抓取
		'__EVENTVALIDATION': '/wEdACUp2xwQA5+MxGAylYqe6RvwESCFkFW/RuhzY1oLb/NUVB2nXP6dhZn6mKtmTGNHd3MwXQrG5ab0It+QKWTLaqmfIGx0hKQHqP/3fgB45pITpVPxlwAt6+N0jBvmsiExk1IL7R6YXHs4CYW6xoeIyFd16zXVvnblom7uU1wVnGg7wjTQGKLCZEVQGnXF5+HuveXO10VSDEID+Eh3nI1jlRVvAThS3H1vAk8dedvccz5HgzmT0s6BT0Wkysz2I1SVLK+BBoNsEnjusSCSqveEZIqKAqG9xWW5285pNEE/6xwtSGnvX+yWIf+Wd+BdgehLsTAOZMoWbJOD2xQz+jIVoq5usPGGtH1tfrRv2ZNXrhgDFgrzjXp2SzUmL/y0eqihj4CJd11haMaOlgGzsMzfNEGBCbGJdvVBiiKVFujA6Ty1+MteZur+FCukzKhg+dlfCCZ5ZXtzeYjop7ggcaKI2ArSMioS6xc0u4fT37iCAdJxSZ6Mq6ynQbr4SRbEt4fHquJ8HmzRIlNrYaLaoxNFkxJO8yv94tgoHy9fqXClMftcBv4KKg+fSMB29qVef+gLDI7R6mxQNC8xefIWSo4ykR6hMTQRw0wuRK4Dl44ooHPTmt+ZBkpb3m69wIYc3c25ONNlxf5DDVPFMmdvMOOjsZ8t2Mw1Ns2QByN3423c3ELIzh9H7TEwiNBjwLWQMcU1zfvVpr/9fHHTrBelNp+6kgKqR2Lfb8DngnqdQ/vCfpj94mQiGuqbQE6PCJUV5xtw06aeG3AaN7W8QZ1ogxwj25m/E4I+VOAdW6Oiquo3Vm9x9KL3uQI+SWcZLuVZNvx80A0=',	# 提前抓取
		'Button_cjcx': '查询',
		'drop_type': '全部成绩',	# TODO: 不要写死了
		'drop_xn': '2018-2019',	# 不要写死了
		'drop_xq': '1',		# 1,2
		'hid_dqszj': '',
		'TextBox1': cfl.getUserId(),	# id
		'TextBox2': cfl.getUserPassword(),	# pwd
	}
	content = requests.post(url=index_url, headers=request_headers, data=request_body)
	# print(content.text)

	catch = '<td>(.*?)</td>'
	data = re.findall(catch, content.text)
	for item in data:
		print(item)



# 批量登录入口
def main_loop():
	userset = getAllUsersFromExcel("info_table.csv")	# 获取所有的用户信息
	for index, row in userset.iterrows():
		userid = str(row['学号'])
		userpwd = str(row['身份证件号'])
		#print(userid)
		#print(userpwd)
		checkcodefile = os.curdir + os.sep + cfl.getCheckcodeFilename()
		resultfile = os.curdir + os.sep + cfl.getResultDirname()
		
		login = Login(userid.strip(), userpwd.strip())
		
		print("###  " + login.user_id)
		print( "### " + login.user_pwd )
		
		# 当前信息不对，跳过
		if doLogin( login, checkcodefile, resultfile ) == False:
			continue

		if os.path.exists(checkcodefile):
			os.remove(checkcodefile)
	
		
# 单个查询
def main():
	checkcodefile = os.curdir + os.sep + cfl.getCheckcodeFilename()
	resultfile = os.curdir + os.sep + cfl.getResultDirname()
	login = Login()
	doLogin( login, checkcodefile, resultfile )

	if os.path.exists(checkcodefile):
		os.remove(checkcodefile)


if __name__ == '__main__':
	#main_loop()	
	#main()
	queryScore()
	

