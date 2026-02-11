from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger #分頁功能套件，Django本身就有支援
from dateutil.relativedelta import relativedelta
import pandas as pd
import os, datetime, re, glob, calendar, time, smtplib, openpyxl
from django.conf import settings

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

try:
	import pymssql
except ImportError:
	pymssql = None


from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


# Credentials loaded from settings
case_plsql_host = settings.CASE_PLSQL_HOST
case_plsql_db = settings.CASE_PLSQL_DB
case_plsql_user = settings.CASE_PLSQL_USER
case_plsql_pwd = settings.CASE_PLSQL_PWD

mssql_66_146_host = settings.MSSQL_66_146_HOST
mssql_66_146_db = settings.MSSQL_66_146_DB
mssql_66_146_user = settings.MSSQL_66_146_USER
mssql_66_146_pwd = settings.MSSQL_66_146_PWD

mssql_66_147_host = settings.MSSQL_66_147_HOST
mssql_66_147_db = settings.MSSQL_66_147_DB
mssql_66_147_user = settings.MSSQL_66_147_USER
mssql_66_147_pwd = settings.MSSQL_66_147_PWD

mssql_200_211_host = settings.MSSQL_200_211_HOST
mssql_200_211_db = settings.MSSQL_200_211_DB
mssql_200_211_user = settings.MSSQL_200_211_USER
mssql_200_211_pwd = settings.MSSQL_200_211_PWD


# 維護時間設定 (如果需要啟用維護模式，可以設定 s_time 和 e_time)
# 例如:
# s_time = datetime.datetime.strptime("2024/05/04 15:00:00", "%Y/%m/%d %H:%M:%S")
# e_time = datetime.datetime.strptime("2024/05/04 16:00:00", "%Y/%m/%d %H:%M:%S")

# 預設為過去時間，避免觸發維護模式
s_time = datetime.datetime.strptime("2000/01/01 00:00:00", "%Y/%m/%d %H:%M:%S")
e_time = datetime.datetime.strptime("2000/01/01 00:00:01", "%Y/%m/%d %H:%M:%S")


def error_update_send_mail(e):
	print(e)
	# Mail設定
	message = MIMEMultipart()
	message['Subject'] = Header('網路掛號錯誤提示（本郵件為自動發送，請勿回覆）', 'utf-8')
	message['From'] = Header("網路掛號系統", 'utf-8')   # 發送者
	message['To'] =  Header("資訊室", 'utf-8')        # 接收者
	ftp_text = MIMEText('掛號失敗，' + e + '。', 'plain', 'utf-8')
	message.attach(ftp_text)

	try:
		smtpObj = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
		if settings.EMAIL_USE_TLS:
			smtpObj.starttls()
		smtpObj.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
		smtpObj.sendmail(settings.EMAIL_HOST_USER, "ha01540@everanhospital.com.tw", message.as_string())
	except smtplib.SMTPException:
		pass

# HIS資料庫相關程式
class PLSQLAPI:
	def Search_Stop_Show(date):
		if cx_Oracle is None:
			print("cx_Oracle driver not installed.")
			return []
		try:
			# 連線Oracle資料庫
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		except Exception as e:
			print(f"Oracle connection failed: {e}")
			return []

		try:
			# 輸入你要查找的資料表語法
			# 使用 :param_name 作為佔位符
			# SUBSTR(SCD_VISITDT,7,2) 從第7個字符開始取2個字符，獲取日期部分（DD）
			# TO_CHAR(SCD_SHIFTNO) 將時段轉換為字符串格式
			# 在 Python 中構建完整的 LIKE 模式，避免 Oracle 綁定變量問題
			date_pattern = date + '%'
			sql = '''SELECT SEC_SENAME,EMP_EMPNAME,SUBSTR(SCD_VISITDT,7,2),TO_CHAR(SCD_SHIFTNO),SCD_ROOMNO FROM REGSCD
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON SCD_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_VISITDT LIKE :date_pattern
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT,SCD_SHIFTNO'''
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql, {'date_pattern': date_pattern})

			rows = c.fetchall()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return(rows)
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show: {e}")
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return []

	def Search_Stop_Show_by_Dr(patid):
		if cx_Oracle is None:
			print("cx_Oracle driver not installed.")
			return []
		try:
			# 連線Oracle資料庫
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		except Exception as e:
			print(f"Oracle connection failed: {e}")
			return []
		today = datetime.datetime.now()
		n_date = today.strftime("%Y%m%d")
		e_date = (today + datetime.timedelta(days = 60)).strftime("%Y%m%d")

		try:
			# 輸入你要查找的資料表語法
			# 使用 :param_name 作為佔位符
			sql = '''SELECT SEC_SENAME,EMP_EMPNAME,SCD_VISITDT,SCD_SHIFTNO,SCD_ROOMNO FROM REGSCD 
			INNER JOIN BASEMP
				ON SCD_EMPNO = EMP_EMPNO 
			INNER JOIN BASSECT
				ON EMP_SECTNO = SEC_SECTNO
			WHERE SCD_CANCEL = 'Q'
				AND SCD_EMPNO = :patid
				AND SCD_VISITDT BETWEEN :n_date AND :e_date
				AND EMP_DC = 'N'
			ORDER BY SCD_VISITDT'''
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql, {'patid': patid, 'n_date': n_date, 'e_date': e_date})

			rows = c.fetchall()
			datas = []

			for row in rows:
				datas.append(list(row))

			i = 0
			for data in datas:
				datas[i].append(data[2][4:6])
				datas[i].append(data[2][6:8])

				if (data[3] == "1"):
					datas[i][3] = "早診"
				elif (data[3] == "2"):
					datas[i][3] = "午診"
				elif (data[3] == "3"):
					datas[i][3] = "晚診"

				i += 1

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return(datas)
		except Exception as e:
			print(f"SQL execution failed in Search_Stop_Show_by_Dr: {e}")
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return []

	def A002_Search_Room_All_Number(shiftno, roomno):
		if cx_Oracle is None:
			return []

		today = datetime.datetime.now()
		date = today.strftime("%Y%m%d")

		try:
			# 連線Oracle資料庫
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		except Exception as e:
			print(f"Oracle connection failed in A002_Search_Room_All_Number: {e}")
			return []

		# 輸入你要查找的資料表語法
		# 使用位置參數 :1, :2, :3 避免命名參數的問題
		# 中文別名用雙引號包起來並加上 AS
		sql = '''SELECT REG_VISITNO,REG_CANCD,CAL_STATUS,CAL_LEVEL,CASE WHEN CAL_STARTTIME = ' ' OR CAL_STARTTIME IS NULL THEN 'N' ELSE 'Y' END AS "報到否" FROM REGBAS 
		LEFT JOIN CALLOG
			ON REG_PATID = CAL_PATID
			AND REG_SHIFTNO = CAL_SHIFTNO
			AND REG_VISITDT = CAL_VISITDT
			AND REG_ROOMNO = CAL_ROOMNO
			AND REG_SEQ = CAL_SEQ
		WHERE REG_SHIFTNO = :1
			AND REG_VISITDT = :2
			AND REG_ROOMNO = :3
		ORDER BY REG_VISITNO'''
		
		try:
			# 定義資料庫游標
			c = connection.cursor()
			# 使用元組傳遞位置參數，順序：shiftno, date, roomno
			c.execute(sql, (shiftno, date, roomno))

			rows = c.fetchall()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return(rows)
		except Exception as e:
			print(f"SQL execution failed in A002_Search_Room_All_Number: {e}")
			print(f"Parameters: shiftno={shiftno} (type: {type(shiftno)}), roomno={roomno} (type: {type(roomno)}), date={date}")
			import traceback
			traceback.print_exc()
			try:
				connection.close()
			except:
				pass
			return []

	def A006_Search_BASEMP_EMPNAME(deptno):
		try:
			# 連線Oracle資料庫
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		except Exception as e:
			print(f"Oracle connection failed in A006_Search_BASEMP_EMPNAME: {e}")
			return None

		try:
			# 輸入你要查找的資料表語法
			# 使用 :param_name 作為佔位符
			sql = '''
				SELECT EMP_EMPNAME FROM BASEMP
				WHERE EMP_EMPNO = :deptno
			'''
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql, {'deptno': deptno})

			rows = c.fetchone()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			if rows:
				return rows[0]
			return None
		except Exception as e:
			print(f"SQL execution failed in A006_Search_BASEMP_EMPNAME: {e}")
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return None

