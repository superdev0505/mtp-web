## Python packages
from datetime import datetime
import json
import re
from binascii import a2b_base64
import os

## Django Packages
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.http import (
    Http404, HttpResponse, JsonResponse, HttpResponsePermanentRedirect, HttpResponseRedirect,
)
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib import messages
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.db.models import Avg, Count, Min, Sum
from django.db.models.expressions import F, Window
from django.db.models.functions.window import RowNumber
from django.contrib.gis.geos import Point, Polygon, MultiPolygon, LinearRing, LineString
## Custom Libs ##
from lib.functions import *

## Project packages
from accounts.models import CustomUser, MapillaryUser
from tour.models import Tour, TourSequence
from guidebook.models import Guidebook, Scene
import requests
import tempfile
from django.core import files
## App packages

# That includes from .models import *
from .forms import * 

############################################################################

MAIN_PAGE_DESCRIPTION = "Sequences are collections of images continuously captured by a user at a give time. Browse those created by others, or import your own from Mapillary."
IMPORT_PAGE_DESCRIPTION = "First start by choosing the month your sequences we're captured. If they were taken over multiple months, don't worry, once you've selected all the ones you want from the current month you can change this filter to add more."

############################################################################

def index(request):
    return redirect('sequence.sequence_list')

def testImageDownload(request):
    image_key = request.GET.get('image_key')
    image = Image.objects.filter(image_key=image_key)[:1]
    if image.count() == 0:
        return HttpResponse('The image is not existing.')
    image_urls = [
        'https://a.mapillary.com/v3/images/{}}/download_original?client_id={}'.format(image_key, settings.MAPILLARY_CLIENT_ID),
    ]
    headers = {"Authorization": "Bearer {}".format(request.user.mapillary_access_token)}
    for image_url in image_urls:
        # Steam the image from the url
        request = requests.get(image_url, stream=True, headers=headers)

        # Was the request OK?
        if request.status_code != requests.codes.ok:
            # Nope, error handling, skip file etc etc etc
            continue

        # Get the filename from the url, used for saving later
        file_name = image_url.split('/')[-1]

        # Create a temporary file
        lf = tempfile.NamedTemporaryFile()

        # Read the streamed image in sections
        for block in request.iter_content(1024 * 8):

            # If no more file then stop
            if not block:
                break

            # Write image block to temporary file
            lf.write(block)

        # Create the model you want to save the image to
        # image = Image()
        image.image.save(file_name, files.File(lf))
        # Save the temporary image to the model#
        # This saves the model so be sure that is it valid
        # image.image.save(file_name, files.File(lf))

def import_sequence(request):
    map_user_data = check_mapillary_token(request.user)
    if not map_user_data:
        return redirect(settings.MAPILLARY_AUTHENTICATION_URL)
    else:
        return redirect('sequence.import_sequence_list')

def sequence_list(request):
    sequences = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = SequenceSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_make = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']
            username = form.cleaned_data['username']

            sequences = Sequence.objects.all().filter(
                is_published=True
            )
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
            if transport_type and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    sequences = sequences.filter(transport_type_id__in=types)
                else:
                    sequences = sequences.filter(transport_type_id=transport_type)
            if username and username != '':
                users = CustomUser.objects.filter(username__contains=username)
                sequences = sequences.filter(user__in=users)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)

    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True)
        form = SequenceSearchForm()

    paginator = Paginator(sequences.order_by('-created_at'), 5)

    try:
        pSequences = paginator.page(page)
    except PageNotAnInteger:
        pSequences = paginator.page(1)
    except EmptyPage:
        pSequences = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pSequences.number < 4:
            first_num = 1
            last_num = 7
        elif pSequences.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pSequences.number - 3
            last_num = pSequences.number + 3
    pSequences.paginator.pages = range(first_num, last_num + 1)
    pSequences.count = len(pSequences)

    for i in range(len(pSequences)):
        tour_sequences = TourSequence.objects.filter(sequence_id=pSequences[i].pk)
        if tour_sequences is None or not tour_sequences:
            pSequences[i].tour_count = 0
        else:
            pSequences[i].tour_count = tour_sequences.count()


    content = {
        'sequences': pSequences,
        'form': form,
        'pageName': 'Sequences',
        'pageTitle': 'Sequences',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'sequence/list.html', content)

