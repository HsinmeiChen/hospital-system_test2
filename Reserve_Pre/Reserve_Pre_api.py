import pymssql
from django.conf import settings

if settings.DEBUG:
	import oracledb as cx_Oracle
else:
	import cx_Oracle

#HIS連線----------------------------------------
case_plsql_host = settings.CASE_PLSQL_HOST
case_plsql_db = settings.CASE_PLSQL_DB
case_plsql_user = settings.CASE_PLSQL_USER
case_plsql_pwd = settings.CASE_PLSQL_PWD
#HIS連線----------------------------------------


#MSSQL 192.168.66.149-------------------------------
ms_host = settings.MSSQL_66_149_HOST
ms_db = settings.MSSQL_66_149_DB
ms_user = settings.MSSQL_66_149_USER
ms_pwd = settings.MSSQL_66_149_PWD
#MSSQL 192.168.66.149-------------------------------


#MSSQL 192.168.66.146-------------------------------
mssql_66_146_host = settings.MSSQL_66_146_HOST
mssql_66_146_db = settings.MSSQL_66_146_DB
mssql_66_146_user = settings.MSSQL_66_146_USER
mssql_66_146_pwd = settings.MSSQL_66_146_PWD
#MSSQL 192.168.66.146-------------------------------







class HisapiReserve:
	def select_CHTPAT(pd_id,birthday): #找病人資料
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')

		sql = '''SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_MOBILE,PT_TELNO_HOME
				FROM CHTPAT
				WHERE PT_IDNO = '{pd_id}' --身分證字號
				AND PT_BIRTHDATE = '{birthday}'--生日
				'''.format(
					pd_id=pd_id,
					birthday=birthday)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()
		return(data)

	def select_CHTPAT2(pdnum): #找病人資料(病歷號)
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')

		sql = '''SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_MOBILE,PT_TELNO_HOME
				FROM CHTPAT
				WHERE PT_PATID = '{pdnum}'
				'''.format(
					pdnum=pdnum)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()
		return(data)

	def select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT(pd_id,birthday,today):#搜尋慢箋
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')


		sql = '''SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_TELNO_HOME,PT_MOBILE,CRO_CHROCARD,SEC_SENAME,CRO_VISITDT,EMP_EMPNAME,CRO_COUNTER,CRO_MAXTIMES,CRO_LASTDATE,CRO_ENDDATE,CRO_DAYS,CRO_SECOND_START,CRO_SECOND_END,CRO_THIRD_START,CRO_THIRD_END,OCB_DRUGNO
			FROM OPDCRO
			INNER JOIN OPDVCB 
			ON CRO_CHROCARD = OCB_CHROCARD
			--AND CRO_VISITDT = OCB_VISITDT
			AND CRO_LASTDATE = OCB_VISITDT --找最近領藥號(最近領藥日=看診日)
			INNER JOIN BASEMP 
			ON EMP_EMPNO = OCB_DOCCD 
			INNER JOIN BASSECT 
			ON OCB_SECTNO = SEC_SECTNO  
			INNER JOIN CHTPAT
			ON CRO_PATID = PT_PATID
			WHERE  OCB_NEXT > 0 --批價次數
			AND CRO_DCTYPE = 'N' --未取消
			AND OCB_TYPE <> 'D'
			AND CRO_COUNTER < 3
			AND CRO_MAXTIMES > CRO_COUNTER --最大調劑次數 >累計調劑次數 (未完成)
			AND PT_IDNO = '{pd_id}' --身分證字號
			AND PT_BIRTHDATE = '{birthday}'--生日
			AND CRO_ENDDATE > '{today}' --最終有效日期
				'''.format(
					pd_id=pd_id,
					birthday=birthday,
					today=today)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT2(pdnum,today):#搜尋慢箋(病歷號)
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')


		sql = '''SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_TELNO_HOME,PT_MOBILE,CRO_CHROCARD,SEC_SENAME,CRO_VISITDT,EMP_EMPNAME,CRO_COUNTER,CRO_MAXTIMES,CRO_LASTDATE,CRO_ENDDATE,CRO_DAYS,CRO_SECOND_START,CRO_SECOND_END,CRO_THIRD_START,CRO_THIRD_END,OCB_DRUGNO
			FROM OPDCRO
			INNER JOIN OPDVCB 
			ON CRO_CHROCARD = OCB_CHROCARD
			--AND CRO_VISITDT = OCB_VISITDT
			AND CRO_LASTDATE = OCB_VISITDT --找最近領藥號(最近領藥日=看診日)
			INNER JOIN BASEMP 
			ON EMP_EMPNO = OCB_DOCCD 
			INNER JOIN BASSECT 
			ON OCB_SECTNO = SEC_SECTNO  
			INNER JOIN CHTPAT
			ON CRO_PATID = PT_PATID
			WHERE  OCB_NEXT > 0 --批價次數
			AND CRO_DCTYPE = 'N' --未取消
			AND OCB_TYPE <> 'D'
			AND CRO_COUNTER < 3
			AND CRO_MAXTIMES > CRO_COUNTER --最大調劑次數 >累計調劑次數 (未完成)
			AND PT_PATID = '{pdnum}'
			AND CRO_ENDDATE > '{today}' --最終有效日期
				'''.format(
					pdnum=pdnum,
					today=today)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT3(pdnum,today):#搜尋慢箋(病歷號new)
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')


		sql = '''SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_TELNO_HOME,PT_MOBILE,CRO_CHROCARD,SEC_SENAME,CRO_VISITDT,EMP_EMPNAME,CRO_COUNTER,CRO_MAXTIMES,CRO_LASTDATE,CRO_ENDDATE,CRO_DAYS,CRO_SECOND_START,CRO_SECOND_END,CRO_THIRD_START,CRO_THIRD_END,OCB_VISITSEQ
			FROM OPDCRO
			INNER JOIN OPDVCB 
			ON CRO_CHROCARD = OCB_CHROCARD
			--AND CRO_VISITDT = OCB_VISITDT
			AND CRO_LASTDATE = OCB_VISITDT --找最近領藥號(最近領藥日=看診日)
			INNER JOIN BASEMP 
			ON EMP_EMPNO = OCB_DOCCD 
			INNER JOIN BASSECT 
			ON OCB_SECTNO = SEC_SECTNO
			INNER JOIN CHTPAT
			ON CRO_PATID = PT_PATID
			WHERE  OCB_NEXT > 0 --批價次數
			AND CRO_DCTYPE = 'N' --未取消
			AND OCB_TYPE <> 'D'
			--AND CRO_COUNTER < 3
			--AND CRO_MAXTIMES > CRO_COUNTER --最大調劑次數 >累計調劑次數 (未完成)
			AND PT_PATID = '{pdnum}'
			AND CRO_ENDDATE > '{today}' --最終有效日期
				'''.format(
					pdnum=pdnum,
					today=today)
		# print(sql)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_OPDCRO_OPDVCB_BASEMP_BASSECT_CHTPAT4(pdnum,today):#搜尋慢箋(病歷號new2) 20250304改
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')

		sql = f"""SELECT PT_IDNO,PT_BIRTHDATE,PT_PATNAME,PT_PATID,PT_SEX,PT_TELNO_HOME,PT_MOBILE,CRO_CHROCARD,SEC_SENAME,CRO_VISITDT,EMP_EMPNAME,CRO_COUNTER,CRO_MAXTIMES,CRO_LASTDATE,CRO_ENDDATE,CRO_DAYS,CRO_SECOND_START,CRO_SECOND_END,CRO_THIRD_START,CRO_THIRD_END,main_opd.max_OCB_VISITSEQ,main_opd.OCB_DRUGNO
				FROM OPDCRO
				INNER JOIN CHTPAT
				ON CRO_PATID = PT_PATID
				INNER JOIN (

				SELECT in_opd.OCB_VISITDT, inside_opd.max_OCB_VISITSEQ, in_opd.OCB_CHROCARD, in_opd.OCB_DOCCD, in_opd.OCB_SECTNO,in_opd.OCB_DRUGNO
						FROM OPDVCB in_opd
						INNER JOIN (
						
							SELECT MAX(OCB_VISITDT) AS max_VISITDT,  OCB_CHROCARD, 
									MAX(OCB_VISITSEQ) KEEP (DENSE_RANK FIRST ORDER BY 
									CASE 
									WHEN OCB_VISITSEQ = 'IC03' THEN 1
									WHEN OCB_VISITSEQ = 'IC02' THEN 2
									ELSE 3 
									END
									) AS max_OCB_VISITSEQ
								FROM OPDVCB
								WHERE OCB_TYPE <> 'D'
								AND OCB_NEXT > 0
								AND OCB_CANDTTM = ' '
								AND OCB_PATID = '{pdnum}' --病歷號
								GROUP BY OCB_CHROCARD
					
							) inside_opd
						ON in_opd.OCB_CHROCARD = inside_opd.OCB_CHROCARD
						AND in_opd.OCB_VISITDT = inside_opd.max_VISITDT
						--AND in_opd.OCB_VISITSEQ = inside_opd.max_OCB_VISITSEQ
						WHERE in_opd.OCB_TYPE <> 'D'
						AND in_opd.OCB_NEXT > 0
						AND in_opd.OCB_CANDTTM = ' '
						AND in_opd.OCB_PATID = '{pdnum}' --病歷號
					
					) main_opd
					ON CRO_CHROCARD = main_opd.OCB_CHROCARD
					INNER JOIN BASEMP
					ON EMP_EMPNO = main_opd.OCB_DOCCD
					INNER JOIN BASSECT 
					ON SEC_SECTNO = main_opd.OCB_SECTNO
					WHERE CRO_DCTYPE = 'N' --未取消
					AND main_opd.max_OCB_VISITSEQ <> 'IC03' --此慢箋未完成
					--AND CRO_COUNTER < CRO_MAXTIMES --此慢箋未完成
					AND CRO_ENDDATE > '{today}' --最終有效日期
					AND PT_PATID = '{pdnum}' --病歷號
					ORDER BY CRO_VISITDT DESC
				"""

		# print(sql)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_OPDCRO_OPDVCB(chrocard,times,pd_num):#搜尋慢箋是否已領(黑名單)
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')


		sql = '''
			SELECT SEC_SENAME,OCB_CHROCARD,SUBSTR(OCB_VISITSEQ, -1, 1),OCB_VISITDT
			FROM OPDVCB
			INNER JOIN BASSECT 
			ON OCB_SECTNO = SEC_SECTNO
			WHERE OCB_TYPE <> 'D'
			AND OCB_CHROCARD = '{chrocard}'
			AND OCB_VISITSEQ = 'IC0{times}'
			AND OCB_PATID = '{pd_num}'
				'''.format(
					chrocard=chrocard,
					times=times,
					pd_num = pd_num)
		# print(sql)

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_BASCODE(): #過年提早領取參數
		# 連線Oracle資料庫
		if settings.DEBUG:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db)
		else:
			connection = cx_Oracle.connect(case_plsql_user + '/' + case_plsql_pwd + '@' + case_plsql_host + '/' + case_plsql_db
			,encoding='UTF-8', nencoding='UTF-8')

		sql = '''SELECT BAS_FIELD
				FROM BASCODE
				WHERE BAS_SYSTEMID = 'OPO'
				AND BAS_CODETYPE = '00'
				AND BAS_CODE = '98'
				'''

		# 定義資料庫游標
		c = connection.cursor()
		c.execute(sql)
		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()
		return(data)