class MSSQLAPI:
	# 網路掛號，登入LOG 20241225新增
	def insertA006LoginLogWeb(idno, patBirthday, url):
		# 連線MSSQL資料庫
		connection = pymssql.connect(
			host = mssql_66_146_host,
			user = mssql_66_146_user,
			password = mssql_66_146_pwd,
			database = mssql_66_146_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = """INSERT INTO LOG_WEB(
			IDNO,
			PATBIRTHDAY,
			URL) VALUES (
			%s,
			%s,
			%s)
		"""

		# 定義資料庫游標
		c = connection.cursor(as_dict = True)
		c.execute(sql, (idno, patBirthday, url))

		# 如果執行的是修改操作，需要提交事務；如果執行的是查詢操作，不需要提交
		connection.commit()

		c.close()
		connection.close()

		return("true")
	def A002_Now_Call(shiftno):
		today = datetime.datetime.now()
		date = today.strftime("%Y%m%d")

		# 連線MSSQL資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = """SELECT CONVERT(NVARCHAR(40),SCD_RONAME) as SCD_RONAME,CONVERT(NVARCHAR(40),SCD_SENAME) as SCD_SENAME,
		SCD_EMPNAME,SCD_CALLER_NOW_NUM,SCD_ROOMNO FROM NRGSCD
		WHERE SCD_SHIFTNO=%s 
			AND SCD_VISITDT=%s 
			AND SCD_CANCEL='N'
		ORDER BY SCD_ROOMNO
		"""

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (shiftno, date))

		rows = c.fetchall()

		c.close()
		connection.close()

		return(rows)

	def Insert_LOG_WEB(patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd):
		# 連線MSSQL資料庫
		connection = pymssql.connect(
			host = mssql_66_146_host,
			user = mssql_66_146_user,
			password = mssql_66_146_pwd,
			database = mssql_66_146_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = """INSERT INTO LOG_WEB(
			PATID,
			IDNO,
			VISITDT,
			RECNO,
			SHIFTNO,
			ROOMNO,
			SECTNO,
			DOCCD) VALUES (
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s,
			%s)
		"""

		# 定義資料庫游標
		c = connection.cursor(as_dict = True)

		try:
			c.execute(sql, (patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd))
			# 如果執行的是修改操作，需要提交事務；如果執行的是查詢操作，不需要提交
			connection.commit()
		except Exception as e:
			error_update_send_mail(e)
			# pass
		finally:
			pass

		c.close()
		connection.close()

		return("true")

	def Search_Dr_SECTNO(sename):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''SELECT SEC_SECTNO FROM NRGSEC 
		WHERE SEC_SHOWNAME=%s
		'''
		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (sename,))

		rows = c.fetchone()

		c.close()
		connection.close()

		return (rows)

	def Search_SENAME_BASSECT():
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='CP950')

		# 輸入你要查找的資料表語法
		sql = '''SELECT SEC_SHOWNAME,SEC_SENAME,SEC_INSSECTNO FROM NRGSEC'''
		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)

		rows = c.fetchall()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(rows)

	# 查詢儲存在table的資料
	def Search_EAH_WEB_DATA(data_type):
		try:
			# 連線MSSQL資料庫
			connection = pymssql.connect(
				host = mssql_66_146_host,
				user = mssql_66_146_user,
				password = mssql_66_146_pwd,
				database = mssql_66_146_db,
				charset='UTF-8')
		except Exception as e:
			print(f"MSSQL connection failed: {e}")
			return []

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = """SELECT * FROM EAH_WEB_DATA
			WHERE EAH_WEB_TYPE = %s
			AND EAH_WEB_STOP = 'N'
			ORDER BY EAH_WEBNO
			"""

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (data_type,))

		rows = c.fetchall()

		c.close()
		connection.close()

		return(rows)

	# 根據中文科別名稱，查HIS科別代碼
	def A006_Search_SEC_SECTNO_BY_SENAME(sename):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''SELECT SEC_SECTNO FROM NRGSEC
			WHERE SEC_SHOWNAME = %s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (sename,))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		if (data == None):
			return("error")
		else:
			return(data[0])

	# 根據醫師，查詢當週看診的日期與診別
	def A006_Search_NRGSCD_BY_EMPNO(empno, sectno, startdt, enddt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''SELECT SCD_VISITDT,SCD_SHIFTNO,SCD_ROOMNO FROM NRGSCD
			-- INNER JOIN NRGSEC
			-- 	  ON SCD_HOSPAREA = SEC_HOSPAREA
			-- 	  AND SCD_SECTNO = SEC_SECTNO
			  WHERE SCD_HOSPAREA='1'
				  AND SCD_CANCEL='N'
				  AND SCD_KNDKIND='1'
				  AND SCD_SECTNO = %s
				  --AND SEC_ISNET='Y'
				  AND SCD_VISITDT BETWEEN %s AND %s
				  AND SCD_EMPNO = %s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (sectno, startdt, enddt, empno))

		data = c.fetchall()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據科別，查詢當週看診的日期與診別
	def A006_Search_NRGSCD_BY_SECTNO(sectno, startdt, enddt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''SELECT SCD_VISITDT,SCD_SHIFTNO,SCD_EMPNO,SCD_SECTNO,SCD_EMPNAME FROM NRGSCD
			-- INNER JOIN NRGSEC
			-- 	  ON SCD_HOSPAREA = SEC_HOSPAREA
			-- 	  AND SCD_SECTNO = SEC_SECTNO
			  WHERE SCD_HOSPAREA='1'
				  AND SCD_CANCEL='N'
				  AND SCD_KNDKIND='1'
				  AND SCD_SECTNO = %s
				  --AND SEC_ISNET='Y'
				  AND SCD_VISITDT BETWEEN %s AND %s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (sectno, startdt, enddt))

		data = c.fetchall()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據醫師，查詢診間以掛號人數（醫師查詢用）
	def A006_Search_NRGRGB_COUNT(visitdt, sectno, doccd ,shiftno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT REG_HOSPAREA,REG_VISITDT,REG_SECTNO,REG_SHIFTNO,REG_DOCCD,count(*) AS NRP FROM NRGRGB
				WHERE REG_HOSPAREA='1'
					AND REG_VISITDT=%s
					AND REG_SECTNO=%s
					AND REG_DOCCD=%s
					AND REG_SHIFTNO=%s
					AND REG_VISITNO > 0
					AND REG_CANCEL='N'
				GROUP BY REG_HOSPAREA,REG_VISITDT,REG_SECTNO,REG_SHIFTNO,REG_DOCCD
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, sectno, doccd, shiftno))

		data = c.fetchall()
		if (len(data) == 0):
			data = 0
		else:
			data = data[0][5]

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據醫師，查詢診間以掛號人數（科室查詢用）
	def A006_Search_NRGNPRO_COUNT(visitdt, sectno, doccd ,shiftno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_66_147_host,
			user = mssql_66_147_user,
			password = mssql_66_147_pwd,
			database = mssql_66_147_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT NPRO_HOSPAREA,NPRO_VISITDT,NPRO_SECTNO,NPRO_SHIFTNO,NPRO_DOCCD,NPRO_NRP FROM NRGNPRO
				WHERE NPRO_HOSPAREA='1'
					AND NPRO_VISITDT=%s
					AND NPRO_SECTNO=%s
					AND NPRO_DOCCD=%s
					AND NPRO_SHIFTNO=%s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, sectno, doccd, shiftno))

		data = c.fetchall()
		if (len(data) == 0):
			data = 0
		else:
			data = data[0][5]

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據科別，查詢診間當周已掛號人數（科室查詢用）
	def A006_Search_NRGNPRO_COUNT_BY_SECTNO(sectno, startdt, enddt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT
				 REG_HOSPAREA,
				 REG_VISITDT,
				 REG_SECTNO,
				 REG_SHIFTNO,
				 REG_DOCCD,
				 COUNT(*) as NRP 
				FROM NRGRGB
				WHERE 
				 REG_HOSPAREA = '1'
				 and REG_VISITDT >= %s
				 and REG_VISITDT <= %s
				 and REG_CANCEL = 'N'
				 AND REG_VISITNO > 0
				 AND REG_SECTNO = %s
				GROUP BY 
				 REG_HOSPAREA,
				 REG_VISITDT,
				 REG_SECTNO,
				 REG_SHIFTNO,
				 REG_DOCCD ;
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (startdt, enddt, sectno))

		data = c.fetchall()

		# 回傳第一比查詢資料(rows[0])
		return(data)


	# 根據醫師，查詢診間是否有代診、約滿、停約尚不知道欄位
	def A006_Search_NRGSCD_DATA(visitdt, sectno, doccd ,shiftno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT SCD_REPLACE,SCD_REPLACENO,SCD_REPLACENM,SCD_RESVNORM FROM NRGSCD
				WHERE SCD_VISITDT = %s
				AND SCD_SHIFTNO = %s
				AND SCD_SECTNO = %s
				AND SCD_EMPNO = %s
				AND SCD_CANCEL = 'N'
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, shiftno, sectno, doccd))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據科別，查詢診間當周是否有代診、約滿、停約尚不知道欄位
	def A006_Search_NRGSCD_DATA_BY_SECTNO(sectno, startdt, enddt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT SCD_REPLACE,SCD_REPLACENO,SCD_REPLACENM,SCD_RESVNORM,SCD_SHIFTNO,SCD_EMPNO FROM NRGSCD
				WHERE SCD_VISITDT BETWEEN %s AND %s
					AND SCD_SECTNO = %s
					AND SCD_REPLACE = 'Y'
					AND SCD_CANCEL = 'N'
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (startdt, enddt, sectno))

		data = c.fetchall()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢病人病歷號
	def A006_Search_NRGPAT(acc):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
			    SELECT PAT_PATID,PAT_PATNAME,PAT_BIRTHDATE FROM NRGPAT
			    WHERE PAT_HOSPAREA='1'
			    AND (PAT_IDNO=%s OR PAT_PATID=%s)
			'''

		sql2 = '''
			    SELECT TPT_PATID,TPT_PATNAME,TPT_BIRTHDATE FROM NRGPATTEMP
			    WHERE TPT_HOSPAREA='1'
			    AND (TPT_IDNO=%s OR TPT_PATID=%s)
			    AND TPT_PATID <> ' '
			'''

		#print(sql2)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (acc, acc))

		data = c.fetchone()

		c.close()
		# 若NRGPAT找不到資料，則到NRGPATTEMP查找
		if (data == None):
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql2, (acc, acc))

			data = c.fetchone()

			c.close()

		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢病人全部看診資料
	def A006_Search_NRGRGB_BY_PATID(patid):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		date = datetime.date.today().strftime("%Y%m%d")
		if (patid[0].isdigit()):
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
					SELECT REG_PATID,PAT_PATNAME,REG_VISITDT,REG_SHIFTNO,SCD_SECTNO,SCD_EMPNAME,REG_VISITNO,REG_DOCCD,REG_RECNO,SCD_RONAME FROM NRGRGB
					LEFT JOIN NRGPAT
					ON PAT_PATID = REG_PATID
					LEFT JOIN NRGSCD
					ON SCD_SECTNO = REG_SECTNO
					AND SCD_EMPNO = REG_DOCCD
					AND SCD_VISITDT = REG_VISITDT
					AND SCD_SHIFTNO = REG_SHIFTNO
					WHERE REG_HOSPAREA='1'
					AND REG_PATID=%s
					AND REG_VISITDT >= %s
					AND REG_CANCEL='N'
					AND SCD_CANCEL='N'
					AND REG_VISITNO > -1
				'''
		else:
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
					SELECT REG_PATID,TPT_PATNAME,REG_VISITDT,REG_SHIFTNO,SCD_SECTNO,SCD_EMPNAME,REG_VISITNO,REG_DOCCD,REG_RECNO,SCD_RONAME FROM NRGRGB
					LEFT JOIN NRGPATTEMP
					ON TPT_PATID = REG_PATID
					LEFT JOIN NRGSCD
					ON SCD_SECTNO = REG_SECTNO
					AND SCD_EMPNO = REG_DOCCD
					AND SCD_VISITDT = REG_VISITDT
					AND SCD_SHIFTNO = REG_SHIFTNO
					WHERE REG_HOSPAREA='1'
					AND REG_PATID=%s
					AND REG_VISITDT >= %s
					AND REG_CANCEL='N'
					AND SCD_CANCEL='N'
				'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (patid, date))

		data = c.fetchall()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢病人是否重複看診
	def A006_Search_NRGRGB_FOR_PATID(patid, visitdt, shiftno, doccd):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT * FROM NRGRGB
				WHERE REG_HOSPAREA='1'
				AND REG_PATID = %s
				AND REG_VISITDT = %s
				AND REG_SHIFTNO = %s
				AND REG_DOCCD = %s
				AND REG_CANCEL='N'
				AND REG_VISITNO <> -300
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (patid, visitdt, shiftno, doccd))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 根據科別查科別名稱
	def A006_Search_NRGSEC_SHOWNAME(sectno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='CP950')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
			SELECT SEC_SHOWNAME FROM NRGSEC
			WHERE SEC_SECTNO = %s
		'''
		#print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (sectno,))

		rows = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(rows)

	# 查詢診間號
	def A006_Search_SCD_ROOMNO(visitdt, shiftno, sectno, doccd):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT SCD_ROOMNO FROM NRGSCD
				WHERE SCD_VISITDT = %s
					AND SCD_SHIFTNO = %s
					AND SCD_SECTNO = %s
					AND SCD_EMPNO = %s
					AND SCD_CANCEL='N'
			'''
		#print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, shiftno, sectno, doccd))

		data = c.fetchone()

		c.close()

		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢病人個資
	def A006_Search_NRGPAT_BY_PATID(patid):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT PAT_IDNO,PAT_PATNAME,PAT_BIRTHDATE,PAT_SEX FROM NRGPAT
				WHERE PAT_HOSPAREA='1'
				AND PAT_PATID = %s
			'''

		sql2 = '''
				SELECT TPT_IDNO,TPT_PATNAME,TPT_BIRTHDATE,TPT_SEX FROM NRGPATTEMP
				WHERE TPT_HOSPAREA='1'
				AND TPT_PATID = %s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (patid,))

		data = c.fetchone()

		c.close()
		# 若NRGPAT找不到資料，則到NRGPATTEMP查找
		if (data == None):
			# 定義資料庫游標
			c = connection.cursor()
			c.execute(sql2, (patid,))

			data = c.fetchone()

			c.close()

		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢診資料序號
	def A006_Search_EAH_NRGCON_COUNT():
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		sql = '''
				SELECT * FROM EAH_NRGCON WHERE PK_EAH=1
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 更新資料最大序號
	def A006_Update_EAH_NRGCON_COUNT():
		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 5,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			sql = '''
					IF EXISTS(
						SELECT * FROM EAH_NRGCON
						WHERE PK_EAH=1
						AND EAH_NRGCOUNT<9999
					)BEGIN
						UPDATE EAH_NRGCON SET EAH_NRGCOUNT=EAH_NRGCOUNT+1
						WHERE PK_EAH=1
					END
					ELSE
					BEGIN
						UPDATE EAH_NRGCON SET EAH_NRGCOUNT=8001
						WHERE PK_EAH=1
					END
				'''

			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql)
			connection.commit()

			c.close()
			connection.close()

		except Exception as e:
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return("更新最大序號失敗!", e)

	# 查詢診資料序號
	def A006_Search_NRGRGS_RECNO(visitdt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT * FROM NRGRGS WHERE RGS_VISITDT=%s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt,))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 新增資料序號
	def A006_Insert_NRGRGS_RECNO(visitdt):
		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 5,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
					INSERT INTO NRGRGS VALUES ('1', %s, 1)
				'''

			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql, (visitdt,))
			connection.commit()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return("OK")
		except:
			try:
				c.close()
			except:
				pass
			try:
				connection.close()
			except:
				pass
			return("新增資料序號失敗!")

	# 更新資料最大序號
	def A006_Update_NRGRGS_RECNO(visitdt):
		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 5,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
				UPDATE NRGRGS SET RGS_RECNO=RGS_RECNO+1
				WHERE RGS_HOSPAREA='1' AND RGS_VISITDT=%s
				'''

			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql, (visitdt,))
			connection.commit()

			c.close()
			connection.close()
			return("OK")

		except Exception as e:
			c.close()
			connection.close()
			return("更新最大序號失敗!", e)

	# 新增複診掛號資料
	def A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd):
		# 使用 %s 作為佔位符
		sql = '''
			INSERT INTO NRGRGB ( REG_HOSPAREA, REG_PATID, REG_VISITDT, REG_RECNO, REG_SHIFTNO,
			 REG_ROOMNO, REG_SECTNO, REG_DOCCD, REG_KNDKIND, REG_WAY ) VALUES( 
			 '1', %s, %s, %s, %s, %s, %s, %s, '1', '5')
			'''

		# MSSQLAPI.Insert_LOG_WEB(patid, visitdt, recno, shiftno, roomno, sectno, doccd, sql)

		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 10,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			# sql = '''
			# 	INSERT INTO NRGRGB ( REG_HOSPAREA, REG_PATID, REG_VISITDT, REG_RECNO, REG_SHIFTNO,
			# 	 REG_ROOMNO, REG_SECTNO, REG_DOCCD, REG_KNDKIND, REG_WAY ) SELECT 
			# 	 '1', '{patid}', '{visitdt}', {recno}, '{shiftno}', '{roomno}', '{sectno}', '{doccd}', '1', '5'
			# 	WHERE NOT EXISTS (
			# 	 	SELECT * FROM NRGRGB
			# 	 	WHERE (REG_PATID = '{patid}' OR REG_RECNO = {recno})
			# 	 	AND REG_VISITDT = '{visitdt}'
			# 	 	AND REG_SHIFTNO = '{shiftno}'
			# 	 	AND REG_ROOMNO = '{roomno}'
			# 	 	AND REG_SECTNO = '{sectno}'
			# 	 	AND REG_DOCCD = '{doccd}'
			# 	 	AND REG_VISITNO > -1)
			# 	'''.format(
			# 		patid = patid,
			# 		visitdt = visitdt,
			# 		recno = recno,
			# 		shiftno = shiftno,
			# 		roomno = roomno,
			# 		sectno = sectno,
			# 		doccd = doccd)

			#print(sql)
			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql, (patid, visitdt, recno, shiftno, roomno, sectno, doccd))
			connection.commit()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return("OK")
		except Exception as e:
			c.close()
			connection.close()
			return("寫入掛號資料失敗：", e)

	# 查詢診資料序號
	def A006_Search_NRGRGB_RECNO(visitdt):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT TOP (1) REG_RECNO FROM NRGRGB
				WHERE REG_HOSPAREA='1'
					AND REG_VISITDT=%s
				ORDER BY REG_RECNO DESC
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt,))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 查詢掛號結果
	def A006_Search_NRGRGB_VISITNO(visitdt, recno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT REG_VISITNO,REG_CANCODE FROM NRGRGB
				WHERE REG_HOSPAREA='1'
				AND REG_VISITDT=%s
				AND REG_RECNO=%s
			'''
		#print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, recno))

		data = c.fetchone()

		c.close()
		connection.close()
		#print("OK")

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 確認退掛的使用者身分
	def A006_Search_NRGRGB_PATID_SURE(patid, visitdt, recno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT * FROM NRGRGB
				WHERE REG_HOSPAREA='1'
				AND REG_VISITDT=%s
				AND REG_RECNO=%s
				AND REG_PATID=%s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (visitdt, recno, patid))

		data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 更新掛號狀態
	def A006_Update_NRGRGS_CANCEL(visitdt, recno):
		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 5,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
					UPDATE NRGRGB SET REG_CANCEL='Y'
					WHERE REG_HOSPAREA='1'
					AND REG_VISITDT=%s
					AND REG_RECNO=%s
				'''

			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql, (visitdt, recno))
			connection.commit()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return("OK")
		except Exception as e:
			c.close()
			connection.close()
			return("更新資料序號失敗!",e)

	# 查詢病人是否有資料存在
	def A006_Search_NRGPAT_EXISIT(idno):
		# 連線Oracle資料庫
		connection = pymssql.connect(
			host = mssql_200_211_host,
			user = mssql_200_211_user,
			password = mssql_200_211_pwd,
			database = mssql_200_211_db,
			timeout = 5,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		# 使用 %s 作為佔位符
		sql = '''
				SELECT * FROM NRGPAT
				WHERE PAT_HOSPAREA='1'
				AND PAT_IDNO = %s
			'''

		sql2 = '''
				SELECT * FROM NRGPATTEMP
				WHERE TPT_HOSPAREA='1'
				AND TPT_IDNO = %s
			'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql, (idno,))

		data = c.fetchone()

		if (data == None):
			c.execute(sql2, (idno,))
			data = c.fetchone()

		c.close()
		connection.close()

		# 回傳第一比查詢資料(rows[0])
		return(data)

	# 新增初診掛號資料
	def A006_Insert_NRGPATTEMP(visitdt, recno, idno, name, sex, birthday, phone):
		try:
			# 連線Oracle資料庫
			connection = pymssql.connect(
				host = mssql_200_211_host,
				user = mssql_200_211_user,
				password = mssql_200_211_pwd,
				database = mssql_200_211_db,
				timeout = 5,
				charset='UTF-8')
		except:
			return("資料庫連線失敗!")

		try:
			# 輸入你要查找的資料表語法
			# 使用 %s 作為佔位符
			sql = '''
					INSERT INTO NRGPATTEMP ( TPT_HOSPAREA, TPT_VISITDT, TPT_RECNO, TPT_PATID, TPT_IDNO, TPT_PATNAME,
					 TPT_SEX, TPT_BIRTHDATE, TPT_HOMETELNO, TPT_MOBILETELNO )
					  VALUES ( '1', %s, %s, ' ', %s, %s,
					   %s, %s, %s, ' ' )
				'''

			#print(sql)

			# 定義資料庫游標
			c = connection.cursor(as_dict = True)
			c.execute(sql, (visitdt, recno, idno, name, sex, birthday, phone))
			connection.commit()

			c.close()
			connection.close()

			# 回傳第一比查詢資料(rows[0])
			return("OK")
		except Exception as e:
			c.close()
			connection.close()
			return("新增初診資料失敗!",e)

# Create your views here.
def Hellow_world(request):
	now = datetime.datetime.now()
	html = '<html><body>It is now %s.</body></html>' % now

	return HttpResponse("Hello")

def error_404(request, exception):
	return redirect("/index/")

# def error_500(request, exception):
# 	return redirect("index")

# 功能(其他)、檔案上傳
# @csrf_exempt
# def file_upload(request):
# 	# 判斷是否使用POST
# 	if request.method=="POST":
# 		# 收取網頁回應的FILE檔案
# 		uploaded_file = request.FILES['file']
# 		# 建立django儲存器，並且設定上傳檔案位置 (可不在意檔案類型，會自動儲存)
# 		fss = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'test20230307'))
# 		# 儲存
# 		file = fss.save(uploaded_file.name, uploaded_file)
# 		# 重新導向網址
# 		return redirect("/Pomelo_file_upload/")
# 		# 查詢資料夾清單
# 		# mediafiles = os.listdir(settings.MEDIA_ROOT) 原本會存到 MEDIA_ROOT(可看settings.py是存到哪個路徑),可以改成指定資料夾
# 		mediafiles = os.listdir(os.path.join(settings.MEDIA_ROOT, 'test20230307'))
# 		return render(request, "File_upload.html", locals()) # 單純秀網頁的語法

# =========================================新官網=========================================
class MyPaginator(Paginator):
	"""docstring for MyPaginator"""
	def __init__(self, object_list, per_page, show_count = 1, orphans = 0, allow_empty_first_page = True):
		super().__init__(object_list, per_page, orphans, allow_empty_first_page)
		self.show_count = show_count
		self.has_previous_more = True
		self.has_next_more = True

	def page(self, number):
		self.number = int(number)

		if(self.number <= self.show_count + 2):
			self.has_previous_more = False
			self.previous_range = range(1, self.number)
		else:
			self.previous_range = range(self.number - self.show_count, self.number)

		if(self.number >= self.num_pages - self.show_count - 1):
			self.has_next_more = False
			self.next_range = range(self.number + 1, self.num_pages + 1)
		else:
			self.next_range = range(self.number + 1, self.number + self.show_count + 1)
		return super().page(number)

# 功能(一)、首頁
def index(request):
	# try:
	# 	if ("HTTP_X_FORWARDED_FOR" in request.META):
	# 		user_ip = request.META["HTTP_X_FORWARDED_FOR"]
	# 	else:
	# 		user_ip = request.META["REMOTE_ADDR"]

	# 	MSSQLAPI.Insert_LOG_WEB(user_ip, "/index/")
	# except Exception as e:
	# 	MSSQLAPI.Insert_LOG_WEB("ERROR", str(e))

	# 最新消息區
	in_news_lists = []
	in_info_data = []
	in_message_lists = []

	in_n_data = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_1'))
	i = 0
	for d in in_n_data:
		if (".txt" in d):
			in_news_lists.append(d.split("_"))
			in_news_lists[i].insert(0, "D00" + str(i))
			i += 1

	in_news_lists.sort(key = get_year, reverse = True)

	for c in in_news_lists:
		for d in in_n_data:
			if c[3] in d:
				in_info_data.append(d)

	for f in in_info_data:
		fd = open(os.path.join(settings.MEDIA_ROOT, 'news_1', f), "r", encoding="utf-8")
		in_message_lists.append(fd.readlines())
		fd.close()

	in_abc = zip(in_news_lists, in_message_lists)

	in_paginator = Paginator(in_news_lists, 6)
	total = int(in_paginator.num_pages)
	page = request.GET.get('page')
	in_contacts = in_paginator.get_page(page)

	# 媒體報導區
	in_medias_split_box = []
	in_medias_all_box = []
	in_modal_content = []
	in_list_description = []
	in_list_picture = []

	in_medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

	i = 0
	for md in in_medias_datas:
		if (".txt" in md):
			in_medias_split_box.append(md.split("_"))
			# medias_all_box.append(md)
			in_medias_split_box[i].insert(0, "D00" + str(i))
			i += 1

	in_medias_split_box.sort(key = get_m_year, reverse = True)

	for in_mc in in_medias_split_box:
		for in_md in in_medias_datas:
			if in_mc[3] in in_md:
				in_medias_all_box.append(in_md)

	for in_mf in in_medias_all_box:
		# open(filename,mode)
		in_mfd = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mf), "r", encoding="utf-8")
		lines = in_mfd.readlines()
		cleaned_lines = [line.strip() for line in lines]
		in_modal_content.append(cleaned_lines)
		in_mfd.close()

	for in_mread in in_medias_all_box:
		in_mrd_size = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mread), "r", encoding="utf-8")
		in_pxpx = in_mrd_size.read(100)
		in_pxpx = in_pxpx.replace('<h>','')
		in_pxpx = in_pxpx.replace('\n','')
		in_pxpx = in_pxpx.replace('\r','')
		in_pxpx = in_pxpx.replace('<t>','')
		in_list_description.append(in_pxpx)
		for in_gg in in_mrd_size.readlines():
			if "<img1>" in in_gg:
				in_list_picture.append(in_gg.strip())
				break
		in_mrd_size.close()

	in_paginator_2 = MyPaginator(in_medias_split_box, 6)
	in_total_2 = int(in_paginator_2.num_pages)
	in_page_2 = request.GET.get('page', 1)
	in_contacts_2 = in_paginator_2.page(in_page_2)

	in_paginator_3 = MyPaginator(in_list_description, 6)
	in_total_3 = int(in_paginator_3.num_pages)
	in_page_3 = request.GET.get('page', 1)
	in_contacts_3 = in_paginator_3.page(in_page_3)

	in_paginator_3P = MyPaginator(in_list_picture, 6)
	in_total_3P = int(in_paginator_3P.num_pages)
	in_page_3P = request.GET.get('page', 1)
	in_contacts_3P = in_paginator_3P.page(in_page_3P)

	in_paginator_4 = MyPaginator(in_modal_content, 6)
	in_total_4 = int(in_paginator_4.num_pages)
	in_page_4 = request.GET.get('page', 1)
	in_contacts_4 = in_paginator_4.page(in_page_4)

	in_zip_data = zip(in_contacts_2, in_contacts_4)
	# zdata = zip(medias_split_box, medias_all_box)

	in_zdata = zip(in_contacts_2, in_contacts_3, in_contacts_3P)

	# 傳遞 MEDIA_URL
	MEDIA_URL = settings.MEDIA_URL

	# 影音消息
	_dir=os.path.join(settings.MEDIA_ROOT, 'news_3')
	data = os.listdir(_dir)
	message_lists=[]
	for d in data:
		split_data=[]
		if '.txt' in d:
			split_data=d.split('_')
			# if len(split_data)==3:
			# 	C003=split_data[0]
			# 	if C003=='C003':
			# 		name=split_data[1]
			# 		videoType=split_data[2].split('.')[0]
			# 		message_lists.append({"name":name,"video_type":videoType,"file_name":d})
			if len(split_data)==3:
				C003=split_data[0]
				if C003=='C003':
					name=split_data[1]
					videoType=split_data[2].split('.')[0]
					message_lists.append({"name":name,"video_type":videoType,"file_name":d})
			if len(split_data)==4:
				C003=split_data[0]
				if C003=='C003':
					name=split_data[1]
					videoType=split_data[2]
					message_lists.append({"name":name,"video_type":videoType,"file_name":d})

	i=0
	for m in message_lists:
		message_lists[i]['index']=i+1;
		fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8")
		fd_lines=fd.readlines()
		for line in fd_lines:
			if "<yh>" in line:
				line=line.replace('<yh>','')
				# split_line=line.split('/')
				split_line=re.split('[/／]', line)
				if len(split_line)==2:
					message_lists[i]['title']=split_line[0].strip()
					message_lists[i]['sub']=split_line[1].strip()
				elif len(split_line)==1:
					message_lists[i]['title']=split_line[0].strip()
			elif "<yd>" in line:
				message_lists[i]['date']=line.replace('<yd>','').strip()
			elif "<dr>" in line:
				message_lists[i]['doctor_id']=line.replace('<dr>','').strip()
			elif "<ytb>" in line:
				youtube_url=line.replace('<ytb>','').strip()
				youtube_id=youtube_url.split('/')[-1]
				youtube_image=f'https://img.youtube.com/vi/{youtube_id}/0.jpg'
				message_lists[i]['youtube_url']=youtube_url
				message_lists[i]['youtube_image']=youtube_image
				message_lists[i]['youtube_id']=youtube_id
		i+=1
	message_lists=sorted(message_lists, key=lambda k: k['date'], reverse=True)
	message_lists_1=list(filter(lambda x: x['video_type'] == '1',message_lists))[:4]
	message_lists_2=list(filter(lambda x: x['video_type'] == '2',message_lists))[:4]
	message_lists_3=list(filter(lambda x: x['video_type'] == '3',message_lists))[:4]
	message_lists_4=list(filter(lambda x: x['video_type'] == '4',message_lists))[:4]

	# 醫療資訊
	# data = MSSQLAPI.Search_EAH_WEB_DATA("000")
	#print(data)
	# for d in data:
	# 	re_d = d.split("\n")
	# 	for dd in re_d:
	# 		if ("<h>" in d):
	# 			media_page_data.append(d.replace("<h>", ""))
	# 		if ("<in_date>" in d):
	# 			media_page_data.append(d.replace("<in_date>", ""))
	# 		if (("<t>" in d) and (t == 0)):
	# 			t += 1
	# 			media_page_data.append(d.replace("<t>", ""))
	# 		if ("<img_t>" in d):
	# 			media_page_data.append(d.replace("<img_t>", ""))

	# media_page_list.append(media_page_data)

	media_page_list = []
	media_page_dir = os.path.join(settings.MEDIA_ROOT, 'news_4')
	media_page_files = os.listdir(media_page_dir)
	re_media_page_files = sorted(media_page_files, reverse=True)

	for media_page_file in re_media_page_files:
		if ("IN001" in media_page_file):
			media_page_data = []
			t = 0

			fd = open(media_page_dir + "\\" + media_page_file, "r", encoding="utf-8")
			fd_lines = fd.readlines()
			for fd_line in fd_lines:
				if ("<h>" in fd_line):
					media_page_data.append(fd_line.replace("<h>", ""))
				if ("<in_date>" in fd_line):
					media_page_data.append(fd_line.replace("<in_date>", ""))
				if (("<t>" in fd_line) and (t == 0)):
					t += 1
					media_page_data.append(fd_line.replace("<t>", ""))
				if ("<img_t>" in fd_line):
					media_page_data.append(fd_line.replace("<img_t>", ""))

			media_page_data.append(media_page_file.split("_")[0] + "_" + media_page_file.split("_")[1])
			media_page_list.append(media_page_data)

	return render(request, "index.html", {
		'in_abc': in_abc,
		'in_contacts': in_contacts,
		'in_zip_data': in_zip_data,
		'in_zdata': in_zdata,
		'message_lists_1': message_lists_1,
		'message_lists_2': message_lists_2,
		'message_lists_3': message_lists_3,
		'message_lists_4': message_lists_4,
		'media_page_list': media_page_list,
		'MEDIA_URL': MEDIA_URL,
	})

# =========================================A000(醫院公告)=========================================

# 功能(二)、子頁-最新消息
def get_year(element):
	return element[5]  #指讀取資料第 5 個

# 最新消息
def new_news(request):
	# 定義變數
	news_lists = [] # 宣告一個空的陣列裝 news_lists.append(d.split("_")) 產出的切割後檔名陣列資料
	info_data = []  # 宣告一個空的陣列裝 info_data.append(d) 產出的完整檔名陣列資料
	message_lists = []  # 宣告一個空的陣列裝 message_lists.append(fd.readlines()) 產出的完整檔名陣列資料

	# 去查詢資料夾裡面有哪些檔案，並帶入 datas 陣列變數，html 在用 datas 變數將檔案列出 (等同所有檔案；類型-陣列)
	n_data = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_1'))
	i = 0
	# 將檔案名稱進行文字切割並篩選檔案類型分類 (例如.txt)
	for d in n_data:
		if (".txt" in d):
			news_lists.append(d.split("_")) #切割後的檔名 (為了要分別放到 table 的欄位中)
			news_lists[i].insert(0, "D00" + str(i)) #因 modal 需要取到 ID，但因 txt 的檔名沒有唯一值，所以需要幫他每筆資料新增流水號，讓 modal 可以取 ID 帶資料
			i += 1

	news_lists.sort(key = get_year, reverse = True) #根據 get_year function 取出的值為 key，去進行資料排序

	#用巢狀迴圈雙重比對並排序資料 (最外層陣列資料筆數代表迴圈執行次數，內層所有陣列資料會隨著外層重複比對)
	for c in news_lists:
		for d in n_data:
			if c[3] in d: #由於前面新增了流水號，為取得完整檔名，所以資料位置讀取要取第3個
				info_data.append(d) #完整檔名(因讀取txt檔必須是完整的檔名，所以才需多info_data這個陣列)

	for f in info_data:
		fd = open(os.path.join(settings.MEDIA_ROOT, 'news_1', f), "r", encoding="utf-8")
		message_lists.append(fd.readlines())
		fd.close()

	abc = zip(news_lists, message_lists)  #把拆散的資料，透過 zip 指令重新組合起來

	page_limit = 10
	# 設定分頁功能
	paginator = Paginator(news_lists, page_limit) # 設定一頁要顯示幾筆
	page = request.GET.get('page') # 接收使用者點選的頁碼
	contacts = paginator.get_page(page) # 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)

	return render(request, "news_1.html", {
		'abc': abc,
		'contacts': contacts,
		'paginator': paginator,
		'MEDIA_URL': settings.MEDIA_URL,
	})

# 功能(三)、子頁-媒體報導
def get_m_year(element):
	return element[7]  #指取資料第 7 個位置值

def new_medias(request):

	# 步驟(1)、定義變數 (先給一個空盒子，才有辦法裝 append 出來的資料)
	medias_split_box = [] # 裝 news_lists.append(d.split("_")) 產出的切割後的「檔名」
	medias_all_box = [] # 裝 info_data.append(d) 完整檔名下的「檔案內容」
	modal_content = [] # 裝 modal_content.append(mfd.readlines()) 產出的完整檔名下的「檔案內容」
	list_description = [] # 裝 list_description.append(mrd_size.read(20)) 產出的「檔案內容(前150字)」
	list_picture = [] # 裝 list_picture.append(mrd_size.readlines()) 產出的完整檔名下的「檔案內容-圖片」

	# 步驟(2)、查詢並帶入 C:\python\media\news_2 資料夾中所有檔案
	medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

	# 步驟(3)、將步驟(2)取得的檔案資料用迴圈進行檔名切割並篩出指定檔案類型
	i = 0
	for md in medias_datas:
		if (".txt" in md):
			medias_split_box.append(md.split("_")) # 將檔名進行切割，再透過 append 一筆筆產出切後的「檔名」 (為了要分別放到 table 的欄位中)
			# medias_all_box.append(md) # 因讀取 txt 檔需是完整檔名，才能一筆筆產出「檔案內容」

			'''# 步驟(5) 顯示 modal 效果(因 modal 需要對應 ID，但因 txt 的檔名沒有唯一值，
			所以需要幫他每筆資料新增流水號，讓 modal 可以取 ID 帶資料)'''
			medias_split_box[i].insert(0, "D00" + str(i))
			i += 1

	# 步驟(4)、根據 get_m_year function 取出的值為 key，按照日期去進行資料排序
	medias_split_box.sort(key = get_m_year, reverse = True)

	'''# 步驟(6-1)、將「檔名」與「所有檔案」作比對 function，若有比對到，以切割後的「檔名」呈現的數量去執行次數
		 並以第2位檔名去取值並進行檔案內容判斷，一筆筆產出「檔案內容」'''
	'''# 步驟(6-2)、再打開「檔案」去讀裡面的內容，並將讀取的內容打包成一筆筆，存到 modal_content 陣列'''
	for mc in medias_split_box:
		for md in medias_datas:
			if mc[3] in md:
				medias_all_box.append(md)

	for mf in medias_all_box:
		# open(filename,mode)-filename：檔案存在位置，mode：對這個檔案做些事情；r - 唯讀模式(檔案需存在)，只能從指定檔案讀取資料，並不能夠對這個檔案的內容進行任何寫入或變更
		mfd = open(os.path.join(settings.MEDIA_ROOT, 'news_2', mf), "r", encoding="utf-8")
		# 讀取檔案內容並去除換行符號
		lines = mfd.readlines()
		cleaned_lines = [line.strip() for line in lines]
		modal_content.append(cleaned_lines) 
		mfd.close() #.close:將檔案關閉，停止對於檔案進行任何操作。

	# 步驟(7)、設定 list 可以讀取顯示幾個字(150)
	for mread in medias_all_box:
		mrd_size = open(os.path.join(settings.MEDIA_ROOT, 'news_2', mread), "r", encoding="utf-8")
		pxpx = mrd_size.read(100)
		pxpx = pxpx.replace('<h>','') # 不帶出<h>
		pxpx = pxpx.replace('\n','') # 不帶出\n
		pxpx = pxpx.replace('\r','') # 不帶出\r
		pxpx = pxpx.replace('<t>','')# 不帶出<t>
		list_description.append(pxpx)
		# 步驟(8)、先把txt所有行數讀進去gg，再去找第一個<img1>把這行紀錄到 list_picture 陣列資料
		for gg in mrd_size.readlines():
			if "<img1>" in gg:
				list_picture.append(gg.strip())
				break # 跳離迴圈 因為圖片只抓每個txt檔的第一張
		mrd_size.close() #.close:將檔案關閉，停止對於檔案進行任何操作。

	page_limit = 3
	# 步驟(9)、設定分頁功能
	'''假設一個陣列已有作分頁，但另外一個陣列沒有作分頁的話，就會影響 zip 組合數量不一，
	顯示的筆數就會以少的為主，所以要把數量(例如.分頁)弄成一致，才會完成組合順利顯示'''
	paginator_2 = MyPaginator(medias_split_box, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('page', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)

	paginator_3 = MyPaginator(list_description, page_limit)
	total_3 = int(paginator_3.num_pages)
	page_3 = request.GET.get('page', 1)
	contacts_3 = paginator_3.page(page_3)

	paginator_3P = MyPaginator(list_picture, page_limit)
	total_3P = int(paginator_3P.num_pages)
	page_3P = request.GET.get('page', 1)
	contacts_3P = paginator_3P.page(page_3P)

	paginator_4 = MyPaginator(modal_content, page_limit)
	total_4 = int(paginator_4.num_pages)
	page_4 = request.GET.get('page', 1)
	contacts_4 = paginator_4.page(page_4)

	# 步驟(10)、組合陣列變數，讓前端可以用帶值(contacts_可以被拿來組合，是因為已經整理好了)
	# (modal用) 因要把「檔名」+「檔案內容」資料帶到前端，所以需用 zip 將兩個重新組合起來並放到 abc 變數中 (程式碼要放在 sort 後面)
	zip_data = zip(contacts_2, contacts_4)
	# zdata = zip(medias_split_box, medias_all_box) # (列表清單內容用)html 若前面有用過變數，就要用另一個變數，不然會帶不出來
	zdata = zip(contacts_2, contacts_3, contacts_3P)

	# 確保 MEDIA_URL 傳遞到模板
	MEDIA_URL = settings.MEDIA_URL

	if ("medical" in request.path):
		return render(request, "news_4/news_4.html", {
			'contacts_2': contacts_2,
			'contacts_3': contacts_3,
			'contacts_3P': contacts_3P,
			'contacts_4': contacts_4,
			'paginator_2': paginator_2,
			'zip_data': zip_data,
			'zdata': zdata,
			'MEDIA_URL': MEDIA_URL,
		})

	return render(request, "news_2.html", {
		'zip_data': zip_data,
		'zdata': zdata,
		'contacts_2': contacts_2,
		'paginator_2': paginator_2,
		'MEDIA_URL': MEDIA_URL,
	})

# 功能(三)、子頁-停休診公告
def new_stop_show(request):
	today = datetime.datetime.today()
	year = datetime.datetime.strftime(today,"%Y")
	month = datetime.datetime.strftime(today,"%m")

	# 處理日期加減
	if ("date_add" in request.GET):
		try:
			re_today = datetime.datetime.strptime(request.GET['date_now'],"%Y%m")
			re_date = re_today + relativedelta(months=1)
			year = datetime.datetime.strftime(re_date,"%Y")
			month = datetime.datetime.strftime(re_date,"%m")
		except Exception as e:
			print(f"Error parsing date_add: {e}")
			pass

	if ("date_sub" in request.GET):
		try:
			re_today = datetime.datetime.strptime(request.GET['date_now'],"%Y%m")
			re_date = re_today - relativedelta(months=1)
			year = datetime.datetime.strftime(re_date,"%Y")
			month = datetime.datetime.strftime(re_date,"%m")
		except Exception as e:
			print(f"Error parsing date_sub: {e}")
			pass

	# 查詢資料
	pl_data = PLSQLAPI.Search_Stop_Show(year + month)

	# 處理空資料情況
	if not pl_data or len(pl_data) == 0:
		datas = zip([], [])
		return render(request, "news_index.html", {
			'datas': datas,
			'year': year,
			'month': month,
		})

	# 處理資料
	data1 = []
	data2 = []
	try:
		# 將 tuple 列表轉換為列表列表，確保資料格式正確
		pl_data_list = [list(row) for row in pl_data]
		df = pd.DataFrame(pl_data_list)
		df.columns = ["科別", "醫師", "休診日", "時段", "診間"]
		data_g = df.groupby(["科別", "醫師"])
		for d in data_g:
			data1.append(d[0])
			data2.append(d[1].values.tolist())
	except Exception as e:
		print(f"Error processing data in new_stop_show: {e}")
		import traceback
		traceback.print_exc()
		data1 = []
		data2 = []

	# 在迴圈外部創建 zip 對象
	datas = zip(data1, data2)

	return render(request, "news_index.html", {
		'datas': datas,
		'year': year,
		'month': month,
	})

# 功能(四)、子頁-影音消息
@csrf_exempt
def new_video(request):
	active_page = request.GET.get('active_page', '1')

	_dir=os.path.join(settings.MEDIA_ROOT, 'news_3')
	data = os.listdir(_dir)
	message_lists=[]
	for d in data:
		split_data=[]
		if '.txt' in d:
			split_data=d.split('_')
			# if len(split_data)==3:
			# 	C003=split_data[0]
			# 	if C003=='C003':
			# 		name=split_data[1]
			# 		videoType=split_data[2].split('.')[0]
			# 		message_lists.append({"name":name,"video_type":videoType,"file_name":d})
			if len(split_data)==3:
				C003=split_data[0]
				if C003=='C003':
					name=split_data[1]
					videoType=split_data[2].split('.')[0]
					message_lists.append({"name":name,"video_type":videoType,"file_name":d})
			if len(split_data)==4:
				C003=split_data[0]
				if C003=='C003':
					name=split_data[1]
					videoType=split_data[2]
					message_lists.append({"name":name,"video_type":videoType,"file_name":d})

	i=0
	for m in message_lists:
		message_lists[i]['index']=i+1;
		fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8")
		fd_lines=fd.readlines()
		for line in fd_lines:
			if "<yh>" in line:
				line=line.replace('<yh>','')
				# split_line=line.split('/')
				split_line=re.split('[/／]', line)
				if len(split_line)==2:
					message_lists[i]['title']=split_line[0].strip()
					message_lists[i]['sub']=split_line[1].strip()
				elif len(split_line)==1:
					message_lists[i]['title']=split_line[0].strip()
			elif "<yd>" in line:
				message_lists[i]['date']=line.replace('<yd>','').strip()
			elif "<dr>" in line:
				message_lists[i]['doctor_id']=line.replace('<dr>','').strip()
			elif "<ytb>" in line:
				youtube_url=line.replace('<ytb>','').strip()
				youtube_id=youtube_url.split('/')[-1]
				youtube_image=f'https://img.youtube.com/vi/{youtube_id}/0.jpg'
				message_lists[i]['youtube_url']=youtube_url
				message_lists[i]['youtube_image']=youtube_image
				message_lists[i]['youtube_id']=youtube_id
		i+=1

	message_lists=sorted(message_lists, key=lambda k: k['date'], reverse=True)
	message_lists_1=list(filter(lambda x: x['video_type'] == '1',message_lists))
	message_lists_2=list(filter(lambda x: x['video_type'] == '2',message_lists))
	message_lists_3=list(filter(lambda x: x['video_type'] == '3',message_lists))
	message_lists_4=list(filter(lambda x: x['video_type'] == '4',message_lists))

	page_limit = 4
	# 步驟(六)、設定分頁功能
	paginator_1 = MyPaginator(message_lists_1, page_limit) # 設定一頁要顯示幾筆
	total_1 = int(paginator_1.num_pages) # 將筆數計算總共有幾頁
	page_1 = request.GET.get('p_1', '1') # 接收使用者點選的頁碼
	contacts_1 = paginator_1.page(page_1) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)
	message_lists_cut_1=contacts_1

	paginator_2 = MyPaginator(message_lists_2, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('p_2', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)
	message_lists_cut_2=contacts_2
	
	paginator_3 = MyPaginator(message_lists_3, page_limit) # 設定一頁要顯示幾筆
	total_3 = int(paginator_3.num_pages) # 將筆數計算總共有幾頁
	page_3 = request.GET.get('p_3', 1) # 接收使用者點選的頁碼
	contacts_3 = paginator_3.page(page_3) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)
	message_lists_cut_3=contacts_3

	paginator_4 = MyPaginator(message_lists_4, page_limit) # 設定一頁要顯示幾筆
	total_4 = int(paginator_4.num_pages) # 將筆數計算總共有幾頁
	page_4 = request.GET.get('p_4', 1) # 接收使用者點選的頁碼
	contacts_4 = paginator_4.page(page_4) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)
	message_lists_cut_4=contacts_4

	# message_lists_concat=message_lists_cut_1+message_lists_cut_2+message_lists_cut_3+message_lists_cut_4

	return render(request, "news_3.html", {
		'message_lists_cut_1': message_lists_cut_1,
		'message_lists_cut_2': message_lists_cut_2,
		'message_lists_cut_3': message_lists_cut_3,
		'message_lists_cut_4': message_lists_cut_4,
		'contacts_1': contacts_1,
		'contacts_2': contacts_2,
		'contacts_3': contacts_3,
		'contacts_4': contacts_4,
		'paginator_1': paginator_1,
		'paginator_2': paginator_2,
		'paginator_3': paginator_3,
		'paginator_4': paginator_4,
		'active_page': active_page,
	})

# 功能(五)、子頁-醫療資訊

# 【總覽頁】
def medical_info(request):
	# 步驟(1)、定義變數 (先給一個空盒子，才有辦法裝 append 出來的資料)
	medias_split_box = [] # 裝 news_lists.append(d.split("_")) 產出的切割後的「檔名」
	medias_all_box = [] # 裝 info_data.append(d) 完整檔名下的「檔案內容」
	modal_content = [] # 裝 modal_content.append(mfd.readlines()) 產出的完整檔名下的「檔案內容」
	list_description = [] # 裝 list_description.append(mrd_size.read(20)) 產出的「檔案內容(前150字)」
	list_picture = [] # 裝 list_picture.append(mrd_size.readlines()) 產出的完整檔名下的「檔案內容-圖片」

	# 步驟(2)、查詢並帶入 C:\python\media\news_2 資料夾中所有檔案
	medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

	# 步驟(3)、將步驟(2)取得的檔案資料用迴圈進行檔名切割並篩出指定檔案類型
	i = 0
	for md in medias_datas:
		if (".txt" in md):
			medias_split_box.append(md.split("_")) # 將檔名進行切割，再透過 append 一筆筆產出切後的「檔名」 (為了要分別放到 table 的欄位中)
			# medias_all_box.append(md) # 因讀取 txt 檔需是完整檔名，才能一筆筆產出「檔案內容」

			'''# 步驟(5) 顯示 modal 效果(因 modal 需要對應 ID，但因 txt 的檔名沒有唯一值，
			所以需要幫他每筆資料新增流水號，讓 modal 可以取 ID 帶資料)'''
			medias_split_box[i].insert(0, "D00" + str(i))
			i += 1

	# 步驟(4)、根據 get_m_year function 取出的值為 key，按照日期去進行資料排序
	medias_split_box.sort(key = get_m_year, reverse = True)

	'''# 步驟(6-1)、將「檔名」與「所有檔案」作比對 function，若有比對到，以切割後的「檔名」呈現的數量去執行次數
		 並以第2位檔名去取值並進行檔案內容判斷，一筆筆產出「檔案內容」'''
	'''# 步驟(6-2)、再打開「檔案」去讀裡面的內容，並將讀取的內容打包成一筆筆，存到 modal_content 陣列'''
	for mc in medias_split_box:
		for md in medias_datas:
			if mc[3] in md:
				medias_all_box.append(md)

	for mf in medias_all_box:
		# open(filename,mode)-filename：檔案存在位置，mode：對這個檔案做些事情；r - 唯讀模式(檔案需存在)，只能從指定檔案讀取資料，並不能夠對這個檔案的內容進行任何寫入或變更
		mfd = open(os.path.join(settings.MEDIA_ROOT, 'news_2', mf), "r", encoding="utf-8")
		# 讀取檔案內容並去除換行符號
		lines = mfd.readlines()
		cleaned_lines = [line.strip() for line in lines]
		modal_content.append(cleaned_lines)
		mfd.close() #.close:將檔案關閉，停止對於檔案進行任何操作。

	# 步驟(7)、設定 list 可以讀取顯示幾個字(150)
	for mread in medias_all_box:
		mrd_size = open(os.path.join(settings.MEDIA_ROOT, 'news_2', mread), "r", encoding="utf-8")
		pxpx = mrd_size.read(100)
		pxpx = pxpx.replace('<h>','') # 不帶出<h>
		pxpx = pxpx.replace('\n','') # 不帶出\n
		pxpx = pxpx.replace('\r','') # 不帶出\r
		pxpx = pxpx.replace('<t>','')# 不帶出<t>
		list_description.append(pxpx)
		# 步驟(8)、先把txt所有行數讀進去gg，再去找第一個<img1>把這行紀錄到 list_picture 陣列資料
		for gg in mrd_size.readlines():
			if "<img1>" in gg:
				list_picture.append(gg.strip())
				break # 跳離迴圈 因為圖片只抓每個txt檔的第一張
		mrd_size.close() #.close:將檔案關閉，停止對於檔案進行任何操作。

	page_limit = 10
	# 步驟(9)、設定分頁功能
	'''假設一個陣列已有作分頁，但另外一個陣列沒有作分頁的話，就會影響 zip 組合數量不一，
	顯示的筆數就會以少的為主，所以要把數量(例如.分頁)弄成一致，才會完成組合順利顯示'''
	paginator_2 = MyPaginator(medias_split_box, page_limit) # 設定一頁要顯示幾筆
	total_2 = int(paginator_2.num_pages) # 將筆數計算總共有幾頁
	page_2 = request.GET.get('page', 1) # 接收使用者點選的頁碼
	contacts_2 = paginator_2.page(page_2) # (列表清單用變數) 回傳使用者點的頁碼，讓前台顯示 (取得第幾頁的內容再丟回contacts)

	paginator_3 = MyPaginator(list_description, page_limit)
	total_3 = int(paginator_3.num_pages)
	page_3 = request.GET.get('page', 1)
	contacts_3 = paginator_3.page(page_3)

	paginator_3P = MyPaginator(list_picture, page_limit)
	total_3P = int(paginator_3P.num_pages)
	page_3P = request.GET.get('page', 1)
	contacts_3P = paginator_3P.page(page_3P)

	paginator_4 = MyPaginator(modal_content, page_limit)
	total_4 = int(paginator_4.num_pages)
	page_4 = request.GET.get('page', 1)
	contacts_4 = paginator_4.page(page_4)

	# 步驟(10)、組合陣列變數，讓前端可以用帶值(contacts_可以被拿來組合，是因為已經整理好了)
	# (modal用) 因要把「檔名」+「檔案內容」資料帶到前端，所以需用 zip 將兩個重新組合起來並放到 abc 變數中 (程式碼要放在 sort 後面)
	zip_data = zip(contacts_2, contacts_4)
	# zdata = zip(medias_split_box, medias_all_box) # (列表清單內容用)html 若前面有用過變數，就要用另一個變數，不然會帶不出來
	zdata = zip(contacts_2, contacts_3, contacts_3P)
	MEDIA_URL = settings.MEDIA_URL
	return render(request, "news_4/news_4.html", {
		'contacts_2': contacts_2,
		'contacts_3': contacts_3,
		'contacts_3P': contacts_3P,
		'contacts_4': contacts_4,
		'paginator_2': paginator_2,
		'zip_data': zip_data,
		'zdata': zdata,
		'MEDIA_URL': MEDIA_URL,
	})

	# 【項目內頁】
def medical_pages(request):
	media_page_dir = os.path.join(settings.MEDIA_ROOT, 'news_4')
	if ("media_page_path" in request.GET):
		path = request.GET.get("media_page_path")
		media_page_files = os.listdir(media_page_dir)
		for media_page_file in media_page_files:
			if (path in media_page_file):
				path = media_page_file

		path = os.path.join(media_page_dir, path)
		try:
			data = open(path, "r", encoding="utf-8")
			data_lines = data.readlines()
		except:
			return render(request, "404.html", status = 404)

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "news_4/news_4_1.html", {
		'data_lines': data_lines,
		'MEDIA_URL': MEDIA_URL,
	})

# =========================================A001(科室介紹)=========================================

# 科室總覽
def A001_department_overview(request):
	subjects = []
	django_subjects = []
	departments = []

	s_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department'))
	for s_dir in s_dirs:
		if ("D000" in s_dir):
			re_dir = s_dir.split("_")
			subjects.append(re_dir[2])
			django_subjects.append(s_dir)

	for subject in django_subjects:
		django_departments = []
		django_departments2 = []
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))

		for d_dir in d_dirs:
			red_dir = d_dir.split("_")
			django_departments.append(red_dir[1])
			# django_departments2.append(os.path.join(settings.MEDIA_ROOT, 'department', str(subject), str(d_dir)))

			"""20250715 path 格式為 大科室序號_科別序號"""
			django_departments2.append(str(subject).split("_")[1] + "_" + str(d_dir).split("_")[0])
			"""20250715 path 格式為 大科室序號_科別序號"""

			z_departments = zip(django_departments,django_departments2)

		departments.append(z_departments)

	datas = zip(subjects, departments)

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "department/department_index.html", {
		'datas': datas,
		'MEDIA_URL': MEDIA_URL,
	})

# 科室介紹
# @csrf_exempt
def A001_department_part(request):
	if ("open_info_name" in request.GET):
		path = request.GET.get("open_info_name")
		request.session['path'] = path

	if ("path" in request.session):
		path = request.session['path']

		"""20250715 path 格式為 大科室序號_科別序號"""
		pathP = path.split("_")[0]
		pathD = path.split("_")[1]
		pathC = os.path.join(settings.MEDIA_ROOT, 'department')
		pathDirs = os.listdir(pathC)
		pathFile = ""
		for pathDir in pathDirs:
			if ("D000" in pathDir) and (pathP == pathDir.split("_")[1]):
				fileDirs = os.listdir(os.path.join(pathC, pathDir))
				for fileDir in fileDirs:
					if (pathD == fileDir.split("_")[0]):
						pathFile = os.path.join(pathC, pathDir, fileDir)

		department = os.path.basename(pathFile).split("_")[1]
		disablePath = os.path.basename(pathFile).split("_")
		"""20250715 path 格式為 大科室序號_科別序號"""

		# department = path.split("\\")[6].split("_")[1]
		# disablePath = path.split("\\")[6].split("_")
		disable_X = False
		if ((len(disablePath) == 3) and (disablePath[2] == "x")):
			disable_X = True


		# 醫師姓名
		doctor_list = []
		# 醫師專業
		doctor_list2 = []
		# 醫師照片
		doctor_list3 = []
		# modal 標籤
		doctor_list4 = []
		# 詳細介紹開啟檔案用
		doctor_list5 = []
		# modal 停休診資訊
		doctor_list6 = []
		# 醫師所屬科別代碼
		doctor_list7 = []
		# 醫師員編
		doctor_list8 = []

		"""20250715 path改pathFile 格式為 大科室序號_科別序號"""
		# files = os.listdir(path)
		files = os.listdir(pathFile)

		for file in files:
			if (".txt" in file) and ("I000" in file):

				content = open(os.path.join(pathFile, file), "r", encoding="utf-8")
				introduction_list = content.readlines()
				content.close()

			if (".txt" in file) and ("D000" in file):
				re_file = file.split("_")
				# 醫師所屬科別代碼
				d_sectno = MSSQLAPI.Search_Dr_SECTNO(department)
				if (d_sectno != None):
					sectno = d_sectno[0]
				else:
					sectno = " "

				doctor_list.append(re_file[2])
				doctor_list4.append(re_file[1])
				"""20250715 改抓檔案序號"""
				# doctor_list5.append(file)
				doctor_list5.append(path.split("_")[0] + "_" + path.split("_")[1] + "_" + re_file[1])
				"""20250715 改抓檔案序號"""
				doctor_list6.append(PLSQLAPI.Search_Stop_Show_by_Dr(str(re_file[3]).replace(".txt","")))
				doctor_list7.append(sectno)
				doctor_list8.append(re_file[3].replace(".txt",""))

				content = open(os.path.join(pathFile, file), "r", encoding="utf-8")
				for c in content.readlines():
					if ("<e>" in c):
						doctor_list2.append(c.replace("<e>",""))
					if ("<img1>" in c):
						doctor_list3.append(c.replace("<img1>",""))
				content.close()
		"""20250715 path改pathFile 格式為 大科室序號_科別序號"""
		doctors = zip(doctor_list, doctor_list2, doctor_list3, doctor_list4, doctor_list5, doctor_list7, doctor_list8)
		modals = zip(doctor_list4, doctor_list6)

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "department/department_part.html", {
		'department': department,
		'modals': modals,
		'introduction_list': introduction_list,
		'doctors': doctors,
		'disable_X': disable_X,
		'MEDIA_URL': MEDIA_URL,
	})

# 醫師個人介紹
# @csrf_exempt
def A001_department_doctor(request):
	"""20250715 統一醫師查詢與科室總覽 path 格式為 大科室序號_科別序號_醫師序號"""
	if ("part_info" in request.GET) or ("dr_search" in request.GET):
		# 定義 dorp 和 porn 變數用於分頁連結
		if ("part_info" in request.GET):
			dorp = "part_info"
			porn = "open_info_name"
		elif ("dr_search" in request.GET):
			dorp = "dr_search"
			porn = "open_info_path"
		else:
			dorp = ""
			porn = ""
		
		# 優先從 GET 參數獲取 filename，如果沒有則從 session 獲取（分頁時使用）
		if ("open_info_name" in request.GET):
			filename = request.GET.get("open_info_name")
		elif ("open_info_path" in request.GET):
			filename = request.GET.get("open_info_path")
		elif ("path" in request.session):
			filename = request.session.get("path", "")
		else:
			filename = ""

		# 驗證 filename 格式是否正確（應為 大科室序號_科別序號_醫師序號）
		if not filename or filename.count("_") < 2:
			from django.http import Http404
			raise Http404("無效的醫師路徑參數")

		# 構建 URL，用於分頁連結
		# 確保 URL 包含必要的參數（dorp 和 porn），但不包含 page 參數（分頁時會添加）
		from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
		parsed = urlparse(request.get_full_path())
		query_params = parse_qs(parsed.query)
		
		# 移除 page 參數（分頁時會重新添加）
		if 'page' in query_params:
			del query_params['page']
		
		# 確保保留必要的參數（dorp 和 porn）
		if dorp and porn:
			# 確保 dorp 參數存在
			if dorp not in query_params:
				query_params[dorp] = ['']
			# 確保 porn 參數存在，使用實際的 filename
			if porn not in query_params:
				query_params[porn] = [filename] if filename else ['1']
			else:
				# 如果參數值為 '1'，更新為實際的 filename
				if query_params.get(porn) == ['1'] and filename:
					query_params[porn] = [filename]
		
		# 重新構建 URL（不包含 page 參數）
		# 確保至少有一個查詢參數，這樣模板中使用 & 連接就不會有問題
		if not query_params and dorp and porn:
			query_params[dorp] = ['']
			query_params[porn] = [filename] if filename else ['1']
		
		new_query = urlencode(query_params, doseq=True)
		url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))

		request.session['path'] = filename
		filename_parts = filename.split("_")
		pathP = filename_parts[0]
		pathD = filename_parts[1]
		pathF = filename_parts[2]
		pathC = os.path.join(settings.MEDIA_ROOT, 'department')
		pathDirs = os.listdir(pathC)
		pathFile = ""
		for pathDir in pathDirs:
			if ("D000" in pathDir) and (pathP == pathDir.split("_")[1]):
				fileDirs = os.listdir(os.path.join(pathC, pathDir))
				for fileDir in fileDirs:
					if (pathD == fileDir.split("_")[0]):
						pathFile = os.path.join(pathC, pathDir, fileDir)
						dFiles = os.listdir(pathFile)
						for dFile in dFiles:
							if (pathF == dFile.split("_")[1]):
								filename = dFile

		department = os.path.basename(pathFile).split("_")[1]
		disablePath = os.path.basename(pathFile).split("_")
		"""20250715 path 格式為 大科室序號_科別序號_醫師序號"""

		# dorp = "part_info"
		# porn = "open_info_name"
		# filename = request.GET.get("open_info_name")
		# print(filename)

		if filename == "1":
			filename = request.session['filename']
		else:
			request.session['filename'] = filename


		# path = request.session['path']
		# department = path.split("\\")[6].split("_")[1]

		# disablePath = path.split("\\")[6].split("_")
		disable_X = False
		if ((len(disablePath) == 3) and (disablePath[2] == "x")):
			disable_X = True

		d_sectno = MSSQLAPI.Search_Dr_SECTNO(department)
		if (d_sectno != None):
			sectno = d_sectno[0]
		else:
			sectno = " "

		re_file = filename.split("_")
		doctor_name = re_file[2]
		department_doctor_id = re_file[3].replace(".txt", "")
		docno = department_doctor_id
		stop_datas = PLSQLAPI.Search_Stop_Show_by_Dr(str(re_file[3]).replace(".txt",""))

		content = open(pathFile + "\\" + filename, "r", encoding="utf-8")
		for c in content.readlines():
			if ("<i>" in c):
				doctor_info = c.replace("<i>","")
			if ("<e>" in c):
				doctor_e = c.replace("<e>","").split("、")
			if ("<a>" in c):
				doctor_a = c.replace("<a>","").split("；")
			if ("<img1>" in c):
				doctor_img = c.replace("<img1>","")

		# 媒體報導區
		in_medias_split_box = []
		in_medias_all_box = []
		in_modal_content = []
		in_list_description = []
		in_list_picture = []

		in_medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

		i = 0
		for md in in_medias_datas:
			if (department_doctor_id in md):
				in_medias_split_box.append(md.split("_"))
				# medias_all_box.append(md)
				in_medias_split_box[i].insert(0, "D00" + str(i))
				i += 1

		in_medias_split_box.sort(key = get_m_year, reverse = True)

		for in_mc in in_medias_split_box:
			for in_md in in_medias_datas:
				if in_mc[3] in in_md:
					in_medias_all_box.append(in_md)

		for in_mf in in_medias_all_box:
			# open(filename,mode)
			in_mfd = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mf), "r", encoding="utf-8")
			lines = in_mfd.readlines()
			cleaned_lines = [line.strip() for line in lines]
			in_modal_content.append(cleaned_lines)
			in_mfd.close()

		for in_mread in in_medias_all_box:
			in_mrd_size = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mread), "r", encoding="utf-8")
			in_pxpx = in_mrd_size.read(100)
			in_pxpx = in_pxpx.replace('<h>','')
			in_pxpx = in_pxpx.replace('\n','')
			in_pxpx = in_pxpx.replace('\r','')
			in_pxpx = in_pxpx.replace('<t>','')
			in_list_description.append(in_pxpx)
			for in_gg in in_mrd_size.readlines():
				if "<img1>" in in_gg:
					in_list_picture.append(in_gg.strip())
					break
			in_mrd_size.close()

		in_paginator_2 = MyPaginator(in_medias_split_box, 6)
		in_total_2 = int(in_paginator_2.num_pages)
		in_page_2 = request.GET.get('page', 1)
		in_contacts_2 = in_paginator_2.page(in_page_2)

		in_paginator_3 = MyPaginator(in_list_description, 6)
		in_total_3 = int(in_paginator_3.num_pages)
		in_page_3 = request.GET.get('page', 1)
		in_contacts_3 = in_paginator_3.page(in_page_3)

		in_paginator_3P = MyPaginator(in_list_picture, 6)
		in_total_3P = int(in_paginator_3P.num_pages)
		in_page_3P = request.GET.get('page', 1)
		in_contacts_3P = in_paginator_3P.page(in_page_3P)

		in_paginator_4 = MyPaginator(in_modal_content, 6)
		in_total_4 = int(in_paginator_4.num_pages)
		in_page_4 = request.GET.get('page', 1)
		in_contacts_4 = in_paginator_4.page(in_page_4)

		in_zip_data = zip(in_contacts_2, in_contacts_4)
		# zdata = zip(medias_split_box, medias_all_box)

		in_zdata = zip(in_contacts_2, in_contacts_3, in_contacts_3P)
		in_zdata_i = i

		# 影音消息
		_dir=os.path.join(settings.MEDIA_ROOT, 'news_3')
		data = os.listdir(_dir)
		message_lists=[]
		for d in data:
			split_data=[]
			if (department_doctor_id in d):
				split_data=d.split('_')
				if len(split_data)==3:
					C003=split_data[0]
					if C003=='C003':
						name=split_data[1]
						videoType=split_data[2].split('.')[0]
						message_lists.append({"name":name,"video_type":videoType,"file_name":d})
				if len(split_data)==4:
					C003=split_data[0]
					if C003=='C003':
						name=split_data[1]
						videoType=split_data[2]
						message_lists.append({"name":name,"video_type":videoType,"file_name":d})

		i=0
		for m in message_lists:
			message_lists[i]['index']=i+1;
			fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8")
			fd_lines=fd.readlines()
			for line in fd_lines:
				if "<yh>" in line:
					line=line.replace('<yh>','')
					split_line=re.split('[/／]', line)
					if len(split_line)==2:
						message_lists[i]['title']=split_line[0].strip()
						message_lists[i]['sub']=split_line[1].strip()
					elif len(split_line)==1:
						message_lists[i]['title']=split_line[0].strip()
				elif "<yd>" in line:
					message_lists[i]['date']=line.replace('<yd>','').strip()
				elif "<dr>" in line:
					message_lists[i]['doctor_id']=line.replace('<dr>','').strip()
				elif "<ytb>" in line:
					youtube_url=line.replace('<ytb>','').strip()
					youtube_id=youtube_url.split('/')[-1]
					youtube_image=f'https://img.youtube.com/vi/{youtube_id}/0.jpg'
					message_lists[i]['youtube_url']=youtube_url
					message_lists[i]['youtube_image']=youtube_image
					message_lists[i]['youtube_id']=youtube_id
			i+=1
		message_lists=sorted(message_lists, key=lambda k: k['date'], reverse=True)
		message_lists_1=list(message_lists)[:4]
		message_lists_1_i = i

	# if ("dr_search" in request.GET):
	# 	if ("open_info_path" in request.GET):
	# 		"""20250715 path 格式為 大科室序號_科別序號_醫師序號"""
	# 		filename = request.GET.get("open_info_path")

	# 		pathP = filename.split("_")[0]
	# 		pathD = filename.split("_")[1]
	# 		pathF = filename.split("_")[2]
	# 		pathC = os.path.join(settings.MEDIA_ROOT, 'department')
	# 		pathDirs = os.listdir(pathC)
	# 		pathFile = ""
	# 		for pathDir in pathDirs:
	# 			if ("D000" in pathDir) and (pathP == pathDir.split("_")[1]):
	# 				fileDirs = os.listdir(pathC + "\\" + pathDir)
	# 				for fileDir in fileDirs:
	# 					if (pathD == fileDir.split("_")[0]):
	# 						pathFile = pathC + "\\" + pathDir + "\\" + fileDir
	# 						dFiles = os.listdir(pathC + "\\" + pathDir + "\\" + fileDir)
	# 						for dFile in dFiles:
	# 							if (pathF == dFile.split("_")[1]):
	# 								filename = dFile

	# 		department = pathFile.split("\\")[5].split("_")[1]
	# 		disablePath = pathFile.split("\\")[5].split("_")
	# 		"""20250715 path 格式為 大科室序號_科別序號_醫師序號"""

	# 		# dorp = "dr_search"
	# 		# porn = "open_info_path"
	# 		# path = request.GET.get("open_info_path")
	# 		# if path == "1":
	# 		# 	path = request.session['re_path']
	# 		# else:
	# 		# 	request.session['re_path'] = path
	# 		# 	# 20240129關係re_path先改 + "\\" + re_path[7]； + "\\" + re_path[8]
	# 		# 	re_path = path.split("\\")
	# 		# 	rp = re_path[0] + "\\" + re_path[1] + "\\"  + "\\" + re_path[2] + "\\" + re_path[3] + "\\" + re_path[5] + "\\" + re_path[6]

	# 		# 	request.session['path'] = rp
	# 		# 	# rep = re_path[0] + "\\" + re_path[1] + "\\"  + "\\" + re_path[2] + "\\" + re_path[3] + "\\" + re_path[5] + "\\" + re_path[6] + "\\" + re_path[7]

	# 		# department = path.split("\\")[6].split("_")[1]

	# 		disablePath = pathFile.split("\\")[6].split("_")
	# 		if ((len(disablePath) == 3) and (disablePath[2] == "x")):
	# 			disable_X = True


	# 		d_sectno = MSSQLAPI.Search_Dr_SECTNO(department)
	# 		if (d_sectno != None):
	# 			sectno = d_sectno[0]
	# 		else:
	# 			sectno = "XXX"

	# 		re_path = pathFile.split("\\")
	# 		# print(re_path)
	# 		# 20240129關係re_path先改成8原本是7
	# 		doctor_name = re_path[7].split("_")[2]
	# 		department_doctor_id = re_path[7].split("_")[3].replace(".txt", "")
	# 		docno = department_doctor_id
	# 		stop_datas = PLSQLAPI.Search_Stop_Show_by_Dr(str(re_path[7].split("_")[3]).replace(".txt",""))

	# 		content = open(filename, "r", encoding="utf-8")
	# 		for c in content.readlines():
	# 			if ("<i>" in c):
	# 				doctor_info = c.replace("<i>","")
	# 			if ("<e>" in c):
	# 				doctor_e = c.replace("<e>","").split("、")
	# 			if ("<a>" in c):
	# 				doctor_a = c.replace("<a>","").split("；")
	# 			if ("<img1>" in c):
	# 				doctor_img = c.replace("<img1>","")

	# 		# 媒體報導區
	# 		in_medias_split_box = []
	# 		in_medias_all_box = []
	# 		in_modal_content = []
	# 		in_list_description = []
	# 		in_list_picture = []

	# 		in_medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

	# 		i = 0
	# 		for md in in_medias_datas:
	# 			if (department_doctor_id in md):
	# 				in_medias_split_box.append(md.split("_"))
	# 				# medias_all_box.append(md)
	# 				in_medias_split_box[i].insert(0, "D00" + str(i))
	# 				i += 1

	# 		in_medias_split_box.sort(key = get_m_year, reverse = True)

	# 		for in_mc in in_medias_split_box:
	# 			for in_md in in_medias_datas:
	# 				if in_mc[3] in in_md:
	# 					in_medias_all_box.append(in_md)

	# 		for in_mf in in_medias_all_box:
	# 			# open(filename,mode)
	# 			in_mfd = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mf), "r", encoding="utf-8")
	# 			in_modal_content.append(in_mfd.readlines())
	# 			in_mfd.close()

	# 		for in_mread in in_medias_all_box:
	# 			in_mrd_size = open(os.path.join(settings.MEDIA_ROOT, 'news_2', in_mread), "r", encoding="utf-8")
	# 			in_pxpx = in_mrd_size.read(100)
	# 			in_pxpx = in_pxpx.replace('<h>','')
	# 			in_pxpx = in_pxpx.replace('\n','')
	# 			in_pxpx = in_pxpx.replace('\r','')
	# 			in_pxpx = in_pxpx.replace('<t>','')
	# 			in_list_description.append(in_pxpx)
	# 			for in_gg in in_mrd_size.readlines():
	# 				if "<img1>" in in_gg:
	# 					in_list_picture.append(in_gg)
	# 					break
	# 			in_mrd_size.close()

	# 		in_paginator_2 = MyPaginator(in_medias_split_box, 6)
	# 		in_total_2 = int(in_paginator_2.num_pages)
	# 		in_page_2 = request.GET.get('page', 1)
	# 		in_contacts_2 = in_paginator_2.page(in_page_2)

	# 		in_paginator_3 = MyPaginator(in_list_description, 6)
	# 		in_total_3 = int(in_paginator_3.num_pages)
	# 		in_page_3 = request.GET.get('page', 1)
	# 		in_contacts_3 = in_paginator_3.page(in_page_3)

	# 		in_paginator_3P = MyPaginator(in_list_picture, 6)
	# 		in_total_3P = int(in_paginator_3P.num_pages)
	# 		in_page_3P = request.GET.get('page', 1)
	# 		in_contacts_3P = in_paginator_3P.page(in_page_3P)

	# 		in_paginator_4 = MyPaginator(in_modal_content, 6)
	# 		in_total_4 = int(in_paginator_4.num_pages)
	# 		in_page_4 = request.GET.get('page', 1)
	# 		in_contacts_4 = in_paginator_4.page(in_page_4)

	# 		in_zip_data = zip(in_contacts_2, in_contacts_4)
	# 		# zdata = zip(medias_split_box, medias_all_box)

	# 		in_zdata = zip(in_contacts_2, in_contacts_3, in_contacts_3P)
	# 		in_zdata_i = i

	# 		# 影音消息
	# 		_dir=os.path.join(settings.MEDIA_ROOT, 'news_3')
	# 		data = os.listdir(_dir)
	# 		message_lists=[]
	# 		for d in data:
	# 			split_data=[]
	# 			if (department_doctor_id in d):
	# 				split_data=d.split('_')
	# 				if len(split_data)==3:
	# 					C003=split_data[0]
	# 					if C003=='C003':
	# 						name=split_data[1]
	# 						videoType=split_data[2].split('.')[0]
	# 						message_lists.append({"name":name,"video_type":videoType,"file_name":d})
	# 				if len(split_data)==4:
	# 					C003=split_data[0]
	# 					if C003=='C003':
	# 						name=split_data[1]
	# 						videoType=split_data[2]
	# 						message_lists.append({"name":name,"video_type":videoType,"file_name":d})

	# 		i=0
	# 		for m in message_lists:
	# 			message_lists[i]['index']=i+1;
	# 			fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8")
	# 			fd_lines=fd.readlines()
	# 			for line in fd_lines:
	# 				if "<yh>" in line:
	# 					line=line.replace('<yh>','')
	# 					split_line=re.split('[/／]', line)
	# 					if len(split_line)==2:
	# 						message_lists[i]['title']=split_line[0].strip()
	# 						message_lists[i]['sub']=split_line[1].strip()
	# 					elif len(split_line)==1:
	# 						message_lists[i]['title']=split_line[0].strip()
	# 				elif "<yd>" in line:
	# 					message_lists[i]['date']=line.replace('<yd>','').strip()
	# 				elif "<dr>" in line:
	# 					message_lists[i]['doctor_id']=line.replace('<dr>','').strip()
	# 				elif "<ytb>" in line:
	# 					youtube_url=line.replace('<ytb>','').strip()
	# 					youtube_id=youtube_url.split('/')[-1]
	# 					youtube_image=f'https://img.youtube.com/vi/{youtube_id}/0.jpg'
	# 					message_lists[i]['youtube_url']=youtube_url
	# 					message_lists[i]['youtube_image']=youtube_image
	# 					message_lists[i]['youtube_id']=youtube_id
	# 			i+=1
	# 		message_lists=sorted(message_lists, key=lambda k: k['date'], reverse=True)
	# 		message_lists_1=list(message_lists)[:4]
	# 		message_lists_1_i = i

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "department/department_doctor.html", {
		'doctor_name': doctor_name,
		'department': department,
		'stop_datas': stop_datas,
		'in_zip_data': in_zip_data,
		'in_zdata': in_zdata,
		'in_zdata_i': in_zdata_i,
		'in_contacts_2': in_contacts_2,
		'in_paginator_2': in_paginator_2,
		'message_lists_1': message_lists_1,
		'message_lists_1_i': message_lists_1_i,
		'doctor_img': doctor_img,
		'doctor_info': doctor_info,
		'disable_X': disable_X,
		'docno': docno,
		'doctor_e': doctor_e,
		'doctor_a': doctor_a,
		'MEDIA_URL': MEDIA_URL,
		'url': url,
		'dorp': dorp,
		'porn': porn,
	})

# 醫師查詢
def A001_dr_search(request):
	subjects = []
	django_subjects = []
	doctors = []

	s_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department'))
	for s_dir in s_dirs:
		if ("D000" in s_dir):
			re_dir = s_dir.split("_")
			django_subjects.append(s_dir)

	for subject in django_subjects:
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))

		for d_dir in d_dirs:
			django_doctors = []
			django_doctors2 = []
			re_subject = d_dir.split("_")
			subjects.append(re_subject[1])
			dd_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject), str(d_dir)))

			for dd_dir in dd_dirs:
				if ("D000" in dd_dir):
					red_dir = dd_dir.split("_")
					django_doctors.append(red_dir[2].split(" ")[0])
					"""20250715 path 格式為 大科室序號_科別序號_醫師序號"""
					django_doctors2.append(str(subject).split("_")[1] + "_" + str(d_dir).split("_")[0] + "_" + str(dd_dir).split("_")[1])
					"""20250715 path 格式為 大科室序號_科別序號_醫師序號"""
					z_doctors = zip(django_doctors,django_doctors2)

			doctors.append(z_doctors)

	datas = zip(subjects, doctors)

	return render(request, "dr_search.html", {
		'datas': datas,
	})

# =========================================A002(就醫指南)=========================================

# 看診進度
def A002_consultation_progress(request):
	now = datetime.datetime.now()
	now = datetime.datetime.strftime(now,"%H:%M:%S")


	# afternoon_lists = MSSQLAPI.A002_Now_Call("2")
	# night_lists = MSSQLAPI.A002_Now_Call("3")

	if (now <= "13:30:00") :
		now_status = "1"
		number_lists = MSSQLAPI.A002_Now_Call("1")
		all_number_list = []
		for number_list in number_lists:
			all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("1", number_list[4]))
		all_count_list = []
		all_completed_list = []
		all_no_completed_list = []
		for c in all_number_list:
			all_count = 0
			all_completed = 0
			all_no_completed = 0
			for cc in c:
				if (cc[1] != "Y"):
					all_count += 1
					if (cc[3] == 8):
						all_completed += 1
					if ((cc[4] == "Y") and (cc[3] == 3)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 7)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 6)):
						all_no_completed += 1

			all_count_list.append(all_count)
			all_completed_list.append(all_completed)
			all_no_completed_list.append(all_no_completed)

		modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

	elif ((now > "13:30:00") and (now <= "17:40:00")):
		now_status = "2"
		number_lists = MSSQLAPI.A002_Now_Call("2")
		all_number_list = []
		for number_list in number_lists:
			all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("2", number_list[4]))
		all_count_list = []
		all_completed_list = []
		all_no_completed_list = []
		for c in all_number_list:
			all_count = 0
			all_completed = 0
			all_no_completed = 0
			for cc in c:
				if (cc[1] != "Y"):
					all_count += 1
					if (cc[3] == 8):
						all_completed += 1
					if ((cc[4] == "Y") and (cc[3] == 3)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 7)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 6)):
						all_no_completed += 1

			all_count_list.append(all_count)
			all_completed_list.append(all_completed)
			all_no_completed_list.append(all_no_completed)

		modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

	else:
		now_status = "3"
		number_lists = MSSQLAPI.A002_Now_Call("3")
		all_number_list = []
		for number_list in number_lists:
			all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("3", number_list[4]))
		all_count_list = []
		all_completed_list = []
		all_no_completed_list = []
		for c in all_number_list:
			all_count = 0
			all_completed = 0
			all_no_completed = 0
			for cc in c:
				if (cc[1] != "Y"):
					all_count += 1
					if (cc[3] == 8):
						all_completed += 1
					if ((cc[4] == "Y") and (cc[3] == 3)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 7)):
						all_no_completed += 1
					elif ((cc[4] == "Y") and (cc[3] == 6)):
						all_no_completed += 1

			all_count_list.append(all_count)
			all_completed_list.append(all_completed)
			all_no_completed_list.append(all_no_completed)

		modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

	if ("shiftno_h" in request.GET):
		chs_status = request.GET.get("shiftno_h")
		if (chs_status == "早診"):
			now_status = "1"
			number_lists = MSSQLAPI.A002_Now_Call("1")
			all_number_list = []
			for number_list in number_lists:
				all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("1", number_list[4]))
			all_count_list = []
			all_completed_list = []
			all_no_completed_list = []
			for c in all_number_list:
				all_count = 0
				all_completed = 0
				all_no_completed = 0
				for cc in c:
					if (cc[1] != "Y"):
						all_count += 1
						if (cc[3] == 8):
							all_completed += 1
						if ((cc[4] == "Y") and (cc[3] == 3)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 7)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 6)):
							all_no_completed += 1

				all_count_list.append(all_count)
				all_completed_list.append(all_completed)
				all_no_completed_list.append(all_no_completed)

			modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

		elif (chs_status == "午診"):
			now_status = "2"
			number_lists = MSSQLAPI.A002_Now_Call("2")
			all_number_list = []
			for number_list in number_lists:
				all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("2", number_list[4]))
			all_count_list = []
			all_completed_list = []
			all_no_completed_list = []
			for c in all_number_list:
				all_count = 0
				all_completed = 0
				all_no_completed = 0
				for cc in c:
					if (cc[1] != "Y"):
						all_count += 1
						if (cc[3] == 8):
							all_completed += 1
						if ((cc[4] == "Y") and (cc[3] == 3)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 7)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 6)):
							all_no_completed += 1

				all_count_list.append(all_count)
				all_completed_list.append(all_completed)
				all_no_completed_list.append(all_no_completed)

			modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

		elif (chs_status == "晚診"):
			now_status = "3"
			number_lists = MSSQLAPI.A002_Now_Call("3")
			all_number_list = []
			for number_list in number_lists:
				all_number_list.append(PLSQLAPI.A002_Search_Room_All_Number("3", number_list[4]))
				print(number_list[4])
				if (number_list[4] == '501'):
					print(PLSQLAPI.A002_Search_Room_All_Number("3", number_list[4]))
			all_count_list = []
			all_completed_list = []
			all_no_completed_list = []
			for c in all_number_list:
				all_count = 0
				all_completed = 0
				all_no_completed = 0
				for cc in c:
					if (cc[1] != "Y"):
						all_count += 1
						if (cc[3] == 8):
							all_completed += 1
						if ((cc[4] == "Y") and (cc[3] == 3)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 7)):
							all_no_completed += 1
						elif ((cc[4] == "Y") and (cc[3] == 6)):
							all_no_completed += 1

				all_count_list.append(all_count)
				all_completed_list.append(all_completed)
				all_no_completed_list.append(all_no_completed)

			modals = zip(number_lists, all_number_list,all_count_list,all_completed_list,all_no_completed_list)

	# 格式化 now 為顯示用
	now_display = datetime.datetime.now()
	now_display = datetime.datetime.strftime(now_display, "%Y-%m-%d %H:%M:%S")
	
	return render(request, "consultation_progress_v3.html", {
		'modals': modals,
		'number_lists': number_lists,
		'now_status': now_status,
		'now': now_display,
	})

# 掛號須知
def A002_registration_notice(request):
	A006_True = "True"
	data = open(os.path.join(settings.MEDIA_ROOT, 'A002', 'registration_notice', 'main.txt'), "r", encoding="utf-8")
	data_lines = data.readlines()

	return render(request, "Patient_Guide/Patient_Guide_index_v2.html", {
		'data_lines': data_lines,
		'A006_True': A006_True,
	})

# 門診時刻表
def A002_clinic_time(request):

	return render(request, "Patient_Guide/Patient_Guide_1.html", {})

# 我該看哪一科
def A002_which_disease(request):
	subjects = []
	django_subjects = []
	departments = []

	s_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department'))
	for s_dir in s_dirs:
		if ("D000" in s_dir):
			subjects.append(s_dir.split("_")[2])

			d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', s_dir))
			department_1 = []
			department_2 = []
			department_3 = []
			for d_dir in d_dirs:
				department_1.append(d_dir.split("_")[1])
				dir_path = os.path.join(settings.MEDIA_ROOT, 'department', s_dir, d_dir)
				department_3.append(dir_path)

				files = os.listdir(dir_path)
				for file in files:
					if ("I000" in file):
						text = open(os.path.join(dir_path, file), "r", encoding="utf-8")

						for t in text.readlines():
							if("<dm>" in t):
								re_text = t.replace("<dm>", "")
								department_2.append(re_text)

			z_departments = zip(department_1, department_2, department_3)
			departments.append(z_departments)

	datas = zip(subjects, departments)

	return render(request, "Patient_Guide/Patient_Guide_7.html", {
		'datas': datas,
	})

# 繳費機介紹
def A002_payment_machine(request):
	return render(request, "Patient_Guide/Patient_Guide_5.html", {})
# 自助掛號機介紹
def A002_self_service(request):
	return render(request, "Patient_Guide/Patient_Guide_6.html", {})

# 資料申請
def A002_data_apply(request):
	return render(request, "Patient_Guide/Patient_Guide_8.html", {})

# =========================================A003(醫療支援部門)=========================================

# 醫療支援-科室總覽
def A003_Medical_Support(request):

	return render(request, "MedicalSupport/d-support_index.html", {})

# 急診醫學科
def A003_ER(request):
	return render(request, "MedicalSupport/ER/ER-index.html", {})

def A003_ER_1(request):
	return render(request, "MedicalSupport/ER/ER-1.html", {})

def A003_ER_2(request):
	return render(request, "MedicalSupport/ER/ER-Service-2.html", {})

def A003_AED(request):
	return render(request, "MedicalSupport/ER/AED-index.html", {})

def A003_AED_1(request):
	return render(request, "MedicalSupport/ER/AED-1.html", {})

def A003_Story_1(request):
	return render(request, "MedicalSupport/ER/ER-Story-1.html", {})

def A003_Story_2(request):
	return render(request, "MedicalSupport/ER/ER-Story-2.html", {})

# 檢驗科
def A003_Laboratory(request):
	# try:
	# 	if ("HTTP_X_FORWARDED_FOR" in request.META):
	# 		user_ip = request.META["HTTP_X_FORWARDED_FOR"]
	# 	else:
	# 		user_ip = request.META["REMOTE_ADDR"]

	# 	MSSQLAPI.Insert_LOG_WEB(user_ip, "/A003_Laboratory/")
	# except Exception as e:
	# 	MSSQLAPI.Insert_LOG_WEB("ERROR", str(e))

	return render(request, "MedicalSupport/Laboratory/labor-index.html", {})

def A003_Laboratory_1(request):
	return render(request, "MedicalSupport/Laboratory/labor-1.html", {})

def A003_Laboratory_2(request):
	return render(request, "MedicalSupport/Laboratory/labor-2.html", {})

# def A003_Laboratory_3(request):
# 	return render(request, "MedicalSupport/Laboratory/labor-3.html", locals())

def A003_Laboratory_4(request):
	return render(request, "MedicalSupport/Laboratory/labor-4.html", {})

def A003_labor_blood(request):
	return render(request, "MedicalSupport/Laboratory/labor-blood-index.html", {})

def A003_labor_blood_2(request):
	return render(request, "MedicalSupport/Laboratory/labor-blood-2.html", {})

def A003_labor_blood_3(request):
	return render(request, "MedicalSupport/Laboratory/labor-blood-3.html", {})

def A003_labor_clinical(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-index.html", {})

def A003_labor_clinical_1(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-1.html", {})

def A003_labor_clinical_2(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-2.html", {})

def A003_labor_clinical_3(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3.html", {})

def A003_labor_clinical_3_3c(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-3c.html", {})

def A003_labor_clinical_3_art(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-artery.html", {})

def A003_labor_clinical_3_baby(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-baby.html", {})

def A003_labor_clinical_3_blood(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-blood.html", {})

def A003_labor_clinical_3_cav(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-cavity.html", {})

def A003_labor_clinical_3_csf(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-csf.html", {})

def A003_labor_clinical_3_dung(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-dung.html", {})

def A003_labor_clinical_3_ra(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-igra.html", {})

def A003_labor_clinical_3_phlegm(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-phlegm.html", {})

def A003_labor_clinical_3_prepare(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-prepare.html", {})

def A003_labor_clinical_3_respiratory(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-respiratory.html", {})

def A003_labor_clinical_3_semen(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-semen.html", {})

def A003_labor_clinical_3_solid(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-solidification.html", {})

def A003_labor_clinical_3_sugar(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-sugar.html", {})

def A003_labor_clinical_3_tract(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-tract.html", {})

def A003_labor_clinical_3_urine(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-urine.html", {})

def A003_labor_clinical_3_vein(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-vein.html", {})

def A003_labor_clinical_3_wine(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-3-wine.html", {})

def A003_labor_clinical_4(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4.html", {})

def A003_labor_clinical_4_abscess(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-abscess.html", {})

def A003_labor_clinical_4_bf(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-bodyfluid.html", {})

def A003_labor_clinical_4_bottle(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-bottle.html", {})

def A003_labor_clinical_4_collection(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-collection.html", {})

def A003_labor_clinical_4_dung(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-dung.html", {})

def A003_labor_clinical_4_eye(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-eye.html", {})

def A003_labor_clinical_4_respiratory(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-respiratory.html", {})

def A003_labor_clinical_4_urine(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-4-urine.html", {})

def A003_labor_clinical_5(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-5.html", {})

def A003_labor_clinical_6(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-6.html", {})

def A003_labor_clinical_7(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-7.html", {})

def A003_labor_clinical_8(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-8.html", {})

def A003_labor_clinical_9(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-9.html", {})

def A003_labor_clinical_in_b(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-blood.html", {})

def A003_labor_clinical_in_du(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-dung.html", {})

def A003_labor_clinical_in_glu(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-glucose.html", {})

def A003_labor_clinical_in_ig(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-igra.html", {})

def A003_labor_clinical_in_occ(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-occult.html", {})

def A003_labor_clinical_in_pin(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-pinworm.html", {})

def A003_labor_clinical_in_sem(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-semen.html", {})

def A003_labor_clinical_in_spu(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-sputum.html", {})

def A003_labor_clinical_in_third(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-thirteen.html", {})

def A003_labor_clinical_in_urine(request):
	return render(request, "MedicalSupport/Laboratory/labor-clinical-in-urine.html", {})

def A003_labor_Genetic(request):
	return render(request, "MedicalSupport/Laboratory/labor-Genetic-index.html", {})

def A003_labor_Genetic_1(request):
	return render(request, "MedicalSupport/Laboratory/labor-Genetic-1.html", {})

def A003_labor_pathology(request):
	return render(request, "MedicalSupport/Laboratory/labor-pathology-index.html", {})

def A003_labor_pathology_1(request):
	return render(request, "MedicalSupport/Laboratory/labor-pathology-1.html", {})

def A003_labor_pathology_2(request):
	return render(request, "MedicalSupport/Laboratory/labor-pathology-2.html", {})

def A003_labor_pathology_3(request):
	return render(request, "MedicalSupport/Laboratory/labor-pathology-3.html", {})

def A003_labor_pathology_4(request):
	return render(request, "MedicalSupport/Laboratory/labor-pathology-4.html", {})


def get_values(sheet):
	arr = []                      # 第一層串列
	for row in sheet:
		arr2 = []                 # 第二層串列
		for column in row:
			arr2.append(column.value)  # 寫入內容
		arr.append(arr2)
	return arr

def A003_labor_pathology_5(request):
	wb = openpyxl.load_workbook(os.path.join(settings.BASE_DIR, 'Public', 'apps', 'MedicalSupport', 'Laboratory', 'excel', 'pathology.xlsx'))
	names = wb.sheetnames
	s2 = wb.active

	data = get_values(s2)
	del data[0]

	data2 = []

	search_keywords = request.GET.get("search_keywords", "")
	search_keywords = search_keywords.lower()

	for d in data:
		if ((search_keywords in str(d[1]).lower()) or (search_keywords in str(d[3]).lower()) or (search_keywords in str(d[4]).lower()) or (search_keywords in str(d[12]).lower())):
			data2.append(d)

	return render(request, "MedicalSupport/Laboratory/labor-pathology-5_v3.html", {
		'data2': data2,
		'search_keywords': search_keywords,
	})

# =========================================A004(關於長安)=============================================

# 長安簡介
def A004_hos_intro(request):
	path = os.path.join(settings.MEDIA_ROOT, 'A004', 'about.txt')
	data = open(path, "r", encoding="utf-8")
	data_lines = data.readlines()

	return render(request, "department/m_intro_index.html", {
		'data_lines': data_lines,
	})

# 交通資訊
def A004_hos_traffic_info(request):
	return render(request, "department/m_intro_1.html", {})

# =========================================A005(收費標準)=============================================

# 自費項目
def A005_Self_fee(request):
	return render(request, "department/Self_fee_index.html", {})

# 自付差額特材
# def A005_Diff_fee(request):
# 	return render(request, "department/Diff_fee_index.html", locals()) # 秀出網頁

# 病房訊息_病人住院流程
def A005_ward_mes_1(request):
	return render(request, "department/ward_mes_1.html", {})

# 病房訊息_住院須知
# def A005_ward_mes_2(request):
	#return render(request, "department/ward_mes_2.html", locals())  秀出網頁

# 病房訊息_病人出院流程
def A005_ward_mes_3(request):
	return render(request, "department/ward_mes_3.html", {})

# 病房訊息_病房訊息
def A005_ward_mes_0(request):
	return render(request, "department/ward_mes_index.html", {})

# =========================================A006(網路掛號)=========================================
# 取得下一個月一號
def get_next_month_start(add_month):
	month_str = datetime.date.today().strftime("%Y-%m")
	year, month = int(month_str.split("-")[0]),int(month_str.split("-")[1])
	if (month == 12) and (add_month == 1):
		year += 1
		month = 1
	elif (month == 11) and (add_month == 2):
		year += 1
		month = 1
	elif (month == 12) and (add_month == 2):
		year += 1
		month = 2
	else:
		month += add_month

	return("{}/{}/01".format(year, str(month).zfill(2)))

# 登出
def A006_sign_out(request):
	request.session.flush()
	return redirect("/A006_Online_Booking_0/")
# 掛號
def A006_register(request):
	now = datetime.datetime.now()
	if (s_time < now) and (now < e_time):
		A006_True = "True"
		return render(request, "Patient_Guide/Patient_Guide_2_stop.html", {
			'A006_True': A006_True,
		})
	else:
		A006_now = datetime.datetime.now()
		A006_now = datetime.datetime.strftime(A006_now,"%H:%M:%S")
		A006_today = datetime.datetime.now()
		A006_today = datetime.datetime.strftime(A006_today,"%Y%m%d")

		if (request.session["A006_first"] == "0"):
			idno = " "
			patid = request.session["A006_patid"]
			visitdt = request.session["A006_user_visitdt"]
			shiftno = request.session["A006_user_shiftno"]
			roomno = request.session["A006_user_roomno"]
			sectno = request.session["A006_user_sectno"]
			doccd = request.session["A006_user_doccd"]

			if ((visitdt == A006_today) and (shiftno == "1") and (A006_now > "11:45:00")) or (A006_today > visitdt):
				return HttpResponse("超過早診預約時間")
			elif ((visitdt == A006_today) and (shiftno == "2") and (A006_now > "16:45:00")) or (A006_today > visitdt):
				return HttpResponse("超過午診預約時間")
			elif ((visitdt == A006_today) and (shiftno == "3") and (A006_now > "20:30:00")) or (A006_today > visitdt):
				return HttpResponse("超過晚診預約時間")
			else:
				# 查詢當日資料序號（需使用交易機制?）
				recno = MSSQLAPI.A006_Search_NRGRGS_RECNO(visitdt)
				if (recno == None):
					MSSQLAPI.A006_Insert_NRGRGS_RECNO(visitdt)
					recno = 1
					MSSQLAPI.Insert_LOG_WEB(patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd)
					resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
					request.session["A006_user_recno"] = recno
				else:
					insert_ok = True
					recno = recno[2] + 1
					# while(insert_ok):
					MSSQLAPI.A006_Update_NRGRGS_RECNO(visitdt)
						# try:
					print(987654321)
					insert_ok = False
					MSSQLAPI.Insert_LOG_WEB(patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd)
					resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
					request.session["A006_user_recno"] = recno
						# except:
						# 	time.sleep(1)
						# 	recno = MSSQLAPI.A006_Search_NRGRGS_RECNO(visitdt)
						# 	recno = recno[2] + 1
						# 	insert_ok = True

		elif (request.session["A006_first"] == "1"):
			patid = " "
			visitdt = request.session["A006_user_visitdt"]
			shiftno = request.session["A006_user_shiftno"]
			roomno = request.session["A006_user_roomno"]
			sectno = request.session["A006_user_sectno"]
			doccd = request.session["A006_user_doccd"]

			pat_name = request.session["pat_name"]
			pat_id = request.session["pat_id"]
			pat_birthday = request.session["pat_birthday"]
			birthday = pat_birthday[:4] + pat_birthday[4:6] + pat_birthday[6:8]
			pat_sex = request.session["pat_sex"]
			pat_phone = request.session["pat_phone"]

			if ((visitdt == A006_today) and (shiftno == "1") and (A006_now > "11:45:00")) or (A006_today > visitdt):
				return HttpResponse("超過早診預約時間")
			elif ((visitdt == A006_today) and (shiftno == "2") and (A006_now > "16:45:00")) or (A006_today > visitdt):
				return HttpResponse("超過午診預約時間")
			elif ((visitdt == A006_today) and (shiftno == "3") and (A006_now > "20:30:00")) or (A006_today > visitdt):
				return HttpResponse("超過晚診預約時間")
			else:
				# 查詢當日資料序號（需使用交易機制?）
				recno = MSSQLAPI.A006_Search_NRGRGS_RECNO(visitdt)
				# print(recno)
				if (recno == None):
					MSSQLAPI.A006_Insert_NRGRGS_RECNO(visitdt)
					recno = 1
					MSSQLAPI.Insert_LOG_WEB(patid, pat_id, visitdt, recno, shiftno, roomno, sectno, doccd)
					resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
					request.session["A006_user_recno"] = recno
					resluet2 = MSSQLAPI.A006_Insert_NRGPATTEMP(visitdt, recno, pat_id, pat_name, pat_sex, birthday, pat_phone)
				else:
					insert_ok = True
					recno = recno[2] + 1
					# while(insert_ok):
					resluet3 = MSSQLAPI.A006_Update_NRGRGS_RECNO(visitdt)
						# try:

					print(123456789)
					insert_ok = False
					MSSQLAPI.Insert_LOG_WEB(patid, pat_id, visitdt, recno, shiftno, roomno, sectno, doccd)

					resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
					# print(resluet1)
					resluet2 = MSSQLAPI.A006_Insert_NRGPATTEMP(visitdt, recno, pat_id, pat_name, pat_sex, birthday, pat_phone)
					request.session["A006_user_recno"] = recno
						# except:
						# 	time.sleep(1)
						# 	recno = MSSQLAPI.A006_Search_NRGRGS_RECNO(visitdt)
						# 	recno = recno[2] + 1
						# 	insert_ok = True

		return HttpResponse("OK")

# 掛號結果
def A006_find_register(request):
	now = datetime.datetime.now()
	if (s_time < now) and (now < e_time):
		A006_True = "True"
		return render(request, "Patient_Guide/Patient_Guide_2_stop.html", {
			'A006_True': A006_True,
		})
	else:
		if (request.session["A006_first"] == "0"):
			# patid = request.session["A006_patid"]
			# data = MSSQLAPI.A006_Search_NRGRGB_BY_PATID(patid)
			# print(data)
			# recno = data[8]
			# 20240418 看要不要使用try保護沒有recno的時候可以用病歷號+看診日去查詢
			recno = request.session["A006_user_recno"]
			visitdt = request.session["A006_user_visitdt"]

			visitno = MSSQLAPI.A006_Search_NRGRGB_VISITNO(visitdt, recno)
			del request.session["A006_user_recno"]

		elif (request.session["A006_first"] == "1"):
			# patid = request.session["A006_patid"]
			# data = MSSQLAPI.A006_Search_NRGRGB_BY_PATID(patid)
			# print(data)
			# recno = data[8]
			recno = request.session["A006_user_recno"]
			visitdt = request.session["A006_user_visitdt"]

			visitno = MSSQLAPI.A006_Search_NRGRGB_VISITNO(visitdt, recno)
			del request.session["A006_user_recno"]

			user_acc = request.session["A006_acc"]
			user_pwd = request.session["A006_pwd"]
			A006_user_data = MSSQLAPI.A006_Search_NRGPAT(user_acc)
			if (A006_user_data != None):
				request.session["A006_patid"] = A006_user_data[0]
				request.session["A006_patname"] = A006_user_data[1]
				request.session["A006_first"] = "0"
			else:
				print("無使用者病歷號！")
				return redirect("/A006_Online_Booking_first/")

		return HttpResponse(visitno)

# 退掛
def A006_out_register(request):
	now = datetime.datetime.now()
	if (s_time < now) and (now < e_time):
		A006_True = "True"
		return render(request, "Patient_Guide/Patient_Guide_2_stop.html", {
			'A006_True': A006_True,
		})
	else:
		patid = request.session["A006_patid"]
		visitdt = request.GET.get("A006_user_visitdt")
		recno = request.GET.get("A006_user_recno")

		patid_sure = MSSQLAPI.A006_Search_NRGRGB_PATID_SURE(patid, visitdt, recno)

		if (patid_sure != None):
			reslute = MSSQLAPI.A006_Update_NRGRGS_CANCEL(visitdt, recno)
			return HttpResponse(reslute)
		else:
			return HttpResponse("請先登入正確的使用者!")

# 網路掛號_初診複診判斷
def A006_Online_Booking_0(request):
	now = datetime.datetime.now()
	if (s_time < now) and (now < e_time):
		A006_True = "True"
		return render(request, "Patient_Guide/Patient_Guide_2_stop.html", {
			'A006_True': A006_True,
		})
	else:
		if (now < e_time):
			A006_Stop = "True"
		A006_True = "True"
		if ("A006_acc" in request.session):
			request.session["A006_first"] = "0"
			# print(request.session["A006_first"])
			if not ("A006_patid" in request.session):
				request.session["A006_first"] = "1"
				user_acc = request.session["A006_acc"]
				user_pwd = request.session["A006_pwd"]
				try:
					A006_user_data = MSSQLAPI.A006_Search_NRGPAT(user_acc)
					request.session["A006_patid"] = A006_user_data[0]
					request.session["A006_patname"] = A006_user_data[1]
				except Exception as e:
					pass

			return redirect("/A006_Online_Booking_0_0/")

		if ("A006_first" in request.session):
			del request.session["A006_first"]

		# 目前如果是轉址過來的話，若再點選首頁，則選擇初/複診時，會導回前一網址，不是首頁
		if ("referrer" in request.session):
			referrer = request.session.get("referrer")
			if ("first" in request.GET):
				A006_first = request.GET.get("first", None)
				request.session["A006_first"] = A006_first
				if (A006_first == "1"):
					return redirect("/A006_Online_Booking_first/")
				else:
					del request.session["referrer"]

					return redirect(referrer)
		else:
			if ("first" in request.GET):
				A006_first = request.GET.get("first", None)
				request.session["A006_first"] = A006_first

				if (A006_first == "1"):
					return redirect("/A006_Online_Booking_first/")
				else:
					return redirect("/A006_Online_Booking_0_0/")

		return render(request, "Patient_Guide/Patient_Guide_2.html", {
			'A006_True': A006_True,
			'A006_Stop': A006_Stop if 'A006_Stop' in locals() else None,
			'referrer': referrer if 'referrer' in locals() else None,
		})

# 網路掛號_首頁
def A006_Online_Booking_0_0(request):
	A006_True = "True"

	return render(request, "Patient_Guide/Patient_Guide_2_0.html", {
		'A006_True': A006_True,
	})

# 網路掛號_登入頁
# 是否有包括海外簽證號
@csrf_exempt
def A006_Online_Booking_login(request):
	now = datetime.datetime.now()
	if (s_time < now) and (now < e_time):
		A006_True = "True"
		return render(request, "Patient_Guide/Patient_Guide_2_stop.html", {
			'A006_True': A006_True,
		})
	else:
		A006_True = "True"
		# 未選擇初/複診，轉址回選擇
		# if not ("A006_first" in request.session):
		# 	url = request.get_full_path()
		# 	request.session["referrer"] = str(url)
		# 	return redirect("/A006_Online_Booking_0/")

		# 紀錄要掛號的資訊
		if ("A006_check_in" in request.POST):
			visitdt = request.POST.get("user_visitdt", None).replace("/","")
			shiftno = request.POST.get("user_shiftno", None)
			sectno = request.POST.get("user_sectno", None)
			doccd = request.POST.get("user_doccd", None)

			request.session["A006_check_in"] = "true"
			request.session["A006_user_visitdt"] = visitdt
			request.session["A006_user_shiftno"] = shiftno
			request.session["A006_user_sectno"] = sectno
			request.session["A006_user_doccd"] = doccd

			# 查詢要掛號診間號
			roomno = MSSQLAPI.A006_Search_SCD_ROOMNO(visitdt, shiftno, sectno, doccd)[0]
			request.session["A006_user_roomno"] = roomno

		# 已輸入帳號密碼的情況，轉址到紀錄查詢
		if ("A006_acc" in request.session) and ("A006_pwd" in request.session):
			if ("A006_check_in" in request.session):
				return redirect("/A006_Online_Booking_check/")
			else:
				return redirect("/A006_Online_Booking_data/")
		# 未輸入帳號密碼的情況
		elif ("ID_card" in request.POST) and ("Birthday" in request.POST):
			user_acc = request.POST.get("ID_card", None)
			user_pwd = request.POST.get("Birthday", None)
			""" 20241225新增網路掛號登入log """
			MSSQLAPI.insertA006LoginLogWeb(user_acc, user_pwd, "A006_Online_Booking_login")
			"""end"""

			user_acc = user_acc.zfill(10)
			n_user_pwd = str(int(user_pwd) + 19110000)

			""" 20241225 修正先判斷身分證是否存在病歷號，才後判斷生日是否正確 """
			A006_user_data = MSSQLAPI.A006_Search_NRGPAT(user_acc)
			try:
				# 驗證生日格式，但不輸出到控制台
				datetime.date(int(n_user_pwd[:4]), int(n_user_pwd[4:6]), int(n_user_pwd[6:8]))
				patBirthdayError = False
			except:
				patBirthdayError = True

			# 判斷若是初診，導到初診資料填寫
			if (A006_user_data == None):
				# 查無有在本院掛號紀錄，轉址到處診紀錄單
				request.session["A006_first"] = "1"
				return redirect("/A006_Online_Booking_first/")
			elif ("A006_check_in" in request.session):
				patBirthday = A006_user_data[2]
				if (patBirthday == n_user_pwd):
					request.session["A006_patid"] = A006_user_data[0]
					request.session["A006_patname"] = A006_user_data[1]
					request.session["A006_acc"] = user_acc
					request.session["A006_pwd"] = user_pwd
					return redirect("/A006_Online_Booking_check/")
				else:
					errorMessageOn = "true"
					errorMessage = "您的身分證字號或生日日期有錯誤！"
			else:
				patBirthday = A006_user_data[2]
				if (patBirthday == n_user_pwd) and (patBirthdayError == False):
					request.session["A006_first"] = "0"
					request.session["A006_patid"] = A006_user_data[0]
					request.session["A006_patname"] = A006_user_data[1]
					request.session["A006_acc"] = user_acc
					request.session["A006_pwd"] = user_pwd
					return redirect("/A006_Online_Booking_data/")
				else:
					errorMessageOn = "true"
					errorMessage = "您的身分證字號或生日日期有錯誤！"

			"""end"""

		# 準備模板變數，只有在有錯誤訊息時才保留輸入值
		template_vars = {
			'A006_True': A006_True,
			'errorMessageOn': errorMessageOn if 'errorMessageOn' in locals() else None,
			'errorMessage': errorMessage if 'errorMessage' in locals() else None,
		}
		# 只有在有錯誤訊息時才傳遞輸入值，否則不傳遞以保持空白
		if 'errorMessageOn' in locals() and errorMessageOn == "true":
			if 'user_acc' in locals() and user_acc is not None:
				template_vars['user_acc'] = user_acc
			if 'user_pwd' in locals() and user_pwd is not None:
				template_vars['user_pwd'] = user_pwd
		
		return render(request, "Patient_Guide/Patient_Guide_2_4_v8.html", template_vars)

# 網路掛號_初診資料建立
@csrf_exempt
def A006_Online_Booking_first(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	if ("creat_data" in request.POST):
		pat_name = request.POST.get("ID_name")
		pat_id = request.POST.get("ID_card")
		pat_phone = request.POST.get("Contact_phone")
		pat_birthday = request.POST.get("Birthday")
		pat_birthday = str(int(pat_birthday) + 19110000)
		pat_sex = request.POST.get("customRadioInline1")

		# 查詢是否已有資料
		data = MSSQLAPI.A006_Search_NRGPAT_EXISIT(pat_id)

		# 新增初診資料
		if (data == None):
			request.session["pat_name"] = pat_name
			request.session["A006_patname"] = pat_name
			request.session["pat_id"] = pat_id.strip()
			request.session["pat_phone"] = pat_phone
			request.session["pat_birthday"] = pat_birthday
			request.session["pat_sex"] = pat_sex
			request.session["A006_acc"] = pat_id
			request.session["A006_pwd"] = pat_birthday
			showalert = "true"
		else:
			showalert_error = "true"

	if ("pat_sex" in request.session):
		return redirect("/A006_Online_Booking_0_0/")

	return render(request, "Patient_Guide/Patient_Guide_2_5_v8.html", {
		'A006_True': A006_True,
		'showalert': showalert if 'showalert' in locals() else None,
		'showalert_error': showalert_error if 'showalert_error' in locals() else None,
	})

# 網路掛號_預約資料確認
def A006_Online_Booking_check(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	if (request.session["A006_first"] == "0"):
		visitdt = request.session["A006_user_visitdt"]
		n_visitdt = visitdt[:4] + "-" + visitdt[4:6] + "-" + visitdt[6:8]

		shiftno = request.session["A006_user_shiftno"]
		if (shiftno == "1"):
			n_shiftno = "早"
		elif (shiftno == "2"):
			n_shiftno = "午"
		elif (shiftno == "3"):
			n_shiftno = "夜"
		sectno = request.session["A006_user_sectno"]
		n_sectno = MSSQLAPI.A006_Search_NRGSEC_SHOWNAME(sectno)[0]
		doccd = request.session["A006_user_doccd"]
		n_doccd = PLSQLAPI.A006_Search_BASEMP_EMPNAME(doccd)
		roomno = request.session["A006_user_roomno"]
		n_roomno = roomno[1:]
		patid = request.session["A006_patid"]
		pat_data = MSSQLAPI.A006_Search_NRGPAT_BY_PATID(patid)
		request.session["pat_data"] = pat_data

		birthday = pat_data[2][:4] + "-" + pat_data[2][4:6] + "-" + pat_data[2][6:8]
		if (pat_data[3] == "M"):
			sex = "男"
		else:
			sex = "女"

		# 限制預約（之後再維護優化）
		A006_today = datetime.datetime.now()
		A006_today = datetime.datetime.strftime(A006_today,"%Y%m%d")
		age = int(A006_today) - int(pat_data[2])

		if (request.session["A006_user_sectno"] in ["12","AB","AC","AA","01","AG","AD"]) and (age < 180000):
			stop_reserve_on = True
		elif (request.session["A006_user_sectno"] in ["09"]) and (age < 120000):
			stop_reserve_on = True

		# 查詢是否有重複預約
		repeat_data = MSSQLAPI.A006_Search_NRGRGB_FOR_PATID(patid, visitdt, shiftno, doccd)

		if (repeat_data != None):
			repeat_data_on = True

	elif (request.session["A006_first"] == "1"):
		visitdt = request.session["A006_user_visitdt"]
		n_visitdt = visitdt[:4] + "-" + visitdt[4:6] + "-" + visitdt[6:8]

		shiftno = request.session["A006_user_shiftno"]
		if (shiftno == "1"):
			n_shiftno = "早"
		elif (shiftno == "2"):
			n_shiftno = "午"
		elif (shiftno == "3"):
			n_shiftno = "夜"
		sectno = request.session["A006_user_sectno"]
		n_sectno = MSSQLAPI.A006_Search_NRGSEC_SHOWNAME(sectno)[0]
		doccd = request.session["A006_user_doccd"]
		n_doccd = PLSQLAPI.A006_Search_BASEMP_EMPNAME(doccd)
		roomno = request.session["A006_user_roomno"]
		n_roomno = roomno[1:]
		pat_name = request.session["pat_name"]
		pat_id = request.session["pat_id"]
		pat_birthday = request.session["pat_birthday"]
		birthday = pat_birthday[:4] + "-" + pat_birthday[4:6] + "-" + pat_birthday[6:8]

		pat_sex = request.session["pat_sex"]

		if (pat_sex == "M"):
			sex = "男"
		else:
			sex = "女"

		# 限制預約（之後再維護優化）
		A006_today = datetime.datetime.now()
		A006_today = datetime.datetime.strftime(A006_today,"%Y%m%d")
		age = int(A006_today) - int(pat_birthday)

		stop_reserve_on = False
		repeat_data_on = False
		specialSectno = False
		if (request.session["A006_user_sectno"] in ["12","AB","AC","AA","01","AG","AD"]) and (age < 180000):
			stop_reserve_on = True
		elif (request.session["A006_user_sectno"] in ["09"]) and (age < 120000):
			stop_reserve_on = True

	return render(request, "Patient_Guide/Patient_Guide_2_6_v3.html", {
		'A006_True': A006_True,
		'stop_reserve_on': stop_reserve_on,
		'repeat_data_on': repeat_data_on,
		'specialSectno': specialSectno,
		'pat_data': pat_data,
		'pat_name': pat_name,
		'n_sectno': n_sectno,
		'n_doccd': n_doccd,
		'n_visitdt': n_visitdt,
		'n_shiftno': n_shiftno,
		'n_roomno': n_roomno,
		'pat_id': pat_id,
		'birthday': birthday,
		'sex': sex,
	})

# 網路掛號_掛號資料查詢、取消
def A006_Online_Booking_data(request):
	A006_True = "True"
	# if not ("A006_first" in request.session):
	# 	url = request.get_full_path()
	# 	request.session["referrer"] = str(url)
	# 	return redirect("/A006_Online_Booking_0/")

	# 20250922 新增初診掛號顯示判斷，若為臨時病歷號，則顯示需要先去填寫初診單
	# 如果有抓到正確的診號，則彈出取到的診號
	if ("visitno" in request.GET):
		visitno = request.GET.get("visitno")
		visitno = int(int(visitno) / 10)
		if ("E" in request.session["A006_patid"] or request.session["A006_first"] == "1"):
			showfancybox = "True"
		else:
			showalert = "True"

	# 已填初診單但未完成一次掛號的病人，是無法取的病歷號
	if ("pat_id" in request.session):
		user_acc = request.session["pat_id"]
		pat_birthday = request.session["pat_birthday"]
		user_pwd = pat_birthday[:4] + pat_birthday[4:6] + pat_birthday[6:8]
		A006_user_data = MSSQLAPI.A006_Search_NRGPAT(user_acc)
		if (A006_user_data != None):
			request.session["A006_patid"] = A006_user_data[0]
			request.session["A006_patname"] = A006_user_data[1]
			request.session["A006_first"] = "0"
		else:
			print("無使用者病歷號！")
			no_patid = True
			# return redirect("/A006_Online_Booking_first/")

	if ("A006_patid" in request.session):
		patid = request.session.get("A006_patid")
		data = MSSQLAPI.A006_Search_NRGRGB_BY_PATID(patid)

		n_data = []
		i = 0
		for d in data:
			n_data.append(list(data[i]))
			n_day = d[2][:4] + "-" + d[2][4:6] + "-" + d[2][6:8]
			n_data[i][2] = n_day

			if (d[3] == "1"):
				n_data[i][3] = "早"
			elif (d[3] == "2"):
				n_data[i][3] = "午"
			elif (d[3] == "3"):
				n_data[i][3] = "夜"

			n_data[i][4] = MSSQLAPI.A006_Search_NRGSEC_SHOWNAME(d[4])[0]
			n_data[i].append(d[2])
			n_data[i].append(d[3])
			n_data[i].append(d[4])
			i += 1

	elif ("pat_id" in request.session):
		if (no_patid):
			print("先讓初診但無病歷號的可以查詢，雖然沒意義")

	else:
		return redirect("/A006_Online_Booking_login/")

	# 20250922 新增初診掛號顯示判斷，Patient_Guide_2_3_v2
	showalert = None
	visitno = None
	showfancybox = None
	if 'showalert' in locals():
		showalert = locals().get('showalert')
	if 'visitno' in locals():
		visitno = locals().get('visitno')
	if 'showfancybox' in locals():
		showfancybox = locals().get('showfancybox')
	return render(request, "Patient_Guide/Patient_Guide_2_3_v2.html", {
		'A006_True': A006_True,
		'showalert': showalert,
		'visitno': visitno,
		'n_data': n_data,
		'showfancybox': showfancybox,
	})

# 網路掛號_選擇科別
def A006_Online_Booking_1(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	subjects = []
	django_subjects = []
	senames = []

	s_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department'))
	for s_dir in s_dirs:
		if ("D000" in s_dir):
			subjects.append(s_dir.split("_")[2])
			django_subjects.append(s_dir)

	for subject in django_subjects:
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))
		django_senames = []
		for d_dir in d_dirs:
			if (len(d_dir.split("_")) == 2):
				django_senames.append(d_dir.split("_")[1])
		senames.append(django_senames)

	datas = zip(subjects, senames)
	return render(request, "Patient_Guide/Patient_Guide_2_1.html", {
		'A006_True': A006_True,
		'datas': datas,
	})

# 網路掛號_選擇科別_當週該科醫師列表
def A006_Online_Booking_1_part(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	if ("A006_width" in request.GET):
		A006_width = int(request.GET.get("A006_width"))

	A006_now = datetime.datetime.now()
	A006_now = datetime.datetime.strftime(A006_now,"%H:%M:%S")

	A006_radio_day_1 = datetime.date.today()
	A006_radio_day_2 = get_next_month_start(1)
	A006_radio_day_3 = get_next_month_start(2)
	A006_radio_day_1 = datetime.datetime.strftime(A006_radio_day_1,"%Y.%m")
	A006_radio_day_2 = A006_radio_day_2.replace("/", ".")[:7]
	A006_radio_day_3 = A006_radio_day_3.replace("/", ".")[:7]

	sename = request.GET.get("A006_sename")
	if (sename == "高壓氧中心"):
		sename = "骨科"

		return redirect("/A006_Online_Booking_2_1/?A006_sename=骨科&A006_userid=HA01855")
	# print(sename)
	A006_I000 = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}', 'I000*'))

	# 科室介紹資訊
	I000_concent = open(A006_I000[0], "r", encoding="utf-8")
	A006_I000_list = I000_concent.readlines()
	I000_concent.close()

	# 查詢科別代碼
	sectno = MSSQLAPI.A006_Search_SEC_SECTNO_BY_SENAME(sename)

	I000_day_list = []				# 一週日期
	I000_weekday_list = []			# 一週星期對照
	I000_lookday_list_s = []		# 一週早班資料
	I000_lookday_list_a = []		# 一周午班資料
	I000_lookday_list_n = []		# 一週夜班資料
	I000_day_compare_list = []

	# 一週起始日的判斷
	# 上線前要增加3個月的限制
	if ("A006_date_add" in request.GET):
		A006_now_date = request.GET.get("A006_date_check")
		I000_days = datetime.datetime.strptime(A006_now_date, "%Y/%m/%d")
		I000_days_limit = datetime.datetime.now()
		I000_days_limit = I000_days_limit + datetime.timedelta(days=90)
		I000_days = I000_days + datetime.timedelta(days=7)
		if (I000_days > I000_days_limit):
			I000_days_limit_start = True
			I000_days = I000_days_limit
	elif ("A006_date_sub" in request.GET):
		A006_now_date = request.GET.get("A006_date_check")
		A006_today = datetime.date.today().strftime("%Y/%m/%d")
		if (A006_today == A006_now_date):
			I000_days = datetime.date.today()
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		else:
			I000_days = datetime.datetime.strptime(A006_now_date, "%Y/%m/%d")
			I000_days = I000_days - datetime.timedelta(days=7)
	# 醫師介面選擇的月份
	elif ("switch_day" in request.GET) and (A006_width > 768):
		switch_day = int(request.GET.get("switch_day"))
		if (switch_day == 1):
			I000_days = datetime.date.today()
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		elif (switch_day == 2):
			I000_days = datetime.date.today()
			I000_days = get_next_month_start(1)
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		elif (switch_day == 3):
			I000_days = datetime.date.today()
			I000_days = get_next_month_start(2)
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
		elif (switch_day == 4):
			I000_days = "2025/04/08"
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
	elif ("switch_day2" in request.GET) and (A006_width <= 767):
		switch_day2 = int(request.GET.get("switch_day2"))
		if (switch_day2 == 1):
			I000_days = datetime.date.today()
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 2):
			I000_days = datetime.date.today()
			I000_days = get_next_month_start(1)
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 3):
			I000_days = datetime.date.today()
			I000_days = get_next_month_start(2)
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 4):
			I000_days = "2025/04/08"
			I000_days = datetime.datetime.strptime(I000_days, "%Y/%m/%d")
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
	else:
		I000_days = datetime.date.today()
		day_sub = I000_days.isoweekday() - 1
		I000_days = I000_days - datetime.timedelta(days=day_sub)

	# 當週該科醫師掛號資料
	startdt = I000_days
	c_startdt = startdt.strftime("%Y%m%d")
	enddt = startdt + datetime.timedelta(days=6)
	I000_lookday_data = MSSQLAPI.A006_Search_NRGSCD_BY_SECTNO(sectno, startdt.strftime("%Y%m%d"), enddt.strftime("%Y%m%d"))

	for i in range(7):
		# 建立一周日期
		I000_day_list.append(I000_days.strftime("%Y/%m/%d"))
		I000_day_compare_list.append(I000_days.strftime("%Y%m%d"))

		# 建立一周星期中文對照
		I000_weekday = I000_days.weekday()
		if (I000_weekday == 0):
			I000_weekday = "(一)"
		elif (I000_weekday == 1):
			I000_weekday = "(二)"
		elif (I000_weekday == 2):
			I000_weekday = "(三)"
		elif (I000_weekday == 3):
			I000_weekday = "(四)"
		elif (I000_weekday == 4):
			I000_weekday = "(五)"
		elif (I000_weekday == 5):
			I000_weekday = "(六)"
		elif (I000_weekday == 6):
			I000_weekday = "(日)"
		I000_weekday_list.append(I000_weekday)

		# 新增下一筆
		I000_days = I000_days + datetime.timedelta(days=1)

	I000_lookday_list_ss = []
	I000_lookday_list_aa = []
	I000_lookday_list_nn = []
	for lookday_data in I000_lookday_data:
		if (lookday_data[1] == "1"):
			I000_lookday_list_ss.append([lookday_data[0], lookday_data[2], lookday_data[4]])
		elif (lookday_data[1] == "2"):
			I000_lookday_list_aa.append([lookday_data[0], lookday_data[2], lookday_data[4]])
		elif (lookday_data[1] == "3"):
			I000_lookday_list_nn.append([lookday_data[0], lookday_data[2], lookday_data[4]])

	A006_today = datetime.datetime.now()
	A006_today = datetime.datetime.strftime(A006_today,"%Y%m%d")

	data_counts = MSSQLAPI.A006_Search_NRGNPRO_COUNT_BY_SECTNO(sectno, I000_day_compare_list[0], I000_day_compare_list[6])
	# print(data_counts)
	data_counts_s = []
	data_counts_a = []
	data_counts_n = []
	for data_count in data_counts:
		if (int(data_count[3]) == 1):
			data_counts_s.append(data_count)
		elif (int(data_count[3]) == 2):
			data_counts_a.append(data_count)
		elif (int(data_count[3]) == 3):
			data_counts_n.append(data_count)

	# print(data_counts_a)

	# 代診是否改良，待確認
	# data_replaces = MSSQLAPI.A006_Search_NRGSCD_DATA_BY_SECTNO(sectno, I000_day_compare_list[0], I000_day_compare_list[6])
	# # print(data_counts)
	# data_replace_s = []
	# data_replace_a = []
	# data_replace_n = []
	# for data_replace in data_replaces:
	# 	if (int(data_count[4]) == 1):
	# 		data_replace_s.append(data_replace)
	# 	elif (int(data_count[4]) == 2):
	# 		data_replace_a.append(data_replace)
	# 	elif (int(data_count[4]) == 3):
	# 		data_replace_n.append(data_replace)

	# 判段當日是否有看診
	for compare_day in I000_day_compare_list:
		I000_lookday_list_sss = []
		for lookday_list_ss in I000_lookday_list_ss:
			if ((compare_day == A006_today) and (A006_now > "11:45:00") or (A006_today > compare_day)) and (lookday_list_ss[0] == compare_day):
				I000_lookday_list_sss.append([compare_day, "Q", lookday_list_ss[2]])
			elif (lookday_list_ss[0] == compare_day):
				lookday_list_ss_data = []
				person_count = 0
				# 查詢診間人數
				if (len(data_counts_s) != 0):
					for data_count in data_counts_s:
						if (data_count[1] == compare_day) and (data_count[4] == lookday_list_ss[1]):
							person_count = data_count[5]
				# else:
				# 	person_count = 0
				lookday_list_ss_data.append(compare_day)
				lookday_list_ss_data.append(lookday_list_ss[2])
				lookday_list_ss_data.append(person_count)
				lookday_list_ss_data.append(lookday_list_ss[1])

				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, lookday_list_ss[1], 1)
				if (replace_data[0] == "Y") and (lookday_list_ss[2] != replace_data[2]):
					# lookday_list_ss_data.append("R")
					lookday_list_ss_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_ss_data.append(replace_data[2])
					lookday_list_ss_data.append(" ")
				else:
					lookday_list_ss_data.append("Z")
					lookday_list_ss_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					lookday_list_ss_data.append("M")

				I000_lookday_list_sss.append(lookday_list_ss_data)

		I000_lookday_list_s.append(I000_lookday_list_sss)

		I000_lookday_list_aaa = []
		for lookday_list_aa in I000_lookday_list_aa:
			if ((compare_day == A006_today) and (A006_now > "16:45:00") or (A006_today > compare_day)) and (lookday_list_aa[0] == compare_day):
				I000_lookday_list_aaa.append([compare_day, "Q", lookday_list_aa[2]])
			elif (lookday_list_aa[0] == compare_day):
				lookday_list_aa_data = []
				person_count = 0
				# 查詢診間人數
				# person_count = MSSQLAPI.A006_Search_NRGNPRO_COUNT(compare_day, sectno, lookday_list_aa[1], 2)
				if (len(data_counts_a) != 0):
					for data_count in data_counts_a:
						if (data_count[1] == compare_day) and (data_count[4] == lookday_list_aa[1]):
							person_count = data_count[5]
				# else:
				# 	person_count = 0
				lookday_list_aa_data.append(compare_day)
				lookday_list_aa_data.append(lookday_list_aa[2])
				lookday_list_aa_data.append(person_count)
				lookday_list_aa_data.append(lookday_list_aa[1])
				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, lookday_list_aa[1], 2)
				if (replace_data[0] == "Y") and (lookday_list_aa[2] != replace_data[2]):
					# lookday_list_aa_data.append("R")
					lookday_list_aa_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_aa_data.append(replace_data[2])
					lookday_list_aa_data.append(" ")
				else:
					lookday_list_aa_data.append("Z")
					lookday_list_aa_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					lookday_list_aa_data.append("M")

				I000_lookday_list_aaa.append(lookday_list_aa_data)

		I000_lookday_list_a.append(I000_lookday_list_aaa)

		I000_lookday_list_nnn = []
		for lookday_list_nn in I000_lookday_list_nn:
			if ((compare_day == A006_today) and (A006_now > "20:30:00") or (A006_today > compare_day)) and (lookday_list_nn[0] == compare_day):
				I000_lookday_list_nnn.append([compare_day, "Q", lookday_list_nn[2]])
			elif (lookday_list_nn[0] == compare_day):
				lookday_list_nn_data = []
				person_count = 0
				# 查詢診間人數
				# person_count = MSSQLAPI.A006_Search_NRGNPRO_COUNT(compare_day, sectno, lookday_list_nn[1], 3)
				if (len(data_counts_n) != 0):
					for data_count in data_counts_n:
						if (data_count[1] == compare_day) and (data_count[4] == lookday_list_nn[1]):
							person_count = data_count[5]
				# else:
				# 	person_count = 0
				lookday_list_nn_data.append(compare_day)
				lookday_list_nn_data.append(lookday_list_nn[2])
				lookday_list_nn_data.append(person_count)
				lookday_list_nn_data.append(lookday_list_nn[1])
				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, lookday_list_nn[1], 3)
				if (replace_data[0] == "Y") and (lookday_list_nn[2] != replace_data[2]):
					# lookday_list_nn_data.append("R")
					lookday_list_nn_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_nn_data.append(replace_data[2])
					lookday_list_nn_data.append(" ")
				else:
					lookday_list_nn_data.append("Z")
					lookday_list_nn_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					lookday_list_nn_data.append("M")

				I000_lookday_list_nnn.append(lookday_list_nn_data)

		I000_lookday_list_n.append(I000_lookday_list_nnn)

	datas = zip(I000_day_list, I000_weekday_list, I000_lookday_list_s, I000_lookday_list_a, I000_lookday_list_n)

	# 確保 switch_day2 有預設值
	if 'switch_day2' not in locals():
		switch_day2 = None

	return render(request, "Patient_Guide/Patient_Guide_2_1_1.html", {
		'A006_True': A006_True,
		'datas': datas,
		'sename': sename,
		'A006_I000_list': A006_I000_list,
		'A006_radio_day_1': A006_radio_day_1,
		'A006_radio_day_2': A006_radio_day_2,
		'A006_radio_day_3': A006_radio_day_3,
		'switch_day2': switch_day2,
		'I000_day_list': I000_day_list,
	})

# 網路掛號_選擇醫師
def A006_Online_Booking_2(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	subjects = []
	django_subjects = []
	doctors = []

	s_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department'))
	for s_dir in s_dirs:
		if ("D000" in s_dir):
			re_dir = s_dir.split("_")
			django_subjects.append(s_dir)

	for subject in django_subjects:
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))

		for d_dir in d_dirs:
			if (len(d_dir.split("_")) == 2):
				django_doctors = []
				django_doctors2 = []
				django_doctors3 = []
				re_subject = d_dir.split("_")
				subjects.append(re_subject[1])
				sename = re_subject[1]
				dd_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject), str(d_dir)))

				for dd_dir in dd_dirs:
					if ("D000" in dd_dir):
						red_dir = dd_dir.split("_")
						django_doctors.append(red_dir[2].split(" ")[0])
						django_doctors2.append(red_dir[3].replace(".txt", ""))
						django_doctors3.append(sename)
						z_doctors = zip(django_doctors,django_doctors2,django_doctors3)

				doctors.append(z_doctors)

	datas = zip(subjects, doctors)

	return render(request, "Patient_Guide/Patient_Guide_2_2.html", {
		'A006_True': A006_True,
		'datas': datas,
	})

# 網路掛號_個別醫師預約頁
@csrf_exempt
def A006_Online_Booking_2_1(request):
	A006_True = "True"
	if not ("A006_first" in request.session):
		url = request.get_full_path()
		request.session["referrer"] = str(url)
		return redirect("/A006_Online_Booking_0/")

	A006_radio_day_1 = datetime.date.today()
	A006_radio_day_2 = get_next_month_start(1)
	A006_radio_day_3 = get_next_month_start(2)
	A006_radio_day_1 = datetime.datetime.strftime(A006_radio_day_1,"%Y.%m")
	A006_radio_day_2 = A006_radio_day_2.replace("/", ".")[:7]
	A006_radio_day_3 = A006_radio_day_3.replace("/", ".")[:7]

	if ("A006_width" in request.GET):
		A006_width = int(request.GET.get("A006_width"))

	A006_now = datetime.datetime.now()
	A006_now = datetime.datetime.strftime(A006_now,"%H:%M:%S")

	# 選擇醫師需要帶入的參數
	if ("A006_userid" in request.GET):
		userid = request.GET.get("A006_userid"," ")
	if ("A006_sename" in request.GET):
		sename = request.GET.get("A006_sename"," ")
		if (sename == "高壓氧中心"):
			sename = "骨科"

			return redirect("/A006_Online_Booking_2_1/?A006_sename=骨科&A006_userid=HA01855")
		# 查詢科別代碼
		sectno = MSSQLAPI.A006_Search_SEC_SECTNO_BY_SENAME(sename)
	else:
		sectno = None

	# 醫師基本資料介紹
	A006_dirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}', 'D000*'))
	for A006_dir in A006_dirs:
		if (userid in A006_dir):
			drname = os.path.basename(A006_dir).split("_")[2]
			# 測試區
			# drname = A006_dir.split("\\")[6].split("_")[2]
			dr_concent = open(A006_dir, "r", encoding="utf-8")
			for concent in dr_concent.readlines():
				if ("<img1>" in concent):
					dr_img = concent.replace("<img1>","")
				if ("<e>" in concent):
					dr_e = concent.replace("<e>","").split("、")
			dr_concent.close()

	dr_day_list = []
	dr_weekday_list = []
	dr_lookday_list_s = []
	dr_lookday_list_a = []
	dr_lookday_list_n = []
	dr_day_compare_list = []

	# 醫師介面下一周
	# 上線前要增加3個月的限制
	if ("A006_date_add" in request.GET):
		A006_now_date = request.GET.get("A006_date_check")
		dr_days = datetime.datetime.strptime(A006_now_date, "%Y/%m/%d")
		dr_days_limit = datetime.datetime.now()
		dr_days_limit = dr_days_limit + datetime.timedelta(days=90)
		dr_days = dr_days + datetime.timedelta(days=7)
		if (dr_days > dr_days_limit):
			dr_days_limit_start = True
			dr_days = dr_days_limit
	# 醫師介面上一周
	elif ("A006_date_sub" in request.GET):
		A006_now_date = request.GET.get("A006_date_check")
		A006_today = datetime.date.today().strftime("%Y/%m/%d")
		if (A006_today == A006_now_date):
			dr_days = datetime.date.today()
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		else:
			dr_days = datetime.datetime.strptime(A006_now_date, "%Y/%m/%d")
			dr_days = dr_days - datetime.timedelta(days=7)
	# 別的介面跳轉過來的保存選擇日期
	elif ("A006_date_select" in request.GET):
		dr_days = request.GET.get("A006_date_select")
		dr_days = datetime.datetime.strptime(dr_days, "%Y%m%d")
		day_sub = dr_days.isoweekday() - 1
		dr_days = dr_days - datetime.timedelta(days=day_sub)
	# 醫師介面選擇的月份
	elif ("switch_day" in request.GET) and (A006_width > 768):
		switch_day = int(request.GET.get("switch_day"))
		if (switch_day == 1):
			dr_days = datetime.date.today()
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day == 2):
			dr_days = datetime.date.today()
			dr_days = get_next_month_start(1)
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day == 3):
			dr_days = datetime.date.today()
			dr_days = get_next_month_start(2)
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day == 4):
			dr_days = "2025/04/08"
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
	elif ("switch_day2" in request.GET) and (A006_width <= 767):
		switch_day2 = int(request.GET.get("switch_day2"))
		if (switch_day2 == 1):
			dr_days = datetime.date.today()
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 2):
			dr_days = datetime.date.today()
			dr_days = get_next_month_start(1)
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 3):
			dr_days = datetime.date.today()
			dr_days = get_next_month_start(2)
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		elif (switch_day2 == 4):
			dr_days = "2025/04/08"
			dr_days = datetime.datetime.strptime(dr_days, "%Y/%m/%d")
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
	else:
		dr_days = datetime.date.today()
		day_sub = dr_days.isoweekday() - 1
		dr_days = dr_days - datetime.timedelta(days=day_sub)

	# 醫師掛號資料
	startdt = dr_days
	c_startdt = startdt.strftime("%Y%m%d")
	enddt = startdt + datetime.timedelta(days=6)
	dr_lookday_data = MSSQLAPI.A006_Search_NRGSCD_BY_EMPNO(userid, sectno, startdt.strftime("%Y%m%d"), enddt.strftime("%Y%m%d"))

	for i in range(7):
		# 建立一周日期
		dr_day_list.append(dr_days.strftime("%Y/%m/%d"))
		dr_day_compare_list.append(dr_days.strftime("%Y%m%d"))

		# 建立一周星期中文對照
		dr_weekday = dr_days.weekday()
		if (dr_weekday == 0):
			dr_weekday = "(一)"
		elif (dr_weekday == 1):
			dr_weekday = "(二)"
		elif (dr_weekday == 2):
			dr_weekday = "(三)"
		elif (dr_weekday == 3):
			dr_weekday = "(四)"
		elif (dr_weekday == 4):
			dr_weekday = "(五)"
		elif (dr_weekday == 5):
			dr_weekday = "(六)"
		elif (dr_weekday == 6):
			dr_weekday = "(日)"
		dr_weekday_list.append(dr_weekday)

		# 新增下一筆
		dr_days = dr_days + datetime.timedelta(days=1)

	dr_lookday_list_ss = []
	for lookday_data in dr_lookday_data:
		if (lookday_data[1] == "1"):
			dr_lookday_list_ss.append(lookday_data[0])

	dr_lookday_list_aa = []
	for lookday_data in dr_lookday_data:
		if (lookday_data[1] == "2"):
			dr_lookday_list_aa.append(lookday_data[0])

	dr_lookday_list_nn = []
	for lookday_data in dr_lookday_data:
		if (lookday_data[1] == "3"):
			dr_lookday_list_nn.append(lookday_data[0])

	A006_today = datetime.datetime.now()
	A006_today = datetime.datetime.strftime(A006_today,"%Y%m%d")

	# 判段當日是否有看診
	for compare_day in dr_day_compare_list: # 1~7
		if (compare_day in dr_lookday_list_ss):
			if ((compare_day == A006_today) and (A006_now > "11:45:00")) or (A006_today > compare_day):
				dr_lookday_list_s.append(["Q"])
			else:
				dr_lookday_s_data = []
				# 查詢診間人數
				person_count = MSSQLAPI.A006_Search_NRGRGB_COUNT(compare_day, sectno, userid, 1)
				dr_lookday_s_data.append("Y")
				dr_lookday_s_data.append(person_count)
				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, userid, 1)
				if (replace_data[0] == "Y") and (replace_data[1] != userid):
					# dr_lookday_s_data.append("R")
					dr_lookday_s_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_s_data.append(replace_data[2])
					dr_lookday_s_data.append(" ")
				else:
					dr_lookday_s_data.append("Z")
					dr_lookday_s_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					dr_lookday_s_data.append("M")

				dr_lookday_list_s.append(dr_lookday_s_data)
		else:
			dr_lookday_list_s.append(["N"])

		if (compare_day in dr_lookday_list_aa):
			if ((compare_day == A006_today) and (A006_now > "16:45:00")) or (A006_today > compare_day):
				dr_lookday_list_a.append(["Q"])
			else:
				dr_lookday_a_data = []
				# 查詢診間人數
				person_count = MSSQLAPI.A006_Search_NRGRGB_COUNT(compare_day, sectno, userid, 2)
				dr_lookday_a_data.append("Y")
				dr_lookday_a_data.append(person_count)
				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, userid, 2)
				if (replace_data[0] == "Y") and (replace_data[1] != userid):
					# dr_lookday_a_data.append("R")
					dr_lookday_a_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_a_data.append(replace_data[2])
					dr_lookday_a_data.append(" ")
				else:
					dr_lookday_a_data.append("Z")
					dr_lookday_a_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					dr_lookday_a_data.append("M")

				dr_lookday_list_a.append(dr_lookday_a_data)
		else:
			dr_lookday_list_a.append(["N"])

		if (compare_day in dr_lookday_list_nn):
			if ((compare_day == A006_today) and (A006_now > "20:45:00")) or (A006_today > compare_day):
				dr_lookday_list_n.append(["Q"])
			else:
				dr_lookday_n_data = []
				# 查詢診間人數
				person_count = MSSQLAPI.A006_Search_NRGRGB_COUNT(compare_day, sectno, userid, 3)
				dr_lookday_n_data.append("Y")
				dr_lookday_n_data.append(person_count)
				# 查詢是否代診
				replace_data = MSSQLAPI.A006_Search_NRGSCD_DATA(compare_day, sectno, userid, 3)
				if (replace_data[0] == "Y") and (replace_data[1] != userid):
					# dr_lookday_n_data.append("R")
					dr_lookday_n_data.append("RXX")
					# 20240508主任要求直接拿掉
					# lookday_list_n_data.append(replace_data[2])
					dr_lookday_n_data.append(" ")
				else:
					dr_lookday_n_data.append("Z")
					dr_lookday_n_data.append("Z")
				# 查詢是否約滿
				if (replace_data[3] <= person_count) or (replace_data[3] == 0):
					dr_lookday_n_data.append("M")

				dr_lookday_list_n.append(dr_lookday_n_data)
		else:
			dr_lookday_list_n.append(["N"])
		print(dr_lookday_list_n)
	dr_clinic_list = zip(dr_day_list, dr_weekday_list, dr_lookday_list_s, dr_lookday_list_a, dr_lookday_list_n)

	# 確保變數有預設值（如果未定義）
	if 'userid' not in locals():
		userid = None
	if 'sename' not in locals():
		sename = None
	if 'sectno' not in locals():
		sectno = None
	if 'drname' not in locals():
		drname = None
	if 'dr_img' not in locals():
		dr_img = None
	if 'dr_e' not in locals():
		dr_e = []
	if 'switch_day2' not in locals():
		switch_day2 = None

	return render(request, "Patient_Guide/Patient_Guide_2_2_1.html", {
		'A006_True': A006_True,
		'dr_clinic_list': dr_clinic_list,
		'drname': drname,
		'sename': sename,
		'dr_img': dr_img,
		'dr_e': dr_e,
		'userid': userid,
		'A006_radio_day_1': A006_radio_day_1,
		'A006_radio_day_2': A006_radio_day_2,
		'A006_radio_day_3': A006_radio_day_3,
		'switch_day2': switch_day2,
		'sectno': sectno,
		'dr_day_list': dr_day_list,
	})

# =========================================A100(新官網相關協助查詢頁面)=============================================

# 新官網查詢－查詢院內科別代碼
def A100_search_sename(request):
	showlist = MSSQLAPI.Search_SENAME_BASSECT()
	return render(request, "A100/sename.html", {
		'showlist': showlist,
	})

# =========================================A101(新官網占床率)=============================================

# 新官網占床率（JS）
def A101_search_bed(request):
	# 連線MSSQL資料庫
	try:
		connection = pymssql.connect(
			host = settings.MSSQL_51_45_HOST,
			user = settings.MSSQL_51_45_USER,
			password = settings.MSSQL_51_45_PWD,
			database = settings.MSSQL_51_45_DB,
			charset = 'UTF-8',
			tds_version = '7.0'
		)

		# 輸入你要查找的資料表語法
		sql = "SELECT * FROM OLAP_EMPTY_BED_SUMMY"

		# 定義資料庫游標
		c = connection.cursor(as_dict = True)
		c.execute(sql)

		rows = c.fetchone()

		c.close()
		connection.close()
	except Exception as e:
		print(f"A101_search_bed DB Error: {e}")
		return JsonResponse({"error": "Database connection failed", "details": str(e)}, status=500)

	return JsonResponse(rows, safe=False, json_dumps_params={'ensure_ascii': False})

# =========================================A102(資通安全政策聲明)=============================================
def A102_Safe_ISMS(request):
	return render(request, "Safe_ISMS.html", {})

# =========================================A103(麵包屑導航)=============================================
def A103_bread_pencil(request):
	'''提供麵包屑導航 HTML 片段，供 JavaScript 動態載入使用'''
	return render(request, "bread_pencil.html", {})