from django import forms
from django.contrib.auth.forms import AuthenticationForm


class CustomAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Usuario o contraseña incorrectos. Verifica tus credenciales.",
        "inactive": "Tu cuenta se encuentra inactiva.",
    }

    username = forms.CharField(
        label="Usuario",
        widget=forms.TextInput(
            attrs={
                "class": (
                    "w-full rounded-2xl border border-white/10 bg-white/5 "
                    "py-3.5 pl-12 pr-4 text-sm text-white placeholder:text-slate-400 "
                    "outline-none transition duration-200 "
                    "focus:border-cyan-400/70 focus:bg-white/10 focus:ring-4 focus:ring-cyan-400/15"
                ),
                "placeholder": "Ingresa tu usuario",
                "autofocus": True,
                "autocomplete": "username",
                "spellcheck": "false",
            }
        ),
    )

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": (
                    "w-full rounded-2xl border border-white/10 bg-white/5 "
                    "py-3.5 pl-12 pr-16 text-sm text-white placeholder:text-slate-400 "
                    "outline-none transition duration-200 "
                    "focus:border-cyan-400/70 focus:bg-white/10 focus:ring-4 focus:ring-cyan-400/15"
                ),
                "placeholder": "Ingresa tu contraseña",
                "autocomplete": "current-password",
            }
        ),
    )