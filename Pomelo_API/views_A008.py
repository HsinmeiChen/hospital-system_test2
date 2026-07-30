# 網路掛號_登入頁
@xframe_options_exempt
def A008_login(request):
		from urllib.parse import urlencode

		# 未輸入帳號密碼的情況
		if ("ID_card" in request.GET) and ("Birthday" in request.GET) and ("token" in request.GET):
			user_acc = request.GET.get("ID_card", None)
			user_pwd = request.GET.get("Birthday", None)
			token = request.GET.get("token", None)

			# 確認金鑰正確
			publicToken = "test"
			if token != publicToken:
				url = "/A008_error/"
				params = {"errorMessage": "Token驗證失敗，請重新輸入！"}
				url_with_params = f"{url}?{urlencode(params)}"

				return redirect(url_with_params)
			else:
				# 將生日轉換為西元年格式
				n_user_pwd = str(int(user_pwd) + 19110000)

				# 檢查身分證字號是否存在於資料庫中，確認存在再核對生日
				A008_user_data = MSSQLAPI.A006_Search_NRGPAT(user_acc)
				if A008_user_data is None:
					url = "/A008_error/"
					params = {"errorMessage": "您目前身分為初診，請至服務櫃台填寫初診單。"}
					url_with_params = f"{url}?{urlencode(params)}"

					return redirect(url_with_params)
				else:
					# 核對生日是否正確
					if (A008_user_data[2] == n_user_pwd):
						request.session["A008_patid"] = A008_user_data[0]
						request.session["A008_patname"] = A008_user_data[1]
						request.session["A008_acc"] = user_acc
						request.session["A008_pwd"] = user_pwd

						# 進入網路掛號頁面
						return redirect("/A008_Online_Booking_0/")
					else:
						url = "/A008_error/"
						params = {"errorMessage": "身分證字號或生日日期有錯誤！"}
						url_with_params = f"{url}?{urlencode(params)}"

						return redirect(url_with_params)
		else:
			url = "/A008_error/"
			params = {"errorMessage": "資料有缺失，請重新輸入！"}
			url_with_params = f"{url}?{urlencode(params)}"

			return redirect(url_with_params)

@xframe_options_exempt
def A008_Online_Booking_0(request):
	return render(request, "A008/A008_Patient_Guide_2_0.html", {"A008_True": True})

@xframe_options_exempt
def A008_Online_Booking_1(request):
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
	return render(request, "A008/A008_Patient_Guide_2_1.html", {
		'A008_True': True,
		'datas': datas,
	})

