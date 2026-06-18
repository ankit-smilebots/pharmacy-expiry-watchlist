from django import forms

from .models import Batch


class UnlockForm(forms.Form):
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "autofocus": True,
            "autocomplete": "current-password",
            "placeholder": "Enter password",
        }),
    )


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["medicine_name", "batch_number", "expiry_date", "quantity", "supplier"]
        widgets = {
            "medicine_name": forms.TextInput(attrs={
                "placeholder": "e.g. Paracetamol 500mg",
                "autofocus": True,
            }),
            "batch_number": forms.TextInput(attrs={"placeholder": "e.g. B12345"}),
            # type=date gives the native date picker on phones and desktops.
            "expiry_date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "quantity": forms.NumberInput(attrs={"min": 0, "placeholder": "e.g. 50"}),
            "supplier": forms.TextInput(attrs={"placeholder": "e.g. City Medical Distributors"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure an existing value shows up correctly in the date input.
        self.fields["expiry_date"].input_formats = ["%Y-%m-%d"]
