## Django Packages
from django.contrib.gis.db import models
from django.contrib.auth import (
    REDIRECT_FIELD_NAME, get_user_model, login as auth_login,
    logout as auth_logout, update_session_auth_hash,
)
from datetime import datetime
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse

## Python Packages
import uuid

UserModel = get_user_model()

def image_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'guidebook/{0}/cover_image/{1}'.format(instance.unique_id, filename)

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(default=None, blank=True, null=True)
    is_actived = models.BooleanField(default=True)

    def __str__(self):
        return self.name

def getAllTags():
    items = Tag.objects.filter(is_actived=True)
    itemsTuple = ()
    for item in items:
        itemsTuple = itemsTuple + ((item.pk, item.name),)
    print(itemsTuple)
    return itemsTuple

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default=None, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'



class Guidebook(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    cover_image = models.ImageField(upload_to=image_directory_path, null=True)
    tag = ArrayField(models.CharField(default='0', max_length=6), null=True)
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

    def get_absolute_url(self):
        return reverse('guidebook.guidebook_detail', kwargs={'unique_id': str(self.unique_id)})

    def getScenes(self):
        scenes = Scene.objects.filter(guidebook=self).order_by('sort')
        return scenes

    def getScenePositions(self):
        scenes = Scene.objects.filter(guidebook=self)
        positions = []
        if scenes and scenes.count() > 0:
            for scene in scenes:
                position = [scene.lat, scene.lng]
                positions.append(position)
        return positions

    def getFirstSceneKey(self):
        scenes = Scene.objects.filter(guidebook=self)
        if scenes and scenes.count() > 0:
            firstScene = scenes[0]
            return firstScene.image_key
        else:
            return ''

    def getSceneCount(self):
        scenes = Scene.objects.filter(guidebook=self)
        return scenes.count()

    def getLikeCount(self):
        liked_guidebook = GuidebookLike.objects.filter(guidebook=self)
        if not liked_guidebook:
            return 0
        else:
            return liked_guidebook.count()

    def getShortDescription(self):
        description = self.description
        if len(description) > 100:
            return description[0:100] + '...'
        else:
            return description

    def getTagStr(self):
        tags = []
        if self.tag is None:
            return ''
        for t in self.tag:
            tag = Tag.objects.get(pk=t)
            if tag and tag.is_actived:
                tags.append(tag.name)

        if len(tags) > 0:
            return ', '.join(tags)
        else:
            return ''

    def getTags(self):
        tags = []
        if self.tag is None:
            return []
        for t in self.tag:
            tag = Tag.objects.get(pk=t)
            if tag and tag.is_actived:
                tags.append(tag.name)
        return tags


class GuidebookLike(models.Model):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    guidebook = models.ForeignKey(Guidebook, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=datetime.now, blank=True)
    updated_at = models.DateTimeField(default=datetime.now, blank=True)

class POICategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(default=None, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'POI Categories'

class Scene(models.Model):
    guidebook = models.ForeignKey(Guidebook, on_delete=models.CASCADE)
    image_key = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    sort = models.IntegerField(default=1, null=True)
    image_url = models.CharField(max_length=100, null=True)


class PointOfInterest(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, default='')
    description = models.TextField(default='')
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    category = models.ForeignKey(POICategory, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return self.title








