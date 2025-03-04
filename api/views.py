from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status , permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User ,Loan_Data
from  .serializer import UserSeraializer , LoanSerailizer
from decimal import Decimal
from django.contrib.auth import get_user_model
import random
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException


User=get_user_model

class UserRegistration(APIView):
     def post(self,request):
        try:
          serializer=UserSeraializer(data=request.data)
          if serializer.is_valid():
               otp=random.randint(100000,999999)
               user = serializer.save(otp=otp, is_active=False)
               subject='Your One-Time Password (OTP) for Signup'
               message=f'''Dear {request.data.get('username')},

                        Thank you for registering with us! To complete your signup, please use the One-Time Password (OTP) below:

                        Your OTP: {otp}

                        This OTP is valid for 5 minutes. Please do not share this code with anyone for security reasons.

                        If you did not request this, please ignore this email.

                        Best regards,
                        FlashFund'''
               send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email], fail_silently=True)
               return Response({"status": "success", "message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)
        except SMTPException as e:
            return Response({"error": f"SMTP error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class otpverify(APIView):
     def post(self,request):
          email=request.data.get('email')
          otp=request.data.get('otp')
          try:
               user=User.objects.get(email=email,otp=otp)
               user.is_active=True
               user.otp = None  # Clear the OTP
               user.save()
               return Response({"status": "success", "message": "OTP verified successfully"}, status=status.HTTP_200_OK)
          except User.DoesNotExist:
             return Response({"status": "error", "message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)




# monthly_emi_calculation
def monthly_emi(loan_amount,tenure,interestrate):
      monthly_intereset_rate=(interestrate/100)/12
      emi=loan_amount*monthly_intereset_rate*((1+monthly_intereset_rate)**tenure)/(((1+monthly_intereset_rate)**tenure)-1)
      return round(emi,2)
# total interest calculation
def total_interest(loan_amount,tenure,interestrate):
    emi=monthly_emi(loan_amount,tenure,interestrate)
    total_amount=emi*tenure
    tot_interset=total_amount-loan_amount
    return round(tot_interset,2)

class LoanListCreate(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[permissions.IsAuthenticated]

    # all loans viewing for admin and if logged in  is user he can view his loandetail
    def get(self,request):
                
            try:
                if request.user.role=='admin':
                    loans=Loan_Data.objects.all()
                else:
                    loans=Loan_Data.objects.filter(user=request.user)
                serializer=LoanSerailizer(loans,many=True)
                return Response(serializer.data)
            except Exception as e:
                return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

    def post(self,request):
       
        try:
                data=request.data
                data['user']=request.user.id
                data['emi']=monthly_emi(float(data['amount']),int('tenure'),float('interest_rate'))
                data['total_interest']=total_interest(float(data['amount']),int('tenure'),float('interest_rate'))
                data['total_amount']=float(data['amount'])+float( data['total_interest'])
                serializer=LoanSerailizer(data=data)

                if serializer.is_valid:
                    serializer.save()
                    return Response(serializer.data,status=status.HTTP_201_CREATED)
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
             return Response({"error": "Invalid input type. Please check 'amount', 'tenure', and 'interest_rate'."},
                            status=status.HTTP_400_BAD_REQUEST)
        

class LoanDetailView(APIView):
    authentication_classes = [JWTAuthentication]  
    permission_classes = [permissions.IsAuthenticated] 

    def get_object(self, pk):
            try:
                return Loan_Data.objects.get(pk=pk)  
            except Loan_Data.DoesNotExist:
                return None 
            
    def get(self, request, pk):
            try:
                loan = self.get_object(pk)  
                if loan is None:  # If the loan doesn't exist
                    return Response({"status": "error", "message": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)
                if request.user.role != 'admin' and loan.user != request.user:  # Check if the user is not an admin and doesn't own the loan
                    return Response({"status": "error", "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)  
                serializer = LoanSerailizer(loan)  
                return Response(serializer.data)  
            except Exception as e:
                 return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

    def delete(self,request,pk):
            try:
                loan=self.get_object(pk)
                if loan is None:
                    return Response({'status':'error','message':'Loan Not Found'},status=status.HTTP_404_NOT_FOUND)
                if request.user.role != 'admin':
                    return Response({'status':'error','message':'Permission Denied'},status=status.HTTP_403_FORBIDDEN)
                loan.delete()
                return Response({'status':'error','message':'Loan Deleted Successfully'},status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                 return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

class LoanForeclosure(APIView):
    authentication_classes = [JWTAuthentication]  
    permission_classes = [permissions.IsAuthenticated]  

    def post(self, request, pk):
        try:
            loan = Loan_Data.objects.get(pk=pk)  
        except Loan_Data.DoesNotExist:  
            return Response({"status": "error", "message": "Loan not found"}, status=status.HTTP_404_NOT_FOUND)  
        
        if loan.status != 'ACTIVE':  
            return Response({"status": "error", "message": "Loan is not active"}, status=status.HTTP_400_BAD_REQUEST) 
        if request.user.role != 'admin' and loan.user != request.user:  
            return Response({"status": "error", "message": "Permission denied"}, status=status.HTTP_403_FORBIDDEN) 

        total_paid = loan.emi * loan.tenure  # Calculate the total amount paid 
        foreclosure_discount = total_interest(loan.amount, loan.tenure, loan.interest_rate) / 2  
        final_settlement = total_paid - foreclosure_discount  

        loan.status = 'CLOSED'  
        loan.save()  

        return Response({ 
            "status": "success",
            "message": "Loan foreclosed successfully",
            "data": {
                "loan_id": loan.loan_id,
                "amount_paid": total_paid,
                "foreclosure_discount": foreclosure_discount,
                "final_settlement_amount": final_settlement,
                "status": loan.status,
            }
        })