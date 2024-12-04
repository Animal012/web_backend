from django.http import HttpResponse
from app.views import session_storage
from app.models import CustomUser


def session_middleware(get_response):
    def middleware(request):
        print("Session middleware: Before processing")
        ssid = request.COOKIES.get("session_id")
        if ssid and session_storage.exists(ssid):
            email = session_storage.get(ssid).decode("utf-8")
            print(f"Email found in session: {email}")
            request.user = CustomUser.objects.get(email=email)
        else:
            print("No valid session found.")
            request.user = None
        print(f"request.user = {getattr(request.user, 'email', None)}")
        response = get_response(request)
        print(f"Session middleware: After processing, request.user = {getattr(request.user, 'email', None)}")
        return response

    return middleware