@my_login_required
def my_sequence_list(request):
    sequences = None
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1
        form = SequenceSearchForm(request.GET)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_make = form.cleaned_data['camera_make']
            tags = form.cleaned_data['tag']
            transport_type = form.cleaned_data['transport_type']

            sequences = Sequence.objects.all().filter(
                user=request.user
            )
            if name and name != '':
                sequences = sequences.filter(name__contains=name)
            if camera_make and camera_make != '':
                sequences = sequences.filter(camera_make__contains=camera_make)
            if transport_type and transport_type != 0 and transport_type != '':
                children_trans_type = TransType.objects.filter(parent_id=transport_type)
                if children_trans_type.count() > 0:
                    types = []
                    types.append(transport_type)
                    for t in children_trans_type:
                        types.append(t.pk)
                    sequences = sequences.filter(transport_type_id__in=types)
                else:
                    sequences = sequences.filter(transport_type_id=transport_type)
            if len(tags) > 0:
                for tag in tags:
                    sequences = sequences.filter(tag=tag)

    if sequences == None:
        sequences = Sequence.objects.all().filter(is_published=True)
        form = SequenceSearchForm()

    paginator = Paginator(sequences.order_by('-created_at'), 5)

    try:
        pSequences = paginator.page(page)
    except PageNotAnInteger:
        pSequences = paginator.page(1)
    except EmptyPage:
        pSequences = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pSequences.number < 4:
            first_num = 1
            last_num = 7
        elif pSequences.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pSequences.number - 3
            last_num = pSequences.number + 3
    pSequences.paginator.pages = range(first_num, last_num + 1)
    pSequences.count = len(pSequences)

    for i in range(len(pSequences)):
        tour_sequences = TourSequence.objects.filter(sequence_id=pSequences[i].pk)
        if tour_sequences is None or not tour_sequences:
            pSequences[i].tour_count = 0
        else:
            pSequences[i].tour_count = tour_sequences.count()
    form._my(request.user.username)
    content = {
        'sequences': pSequences,
        'form': form,
        'pageName': 'My Sequences',
        'pageTitle': 'My Sequences',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page
    }
    return render(request, 'sequence/list.html', content)

def sequence_detail(request, unique_id):
    sequence = get_object_or_404(Sequence, unique_id=unique_id)
    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        if page is None:
            page = 1

    geometry_coordinates_ary = sequence.geometry_coordinates_ary
    coordinates_image = sequence.coordinates_image
    coordinates_cas = sequence.coordinates_cas

    images = []

    for i in range(len(coordinates_image)):
        images.append(
            {
                'lat': geometry_coordinates_ary[i][0],
                'lng': geometry_coordinates_ary[i][1],
                'key': coordinates_image[i],
                'cas': coordinates_cas[i]
            }
        )

    view_points = 0
    imgs = Image.objects.filter(image_key=coordinates_image[0])
    if imgs.count() > 0:
        i_vs = ImageViewPoint.objects.filter(image=imgs[0])
        view_points = i_vs.count()

    addSequenceForm = AddSequeceForm(instance=sequence)
    content = {
        'sequence': sequence,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': sequence.description,
        'first_image': images[0],
        'page': page,
        'view_points': view_points,
        'addSequenceForm': addSequenceForm
    }
    return render(request, 'sequence/detail.html', content)

