from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Le site access4all est actuellement en construction.")
