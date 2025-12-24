from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import copy

# import sys
# sys.path.append(r"C:\Python\Pomelo_test\Reserve_Pre")
# print(sys.path)
from Reserve_Pre import Reserve_Pre

def Hellow1(request):
	return HttpResponse("Hellow123") #網頁上會顯示


# request.session["emp"] = emp
# emp = request.session.get("emp")

#登入頁
@csrf_exempt
def A007_Reserve_pre_login(request):
	A007_True = "True"
	Drug_login = "True"
	if ("login_sub" in request.POST): #登入
		#輸入病歷號-------------------------------------
		# pdnum = request.POST.get("pdnum") #病歷號
		# # print(pdnum)
		# pdnum = pdnum.zfill(10)
		#輸入病歷號-------------------------------------


		#輸入身分證/生日-------------------------------------
		pd_id = request.POST.get("pd_id") #身分證
		# print(pd_id)
		pd_id = pd_id.upper() #轉成大寫
		birthday = request.POST.get("birthday")
		write_log = Reserve_Pre.AllCode.logrecond(pd_id,birthday) #登入log紀錄
		#輸入身分證/生日-------------------------------------



		if birthday.isdigit():
			data = Reserve_Pre.AllCode.searchChrocard_new(pd_id,birthday) #身分證
			mark = '尋找'

			pd_info = data[0] #病患基本資料
			data_info = data[1] #慢箋資料
			breakdata = data[2] #爽約紀錄
			stop_date = data[3] #解除黑名單日期

			breaktime = len(breakdata)
			# print(breakdata)
			# print(breaktime)

			# if birthday.isdigit():身分證
			if (pd_info == '無此病患'): #登入失敗
				alert = '請確認「身分證字號」與「出生年月日」是否輸入正確'
				return render(request, 'Reserve_Pre/Patient_Guide_Drug_1.html', locals())

			else: #登入成功
				Drug_login = "False"
				Pdinfo_Page = "True"
				#-----------記住資訊--------------------------
				request.session["pd_info"] = pd_info
				request.session["data_info"] = data_info
				request.session["breakdata"] = breakdata
				request.session["stop_date"] = stop_date
				request.session["mark"] = mark
				#-----------記住資訊--------------------------

				return render(request, 'Reserve_Pre/Patient_Guide_Drug_2.html', locals())

		else: #登入失敗
			alert = '請確認是否輸入正確'
			return render(request, 'Reserve_Pre/Patient_Guide_Drug_1.html', locals())

	return render(request, 'Reserve_Pre/Patient_Guide_Drug_1.html', locals())

#登出頁
def A007_Reserve_pre_logout(request):
	request.session.flush()
	# print("已執行登出頁")
	return render(request, 'Reserve_Pre/Patient_Guide_Drug_1.html', locals())

#預約/取消預約
def A007_Reserve_pre_reserve(request): 
	#-----------拿出資訊--------------------------
	pd_info = request.session.get("pd_info")
	data_info = request.session.get("data_info")
	breakdata = request.session.get("breakdata")
	stop_date = request.session.get("stop_date")
	#-----------拿出資訊--------------------------

	# breaktime = len(breakdata)

	if (pd_info == None):
		alert = '請重新登入'
		# return redirect("/A007_Reserve_pre/login/")
		return HttpResponse(alert)

	else:
		breaktime = len(breakdata)
		
		values = request.GET.get("A007_chroarddata")
		func = values.split('$')
		pd_info2 = copy.deepcopy(pd_info)
		data_info2 = copy.deepcopy(data_info)
		
		if (func[0] == '預約'):
			data_info = Reserve_Pre.AllCode.reserve(pd_info2,data_info2,values) #預約完的新資料
			mark = '預約後'
			request.session["data_info"] = data_info #記住新data_info
			request.session["mark"] = mark

			return HttpResponse(data_info) #網頁回應

		else: #取消預約
			newdata = Reserve_Pre.AllCode.cancelReserve(pd_info2,data_info2,values) #預約取消

			if (newdata == '不可取消'):
				return HttpResponse(newdata) #網頁回應
			else:
				data_info = newdata[1] #慢箋資料
				breakdata = newdata[2]
				#-----------記住資訊--------------------------
				request.session["data_info"] = data_info #記住新data_info
				request.session["breakdata"] = breakdata
				#-----------記住資訊--------------------------

		return render(request, 'Reserve_Pre/Patient_Guide_Drug_2.html', locals())

#讀取出資料
def A007_Reserve_pre_data(request):
	A007_True = "True"
	Pdinfo_Page = "True"
	#-----------拿出資訊--------------------------
	pd_info = request.session.get("pd_info")
	data_info = request.session.get("data_info")
	breakdata = request.session.get("breakdata")
	stop_date = request.session.get("stop_date")
	mark = request.session.get("mark")
	#-----------拿出資訊--------------------------

	if (pd_info == None):
		alert = '請重新登入'
		return redirect("/A007_Reserve_pre/login/")
	else:
		breaktime = len(breakdata)

	return render(request, 'Reserve_Pre/Patient_Guide_Drug_2.html', locals())











#目前沒用到-----------------------------------------------------------------------
def iptest(): #抓取使用者ip
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		user_ip = x_forwarded_for.split(',')[0]  # 取第一個 IP
	else:
		user_ip = request.META.get('REMOTE_ADDR')  # 使用者的真實 IP

	# 測試輸出或處理 IP
	print(f"使用者 IP: {user_ip}")
	print(user_ip)
#目前沒用到-----------------------------------------------------------------------


