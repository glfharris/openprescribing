from django import forms
from django.contrib.auth.models import User
from frontend.models import PCT


class BookmarkListForm(forms.Form):
    org_bookmarks = forms.MultipleChoiceField(
        label="Alerts about organisations",
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
