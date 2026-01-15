from rest_framework import serializers
from .models import Order, OrderItem, State, Location


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ['id', 'name', 'code', 'is_active']


class LocationSerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        queryset=State.objects.all(), source='state', write_only=True
    )

    class Meta:
        model = Location
        fields = ['id', 'state', 'state_id', 'name', 'delivery_fee', 'is_active']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    subtotal = serializers.ReadOnlyField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price', 'subtotal']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_username = serializers.CharField(source='buyer.username', read_only=True)
    buyer_email = serializers.CharField(source='buyer.email', read_only=True)
    delivery_location_name = serializers.CharField(source='delivery_location.name', read_only=True)
    delivery_location_state = serializers.CharField(source='delivery_location.state.name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_id', 'buyer', 'buyer_username', 'buyer_email',
            'status', 'total_amount', 'shipping_address', 'delivery_location',
            'delivery_location_name', 'delivery_location_state', 'delivery_fee',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['order_id', 'buyer', 'created_at', 'updated_at']


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)
    location_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    detailed_address = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Order
        fields = ['items', 'location_id', 'detailed_address', 'notes']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        location_id = validated_data.pop('location_id', None)
        detailed_address = validated_data.pop('detailed_address', '')
        
        buyer = self.context['request'].user
        
        # Get delivery location and fee
        delivery_location = None
        delivery_fee = 0
        if location_id:
            try:
                delivery_location = Location.objects.get(id=location_id, is_active=True)
                delivery_fee = delivery_location.delivery_fee
            except Location.DoesNotExist:
                raise serializers.ValidationError({'location_id': 'Invalid location'})
        
        # Calculate total amount
        total_amount = 0
        order_items = []
        
        for item_data in items_data:
            from products.models import Product
            try:
                product = Product.objects.get(id=item_data['product_id'])
            except Product.DoesNotExist:
                raise serializers.ValidationError({'items': f'Product {item_data["product_id"]} not found'})
            
            quantity = item_data['quantity']
            price = product.price
            subtotal = quantity * price
            total_amount += subtotal
            
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
            })
        
        total_amount += delivery_fee
        
        # Create order
        order = Order.objects.create(
            buyer=buyer,
            total_amount=total_amount,
            shipping_address=detailed_address,
            delivery_location=delivery_location,
            delivery_fee=delivery_fee,
            notes=validated_data.get('notes', ''),
        )
        
        # Create order items
        for item_data in order_items:
            OrderItem.objects.create(
                order=order,
                product=item_data['product'],
                quantity=item_data['quantity'],
                price=item_data['price'],
            )
        
        return order


