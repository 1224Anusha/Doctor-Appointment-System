from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, AppointmentBookingForm, PatientEditForm, DoctorEditForm
from .models import DoctorProfile, Appointment, Notification, User
from .utils import send_email_notification

def home_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'doctor':
            return redirect('doctor_dashboard')
        elif request.user.role == 'patient':
            return redirect('patient_dashboard')
        elif request.user.role == 'admin' or request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('login')
    return render(request, 'home.html')

def about_view(request):
    return render(request, 'about.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get('role')
            if role == 'doctor':
                DoctorProfile.objects.create(user=user, specialization="Not Specified")
            login(request, user)
            messages.success(request, f"Account created successfully for {user.username}!")
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('home')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have successfully logged out.")
    return redirect('login')

@login_required
def patient_dashboard(request):
    if request.user.role != 'patient':
        return redirect('home')
    appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')
    return render(request, 'dashboards/patient.html', {'appointments': appointments})

@login_required
def doctor_search(request):
    if request.user.role != 'patient':
        return redirect('home')
    query = request.GET.get('q', '')
    specialty = request.GET.get('specialty', '')
    
    doctors = DoctorProfile.objects.all()
    if query:
        doctors = doctors.filter(user__first_name__icontains=query) | doctors.filter(user__last_name__icontains=query)
    if specialty:
        doctors = doctors.filter(specialization__icontains=specialty)
        
    return render(request, 'search/doctors.html', {'doctors': doctors})

@login_required
def book_appointment(request, doctor_id):
    if request.user.role != 'patient':
        return redirect('home')
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    
    if request.method == 'POST':
        form = AppointmentBookingForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.patient = request.user
            appointment.doctor = doctor
            appointment.status = 'pending'
            appointment.save()
            
            # Send Notification to Doctor
            Notification.objects.create(
                user=doctor.user,
                message=f"New appointment request from {request.user.get_full_name()} for {appointment.date} at {appointment.time}."
            )
            
            # Send Email to Patient
            if request.user.email:
                email_subject = "MediConnect: Appointment Request Sent"
                email_body = f"Hello {request.user.get_full_name()},\n\nYour appointment request with Dr. {doctor.user.get_full_name() or doctor.user.username} for {appointment.date} at {appointment.time} has been sent and is pending approval.\n\nThank you,\nMediConnect Team"
                send_email_notification(request.user.email, email_subject, email_body)
            
            messages.success(request, f"Appointment request sent to Dr. {doctor.user.get_full_name()} successfully!")
            return redirect('patient_dashboard')
    else:
        form = AppointmentBookingForm()
        
    return render(request, 'search/book_appointment.html', {'form': form, 'doctor': doctor})

@login_required
def doctor_dashboard(request):
    if request.user.role != 'doctor':
        return redirect('home')
    appointments = Appointment.objects.filter(doctor=request.user.doctor_profile).order_by('-date', '-time')
    return render(request, 'dashboards/doctor.html', {'appointments': appointments})

@login_required
def doctor_profile_update(request):
    if request.user.role != 'doctor':
        return redirect('home')
        
    profile = request.user.doctor_profile
    if request.method == 'POST':
        profile.specialization = request.POST.get('specialization', '')
        profile.hospital_name = request.POST.get('hospital_name', '')
        profile.available_days = request.POST.get('available_days', '')
        profile.available_time = request.POST.get('available_time', '')
        profile.bio = request.POST.get('bio', '')
        profile.save()
        messages.success(request, "Your profile and availability have been updated.")
        return redirect('doctor_dashboard')
        
    return render(request, 'dashboards/doctor_profile.html', {'profile': profile})

@login_required
def update_appointment_status(request, appointment_id, action):
    if request.user.role != 'doctor':
        return redirect('home')
        
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=request.user.doctor_profile)
    
    if action in ['confirm', 'complete', 'cancel']:
        status_map = {'confirm': 'confirmed', 'complete': 'completed', 'cancel': 'cancelled'}
        appointment.status = status_map[action]
        appointment.save()
        
        # Send Notification to Patient
        Notification.objects.create(
            user=appointment.patient,
            message=f"Your appointment with Dr. {request.user.get_full_name()} on {appointment.date} has been {appointment.status}."
        )
        
        # Send Email to Patient
        if appointment.patient.email:
            email_subject = f"MediConnect: Appointment {appointment.status.title()}"
            email_body = f"Hello {appointment.patient.get_full_name()},\n\nYour appointment request with Dr. {request.user.get_full_name() or request.user.username} on {appointment.date} at {appointment.time} has been {appointment.status}.\n\nThank you,\nMediConnect Team"
            send_email_notification(appointment.patient.email, email_subject, email_body)
        
        messages.success(request, f"Appointment status updated to {appointment.status}.")
        
        
    return redirect('doctor_dashboard')

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    context = {
        'total_patients': User.objects.filter(role='patient').count(),
        'total_doctors': DoctorProfile.objects.count(),
        'total_appointments': Appointment.objects.count(),
        'recent_appointments': Appointment.objects.all().order_by('-created_at')[:10],
        'users': User.objects.all().exclude(id=request.user.id)[:10]
    }
    
    return render(request, 'dashboards/admin.html', context)