@my_login_required
def sequence_delete(request, unique_id):
    sequence = get_object_or_404(Sequence, unique_id=unique_id)
    if request.method == "POST":
        if sequence.user != request.user:
            messages.error(request, 'The sequence does not exist or has no access.')
            return redirect('sequence.index')
        name = sequence.name
        sequence.name = ''
        sequence.description = ''
        sequence.transport_type = None
        tags = sequence.tag.all()
        for tag in tags:
            sequence.tag.remove(tag)
        sequence.is_published = False
        sequence.save()

        seq_likes = SequenceLike.objects.filter(sequence=sequence)

        if seq_likes.count() > 0:
            for s in seq_likes:
                s.delete()

        tour_sequences = TourSequence.objects.filter(sequence=sequence)

        if tour_sequences.count() > 0:
            for t_seq in tour_sequences:
                t_seq.delete()

        messages.success(request, '"{}" is deleted successfully.'.format(name))
        return redirect('sequence.index')

    messages.error(request, 'The sequence does not exist or has no access.')
    return redirect('sequence.index')

def ajax_save_sequence(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist or has no access.'
        })
    if request.method == "POST":
        form = AddSequeceForm(request.POST)

        if form.is_valid():
            sequence = Sequence.objects.get(unique_id=unique_id)

            if not sequence or sequence is None or sequence.user != request.user:
                return JsonResponse({
                    'status': 'failed',
                    'message': 'The Sequence does not exist or has no access.'
                })

            sequence.name = form.cleaned_data['name']
            sequence.description = form.cleaned_data['description']
            sequence.transport_type = form.cleaned_data['transport_type']
            if form.cleaned_data['tag'].count() > 0:
                for tag in form.cleaned_data['tag']:
                    sequence.tag.add(tag)
                for tag in sequence.tag.all():
                    if not tag in form.cleaned_data['tag']:
                        sequence.tag.remove(tag)
            sequence.save()

            tags = []
            if sequence.tag.all().count() > 0:
                for tag in sequence.tag.all():
                    if not tag or tag is None:
                        continue
                    tags.append(tag.name)

            transport_parent_html = render_to_string(
                'sequence/transport_parent_box.html',
                {'sequence': sequence},
                request
            )

            transport_html = render_to_string(
                'sequence/transport_box.html',
                {'sequence': sequence},
                request
            )


            return JsonResponse({
                'status': 'success',
                'message': 'This sequence is updated successfully.',
                'sequence': {
                    'name': sequence.name,
                    'description': sequence.description,
                    'transport_type': sequence.transport_type.name,
                    'transport_parent_html': transport_parent_html,
                    'transport_html': transport_html,
                    'tags': tags
                }
            })
        else:
            errors = []
            for field in form:
                for error in field.errors:
                    errors.append(field.name + ': ' + error)
            return JsonResponse({
                'status': 'failed',
                'message': '<br>'.join(errors)
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'The sequence does not exist or has no access.'
    })

def sort_by_captured_at(item):
    return str(item['properties']['captured_at'])

