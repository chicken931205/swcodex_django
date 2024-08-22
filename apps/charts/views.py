from django.shortcuts import render
from apps.common.models import Sales
from django.core import serializers
import csv

# Create your views here.

def index(request):
    sales = serializers.serialize('json', Sales.objects.all())
    context = {
        'segment'  : 'charts',
        'parent'   : 'apps',
        'sales': sales
    }
    return render(request, 'pages/apps/charts.html', context)