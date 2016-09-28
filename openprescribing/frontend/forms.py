from django import forms
from django.contrib.auth.models import User
from frontend.models import PCT, Practice


class BookmarkListForm(forms.Form):
    org_bookmarks = forms.MultipleChoiceField(
        label="",
        widget=forms.CheckboxSelectMultiple())
    search_bookmarks = forms.MultipleChoiceField(
        label="Alerts about searches",
        widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        """Populate choices with those passed in, and remove fields with no
        choices.

        """
        org_bookmarks = kwargs.pop('org_bookmarks', [])
        search_bookmarks = kwargs.pop('search_bookmarks', [])
        super(BookmarkListForm, self).__init__(*args, **kwargs)
        if org_bookmarks:
            self.fields['org_bookmarks'].choices = [
                (x.id, x.name()) for x in org_bookmarks]
        else:
            del self.fields['org_bookmarks']
        if search_bookmarks:
            self.fields['search_bookmarks'].choices = [
                (x.id, x.name()) for x in search_bookmarks]
        else:
            del self.fields['search_bookmarks']


class OrgBookmarkForm(forms.Form):
    email = forms.EmailField(
        label="",
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Email address',
                'size': '35'})
    )
    pct = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    practice = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
    next = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        pct_id = self.cleaned_data['pct']
        practice_id = self.cleaned_data['practice']
        if pct_id:
            try:
                self.cleaned_data['pct'] = PCT.objects.get(pk=pct_id)
            except PCT.DoesNotExist:
                raise forms.ValidationError("CCG %s does not exist" % pct_id)
        elif practice_id:
            try:
                self.cleaned_data['practice'] = Practice.objects.get(pk=practice_id)
            except Practice.DoesNotExist:
                raise forms.ValidationError("Practice %s does not exist" % pct_id)
        else:
            raise forms.ValidationError("No practice or CCG specified")
        return self.cleaned_data