@my_login_required
def import_sequence_list(request):
    sequences = []
    search_form = TransportSearchForm()
    action = 'filter'
    if request.method == "GET":
        month = request.GET.get('month')
        page = request.GET.get('page')
        action = request.GET.get('action')
        if action is None:
            action = 'filter'

        if not month is None:
            search_form.set_month(month)

            y = month.split('-')[0]
            m = month.split('-')[1]

            map_user = MapillaryUser.objects.get(user=request.user)
            if map_user is None:
                return redirect('home')

            if page is None:
                start_time = month + '-01'

                if m == '12':
                    y = str(int(y) + 1)
                    m = '01'
                else:
                    if int(m) < 9:
                        m = '0' + str(int(m) + 1)
                    else:
                        m = str(int(m) + 1)
                end_time = y + '-' + m + '-01'
                per_page = 1000

                url = 'https://a.mapillary.com/v3/sequences?page=1&per_page={}&client_id={}&userkeys={}&start_time={}&end_time={}'.format(
                    per_page,
                    settings.MAPILLARY_CLIENT_ID,
                    map_user.key,
                    start_time,
                    end_time
                )
                response = requests.get(url)
                data = response.json()
                features = data['features']
                features.sort(key=sort_by_captured_at)
                request.session['sequences'] = features

                page = 1
            if request.session['sequences'] is None or not request.session['sequences']:
                request.session['sequences'] = []

            sequences_ary = []

            for seq in request.session['sequences']:
                seq_s = Sequence.objects.filter(seq_key=seq['properties']['key'])[:1]
                if seq_s.count() == 0:
                    sequences_ary.append(seq)

            paginator = Paginator(sequences_ary, 5)
            try:
                sequences = paginator.page(page)
            except PageNotAnInteger:
                sequences = paginator.page(1)
            except EmptyPage:
                sequences = paginator.page(paginator.num_pages)

            first_num = 1
            last_num = paginator.num_pages
            if paginator.num_pages > 7:
                if sequences.number < 4:
                    first_num = 1
                    last_num = 7
                elif sequences.number > paginator.num_pages - 3:
                    first_num = paginator.num_pages - 6
                    last_num = paginator.num_pages
                else:
                    first_num = sequences.number - 3
                    last_num = sequences.number + 3
            sequences.paginator.pages = range(first_num, last_num + 1)
            sequences.count = len(sequences)

            for i in range(len(sequences)):
                seq = Sequence.objects.filter(seq_key=sequences[i]['properties']['key'])[:1]
                if seq.count() > 0:
                    sequences[i]['unique_id'] = str(seq[0].unique_id)
                    sequences[i]['name'] = seq[0].name
                    sequences[i]['description'] = seq[0].description
                    if seq[0].transport_type is None:
                        sequences[i]['transport_type'] = ''
                    else:
                        sequences[i]['transport_type'] = seq[0].transport_type.parent.name + ' - ' +seq[0].transport_type.name
                    sequences[i]['tags'] = seq[0].getTags()
                else:
                    sequences[i]['unique_id'] = None

                sequences[i]['image_count'] = len(sequences[i]['properties']['coordinateProperties']['image_keys'])
                sequences[i]['captured_at'] = sequences[i]['properties']['captured_at']
                sequences[i]['camera_make'] = sequences[i]['properties']['camera_make']
                sequences[i]['created_at'] = sequences[i]['properties']['created_at']
                sequences[i]['seq_key'] = sequences[i]['properties']['key']
                sequences[i]['pano'] = sequences[i]['properties']['pano']
                sequences[i]['user_key'] = sequences[i]['properties']['user_key']
                sequences[i]['username'] = sequences[i]['properties']['username']
                sequences[i]['geometry_coordinates_ary'] = sequences[i]['geometry']['coordinates']


    addSequenceForm = AddSequeceForm()

    all_transport_types = []
    transport_types = TransType.objects.all()
    for type in transport_types:
        all_transport_types.append({'id': type.pk, 'name': type.name})
    content = {
        'search_form': search_form,
        'seq_count': len(sequences),
        'sequences': sequences,
        'pageName': 'Sequences',
        'pageTitle': 'Import Sequences',
        'pageDescription': IMPORT_PAGE_DESCRIPTION,
        'addSequenceForm': addSequenceForm,
        'all_transport_types': all_transport_types,
        'action': action,
        'page': page
    }
    return render(request, 'sequence/import_list.html', content)

