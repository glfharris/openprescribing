from itertools import chain
from django.http import HttpResponse
from django import forms
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import authenticate
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from frontend.models import SearchBookmark, OrgBookmark
from frontend.models import Profile
from frontend.forms import BookmarkListForm


class BookmarkList(ListView):
    # XXX as we're using custom context data, I'm not sure what
    # benefits using a ListView brings us
    context_object_name = 'bookmark_list'
    template_name = 'bookmarks/bookmark_list.html'
    model = SearchBookmark

    def post(self, request, *args, **kwargs):
        count = 0
        if request.POST.get('unsuball'):
            org_bookmarks = [x.id for x in self._org_bookmarks()]
            search_bookmarks = [x.id for x in self._search_bookmarks()]
        else:
            org_bookmarks = request.POST.getlist('org_bookmarks')
            search_bookmarks = request.POST.getlist('search_bookmarks')
        for b in org_bookmarks:
            OrgBookmark.objects.get(pk=b).delete()
            count += 1
        for b in search_bookmarks:
            SearchBookmark.objects.get(pk=b).delete()
            count += 1
        if count > 0:
            messages.success(
                request,
                "Unsubscribed from %s alerts" % count)
        return redirect(
            reverse('bookmark-list'))

    def _search_bookmarks(self):
        return SearchBookmark.objects.filter(
            user__id=self.request.user.id)

    def _org_bookmarks(self):
        return OrgBookmark.objects.filter(
            user__id=self.request.user.id)

    def get_context_data(self):
        search_bookmarks = self._search_bookmarks()
        org_bookmarks = self._org_bookmarks()
        form = BookmarkListForm(
            org_bookmarks=org_bookmarks,
            search_bookmarks=search_bookmarks
        )
        return {
            'search_bookmarks': search_bookmarks,
            'org_bookmarks': org_bookmarks,
            'form': form,
            'count': search_bookmarks.count() + org_bookmarks.count()
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


def login_from_key(request, key):
    user = authenticate(key=key)
    if user:
        login(request, user)
    else:
        raise PermissionDenied
    return redirect('bookmark-list')
