from django.http import Http404


class DevAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path_info.startswith("/dev/"):
            if not request.user.is_authenticated or not request.user.is_dev:
                raise Http404()
        return self.get_response(request)
