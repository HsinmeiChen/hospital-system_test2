from django.http import HttpResponse, JsonResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger #分頁功能套件，Django本身就有支援
from dateutil.relativedelta import relativedelta
import pandas as pd
import os, datetime, re, glob, calendar, time, smtplib, openpyxl
from django.conf import settings

# --- 導入共用圖片轉 .webp 格式 與清理舊檔案函式 ---
from Pomelo_test.utils import convert_image_to_webp, safe_cleanup_webp_cache

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
		smtpObj.sendmail(settings.EMAIL_HOST_USER, "evanitdept@gmail.com", message.as_string())
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

# --- [ 最新消息:解析檔名(slug / hash) ] ---
def _get_news_1_list():
	"""負責高速度掃描文章檔名、自動提取 Slug/Hash 識別碼、由新到舊排序"""
	news_lists = []
	n_data = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_1'))

	for d in n_data:
		if (".txt" in d):
			name_without_ext = d.replace(".txt", "")

			# --- 提取 Slug (Hash Key) ---
			slug = name_without_ext.split('^')[1] if '^' in name_without_ext else ""
			body_part = name_without_ext.split('^')[0]
			parts = body_part.split("_")

			# --- 將 Slug 加入陣列最後，方便前端讀取 (成為 news_list.7) ---
			parts.append(slug)
			news_lists.append(parts)

	news_lists.sort(key=get_year, reverse=True)
	return news_lists

# --- [ 媒體報導:解析檔名(slug / hash) ] ---
def _get_news_2_list():
	"""負責高速度掃描文章檔名、自動提取 Slug/Hash 識別碼、由新到舊排序"""
	medias_split_box = []
	medias_datas = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))

	for md in medias_datas:
		if (".txt" in md):
			name_without_ext = md.replace(".txt", "")
			parts = name_without_ext.split("_")

			# 增加防錯機制：確保檔名格式正確才解析
			if len(parts) >= 8:
				slug = f"{parts[6]}_{parts[7]}"  # 生成 Slug：日期 + ID
				parts.append(slug)  # Index [8]
				parts.append(md)    # Index [9] 儲存原始檔名
				medias_split_box.append(parts)
			else:
				continue

	medias_split_box.sort(key=get_m_year, reverse=True)
	return medias_split_box

def _parse_news_2_items(items):
	"""
	【媒體報導 - 深度內容解析器】
	1. 僅針對需要顯示的文章開檔 (首頁 6 筆 / 分頁 10 筆)，大幅降低磁碟 I/O
	2. 提取首張縮圖與內文文字摘要
	3. 自動生成極速 WebP 縮圖快取，並清理孤立快取
	"""
	for item in items:
		if len(item) > 10:  # 防止重複解析
			continue
		img_name = ""
		excerpt = ""

		try:
			# 僅讀取該筆新聞的內容，抓取第一個圖片 <img1> 與摘要 <t> 
			with open(os.path.join(settings.MEDIA_ROOT, 'news_2', item[9]), "r", encoding="utf-8-sig") as f:
				for line in f:
					if not img_name and "<img1>" in line:
						img_name = line.replace("<img1>", "").strip()
					if not excerpt and "<t>" in line:
						excerpt = line.replace("<t>", "").strip()
					if img_name and excerpt:
						break
		except:
			pass

		# 縮圖自動轉檔 WebP 與快取清理
		webp_path = ""
		if img_name:
			source_dir = os.path.join(settings.MEDIA_ROOT, 'news_2', 'img')
			target_dir = os.path.join(source_dir, 'thumb-webp')
			webp_path = convert_image_to_webp(
				source_dir=source_dir,
				target_dir=target_dir,
				original_filename=img_name,
				quality=50
			)
			safe_cleanup_webp_cache(source_dir, target_dir)
			
		item.append(img_name)   # Index [10]
		item.append(excerpt)    # Index [11]
		item.append(webp_path)  # Index [12]


def index(request):
	# 1. 沿用並引入共用資料邏輯（僅取最新發布前 5 筆）
	news_lists_5 = _get_news_1_list()[:5]

	# 2. 沿用並引入共用資料邏輯（僅取最新發布前 6 筆，並動態提取摘要）
	medias_split_box = _get_news_2_list()
	media_reports_6 = medias_split_box[:6]
	_parse_news_2_items(media_reports_6)

	MEDIA_URL = settings.MEDIA_URL

	# 3. 影音消息
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
		fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8-sig")
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


	# 4. 醫療資訊對接 Mapping Cache 取得極速緩存 (僅顯示最新 4 筆)
	mapping = _get_medical_map()
	media_page_list = mapping['list_data'][:4]

	return render(request, "index.html", {
		'news_lists_5': news_lists_5,
		'media_reports_6': media_reports_6,
		'message_lists_1': message_lists_1,
		'message_lists_2': message_lists_2,
		'message_lists_3': message_lists_3,
		'message_lists_4': message_lists_4,
		'media_page_list': media_page_list,
		'contacts': media_page_list, # 增加 contacts 變數以相容於 news_4_card_single.html 的 data 參照
		'MEDIA_URL': MEDIA_URL,
	})

# =========================================A000(醫院公告)=========================================

# 功能(二)、子頁-最新消息
def get_year(element):
	return element[6]

# 最新消息 (清單頁)
def new_news(request, page=None):
	# 沿用並引入共用最新消息資料邏輯，確保未來更新同步！
	news_lists = _get_news_1_list()

	paginator = Paginator(news_lists, 10)
	page = page or request.GET.get('page') or 1
	contacts = paginator.get_page(page)

	# --- 加入 AJAX 分頁邏輯 ---
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, "news_1_partial.html", {
			'contacts': contacts,
			'paginator': paginator,
			'MEDIA_URL': settings.MEDIA_URL,
		})
	else:
		return render(request, "news_1.html", {
			'contacts': contacts,
			'paginator': paginator,
			'MEDIA_URL': settings.MEDIA_URL,
		})

