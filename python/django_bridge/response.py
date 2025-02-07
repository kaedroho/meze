from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.utils.cache import patch_cache_control
from django.utils.html import conditional_escape
from django.utils.module_loading import import_string

from .adapters.registry import JSContext


def get_messages(request):
    default_level_tag = messages.DEFAULT_TAGS[messages.SUCCESS]
    return [
        {
            "level": messages.DEFAULT_TAGS.get(message.level, default_level_tag),
            "html": conditional_escape(message.message),
        }
        for message in messages.get_messages(request)
    ]


class BaseResponse(JsonResponse):
    """
    Base class for all Django Bridge responses.
    """

    status = None

    def __init__(self, data, *, http_status=None):
        js_context = JSContext()
        self.data = {
            "status": self.status,
            **data,
        }
        super().__init__(js_context.pack(self.data), status=http_status)
        self["X-DjangoBridge-Status"] = self.status

        # Make sure that Django Bridge responses are never cached by browsers
        # We need to do this because Django Bridge responses are given on the same URLs that
        # users would otherwise get HTML responses on if they visited those URLs
        # directly.
        # If a Django Bridge response is cached, there's a chance that a user could see the
        # JSON document in their browser rather than a HTML page.
        # This behaviour only seems to occur (intermittently) on Firefox.
        patch_cache_control(self, no_store=True)


class Response(BaseResponse):
    """
    Instructs the client to render a view (React component) with the given context.
    """

    status = "render"

    def __init__(
        self, request, view, props, *, overlay=False, title="", http_status=None
    ):
        self.view = view
        self.props = props
        self.overlay = overlay
        self.title = title
        self.context = {
            name: import_string(provider)(request)
            for name, provider in settings.DJANGO_BRIDGE.get(
                "CONTEXT_PROVIDERS", {}
            ).items()
        }
        self.messages = (get_messages(request),)
        super().__init__(
            {
                "view": self.view,
                "overlay": self.overlay,
                "title": self.title,
                "props": self.props,
                "context": self.context,
                "messages": self.messages,
            },
            http_status=http_status,
        )


class ReloadResponse(BaseResponse):
    """
    Instructs the client to load the view the old-fashioned way.
    """

    status = "reload"


class RedirectResponse(BaseResponse):
    status = "redirect"

    def __init__(self, path):
        self.path = path
        super().__init__(
            {
                "path": self.path,
            }
        )


class CloseOverlayResponse(BaseResponse):
    status = "close-overlay"

    def __init__(self, request):
        self.messages = (get_messages(request),)
        super().__init__(
            {
                "messages": self.messages,
            }
        )
