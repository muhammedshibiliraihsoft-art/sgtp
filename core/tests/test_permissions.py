import pytest
from django.db import models, connection
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.response import Response
from core.permissions import IsOwner, IsTenantMember, DenyAll
from apps.common.views import TenantScopedMixin
from django.http import Http404
from rest_framework.exceptions import PermissionDenied

User = get_user_model()

# Dummy Model for testing permissions and querysets
class DummyTestModel(models.Model):
    tenant_id = models.IntegerField()
    owner_id = models.UUIDField()

    class Meta:
        app_label = 'core'

from rest_framework import serializers

class DummyTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DummyTestModel
        fields = '__all__'

# Dummy View extending TenantScopedMixin and GenericAPIView
class DummyTestView(TenantScopedMixin, generics.RetrieveAPIView):
    queryset = DummyTestModel.objects.all()
    serializer_class = DummyTestSerializer
    permission_classes = [IsOwner]
    
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

class PermissionsAndScopingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create the dummy table for testing
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyTestModel)

    @classmethod
    def tearDownClass(cls):
        # Drop the dummy table after testing
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyTestModel)
        super().tearDownClass()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.user1 = User.objects.create_user(email='user1@test.com', password='pw')
        self.user2 = User.objects.create_user(email='user2@test.com', password='pw')
        
        # Object 1 belongs to tenant 100, owned by user1
        self.obj1 = DummyTestModel.objects.create(tenant_id=100, owner_id=self.user1.id)
        # Object 2 belongs to tenant 200, owned by user2
        self.obj2 = DummyTestModel.objects.create(tenant_id=200, owner_id=self.user2.id)

    def test_missing_object_returns_404(self):
        """Requesting an object that does not exist returns 404."""
        request = self.factory.get('/dummy/100/999/')
        force_authenticate(request, user=self.user1)
        
        view = DummyTestView.as_view()
        response = view(request, shop_id=100, pk=999)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_out_of_scope_object_returns_404(self):
        """
        Requesting an object that exists but belongs to a different tenant_id 
        than the URL's shop_id must return 404 (IDOR defense).
        """
        # User1 requests obj2 (tenant 200) but specifies shop_id=100 in the URL
        request = self.factory.get(f'/dummy/100/{self.obj2.id}/')
        force_authenticate(request, user=self.user1)
        
        view = DummyTestView.as_view()
        response = view(request, shop_id=100, pk=self.obj2.id)
        # 404 because the TenantScopedMixin excludes it from the queryset
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_but_unauthorized_returns_403(self):
        """
        Requesting an in-scope object (correct shop_id) but failing the 
        IsOwner permission check must return 403.
        """
        # User2 requests obj1 (tenant 100), using the correct shop_id=100 in URL
        request = self.factory.get(f'/dummy/100/{self.obj1.id}/')
        force_authenticate(request, user=self.user2)
        
        view = DummyTestView.as_view()
        response = view(request, shop_id=100, pk=self.obj1.id)
        # 403 because it is in the queryset, but IsOwner fails
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_in_scope_and_authorized_returns_200(self):
        """
        Requesting an in-scope object as the valid owner returns 200.
        """
        request = self.factory.get(f'/dummy/100/{self.obj1.id}/')
        force_authenticate(request, user=self.user1)
        
        view = DummyTestView.as_view()
        response = view(request, shop_id=100, pk=self.obj1.id)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_istenantmember_interface_is_secure_by_default(self):
        """
        IsTenantMember is currently an interface and must return False.
        """
        request = self.factory.get('/')
        force_authenticate(request, user=self.user1)
        perm = IsTenantMember()
        
        # It should deny by default
        self.assertFalse(perm.has_permission(request, None))
        self.assertFalse(perm.has_object_permission(request, None, self.obj1))

    def test_denyall_interface(self):
        request = self.factory.get('/')
        perm = DenyAll()
        self.assertFalse(perm.has_permission(request, None))
        self.assertFalse(perm.has_object_permission(request, None, self.obj1))
