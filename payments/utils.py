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
    Verify a Flutterwave payment status by tx_ref
    """
    from .models import Payment
    from django.utils import timezone
    
    try:
        payment = Payment.objects.get(tx_ref=tx_ref)
    except Payment.DoesNotExist:
        raise Exception("Payment not found")
    
    # Flutterwave API: Query transactions by tx_ref
    url = "https://api.flutterwave.com/v3/transactions"
    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "tx_ref": tx_ref
    }
    
    try:
        # Get transaction by tx_ref
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print(f"Flutterwave response for tx_ref {tx_ref}: {data}")
        
        if data.get('status') == 'success':
            transaction_list = data.get('data', [])
            
            # If transaction data is empty, the transaction might not be available yet
            # This can happen immediately after payment - Flutterwave needs a moment to process
            if not transaction_list or len(transaction_list) == 0:
                # Transaction not found yet - might still be processing
                # Return the payment as-is (status will remain pending)
                # The webhook will update it when Flutterwave processes it
                raise Exception("Transaction not yet available in Flutterwave. Please wait a moment and refresh, or check your payment status later.")
            
            # Get the first transaction (should only be one for a tx_ref)
            transaction_data = transaction_list[0] if isinstance(transaction_list, list) else transaction_list
            
            # Update payment with transaction data
            payment.flw_ref = transaction_data.get('flw_ref', '')
            payment.transaction_id = str(transaction_data.get('id', ''))
            payment.webhook_data = transaction_data
            
            # Check transaction status
            transaction_status = transaction_data.get('status', '').lower()
            
            if transaction_status == 'successful':
                payment.status = 'successful'
                if transaction_data.get('created_at'):
                    try:
                        from datetime import datetime
                        date_str = transaction_data.get('created_at')
                        # Handle different date formats
                        if 'T' in date_str:
                            payment.paid_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            payment.paid_at = timezone.now()
                    except Exception:
                        payment.paid_at = timezone.now()
                if transaction_data.get('payment_type'):
                    payment.payment_method = transaction_data.get('payment_type', '').lower()
            elif transaction_status in ['failed', 'cancelled']:
                payment.status = 'failed'
                payment.failure_reason = transaction_data.get('processor_response', f'Payment {transaction_status}')
            else:
                # Still processing
                payment.status = 'processing'
            
            payment.save()
            return payment
        else:
            error_msg = data.get('message', 'Transaction not found')
            payment.status = 'failed'
            payment.failure_reason = error_msg
            payment.save()
            raise Exception(error_msg)
    except requests.RequestException as e:
        error_msg = str(e)
        payment.status = 'failed'
        payment.failure_reason = error_msg
        payment.save()
        print(f"Request error: {error_msg}")
        raise Exception(f"Failed to verify payment: {error_msg}")


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

