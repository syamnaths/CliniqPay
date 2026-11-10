from django.urls import path
from enrollment import views

app_name = 'enrollment'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('submit/', views.submit_enrollment, name='submit'),
    path('status/<uuid:token>/', views.track_status, name='status'),
]
