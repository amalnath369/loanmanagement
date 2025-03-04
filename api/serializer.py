from rest_framework import serializers
from .models import User , Loan_Data

class UserSeraializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True)
    class Meta:
        model=User
        fields=['id','username','email','password','role']

    def create(self,validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data.get('role', 'USER')
        )
        return user

class LoanSerailizer(serializers.ModelSerializer):
    class Meta:
        model=Loan_Data
        fields='__all__'
    
