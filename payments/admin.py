from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'user', 'amount', 'currency', 'status', 'payment_method', 'tx_ref', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['tx_ref', 'flw_ref', 'transaction_id', 'order__order_id', 'user__username', 'customer_email']
    readonly_fields = ['tx_ref', 'flw_ref', 'transaction_id', 'webhook_data', 'created_at', 'updated_at', 'paid_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'user', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Flutterwave Details', {
            'fields': ('tx_ref', 'flw_ref', 'transaction_id')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'customer_name', 'customer_phone')
        }),
        ('Additional Information', {
            'fields': ('metadata', 'failure_reason', 'webhook_data', 'created_at', 'updated_at', 'paid_at')
        }),
    )