def ajax_import(request, seq_key):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })
    if request.method == 'POST':

        # form = AddSequeceForm(request.POST)
        # if form.is_valid():
        # for unique_id in sequence_json.keys():
        #     sequence = Sequence.objects.get(unique_id=unique_id)
        #     if sequence is None:
        #         continue
        #     if sequence_json[unique_id]['name'] == '' or sequence_json[unique_id]['description'] == '' or sequence_json[unique_id]['transport_type'] == 0 or len(sequence_json[unique_id]['tags']) == 0:
        #         continue
        form = AddSequeceForm(request.POST)
        if form.is_valid():

            # for i in range(len(request.session['sequences'])):
            for feature in request.session['sequences']:
                # feature = request.session['sequences'][i]
                if feature['properties']['key'] == seq_key:
                    properties = feature['properties']
                    geometry = feature['geometry']
                    sequence = Sequence.objects.filter(seq_key=seq_key)[:1]

                    if sequence.count() > 0:
                        continue
                    else:
                        sequence = Sequence()
                    sequence.user = request.user
                    if 'camera_make' in properties:
                        sequence.camera_make = properties['camera_make']
                    sequence.captured_at = properties['captured_at']
                    if 'created_at' in properties:
                        sequence.created_at = properties['created_at']
                    sequence.seq_key = properties['key']
                    if 'pano' in properties:
                        sequence.pano = properties['pano']
                    if 'user_key' in properties:
                        sequence.user_key = properties['user_key']
                    if 'username' in properties:
                        sequence.username = properties['username']
                    sequence.geometry_coordinates_ary = geometry['coordinates']
                    sequence.image_count = len(geometry['coordinates'])

                    lineString = LineString()
                    firstPoint = None
                    if sequence.image_count == 0:
                        firstPoint = Point(sequence.geometry_coordinates_ary[0][0], sequence.geometry_coordinates_ary[0][1])
                        lineString = LineString(firstPoint.coords, firstPoint.coords)
                    else:
                        for i in range(len(sequence.geometry_coordinates_ary)):
                            coor = sequence.geometry_coordinates_ary[i]
                            if i == 0:
                                firstPoint = Point(coor[0], coor[1])
                                continue
                            point = Point(coor[0], coor[1])
                            if i == 1:
                                lineString = LineString(firstPoint.coords, point.coords)
                            else:
                                lineString.append(point.coords)

                    sequence.geometry_coordinates = lineString

                    sequence.coordinates_cas = properties['coordinateProperties']['cas']
                    sequence.coordinates_image = properties['coordinateProperties']['image_keys']
                    if 'private' in properties:
                        sequence.is_privated = properties['private']

                    sequence.name = form.cleaned_data['name']
                    sequence.description = form.cleaned_data['description']
                    sequence.transport_type = form.cleaned_data['transport_type']
                    sequence.is_published = True
                    sequence.save()

                    if form.cleaned_data['tag'].count() > 0:
                        for tag in form.cleaned_data['tag']:
                            sequence.tag.add(tag)
                        for tag in sequence.tag.all():
                            if not tag in form.cleaned_data['tag']:
                                sequence.tag.remove(tag)

                    # messages.success(request, "Sequences successfully imported.")
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Sequence successfully imported.',
                        'unique_id': str(sequence.unique_id)
                    })
        else:
            errors = []
            for field in form:
                for error in field.errors:
                    errors.append(field.name + ': ' + error)
            return JsonResponse({
                'status': 'failed',
                'message': '<br>'.join(errors)
            })
    return JsonResponse({
        'status': 'failed',
        'message': 'Sequence was not imported.'
    })

def ajax_add_ele(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence does not exist.'
        })

    eles = request.POST.get('eles')
    if eles is None:
        return JsonResponse({
            'status': 'failed',
            'message': 'The ele is empty.'
        })

    eles_ary = eles.split(',')
    sequence.coordinates_ele = eles_ary

    sequence.save()
    return JsonResponse({
        'status': 'success',
        'message': 'Ele is saved.'
    })

def ajax_sequence_check_publish(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence does not exist.'
        })

    if sequence.user != request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This sequence is not created by you.'
        })

    if sequence.is_published:
        sequence.is_published = False
        message = 'Unpublished'
    else:
        sequence.is_published = True
        message = 'Published'
    sequence.save()
    return JsonResponse({
        'status': 'success',
        'message': message,
        'is_published': sequence.is_published
    })

def ajax_sequence_check_like(request, unique_id):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence does not exist.'
        })

    if sequence.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'This sequence is created by you.'
        })

    sequence_like = SequenceLike.objects.filter(sequence=sequence, user=request.user)
    if sequence_like:
        for g in sequence_like:
            g.delete()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unliked',
            'is_checked': False,
            'liked_count': liked_count
        })
    else:
        sequence_like = SequenceLike()
        sequence_like.sequence = sequence
        sequence_like.user = request.user
        sequence_like.save()
        liked_sequence = SequenceLike.objects.filter(sequence=sequence)
        if not liked_sequence:
            liked_count = 0
        else:
            liked_count = liked_sequence.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Liked',
            'is_checked': True,
            'liked_count': liked_count
        })