class MssqlApiReserve:
	def insertA007LoginLogWeb(idno, patBirthday, url): #登入LOG 20241225新增
		# 連線MSSQL資料庫
		connection = pymssql.connect(
			host = mssql_66_146_host,
			user = mssql_66_146_user,
			password = mssql_66_146_pwd,
			database = mssql_66_146_db,
			charset='UTF-8')

		# 輸入你要查找的資料表語法
		sql = """INSERT INTO LOG_WEB(
			IDNO,
			PATBIRTHDAY,
			URL) VALUES (
			'{idno}',
			'{patBirthday}',
			'{url}')
		""".format(
			idno = idno,
			patBirthday = patBirthday,
			url = url)

		# 定義資料庫游標
		c = connection.cursor(as_dict = True)
		c.execute(sql)

		# 如果執行的是修改操作，需要提交事務；如果執行的是查詢操作，不需要提交
		connection.commit()

		c.close()
		connection.close()

		return("true")

	def select_reserve_pre_list(chrocard,resno_times,todayformat): #找預約紀錄
		connection = pymssql.connect(
				host = ms_host,
				user = ms_user,
				password = ms_pwd,
				database = ms_db,
				charset='UTF-8'
			)

		sql = '''
				SELECT reserve_date
				FROM reserve_pre_list
				WHERE chrocard = '{chrocard}'
				AND cancel = 'N'
				AND resno_times = '{resno_times}'
				AND reserve_date >= '{todayformat}'
				'''.format(chrocard = chrocard,
							resno_times = resno_times,
							todayformat = todayformat)
		# print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		try:
			c.execute(sql)
		except Exception as e:
			if ('dead or not' in e): #網路斷掉
				pass
			else:
				print(e)
				raise

		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_reserve_pre_list2(chrocard,resno_times,todayformat): #找此筆慢箋爽約紀錄
		connection = pymssql.connect(
				host = ms_host,
				user = ms_user,
				password = ms_pwd,
				database = ms_db,
				charset='UTF-8'
			)

		sql = '''
				SELECT reserve_date
				FROM reserve_pre_list
				WHERE chrocard = '{chrocard}'
				AND cancel = 'N'
				AND resno_times = '{resno_times}'
				AND reserve_date < '{todayformat}' --小於今日(不包含今天)
				'''.format(chrocard = chrocard,
							resno_times = resno_times,
							todayformat = todayformat)
		# print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		try:
			c.execute(sql)
		except Exception as e:
			if ('dead or not' in e): #網路斷掉
				pass
			else:
				print(e)
				raise

		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def select_reserve_pre_list3_new(pdnum,breakdate,todayformat): #找56天內爽約紀錄(黑名單)
		connection = pymssql.connect(
				host = ms_host,
				user = ms_user,
				password = ms_pwd,
				database = ms_db,
				charset='UTF-8'
			)

		sql = '''
				SELECT sen_name,chrocard,resno_times,reserve_date
				FROM reserve_pre_list
				WHERE pd_num = '{pdnum}'
				AND cancel = 'N'
				AND reserve_date >= '{breakdate}' --大於等於56天前
				AND reserve_date < '{todayformat}' --小於今日
				ORDER BY reserve_date
				'''.format(pdnum = pdnum,
							breakdate = breakdate,
							todayformat = todayformat)
		# print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		try:
			c.execute(sql)
		except Exception as e:
			if ('dead or not' in e): #網路斷掉
				pass
			else:
				print(e)
				raise

		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)

	def insert_reserve_pre_list(pd_info,re_data,reserve_date,today): #預約(2025/4/1前)
		connection = pymssql.connect(
			host = ms_host,
			user = ms_user,
			password = ms_pwd,
			database = ms_db,
			charset='UTF-8'
		)

		sql = """
			IF NOT EXISTS(
				SELECT * FROM reserve_pre_list
				WHERE chrocard = '{chrocard}'
				AND resno_times = '{resno_times}'
				AND cancel = 'N'
				AND reserve_date > '{today}'
				)
			BEGIN 
				INSERT INTO reserve_pre_list (chrocard,pd_num,pd_name,pd_idnum,pd_birthday,visitdt,resno_times,sen_name,doc_name,reserve_date,sms_words,cro_lastdate,ocb_drugno)
				VALUES ('{chrocard}', '{pd_num}', N'{pd_name}', '{pd_idnum}', '{pd_birthday}','{visitdt}','{resno_times}', N'{sen_name}', N'{doc_name}','{reserve_date}', 
				N'{pd_name} 您好，您預約({re})領藥，請於早上8點半～下午5點半，持健保卡、慢箋單至藥局櫃檯領藥。如需改期請撥04-36113600，長安醫院關心您～','{cro_lastdate}','{ocb_drugno}');
			END;
		""".format(
				chrocard = re_data[0],
				pd_num = pd_info[0][3],
				pd_name = pd_info[0][2],
				pd_idnum = pd_info[0][0],
				pd_birthday = pd_info[0][1],
				visitdt = re_data[2],
				resno_times = re_data[10],
				sen_name = re_data[1],
				doc_name = re_data[3],
				reserve_date = reserve_date[0],
				re = reserve_date[1],
				cro_lastdate = re_data[11],
				ocb_drugno = re_data[12],
				today = today)
		# print(sql)

		c = connection.cursor(as_dict = True)
		c.execute(sql)
		connection.commit()
		c.close()
		connection.close()

		return("已預約")

	def insert_reserve_pre_list2(pd_info,re_data,reserve_date,today): #預約(2025/4/1後，包含4/1當天)
		# print()
		connection = pymssql.connect(
			host = ms_host,
			user = ms_user,
			password = ms_pwd,
			database = ms_db,
			charset='UTF-8'
		)

		sql = """
			IF NOT EXISTS(
				SELECT * FROM reserve_pre_list
				WHERE chrocard = '{chrocard}'
				AND resno_times = '{resno_times}'
				AND cancel = 'N'
				AND reserve_date > '{today}'
				)
			BEGIN 
				INSERT INTO reserve_pre_list (chrocard,pd_num,pd_name,pd_idnum,pd_birthday,visitdt,resno_times,sen_name,doc_name,reserve_date,sms_words,cro_lastdate,ocb_drugno)
				VALUES ('{chrocard}', '{pd_num}', N'{pd_name}', '{pd_idnum}', '{pd_birthday}','{visitdt}','{resno_times}', N'{sen_name}', N'{doc_name}','{reserve_date}', 
				N'{pd_name} 您好，您預約({re})領藥，請於早上9點半～下午9點半，持健保卡、慢箋單至藥局櫃檯領藥。如需改期請撥04-36113600，長安醫院關心您～','{cro_lastdate}','{ocb_drugno}');
			END;
		""".format(
				chrocard = re_data[0],
				pd_num = pd_info[0][3],
				pd_name = pd_info[0][2],
				pd_idnum = pd_info[0][0],
				pd_birthday = pd_info[0][1],
				visitdt = re_data[2],
				resno_times = re_data[10],
				sen_name = re_data[1],
				doc_name = re_data[3],
				reserve_date = reserve_date[0],
				re = reserve_date[1],
				cro_lastdate = re_data[11],
				ocb_drugno = re_data[12],
				today = today)
		# print(sql)

		c = connection.cursor(as_dict = True)
		c.execute(sql)
		connection.commit()
		c.close()
		connection.close()

		return("已預約")

	def update_reserve_pre_list(cancel_datetime,chrocard,resno_times,today): #取消預約
		connection = pymssql.connect(
				host = ms_host,
				user = ms_user,
				password = ms_pwd,
				database = ms_db,
				charset='UTF-8'
			)

		sql = """
			UPDATE reserve_pre_list 
			SET cancel = 'Y',cancel_datetime='{cancel_datetime}'
			WHERE chrocard = '{chrocard}'
			AND resno_times = '{resno_times}'
			AND cancel = 'N'
			AND reserve_date > '{today}' --今天以前的都無法再取消了(留黑名單)
			""".format(
				cancel_datetime = cancel_datetime,
				chrocard = chrocard,
				resno_times = resno_times,
				today = today)

		c = connection.cursor(as_dict = True)
		c.execute(sql)
		connection.commit()
		c.close()
		connection.close()

		return("已取消")

	def select_reserve_pre_closeday(): #找休診日
		connection = pymssql.connect(
				host = ms_host,
				user = ms_user,
				password = ms_pwd,
				database = ms_db,
				charset='UTF-8'
			)

		sql = '''
				SELECT reserve_close
				FROM reserve_pre_closeday
				WHERE CONVERT(DATE, reserve_close, 112) >= CAST(GETDATE() AS DATE)
				AND cancel = 'N'
				order by reserve_close
				'''

		# print(sql)
		# 定義資料庫游標
		c = connection.cursor()
		try:
			c.execute(sql)
		except Exception as e:
			if ('dead or not' in e): #網路斷掉
				pass
			else:
				print(e)
				raise

		data = c.fetchall()
		# print("{:-^50s}".format("下一筆"))
		c.close()
		connection.close()

		return(data)