import requests
from rest_framework import status
from rest_framework.response import Response
from finance_tracker.settings import CHAPA_PRIVATE_KEY
from core.models import Budget, Transaction

url = "https://api.chapa.co/v1"
private_key = CHAPA_PRIVATE_KEY

def payment_gateway(amount, email, first_name, last_name, request, phone_number, tx_ref):
    api_url = f"{url}/transaction/initialize"
    

    payload = {
        "amount": str(amount),
        "currency": "ETB",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "tx_ref": tx_ref,
        "phone_number": phone_number,
        "callback_url": f"{request.scheme}://{request.get_host()}/api/chapa/callback/",
        "return_url": "http://localhost:8080/payment-success",
        "customization": {
            "title": "Let us do this",
            "description": "Paying with Confidence with Chapa",
        },
    }

    headers = {
        "Authorization": f"Bearer {private_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers)

        if not response.text.strip():
            return Response(
                {"error": "Empty response from Chapa"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            checkout_url = data["data"]["checkout_url"]

            return Response(
                {
                    "checkout_url": checkout_url, 
                    "tx_ref": tx_ref, 
                    "amount": amount,
                    "status": data.get("status")
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "error": data,
                "status": data.get("status")
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    



def verify_payment(tx_ref):
    api_url = f"{url}/transaction/verify/{tx_ref}"
    payload = ''
    headers = {
        'Authorization': f'Bearer {private_key}'
    }
    response = requests.get(api_url, headers=headers, data=payload)
    data = response.text
    print(data)
    return Response(data)

def calculate_user_payment(user_id, payment_done=False, tx_ref=None):

    budgets = Budget.objects.filter(user_id=user_id).select_related(
        "category", "transaction"
    )

    total_income = sum(b.amount for b in budgets if b.category.type == "income")
    total_expenses = sum(b.amount for b in budgets if b.category.type == "expense")

    amount_to_pay = total_expenses
    remaining_budget = total_income - total_expenses

    if not payment_done:
        return {
            "amount_to_pay": amount_to_pay,
            "status": "pending_payment",
            "remaining_budget": remaining_budget
        }

    if payment_done:
        with transaction.atomic():
            
            tx = Transaction.objects.filter(tx_ref=tx_ref, user_id=user_id).first()

            if not tx:
                return {"error": "Transaction not found."}

            
            for b in budgets.filter(category__type="expense"):
                b.transaction = tx
                b.save()

            
            for b in budgets.filter(category__type="income"):
                b.amount = remaining_budget if remaining_budget > 0 else 0
                b.save()

        return {
            "amount_to_pay": amount_to_pay,
            "status": "payment_done",
            "remaining_budget": remaining_budget,
            "transaction_ref": tx_ref
        }
    
    
def bank_transfer(account_number, amount, tx_ref, bank_code):
    api_url = f"{url}/transfers"

    payload = {
        "account_number": account_number,
        "amount": amount,
        "currency": "ETB",
        "reference": tx_ref,
        "bank_code": bank_code
    }

    headers = {
        'Authorization': f'Bearer {private_key}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)

        if not response.text.strip():
            return Response(
                {"error": "Empty response from chapa"},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        data = response.json()

        if response.status_code == 200 and data.get("status") == "success":
            message = data["message"]
            transaction_ref = data["data"]
            return Response(
                {
                    "message": message,
                    "tx_ref": transaction_ref,
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {
                    "error": data,
                    "status": data.get("status")
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception as e:
        return Response(
            {
                "error": str(e),
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR
            }
        )
    
def get_bank():

    api_url = f"{url}/banks"
    payload = ''
    headers = {
        'Authorization': f'Bearer {private_key}'
    }

    response = requests.get(api_url, headers=headers, data=payload)
    data = response.json()

    return Response(
        {
            "data": data
        }
    )

def initiate_payment(tx_ref, phone_number=None):   

    api_url = f"{url}/charges?type=telebirr"
    dataList = []
    boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
    dataList.append('--' + boundary)
    dataList.append('Content-Disposition: form-data; name="amount"')
    dataList.append('')
    dataList.append('10')

    dataList.append('--' + boundary)
    dataList.append('Content-Disposition: form-data; name="currency"')
    dataList.append('')
    dataList.append('ETB')

    dataList.append('--' + boundary)
    dataList.append('Content-Disposition: form-data; name="tx_ref"')
    dataList.append('')
    dataList.append(tx_ref)

    dataList.append('--' + boundary)
    dataList.append('Content-Disposition: form-data; name="mobile"')
    dataList.append('')
    dataList.append('0900123456' if phone_number == None else phone_number)

    dataList.append('--' + boundary + '--')
    dataList.append('')
    body = '\r\n'.join(dataList)
    payload = body.encode('utf-8')
    headers = {
        'Authorization': 'Bearer CHASECK_TEST-mgWrd2rhogka8FINIdgfl7wM2Yo1mpwL',
        'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }

    response = requests.post(api_url, data=payload, headers=headers)
    data = response.json()

    return data

    
