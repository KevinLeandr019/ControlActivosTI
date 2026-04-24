from .models import PerfilUsuario


def current_user_profile(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"current_user_profile": None}

    profile = PerfilUsuario.objects.filter(user=request.user).first()
    return {"current_user_profile": profile}
