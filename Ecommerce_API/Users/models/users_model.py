from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

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
    
class CustomUser(AbstractUser):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255)
    name = models.CharField(max_length=255)
    phone_number = models.TextField()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'password', 'phone_number']

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['email'], include=['password'], name='unique_email'),
            models.UniqueConstraint(fields=['phone_number'], name='unique_phone_number'),
        ]


    objects = CustomUserManager()

    def __str__(self):
        return self.first_name + ' ' + self.last_name