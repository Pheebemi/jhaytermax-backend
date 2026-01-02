import hashlib
import hmac
import json
import requests
from django.conf import settings


def generate_tx_ref(order_id):
    """Generate a unique transaction reference for Flutterwave"""
    import uuid
    return f"JHYTERMAX-{order_id}-{uuid.uuid4().hex[:8].upper()}"


def initiate_flutterwave_payment(order, customer_email, customer_name, customer_phone=None, payment_method=None):
    """
    Initiate a Flutterwave payment and return the payment link
    """
    from .models import Payment
    
    tx_ref = generate_tx_ref(order.id)
    
    # Create payment record
    payment = Payment.objects.create(
        order=order,
        user=order.buyer,
        amount=order.total_amount,
        currency=settings.FLUTTERWAVE_CURRENCY,
        tx_ref=tx_ref,
        customer_email=customer_email,
        customer_name=customer_name,
        customer_phone=customer_phone or '',
        payment_method=payment_method or '',
        status='pending',
    )
    
    # Prepare Flutterwave API request
    url = "https://api.flutterwave.com/v3/payments"
    if settings.FLUTTERWAVE_SANDBOX:
        url = "https://api.flutterwave.com/v3/payments"  # Sandbox uses same URL
    
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "tx_ref": tx_ref,
        "amount": str(float(order.total_amount)),
        "currency": settings.FLUTTERWAVE_CURRENCY,
        "redirect_url": settings.FLUTTERWAVE_REDIRECT_URL,
        "payment_options": "card,banktransfer,ussd,mobilemoney",
        "customer": {
            "email": customer_email,
            "name": customer_name,
            "phone_number": customer_phone or "",
        },
        "customizations": {
            "title": "Jhytermax Order Payment",
            "description": f"Payment for order {order.order_id}",
            "logo": "",  # Add logo URL if available
        },
        "meta": {
            "order_id": order.id,
            "order_ref": order.order_id,
        },
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            payment_link = data['data']['link']
            return payment, payment_link
        else:
            payment.status = 'failed'
            payment.failure_reason = data.get('message', 'Payment initiation failed')
            payment.save()
            raise Exception(data.get('message', 'Payment initiation failed'))
    except requests.RequestException as e:
        payment.status = 'failed'
        payment.failure_reason = str(e)
        payment.save()
        raise Exception(f"Failed to initiate payment: {str(e)}")


def verify_flutterwave_payment(tx_ref):
    """
    Verify a Flutterwave payment status
    """
    from .models import Payment
    
    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        raise Exception("Payment not found")
    
    url = f"https://api.flutterwave.com/v3/transactions/{tx_ref}/verify"
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'success':
            transaction_data = data['data']
            
            payment.flw_ref = transaction_data.get('flw_ref', '')
            payment.transaction_id = transaction_data.get('id', '')
            payment.webhook_data = transaction_data
            
            if transaction_data.get('status') == 'successful':
                payment.status = 'successful'
                payment.paid_at = transaction_data.get('created_at')
                if transaction_data.get('payment_type'):
                    payment.payment_method = transaction_data.get('payment_type', '').lower()
            else:
                payment.status = 'failed'
                payment.failure_reason = transaction_data.get('processor_response', 'Payment failed')
            
            payment.save()
            return payment
        else:
            payment.status = 'failed'
            payment.failure_reason = data.get('message', 'Verification failed')
            payment.save()
            raise Exception(data.get('message', 'Verification failed'))
    except requests.RequestException as e:
        payment.status = 'failed'
        payment.failure_reason = str(e)
        payment.save()
        raise Exception(f"Failed to verify payment: {str(e)}")


def verify_webhook_signature(secret_hash, payload, signature):
    """
    Verify Flutterwave webhook signature
    """
    if not secret_hash:
        return False
    
    expected_signature = hmac.new(
        secret_hash.encode('utf-8'),
        json.dumps(payload, separators=(',', ':')).encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

