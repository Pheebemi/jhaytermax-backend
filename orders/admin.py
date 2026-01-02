from django.contrib import admin
from .models import Order, OrderItem, State, Location


class LocationInline(admin.TabularInline):
    model = Location
    extra = 1
    fields = ['name', 'delivery_fee', 'is_active']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code']
    inlines = [LocationInline]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'delivery_fee', 'is_active', 'created_at']
    list_filter = ['is_active', 'state', 'created_at']
    search_fields = ['name', 'state__name']
    list_editable = ['delivery_fee', 'is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']
    fields = ['product', 'quantity', 'price', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'buyer', 'status', 'total_amount', 'delivery_fee', 'delivery_location', 'created_at']
    list_filter = ['status', 'created_at', 'delivery_location__state']
    search_fields = ['order_id', 'buyer__username', 'buyer__email']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'buyer', 'status', 'total_amount')
        }),
        ('Delivery Information', {
            'fields': ('delivery_location', 'delivery_fee', 'shipping_address')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
