import re

from django.conf import settings
from django.contrib.auth.views import redirect_to_login


class LoginRequiredUnlessExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        patterns = list(getattr(settings, "LOGIN_EXEMPT_URLS", []))
        if settings.DEBUG:
            patterns.append(r"^/static/")
        self.exempt_patterns = [re.compile(p) for p in patterns]

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)
        path = request.path_info
        for pattern in self.exempt_patterns:
            if pattern.search(path):
                return self.get_response(request)
        return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
