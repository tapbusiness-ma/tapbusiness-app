from django import forms

from .models import Restaurant


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ["name", "slug", "phone", "address", "delivery_fee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        self.fields["slug"].help_text = "اختياري — إلا خليتيه خاوي غنولدوه من الاسم"