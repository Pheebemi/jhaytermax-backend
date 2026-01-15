from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

from .models import Payment
from .serializers import PaymentSerializer, PaymentInitiateSerializer
from .utils import initiate_flutterwave_payment, verify_flutterwave_payment, verify_webhook_signature


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.is_staff or user.is_superuser:
            return Payment.objects.select_related('order', 'user').all()
        return Payment.objects.select_related('order', 'user').filter(user=user)

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        # Log incoming data for debugging
        import json
        print(f"Payment initiate request data: {json.dumps(request.data)}")
        print(f"Request data type: {type(request.data)}")
        print(f"order_id in request.data: {'order_id' in request.data}")
        if 'order_id' in request.data:
            print(f"order_id value: {request.data.get('order_id')}, type: {type(request.data.get('order_id'))}")
        
        serializer = PaymentInitiateSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        from orders.models import Order
        
        order_id = serializer.validated_data['order_id']
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            payment, payment_link = initiate_flutterwave_payment(
                order=order,
                customer_email=serializer.validated_data['customer_email'],
                customer_name=serializer.validated_data['customer_name'],
                customer_phone=serializer.validated_data.get('customer_phone') or None,
                payment_method=serializer.validated_data.get('payment_method') or None,
            )
            
            return Response({
                'payment_id': payment.id,
                'payment_link': payment_link,
                'tx_ref': payment.tx_ref,
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def verify(self, request):
        tx_ref = request.data.get('tx_ref')
        if not tx_ref:
            return Response({'error': 'tx_ref is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = verify_flutterwave_payment(tx_ref)
            serializer = self.get_serializer(payment)
            return Response(serializer.data)
        except Exception as e:
            error_msg = str(e)
            # If transaction not available yet, return 202 (Accepted) instead of 400
            if "not yet available" in error_msg.lower():
                return Response({
                    'error': error_msg,
                    'status': 'pending',
                    'message': 'Transaction is being processed. Please check again in a moment.'
                }, status=status.HTTP_202_ACCEPTED)
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
@permission_classes([])
def flutterwave_webhook(request):
    """
    Handle Flutterwave webhook notifications
    """
    try:
        signature = request.headers.get('verif-hash', '')
        payload = json.loads(request.body)
        
        # Verify webhook signature if secret hash is configured
        if settings.FLUTTERWAVE_SECRET_HASH:
            if not verify_webhook_signature(settings.FLUTTERWAVE_SECRET_HASH, payload, signature):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Process webhook
        event = payload.get('event')
        data = payload.get('data', {})
        
        if event == 'charge.completed':
            tx_ref = data.get('tx_ref')
            if tx_ref:
                try:
                    payment = Payment.objects.select_related('order').get(tx_ref=tx_ref)
                    payment.webhook_data = payload
                    
                    if data.get('status') == 'successful':
                        payment.status = 'successful'
                        payment.flw_ref = data.get('flw_ref', '')
                        payment.transaction_id = data.get('id', '')
                        if data.get('created_at'):
                            payment.paid_at = data.get('created_at')
                        if data.get('payment_type'):
                            payment.payment_method = data.get('payment_type', '').lower()
                        payment.save()
                        
                        # Update order status to confirmed when payment is successful
                        if payment.order and payment.order.status == 'pending':
                            payment.order.status = 'confirmed'
                            payment.order.save()
                    else:
                        payment.status = 'failed'
                        payment.failure_reason = data.get('processor_response', 'Payment failed')
                        payment.save()
                except Payment.DoesNotExist:
                    pass  # Payment not found, ignore
        
        return Response({'status': 'success'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