@xframe_options_exempt
def A008_Online_Booking_1_1(request):
	A008_now = datetime.datetime.now()
	A008_now = datetime.datetime.strftime(A008_now,"%H:%M:%S")

	A008_radio_day_1 = datetime.date.today()
	A008_radio_day_2 = get_next_month_start(1)
	A008_radio_day_3 = get_next_month_start(2)
	A008_radio_day_1 = datetime.datetime.strftime(A008_radio_day_1,"%Y.%m")
	A008_radio_day_2 = A008_radio_day_2.replace("/", ".")[:7]
	A008_radio_day_3 = A008_radio_day_3.replace("/", ".")[:7]

	sename = request.GET.get("A008_sename")
	if (sename == "高壓氧中心"):
		sename = "骨科"

		return redirect("/A008_Online_Booking_2_1/?A008_sename=骨科&A008_userid=HA01855")

	A008_I000 = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}*', 'I000*'))

	# 科室介紹資訊
	I000_concent = open(A008_I000[0], "r", encoding="utf-8-sig")
	A008_I000_list = I000_concent.readlines()
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
	if ("A008_date_check_add" in request.GET):
		A008_now_date = request.GET.get("A008_date_check_add")
		I000_days = datetime.datetime.strptime(A008_now_date, "%Y%m%d")
		I000_days_limit = datetime.datetime.now()
		I000_days_limit = I000_days_limit + datetime.timedelta(days=90)
		I000_days = I000_days + datetime.timedelta(days=7)
		if (I000_days > I000_days_limit):
			I000_days_limit_start = True
			I000_days = I000_days_limit
	elif ("A008_date_check_sub" in request.GET):
		A008_now_date = request.GET.get("A008_date_check_sub")
		A008_today = datetime.date.today().strftime("%Y%m%d")
		if (A008_today == A008_now_date):
			I000_days = datetime.date.today()
			day_sub = I000_days.isoweekday() - 1
			I000_days = I000_days - datetime.timedelta(days=day_sub)
		else:
			I000_days = datetime.datetime.strptime(A008_now_date, "%Y%m%d")
			I000_days = I000_days - datetime.timedelta(days=7)
	# 醫師介面選擇的月份
	elif ("switch_day" in request.GET):
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
	else:
		I000_days = datetime.date.today()
		day_sub = I000_days.isoweekday() - 1
		I000_days = I000_days - datetime.timedelta(days=day_sub)

	# 當週該科醫師掛號資料
	I000_days = I000_days - datetime.timedelta(days=I000_days.weekday())
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

	A008_today = datetime.datetime.now()
	A008_today = datetime.datetime.strftime(A008_today,"%Y%m%d")

	data_counts = MSSQLAPI.A006_Search_NRGNPRO_COUNT_BY_SECTNO(sectno, I000_day_compare_list[0], I000_day_compare_list[6])

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

	# 判段當日是否有看診
	for compare_day in I000_day_compare_list:
		I000_lookday_list_sss = []
		for lookday_list_ss in I000_lookday_list_ss:
			if ((compare_day == A008_today) and (A008_now > "11:45:00") or (A008_today > compare_day)) and (lookday_list_ss[0] == compare_day):
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
			if ((compare_day == A008_today) and (A008_now > "16:45:00") or (A008_today > compare_day)) and (lookday_list_aa[0] == compare_day):
				I000_lookday_list_aaa.append([compare_day, "Q", lookday_list_aa[2]])
			elif (lookday_list_aa[0] == compare_day):
				lookday_list_aa_data = []
				person_count = 0
				# 查詢診間人數
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
			if ((compare_day == A008_today) and (A008_now > "20:30:00") or (A008_today > compare_day)) and (lookday_list_nn[0] == compare_day):
				I000_lookday_list_nnn.append([compare_day, "Q", lookday_list_nn[2]])
			elif (lookday_list_nn[0] == compare_day):
				lookday_list_nn_data = []
				person_count = 0
				# 查詢診間人數
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

	return render(request, "A008/A008_Patient_Guide_2_1_1.html", {
		'A008_True': True,
		'datas': datas,
		'sename': sename,
		'A008_I000_list': A008_I000_list,
		'A008_radio_day_1': A008_radio_day_1,
		'A008_radio_day_2': A008_radio_day_2,
		'A008_radio_day_3': A008_radio_day_3,
		'I000_day_list': I000_day_list,
		'c_startdt': c_startdt,
		'A008_today': A008_today,
	})

@xframe_options_exempt
def A008_Online_Booking_2(request):
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
				django_doctors4 = []
				re_subject = d_dir.split("_")
				subjects.append(re_subject[1])
				sename = re_subject[1]
				dept_en = re_subject[2] if len(re_subject) >= 3 else ""
				dd_dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'department', str(subject), str(d_dir)))

				for dd_dir in dd_dirs:
					if ("D000" in dd_dir):
						red_dir = dd_dir.split("_")
						django_doctors.append(red_dir[2].split(" ")[0])
						django_doctors2.append(red_dir[3].replace(".txt", ""))
						django_doctors3.append(sename)
						django_doctors4.append(dept_en)
						
						z_doctors = zip(django_doctors, django_doctors2, django_doctors3, django_doctors4)

				doctors.append(z_doctors)

	datas = zip(subjects, doctors)

	return render(request, "A008/A008_Patient_Guide_2_2.html", {
		'A008_True': True,
		'datas': datas,
	})

