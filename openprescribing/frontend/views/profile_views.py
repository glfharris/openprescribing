from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

def index(request):
    #sections = Section.objects.all()
    #context = {
    #    'sections': sections
    #}
    context = {}
    return render(request, 'profile/index.html', context)
