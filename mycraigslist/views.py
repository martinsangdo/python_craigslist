from django.http import HttpResponse

# http://127.0.0.1:8000/cr/
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
