from django.db import models
from shared.services.models import TimeStamp
from django.contrib.auth.models import AbstractUser, BaseUserManager
from shipping.models import City

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)
    
class CustomUser(AbstractUser, TimeStamp):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255)
    name = models.CharField(max_length=255)
    phone_number = models.TextField()
    username = None  # This removes the username field
    first_name = None
    last_name = None


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'password', 'phone_number']

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], include=['password'], name='unique_email'),
            models.UniqueConstraint(fields=['phone_number'], name='unique_phone_number'),
        ]


    objects = CustomUserManager()
    
class Address(TimeStamp):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.PROTECT)
    street = models.CharField(max_length=255)
    building_no = models.SmallIntegerField()
    apartment_no = models.SmallIntegerField()
    default = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['user_id', 'id'])
        ]