from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import SignUpForm


@require_http_methods(["GET", "POST"])
def signup(request):
    """Create a user account and redirect to the research home."""
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("research:index")
    return render(request, "accounts/signup.html", {"form": form})


@login_required
@require_http_methods(["POST"])
def logout_view(request):
    """Log the user out and send them back to the login screen."""
    logout(request)
    return redirect("accounts:login")