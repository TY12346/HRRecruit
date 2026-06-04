from django.contrib import admin

from .models import Payment, Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'billing_cycle', 'max_job_postings', 'price', 'is_active')
    list_filter = ('name', 'billing_cycle', 'is_active')
    search_fields = ('name', 'features_description')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'plan', 'start_date', 'end_date', 'status', 'is_auto_renew', 'created_at')
    list_filter = ('status', 'is_auto_renew', 'plan__name', 'plan__billing_cycle')
    search_fields = ('organization__name', 'plan__name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'invoice_number', 'subscription', 'payment_gateway', 'amount', 'currency', 'status', 'paid_at')
    list_filter = ('payment_gateway', 'status', 'currency')
    search_fields = (
        'invoice_number',
        'transaction_reference',
        'subscription__organization__name',
        'subscription__plan__name',
    )
