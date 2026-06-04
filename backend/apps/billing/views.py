"""Demo subscription and billing APIs."""

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User

from .models import Payment, SubscriptionPlan
from .serializers import (
    DemoPaymentSuccessSerializer,
    PaymentSerializer,
    PlanSelectionSerializer,
    SubscriptionPlanSerializer,
    SubscriptionSerializer,
)
from .services import (
    activate_demo_subscription,
    create_pending_subscription,
    get_active_hr_head_membership,
    get_active_subscription,
)


class BillingHRHeadMixin:
    def get_organization(self, request):
        if request.user.role != User.Role.HR_HEAD:
            raise PermissionDenied('Only HR heads can manage subscriptions and billing.')
        membership = get_active_hr_head_membership(request.user)
        if not membership:
            raise PermissionDenied('An active HR head organization membership is required.')
        return membership.organization


class SubscriptionPlanListAPIView(BillingHRHeadMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        self.get_organization(request)
        plans = SubscriptionPlan.objects.filter(is_active=True)
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class SubscribeAPIView(BillingHRHeadMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = self.get_organization(request)
        serializer = PlanSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = create_pending_subscription(
            organization=organization,
            plan=serializer.validated_data['plan_id'],
            is_auto_renew=serializer.validated_data['is_auto_renew'],
        )
        return Response(
            {
                'message': 'Demo subscription created. Complete demo payment to activate it.',
                'subscription': SubscriptionSerializer(subscription).data,
                'demo_payment_endpoint': '/api/billing/demo-payment-success/',
            },
            status=status.HTTP_201_CREATED,
        )


class CurrentSubscriptionAPIView(BillingHRHeadMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = self.get_organization(request)
        subscription = get_active_subscription(organization)
        if not subscription:
            return Response({'detail': 'No active subscription found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubscriptionSerializer(subscription).data)


class UpgradeSubscriptionAPIView(SubscribeAPIView):
    def post(self, request):
        organization = self.get_organization(request)
        serializer = PlanSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = create_pending_subscription(
            organization=organization,
            plan=serializer.validated_data['plan_id'],
            is_auto_renew=serializer.validated_data['is_auto_renew'],
        )
        return Response(
            {
                'message': 'Demo plan change created. Complete demo payment to activate the new plan.',
                'subscription': SubscriptionSerializer(subscription).data,
                'demo_payment_endpoint': '/api/billing/demo-payment-success/',
            },
            status=status.HTTP_201_CREATED,
        )


class InvoiceListAPIView(BillingHRHeadMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        organization = self.get_organization(request)
        payments = Payment.objects.filter(subscription__organization=organization).select_related(
            'subscription', 'subscription__plan', 'subscription__organization'
        )
        return Response(PaymentSerializer(payments, many=True).data)


class DemoPaymentSuccessAPIView(BillingHRHeadMixin, APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        organization = self.get_organization(request)
        serializer = DemoPaymentSuccessSerializer(data=request.data, context={'organization': organization})
        serializer.is_valid(raise_exception=True)
        payment = activate_demo_subscription(
            serializer.validated_data['subscription_id'],
            serializer.validated_data.get('transaction_reference', ''),
        )
        return Response(
            {
                'message': 'Demo payment recorded and subscription activated.',
                'subscription': SubscriptionSerializer(payment.subscription).data,
                'payment': PaymentSerializer(payment).data,
            },
            status=status.HTTP_201_CREATED,
        )
