from django import forms
from django.contrib.auth import authenticate
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from frontend.models import SearchBookmark, OrgBookmark, PCT
from frontend.models import Measure, MeasureGlobal, MeasureValue
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
            msg = "Unsubscribed from %s alert" % count
            if count > 1:
                msg += "s"
            messages.success(
                request,
                msg)
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
        count = search_bookmarks.count() + org_bookmarks.count()
        single_bookmark = None
        if count == 1:
            single_bookmark = search_bookmarks.first() or org_bookmarks.first()
        return {
            'search_bookmarks': search_bookmarks,
            'org_bookmarks': org_bookmarks,
            'form': form,
            'count': count,
            'single_bookmark': single_bookmark
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


def org_alert_email_context(org_bookmark):
    """Given an org, generate a context to be used when composing monthly
    alerts.

    Not a true Django view, but feels appropriate to store it with
    other views."""
    org = org_bookmark.pct

    # Where they're in the worst decile over the past six months,
    # ordered by badness

    worst_measures = []
    for measure in Measure.objects.all():
        percentiles = MeasureGlobal.objects.filter(
            measure=measure, month__gte='2012-01-01'
        ).only('month', 'percentiles')
        bad_count_threshold = percentiles.count()
        print
        print "Found %s thresholds" % bad_count_threshold
        print "Looking at %s for CCG %s" % (measure, org.code)
        if measure.low_is_good:
            for p in percentiles:
                print "Bad means more than %s on %s"% (p.percentiles['ccg']['90'], p.month)
                is_worst = MeasureValue.objects.filter(
                    measure=measure, pct=org, practice=None,
                    percentile__gte=p.percentiles['ccg']['90'] * 100,
                    month=p.month
                )
                if is_worst.count() == 0:
                    worst_measures = []
                    break
                else:
                    print "Worse on following dates"
                    print [(x.month, x.percentile) for x in is_worst]
                    worst_measures.append(measure)
        else:
            for p in percentiles:
                is_worst = MeasureValue.objects.filter(
                    measure=measure,
                    pct=org, practice=None,
                    percentile__lte=p.percentiles['ccg']['10'] * 100,
                    month=p.month
                )
                if is_worst.count() == 0:
                    worst_measures = []
                    break
                else:
                    worst_measures.append(measure)

    # Where they're in the top 10% over the past six months, ordered by badness
    best_measures = []

    # Where they've slipped more than N centiles over period Y, overed
    # by most slippage. A triple of (slippage_from, slippage_to,
    # mesaure_id)
    fastest_worsening_measures = [()]

    # Top savings for CCG, where savings are greater than GBP1000 .
    top_savings = []

    total_possible_savings = 0
    return {
        'worst_measures': worst_measures,
        'best_measures': best_measures,
        'fastest_worsening_measures': fastest_worsening_measures,
        'top_savings': top_savings,
        'total_possible_savings': total_possible_savings}
