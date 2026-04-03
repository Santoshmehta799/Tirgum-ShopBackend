# middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from django.views.defaults import page_not_found
from django.http import HttpResponse
from django.http import Http404

class UserApprovalMiddleware:
    EXEMPT_URLS = [
        reverse('login'), 
        reverse('signup'), 
        reverse('logout'), 
        reverse('admin:index'), 
        reverse('admin:logout'),  # Add Django admin logout URL if needed
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated or not request.user.is_approved:
            path = request.path_info
            if path not in self.EXEMPT_URLS and not path.startswith('/admin') and not path.startswith('favicon.ico'):
                return redirect("login")
        try:
            return self.get_response(request)
        except Exception:
            return page_not_found(request, exception=None)
