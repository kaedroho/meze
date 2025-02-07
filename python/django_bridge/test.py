from django.test import Client as DjangoClient
from django.test import TestCase as DjangoTestCase

BOUNDARY = "BoUnDaRyStRiNg"
MULTIPART_CONTENT = "multipart/form-data; boundary=%s" % BOUNDARY

class Client(DjangoClient):
    def get(
        self, path, data=None, secure=False, *, headers=None, query_params=None, **extra
    ):
        extra.setdefault("HTTP_X_REQUESTED_WITH", "DjangoBridge")
        return super().get(
            path, data, secure, headers=headers, query_params=query_params, **extra
        )

    def post(
        self,
        path,
        data=None,
        content_type=MULTIPART_CONTENT,
        secure=False,
        *,
        headers=None,
        query_params=None,
        **extra,
    ):
        extra.setdefault("HTTP_X_REQUESTED_WITH", "DjangoBridge")
        return super().post(
            path,
            data,
            content_type,
            secure,
            headers=headers,
            query_params=query_params,
            **extra,
        )


class TestCase(DjangoTestCase):
    client_class = Client

    def assertRedirects(self, response, expected_url, *args, **kwargs):
        if response.request.get("HTTP_X_REQUESTED_WITH") == "DjangoBridge":
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.status, "redirect")
            self.assertEqual(response.path, expected_url)
        else:
            return super().assertRedirects(response, expected_url, *args, **kwargs)
