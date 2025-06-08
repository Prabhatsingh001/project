from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
import uuid
from django.contrib.auth.models import BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_file_size(value):
        limit = 2 * 1024 * 1024  # 2 MB
        if value.size > limit:
            raise ValidationError('File too large. Size should not exceed 2 MiB.')

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email=email, phone_number=phone_number, password=password, **extra_fields)


class CustomUser(AbstractUser):
    """
    custom user model that extends the default Django user model
    """
    username = None
    id = models.UUIDField(_("id"), primary_key = True, editable=False, unique=True, default=uuid.uuid4)
    email = models.EmailField(_("email address"), unique=True)
    phone_number = PhoneNumberField(_("phone number"), null=True, blank=True)
    is_provider = models.BooleanField(_("is verified"), default=False)
    is_verified = models.BooleanField(_("is verified"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']
    objects = CustomUserManager() #type: ignore

    def __str__(self):
        return f"{self.email}"
    

    def save(self, *args, **kwargs):
        """
        Override the save method to ensure the email is always lowercase
        """
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)


class ProviderProfile(models.Model):
    """
    provider profile
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='provider_profile')
    first_name = models.CharField(_("first name"), max_length=30, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True, null=True)
    address = models.CharField(_("address"), max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(_("profile picture"), upload_to='provider_pictures/', blank=True, null=True, validators=[validate_file_size])
    documents = models.FileField(_("documents"), upload_to='provider_documents/', blank=True, null=True, validators=[validate_file_size])

    def __str__(self):
        return f"{self.user.email} - Provider Profile"


class CustomerProfile(models.Model):
    """
    customer profile
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='customer_profile')
    first_name = models.CharField(_("first name"), max_length=30, blank=True, null=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True, null=True)
    address = models.CharField(_("address"), max_length=255, blank=True, null=True)
    profile_picture = models.ImageField(_("profile picture"), upload_to='customer_pictures/', blank=True, null=True, validators=[validate_file_size])

    def __str__(self):
        return f"{self.user.email} - Customer Profile"
    

@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.is_provider:
            ProviderProfile.objects.create(user=instance)
        else:
            CustomerProfile.objects.create(user=instance)
    


class Service(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    provider = models.ForeignKey(ProviderProfile, on_delete=models.CASCADE, related_name='services')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} - {self.provider.first_name}"



class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    schedule = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.schedule < timezone.now():
            raise ValidationError("Booking time must be in the future.")


    def __str__(self):
        return f"Booking by {self.customer.first_name} for {self.service.name}"

