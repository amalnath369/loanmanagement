Loan Management System REST API - Django

Objective

The Loan Management System is a Django-based REST API designed to manage loans with user-defined monthly compound interest. It provides role-based authentication, automatic interest calculations, and loan repayment schedules. Users can also foreclose loans before tenure completion with adjusted interest calculations.

Tech Stack

Backend: Django, Django REST Framework (DRF)

Authentication: JWT (Simple JWT)

OTP Email Service: Django inbuilt mail is provided

Database: PostgreSQL (Preferred) or MongoDB (Optional with Djongo)

Deployment: Render (Free Tier)

Features & Requirements

1. Authentication & Role-Based Access Control

Implement JWT authentication using Simple JWT.

Support two user roles: Admin & User.

Register users with OTP email verification.

Each API call must include a valid JWT token in the request header.

Determine role (Admin/User) from token and allow/restrict access accordingly.

2. Core Loan Features

Users can:

Add a new loan by specifying the amount, tenure, and interest rate.

View their active and past loans.

View loan details with monthly installments and interest breakdown.

Foreclose a loan before tenure completion (adjusted interest calculations apply).

Admins can:

View all loans in the system.

View all user loan details.

Delete loan records.

3. Loan Calculation

User-defined yearly compound interest.

Monthly installments and total payable amount are calculated automatically.

Foreclosure allows users to pay off the loan early with adjusted interest.

The system stores total amount payable, interest amount, and payment schedules.

API Endpoints & Examples

1. Add Loan

Endpoint: POST /api/loans/

Request:

{
    "amount": 10000,
    "tenure": 12,
    "interest_rate": 10
}

Response:

{
    "status": "success",
    "data": {
        "loan_id": "LOAN001",
        "amount": 10000,
        "tenure": 12,
        "interest_rate": "10% yearly",
        "monthly_installment": 879.16,
        "total_interest": 1549.92,
        "total_amount": 11549.92,
        "payment_schedule": [
            {
                "installment_no": 1,
                "due_date": "2024-03-24",
                "amount": 879.16
            }
        ]
    }
}

2. List Loans

Endpoint: GET /api/loans/

Response:

{
    "status": "success",
    "data": {
        "loans": [
            {
                "loan_id": "LOAN001",
                "amount": 10000,
                "tenure": 12,
                "monthly_installment": 879.16,
                "total_amount": 11549.92,
                "amount_paid": 1758.32,
                "amount_remaining": 9791.60,
                "next_due_date": "2024-04-24",
                "status": "ACTIVE",
                "created_at": "2024-02-24T10:30:00Z"
            }
        ]
    }
}

3. Loan Foreclosure

Endpoint: POST /api/loans/{loan_id}/foreclose/

Request:

{
    "loan_id": "LOAN001"
}

Response:

{
    "status": "success",
    "message": "Loan foreclosed successfully.",
    "data": {
        "loan_id": "LOAN001",
        "amount_paid": 11000.00,
        "foreclosure_discount": 500.00,
        "final_settlement_amount": 10500.00,
        "status": "CLOSED"
    }
}



Validation Rules

Amount Validation

Minimum: ₹1,000

Maximum: ₹100,000

Must be a number

Tenure Validation

Minimum: 3 months

Maximum: 24 months

Must be a whole number

Interest Calculation Example

For a loan of ₹10,000 for 12 months at 10% yearly compound interest:

Yearly Interest Rate: 10%

Monthly Interest Rate: 0.833% (10% ÷ 12)

Total Interest: ₹1,549.92

Total Amount: ₹11,549.92

Monthly Installment: ₹879.16


