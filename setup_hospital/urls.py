from django.urls import path
from setup_hospital import views

app_name = 'setup_hospital'

urlpatterns = [
    path('<slug:slug>/', views.dashboard, name='dashboard'),
    path('<slug:slug>/login/', views.hospital_login, name='login'),
    path('<slug:slug>/logout/', views.hospital_logout, name='logout'),
    path('<slug:slug>/profile/', views.user_profile, name='user_profile'),
    path('<slug:slug>/profile/update/', views.update_profile, name='update_profile'),
    path('<slug:slug>/services/add/', views.add_service, name='add_service'),
    path('<slug:slug>/services/csv/download/', views.download_services_csv_sample, name='download_services_csv_sample'),
    path('<slug:slug>/services/csv/upload/', views.upload_services_csv, name='upload_services_csv'),
    path('<slug:slug>/services/<int:service_id>/edit/', views.edit_service, name='edit_service'),
    path('<slug:slug>/services/<int:service_id>/delete/', views.delete_service, name='delete_service'),
    path('<slug:slug>/doctors/add/', views.add_doctor, name='add_doctor'),
    path('<slug:slug>/doctors/<int:doctor_id>/edit/', views.edit_doctor, name='edit_doctor'),
    path('<slug:slug>/doctors/<int:doctor_id>/delete/', views.delete_doctor, name='delete_doctor'),
    path('<slug:slug>/doctor/', views.doctor_portal, name='doctor_portal'),
    path('<slug:slug>/doctor/prescription/create/', views.create_prescription, name='create_prescription'),
    path('<slug:slug>/doctor/notes/save/', views.save_clinical_note_ajax, name='save_clinical_note_ajax'),
    path('<slug:slug>/doctor/queue/update-status/', views.update_queue_status_ajax, name='update_queue_status_ajax'),
    path('<slug:slug>/doctor/queue/poll/', views.doctor_queue_poll_ajax, name='doctor_queue_poll_ajax'),
    path('<slug:slug>/prescription/<str:rx_number>/', views.prescription_detail, name='prescription_detail'),
    path('<slug:slug>/prescription/<str:rx_number>/send-whatsapp/', views.dispatch_prescription_whatsapp, name='dispatch_prescription_whatsapp'),
    path('<slug:slug>/staff/add/', views.add_staff, name='add_staff'),
    path('<slug:slug>/staff/<int:staff_id>/edit/', views.edit_staff, name='edit_staff'),
    path('<slug:slug>/staff/reset-password/', views.reset_staff_password, name='reset_staff_password'),
    path('<slug:slug>/housekeeping/', views.housekeeping_dashboard, name='housekeeping_dashboard'),
    path('<slug:slug>/housekeeping/mark-ready/', views.mark_room_ready, name='mark_room_ready'),
    path('<slug:slug>/cadres/add/', views.add_ward_cadre, name='add_ward_cadre'),
    path('<slug:slug>/cadres/<int:cadre_id>/delete/', views.delete_ward_cadre, name='delete_ward_cadre'),
    path('<slug:slug>/support/', views.hospital_support, name='support'),
    path('<slug:slug>/support/<str:ticket_number>/', views.hospital_ticket_detail, name='ticket_detail'),
    path('<slug:slug>/help/', views.hospital_help_guide, name='help_guide'),
]
