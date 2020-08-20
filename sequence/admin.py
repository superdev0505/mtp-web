## Django Packages
from django.contrib import admin
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.urls import reverse
from django.urls import path
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string

## Custom Libs ##
from lib.functions import send_mail_with_html

## App packages
from .models import *


############################################################################


class TransportTypeAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )


class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description'
    )

class SequenceAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
        'camera_make',
        'seq_key',
        'pano',
        'user_key',
        'username',
        'name',
        'description'
    )

class TourAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
    )

class TourTagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'description',
    )

admin.site.register(TransportType, TransportTypeAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(TourTag, TourTagAdmin)
admin.site.register(Tour, TourAdmin)
admin.site.register(Sequence, SequenceAdmin)
