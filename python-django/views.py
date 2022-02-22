from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework.response import Response
from .serializers.models_sz import *
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route, list_route, api_view
from cleaning.models import SMSVerifier


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    queryset = Category.objects.all()

    def get_serializer_class(self):
        return CategorySerializer


class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    queryset = Subject.objects.all()

    def get_serializer_class(self):
        return SubjectSerializer


class ServiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    queryset = Service.objects.all()

    def get_serializer_class(self):
        return ServiceSerializer


class SubjectServiceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    queryset = SubjectService.objects.all()

    def get_serializer_class(self):
        return SubjectServiceSerializer


class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    authentication_classes = ()
    queryset = PaymentMethod.objects.all()

    def get_serializer_class(self):
        return PaymentMethodSerializer
