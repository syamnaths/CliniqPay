from django.urls import path
from billing import views

app_name = 'billing'

urlpatterns = [
    path('<slug:slug>/', views.cashier_counter, name='counter'),
    path('<slug:slug>/pharmacy/', views.pharmacy_counter, name='pharmacy_counter'),
    path('<slug:slug>/pharmacy/csv/download/', views.download_pharmacy_batch_csv_sample, name='download_pharmacy_batch_csv_sample'),
    path('<slug:slug>/pharmacy/csv/upload/', views.upload_pharmacy_batch_csv, name='upload_pharmacy_batch_csv'),
    path('<slug:slug>/create/', views.create_bill, name='create_bill'),
    path('<slug:slug>/patient/save/', views.save_patient_ajax, name='save_patient_ajax'),
    path('<slug:slug>/api/search-patients/', views.search_patients_api, name='search_patients_api'),
    path('<slug:slug>/api/patient-summary/<int:patient_id>/', views.patient_inpatient_summary_api, name='patient_summary_api'),
    path('<slug:slug>/patient/<int:patient_id>/discharge/', views.discharge_patient, name='discharge_patient'),
    path('<slug:slug>/bill/<str:bill_number>/', views.bill_detail, name='detail'),
]
