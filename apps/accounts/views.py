from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.menu.models import Product
from apps.orders.models import Order


def home(request):
    """الصفحة الرئيسية — عرض TAPBusiness."""
    if request.user.is_authenticated:
        return redirect("accounts:dashboard")
    return render(request, "home.html")


def signup(request):
    """إنشاء حساب جديد لمول مطعم."""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # كنحددو الـbackend صراحة حيث كاينين جوج (Axes + ModelBackend)
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("accounts:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    """لوحة تحكم مول المطعم: إحصائيات + آخر الطلبات + المطاعم."""
    memberships = (
        request.user.memberships.select_related(
            "restaurant", "restaurant__subscription__plan"
        )
        .prefetch_related("restaurant__tables")
    )
    restaurant_ids = [m.restaurant_id for m in memberships]
    today = timezone.localdate()
    orders_qs = Order.objects.filter(restaurant_id__in=restaurant_ids)
    revenue_statuses = [
        Order.Status.CONFIRMED,
        Order.Status.PREPARING,
        Order.Status.READY,
        Order.Status.DELIVERED,
    ]
    stats = {
        "today_count": orders_qs.filter(created_at__date=today).count(),
        "today_total": orders_qs.filter(
            created_at__date=today, status__in=revenue_statuses
        ).aggregate(total=Sum("total"))["total"]
        or 0,
        "dishes_count": Product.objects.filter(
            restaurant_id__in=restaurant_ids, is_available=True
        ).count(),
        "pending_count": orders_qs.filter(status=Order.Status.PENDING).count(),
    }
    recent_orders = orders_qs.select_related("restaurant").order_by("-created_at")[:8]
    return render(
        request,
        "accounts/dashboard.html",
        {
            "memberships": memberships,
            "stats": stats,
            "recent_orders": recent_orders,
        },
    )