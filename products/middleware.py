from .models import VisitorLog
from django.utils import timezone

class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only care about GET requests to our API or the main pages
        # And we don't want to log admin actions
        if request.method == 'GET' and not request.path.startswith('/admin'):
            ip = self.get_client_ip(request)
            if ip:
                # Check if this IP has EVER been logged to get a total unique count
                already_logged = VisitorLog.objects.filter(
                    ip_address=ip
                ).exists()
                
                if not already_logged:
                    VisitorLog.objects.create(ip_address=ip)

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