# 最新消息 (文章內容頁)
def new_news_detail(request, slug):
	# --- 在資料夾中尋找符合該 slug 的檔案 ---
	n_data = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_1'))
	target_file = next((f for f in n_data if f.endswith(f"^{slug}.txt")), None)
    
	if not target_file:
		return redirect('/A000_news/') # 找不到檔案就回列表

    # --- 解析標題與日期 ---
	name_without_ext = target_file.replace(".txt", "")
	body_part = name_without_ext.split('^')[0]
	parts = body_part.split("_")
	title = parts[2]
	date = parts[6]

	# --- 讀取內容，並轉換內文圖片為 80% 品質 WebP ---
	with open(os.path.join(settings.MEDIA_ROOT, 'news_1', target_file), "r", encoding="utf-8-sig") as fd:
		raw_lines = fd.readlines()
	
	content_lines = []
	first_img = ""
	excerpt = ""
	for line in raw_lines:
		# 1.抓取第一個圖片
		if not first_img and "<img1>" in line:
			first_img = line.replace("<img1>", "").strip()

		# 2.抓取摘要(第一個 <t>)
		if not excerpt and "<t>" in line:
			excerpt = line.replace("<t>", "").strip()

		# 自動轉換內文圖片為 80% 品質 WebP 並且直接預渲染好相容 .jpeg/.png 各種長度副檔名的 picture 標籤
		if "<img1>" in line:
			img_filename = line.replace("<img1>", "").strip()
			if img_filename:
				source_dir = os.path.join(settings.MEDIA_ROOT, 'news_1', 'img')
				target_dir = os.path.join(source_dir, 'img_webp_article')

				# 執行 WebP 轉換 (文章圖片使用 80% 品質)
				convert_image_to_webp(source_dir, target_dir, img_filename, quality=80)

				# 安全清理機制
				safe_cleanup_webp_cache(source_dir, target_dir)

				# 組裝 HTML (利用 os.path.splitext，無痛相容 .jpeg/.png/.gif 等任意長度的副檔名！)
				name_without_ext = os.path.splitext(img_filename)[0]
				picture_html = (
					f'<picture>'
					f'<source srcset="{settings.MEDIA_URL}news_1/img/img_webp_article/{name_without_ext}.webp" type="image/webp">'
					f'<img class="img-fluid w-100 my-3" src="{settings.MEDIA_URL}news_1/img/{img_filename}" alt="{title}" title="{title}" loading="lazy">'
					f'</picture>'
				)
				line = f"<img1_html>{picture_html}\n"
		
		content_lines.append(line)

	# --- 檢查內容中是否包含任何 <h> 標籤-優先採用，沒有則使用檔案名稱的標題 ---
	has_h_tag = any("<h>" in line for line in content_lines)

	return render(request, "news_detail.html", {
		'title': title,
		'date': date,
		'content_lines': content_lines,
		'first_img': first_img,
		'excerpt': excerpt,
		'has_h_tag': has_h_tag,
		'MEDIA_URL': settings.MEDIA_URL,
	})



# 功能(三)、子頁-媒體報導
def get_m_year(element):
	return element[6]  #指取資料第 6 個位置值

def new_medias(request, page=None):
	# 沿用並引入共用媒體報導資料邏輯，確保未來更新同步！
	medias_split_box = _get_news_2_list()

	paginator = Paginator(medias_split_box, 10)
	page = page or request.GET.get('page') or 1
	contacts = paginator.get_page(page)

	# --- 僅針對當前分頁的 10 筆資料深度提取圖片與摘要，並處理快取 ---
	_parse_news_2_items(contacts)

	# --- 加入 AJAX 分頁邏輯 ---
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, "news_2_partial.html", {
			'contacts': contacts,
			'paginator': paginator,
			'MEDIA_URL': settings.MEDIA_URL,
		})
	else:
		return render(request, "news_2.html", {
			'contacts': contacts,
			'paginator': paginator,
			'MEDIA_URL': settings.MEDIA_URL,
		})


