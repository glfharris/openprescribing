from itertools import chain
from django.http import HttpResponse
from django import forms
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from frontend.models import SearchBookmark, OrgBookmark


class BookmarkList(ListView):
    # XXX as we're using custom context data, I'm not sure what
    # benefits using a ListView brings us
    context_object_name = 'bookmark_list'
    template_name = 'bookmarks/bookmark_list.html'
    model = SearchBookmark

    def get_context_data(self):
        search_bookmarks = SearchBookmark.objects.filter(
            user__id=self.request.user.id)
        org_bookmarks = OrgBookmark.objects.filter(
            user__id=self.request.user.id)
        return {
            'search_bookmarks': search_bookmarks,
            'org_bookmarks': org_bookmarks
        }

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
    success_url = reverse_lazy('bookmark-list')

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
    success_url = reverse_lazy('bookmark-list')


class SearchBookmarkDelete(DeleteView):
    model = SearchBookmark
    success_url = reverse_lazy('bookmark-list')


class OrgBookmarkForm(forms.ModelForm):
    class Meta:
        model = OrgBookmark
        fields = ['pct', 'practice', 'include_in_email']


@method_decorator(login_required, name='dispatch')
class OrgBookmarkCreate(CreateView):
    model = OrgBookmark
    form_class = OrgBookmarkForm
    template_name = 'bookmarks/orgbookmark_form.html'
    success_url = reverse_lazy('bookmark-list')

    def get_initial(self):
        return {
            'pct': self.request.GET.get('pct'),
            'practice': self.request.GET.get('practice'),
        }

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super(OrgBookmarkCreate, self).form_valid(form)


class OrgBookmarkUpdate(UpdateView):
    model = OrgBookmark
    template_name = 'bookmarks/orgbookmark_form.html'
    form_class = OrgBookmarkForm
    success_url = reverse_lazy('bookmark-list')


class OrgBookmarkDelete(DeleteView):
    model = OrgBookmark
    success_url = reverse_lazy('bookmark-list')
