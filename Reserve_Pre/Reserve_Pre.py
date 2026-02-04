from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

# import sys
# sys.path.append(r"C:\Python\Pomelo_test\Reserve_Pre")
# print(sys.path)
from Reserve_Pre.Reserve_Pre_api import HisapiReserve,MssqlApiReserve

from django.conf import settings
import pymssql

try:
	import oracledb
	try:
		# 從 settings 讀取 Oracle Client 路徑
		oracle_client_path = getattr(settings, 'ORACLE_CLIENT_PATH', None)
		
		if oracle_client_path:
			# 使用指定路徑啟用 Thick Mode
			oracledb.init_oracle_client(lib_dir=oracle_client_path)
			print(f"Oracle Thick Mode enabled with path: {oracle_client_path}")
		else:
			# 嘗試使用預設路徑啟用 Thick Mode
			oracledb.init_oracle_client()
			print("Oracle Thick Mode enabled with default path")
	except Exception as e:
		print(f"Failed to enable Thick Mode: {e}")
		print("Will attempt to use Thin Mode, but may encounter password verifier issues")
	
	import oracledb as cx_Oracle
except ImportError:
	cx_Oracle = None
	print("oracledb module not installed")
import re
from datetime import datetime,timedelta
import pandas as pd
import numpy as np
import base64
import json
import requests
import time


#慢箋序號/科別名/看診日/醫師名字/第二次慢箋可預約日期/第二次慢箋預約日期/第三次慢箋可預約日期/第三次慢箋預約日期/第幾次慢箋預約/最近領藥日/最近領藥號
chroard = 0
sename = 1
visitdt = 2
doc_name = 3
HIS_2_START = 4
HIS_2_END = 5
reserve_2 = 6
third_START = 7
third_END = 8
reserve_3 = 9
resno_times = 10
lastdate = 11
drugno = 12
datecolumn = 13
alert_word = 14


