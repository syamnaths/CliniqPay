from django.urls import path
from platform_admin import views

app_name = 'platform_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    path('approve/<int:pk>/', views.approve_request, name='approve'),
    path('reject/<int:pk>/', views.reject_request, name='reject'),
    path('edit-enrollment/<int:pk>/', views.edit_enrollment, name='edit_enrollment'),
    path('reset-password/<int:pk>/', views.reset_hospital_password, name='reset_password'),
    path('support/', views.support_dashboard, name='support_dashboard'),
    path('support/<str:ticket_number>/', views.support_ticket_resolve, name='support_ticket_resolve'),
]
