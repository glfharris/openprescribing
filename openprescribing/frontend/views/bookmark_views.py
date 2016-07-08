from django.http import HttpResponse
from django import forms
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from frontend.models import SearchBookmark


class SearchBookmarkList(ListView):
    model = SearchBookmark
    template_name = 'bookmarks/searchbookmark_list.html'

    def get_queryset(self):
        return SearchBookmark.objects.filter(
            user__id=self.request.user.id)


class SearchBookmarkForm(forms.ModelForm):

    class Meta:
        model = SearchBookmark
        fields = ['name', 'include_in_email', 'url']
        widgets = {
            'url': forms.HiddenInput(),
            'name': forms.Textarea()
            }


@method_decorator(login_required, name='dispatch')
class SearchBookmarkCreate(CreateView):
    model = SearchBookmark
    form_class = SearchBookmarkForm
    template_name = 'bookmarks/searchbookmark_form.html'
    success_url = reverse_lazy('searchbookmark-list')

    def get_initial(self):
        return {
            'url': self.request.GET.get('url'),
            'name': self.request.GET.get('name'),
        }


    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(SearchBookmarkCreate, self).form_valid(form)


class SearchBookmarkUpdate(UpdateView):
    model = SearchBookmark
    template_name = 'bookmarks/searchbookmark_form.html'
    form_class = SearchBookmarkForm


class SearchBookmarkDelete(DeleteView):
    model = SearchBookmark
    template_name = 'bookmarks/searchbookmark_form.html'
    fields = ['name', 'include_in_email']
    success_url = reverse_lazy('searchbookmark-list')
