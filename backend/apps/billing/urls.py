from django.urls import path

from .views import (
    CheckoutSessionAPIView,
    CurrentSubscriptionAPIView,
    DemoPaymentSuccessAPIView,
    InvoiceListAPIView,
    SubscribeAPIView,
    StripeWebhookAPIView,
    SubscriptionPlanListAPIView,
    UpgradeSubscriptionAPIView,
)

urlpatterns = [
    path('plans/', SubscriptionPlanListAPIView.as_view(), name='billing-plan-list'),
    path('subscribe/', SubscribeAPIView.as_view(), name='billing-subscribe'),
    path('subscription/', CurrentSubscriptionAPIView.as_view(), name='billing-current-subscription'),
    path('upgrade/', UpgradeSubscriptionAPIView.as_view(), name='billing-upgrade'),
    path('invoices/', InvoiceListAPIView.as_view(), name='billing-invoice-list'),
    path('checkout-sessions/', CheckoutSessionAPIView.as_view(), name='billing-checkout-session'),
    path('webhooks/stripe/', StripeWebhookAPIView.as_view(), name='billing-stripe-webhook'),
    path('demo-payment-success/', DemoPaymentSuccessAPIView.as_view(), name='billing-demo-payment-success'),
]
