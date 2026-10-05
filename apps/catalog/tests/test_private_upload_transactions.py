from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from django.db import connection
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIRequestFactory

from apps.catalog.views import ShopPrivateMediaUploadView


class ShopPrivateMediaUploadTransactionTests(TransactionTestCase):
    @override_settings(R2_ENABLED=True)
    def test_shop_upload_authorization_locks_inside_database_transaction(self):
        shop_id = uuid4()
        target_id = uuid4()
        view = ShopPrivateMediaUploadView()
        request = view.initialize_request(
            APIRequestFactory().post(
                "/api/v1/shops/test/catalog/media/uploads/",
                {
                    "action": "authorize",
                    "kind": "style_option",
                    "target_id": str(target_id),
                    "content_type": "image/png",
                    "byte_size": 128,
                },
                format="json",
            )
        )
        request.user = SimpleNamespace(pk=uuid4())
        request.shop_context = SimpleNamespace(shop=SimpleNamespace(pk=shop_id))

        def issue_upload(**_kwargs):
            assert connection.in_atomic_block
            return {
                "upload_url": "https://r2.example.invalid/signed-put",
                "upload_token": "test-token",
                "headers": {"Content-Type": "image/png"},
                "expires_in": 600,
            }

        with (
            patch("apps.catalog.views._lock_shop_write_context"),
            patch("apps.catalog.views._shop_write_allowed", return_value=True),
            patch("apps.catalog.views.issue_upload", side_effect=issue_upload),
        ):
            response = view.post(request, shop_id=shop_id)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Cache-Control"], "no-store")