# 媒體報導 (文章內容頁)
def new_media_detail(request, slug):

	# --- 根據 slug (例如 2025-07-21_HA01830) 找尋結尾匹配的檔案 ---
	n_data = os.listdir(os.path.join(settings.MEDIA_ROOT, 'news_2'))
	target_file = next((f for f in n_data if f.endswith(f"{slug}.txt")), None)

	if not target_file:
		return redirect('/A000_reports/')

	# --- 解析標題與日期 ---
	name_without_ext = target_file.replace(".txt", "")
	parts = name_without_ext.split("_")
	title = parts[2]
	date = parts[6]

	with open(os.path.join(settings.MEDIA_ROOT, 'news_2', target_file), "r", encoding="utf-8-sig") as fd:
		raw_lines = fd.readlines()

	# --- 同時提取圖片與摘要文字，並轉換內文圖片為 80% 品質 WebP 並且組裝 picture 標籤 ---
	content_lines = []
	first_img = ""
	excerpt = ""
	for line in raw_lines:
		if not first_img and "<img1>" in line:
			first_img = line.replace("<img1>", "").strip()
		if not excerpt and "<t>" in line:
			excerpt = line.replace("<t>", "").strip()

		# 自動轉換內文圖片為 80% 品質 WebP
		if "<img1>" in line:
			img_filename = line.replace("<img1>", "").strip()
			if img_filename:
				source_dir = os.path.join(settings.MEDIA_ROOT, 'news_2', 'img')
				target_dir = os.path.join(source_dir, 'img_webp_article')

				# 執行 WebP 轉換 (文章圖片使用 80% 品質)
				convert_image_to_webp(source_dir, target_dir, img_filename, quality=80)

				# 安全清理機制
				safe_cleanup_webp_cache(source_dir, target_dir)

				# 組裝 HTML (利用 os.path.splitext，無痛相容 .jpeg/.png/.gif 等任意長度的副檔名！)
				name_without_ext = os.path.splitext(img_filename)[0]
				picture_html = (
					f'<picture>'
					f'<source srcset="{settings.MEDIA_URL}news_2/img/img_webp_article/{name_without_ext}.webp" type="image/webp">'
					f'<img class="img-fluid w-100 my-3" src="{settings.MEDIA_URL}news_2/img/{img_filename}" alt="{title}" title="{title}" loading="lazy">'
					f'</picture>'
				)
				line = f"<img1_html>{picture_html}\n"
		
		content_lines.append(line)

	# ---檢查內容中是否包含任何 <h> 標籤-優先採用，沒有則使用檔案名稱的標題
	has_h_tag = any("<h>" in line for line in content_lines)

	return render(request, "news_2_detail.html", {
		'title': title,
		'date': date,
		'content_lines': content_lines,
		'first_img': first_img,
		'excerpt': excerpt,
		'has_h_tag': has_h_tag,
		'MEDIA_URL': settings.MEDIA_URL,
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
		fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8-sig")
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

# --- [ 檔案加上 hash 值 (slug)、新舊網址對照表快取 ] ---

_MEDICAL_MAP_CACHE = None

def _get_medical_map():
	"""醫療資訊檔案快取對照表 (含自動 CRC32 哈希命名)"""
	global _MEDICAL_MAP_CACHE
	if _MEDICAL_MAP_CACHE is not None:
		return _MEDICAL_MAP_CACHE

	# 1. 自動為 news_4 資料夾下的檔案追加 hash (追加在 .txt 前面)
	media_page_dir = os.path.join(settings.MEDIA_ROOT, 'news_4')
	if os.path.exists(media_page_dir):
		from Pomelo_test.utils import append_hash_to_filenames
		append_hash_to_filenames(media_page_dir, extension='.txt', separator='^')

	mapping = {
		'by_slug': {},        # slug (即 hash 值) -> 完整檔名 (如 IN001_...^a1b2c3d4.txt)
		'by_legacy_key': {},  # 舊金鑰 (如 IN001_2025-09-02) -> hash 值 (如 a1b2c3d4)
		'list_data': []       # 清單頁預解析資料快取
	}

	if not os.path.exists(media_page_dir):
		_MEDICAL_MAP_CACHE = mapping
		return mapping

	media_page_files = os.listdir(media_page_dir)
	# 依檔名排序 (新至舊)
	re_media_page_files = sorted(media_page_files, reverse=True)

	for media_page_file in re_media_page_files:
		if ("IN001" in media_page_file) and media_page_file.endswith(".txt"):
			name_without_ext = media_page_file.replace(".txt", "")
			
			# 分割獲取核心檔名與 Hash
			h_parts = name_without_ext.split("^")
			core_name = h_parts[0]
			file_hash = h_parts[1] if len(h_parts) > 1 else ""

			parts = core_name.split("_")
			if len(parts) >= 2:
				legacy_key = f"{parts[0]}_{parts[1]}"  # IN001_2025-09-02
				slug = file_hash if file_hash else legacy_key  # 若有 hash 則用 hash，沒有則降級用舊 key
				
				mapping['by_slug'][slug] = media_page_file
				mapping['by_legacy_key'][legacy_key] = slug
				
				# 解析檔案內容用於列表呈現
				title = ""
				date_val = ""
				excerpt = ""
				img_t = ""
				t_count = 0
				
				try:
					filepath = os.path.join(media_page_dir, media_page_file)
					with open(filepath, "r", encoding="utf-8-sig") as fd:
						for line in fd:
							if "<h>" in line:
								title = line.replace("<h>", "").strip()
							elif "<in_date>" in line:
								date_val = line.replace("<in_date>", "").strip()
							elif "<t>" in line and t_count == 0:
								t_count += 1
								excerpt = line.replace("<t>", "").strip()
							elif "<img_t>" in line:
								img_t = line.replace("<img_t>", "").strip()
				except Exception as e:
					print(f"解析醫療資訊檔案失敗 {media_page_file}: {e}")
					
				if not date_val:
					date_val = parts[1]
					
				# 儲存清單資料項
				# 0: title, 1: date, 2: excerpt, 3: img_t, 4: slug (hash), 5: webp_path (快取預留)
				mapping['list_data'].append([title, date_val, excerpt, img_t, slug, ""])

	_MEDICAL_MAP_CACHE = mapping
	return mapping


# 【醫療資訊 - 清單總覽頁】
def medical_info(request, page=None):
	mapping = _get_medical_map()
	media_page_list = mapping['list_data']

	# 設定一頁顯示 10 筆 (比照 news_2)
	paginator = Paginator(media_page_list, 10)
	page_num = page or request.GET.get('page') or 1
	contacts = paginator.get_page(page_num)

	# 為當前分頁縮圖自動轉檔為 WebP (品質 50% 適合清單縮圖)
	for item in contacts:
		img_name = item[3]
		if img_name:
			source_dir = os.path.join(settings.MEDIA_ROOT, 'news_4', 'img')
			target_dir = os.path.join(source_dir, 'thumb-webp')
			
			if not os.path.exists(target_dir):
				os.makedirs(target_dir, exist_ok=True)
				
			try:
				webp_path = convert_image_to_webp(
					source_dir=source_dir,
					target_dir=target_dir,
					original_filename=img_name,
					quality=50
				)
				safe_cleanup_webp_cache(source_dir, target_dir)
				item[5] = webp_path  # 寫入 WebP 相對路徑
			except Exception as e:
				print(f"縮圖 WebP 轉換失敗: {e}")

	# 支援 AJAX 無限滾動
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		return render(request, "news_4_partial.html", {
			'contacts': contacts,
			'MEDIA_URL': settings.MEDIA_URL,
		})
	else:
		return render(request, "news_4.html", {
			'contacts': contacts,
			'MEDIA_URL': settings.MEDIA_URL,
		})


# 【醫療資訊 - 舊參數網址轉接頭 (301 永久轉址)】
def medical_pages(request):
	if "media_page_path" in request.GET:
		path = request.GET.get("media_page_path")  # 例如 IN001_2025-09-02
		mapping = _get_medical_map()
		
		# 查詢對照表，獲得 Hashed Slug (即極簡 hash 值)
		new_slug = mapping['by_legacy_key'].get(path)
		if new_slug:
			return redirect(f"/A000_medical_info/{new_slug}/", permanent=True)
			
	return redirect("/A000_medical_info/", permanent=True)


# 【醫療資訊 - 極短網址詳細頁】
def medical_pages_detail(request, slug):
	mapping = _get_medical_map()
	
	# 相容防呆：如果使用者訪問的是舊 Key 形式的新網址 (如 /A000_medical_info/IN001_2025-09-02/)
	if slug in mapping['by_legacy_key']:
		canonical_slug = mapping['by_legacy_key'][slug]
		return redirect(f"/A000_medical_info/{canonical_slug}/", permanent=True)

	# 根據 hash 獲取對應的檔案
	target_file = mapping['by_slug'].get(slug)
	if not target_file:
		return redirect('/A000_medical_info/')

	media_page_dir = os.path.join(settings.MEDIA_ROOT, 'news_4')
	filepath = os.path.join(media_page_dir, target_file)

	try:
		with open(filepath, "r", encoding="utf-8-sig") as fd:
			raw_lines = fd.readlines()
	except Exception as e:
		print(f"讀取詳細頁檔案失敗 {target_file}: {e}")
		return render(request, "404.html", status=404)

	# 解析標題、發佈日期、首張圖片、首段摘要 (用於 OG Title 或 SEO 標籤)
	title = ""
	date = ""
	first_img = ""
	excerpt = ""
	for line in raw_lines:
		if "<h>" in line:
			title = line.replace("<h>", "").strip()
		elif "<in_date>" in line:
			date = line.replace("<in_date>", "").strip()
		elif "<img_t>" in line and not first_img:
			first_img = line.replace("<img_t>", "").strip()
		elif "<img1>" in line and not first_img:
			first_img = line.replace("<img1>", "").strip()
		elif "<t>" in line and not excerpt:
			excerpt = line.replace("<t>", "").strip()

	if not date:
		parts = target_file.split("_")
		if len(parts) >= 2:
			date = parts[1]

	# 遍歷每一行內容，自動轉換內文圖片為 80% 品質 WebP 格式
	data_lines = []
	for line in raw_lines:
		if "<img1>" in line:
			img_filename = line.replace("<img1>", "").strip()
			if img_filename:
				source_dir = os.path.join(settings.MEDIA_ROOT, 'news_4', 'img')
				target_dir = os.path.join(source_dir, 'img_webp_article')
				
				if not os.path.exists(target_dir):
					os.makedirs(target_dir, exist_ok=True)
					
				# 執行轉檔 (80% 品質適合文章內圖片)
				convert_image_to_webp(source_dir, target_dir, img_filename, quality=80)
				safe_cleanup_webp_cache(source_dir, target_dir)
				
				# 封裝為高相容性 HTML5 <picture> 標籤
				name_without_ext = os.path.splitext(img_filename)[0]
				picture_html = (
					f'<picture>'
					f'<source srcset="{settings.MEDIA_URL}news_4/img/img_webp_article/{name_without_ext}.webp" type="image/webp">'
					f'<img class="img-fluid w-100 my-3" src="{settings.MEDIA_URL}news_4/img/{img_filename}" alt="{title}" title="{title}" loading="lazy">'
					f'</picture>'
				)
				line = f"<img1_html>{picture_html}\n"
				
		data_lines.append(line)

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "news_4_1.html", {
		'title': title,
		'date': date,
		'first_img': first_img,
		'excerpt': excerpt,
		'data_lines': data_lines,
		'MEDIA_URL': MEDIA_URL,
		'SITE_DOMAIN': settings.SITE_DOMAIN,
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

	mapping = _get_dept_dr_map() # 115/05/17短網址-新增部分

	for subject in django_subjects:
		django_departments = []
		django_departments2 = []
		django_dept_ens = [] # 115/05/17短網址-新增部分
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))

		for d_dir in d_dirs:
			red_dir = d_dir.split("_")
			django_departments.append(red_dir[1])

			# 115/05/17短網址-新增部分
			path_id = str(subject).split("_")[1] + "_" + str(d_dir).split("_")[0]
			django_departments2.append(path_id)

			dept_en = ""
			if path_id in mapping['depts']:
				dept_en = mapping['depts'][path_id]['en']
			django_dept_ens.append(dept_en)
			
			z_departments = zip(django_departments, django_departments2, django_dept_ens)
			# 115/05/17短網址-新增部分

		departments.append(z_departments)

	datas = zip(subjects, departments)

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "department/department_index.html", {
		'datas': datas,
		'MEDIA_URL': MEDIA_URL,
	})