@xframe_options_exempt
def A008_Online_Booking_2_1(request):
	A008_radio_day_1 = datetime.date.today()
	A008_radio_day_2 = get_next_month_start(1)
	A008_radio_day_3 = get_next_month_start(2)
	A008_radio_day_1 = datetime.datetime.strftime(A008_radio_day_1,"%Y.%m")
	A008_radio_day_2 = A008_radio_day_2.replace("/", ".")[:7]
	A008_radio_day_3 = A008_radio_day_3.replace("/", ".")[:7]

	A008_now = datetime.datetime.now()
	A008_now = datetime.datetime.strftime(A008_now,"%H:%M:%S")

	# 選擇醫師需要帶入的參數
	if ("A008_userid" in request.GET):
		userid = request.GET.get("A008_userid"," ")
	if ("A008_sename" in request.GET):
		sename = request.GET.get("A008_sename"," ")
		
		# 查詢科別代碼
		sectno = MSSQLAPI.A006_Search_SEC_SECTNO_BY_SENAME(sename)

		# ========== [動態尋找醫師主科別 2026.07.17 異動] ==========
		# 若該科室 (例如: 高壓氧中心) 在 HIS 系統中無對應代碼 (sectno == "error")，
		if sectno == "error":
			# 1. 優先檢查該醫師在「當前科別」的 .txt 檔案是否有手動指定 <book> 標籤
			specified_dept = None
			current_file_pattern = os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}*', f'*_{userid}.txt')
			current_files = glob.glob(current_file_pattern)
			if current_files:
				try:
					with open(current_files[0], 'r', encoding='utf-8-sig') as f:
						for line in f:
							if "<book>" in line:
								specified_dept = line.replace("<book>", "").replace("</book>", "").strip()
								break
				except Exception:
					pass
			
			if specified_dept:
				test_sectno = MSSQLAPI.A006_Search_SEC_SECTNO_BY_SENAME(specified_dept)
				if test_sectno != "error":
					sename = specified_dept
					sectno = test_sectno
					
			# 2. 若無手動指定，或指定的科別無效，則動態去尋找該醫師隸屬的「其他科別 (主科別)」。
			if sectno == "error":
				search_pattern = os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', '*', f'*_{userid}.txt')
				# 加上 sorted()，確保資料夾名稱前面的序號 (如 5_一般外科 < 8_乳房外科) 決定優先順序
				for path in sorted(glob.glob(search_pattern)):
					dept_folder = os.path.basename(os.path.dirname(path))
					parts = dept_folder.split('_')
					if len(parts) >= 2:
						dept_name = parts[1]
						# 找到非當前失敗的科別，且確定能在 HIS 查到代碼
						if dept_name and dept_name != sename:
							test_sectno = MSSQLAPI.A006_Search_SEC_SECTNO_BY_SENAME(dept_name)
							if test_sectno != "error":
								sename = dept_name
								sectno = test_sectno
								break
		# ==========================================
	else:
		sectno = None

	# 醫師基本資料介紹
	A008_dirs = glob.glob(os.path.join(settings.MEDIA_ROOT, 'department', 'D000*', f'*{sename}*', 'D000*'))
	for A008_dir in A008_dirs:
		if (userid in A008_dir):
			drname = os.path.basename(A008_dir).split("_")[2]
			dr_concent = open(A008_dir, "r", encoding="utf-8-sig")
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
	if ("A008_date_check_add" in request.GET):
		A008_now_date = request.GET.get("A008_date_check_add")
		dr_days = datetime.datetime.strptime(A008_now_date, "%Y%m%d")
		dr_days_limit = datetime.datetime.now()
		dr_days_limit = dr_days_limit + datetime.timedelta(days=90)
		dr_days = dr_days + datetime.timedelta(days=7)
		if (dr_days > dr_days_limit):
			dr_days_limit_start = True
			dr_days = dr_days_limit
	# 醫師介面上一周
	elif ("A008_date_check_sub" in request.GET):
		A008_now_date = request.GET.get("A008_date_check_sub")
		A008_today = datetime.date.today().strftime("%Y%m%d")
		if (A008_today == A008_now_date):
			dr_days = datetime.date.today()
			day_sub = dr_days.isoweekday() - 1
			dr_days = dr_days - datetime.timedelta(days=day_sub)
		else:
			dr_days = datetime.datetime.strptime(A008_now_date, "%Y%m%d")
			dr_days = dr_days - datetime.timedelta(days=7)
	# 別的介面跳轉過來的保存選擇日期
	elif ("A008_date_select" in request.GET):
		dr_days = request.GET.get("A008_date_select")
		dr_days = datetime.datetime.strptime(dr_days, "%Y%m%d")
		day_sub = dr_days.isoweekday() - 1
		dr_days = dr_days - datetime.timedelta(days=day_sub)
	# 醫師介面選擇的月份
	elif ("switch_day" in request.GET):
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
	else:
		dr_days = datetime.date.today()
		day_sub = dr_days.isoweekday() - 1
		dr_days = dr_days - datetime.timedelta(days=day_sub)

	# 醫師掛號資料
	dr_days = dr_days - datetime.timedelta(days=dr_days.weekday())
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

	A008_today = datetime.datetime.now()
	A008_today = datetime.datetime.strftime(A008_today,"%Y%m%d")

	# 判段當日是否有看診
	for compare_day in dr_day_compare_list: # 1~7
		if (compare_day in dr_lookday_list_ss):
			if ((compare_day == A008_today) and (A008_now > "11:45:00")) or (A008_today > compare_day):
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
			if ((compare_day == A008_today) and (A008_now > "16:45:00")) or (A008_today > compare_day):
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
			if ((compare_day == A008_today) and (A008_now > "20:45:00")) or (A008_today > compare_day):
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

	return render(request, "A008/A008_Patient_Guide_2_2_1.html", {
		'A008_True': True,
		'dr_clinic_list': dr_clinic_list,
		'drname': drname,
		'sename': sename,
		'dr_img': dr_img,
		'dr_e': dr_e,
		'userid': userid,
		'A008_radio_day_1': A008_radio_day_1,
		'A008_radio_day_2': A008_radio_day_2,
		'A008_radio_day_3': A008_radio_day_3,
		'switch_day2': switch_day2,
		'sectno': sectno,
		'dr_day_list': dr_day_list,
		'c_startdt': c_startdt,
		'A008_today': A008_today,
	})

