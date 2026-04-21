from django import forms
from .models import IntakeRequest

class IntakeRequestForm(forms.ModelForm):
    class Meta:
        model = IntakeRequest
        fields = ["request_type", "first_name", "last_name", "email", "message"]
        widgets = {
            "message": forms.Textarea(attrs={"maxlength": 1000, "rows": 6}),
        }

    def clean_message(self):
        msg = self.cleaned_data["message"]
        if len(msg) > 1000:
            raise forms.ValidationError("Message cannot exceed 1000 characters.")
        return msg
