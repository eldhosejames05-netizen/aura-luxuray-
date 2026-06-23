from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.conf import settings

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
    loyalty_points = models.IntegerField(default=0)

    # Use the custom user manager defined above
    objects = CustomUserManager()

    # Use email as the unique identifier for logging in
    USERNAME_FIELD = 'email'
    # No extra required fields when creating a user via createsuperuser
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    """
    Model representing a detailed user profile.
    """
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Profile for {self.user.email}"


class LoyaltyPoints(models.Model):
    """
    Model representing loyalty points transactions (ledger/history).
    """
    TRANSACTION_TYPES = (
        ('Earned', 'Earned'),
        ('Redeemed', 'Redeemed'),
        ('Refunded', 'Refunded'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loyalty_transactions')
    points = models.IntegerField()  # Positive or negative
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_transactions')
    description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} {self.points} points for {self.user.email}"


class LoyaltySettings(models.Model):
    earning_rate = models.IntegerField(default=1, help_text="Points earned per ₹100 spent.")
    redemption_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Cash value (₹) per 1 point.")
    daily_points_min = models.IntegerField(default=50, help_text="Minimum daily claim login points.")
    daily_points_max = models.IntegerField(default=150, help_text="Maximum daily claim login points.")
    terms_and_conditions = models.TextField(
        default="1. Earn 1 point for every ₹100 spent on paid orders.\n2. Redeem points at checkout (1 point = ₹1 discount).\n3. Claim free points daily.",
        help_text="Custom terms text displayed on the loyalty page."
    )

    class Meta:
        verbose_name = "Loyalty Settings"
        verbose_name_plural = "Loyalty Settings"

    def __str__(self):
        return f"Loyalty Settings (Earning: {self.earning_rate} per ₹100, Redemption: ₹{self.redemption_rate})"

    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(id=1)
        return settings


