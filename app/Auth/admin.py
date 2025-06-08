from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, CustomerProfile, ProviderProfile, Service, Booking


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('id', 'email', 'phone_number', 'is_staff', 'is_active', 'is_verified')
    search_fields = ('email', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at') 

    fieldsets = (
        (None, {'fields': ('email', 'phone_number', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Verification', {'fields': ('is_verified',)}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone_number', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )


admin.site.register(CustomerProfile)
admin.site.register(ProviderProfile)
admin.site.register(Service)
admin.site.register(Booking)