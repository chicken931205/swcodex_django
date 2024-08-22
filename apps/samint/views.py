from django.shortcuts import render, redirect, get_object_or_404
from apps.users.models import Profile
from apps.users.forms import ProfileForm, QuillFieldForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password
from django.contrib import messages


# Create your views here.

def index(request):
    profile = get_object_or_404(Profile, user=request.user)
    if profile.dark_mode:
        profile.dark_mode = False
    else:
        profile.dark_mode = True
    
    profile.save()

    return redirect(request.META.get('HTTP_REFERER'))