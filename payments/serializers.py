from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.CharField(source='order.order_id', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_id', 'user', 'user_username',
            'amount', 'currency', 'status', 'payment_method',
            'tx_ref', 'flw_ref', 'transaction_id',
            'customer_email', 'customer_name', 'customer_phone',
            'metadata', 'failure_reason', 'created_at', 'updated_at', 'paid_at'
        ]
        read_only_fields = ['tx_ref', 'flw_ref', 'transaction_id', 'status', 'created_at', 'updated_at', 'paid_at']


class PaymentInitiateSerializer(serializers.Serializer):
    order_id = serializers.IntegerField(required=True)
    customer_email = serializers.EmailField(required=True)
    customer_name = serializers.CharField(max_length=255, required=True)
    customer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    payment_method = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)

    def validate_order_id(self, value):
        from orders.models import Order
        try:
            order = Order.objects.get(id=value)
            if order.buyer != self.context['request'].user:
                raise serializers.ValidationError("You don't have permission to pay for this order.")
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")

