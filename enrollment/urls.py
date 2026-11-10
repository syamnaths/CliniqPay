from django.urls import path
from enrollment import views

app_name = 'enrollment'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('submit/', views.submit_enrollment, name='submit'),
    path('status/<uuid:token>/', views.track_status, name='status'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('security/', views.security_whitepaper, name='security_whitepaper'),
    path('status/', views.system_status, name='system_status'),
]
