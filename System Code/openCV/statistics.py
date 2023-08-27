# -*- coding: utf-8 -*-
# ####################################################################
# Author: WeiyiGeek
# Description: 基于easyocr实现大数据通信行程卡图片识别信息获取-Flask项目。
# Time: 2022年5月25日 17点31分
# Blog: https://www.weiyigeek.top
# Email: master@weiyigeek.top
# ====================================================================
# 环境依赖与模块安装, 建议 Python 3.8.x 的环境下进行
# pip install flask
# pip install easyocr
# ====================================================================
# 行程码有绿色、黄色、橙色、红色四种颜色。
# 1、红卡：行程中的中高风险地市将标记为红色字体作提示。
# 2、橙卡：新冠肺炎确诊或疑似患者的密切接触者。
# 3、黄卡：海外国家和地区。
# 4、绿卡：其他地区。行程卡结果包含在前14天内到访的国家（地区）与停留4小时以上的国内城市。色卡仅对到访地作提醒，不关联健康状况。
# ###################################################################### -*- coding: utf-8 -*-
# ####################################################################
# Author: WeiyiGeek
# Description: 基于easyocr实现大数据通信行程卡图片识别信息获取-Flask项目。
# Time: 2022年5月25日 17点31分
# ====================================================================
# 环境依赖与模块安装, 建议 Python 3.8.x 的环境下进行
# pip install flask
# pip install easyocr
# ====================================================================
# 行程码有绿色、黄色、橙色、红色四种颜色。
# 1、红卡：行程中的中高风险地市将标记为红色字体作提示。
# 2、橙卡：新冠肺炎确诊或疑似患者的密切接触者。
# 3、黄卡：海外国家和地区。
# 4、绿卡：其他地区。行程卡结果包含在前14天内到访的国家（地区）与停留4小时以上的国内城市。色卡仅对到访地作提醒，不关联健康状况。
# #####################################################################
from pprint import pprint
from datetime import datetime
import os
import sys
import cv2
import re
import glob
import json
import easyocr
import numpy as np
import collections
from threading import Thread

# 项目运行路径与行程码图片路径定义
RUNDIR = None
IMGDIR = None
start_time = None
end_time = None

colorDict= {"red": "红色", "red1": "红色", "orange": "橙色", "yellow": "黄色", "green": "绿色"}

class MyThread(Thread):
  def __init__(self, number):
    Thread.__init__(self)
    self.number = number

  def run(self):
    self.result = foo(self.number)

  def get_result(self):
    return self.result


def getColorList():
  """
  函数说明: 定义字典存放 HSV 颜色分量上下限 (HSV-RGB)
  例如：{颜色: [min分量, max分量]}
        {'red': [array([160, 43, 46]), array([179, 255, 255])]}
  返回值: 专门的容器数据类型，提供Python通用内置容器、dict、list、set和tuple的替代品。
  """
  dict = collections.defaultdict(list)

  # 红色
  lower_red = np.array([156, 43, 46])
  upper_red = np.array([180, 255, 255])
  color_list = []
  color_list.append(lower_red)
  color_list.append(upper_red)
  dict['red']=color_list
 
  # 红色2
  lower_red = np.array([0, 43, 46])
  upper_red = np.array([10, 255, 255])
  color_list = []
  color_list.append(lower_red)
  color_list.append(upper_red)
  dict['red2'] = color_list

  # 橙色
  lower_orange = np.array([11, 43, 46])
  upper_orange = np.array([25, 255, 255])
  color_list = []
  color_list.append(lower_orange)
  color_list.append(upper_orange)
  dict['orange'] = color_list
 
  # 黄色
  lower_yellow = np.array([26, 43, 46])
  upper_yellow = np.array([34, 255, 255])
  color_list = []
  color_list.append(lower_yellow)
  color_list.append(upper_yellow)
  dict['yellow'] = color_list

  # 绿色
  lower_green = np.array([35, 43, 46])
  upper_green = np.array([77, 255, 255])
  color_list = []
  color_list.append(lower_green)
  color_list.append(upper_green)
  dict['green'] = color_list

  return dict

