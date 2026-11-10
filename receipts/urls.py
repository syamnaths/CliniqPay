from django.urls import path
from receipts import views

app_name = 'receipts'

urlpatterns = [
    path('<slug:slug>/<str:bill_number>/view/', views.view_receipt, name='view'),
    path('<slug:slug>/receipt/<str:bill_number>/', views.view_receipt, name='receipt_legacy'),
    path('<slug:slug>/<str:bill_number>/send/', views.dispatch_whatsapp, name='dispatch'),
    path('<slug:slug>/<str:bill_number>/status/', views.receipt_status, name='status'),
]
