from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorProfile, Appointment, Notification

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Role & Contact', {'fields': ('role', 'phone_number')}),
    )

class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'hospital_name')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization', 'hospital_name')
    list_filter = ('specialization',)

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('patient__username', 'doctor__user__username')

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')

admin.site.register(User, CustomUserAdmin)
admin.site.register(DoctorProfile, DoctorProfileAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Notification, NotificationAdmin)