def getTravelcodeColor(img_np):
  """
  函数说明: 利用阈值返回行程码主页颜色
  参数值: cv2.imread() 读取的图像对象(np数组)
  返回值: 行程卡颜色{红、橙、绿}
  """
  hsv = cv2.cvtColor(img_np, cv2.COLOR_BGR2HSV)
  maxsum = -100
  color = None
  color_dict = getColorList()
  for d in color_dict:
    mask = cv2.inRange(hsv,color_dict[d][0],color_dict[d][1])
    # cv2.imwrite(os.path.join(os.path.abspath(os.curdir),"img",d+'.jpg')  ,mask)
    binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
    binary = cv2.dilate(binary,None,iterations=2)
    cnts, hiera = cv2.findContours(binary.copy(),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    sum = 0
    for c in cnts:
      sum+=cv2.contourArea(c)
    if sum > maxsum :
      maxsum = sum
      color = d

  return colorDict[color]


def information_filter(file_path,img_np,text_str):
  """
  函数说明: 提出ocr识别的行程码
  参数值：字符串,文件名称
  返回值：有效信息组成的字典
  """
  # 健康码字段
  try:
    re_healthcode = re.compile('请收下(.{,2})行程卡')
    healthcode = re_healthcode.findall(text_str)[0]
  except Exception as _:
    healthcode = getTravelcodeColor(img_np)  # 文字无法识别时采用图片颜色识别
    print("[*] Get Photo Color = ",healthcode)

  # 电话字段
  re_phone = re.compile('[0-9]{3}\*{4}[0-9]{4}')
  phone_str = re_phone.findall(text_str)[0]

  # 日期字段
  re_data = re.compile('2022\.[0-1][0-9]\.[0-3][0-9]')
  data_str = re_data.findall(text_str)[0]

  # 时间字段
  re_time = re.compile('[0-9][0-9]:[0-9][0-9]:[0-9][0-9]')
  time_str = re_time.findall(text_str)[0]

  # 地区城市字段
  citys_re = re.compile('到达或途经:(.+)结果包含')
  citys_str = citys_re.findall(text_str)[0].strip().split('(')[0]

  result_dic = {"status": "succ", "file": file_path ,"类型": healthcode, "电话": phone_str, "日期": data_str, "时间": time_str, "行程": citys_str}
  return result_dic


def getTravelcodeInfo(filename, img_np):
  """
  函数说明: 返回以JSON字符串格式过滤后结果
  参数值：文件名称,图像作为 numpy 数组（来 opencv传递
  返回值：JSON字符串格式
  """
  # 灰度处理
  img_gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
  # 阈值二进制 - > 127 设置为255(白)，否则0(黑) -> 淡白得更白,淡黑更黑
  _,img_thresh = cv2.threshold(img_gray,180,255,cv2.THRESH_BINARY)
  # 图像 OCR 识别
  text = reader.readtext(img_thresh, detail=0, batch_size=10,workers=1) 
  result_dic = information_filter(filename, img_np, "".join(text))
  return result_dic

def main():
  onlydir = [d for d in os.listdir(IMGDIR) if os.path.isdir(os.path.join(IMGDIR, d))]  
  count = {}
  for dirname in onlydir:
    result_dic_all = []
    result_dic_err = []
    succ = 0
    error = 0
    img_path_all =  glob.iglob(os.path.join(os.path.join(IMGDIR,dirname)+"/*.[p|j]*g"))   # 正则匹配 png|jpg|jpeg 后缀的后缀,返回的是迭代器。
    print("[*] ",dirname)
    start_time = datetime.now().strftime('%Y%m%d-%H%M%S-%f')  # 开始时间记录
    for img_path in img_path_all:
      img_np = cv2.imread(img_path)
      try:
        result_dic_succ = getTravelcodeInfo(os.path.join(dirname,os.path.basename(img_path)),img_np)
        print("\033[032m",datetime.now().strftime('%Y%m%d-%H%M%S-%f'),result_dic_succ,"\033[0m")
        succ += 1
      except Exception as _:
        print("\033[31m [ERR] - "+ img_path + "\033[0m") # 输出识别错误的图像
        result_dic_err.append(img_path)
        error += 1
        continue
    
      # 成功则加入到List列表中
      result_dic_all.append(result_dic_succ)

      res_succ_json=json.dumps(result_dic_all, ensure_ascii=False)
      with open(os.path.join(IMGDIR, dirname, dirname + "-succ.json"),'w') as fsucc:
        fsucc.write(res_succ_json)

      res_err_json=json.dumps(result_dic_err, ensure_ascii=False)
      with open(os.path.join(IMGDIR, dirname,  dirname + "-err.json"),'w') as ferr:
        ferr.write(res_err_json)

    end_time = datetime.now().strftime('%Y%m%d-%H%M%S-%f') # 结束时间记录
    count[dirname] = {"succ": succ, "err": error, "start_time": start_time, "end_time": end_time}
    with open(os.path.join(IMGDIR, dirname, "statistics.txt"),'w') as dstatistics:
        dstatistics.write(str(count[dirname]))

  return count


# 程序入口
if __name__ == '__main__':
  try:
    RUNDIR = sys.argv[1]
    IMGDIR = sys.argv[2]
  except Exception as e:
    print("[*] Uage:"+ sys.argv[0] + " RUNDIR IMGDIR")
    print("[*] Default:"+ sys.argv[0] + " ./ ./img" + "\n" )
    RUNDIR = os.path.abspath(os.curdir)
    IMGDIR = os.path.join(RUNDIR, "../img")

  # 使用easyocr模块中的Reader方法, 设置识别中英文两种语言
  reader = easyocr.Reader(['ch_sim', 'en'], gpu=True) 
  start_time = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
  statistics = main() 
  end_time = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
  print("开始时间",start_time,"\n结束时间", end_time)
  pprint(statistics)
