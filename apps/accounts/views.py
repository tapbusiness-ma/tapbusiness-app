from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect, render


def signup(request):
    """إنشاء حساب جديد لمول مطعم."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    """المساحة الخاصة: غير المطاعم ديال هاد المستخدم كتبان."""
    memberships = request.user.memberships.select_related("restaurant").prefetch_related(
        "restaurant__tables"
    )
    return render(request, "accounts/dashboard.html", {"memberships": memberships})