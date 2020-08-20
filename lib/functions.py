from django.core.mail.message import EmailMultiAlternatives
from django.conf import settings
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
import time
import requests

def send_mail_with_html(subject, html_message, to_email, from_email = None):
    if isinstance(to_email, str):
        to = [to_email]
    else:
        to = to_email
    msg = EmailMultiAlternatives(
        subject=subject,
        from_email=from_email,
        to=to, 
        reply_to=[settings.SMTP_REPLY_TO]
    )
    msg.attach_alternative(html_message, 'text/html')
    msg.send()

def my_login_required(function):
    def wrapper(request, *args, **kw):
        if not request.user.is_authenticated:
            return HttpResponseRedirect('/accounts/login')
        else:
            return function(request, *args, **kw)
    return wrapper


def get_mapillary_user(token):
    # omit the bbox if you want to retrieve all data your account can access, it will automatically limit to your subscription area
    url = 'https://a.mapillary.com/v3/me?client_id=' + settings.MAPILLARY_CLIENT_ID
    headers = {"Authorization": "Bearer {}".format(token)}
    response = requests.get(url, headers=headers)
    data = response.json()
    if 'message' in data and data['message'] == 'unauthorized':
        return None
    else:
        return data
