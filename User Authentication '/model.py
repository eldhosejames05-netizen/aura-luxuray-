from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
# Custom User Manager to handle user creation using email instead of username
class CustomUserManager(BaseUserManager):
    """
    Custom manager for Custom User model where email is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)
# Custom User Model
class User(AbstractUser):
    """
    Custom user model representing user accounts in the e-commerce system.
    Authentication is done via email, and the username field is removed.
    """
    username = None  # Remove username field
    email = models.EmailField(unique=True)  # Make email field unique and required
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    # Use the custom user manager defined above
    objects = CustomUserManager()
    # Use email as the unique identifier for logging in
    USERNAME_FIELD = 'email'
    # No extra required fields when creating a user via createsuperuser
    REQUIRED_FIELDS = []
    def __str__(self):
        return self.email
