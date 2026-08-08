"""Auth views: login, register, logout."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.forms import RegisterForm
from accounts.models import Customer
from cart.services import merge_session_cart_to_user


class StoreLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        merge_session_cart_to_user(self.request)
        messages.success(self.request, "Welcome back!")
        return response


class StoreLogoutView(LogoutView):
    next_page = "catalog:home"
    http_method_names = ["get", "post", "options"]


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        Customer.objects.create(
            user=user,
            email=user.email,
            full_name=f"{user.first_name} {user.last_name}".strip() or user.username,
            phone=form.cleaned_data.get("phone", ""),
        )
        login(request, user)
        merge_session_cart_to_user(request)
        messages.success(request, "Account created. Welcome to DESI VIBES!")
        return redirect("catalog:home")
    return render(request, "accounts/register.html", {"form": form})
