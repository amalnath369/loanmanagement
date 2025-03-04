from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
      role_choice=(('admin','Admin'),('user','user'))
      role=models.CharField(max_length=10,choices=role_choice,default='user')
      email=models.EmailField(max_length=255,unique=True)
      otp=models.IntegerField(max_length=6,null=True,blank=False)
      is_active=models.BooleanField(default=False)

      def __str__(self):
           return self.username

class Loan_Data(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    loan_id = models.CharField(max_length=20, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    tenure = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    emi = models.DecimalField(max_digits=10, decimal_places=2)
    total_interest = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loan_id