class AllCode:
	def logrecond(pd_id,birthday): #登入log紀錄
		write = MssqlApiReserve.insertA007LoginLogWeb(pd_id,birthday,'A007_Reserve_pre/login')

	def todateDate(): #抓取今日日期
		today = datetime.now()
		formatted_date = today.strftime("%Y%m%d")

		return formatted_date

	def breakDate(): #抓取56天前的日期
		today = datetime.now()
		previous_date = today - timedelta(days=56)
		formatted_date = previous_date.strftime("%Y%m%d")

		return formatted_date

	def searchChrocard(pd_id,birthday): #找慢箋內容(身分證/生日)
		#轉西元
		year = int(birthday[:3]) + 1911
		birthday_ad = f"{year}{birthday[3:]}"

		pd_chdata = HisapiReserve.select_CHTPAT(pd_id,birthday_ad)
		if (len(pd_chdata) == 0):
			return '無此病患',''

		#抓今天日期
		today = AllCode.todateDate()
		# today = pd.to_datetime(today, format='%Y%m%d')
		# print(today)

		#搜尋慢箋
		data = HisapiReserve.select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT(pd_id,birthday_ad,today)

		today = pd.to_datetime(today, format='%Y%m%d') #轉換以便比較
		if (data == []):
			# print('有這個病人但沒有任何的預約慢箋')
			bir = datetime.strptime(pd_chdata[0][1], '%Y%m%d')

			#生日轉民國
			roc_year = bir.year - 1911
			roc_date_str = f"{roc_year:03d}{bir.month:02d}{bir.day:02d}"

			pd_chdata1 = list(map(list, pd_chdata))
			pd_chdata1[0][1] = roc_date_str
			pd_chdata1[0][4] = '女' if pd_chdata1[0][4] == 'F' else '男'

			return pd_chdata1,''


		else:
			data_f = pd.DataFrame(data)
			data_f = data_f.rename(columns={0:'身分證',1:'生日',2:'名字',3:'病歷號',4:'性別',5:'住家電話',6:'行動電話',
											7:'慢箋序號',8:'科別名',9:'看診日',10:'醫師名',11:'批價次數',12:'最大批價次數',13:'最近領藥日',14:'慢箋結束日',15:'總天數',
											16:'HIS_2_START',17:'HIS_2_END',18:'HIS_3_START',19:'HIS_3_END',20:'最近領藥號'})


			#個人資料-------------------------------------------------------------------------------------------------------------------
			data_pd = data_f[['身分證', '生日','名字','病歷號','性別','住家電話','行動電話']]

			data_pd = data_pd.copy()
			conditions = [data_pd['性別'] == 'M',data_pd['性別'] == 'F']
			choices = ['男', '女']
			data_pd['性別'] = np.select(conditions, choices, default='無')

			data_pd = data_pd.drop_duplicates() #去除重複
			data_pd['生日'] = data_pd['生日'].apply(lambda x: (str(int(x[:4]) - 1911) + x[4:]).zfill(7)) #生日轉民國

			# data_pd['住家電話'] = data_pd['住家電話'].str.replace(r'(\d{2})(\d{4})(\d+)', r'\1-\2-\3', regex=True)
			# data_pd['行動電話'] = data_pd['行動電話'].str.replace(r'(\d{4})(\d{3})(\d+)', r'\1-\2-\3', regex=True)

			data_pd = data_pd.values.tolist() #轉成陣列
			# print(data_pd)



			#慢箋資料整理-----------------------------------------------------------------------------------------------------------------
			data_info = data_f[['慢箋序號', '科別名','看診日','醫師名','批價次數','最大批價次數','最近領藥日','慢箋結束日','總天數','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥號']]

			data_info = data_info.copy()

			data_info['HIS_2_START'] = pd.to_datetime(data_info['HIS_2_START'], format='%Y%m%d')
			data_info['HIS_2_END'] = pd.to_datetime(data_info['HIS_2_END'], format='%Y%m%d')
			data_info['HIS_3_START'] = pd.to_datetime(data_info['HIS_3_START'], format='%Y%m%d')
			data_info['HIS_3_END'] = pd.to_datetime(data_info['HIS_3_END'], format='%Y%m%d')
			data_info['最近領藥日'] = pd.to_datetime(data_info['最近領藥日'], format='%Y%m%d')
			data_info['看診日'] = pd.to_datetime(data_info['看診日'], format='%Y%m%d')
			# print('data_info')
			# print(data_info)


			#判斷是否只有兩次慢箋
			data_info_all2 = data_info[data_info['最大批價次數'] == 2] #只有2次
			# print('data_info_all2:')
			# print(data_info_all2)
			data_info_all3 = data_info[data_info['最大批價次數'] > 2]  #共有3次

			data_info_all3_2 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_between = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_not_between1 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_not_between2 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])

			
			if (len(data_info_all3) > 0): #一共有3次慢箋

				# 且 (1)HIS_2_END >= 現在 (2) "最近領藥日"在HIS_2_START之前 → 顯示第2次
				data_info_all3_2 = data_info_all3[(data_info_all3['HIS_2_END'] >= today) & (data_info_all3['最近領藥日'] < data_info_all3['HIS_2_START'])]
				

				#以下是要顯示第三次的-----------------------------------------------------------------------------------------------------------------
				# 去除前面的第二次條件 → 顯示第3次
				# 總共有兩種可能:(1)HIS_2_END> 現在的 且 "最近領藥日"在HIS_2_START之後(可能是已領藥但是HIS_2_END比現在時間晚，所以要顯示第三次) (2)HIS_2_END(今天算以前) <= 現在
				data_info_all3_3 = data_info_all3[~data_info_all3.isin(data_info_all3_2).all(axis=1)]
				
				if (len(data_info_all3_3) > 0):

					# (1) 最近領藥日 在 HIS_2_START 和 HIS_2_END 之間 → 第二次有準時領 → HIS_2_END+天數 = 第3次
					df_between = data_info_all3_3[(data_info_all3_3['最近領藥日'] >= data_info_all3_3['HIS_2_START']) & (data_info_all3_3['最近領藥日'] <= data_info_all3_3['HIS_2_END'])]

					# (2) 最近領藥日 不在 HIS_2_START 和 HIS_2_END 之間 
					df_not_between = data_info_all3_3[~((data_info_all3_3['最近領藥日'] > data_info_all3_3['HIS_2_START']) & (data_info_all3_3['最近領藥日'] < data_info_all3_3['HIS_2_END']))]

					# 2-1 最近領藥日 < HIS_2_START → 第二次未在長安領 → 第3次只能來現場領(第3次就算未逾期也依然無法預約) HIS_2_END+天數 = 第3次
					df_not_between1 = df_not_between[(df_not_between['最近領藥日'] < df_not_between['HIS_2_START'])]

					# 2-2 HIS_2_END < 最近領藥日 → 第二次延遲領 → 最近領藥日+天數 = 第3次
					df_not_between2 = df_not_between[(df_not_between['最近領藥日'] > df_not_between['HIS_2_END'])]

					df_not_between2 = df_not_between2.copy()
					df_not_between2['總天數'] = df_not_between2['總天數'].astype(int)
					df_not_between2['HIS_3_END'] = df_not_between2['最近領藥日'] + pd.to_timedelta(df_not_between2['總天數']/3, unit='days')
					df_not_between2['HIS_3_START'] = df_not_between2['HIS_3_END'] - pd.Timedelta(days=10)


			data_info_all2_result = data_info_all2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			data_info_all2_result = data_info_all2_result.copy()
			data_info_all2_result['HIS_3_START'] = '無'
			data_info_all2_result['HIS_3_END'] = '無'
			data_info_all2_result.insert(6, '第二次慢箋預約日期','可預約')
			data_info_all2_result.insert(9, '第三次慢箋預約日期','無')
			data_info_all2_result.insert(10, '慢箋次數','2')
			# print(data_info_all2_result)

			#判斷共2次是否已逾期
			data_info_all2_result2 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] < today)] #第2次已逾期
			data_info_all2_result2['第二次慢箋預約日期'] = '已逾期'
			data_info_all2_result3 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] >= today)] #第2次未逾期
			data_info_all2_result4 = pd.concat([data_info_all2_result2, data_info_all2_result3], ignore_index=True)    #1
			# print('共兩次最終結果:')
			# print(data_info_all2_result4)
			#共兩次的最終結果


			#共3次的整理
			data_info_all3_2_result = data_info_all3_2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			data_info_all3_2_result.insert(6, '第二次慢箋預約日期','可預約')
			data_info_all3_2_result.insert(9, '第三次慢箋預約日期','未開放')
			data_info_all3_2_result.insert(10, '慢箋次數','2')                    #2
			# print('有三次第二次還未領取(未過期):')
			# print(data_info_all3_2_result)


			df_between_result = df_between[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_between_result.insert(6, '第二次慢箋預約日期','已領取')

			df_between_result2 = df_between_result[(df_between_result['HIS_3_END'] < today)] #第3次已逾期
			df_between_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_between_result3 = df_between_result[(df_between_result['HIS_3_END'] >= today)] #第3次未逾期
			df_between_result3.insert(9, '第三次慢箋預約日期','可預約')
			df_between_result4 = pd.concat([df_between_result2, df_between_result3], ignore_index=True)
			df_between_result4.insert(10, '慢箋次數','3')         #3
			# print('第二次有準時領，顯示第三次:')
			# print(df_between_result4)

			df_not_between1_result = df_not_between1[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_not_between1_result.insert(6, '第二次慢箋預約日期','已逾期')

			df_not_between1_result2 = df_not_between1_result[(df_not_between1_result['HIS_3_END'] < today)] #第3次已逾期
			df_not_between1_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_not_between1_result3 = df_not_between1_result[(df_not_between1_result['HIS_3_END'] >= today)] #第3次未逾期(第2次未在長安領第3次只能來現場領)
			df_not_between1_result3.insert(9, '第三次慢箋預約日期','無法預約')
			df_not_between1_result4 = pd.concat([df_not_between1_result2, df_not_between1_result3], ignore_index=True)
			df_not_between1_result4.insert(10, '慢箋次數','3')       #4
			# print('第二次未在長安領，顯示第三次:')        
			# print(df_not_between1_result4)


			df_not_between2_result = df_not_between2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_not_between2_result.insert(6, '第二次慢箋預約日期','已領取')

			df_not_between2_result2 = df_not_between2_result[(df_not_between2_result['HIS_3_END'] < today)] #第3次已逾期
			df_not_between2_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_not_between2_result3 = df_not_between2_result[(df_not_between2_result['HIS_3_END'] >= today)] #第3次未逾期(第二次延遲領)



			#----------------------------------------------------------------------------------------------------------------------------------
			#HIS API 未修改 (延遲領不能過API)
			# df_not_between2_result3.insert(9, '第三次慢箋預約日期','無法預約')
			#HIS API 已修改(延遲領可過API)
			df_not_between2_result3.insert(9, '第三次慢箋預約日期','可預約')
			#----------------------------------------------------------------------------------------------------------------------------------




			df_not_between2_result4 = pd.concat([df_not_between2_result2, df_not_between2_result3], ignore_index=True)
			df_not_between2_result4.insert(10, '慢箋次數','3')       #5
			# print('第二次延遲領，顯示第三次:')
			# print(df_not_between2_result4)


			#整合全部並格式整理
			#慢箋序號/科別名/看診日/醫師名字/第二次慢箋可預約日期/第二次慢箋預約日期/第三次慢箋可預約日期/第三次慢箋預約日期/第幾次慢箋預約
			data_all = pd.concat([data_info_all2_result4, data_info_all3_2_result,df_between_result4,df_not_between1_result4,df_not_between2_result4], ignore_index=True)
			data_all['HIS_2_START'] = pd.to_datetime(data_all['HIS_2_START'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['HIS_2_END'] = pd.to_datetime(data_all['HIS_2_END'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['看診日'] = pd.to_datetime(data_all['看診日'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['最近領藥日'] = pd.to_datetime(data_all['最近領藥日'], errors='coerce').dt.strftime('%Y%m%d')

			data_all['HIS_3_START'] = np.where(data_all['HIS_3_START'] == '無', '無', pd.to_datetime(data_all['HIS_3_START'], errors='coerce').dt.strftime('%Y-%m-%d'))
			data_all['HIS_3_END'] = np.where(data_all['HIS_3_END'] == '無', '無', pd.to_datetime(data_all['HIS_3_END'], errors='coerce').dt.strftime('%Y-%m-%d'))
			
			data_all = data_all.sort_values(by='看診日')
			# print(data_all)
			data_all_list = data_all.values.tolist() #轉成陣列
			# print("data_all_list:")
			# print(data_all_list)







			#查MSSQL的預約資料(找預約紀錄)
			result_data = AllCode.searchMssqlReserve(data_all_list)
			# result_data = [['0000462119', '內分泌新陳代謝科', '2024-11-30', '劉存鎮', '2024-12-17', '2024-12-30', '可預約', '2025-01-15', '2025-01-25', '未開放', '2']]

			#可預約日期區間統整(去除昨日之前/六日/跨週末問題/去除休診日，並處理過年提前領藥)
			date_choose = AllCode.reserveDate(result_data)
			# print('date_choose:')
			# print(date_choose)

			#API加回來要刪除---------------------------------------------------------------------------------------------------------------
			# for entry in date_choose:
			# 	if entry[13] != '無' and entry[13] != '已無法預約':
			# 		entry[13] = [AllCode.add_weekday(date) for date in entry[13]]
			# # print(date_choose)
			# check = date_choose
			#API加回來要刪除---------------------------------------------------------------------------------------------------------------

			#呼叫API確認是否可以預約+加入星期幾(先mark)
			check = AllCode.checkApi(data_pd,date_choose)
			


			#判斷預約日期是否可取消
			check2 = AllCode.cancelCheck(check)
 
			return data_pd,check2

	def searchChrocard2(pdnum): #找慢箋內容(病歷號)
		pd_chdata = HisapiReserve.select_CHTPAT2(pdnum)
		if (len(pd_chdata) == 0):
			return '無此病患',''

		#抓今天日期
		today = AllCode.todateDate()
		# today = pd.to_datetime(today, format='%Y%m%d')
		# print(today)

		#搜尋慢箋
		data = HisapiReserve.select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT2(pdnum,today)

		today = pd.to_datetime(today, format='%Y%m%d') #轉換以便比較
		if (data == []):
			# print('有這個病人但沒有任何的預約慢箋')
			bir = datetime.strptime(pd_chdata[0][1], '%Y%m%d')

			#生日轉民國
			roc_year = bir.year - 1911
			roc_date_str = f"{roc_year:03d}{bir.month:02d}{bir.day:02d}"

			pd_chdata1 = list(map(list, pd_chdata))
			pd_chdata1[0][1] = roc_date_str
			pd_chdata1[0][4] = '女' if pd_chdata1[0][4] == 'F' else '男'

			return pd_chdata1,''


		else:
			data_f = pd.DataFrame(data)
			data_f = data_f.rename(columns={0:'身分證',1:'生日',2:'名字',3:'病歷號',4:'性別',5:'住家電話',6:'行動電話',
											7:'慢箋序號',8:'科別名',9:'看診日',10:'醫師名',11:'批價次數',12:'最大批價次數',13:'最近領藥日',14:'慢箋結束日',15:'總天數',
											16:'HIS_2_START',17:'HIS_2_END',18:'HIS_3_START',19:'HIS_3_END',20:'最近領藥號'})


			#個人資料-------------------------------------------------------------------------------------------------------------------
			data_pd = data_f[['身分證', '生日','名字','病歷號','性別','住家電話','行動電話']]

			data_pd = data_pd.copy()
			conditions = [data_pd['性別'] == 'M',data_pd['性別'] == 'F']
			choices = ['男', '女']
			data_pd['性別'] = np.select(conditions, choices, default='無')

			data_pd = data_pd.drop_duplicates() #去除重複
			data_pd['生日'] = data_pd['生日'].apply(lambda x: (str(int(x[:4]) - 1911) + x[4:]).zfill(7)) #生日轉民國

			# data_pd['住家電話'] = data_pd['住家電話'].str.replace(r'(\d{2})(\d{4})(\d+)', r'\1-\2-\3', regex=True)
			# data_pd['行動電話'] = data_pd['行動電話'].str.replace(r'(\d{4})(\d{3})(\d+)', r'\1-\2-\3', regex=True)

			data_pd = data_pd.values.tolist() #轉成陣列
			# print(data_pd)



			#慢箋資料整理-----------------------------------------------------------------------------------------------------------------
			data_info = data_f[['慢箋序號', '科別名','看診日','醫師名','批價次數','最大批價次數','最近領藥日','慢箋結束日','總天數','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥號']]

			data_info = data_info.copy()

			data_info['HIS_2_START'] = pd.to_datetime(data_info['HIS_2_START'], format='%Y%m%d')
			data_info['HIS_2_END'] = pd.to_datetime(data_info['HIS_2_END'], format='%Y%m%d')
			data_info['HIS_3_START'] = pd.to_datetime(data_info['HIS_3_START'], format='%Y%m%d')
			data_info['HIS_3_END'] = pd.to_datetime(data_info['HIS_3_END'], format='%Y%m%d')
			data_info['最近領藥日'] = pd.to_datetime(data_info['最近領藥日'], format='%Y%m%d')
			data_info['看診日'] = pd.to_datetime(data_info['看診日'], format='%Y%m%d')
			# print('data_info')
			# print(data_info)


			#判斷是否只有兩次慢箋
			data_info_all2 = data_info[data_info['最大批價次數'] == 2] #只有2次
			# print('data_info_all2:')
			# print(data_info_all2)
			data_info_all3 = data_info[data_info['最大批價次數'] > 2]  #共有3次

			data_info_all3_2 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_between = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_not_between1 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])
			df_not_between2 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號'])

			
			if (len(data_info_all3) > 0): #一共有3次慢箋

				# 且 (1)HIS_2_END >= 現在 (2) "最近領藥日"在HIS_2_START之前 → 顯示第2次
				data_info_all3_2 = data_info_all3[(data_info_all3['HIS_2_END'] >= today) & (data_info_all3['最近領藥日'] < data_info_all3['HIS_2_START'])]
				

				#以下是要顯示第三次的-----------------------------------------------------------------------------------------------------------------
				# 去除前面的第二次條件 → 顯示第3次
				# 總共有兩種可能:(1)HIS_2_END> 現在的 且 "最近領藥日"在HIS_2_START之後(可能是已領藥但是HIS_2_END比現在時間晚，所以要顯示第三次) (2)HIS_2_END(今天算以前) <= 現在
				data_info_all3_3 = data_info_all3[~data_info_all3.isin(data_info_all3_2).all(axis=1)]
				
				if (len(data_info_all3_3) > 0):

					# (1) 最近領藥日 在 HIS_2_START 和 HIS_2_END 之間 → 第二次有準時領 → HIS_2_END+天數 = 第3次
					df_between = data_info_all3_3[(data_info_all3_3['最近領藥日'] >= data_info_all3_3['HIS_2_START']) & (data_info_all3_3['最近領藥日'] <= data_info_all3_3['HIS_2_END'])]

					# (2) 最近領藥日 不在 HIS_2_START 和 HIS_2_END 之間 
					df_not_between = data_info_all3_3[~((data_info_all3_3['最近領藥日'] > data_info_all3_3['HIS_2_START']) & (data_info_all3_3['最近領藥日'] < data_info_all3_3['HIS_2_END']))]

					# 2-1 最近領藥日 < HIS_2_START → 第二次未在長安領 → 第3次只能來現場領(第3次就算未逾期也依然無法預約) HIS_2_END+天數 = 第3次
					df_not_between1 = df_not_between[(df_not_between['最近領藥日'] < df_not_between['HIS_2_START'])]

					# 2-2 HIS_2_END < 最近領藥日 → 第二次延遲領 → 最近領藥日+天數 = 第3次
					df_not_between2 = df_not_between[(df_not_between['最近領藥日'] > df_not_between['HIS_2_END'])]

					df_not_between2 = df_not_between2.copy()
					df_not_between2['總天數'] = df_not_between2['總天數'].astype(int)
					df_not_between2['HIS_3_END'] = df_not_between2['最近領藥日'] + pd.to_timedelta(df_not_between2['總天數']/3, unit='days')
					df_not_between2['HIS_3_START'] = df_not_between2['HIS_3_END'] - pd.Timedelta(days=10)


			data_info_all2_result = data_info_all2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			data_info_all2_result = data_info_all2_result.copy()
			data_info_all2_result['HIS_3_START'] = '無'
			data_info_all2_result['HIS_3_END'] = '無'
			data_info_all2_result.insert(6, '第二次慢箋預約日期','可預約')
			data_info_all2_result.insert(9, '第三次慢箋預約日期','無')
			data_info_all2_result.insert(10, '慢箋次數','2')
			# print(data_info_all2_result)

			#判斷共2次是否已逾期
			data_info_all2_result2 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] < today)] #第2次已逾期
			data_info_all2_result2['第二次慢箋預約日期'] = '已逾期'
			data_info_all2_result3 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] >= today)] #第2次未逾期
			data_info_all2_result4 = pd.concat([data_info_all2_result2, data_info_all2_result3], ignore_index=True)    #1
			# print('共兩次最終結果:')
			# print(data_info_all2_result4)
			#共兩次的最終結果


			#共3次的整理
			data_info_all3_2_result = data_info_all3_2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			data_info_all3_2_result.insert(6, '第二次慢箋預約日期','可預約')
			data_info_all3_2_result.insert(9, '第三次慢箋預約日期','未開放')
			data_info_all3_2_result.insert(10, '慢箋次數','2')                    #2
			# print('有三次第二次還未領取(未過期):')
			# print(data_info_all3_2_result)


			df_between_result = df_between[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_between_result.insert(6, '第二次慢箋預約日期','已領取')

			df_between_result2 = df_between_result[(df_between_result['HIS_3_END'] < today)] #第3次已逾期
			df_between_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_between_result3 = df_between_result[(df_between_result['HIS_3_END'] >= today)] #第3次未逾期
			df_between_result3.insert(9, '第三次慢箋預約日期','可預約')
			df_between_result4 = pd.concat([df_between_result2, df_between_result3], ignore_index=True)
			df_between_result4.insert(10, '慢箋次數','3')         #3
			# print('第二次有準時領，顯示第三次:')
			# print(df_between_result4)

			df_not_between1_result = df_not_between1[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_not_between1_result.insert(6, '第二次慢箋預約日期','已逾期')

			df_not_between1_result2 = df_not_between1_result[(df_not_between1_result['HIS_3_END'] < today)] #第3次已逾期
			df_not_between1_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_not_between1_result3 = df_not_between1_result[(df_not_between1_result['HIS_3_END'] >= today)] #第3次未逾期(第2次未在長安領第3次只能來現場領)
			df_not_between1_result3.insert(9, '第三次慢箋預約日期','無法預約')
			df_not_between1_result4 = pd.concat([df_not_between1_result2, df_not_between1_result3], ignore_index=True)
			df_not_between1_result4.insert(10, '慢箋次數','3')       #4
			# print('第二次未在長安領，顯示第三次:')        
			# print(df_not_between1_result4)


			df_not_between2_result = df_not_between2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','最近領藥日','最近領藥號']]
			df_not_between2_result.insert(6, '第二次慢箋預約日期','已領取')

			df_not_between2_result2 = df_not_between2_result[(df_not_between2_result['HIS_3_END'] < today)] #第3次已逾期
			df_not_between2_result2.insert(9, '第三次慢箋預約日期','已逾期')
			df_not_between2_result3 = df_not_between2_result[(df_not_between2_result['HIS_3_END'] >= today)] #第3次未逾期(第二次延遲領)



			#----------------------------------------------------------------------------------------------------------------------------------
			#HIS API 未修改 (延遲領不能過API)
			# df_not_between2_result3.insert(9, '第三次慢箋預約日期','無法預約')
			#HIS API 已修改(延遲領可過API)
			df_not_between2_result3.insert(9, '第三次慢箋預約日期','可預約')
			#----------------------------------------------------------------------------------------------------------------------------------




			df_not_between2_result4 = pd.concat([df_not_between2_result2, df_not_between2_result3], ignore_index=True)
			df_not_between2_result4.insert(10, '慢箋次數','3')       #5
			# print('第二次延遲領，顯示第三次:')
			# print(df_not_between2_result4)


			#整合全部並格式整理
			#慢箋序號/科別名/看診日/醫師名字/第二次慢箋可預約日期/第二次慢箋預約日期/第三次慢箋可預約日期/第三次慢箋預約日期/第幾次慢箋預約
			data_all = pd.concat([data_info_all2_result4, data_info_all3_2_result,df_between_result4,df_not_between1_result4,df_not_between2_result4], ignore_index=True)
			data_all['HIS_2_START'] = pd.to_datetime(data_all['HIS_2_START'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['HIS_2_END'] = pd.to_datetime(data_all['HIS_2_END'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['看診日'] = pd.to_datetime(data_all['看診日'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['最近領藥日'] = pd.to_datetime(data_all['最近領藥日'], errors='coerce').dt.strftime('%Y%m%d')

			data_all['HIS_3_START'] = np.where(data_all['HIS_3_START'] == '無', '無', pd.to_datetime(data_all['HIS_3_START'], errors='coerce').dt.strftime('%Y-%m-%d'))
			data_all['HIS_3_END'] = np.where(data_all['HIS_3_END'] == '無', '無', pd.to_datetime(data_all['HIS_3_END'], errors='coerce').dt.strftime('%Y-%m-%d'))
			
			data_all = data_all.sort_values(by='看診日')
			# print(data_all)
			data_all_list = data_all.values.tolist() #轉成陣列
			# print("data_all_list:")
			# print(data_all_list)







			#查MSSQL的預約資料(找預約紀錄)
			result_data = AllCode.searchMssqlReserve(data_all_list)
			# result_data = [['0000462119', '內分泌新陳代謝科', '2024-11-30', '劉存鎮', '2024-12-17', '2024-12-30', '可預約', '2025-01-15', '2025-01-25', '未開放', '2']]

			#可預約日期區間統整(去除昨日之前/六日/跨週末問題/去除休診日，並處理過年提前領藥)
			date_choose = AllCode.reserveDate(result_data)
			# print('date_choose:')
			# print(date_choose)

			#API加回來要刪除---------------------------------------------------------------------------------------------------------------
			# for entry in date_choose:
			# 	if entry[13] != '無' and entry[13] != '已無法預約':
			# 		entry[13] = [AllCode.add_weekday(date) for date in entry[13]]
			# # print(date_choose)
			# check = date_choose
			#API加回來要刪除---------------------------------------------------------------------------------------------------------------

			#呼叫API確認是否可以預約+加入星期幾
			check = AllCode.checkApi(data_pd,date_choose)
			# print(check)


			#判斷預約日期是否可取消
			check2 = AllCode.cancelCheck(check)

			return data_pd,check2

	def searchChrocard3(pdnum): #找慢箋內容(病歷號new)
		# 身分證-----------------------------------------------------
		# #轉西元
		# year = int(birthday[:3]) + 1911
		# birthday_ad = f"{year}{birthday[3:]}"

		# pd_chdata = HisapiReserve.select_CHTPAT(pd_id,birthday_ad)
		# 身分證-----------------------------------------------------

		pd_chdata = HisapiReserve.select_CHTPAT2(pdnum) #病歷號
		if (len(pd_chdata) == 0):
			return '無此病患','','無'

		#抓今天日期
		today = AllCode.todateDate()
		# today = pd.to_datetime(today, format='%Y%m%d')
		# print(today)

		#搜尋慢箋
		# data = HisapiReserve.select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT3(pdnum,today)
		data = HisapiReserve.select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT4(pdnum,today)
		# print(data)

		today = pd.to_datetime(today, format='%Y%m%d') #轉換以便比較
		if (data == []):
			# print('有這個病人但沒有任何的預約慢箋')
			bir = datetime.strptime(pd_chdata[0][1], '%Y%m%d')

			#生日轉民國
			roc_year = bir.year - 1911
			roc_date_str = f"{roc_year:03d}{bir.month:02d}{bir.day:02d}"

			pd_chdata1 = list(map(list, pd_chdata))
			pd_chdata1[0][1] = roc_date_str
			pd_chdata1[0][4] = '女' if pd_chdata1[0][4] == 'F' else '男'

			return pd_chdata1,'','無'


		else:
			data_f = pd.DataFrame(data)
			data_f = data_f.rename(columns={0:'身分證',1:'生日',2:'名字',3:'病歷號',4:'性別',5:'住家電話',6:'行動電話',
											7:'慢箋序號',8:'科別名',9:'看診日',10:'醫師名',11:'批價次數',12:'最大批價次數',13:'最近領藥日',14:'慢箋結束日',15:'總天數',
											16:'HIS_2_START',17:'HIS_2_END',18:'HIS_3_START',19:'HIS_3_END',20:'醫令序號'})


			#個人資料-------------------------------------------------------------------------------------------------------------------
			data_pd = data_f[['身分證', '生日','名字','病歷號','性別','住家電話','行動電話']]

			data_pd = data_pd.copy()
			conditions = [data_pd['性別'] == 'M',data_pd['性別'] == 'F']
			choices = ['男', '女']
			data_pd['性別'] = np.select(conditions, choices, default='無')

			data_pd = data_pd.drop_duplicates() #去除重複
			data_pd['生日'] = data_pd['生日'].apply(lambda x: (str(int(x[:4]) - 1911) + x[4:]).zfill(7)) #生日轉民國

			# data_pd['住家電話'] = data_pd['住家電話'].str.replace(r'(\d{2})(\d{4})(\d+)', r'\1-\2-\3', regex=True)
			# data_pd['行動電話'] = data_pd['行動電話'].str.replace(r'(\d{4})(\d{3})(\d+)', r'\1-\2-\3', regex=True)

			data_pd = data_pd.values.tolist() #轉成陣列
			# print(data_pd)



			#慢箋資料整理-----------------------------------------------------------------------------------------------------------------
			data_info = data_f[['慢箋序號', '科別名','看診日','醫師名','批價次數','最大批價次數','最近領藥日','慢箋結束日','總天數','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號']]

			data_info = data_info.copy()
			# print(data_info)

			data_info['HIS_2_START'] = pd.to_datetime(data_info['HIS_2_START'], format='%Y%m%d')
			data_info['HIS_2_END'] = pd.to_datetime(data_info['HIS_2_END'], format='%Y%m%d')
			data_info['HIS_3_START'] = pd.to_datetime(data_info['HIS_3_START'], format='%Y%m%d')
			data_info['HIS_3_END'] = pd.to_datetime(data_info['HIS_3_END'], format='%Y%m%d')
			data_info['最近領藥日'] = pd.to_datetime(data_info['最近領藥日'], format='%Y%m%d')
			data_info['看診日'] = pd.to_datetime(data_info['看診日'], format='%Y%m%d')
			# print('data_info')
			# print(data_info)




			#判斷是否只有兩次慢箋
			data_info_all2 = data_info[data_info['最大批價次數'] == 2] #只有2次
			# print('data_info_all2:')
			# print(data_info_all2)

			if (len(data_info_all2) > 0):
				data_info_all2_result = data_info_all2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號']]
				data_info_all2_result = data_info_all2_result.copy()
				data_info_all2_result['HIS_3_START'] = '無'
				data_info_all2_result['HIS_3_END'] = '無'
				data_info_all2_result.insert(6, '第二次慢箋預約日期','可預約')
				data_info_all2_result.insert(9, '第三次慢箋預約日期','無')
				data_info_all2_result.insert(10, '慢箋次數','2')
				# print(data_info_all2_result)

				#判斷共2次是否已逾期
				data_info_all2_result2 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] < today)&(data_info_all2_result['醫令序號'] != "IC02")].copy() #第2次已逾期
				# print(type(data_info_all2_result2))
				data_info_all2_result2['第二次慢箋預約日期'] = '已逾期'
				data_info_all2_result3 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] >= today)&(data_info_all2_result['醫令序號'] != "IC02")].copy() #第2次未逾期(可預約不變)
				data_info_all2_result5 = data_info_all2_result[(data_info_all2_result['醫令序號'] == "IC02")] #第2次已領取
				data_info_all2_result5['第二次慢箋預約日期'] = '已領取'

				data_info_all2_result4 = pd.concat([data_info_all2_result2, data_info_all2_result3,data_info_all2_result5], ignore_index=True)

				data_info_all2_result4['補欄位'] = " " #以不要更動後面程式為主
				# print('共兩次最終結果:')
				# print(data_info_all2_result4)

			else:
				data_info_all2_result4 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','第二次慢箋預約日期','HIS_3_START','HIS_3_END','第三次慢箋預約日期','慢箋次數','醫令序號','補欄位'])



			data_info_all3 = data_info[data_info['最大批價次數'] > 2].copy()  #共有3次


			if (len(data_info_all3) > 0): #一共有3次慢箋
				data_info_all3_result = data_info_all3[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號']]
				# print(data_info_all3_result)
				data_info_all3_result = data_info_all3_result.copy()
				data_info_all3_result.insert(6, '第二次慢箋預約日期','可預約')
				data_info_all3_result.insert(9, '第三次慢箋預約日期','可預約')
				data_info_all3_result.insert(10, '慢箋次數','3')


				#情況一：2:可預約/3:未開放
				data_info_all3_result4 = data_info_all3_result[(data_info_all3_result['HIS_2_END'] >= today) & (data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03")].copy() #第2次未領
				data_info_all3_result4['第三次慢箋預約日期'] = '未開放'
				data_info_all3_result4['慢箋次數'] = '2'
				# print("data_info_all3_result4:")
				# print(data_info_all3_result4)                #1



				#情況二：2:已領取/3:已領取、可預約、已逾期
				#2-1:已領取/已領取
				data_info_all3_result2 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC03")].copy() #第2次/第3次都已領取
				data_info_all3_result2['第二次慢箋預約日期'] = '已領取'
				data_info_all3_result2['第三次慢箋預約日期'] = '已領取'
				# print(data_info_all3_result2)                          #2

				#2-2:已領取/可預約
				data_info_all3_result3 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC02") & (data_info_all3_result['HIS_3_END'] >= today)].copy() #第2次已領取/第3次可預約
				data_info_all3_result3['第二次慢箋預約日期'] = '已領取'
				# data_info_all3_result3 = data_info_all3_result3[(data_info_all3_result3['HIS_3_END'] >= today)].copy() #第3次可預約
				# print('data_info_all3_result3:')
				# print(data_info_all3_result3)               #3


				#2-3:已領取/已逾期
				data_info_all3_result5 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC02") & (data_info_all3_result['HIS_3_END'] < today)].copy() #第2次已領取/第3次已逾期
				data_info_all3_result5['第二次慢箋預約日期'] = '已領取'
				# data_info_all3_result5 = data_info_all3_result5[(data_info_all3_result5['HIS_3_END'] < today)].copy() #第3次已逾期
				data_info_all3_result5['第三次慢箋預約日期'] = '已逾期'
				# print(data_info_all3_result5)                 #4





				#情況三：2:已逾期/3:已逾期、無法預約、已領取
				#3-1:已逾期/已逾期
				data_info_all3_result6 = data_info_all3_result[(data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03") & (data_info_all3_result['HIS_2_END'] < today) & (data_info_all3_result['HIS_3_END'] < today)].copy()
				data_info_all3_result6['第二次慢箋預約日期'] = '已逾期'
				data_info_all3_result6['第三次慢箋預約日期'] = '已逾期'
				# print(data_info_all3_result6)                 #5


				#3-2:已逾期/無法預約
				data_info_all3_result7 = data_info_all3_result[(data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03") & (data_info_all3_result['HIS_2_END'] < today) & (data_info_all3_result['HIS_3_END'] >= today)].copy()
				data_info_all3_result7['第二次慢箋預約日期'] = '已逾期'
				data_info_all3_result7['第三次慢箋預約日期'] = '無法預約'
				# print(data_info_all3_result7)                 #6

				#3-3:已逾期/已領取
				#會直接變成已領取/已領取


				# data_info_all3_result = pd.concat([data_info_all3_result2, data_info_all3_result3], ignore_index=True)


				data_info_all3_resultall = pd.concat([data_info_all3_result4,data_info_all3_result2,data_info_all3_result3,data_info_all3_result5,data_info_all3_result6,data_info_all3_result7], ignore_index=True)
				data_info_all3_resultall['補欄位'] = " " #以不要更動後面程式為主
				# print("data_info_all3_resultall:")
				# print(data_info_all3_resultall)

			else:
				data_info_all3_resultall = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','第二次慢箋預約日期','HIS_3_START','HIS_3_END','第三次慢箋預約日期','慢箋次數','醫令序號','補欄位'])



			data_all = pd.concat([data_info_all2_result4,data_info_all3_resultall], ignore_index=True)
			data_all['HIS_2_START'] = pd.to_datetime(data_all['HIS_2_START'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['HIS_2_END'] = pd.to_datetime(data_all['HIS_2_END'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['看診日'] = pd.to_datetime(data_all['看診日'], errors='coerce').dt.strftime('%Y-%m-%d')
			# data_all['最近領藥日'] = pd.to_datetime(data_all['最近領藥日'], errors='coerce').dt.strftime('%Y%m%d')

			data_all['HIS_3_START'] = np.where(data_all['HIS_3_START'] == '無', '無', pd.to_datetime(data_all['HIS_3_START'], errors='coerce').dt.strftime('%Y-%m-%d'))
			data_all['HIS_3_END'] = np.where(data_all['HIS_3_END'] == '無', '無', pd.to_datetime(data_all['HIS_3_END'], errors='coerce').dt.strftime('%Y-%m-%d'))

			data_all = data_all.sort_values(by='看診日',ascending=False)
			# print(data_all)
			data_all_list = data_all.values.tolist() #轉成陣列
			# print("data_all_list:")
			# print(data_all_list)




			#查MSSQL的預約資料(找預約紀錄)/黑名單機制
			result_dataall = AllCode.searchMssqlReserve(data_pd,data_all_list)
			# print(result_data)
			result_data = result_dataall[0]
			breakdata = result_dataall[1]
			# print(breakdata)

			#可預約日期區間統整(去除昨日之前/六日/跨週末問題/去除休診日，並處理過年提前領藥)
			date_choose = AllCode.reserveDate(result_data)

			#呼叫API確認是否可以預約+加入星期幾
			check = AllCode.checkApi(data_pd,date_choose)
			print('123456')

			#判斷預約日期是否可取消
			check2 = AllCode.cancelCheck(check)

			return data_pd,check2,breakdata

	def searchChrocard_new(pd_id,birthday): #找慢箋內容 20250220改
		# 身分證-----------------------------------------------------
		#轉西元
		year = int(birthday[:3]) + 1911
		birthday_ad = f"{year}{birthday[3:]}"
		# 身分證-----------------------------------------------------

		# pd_chdata = HisapiReserve.select_CHTPAT2(pdnum) #病歷號
		pd_chdata = HisapiReserve.select_CHTPAT(pd_id,birthday_ad) #身分證
		if (len(pd_chdata) == 0):
			return '無此病患','','無','無'

		#抓今天日期
		today = AllCode.todateDate()

		#搜尋慢箋
		data = HisapiReserve.select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT4(pd_chdata[0][3],today)
		# print(data)

		today = pd.to_datetime(today, format='%Y%m%d') #轉換以便比較
		if (data == []):
			# print('有這個病人但沒有任何的預約慢箋')
			bir = datetime.strptime(pd_chdata[0][1], '%Y%m%d')

			#生日轉民國
			roc_year = bir.year - 1911
			roc_date_str = f"{roc_year:03d}{bir.month:02d}{bir.day:02d}"

			pd_chdata1 = list(map(list, pd_chdata))
			pd_chdata1[0][1] = roc_date_str
			pd_chdata1[0][4] = '女' if pd_chdata1[0][4] == 'F' else '男'

			return pd_chdata1,'','無','無'


		else:
			data_f = pd.DataFrame(data)
			data_f = data_f.rename(columns={0:'身分證',1:'生日',2:'名字',3:'病歷號',4:'性別',5:'住家電話',6:'行動電話',
											7:'慢箋序號',8:'科別名',9:'看診日',10:'醫師名',11:'批價次數',12:'最大批價次數',13:'最近領藥日',14:'慢箋結束日',15:'總天數',
											16:'HIS_2_START',17:'HIS_2_END',18:'HIS_3_START',19:'HIS_3_END',20:'醫令序號',21:'最近領藥號'})
			# print(data_f)

			#個人資料-------------------------------------------------------------------------------------------------------------------
			data_pd = data_f[['身分證', '生日','名字','病歷號','性別','住家電話','行動電話']]

			data_pd = data_pd.copy()
			conditions = [data_pd['性別'] == 'M',data_pd['性別'] == 'F']
			choices = ['男', '女']
			data_pd['性別'] = np.select(conditions, choices, default='無')

			data_pd = data_pd.drop_duplicates() #去除重複
			data_pd['生日'] = data_pd['生日'].apply(lambda x: (str(int(x[:4]) - 1911) + x[4:]).zfill(7)) #生日轉民國

			data_pd = data_pd.values.tolist() #轉成陣列
			# print(data_pd)



			#慢箋資料整理-----------------------------------------------------------------------------------------------------------------
			data_info = data_f[['慢箋序號', '科別名','看診日','醫師名','批價次數','最大批價次數','最近領藥日','慢箋結束日','總天數','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號','最近領藥號']]

			data_info = data_info.copy()
			# print(data_info)

			data_info['HIS_2_START'] = pd.to_datetime(data_info['HIS_2_START'], format='%Y%m%d')
			data_info['HIS_2_END'] = pd.to_datetime(data_info['HIS_2_END'], format='%Y%m%d')
			data_info['HIS_3_START'] = pd.to_datetime(data_info['HIS_3_START'], format='%Y%m%d')
			data_info['HIS_3_END'] = pd.to_datetime(data_info['HIS_3_END'], format='%Y%m%d')
			data_info['最近領藥日'] = pd.to_datetime(data_info['最近領藥日'], format='%Y%m%d')
			data_info['看診日'] = pd.to_datetime(data_info['看診日'], format='%Y%m%d')
			# print('data_info')
			# print(data_info)




			#判斷是否只有兩次慢箋
			data_info_all2 = data_info[data_info['最大批價次數'] == 2] #只有2次
			# print('data_info_all2:')
			# print(data_info_all2)

			if (len(data_info_all2) > 0):
				data_info_all2_result = data_info_all2[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號','最近領藥日','最近領藥號']]
				data_info_all2_result = data_info_all2_result.copy()
				data_info_all2_result['HIS_3_START'] = '無'
				data_info_all2_result['HIS_3_END'] = '無'
				data_info_all2_result.insert(6, '第二次慢箋預約日期','可預約')
				data_info_all2_result.insert(9, '第三次慢箋預約日期','無')
				data_info_all2_result.insert(10, '慢箋次數','2')
				# print(data_info_all2_result)

				#判斷共2次是否已逾期
				data_info_all2_result2 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] < today)&(data_info_all2_result['醫令序號'] != "IC02")].copy() #第2次已逾期
				# print(type(data_info_all2_result2))
				data_info_all2_result2['第二次慢箋預約日期'] = '已逾期'
				data_info_all2_result3 = data_info_all2_result[(data_info_all2_result['HIS_2_END'] >= today)&(data_info_all2_result['醫令序號'] != "IC02")].copy() #第2次未逾期(可預約不變)
				data_info_all2_result5 = data_info_all2_result[(data_info_all2_result['醫令序號'] == "IC02")] #第2次已領取
				data_info_all2_result5['第二次慢箋預約日期'] = '已領取'

				data_info_all2_result4 = pd.concat([data_info_all2_result2, data_info_all2_result3,data_info_all2_result5], ignore_index=True)

				# data_info_all2_result4['補欄位'] = " " #以不要更動後面程式為主
				data_info_all2_result4 = data_info_all2_result4.drop(columns=['醫令序號']) #以不要更動後面程式為主
				# print('共兩次最終結果:')
				# print(data_info_all2_result4)

			else:
				data_info_all2_result4 = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','第二次慢箋預約日期','HIS_3_START','HIS_3_END','第三次慢箋預約日期','慢箋次數','最近領藥日','最近領藥號'])



			data_info_all3 = data_info[data_info['最大批價次數'] > 2].copy()  #共有3次


			if (len(data_info_all3) > 0): #一共有3次慢箋
				data_info_all3_result = data_info_all3[['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','HIS_3_START','HIS_3_END','醫令序號','最近領藥日','最近領藥號']]
				# print(data_info_all3_result)
				data_info_all3_result = data_info_all3_result.copy()
				data_info_all3_result.insert(6, '第二次慢箋預約日期','可預約')
				data_info_all3_result.insert(9, '第三次慢箋預約日期','可預約')
				data_info_all3_result.insert(10, '慢箋次數','3')


				#情況一：2:可預約/3:未開放
				data_info_all3_result4 = data_info_all3_result[(data_info_all3_result['HIS_2_END'] >= today) & (data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03")].copy() #第2次未領
				data_info_all3_result4['第三次慢箋預約日期'] = '未開放'
				data_info_all3_result4['慢箋次數'] = '2'
				# print("data_info_all3_result4:")
				# print(data_info_all3_result4)                #1



				#情況二：2:已領取/3:已領取、可預約、已逾期
				#2-1:已領取/已領取
				data_info_all3_result2 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC03")].copy() #第2次/第3次都已領取
				data_info_all3_result2['第二次慢箋預約日期'] = '已領取'
				data_info_all3_result2['第三次慢箋預約日期'] = '已領取'
				# print(data_info_all3_result2)                          #2

				#2-2:已領取/可預約
				data_info_all3_result3 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC02") & (data_info_all3_result['HIS_3_END'] >= today)].copy() #第2次已領取/第3次可預約
				data_info_all3_result3['第二次慢箋預約日期'] = '已領取'
				# data_info_all3_result3 = data_info_all3_result3[(data_info_all3_result3['HIS_3_END'] >= today)].copy() #第3次可預約
				# print('data_info_all3_result3:')
				# print(data_info_all3_result3)               #3


				#2-3:已領取/已逾期
				data_info_all3_result5 = data_info_all3_result[(data_info_all3_result['醫令序號'] == "IC02") & (data_info_all3_result['HIS_3_END'] < today)].copy() #第2次已領取/第3次已逾期
				data_info_all3_result5['第二次慢箋預約日期'] = '已領取'
				# data_info_all3_result5 = data_info_all3_result5[(data_info_all3_result5['HIS_3_END'] < today)].copy() #第3次已逾期
				data_info_all3_result5['第三次慢箋預約日期'] = '已逾期'
				# print(data_info_all3_result5)                 #4





				#情況三：2:已逾期/3:已逾期、無法預約、已領取
				#3-1:已逾期/已逾期
				data_info_all3_result6 = data_info_all3_result[(data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03") & (data_info_all3_result['HIS_2_END'] < today) & (data_info_all3_result['HIS_3_END'] < today)].copy()
				data_info_all3_result6['第二次慢箋預約日期'] = '已逾期'
				data_info_all3_result6['第三次慢箋預約日期'] = '已逾期'
				# print(data_info_all3_result6)                 #5


				#3-2:已逾期/無法預約
				data_info_all3_result7 = data_info_all3_result[(data_info_all3_result['醫令序號'] != "IC02") & (data_info_all3_result['醫令序號'] != "IC03") & (data_info_all3_result['HIS_2_END'] < today) & (data_info_all3_result['HIS_3_END'] >= today)].copy()
				data_info_all3_result7['第二次慢箋預約日期'] = '已逾期'
				data_info_all3_result7['第三次慢箋預約日期'] = '無法預約'
				# print(data_info_all3_result7)                 #6

				#3-3:已逾期/已領取
				#會直接變成已領取/已領取


				# data_info_all3_result = pd.concat([data_info_all3_result2, data_info_all3_result3], ignore_index=True)


				data_info_all3_resultall = pd.concat([data_info_all3_result4,data_info_all3_result2,data_info_all3_result3,data_info_all3_result5,data_info_all3_result6,data_info_all3_result7], ignore_index=True)
				# data_info_all3_resultall['補欄位'] = " " #以不要更動後面程式為主
				data_info_all3_resultall = data_info_all3_resultall.drop(columns=['醫令序號']) #以不要更動後面程式為主
				# print("data_info_all3_resultall:")
				# print(data_info_all3_resultall)

			else:
				data_info_all3_resultall = pd.DataFrame(columns=['慢箋序號', '科別名','看診日','醫師名','HIS_2_START','HIS_2_END','第二次慢箋預約日期','HIS_3_START','HIS_3_END','第三次慢箋預約日期','慢箋次數','最近領藥日','最近領藥號'])



			data_all = pd.concat([data_info_all2_result4,data_info_all3_resultall], ignore_index=True)
			data_all['HIS_2_START'] = pd.to_datetime(data_all['HIS_2_START'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['HIS_2_END'] = pd.to_datetime(data_all['HIS_2_END'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['看診日'] = pd.to_datetime(data_all['看診日'], errors='coerce').dt.strftime('%Y-%m-%d')
			data_all['最近領藥日'] = pd.to_datetime(data_all['最近領藥日'], errors='coerce').dt.strftime('%Y%m%d')

			data_all['HIS_3_START'] = np.where(data_all['HIS_3_START'] == '無', '無', pd.to_datetime(data_all['HIS_3_START'], errors='coerce').dt.strftime('%Y-%m-%d'))
			data_all['HIS_3_END'] = np.where(data_all['HIS_3_END'] == '無', '無', pd.to_datetime(data_all['HIS_3_END'], errors='coerce').dt.strftime('%Y-%m-%d'))

			data_all = data_all.sort_values(by='看診日',ascending=False)
			# print(data_all)
			data_all_list = data_all.values.tolist() #轉成陣列
			# print("data_all_list:")
			# print(data_all_list)




			#查MSSQL的預約資料(找預約紀錄)/黑名單機制
			result_dataall = AllCode.searchMssqlReserve(data_pd,data_all_list)
			# print('result_dataall')
			# print(result_dataall)
			result_data = result_dataall[0]
			breakdata = result_dataall[1]
			stop_date = result_dataall[2]
			# print(breakdata)

			#可預約日期區間統整(去除昨日之前/六日/跨週末問題/去除休診日，並處理過年提前領藥)
			date_choose = AllCode.reserveDate(result_data)
			# print('date_choose')
			# print(date_choose)

			#呼叫API確認是否可以預約+加入星期幾
			check = AllCode.checkApi(data_pd,date_choose)

			#判斷預約日期是否可取消
			check2 = AllCode.cancelCheck(check)

			return data_pd,check2,breakdata,stop_date

	def searchMssqlReserve(data_pd,data): #找預約紀錄/黑名單機制
		weekdays = ['一', '二', '三', '四', '五', '六', '日']
		today = datetime.today().strftime('%Y-%m-%d')
		todayformat = datetime.today().strftime('%Y%m%d')

		breakdata = '無' #預設沒有黑名單
		stop_date = '無'

		dataarray = np.array(data)
		contains_target = np.char.find(dataarray, '可預約') >= 0

		#有任何可預約的欄位→找是否已有預約日期
		if (contains_target.any() == True):
			for d in data:
				re_data2 = []
				re_data3 = []

				# if (d[resno_times] == '2'and d[HIS_2_END] == today): #可預約的第二次結束日在今日找尋是否有期間預約紀錄→有就顯示
				# 	re_data2 = MssqlApiReserve.select_reserve_pre_list(d[chroard],d[resno_times]) #找預約紀錄

				# elif (d[resno_times] == '3'and d[third_END] == today):#可預約的第三次結束日在今日找尋是否有期間預約紀錄→有就顯示
				# 	re_data3 = MssqlApiReserve.select_reserve_pre_list(d[chroard],d[resno_times]) #找預約紀錄

				if (d[reserve_2] =='可預約'): #其他條件的第二次可預約
					re_data2 = MssqlApiReserve.select_reserve_pre_list(d[chroard],d[resno_times],todayformat) #找預約紀錄

				if (d[reserve_3] =='可預約'): #其他條件的第三次可預約
					# print('12123')
					re_data3 = MssqlApiReserve.select_reserve_pre_list(d[chroard],d[resno_times],todayformat) #找預約紀錄
					# print(re_data3)



				if (len(re_data2) != 0): #表示已有預約紀錄
					d[reserve_2] = re_data2[0][0]
					d[reserve_2] = f"{d[reserve_2][:4]}-{d[reserve_2][4:6]}-{d[reserve_2][6:]}" #格式調整
					d[reserve_2] = f"{d[reserve_2]} ({weekdays[datetime.strptime(d[reserve_2], '%Y-%m-%d').weekday()]})" #加上星期

				elif (len(re_data3) != 0): #表示已有預約紀錄
					d[reserve_3] = re_data3[0][0]
					d[reserve_3] = f"{d[reserve_3][:4]}-{d[reserve_3][4:6]}-{d[reserve_3][6:]}"
					d[reserve_3] = f"{d[reserve_3]} ({weekdays[datetime.strptime(d[reserve_3], '%Y-%m-%d').weekday()]})" #加上星期



		#有任何可預約的欄位→黑名單判斷
		if (contains_target.any() == True):
			#黑名單------------------------------------------------------------------------------------------------------
			break_date = AllCode.breakDate() #找56天前日期
			reserve = MssqlApiReserve.select_reserve_pre_list3_new(data_pd[0][3],break_date,todayformat) #民眾預約56天前資料
			reservelist = list({(x[0], x[1],x[2]) for x in reserve})
			# print(reservelist)

			actual = []
			for re in reservelist:
				# print(re)
				actualdata = HisapiReserve.select_OPDCRO_OPDVCB(re[1],re[2],data_pd[0][3]) #實際領取日期資料
				# print(actualdata)

				if (len(actualdata) > 0):
					actual.extend(actualdata)

				else:#實際上還沒領，實際領取帶入今天日期
					# actual.extend([(re[0],re[1],re[2],todayformat)])
					actual.extend([(re[0],re[1],re[2],'未領')])

			if (len(reserve) > 0): #有之前預約紀錄才要判斷是否為黑名單
				actual = pd.DataFrame(actual)
				reserve = pd.DataFrame(reserve)

				actual = actual.rename(columns={0:"科別",1:"慢箋單號",2:"慢箋次數",3:"實際日期"})
				reserve = reserve.rename(columns={0:"科別",1:"慢箋單號",2:"慢箋次數",3:"預約日期"})
				merge1 = pd.merge(reserve, actual, on=['科別','慢箋單號','慢箋次數'], how='left')
				# print(merge1)

				breakdata = merge1[(merge1["實際日期"]>merge1["預約日期"]) | (merge1['實際日期'] == '未領')] #實際日期要大於預約日期
				# print(breakdata)
				# print(len(breakdata))

				#有爽約紀錄
				if (len(breakdata) > 0):
					breakdata = breakdata.values.tolist() #轉成陣列

				#無爽約紀錄
				else:
					breakdata = '無'


				#爽約超過3次，是黑名單 > 無法預約
				if (len(breakdata) >= 3):
					#將第一筆為最早的預約日期往後加57天(算出解除黑名單的日期)-------------------------------------
					date_obj = datetime.strptime(breakdata[0][3], "%Y%m%d")
					new_date_obj = date_obj + timedelta(days=57)
					stop_date = new_date_obj.strftime("%Y/%m/%d")
					#將第一筆為最早的預約日期往後加57天(算出解除黑名單的日期)-------------------------------------

					for d in data:
						if (d[reserve_2] =='可預約'):
								d[reserve_2] = '無法預約'

						elif (d[reserve_3] =='可預約'):
							d[reserve_3] = '無法預約'

					return data,breakdata,stop_date

			# print(breakdata)
			#黑名單------------------------------------------------------------------------------------------------------

		# print(data)
		return data,breakdata,stop_date

	def reserveDate(data): #可預約日期區間統整(去除昨日之前/六日/跨週末問題/去除休診日，並處理過年提前領藥)
		#過年參數提取-----------------------------------------------------------
		newyear = HisapiReserve.select_BASCODE() #過年提早領取參數
		# newyear = [('20250101;20250107;20241220',)] #假設
		# print(newyear)
		newyear = [item.split(';') for item in newyear[0]]
		date1 = newyear[0][0]
		date2 = newyear[0][1]
		date1 = datetime.strptime(date1, '%Y%m%d')
		date2 = datetime.strptime(date2, '%Y%m%d')
		#過年參數提取-----------------------------------------------------------


		#休診日參數提取-------------------------------------------------------------
		close = MssqlApiReserve.select_reserve_pre_closeday() #休診日
		#休診日參數提取-------------------------------------------------------------

		data1 = []
		for d in data:
			if (d[reserve_2] =='可預約'): #第二次可預約
				start = d[HIS_2_START]
				end = d[HIS_2_END]
				remark = '有'

			elif (d[reserve_3] =='可預約'): #第三次可預約
				start = d[third_START]
				end = d[third_END]
				remark = '有'

			else:
				remark = '無'



			if (remark == '有'): #日期區間整理
				today = datetime.today().strftime('%Y-%m-%d')
				# today = '2024-12-11'
		
				if (d[resno_times] == '2'and d[HIS_2_END] == today) or (d[resno_times] == '3'and d[third_END] == today): #可預約的第二三次結束日在今日
					date_list = '已無法預約'
					d.append(date_list)
					data1.append(d)

				else:

					#判斷過年提早領------------------------------------------------------------------------------------------
					end2 = datetime.strptime(end, '%Y-%m-%d')

					# 檢查 end 是否在 date1 和 date2 之間
					if date1 <= end2 <= date2:
						#是在過年可提早領期間，將start日期改成提早的日期
						start_new = datetime.strptime(newyear[0][2], '%Y%m%d')
						start = start_new.strftime('%Y-%m-%d')

						if (d[reserve_2] =='可預約'): #第二次可預約
							d[HIS_2_START] = start

						else: #第三次可預約
							d[third_START] = start

					# else:
					# 	print("不在過年期間不做事")
					#判斷過年提早領------------------------------------------------------------------------------------------



					now = datetime.now()
					# now = datetime(2024, 12, 17, 17, 0)  # 假設

					start_date = datetime.strptime(str(start), "%Y-%m-%d")
					end_date = datetime.strptime(str(end), "%Y-%m-%d")


					#步驟一:如果start_date為六日→延到下個周一
					if (start_date.weekday() == 5): #星期六
						start_date += timedelta(days=2)

					elif (start_date.weekday() == 6): #星期日
						start_date += timedelta(days=1)


					# 步驟二:(1)現在<開始日期
					if now.date() < start_date.date():

						#如果start_date為星期二~星期五
						if (start_date.weekday() == 1) or (start_date.weekday() == 2) or (start_date.weekday() == 3) or (start_date.weekday() == 4):
							#開始日期是否為隔天
							if start_date.date() == (now + timedelta(days=1)).date():
								if now.hour >= 17:
									start_date = now + timedelta(days=2) #後天

						#如果start_date為星期一
						elif (start_date.weekday() == 0):
							#是否為星期五六日
							if (now.weekday() == 4) or (now.weekday() == 5) or (now.weekday() == 6):
								#計算下一個週一日期
								day_next = (7 - now.weekday()) % 7 or 7
								next_monday = now.date() + timedelta(days=day_next)

								#判斷是否為下一個週一
								if (next_monday == start_date.date()):
									if (now.weekday() == 4): #星期五
										if now.hour >= 17:
											start_date = start_date + timedelta(days=1) #start_date為星期一→週二開始

									if (now.weekday() == 5) or (now.weekday() == 6): #星期六日
										start_date = start_date + timedelta(days=1) #start_date為星期一→週二開始

					# 步驟二:(2)開始<=現在<結束
					elif start_date.date() <= now.date() < end_date.date():
						if (now.weekday() <= 3): #現在星期一~星期四
							if now.hour >= 17:
								start_date = now + timedelta(days=2)  #如果當前時間已經過 17:00，開始日期是後天

							else:
								start_date = now + timedelta(days=1)  #否則跳過今天，開始日期是明天

						elif (now.weekday() == 5): #現在星期六
							start_date = now + timedelta(days=3) #start_date=下周二

						elif (now.weekday() == 6):#現在星期日
							start_date = now + timedelta(days=2) #start_date=下周二

						elif (now.weekday() == 4): #現在星期五
							if now.hour >= 17:
								start_date = now + timedelta(days=4)  #start_date=下周二

							else:
								start_date = now + timedelta(days=3)  #start_date=下周一


					if start_date.date() > end_date.date():
						date_list = '已無法預約'
						d.append(date_list)
						data1.append(d)
						# return data1
						continue #不會執行以下內容直接跳入下個迴圈


					# 步驟三:生成日期範圍，排除周六和周日，並確保包括结束日期
					date_list = []
					current_date = start_date

					# 使用 while 循环生成日期，並確保包括结束日期
					while current_date <= end_date:
						if current_date.weekday() not in [5, 6]:  # 排除周六(5)和周日(6)
							date_list.append(current_date.strftime("%Y-%m-%d"))
						current_date += timedelta(days=1)

					# 確保結束日期只被添加一次，檢查結束日期是否已經在列表中
					if end_date.weekday() not in [5, 6] and end_date.strftime("%Y-%m-%d") not in date_list:
						date_list.append(end_date.strftime("%Y-%m-%d"))


					#去除休診日---------------------------------------------------------------------------------------
					close2 = {f"{date[0][:4]}-{date[0][4:6]}-{date[0][6:]}" for date in close} #格式轉換

					overlap = close2 & set(date_list) #先檢查有沒有重複
					
					if overlap: #有重複就過濾
						close_result = [date for date in date_list if date not in close2]
						d.append(close_result)
						data1.append(d)
					else:
						d.append(date_list)
						data1.append(d)
					#去除休診日---------------------------------------------------------------------------------------

			else:
				date_list = '無'
				d.append(date_list)
				data1.append(d)

		# print(data1)
		return data1

	def checkApi(data_pd,date_choose): #Check API是否可預約
		#生日民國改西元年
		year = str(1911 + int(data_pd[0][1][:3]))
		birthday = year + data_pd[0][1][3:]

		date_choose2 = date_choose
		number = 0

		for data in date_choose2:
			predate = ''
			afterdate = ''
			alertword = '無'

			if (data[datecolumn] != '無' and data[datecolumn] != '已無法預約'):
				CRR_CROTIMES = data[10] #慢箋次數
				ID_BIRTHDATE = birthday
				ID_CHROCARD = data[0]#慢箋序號
				ID_NUMBER = data_pd[0][0]#身分證

				date_array = [date.split(' ')[0].replace('-', '') for date in data[datecolumn]]
				date1 = date_array
				date2 = date_array[::-1] #倒過來的

				for date1day in date1: #檢查最前面日期
					CRR_RESDT = date1day #預約日期
					
					api_data = {
					"CRR_CROTIMES":CRR_CROTIMES,
					"CRR_RESDT": CRR_RESDT,
					"Functionname": "CheckChronicData",
					"ID_BIRTHDATE": ID_BIRTHDATE,
					"ID_CHROCARD": ID_CHROCARD,
					"ID_NUMBER": ID_NUMBER,
					"WS_CALL_IP": '192.168.51.76'
					}
					# print(api_data)

					json_data = json.dumps(api_data)
					base64_data = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")


					url = f"http://192.168.200.215/webap/WebService.asmx/HISAPI?_Str={base64_data}"
					response = requests.get(url)

					json_string = re.search(r'<string[^>]*>(.*?)</string>', response.text, re.DOTALL).group(1)
					api_data = json.loads(json_string)


					if (api_data['SUCCESS'] == 'Y'): #能夠預約
						predate = date1day
						break
					else:
						big5_text = base64.b64decode(api_data['s_Response']).decode('big5')
						if (big5_text == '本次處方有部分藥品停用或缺貨，請洽服務櫃台確認，謝謝。'):
							alertword = '抱歉！因處方中有藥品為停用狀態，無法預約，再請至本院批掛櫃檯辦理。'
							break
				
				for date2day in date2: #檢查最後面日期
					CRR_RESDT = date2day #預約日期
					
					api_data = {
					"CRR_CROTIMES":CRR_CROTIMES,
					"CRR_RESDT": CRR_RESDT,
					"Functionname": "CheckChronicData",
					"ID_BIRTHDATE": ID_BIRTHDATE,
					"ID_CHROCARD": ID_CHROCARD,
					"ID_NUMBER": ID_NUMBER,
					"WS_CALL_IP": '192.168.51.76'
					}
					# print(api_data)

					json_data = json.dumps(api_data)
					base64_data = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")


					url = f"http://192.168.200.215/webap/WebService.asmx/HISAPI?_Str={base64_data}"
					response = requests.get(url)

					json_string = re.search(r'<string[^>]*>(.*?)</string>', response.text, re.DOTALL).group(1)
					api_data = json.loads(json_string)


					if (api_data['SUCCESS'] == 'Y'): #能夠預約
						afterdate = date2day
						break
					else:
						big5_text = base64.b64decode(api_data['s_Response']).decode('big5')
						if (big5_text == '本次處方有部分藥品停用或缺貨，請洽服務櫃台確認，謝謝。'):
							alertword = '抱歉！因處方中有藥品為停用狀態，無法預約，再請至本院批掛櫃檯辦理。'
							break
	


				if (predate == '' and afterdate == ''):
					date_choose[number][datecolumn] = ''
					if (alertword == '抱歉！因處方中有藥品為停用狀態，無法預約，再請至本院批掛櫃檯辦理。'):
						date_choose[number].append(alertword)
				else:
					start_index = date_array.index(predate)
					end_index = date_array.index(afterdate)
					result = date_array[start_index:end_index + 1]

					#更改星期格式
					weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
					result = [f"{date} ({weekdays[datetime.strptime(date, '%Y%m%d').weekday()]})" for date in result]
					result = [f"{item[:4]}-{item[4:6]}-{item[6:8]}{item[8:]}" for item in result]

					date_choose[number][datecolumn] = result
					date_choose[number].append(alertword)

			number = number + 1

		return date_choose

	def cancelCheck(data): #判斷預約日期是否可取消
		i = 0
		for da in data:
			result = '無'
			try:
				datetime.strptime(da[reserve_2][:10], '%Y-%m-%d')  # 嘗試解析日期部分
				# print('第二次是日期')

				date_str = da[reserve_2][:10]
				# date_str = '2024-12-23' #目標日期

				target_date = datetime.strptime(date_str, "%Y-%m-%d")  # 目標日期（整天）
				target_date_only = target_date.date()  # 只取目標日期的部分（去掉時間）


				now = datetime.now()
				# now = datetime(2024, 12, 22, 0, 0, 0)
				# print(now.weekday)


				# 判斷是否是可取消的情況
				if target_date_only  < now.date():  # 目標日期早於現在日期
					result = "不可取消"

				elif target_date_only  == now.date():  # 目標日期等於今天
					result = "不可取消"

				elif (target_date_only  == (now + timedelta(days=1)).date() and (now.weekday() != 6)):  # 目標日期是明天且今天不是星期日
					if now.hour < 17:  # 當前時間在17:00之前
						result = "可取消"
					else:  # 當前時間在17:00之後
						result = "不可取消"

				elif (target_date_only  == (now + timedelta(days=1)).date() and (now.weekday() == 6)):  # 目標日期是明天且今天是星期日
					result = "不可取消"

				else: #目標日期是明天過後的日期

					if now.weekday() == 4:  #表示星期五
						if (target_date_only == now.date() + timedelta(days=3)): #目標日期是下個星期一
							if now.hour < 17: #當前時間在17:00之前
								result = "可取消"
							else:  #當前時間在17:00之後
								result = "不可取消"
						else:
							result = "可取消"

					elif now.weekday() == 5: #表示星期六
						if (target_date_only == now.date() + timedelta(days=2)): #目標日期是下個星期一
							result = "不可取消"
						else:
							result = "可取消"
					else:
						result = "可取消"

				data[i].append(result) 

			except ValueError: #第二次不是日期
				pass


			try:
				datetime.strptime(da[reserve_3][:10], '%Y-%m-%d')  # 嘗試解析日期部分

				date_str = da[reserve_3][:10]
				target_date = datetime.strptime(date_str, "%Y-%m-%d")  # 目標日期（整天）
				target_date_only = target_date.date()  # 只取目標日期的部分（去掉時間）

				now = datetime.now()

				# 判斷是否是可取消的情況
				if target_date_only  < now.date():  # 目標日期早於現在日期
					result = "不可取消"

				elif target_date_only  == now.date():  # 目標日期等於今天
					result = "不可取消"

				elif (target_date_only  == (now + timedelta(days=1)).date() and (now.weekday() != 6)):  # 目標日期是明天且今天不是星期日
					if now.hour < 17:  # 當前時間在17:00之前
						result = "可取消"
					else:  # 當前時間在17:00之後
						result = "不可取消"

				elif (target_date_only  == (now + timedelta(days=1)).date() and (now.weekday() == 6)):  # 目標日期是明天且今天是星期日
					result = "不可取消"

				else: #目標日期是明天過後的日期

					if now.weekday() == 4:  #表示星期五
						if (target_date_only == now.date() + timedelta(days=3)): #目標日期是下個星期一
							if now.hour < 17: #當前時間在17:00之前
								result = "可取消"
							else:  #當前時間在17:00之後
								result = "不可取消"
						else:
							result = "可取消"

					elif now.weekday() == 5: #表示星期六
						if (target_date_only == now.date() + timedelta(days=2)): #目標日期是下個星期一
							result = "不可取消"
						else:
							result = "可取消"
					else:
						result = "可取消"


				data[i].append(result)

			except ValueError: #第三次不是日期
				pass

			i = i + 1

		return data

	def reserve(pd_info,data_info,values): #預約
		result = values.split('$')
		reserve_date = result[1]     #要預約的預約日期
		chrocard = result[2]         #要預約的慢箋單號

		reserve_date = reserve_date.split(' ')[0].replace('-', '')
		# print(reserve_date)

		#確保現在可以預約----------------------------------------------------
		reserve_date2 = datetime.strptime(reserve_date, '%Y%m%d') #目標日期

		# 獲取系統當前日期和時間
		now = datetime.now()
		# now = datetime(2024, 12, 26, 17, 0) #自己假設現在日期時間(年,月,日,時,秒)
		new_date = now.date()  # 提取當前日期（不包含時間)


		if reserve_date2.date() <= new_date:
			return '不可預約'

		# 計算明天的日期
		tomorrow = new_date + timedelta(days=1)

		# 是明天以後的日期
		if reserve_date2.date() > tomorrow:
			re_result = '可預約'

		# 是明天
		if reserve_date2.date() == tomorrow:
			if now.hour < 17:
				re_result = '可預約'
			else:
				return '不可預約'
		#確保現在可以預約----------------------------------------------------


		re_data = []
		# print(data_info)

		for info in data_info:
			if (info[0] == chrocard):
				re_data = info
				break

		re_data2 = re_data.copy()

		#生日 民國轉西元--------------------------------------------------
		roc_date = pd_info[0][1]
		# 轉換民國年為西元年
		roc_year = int(roc_date[:3]) + 1911  # 民國年是前三位數
		western_date = str(roc_year) + roc_date[3:]  # 替換掉年並保留月日
		# 更新 a 列表
		pd_info[0][1] = western_date
		#生日 民國轉西元--------------------------------------------------


		#預約日期統整----------------------------------------------------------------
		# print(reserve_date)
		roc_date = str(int(reserve_date[:4]) - 1911) + '/' + reserve_date[4:6] + '/' + reserve_date[6:]

		date_obj = datetime.strptime(str(reserve_date), "%Y%m%d")
		formatted_date = date_obj.strftime("%Y-%m-%d") + f" ({'一二三四五六日'[date_obj.weekday()]})"
		reserve_date = [reserve_date, roc_date,formatted_date]
		#預約日期統整----------------------------------------------------------------

		re_data[2] = re_data[2].replace('-', '') #看診日格式調整

		today = AllCode.todateDate()
		if (reserve_date[0] <= '20250331'):
			# print('2025/4/1前')
			result = MssqlApiReserve.insert_reserve_pre_list(pd_info,re_data,reserve_date,today) #預約(病人資料/慢箋資料/預約日期)
		else:
			result = MssqlApiReserve.insert_reserve_pre_list2(pd_info,re_data,reserve_date,today) #預約(病人資料/慢箋資料/預約日期)


		if (re_data2[resno_times] == '2'): #預約第二次
			re_data2[reserve_2] = reserve_date[2]
		else: #預約第三次
			re_data2[reserve_3] = reserve_date[2]

		data_info_new = [re_data2 if row[0] == re_data2[0] else row for row in data_info]

		data_info_new2 = AllCode.cancelCheck(data_info_new) #判斷預約日期是否可取消
		# breakdata = '無'
		return data_info_new2

	def cancelReserve(pd_info,data_info,values): #取消預約
		result = values.split('$')
		chrocard = result[1]
		resno_times = result[2]
		orginal = result[3]


		# 確保當下可取消------------------------------------------------------
		orginal2 = orginal.split(' ')[0]  # 只取 '2024-12-27'
		reserve_date2 = datetime.strptime(orginal2, '%Y-%m-%d') #目標日期

		# 獲取系統當前日期和時間
		now = datetime.now()
		# now = datetime(2025, 1, 3, 17, 0) #自己假設現在日期時間(年,月,日,時,秒)


		if reserve_date2.date() < now.date():  # 目標日期早於現在日期
			return "不可取消"

		elif reserve_date2.date() == now.date():  # 目標日期等於今天
			return "不可取消"

		elif (reserve_date2.date() == (now + timedelta(days=1)).date() and (now.weekday() != 6)):  # 目標日期是明天且今天不是星期日
			if now.hour < 17:  # 當前時間在17:00之前
				cancel_result = "可取消"
			else:  # 當前時間在17:00之後
				return "不可取消"

		elif (reserve_date2.date() == (now + timedelta(days=1)).date() and (now.weekday() == 6)):  # 目標日期是明天且今天是星期日
			return "不可取消"

		else: #目標日期是明天過後的日期

			if now.weekday() == 4:  #表示星期五
				if (reserve_date2.date() == now.date() + timedelta(days=3)): #目標日期是下個星期一
					if now.hour < 17: #當前時間在17:00之前
						cancel_result = "可取消"
					else:  #當前時間在17:00之後
						return "不可取消"
				else:
					cancel_result = "可取消"

			elif now.weekday() == 5: #表示星期六
				if (reserve_date2.date() == now.date() + timedelta(days=2)): #目標日期是下個星期一
					return "不可取消"
				else:
					cancel_result = "可取消"
			else:
				cancel_result = "可取消"
		# 確保當下可取消------------------------------------------------------


		current_time = datetime.now()
		cancel_datetime = current_time.strftime("%Y%m%d%H%M%S")
		today = AllCode.todateDate()
		data = MssqlApiReserve.update_reserve_pre_list(cancel_datetime,chrocard,resno_times,today) #取消

		newdata = AllCode.searchChrocard_new(pd_info[0][0],pd_info[0][1]) #改為身分證
		# newdata = AllCode.searchChrocard_new(pd_info[0][3]) #病歷號
		return newdata

	def add_weekday(date_str): #跳過API時的星期判斷
		weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
		weekday = datetime.strptime(date_str, "%Y-%m-%d").weekday()
		return f"{date_str} ({weekdays[weekday]})"









	#目前沒用到------------------------------------------------------------------------------------------------------------------------------
	def apiDatanumber(CRR_CROTIMES,ID_BIRTHDATE,ID_CHROCARD,ID_NUMBER,date_array,data): #API詳細確認
		date_result = []
		number = 0

		for re_date in date_array:
			CRR_RESDT = re_date #預約日期
			
			api_data = {
			"CRR_CROTIMES":CRR_CROTIMES,
			"CRR_RESDT": CRR_RESDT,
			"Functionname": "CheckChronicData",
			"ID_BIRTHDATE": ID_BIRTHDATE,
			"ID_CHROCARD": ID_CHROCARD,
			"ID_NUMBER": ID_NUMBER,
			"WS_CALL_IP": '192.168.51.76'
			}
			# print(api_data)

			json_data = json.dumps(api_data)
			base64_data = base64.b64encode(json_data.encode("utf-8")).decode("utf-8")


			url = f"http://192.168.200.215/webap/WebService.asmx/HISAPI?_Str={base64_data}"
			response = requests.get(url)

			json_string = re.search(r'<string[^>]*>(.*?)</string>', response.text, re.DOTALL).group(1)
			api_data = json.loads(json_string)


			if (api_data['SUCCESS'] == 'Y'): #能夠預約
				# print('能夠預約')
				date_result.append(data[11][number])

			number = number + 1

		return date_result
	#目前沒用到------------------------------------------------------------------------------------------------------------------------------