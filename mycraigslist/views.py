from django.http import HttpResponse
from django.shortcuts import render

# http://127.0.0.1:8000/mycraigslist/
def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    return render(request, 'mycraigslist/index.html')
