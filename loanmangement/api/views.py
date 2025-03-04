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
from django.core.cache import cache 
from datetime import datetime,timedelta

User=get_user_model()

class UserRegistration(APIView):
     def post(self,request):
        try:
          serializer=UserSeraializer(data=request.data)
          if serializer.is_valid():
               user = serializer.save()  # ✅ Save the user
               user.is_active = False  # ✅ Set as inactive until OTP verification
               user.save()
               email=request.data.get('email')
               otp=random.randint(100000,999999)
               
               cache.set(f"otp_{email}",{"otp": otp, "user_id": user.id},timeout=300)
               subject='Your One-Time Password (OTP) for Signup'
               message=f'''Dear {request.data.get('username')},

                        Thank you for registering with us! To complete your signup, please use the One-Time Password (OTP) below:

                        Your OTP: {otp}

                        This OTP is valid for 5 minutes. Please do not share this code with anyone for security reasons.

                        If you did not request this, please ignore this email.

                        Best regards,
                        FlashFund'''
               send_mail(subject, message, settings.EMAIL_HOST_USER, [email], fail_silently=True)
               return Response({"status": "success", "message": "OTP sent to your email"}, status=status.HTTP_201_CREATED)
          return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except SMTPException as e:
            return Response({"error": f"SMTP error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class otpverify(APIView):
     def post(self,request):
          email=request.data.get('email')
          otp_entered=request.data.get('otp')
          if not otp_entered or not email:  # Explicitly check if OTP is missing
            return Response({"status": "error", "message": "Email and OTP is required"}, status=status.HTTP_400_BAD_REQUEST)
          
          otp_stored = cache.get(f"otp_{email}")
          try:
             if otp_stored and str(otp_stored["otp"])==str(otp_entered):
                   user = User.objects.get(id=otp_stored["user_id"])
                   user.is_active = True
                   user.save()
                   cache.delete(f"otp_{email}")
                   return Response({"status": "success", "message": "OTP verified,User Registered successfully"}, status=status.HTTP_200_OK)
             else:
                 return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
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
            
    # create a loan 
    def post(self,request):
       
        try:
                data=dict(request.data)
                print(data)
                required_fields = ['amount', 'tenure', 'interest_rate']
                for field in required_fields:
                        if field not in data:
                            return Response({f"error": f"{field} is required."}, status=status.HTTP_400_BAD_REQUEST)
                        
                user = request.user
                if not user or user.is_anonymous:
                    return Response({"error": "Authentication failed. Token required."}, status=status.HTTP_401_UNAUTHORIZED)


                amount= float(data['amount'])
                tenure = int(data['tenure'])
                interest_rate = float(data['interest_rate'])
                # Generate user id
                loan_id = f"LOAN{str(int(datetime.now().timestamp()))[-4:]}" 



                # calculate emi total interest and amount
                emi=monthly_emi(data['amount'],data['tenure'],data['interest_rate'])
                actual_interest=total_interest(data['amount'],data['tenure'],data['interest_rate'])
                total_amount=amount+actual_interest

                loan = Loan_Data.objects.create(
                    user=user,
                    loan_id=loan_id,
                    amount=amount,
                    tenure=tenure,
                    interest_rate=interest_rate,
                    emi=emi,
                    total_interest=actual_interest,
                    total_amount=total_amount,
                    status="ACTIVE"
                )
                
                start_date = datetime.now()
                payment_schedule = [
                    {
                        "installment_no": i + 1,
                        "due_date": (start_date + timedelta(days=30 * (i + 1))).strftime("%Y-%m-%d"),
                        "amount": round(emi, 2)
                    }
                    for i in range(tenure)
                ]
                response_data = {
                    "status": "success",
                    "data": {
                        "loan_id": loan_id,
                        "amount": amount,
                        "tenure": tenure,
                        "interest_rate": f"{interest_rate}% yearly",
                        "monthly_installment": round(emi, 2),
                        "total_interest": round(actual_interest, 2),
                        "total_amount": round(total_amount, 2),
                        "payment_schedule": payment_schedule
                    }
                }
                return Response(response_data,status=status.HTTP_201_CREATED)
        except ValueError as e:
                return Response({"error": f"Invalid input type: {str(e)}. Please check 'amount', 'tenure', and 'interest_rate'."},status=status.HTTP_400_BAD_REQUEST)        

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
                return Response({'status':'success','message':'Loan Deleted Successfully'},status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                 return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
 

class LoanForeclosure(APIView):
    authentication_classes = [JWTAuthentication]  
    permission_classes = [permissions.IsAuthenticated]  

    def post(self, request):
        loan_id = request.data.get("loan_id")  

        if not loan_id:
            return Response({"status": "error", "message": "Loan ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            loan = Loan_Data.objects.get(loan_id=loan_id)  
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