@xframe_options_exempt
def A008_Online_Booking_check(request):
	# 預先定義變數以避免 UnboundLocalError  (115/05/19 新增)
	stop_reserve_on = False
	repeat_data_on = False
	specialSectno = False
	pat_data = None
	pat_name = ""
	pat_id = ""
	# --- (115/05/19 新增) ---

	visitdt = request.GET.get("user_visitdt").replace("/","")
	n_visitdt = visitdt[:4] + "-" + visitdt[4:6] + "-" + visitdt[6:8]

	shiftno = request.GET.get("user_shiftno")
	if (shiftno == "1"):
		n_shiftno = "早"
	elif (shiftno == "2"):
		n_shiftno = "午"
	elif (shiftno == "3"):
		n_shiftno = "夜"
	sectno = request.GET.get("user_sectno")
	n_sectno = MSSQLAPI.A006_Search_NRGSEC_SHOWNAME(sectno)[0]
	doccd = request.GET.get("user_doccd")
	n_doccd = request.GET.get("user_drname")
	roomno = MSSQLAPI.A006_Search_SCD_ROOMNO(visitdt, shiftno, sectno, doccd)[0]
	n_roomno = roomno[1:]
	patid = request.session["A008_patid"]
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

	if (request.GET["user_sectno"] in ["12","AB","AC","AA","01","AG","AD"]) and (age < 180000):
		stop_reserve_on = True
	elif (request.GET["user_sectno"] in ["09"]) and (age < 120000):
		stop_reserve_on = True

	# 查詢是否有重複預約
	repeat_data = MSSQLAPI.A006_Search_NRGRGB_FOR_PATID(patid, visitdt, shiftno, doccd)

	if (repeat_data != None):
		repeat_data_on = True

	request.session["A008_user_visitdt"] = visitdt
	request.session["A008_user_shiftno"] = shiftno
	request.session["A008_user_roomno"] = roomno
	request.session["A008_user_sectno"] = sectno
	request.session["A008_user_doccd"] = doccd
	request.session["A008_show_user_visitdt"] = n_visitdt
	request.session["A008_show_user_shiftno"] = n_shiftno
	request.session["A008_show_user_roomno"] = n_roomno
	request.session["A008_show_user_sectno"] = n_sectno
	request.session["A008_show_user_doccd"] = n_doccd

	return render(request, "A008/A008_Patient_Guide_2_6.html", {
		'A008_True': True,
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

# 掛號
@xframe_options_exempt
def A008_register(request):
	A008_now = datetime.datetime.now()
	A008_now = datetime.datetime.strftime(A008_now,"%H:%M:%S")
	A008_today = datetime.datetime.now()
	A008_today = datetime.datetime.strftime(A008_today,"%Y%m%d")

	idno = " "
	patid = request.session["A008_patid"]
	visitdt = request.session["A008_user_visitdt"]
	shiftno = request.session["A008_user_shiftno"]
	roomno = request.session["A008_user_roomno"]
	sectno = request.session["A008_user_sectno"]
	doccd = request.session["A008_user_doccd"]

	if ((visitdt == A008_today) and (shiftno == "1") and (A008_now > "11:45:00")) or (A008_today > visitdt):
		return HttpResponse("超過早診預約時間")
	elif ((visitdt == A008_today) and (shiftno == "2") and (A008_now > "16:45:00")) or (A008_today > visitdt):
		return HttpResponse("超過午診預約時間")
	elif ((visitdt == A008_today) and (shiftno == "3") and (A008_now > "20:30:00")) or (A008_today > visitdt):
		return HttpResponse("超過晚診預約時間")
	else:
		# 查詢當日資料序號（需使用交易機制?）
		recno = MSSQLAPI.A006_Search_NRGRGS_RECNO(visitdt)
		if (recno == None):
			MSSQLAPI.A006_Insert_NRGRGS_RECNO(visitdt)
			recno = 1
			MSSQLAPI.Insert_LOG_WEB(patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd)
			resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
			request.session["A008_user_recno"] = recno
		else:
			insert_ok = True
			recno = recno[2] + 1
			MSSQLAPI.A006_Update_NRGRGS_RECNO(visitdt)
			print("===自助繳費機開始掛號(複診)===")
			insert_ok = False
			MSSQLAPI.Insert_LOG_WEB(patid, idno, visitdt, recno, shiftno, roomno, sectno, doccd)
			resluet1 = MSSQLAPI.A006_Insert_NRGRGB_0(patid, visitdt, recno, shiftno, roomno, sectno, doccd)
			request.session["A008_user_recno"] = recno

	return HttpResponse("OK")

# 掛號結果
@xframe_options_exempt
def A008_find_register(request):
	data = {}
	now = datetime.datetime.now()
	recno = request.session["A008_user_recno"]
	visitdt = request.session["A008_user_visitdt"]

	visitno = MSSQLAPI.A006_Search_NRGRGB_VISITNO(visitdt, recno)[0]
	del request.session["A008_user_recno"]

	if (visitno > -1):
		data["response"] = "success"
		data["visitno"] = visitno
		data["visitdt"] = request.session["A008_show_user_visitdt"]
		data["shiftno"] = request.session["A008_show_user_shiftno"]
		data["roomno"] = request.session["A008_show_user_roomno"]
		data["sectno"] = request.session["A008_show_user_sectno"]
		data["doccd"] = request.session["A008_show_user_doccd"]
	else:
		data["response"] = "error"
		data["errorMessage"] = "掛號失敗，請重新掛號。"

	return JsonResponse(data)

@xframe_options_exempt
def A008_error(request):
		errorMessage = request.GET.get("errorMessage", None)
		return render(request, "A008/A008_postmessage.html", {"response": "error", "errorMessage": errorMessage})

@xframe_options_exempt
def A008_logout(request):
	request.session.flush()