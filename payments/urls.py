from django.urls import path
from payments import views

app_name = 'payments'

urlpatterns = [
    path('<slug:slug>/display/', views.cashier_screen_live, name='counter_display'),
    path('<slug:slug>/<str:bill_number>/', views.checkout, name='checkout'),
    path('<slug:slug>/<str:bill_number>/cash/', views.record_cash, name='record_cash'),
    path('<slug:slug>/<str:bill_number>/upi/', views.confirm_upi, name='confirm_upi'),
    path('<slug:slug>/<str:bill_number>/success/', views.payment_success, name='success'),
    path('<slug:slug>/youpi/webhook/', views.youpi_webhook, name='youpi_webhook'),
    path('<slug:slug>/<str:bill_number>/youpi/test-simulate/', views.test_youpi_sandbox_webhook, name='youpi_test_simulate'),
]
