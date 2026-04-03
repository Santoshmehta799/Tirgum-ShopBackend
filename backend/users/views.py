# from django.conf import settings
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, UsernameField
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from users.serializers import ContactUsSerializer

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User  # Use your custom user model
        fields = ['email', 'password1', 'password2']


class SignUpView(UserPassesTestMixin, CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')  # Redirect to the login page upon successful registration
    template_name = 'registration/signup.html'

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "Stop: You do not have permission to access registration page.")
        return super().handle_no_permission()


class CustomLoginView(LoginView):
    def form_valid(self, form):
        user = form.get_user()

        # Check if the user is approved
        if user.is_approved:
            return super().form_valid(form)
        else:
            return HttpResponse("Not Approved")


class ContactUsAPIView(APIView):
    def post(self, request):
        serializer = ContactUsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()

            # User input
            name = serializer.validated_data.get('name')
            email = serializer.validated_data.get('email')
            message = serializer.validated_data.get('message')

            # Email to your client
            subject = "New Contact Us Submission"
            body = f"""
                You have received a new message from your website contact form.

                Name: {name}
                Email: {email}
                Message:
                {message}
            """

            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,       
                [settings.CLIENT_NOTIFICATION_EMAIL],
                fail_silently=False,
            )

            return Response({"message": "Submitted successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)