@login_required
def admin_manage_patients(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    patients = User.objects.filter(role='patient').order_by('-date_joined')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            patient_id = request.POST.get('patient_id')
            patient = get_object_or_404(User, id=patient_id, role='patient')
            patient_name = patient.username
            patient.delete()
            messages.success(request, f"Patient {patient_name} was deleted along with their appointments.")
            return redirect('admin_manage_patients')
            
    return render(request, 'admin/patients.html', {'patients': patients})

@login_required
def admin_manage_doctors(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    doctors = DoctorProfile.objects.all().select_related('user').order_by('-user__date_joined')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            doctor_id = request.POST.get('doctor_id')
            doctor_profile = get_object_or_404(DoctorProfile, id=doctor_id)
            doctor_user = doctor_profile.user
            doctor_name = doctor_user.get_full_name() or doctor_user.username
            
            # Deleting the user will cascade and delete the DoctorProfile and their Appointments
            doctor_user.delete()
            messages.success(request, f"Doctor {doctor_name} was deleted along with their profile and appointments.")
            return redirect('admin_manage_doctors')
            
    return render(request, 'admin/doctors.html', {'doctors': doctors})

@login_required
def admin_manage_appointments(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    appointments = Appointment.objects.all().order_by('-date', '-time')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            apt_id = request.POST.get('appointment_id')
            apt = get_object_or_404(Appointment, id=apt_id)
            apt.delete()
            messages.success(request, "Appointment record deleted from the system.")
            return redirect('admin_manage_appointments')
            
    return render(request, 'admin/appointments.html', {'appointments': appointments})

@login_required
def admin_edit_patient(request, patient_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    patient = get_object_or_404(User, id=patient_id, role='patient')
    
    if request.method == 'POST':
        form = PatientEditForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f"Patient {patient.get_full_name() or patient.username} details updated successfully.")
            return redirect('admin_manage_patients')
    else:
        form = PatientEditForm(instance=patient)
        
    return render(request, 'admin/edit_patient.html', {'form': form, 'patient': patient})

@login_required
def admin_edit_doctor(request, doctor_id):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    doctor_profile = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor_user = doctor_profile.user
    
    if request.method == 'POST':
        user_form = DoctorEditForm(request.POST, instance=doctor_user)
        if user_form.is_valid():
            user_form.save()
            
            # Save related profile data manually since it's a separate model
            doctor_profile.specialization = request.POST.get('specialization', doctor_profile.specialization)
            doctor_profile.hospital_name = request.POST.get('hospital_name', doctor_profile.hospital_name)
            doctor_profile.available_days = request.POST.get('available_days', doctor_profile.available_days)
            doctor_profile.available_time = request.POST.get('available_time', doctor_profile.available_time)
            doctor_profile.bio = request.POST.get('bio', doctor_profile.bio)
            doctor_profile.save()
            
            messages.success(request, f"Doctor {doctor_user.get_full_name() or doctor_user.username} details updated successfully.")
            return redirect('admin_manage_doctors')
    else:
        user_form = DoctorEditForm(instance=doctor_user)
        
    return render(request, 'admin/edit_doctor.html', {'user_form': user_form, 'profile': doctor_profile})

import csv
from django.http import HttpResponse

@login_required
def admin_reports(request):
    if request.user.role != 'admin' and not request.user.is_superuser:
        return redirect('home')
        
    if request.method == 'POST' and request.POST.get('action') == 'export_appointments':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="appointments_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID', 'Patient Name', 'Doctor Name', 'Doctor Specialization', 'Date', 'Time', 'Status', 'Booking Notes'])
        
        appointments = Appointment.objects.all().order_by('-date')
        for apt in appointments:
            writer.writerow([
                apt.id,
                apt.patient.get_full_name() or apt.patient.username,
                f"Dr. {apt.doctor.user.get_full_name() or apt.doctor.user.username}",
                apt.doctor.specialization,
                apt.date,
                apt.time,
                apt.status,
                apt.notes
            ])
            
        return response
        
    # Stats for the reports dashboard itself
    context = {
        'total_users': User.objects.count(),
        'pending_appointments': Appointment.objects.filter(status='pending').count(),
        'completed_appointments': Appointment.objects.filter(status='completed').count(),
        'cancelled_appointments': Appointment.objects.filter(status='cancelled').count(),
    }
            
    return render(request, 'admin/reports.html', context)