# 科室介紹

# --- [ 圖片轉 WebP 專用包裝函數] ---
def convert_doctor_image_to_webp(original_filename):
	"""專用：轉換醫師大頭照為 WebP，儲存於 department/img/doc-webp，壓縮品質 80%"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'department', 'img')
	target_dir = os.path.join(source_dir, 'doc-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

def convert_about_image_to_webp(original_filename):
	"""專用：轉換長安簡介圖片為 WebP，儲存於 A004/img/about-webp，壓縮品質 80%"""
	source_dir = os.path.join(settings.MEDIA_ROOT, 'A004', 'img')
	target_dir = os.path.join(source_dir, 'about-webp')
	return convert_image_to_webp(source_dir, target_dir, original_filename, quality=80)

# --- [ Mapping Cache 對照表快取機制] ---
_DEPT_DR_MAP_CACHE = None

def _get_dept_dr_map():
	global _DEPT_DR_MAP_CACHE
	if _DEPT_DR_MAP_CACHE is not None:
		return _DEPT_DR_MAP_CACHE

	mapping = {'doctors': {}, 'depts': {}, 'dept_en_to_id': {}}
	pathC = os.path.join(settings.MEDIA_ROOT, 'department')
	if not os.path.exists(pathC): return mapping
		
	for d000 in os.listdir(pathC):
		if "D000" in d000:
			p_parts = d000.split("_")
			if len(p_parts) < 2: continue
			pathP = p_parts[1]
			
			target_dir = os.path.join(pathC, d000)
			for sub_dir in os.listdir(target_dir):
				d_parts = sub_dir.split("_")
				if len(d_parts) < 3: continue
				pathD, dept_name, dept_en = d_parts[0], d_parts[1], d_parts[2]
				dept_id = f"{pathP}_{pathD}"
				
				# 儲存科別資訊
				dept_full_path = os.path.join(target_dir, sub_dir)
				mapping['depts'][dept_id] = {'en': dept_en, 'name': dept_name, 'full_path': dept_full_path}
				mapping['dept_en_to_id'][dept_en] = dept_id
				
				# 掃描該科別下的醫師
				if os.path.isdir(dept_full_path):
					for f in os.listdir(dept_full_path):
						if f.startswith("D000") and f.endswith(".txt"):
							f_parts = f.split("_")
							if len(f_parts) >= 4:
								pathF = f_parts[1]
								dr_id = f_parts[3].replace(".txt", "")
								path_id = f"{dept_id}_{pathF}"

								doc_data = {
									'id': dr_id,
									'path_id': path_id,
									'filename': f,
									'dept_path': dept_full_path,
									'dept_name': dept_name,
									'dept_en': dept_en
								}
								# 同時支援用「路徑ID」、「醫師ID」和「科別英文_醫師ID」組合鍵來查找，防止跨科別同工號衝突
								mapping['doctors'][path_id] = doc_data
								mapping['doctors'][dr_id] = doc_data
								mapping['doctors'][f"{dept_en}_{dr_id}"] = doc_data
	_DEPT_DR_MAP_CACHE = mapping
	return mapping

# --- [ 醫師-短網址轉接頭 ] ---
def A001_department_doctor_short(request, dept_en, dr_id):
	mapping = _get_dept_dr_map()
	# 優先使用「科別英文_醫師ID」組合鍵比對，避免跨科別同工號衝突
	doc_info = mapping['doctors'].get(f"{dept_en}_{dr_id}") or mapping['doctors'].get(dr_id)
	if not doc_info: return redirect('/A001_dr_search/')
	request.GET = request.GET.copy()
	request.GET['dr_search'] = 'true'
	request.GET['open_info_path'] = doc_info['path_id']
	return A001_department_doctor(request)


# --- [ 科別-短網址轉接頭 ] ---
def A001_department_part_short(request, dept_en):
	mapping = _get_dept_dr_map()
	dept_id = mapping['dept_en_to_id'].get(dept_en)
	if not dept_id: return redirect('/A001_department_overview/')
	request.GET = request.GET.copy()
	request.GET['open_info_name'] = dept_id
	return A001_department_part(request)



# @csrf_exempt
def A001_department_part(request):

	# 新增部分 Start (修正轉址迴圈) --------------------------------
	# 只有當請求路徑是舊路徑時，才執行轉址
	if request.path == '/A001_department_part/':
		if "open_info_name" in request.GET:
			path_id = request.GET.get("open_info_name")
			mapping = _get_dept_dr_map()
			if path_id in mapping['depts']:
				# 加上 permanent=True 觸發 301 永久轉址
				return redirect(f"/A001_department_overview/{mapping['depts'][path_id]['en']}/", permanent=True)
	
	path = ""
	department = ""
	dept_en = ""
	modals = []
	introduction_list = []
	doctors = []
	disable_X = False
	# 新增部分 End --------------------------------

	if ("open_info_name" in request.GET):
		path = request.GET.get("open_info_name")
		request.session['path'] = path

	if ("path" in request.session):
		path = request.session['path']

		# 新增部分 Start --------------------------------
		# 使用對照表快取機制取得科室資訊
		mapping = _get_dept_dr_map()

		pathFile = ""
		department = ""
		if path in mapping['depts']:
			pathFile = mapping['depts'][path]['full_path']
			department = mapping['depts'][path]['name']
		

		if not pathFile:
			# 如果快取找不到，降級回原本的掃描邏輯（或報錯）
			pathP = path.split("_")[0]
			pathD = path.split("_")[1]
			pathC = os.path.join(settings.MEDIA_ROOT, 'department')
			pathDirs = os.listdir(pathC)
			for pathDir in pathDirs:
				if ("D000" in pathDir) and (pathP == pathDir.split("_")[1]):
					fileDirs = os.listdir(os.path.join(pathC, pathDir))
					for fileDir in fileDirs:
						if (pathD == fileDir.split("_")[0]):
							pathFile = os.path.join(pathC, pathDir, fileDir)

			if pathFile:
				department = os.path.basename(pathFile).split("_")[1]
		disablePath = os.path.basename(pathFile).split("_") if pathFile else []


		# 新增部分 end --------------------------------

		# department = path.split("\\")[6].split("_")[1]
		# disablePath = path.split("\\")[6].split("_")
		disable_X = False
		if "x" in disablePath: # 只要包含 x 標記就生效
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
		# 醫師 WebP 大頭照列表
		doctor_webp_list = []
		# 科室介紹內容
		introduction_list = []

		"""20250715 path改pathFile 格式為 大科室序號_科別序號"""
		# files = os.listdir(path)
		if pathFile:
			files = os.listdir(pathFile)
		else:
			files = []

		for file in files:
			if (".txt" in file) and ("I000" in file):

				content = open(os.path.join(pathFile, file), "r", encoding="utf-8-sig")
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

				content = open(os.path.join(pathFile, file), "r", encoding="utf-8-sig")
				has_img = False
				for c in content.readlines():
					if ("<e>" in c):
						doctor_list2.append(c.replace("<e>",""))
					if ("<img1>" in c):
						img_name = c.replace("<img1>","").strip()
						doctor_list3.append(img_name)
						# 呼叫底層自動進行轉檔並加入列表
						webp_name = convert_doctor_image_to_webp(img_name) if img_name else ""
						doctor_webp_list.append(webp_name)
						has_img = True
				if not has_img:
					doctor_list3.append("")
					doctor_webp_list.append("")
				content.close()
		"""20250715 path改pathFile 格式為 大科室序號_科別序號"""
		doctors = zip(doctor_list, doctor_list2, doctor_list3, doctor_list4, doctor_list5, doctor_list7, doctor_list8, doctor_webp_list)
		modals = zip(doctor_list4, doctor_list6)

		# 新增部分 Start --------------------------------
		mapping = _get_dept_dr_map()
		dept_id = path.split("_")[0] + "_" + path.split("_")[1]
		dept_en = mapping['depts'][dept_id]['en'] if dept_id in mapping['depts'] else ""
		# 新增部分 end --------------------------------

	MEDIA_URL = settings.MEDIA_URL
	return render(request, "department/department_part.html", {
		'department': department,
		'dept_en': dept_en,
		'modals': modals,
		'introduction_list': introduction_list,
		'doctors': doctors,
		'disable_X': disable_X,
		'MEDIA_URL': MEDIA_URL,
	})

# 醫師個人介紹 (原程式:需要帶參數網址，已改成短網址背後的「引擎」)
# @csrf_exempt
def A001_department_doctor(request):

	# 新增部分 Start (修正轉址迴圈) --------------------------------
	mapping = _get_dept_dr_map()
	# 只有當請求路徑是舊路徑時，才執行轉址
	if request.path == '/A001_department_doctor/':
		if "open_info_path" in request.GET:
			path_id = request.GET.get("open_info_path")
			if path_id in mapping['doctors']:
				doc = mapping['doctors'][path_id]
				# 加上 permanent=True 觸發 301 轉址
				return redirect(f"/A001_department_doctor/{doc['dept_en']}/{doc['id']}/", permanent=True)
		elif "open_info_name" in request.GET:
			dr_id = request.GET.get("open_info_name")
			if dr_id in mapping['doctors']:
				doc = mapping['doctors'][dr_id]
				return redirect(f"/A001_department_doctor/{doc['dept_en']}/{doc['id']}/", permanent=True)
	# 新增部分 End --------------------------------

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
			# from django.http import Http404
			raise Http404("無效的醫師路徑參數")

		# 構建 URL，用於分頁連結
		from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
		parsed = urlparse(request.get_full_path())
		
		# 1. 構建相關文章使用的 url (移除 page，保留 video_page)
		query_params_art = parse_qs(parsed.query)
		if 'page' in query_params_art:
			del query_params_art['page']
		if dorp and porn:
			if dorp not in query_params_art: query_params_art[dorp] = ['']
			if porn not in query_params_art: query_params_art[porn] = [filename] if filename else ['1']
			elif query_params_art.get(porn) == ['1'] and filename: query_params_art[porn] = [filename]
		if not query_params_art and dorp and porn:
			query_params_art[dorp] = ['']
			query_params_art[porn] = [filename] if filename else ['1']
		new_query_art = urlencode(query_params_art, doseq=True)
		url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query_art, parsed.fragment))

		# 2. 構建相關影音使用的 video_url (移除 video_page，保留 page)
		query_params_vid = parse_qs(parsed.query)
		if 'video_page' in query_params_vid:
			del query_params_vid['video_page']
		if dorp and porn:
			if dorp not in query_params_vid: query_params_vid[dorp] = ['']
			if porn not in query_params_vid: query_params_vid[porn] = [filename] if filename else ['1']
			elif query_params_vid.get(porn) == ['1'] and filename: query_params_vid[porn] = [filename]
		if not query_params_vid and dorp and porn:
			query_params_vid[dorp] = ['']
			query_params_vid[porn] = [filename] if filename else ['1']
		new_query_vid = urlencode(query_params_vid, doseq=True)
		video_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query_vid, parsed.fragment))

		request.session['path'] = filename
		
		# 新增部分 Start --------------------------------
		# --- [使用對照表快速定位醫師檔案] ---
		mapping = _get_dept_dr_map()

		pathFile = ""
		if filename in mapping['doctors']:
			doc_m = mapping['doctors'][filename]
			pathFile = doc_m['dept_path']
			filename = doc_m['filename']
		
		if not pathFile:
			filename_parts = filename.split("_")
			pathP = filename_parts[0]
			pathD = filename_parts[1]
			pathF = filename_parts[2]
			pathC = os.path.join(settings.MEDIA_ROOT, 'department')
			pathDirs = os.listdir(pathC)
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

		department = os.path.basename(pathFile).split("_")[1] if pathFile else ""
		disablePath = os.path.basename(pathFile).split("_") if pathFile else []
		# 新增部分 End --------------------------------


		if filename == "1":
			filename = request.session['filename']
		else:
			request.session['filename'] = filename


		# path = request.session['path']
		# department = path.split("\\")[6].split("_")[1]

		# disablePath = path.split("\\")[6].split("_")
		disable_X = False
		if "x" in disablePath: # 只要包含 x 標記就生效
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

		content = open(pathFile + "\\" + filename, "r", encoding="utf-8-sig")
		for c in content.readlines():
			if ("<i>" in c):
				doctor_info = c.replace("<i>","")
			if ("<e>" in c):
				doctor_e = c.replace("<e>","").split("、")
			if ("<a>" in c):
				doctor_a = c.replace("<a>","").split("；")
			if ("<img1>" in c):
				doctor_img = c.replace("<img1>","")
				# 取得轉換後的 WebP 檔名
				doctor_webp_img = convert_doctor_image_to_webp(doctor_img.strip()) if doctor_img else ""

		# --- 媒體報導區  (使用共用函數-醫師工號比對) ---

		# 1. 呼叫共用函數獲取所有媒體報導清單
		all_medias = _get_news_2_list()
		doctor_medias = []
		
		# 2. 進行工號匹配：檔名中只要包含醫師工號（如 HA01507），就視為該醫師的相關文章
		for item in all_medias:
			if len(item) >= 8 and (department_doctor_id == item[7] or department_doctor_id in item[9]):
				doctor_medias.append(item)

		# 3. 進行分頁（每頁顯示 4 筆）
		in_paginator_2 = Paginator(doctor_medias, 4)
		in_page_2 = request.GET.get('page', 1)
		in_contacts_2 = in_paginator_2.get_page(in_page_2)

		# 4. 僅針對當前分頁的 6 筆資料深度提取圖片與摘要，並處理 WebP 快取
		_parse_news_2_items(in_contacts_2)
		# 5. 相容原本前端的變數名稱
		in_zdata = in_contacts_2
		in_zdata_i = len(doctor_medias)
		

		# --- 影音消息 ---
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
			fd = open(os.path.join(_dir,m["file_name"]),"r",encoding="utf-8-sig")
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

		# 為了避免在不同分頁切換時，部分彈窗 (Modal) 無法載入的問題，
		# 我們將在 page_modals 中渲染該醫師的所有影音 Modals，所以保留完整的 message_lists 備用。
		all_video_messages = message_lists

		# 影音分頁（每頁顯示 4 筆）
		video_paginator = Paginator(message_lists, 4)
		video_page_num = request.GET.get('video_page', 1)
		video_contacts = video_paginator.get_page(video_page_num)

		message_lists_1 = video_contacts.object_list
		message_lists_1_i = i


	MEDIA_URL = settings.MEDIA_URL

	# ===【 AJAX 局部渲染相關文章 / 相關影音區塊 】===
	if request.headers.get('x-requested-with') == 'XMLHttpRequest':
		if 'video_page' in request.GET:
			return render(request, "department/doctor_videos_partial.html", {
				'video_contacts': video_contacts,
				'MEDIA_URL': MEDIA_URL,
				'video_url': video_url,
			})
		else:
			return render(request, "department/doctor_articles_partial.html", {
				'contacts': in_contacts_2,
				'MEDIA_URL': MEDIA_URL,
				'url': url,
			})

	return render(request, "department/department_doctor.html", {
		'doctor_name': doctor_name,
		'department': department,
		'stop_datas': stop_datas,
		'in_zdata': in_zdata,
		'in_zdata_i': in_zdata_i,
		'in_contacts_2': in_contacts_2,
		'contacts': in_contacts_2, # 對接 doctor_articles_partial.html 所需
		'in_paginator_2': in_paginator_2,
		'message_lists_1': message_lists_1,
		'message_lists_1_i': message_lists_1_i,
		'all_video_messages': all_video_messages,
		'video_contacts': video_contacts,
		'video_url': video_url,
		'doctor_img': doctor_img,
		'doctor_webp_img': doctor_webp_img,
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

	# 新增部分 Start --------------------------------
	mapping = _get_dept_dr_map()
	# 新增部分 End --------------------------------

	for subject in django_subjects:
		d_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject)))

		for d_dir in d_dirs:
			django_doctors = []
			django_doctors2 = []

			# 新增部分 Start --------------------------------
			django_dept_ens = []
			django_dr_ids = []
			# 新增部分 End --------------------------------

			re_subject = d_dir.split("_")
			subjects.append(re_subject[1])
			dd_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject), str(d_dir)))

			for dd_dir in dd_dirs:
				if ("D000" in dd_dir):
					red_dir = dd_dir.split("_")
					django_doctors.append(red_dir[2].split(" ")[0])

					# 新增部分 Start --------------------------------
					path_id = str(subject).split("_")[1] + "_" + str(d_dir).split("_")[0] + "_" + str(dd_dir).split("_")[1]
					django_doctors2.append(path_id)
					
					# 獲取英文名稱與醫師 ID
					dept_en = ""
					dr_id = ""
					if path_id in mapping['doctors']:
						dept_en = mapping['doctors'][path_id]['dept_en']
						dr_id = mapping['doctors'][path_id]['id']
					django_dept_ens.append(dept_en)
					django_dr_ids.append(dr_id)
					
					z_doctors = zip(django_doctors, django_doctors2, django_dept_ens, django_dr_ids)
					# 新增部分 End --------------------------------

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
	
	return render(request, "consultation_progress.html", {
		'modals': modals,
		'number_lists': number_lists,
		'now_status': now_status,
		'now': now_display,
	})

# 掛號須知
def A002_registration_notice(request):
	A006_True = "True"
	data = open(os.path.join(settings.MEDIA_ROOT, 'A002', 'registration_notice', 'main.txt'), "r", encoding="utf-8-sig")
	data_lines = data.readlines()

	return render(request, "Patient_Guide/Patient_Guide_index.html", {
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
						text = open(os.path.join(dir_path, file), "r", encoding="utf-8-sig")

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

	return render(request, "MedicalSupport/d_support_index.html", {})

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

	return render(request, "MedicalSupport/Laboratory/labor-pathology-5.html", {
		'data2': data2,
		'search_keywords': search_keywords,
	})

# =========================================A004(關於長安)=============================================

# 長安簡介
def A004_hos_intro(request):
	path = os.path.join(settings.MEDIA_ROOT, 'A004', 'about.txt')
	data = open(path, "r", encoding="utf-8-sig")
	data_lines = [line.strip() for line in data.readlines()]
	data.close()

	# 預先轉換簡介內嵌的圖片為 WebP
	for line in data_lines:
		if "<img1>" in line:
			img_name = line.replace("<img1>", "").strip()
			if img_name:
				convert_about_image_to_webp(img_name)

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
	source_dir = os.path.join(settings.BASE_DIR, 'Public', 'common', 'img', 'ward_mes')
	target_dir = os.path.join(source_dir, 'ward-webp')

	# 如果子資料夾不存在，則自動建立它
	if not os.path.exists(target_dir):
		os.makedirs(target_dir)

	convert_image_to_webp(source_dir, target_dir, 'hos_process.jpg', quality=80)
	return render(request, "department/ward_mes_1.html", {})

# 病房訊息_住院須知
# def A005_ward_mes_2(request):
	#return render(request, "department/ward_mes_2.html", locals())  秀出網頁

# 病房訊息_病人出院流程
def A005_ward_mes_3(request):
	source_dir = os.path.join(settings.BASE_DIR, 'Public', 'common', 'img', 'ward_mes')

	target_dir = os.path.join(source_dir, 'ward-webp')

	if not os.path.exists(target_dir):
		os.makedirs(target_dir)

	convert_image_to_webp(source_dir, target_dir, 'dis_process.jpg', quality=80)
	return render(request, "department/ward_mes_3.html", {})

# 病房訊息_病房訊息
def A005_ward_mes_0(request):
	source_dir = os.path.join(settings.BASE_DIR, 'Public', 'common', 'img', 'ward_mes')

	target_dir = os.path.join(source_dir, 'ward-webp')

	if not os.path.exists(target_dir):
		os.makedirs(target_dir)

	convert_image_to_webp(source_dir, target_dir, 'Room_fee.jpg', quality=80)
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
		
		return render(request, "Patient_Guide/Patient_Guide_2_4.html", template_vars)

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

	return render(request, "Patient_Guide/Patient_Guide_2_5.html", {
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

	return render(request, "Patient_Guide/Patient_Guide_2_6.html", {
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
	return render(request, "Patient_Guide/Patient_Guide_2_3.html", {
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
			if (len(d_dir.split("_")) >= 2) and not d_dir.endswith("_x"):
				django_senames.append(d_dir.split("_")[1])
		senames.append(django_senames)

	datas = zip(subjects, senames)
	return render(request, "Patient_Guide/Patient_Guide_2_1.html", {
		'A006_True': A006_True,
		'datas': datas,
	})

# 網路掛號_選擇科別_當週該科醫師列表
# --- [ 網路掛號-科別預約-短網址轉接頭 ] ---
def A006_Online_Booking_1_part_short(request, dept_en):
	mapping = _get_dept_dr_map()
	if dept_en in mapping['dept_en_to_id']:
		dept_id = mapping['dept_en_to_id'][dept_en]
		dept_name = mapping['depts'][dept_id]['name']
		
		# 將參數重新塞回 request.GET 中供原函式使用
		request.GET = request.GET.copy()
		request.GET['A006_sename'] = dept_name
	return A006_Online_Booking_1_part(request)

def A006_Online_Booking_1_part_legacy(request):
	# 攔截舊的 QueryString 網址並轉址到新的 SEO 短網址
	if "A006_sename" in request.GET:
		sename = request.GET.get("A006_sename")
		mapping = _get_dept_dr_map()
		
		# 從反向對應中尋找英文代碼
		dept_en = None
		for k, v in mapping['dept_en_to_id'].items():
			if mapping['depts'][v]['name'] == sename:
				dept_en = k
				break
				
		if dept_en:
			# 保留原本可能帶入的其他參數，例如 A006_date_select 等
			other_params = request.GET.copy()
			other_params.pop("A006_sename", None)
			
			query_string = ""
			if other_params:
				from urllib.parse import urlencode
				query_string = "?" + urlencode(other_params)
				
			return redirect(f"/A006_Online_Booking_1_part/{dept_en}/{query_string}", permanent=True)
	
	# 若無攔截到，則退回原邏輯
	return A006_Online_Booking_1_part(request)


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
	A006_I000 = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}*', 'I000*'))

	# 科室介紹資訊
	I000_concent = open(A006_I000[0], "r", encoding="utf-8-sig")
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
			if (len(d_dir.split("_")) >= 2) and not d_dir.endswith("_x"):
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
# --- [ 網路掛號-醫師預約-短網址轉接頭 ] ---
@csrf_exempt
def A006_Online_Booking_2_1_short(request, dept_en, dr_id):
	mapping = _get_dept_dr_map()
	if dr_id in mapping['doctors']:
		doc = mapping['doctors'][dr_id]
		# 將參數重新塞回 request.GET 中供原函式使用
		request.GET = request.GET.copy()
		request.GET['A006_userid'] = dr_id
		request.GET['A006_sename'] = doc['dept_name']
	return A006_Online_Booking_2_1(request)

@csrf_exempt
def A006_Online_Booking_2_1_legacy(request):
	# 攔截舊的 QueryString 網址並轉址到新的 SEO 短網址
	if "A006_userid" in request.GET:
		dr_id = request.GET.get("A006_userid")
		mapping = _get_dept_dr_map()
		if dr_id in mapping['doctors']:
			doc = mapping['doctors'][dr_id]
			# 保留原本可能帶入的其他參數，例如 A006_date_select 等
			other_params = request.GET.copy()
			other_params.pop("A006_userid", None)
			other_params.pop("A006_sename", None)
			
			query_string = ""
			if other_params:
				from urllib.parse import urlencode
				query_string = "?" + urlencode(other_params)
				
			return redirect(f"/A006_Online_Booking_2_1/{doc['dept_en']}/{doc['id']}/{query_string}", permanent=True)
	
	# 若無攔截到，則退回原邏輯
	return A006_Online_Booking_2_1(request)


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
	A006_dirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}*', 'D000*'))
	for A006_dir in A006_dirs:
		if (userid in A006_dir):
			drname = os.path.basename(A006_dir).split("_")[2]
			# 測試區
			# drname = A006_dir.split("\\")[6].split("_")[2]
			dr_concent = open(A006_dir, "r", encoding="utf-8-sig")
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