def ajax_get_image_detail(request, unique_id, image_key):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })
    images = Image.objects.filter(seq_key=sequence.seq_key, image_key=image_key)
    if images.count() > 0:
        image = images[0]
        if image.ele == 0:
            try:
                url = 'https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/tilequery/{},{}.json?layers=contour&limit=50&access_token={}'.format(
                    image.lng, image.lat, settings.MAPBOX_PUBLISH_TOKEN)
                response = requests.get(url)
                ele_data = response.json()
                allFeatures = ele_data['features']
                elevations = []
                for feature in allFeatures:
                    elevations.append(feature['properties']['ele'])
                highestElevation = max(elevations)
                image.ele = highestElevation
                image.save()
            except:
                pass
    else:
        image = Image()

        try:
            url = 'https://a.mapillary.com/v3/images/{}?client_id={}'.format(image_key, settings.MAPILLARY_CLIENT_ID)
            response = requests.get(url)
            data = response.json()
        except:
            return JsonResponse({
                'status': 'failed',
                'message': "Image key error."
            })
        properties = data['properties']
        keys = properties.keys()
        if 'camera_make' in keys:
            image.camera_make = properties['camera_make']
        if 'camera_model' in keys:
            image.camera_model = properties['camera_model']
        if 'ca' in keys:
            image.cas = properties['ca']
        if 'captured_at' in keys:
            image.captured_at = properties['captured_at']
        if 'sequence_key' in keys:
            image.seq_key = properties['sequence_key']
        if 'user_key' in keys:
            image.user_key = properties['user_key']
        if 'key' in keys:
            image.image_key = properties['key']
        if 'pano' in keys:
            image.pano = properties['pano']
        if 'username' in keys:
            image.username = properties['username']
        if 'organization_key' in keys:
            image.organization_key = properties['organization_key']
        if 'private' in keys:
            image.is_privated = properties['private']

        image.lng = data['geometry']['coordinates'][0]
        image.lat = data['geometry']['coordinates'][1]
        try:
            url = 'https://api.mapbox.com/v4/mapbox.mapbox-terrain-v2/tilequery/{},{}.json?layers=contour&limit=50&access_token={}'.format(image.lng, image.lat, settings.MAPBOX_PUBLISH_TOKEN)
            response = requests.get(url)
            ele_data = response.json()
            allFeatures = ele_data['features']
            elevations = []
            for feature in allFeatures:
                elevations.append(feature['properties']['ele'])
            highestElevation = max(elevations)
            print(highestElevation)
            image.ele = highestElevation
        except:
            pass

        image.is_uploaded = True
        image.is_mapillary = True

        image.user = sequence.user
        image.save()

    view_points = ImageViewPoint.objects.filter(image=image)
    scenes = Scene.objects.filter(image_key=image_key)
    content = {
        'image': image,
        'view_points': view_points.count(),
        'guidebook_count': scenes.count()
    }
    image_detail_box_html = render_to_string(
        'sequence/image_detail_box.html',
        content,
        request
    )
    return JsonResponse({
        'image_detail_box_html': image_detail_box_html,
        'status': 'success',
        'message': "",
        'view_points': view_points.count()
    })

def ajax_add_ele_in_image(request, unique_id, image_key):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })
    images = Image.objects.filter(image_key=image_key)
    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })
    image = images[0]

    ele = request.POST.get('ele')
    if ele is None:
        return JsonResponse({
            'status': 'failed',
            'message': 'ele is empty'
        })
    image.ele = ele
    image.save()

    return JsonResponse({
        'status': 'success',
        'message': "success",
    })

