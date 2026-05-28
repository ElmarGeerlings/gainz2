from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.services import register_user


def redirect_after_auth(req_event):
    next_url = req_event.POST.get("next") or req_event.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={req_event.get_host()},
        require_https=req_event.is_secure(),
    ):
        return redirect(next_url)
    return redirect(settings.LOGIN_REDIRECT_URL)


def home_page(req_event):
    return render(req_event, "accounts/home.html", {"title": "Home"})


def login_page(req_event):
    if req_event.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if req_event.method == "POST":
        username = req_event.POST.get("username", "").strip()
        password = req_event.POST.get("password", "")
        user = authenticate(req_event, username=username, password=password)
        if user is not None:
            login(req_event, user)
            return redirect_after_auth(req_event)
        messages.error(req_event, "Invalid username or password.")
    next_url = req_event.GET.get("next", "")
    return render(
        req_event,
        "accounts/login.html",
        {"title": "Log in", "next": next_url},
    )


def register_page(req_event):
    if req_event.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    if req_event.method == "POST":
        username = req_event.POST.get("username", "").strip()
        password = req_event.POST.get("password", "")
        password_confirm = req_event.POST.get("password_confirm", "")
        if password != password_confirm:
            messages.error(req_event, "Passwords do not match.")
        else:
            user, errors = register_user(username, password)
            if user is not None:
                login(req_event, user)
                return redirect_after_auth(req_event)
            for message in errors:
                messages.error(req_event, message)
    next_url = req_event.GET.get("next", "")
    return render(
        req_event,
        "accounts/register.html",
        {"title": "Register", "next": next_url},
    )


def logout_page(req_event):
    if req_event.method == "POST":
        logout(req_event)
        return redirect(settings.LOGOUT_REDIRECT_URL)
    return redirect(settings.LOGIN_URL)
