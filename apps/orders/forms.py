from django import forms


class CheckoutForm(forms.Form):
    customer_name = forms.CharField(label="الاسم الكامل", max_length=200)
    customer_phone = forms.CharField(label="رقم الهاتف", max_length=20)
    address = forms.CharField(
        label="عنوان التوصيل",
        max_length=255,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
