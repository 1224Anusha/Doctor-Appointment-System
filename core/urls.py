from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Placeholder for dashboards
    # Dashboard
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    # Admin Features
    path('dashboard/admin/patients/', views.admin_manage_patients, name='admin_manage_patients'),
    path('dashboard/admin/patients/edit/<int:patient_id>/', views.admin_edit_patient, name='admin_edit_patient'),
    path('dashboard/admin/doctors/', views.admin_manage_doctors, name='admin_manage_doctors'),
    path('dashboard/admin/doctors/edit/<int:doctor_id>/', views.admin_edit_doctor, name='admin_edit_doctor'),
    path('dashboard/admin/appointments/', views.admin_manage_appointments, name='admin_manage_appointments'),
    path('dashboard/admin/reports/', views.admin_reports, name='admin_reports'),

    # Patient Features
    path('doctors/', views.doctor_search, name='doctor_search'),
    path('book/<int:doctor_id>/', views.book_appointment, name='book_appointment'),

    # Doctor Features
    path('doctor/profile/', views.doctor_profile_update, name='doctor_profile_update'),
    path('appointment/<int:appointment_id>/<str:action>/', views.update_appointment_status, name='update_appointment_status'),
]