def ajax_get_image_list(request, unique_id):
    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    page = 1
    if request.method == "GET":
        page = request.GET.get('page')
        print('page', page)
        if page is None:
            page = 1

    geometry_coordinates_ary = sequence.geometry_coordinates_ary
    coordinates_image = sequence.coordinates_image
    coordinates_cas = sequence.coordinates_cas

    images = []

    for i in range(len(coordinates_image)):
        images.append(
            {
                'lat': geometry_coordinates_ary[i][1],
                'lng': geometry_coordinates_ary[i][0],
                'key': coordinates_image[i],
                'cas': coordinates_cas[i]
            }
        )

    paginator = Paginator(images, 20)

    try:
        pImages = paginator.page(page)
    except PageNotAnInteger:
        pImages = paginator.page(1)
    except EmptyPage:
        pImages = paginator.page(paginator.num_pages)

    first_num = 1
    last_num = paginator.num_pages
    if paginator.num_pages > 7:
        if pImages.number < 4:
            first_num = 1
            last_num = 7
        elif pImages.number > paginator.num_pages - 3:
            first_num = paginator.num_pages - 6
            last_num = paginator.num_pages
        else:
            first_num = pImages.number - 3
            last_num = pImages.number + 3
    pImages.paginator.pages = range(first_num, last_num + 1)
    pImages.count = len(pImages)
    origin_images = []
    for i in range(pImages.count):
        image = Image.objects.filter(image_key=pImages[i]['key'])[:1]
        if image.count() == 0:
            origin_images.append(None)
        else:
            origin_images.append(image[0])

            view_points = ImageViewPoint.objects.filter(image=image[0])
            scenes = Scene.objects.filter(image_key=image[0].image_key)
            pImages[i]['view_points'] = view_points.count()
            pImages[i]['guidebooks'] = scenes.count()

    addSequenceForm = AddSequeceForm(instance=sequence)


    content = {
        'sequence': sequence,
        'images': pImages,
        'origin_images': origin_images,
        'pageName': 'Sequence Detail',
        'pageTitle': sequence.name + ' - Sequence',
        'pageDescription': MAIN_PAGE_DESCRIPTION,
        'page': page,
        'first_image': pImages[0],
        'addSequenceForm': addSequenceForm
    }

    image_list_box_html = render_to_string(
        'sequence/image_list_box.html',
        content,
        request
    )

    return JsonResponse({
        'image_list_box_html': image_list_box_html,
        'page': page,
        'status': 'success',
        'message': ''
    })

def ajax_image_mark_view(request, unique_id, image_key):
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'failed',
            'message': "You can't change the status."
        })

    sequence = Sequence.objects.get(unique_id=unique_id)
    if not sequence:
        return JsonResponse({
            'status': 'failed',
            'message': 'The Sequence does not exist.'
        })

    if sequence.user == request.user:
        return JsonResponse({
            'status': 'failed',
            'message': 'The sequence and image are imported by you.'
        })

    if not sequence.is_published:
        if not request.user.is_authenticated or request.user != sequence.user:
            return JsonResponse({
                'status': 'failed',
                'message': "You can't access this sequence."
            })

    images = Image.objects.filter(seq_key=sequence.seq_key, image_key=image_key)

    if images.count() == 0:
        return JsonResponse({
            'status': 'failed',
            'message': "The Image does not exist."
        })

    image = images[0]

    image_view_points = ImageViewPoint.objects.filter(image=image, user=request.user)
    if image_view_points.count() > 0:
        for v in image_view_points:
            v.delete()
        marked_images = ImageViewPoint.objects.filter(image=image)
        if not marked_images:
            view_points = 0
        else:
            view_points = marked_images.count()
        return JsonResponse({
            'status': 'success',
            'message': 'Unmarked',
            'is_marked': False,
            'view_points': view_points
        })
    else:
        image_view_point = ImageViewPoint()
        image_view_point.image = image
        image_view_point.user = request.user
        image_view_point.save()
        marked_images = ImageViewPoint.objects.filter(image=image)
        if not marked_images:
            view_points = 0
        else:
            view_points = marked_images.count()
        return JsonResponse({

            'status': 'success',
            'message': 'Marked',
            'is_marked': True,
            'view_points': view_points
        })

