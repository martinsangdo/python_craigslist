from django.conf.urls import url

from . import views

urlpatterns = [
    url('', views.index, name='index'), #http://127.0.0.1:8000/cr/
]
