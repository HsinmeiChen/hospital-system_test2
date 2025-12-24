from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect

import re
import os
import datetime
import random

from django.core.paginator import Paginator , EmptyPage, PageNotAnInteger #分頁功能套件，Django本身就有支援

@csrf_exempt
def index(request):

	return render(request, "web_speech/index.html",locals())