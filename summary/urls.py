from django.urls import path
from summary import views

app_name = 'summary'

urlpatterns = [
    path('<slug:slug>/', views.daily_report, name='daily_report'),
    path('<slug:slug>/send-whatsapp/', views.send_whatsapp, name='send_whatsapp'),
]
