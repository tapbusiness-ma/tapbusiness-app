from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.subscriptions.models import Plan, Subscription
from .forms import RestaurantForm, RestaurantSettingsForm
from .models import Membership, Restaurant


@login_required
def restaurant_create(request):
    """مول مطعم جديد كينشئ المطعم ديالو براسو."""
    if request.method == "POST":
        form = RestaurantForm(request.POST)
        if form.is_valid():
            restaurant = form.save(commit=False)
            if not restaurant.slug:
                base = slugify(restaurant.name) or "restaurant"
                slug = base
                counter = 1
                while Restaurant.objects.filter(slug=slug).exists():
                    counter += 1
                    slug = f"{base}-{counter}"
                restaurant.slug = slug

            with transaction.atomic():
                restaurant.save()
                Membership.objects.create(
                    user=request.user,
                    restaurant=restaurant,
                    role=Membership.Roles.OWNER,
                )
                demo_plan = Plan.objects.filter(slug="demo").first()
                if demo_plan:
                    Subscription.objects.create(
                        restaurant=restaurant,
                        plan=demo_plan,
                        status=Subscription.Status.TRIAL,
                    )
            return redirect("accounts:dashboard")
    else:
        form = RestaurantForm()

    return render(request, "restaurants/restaurant_form.html", {"form": form})
def _get_owned_restaurant(request, slug):
    """يرجع المطعم إلا كان المستخدم مالك أو مدير ديالو، وإلا 404."""
    return get_object_or_404(
        Restaurant.objects.filter(
            slug=slug,
            is_active=True,
            memberships__user=request.user,
            memberships__role__in=[
                Membership.Roles.OWNER,
                Membership.Roles.MANAGER,
            ],
        )
    )


@login_required
def restaurant_settings(request, slug):
    """إعدادات المطعم: الاسم، الهاتف، العنوان، ثمن التوصيل."""
    restaurant = _get_owned_restaurant(request, slug)
    if request.method == "POST":
        form = RestaurantSettingsForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            return redirect("accounts:dashboard")
    else:
        form = RestaurantSettingsForm(instance=restaurant)
    ctx = {
        "restaurant": restaurant,
        "form": form,
        "memberships": request.user.memberships.select_related(
            "restaurant"
        ).order_by("restaurant__name"),
    }
    return render(request, "restaurants/restaurant_settings.html", ctx)
