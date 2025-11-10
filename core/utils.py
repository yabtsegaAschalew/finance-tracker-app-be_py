import uuid, requests
from rest_framework import status
from rest_framework.response import Response
from finance_tracker.settings import CHAPA_PRIVATE_KEY

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
        "return_url": f"{request.scheme}://{request.get_host()}/api/payment-success/",
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
    
# Verify payment


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
    
