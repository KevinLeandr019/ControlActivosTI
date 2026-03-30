from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import CustomAuthenticationForm


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("dashboard-inicio")