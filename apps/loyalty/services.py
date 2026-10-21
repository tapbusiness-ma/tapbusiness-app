"""خدمات برنامج الولاء — القواعد التجارية فنقطة وحدة، بلا منطق فالـviews."""

import re
from decimal import Decimal

from django.db import IntegrityError, transaction

from apps.orders.models import Order
from apps.subscriptions.models import Subscription

from .models import LoyaltyTransaction, LoyaltyWallet

# نقطة وحدة لكل 10 دراهم كاملة من المجموع الفرعي (الأطباق فقط، بلا مصاريف التوصيل)
POINTS_STEP_DH = Decimal("10")


def normalize_phone(raw):
    """توحيد رقم الهاتف المغربي: 06xxxxxxxx ولا 00212... ولا 212... → +212..."""
    phone = re.sub(r"[\s\-().]", "", (raw or "").strip())
    if phone.startswith("00212"):
        phone = "+" + phone[2:]
    elif phone.startswith("212") and len(phone) == 12:
        phone = "+" + phone
    elif phone.startswith("0") and len(phone) == 10:
        phone = "+212" + phone[1:]
    return phone


def loyalty_enabled(restaurant):
    """الولاء خاص بمطعم Premium باشتراك نشط — التحقق كيتم فالسيرفر دائماً."""
    subscription = getattr(restaurant, "subscription", None)
    return bool(
        subscription
        and subscription.plan.slug == "premium"
        and subscription.status == Subscription.Status.ACTIVE
    )


def points_for_subtotal(subtotal):
    """floor(subtotal / 10) بحساب Decimal — بلا أخطاء الأعداد العائمة."""
    if not subtotal:
        return 0
    return int(subtotal // POINTS_STEP_DH)


def award_points_for_order(order):
    """ربح نقط طلب تم توصيله — مرة وحدة فقط لكل طلب.

    كترجع عدد النقط المضافة (0 إلا ما تستاهلش ولا تربحات من قبل).
    خاصها تتعيّط داخل transaction.atomic() (من view تبديل الحالة) باش
    تغيير الحالة وتسجيل الربح يوقعو معاً أو يلغاو معاً.
    """
    if order.status != Order.Status.DELIVERED:
        return 0
    if not loyalty_enabled(order.restaurant):
        return 0
    points = points_for_subtotal(order.subtotal)
    if points <= 0:
        return 0
    phone = normalize_phone(order.customer_phone)
    if not phone:
        return 0

    wallet, _created = LoyaltyWallet.objects.select_for_update().get_or_create(
        restaurant=order.restaurant, phone=phone
    )
    already = LoyaltyTransaction.objects.filter(
        order=order, kind=LoyaltyTransaction.Kind.EARN
    ).exists()
    if already:
        return 0
    try:
        with transaction.atomic():
            LoyaltyTransaction.objects.create(
                wallet=wallet,
                kind=LoyaltyTransaction.Kind.EARN,
                points=points,
                order=order,
                reason=f"طلب #{order.id} تم توصيله",
            )
    except IntegrityError:
        # سبقنا طلب متزامن — القيد الفريد هو خط الدفاع الأخير
        return 0
    wallet.balance += points
    wallet.save(update_fields=["balance", "updated_at"])
    return points
