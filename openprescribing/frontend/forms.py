from django import forms
from django.contrib.auth.models import User
from frontend.models import PCT


class OrgBookmarkForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(attrs={'placeholder': 'Email address'})
    )
    pct = forms.CharField(widget=forms.HiddenInput())
    next = forms.CharField(widget=forms.HiddenInput())

    def clean_pct(self):
        pct_id = self.cleaned_data['pct']
        try:
            pct = PCT.objects.get(pk=pct_id)
        except PCT.DoesNotExist:
            raise forms.ValidationError("PCT %s does not exist" % pct_id)
        return pct
