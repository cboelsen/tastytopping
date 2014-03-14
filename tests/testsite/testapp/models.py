from django.db import models
from django.contrib.auth.models import User


class Test(models.Model):
    path   = models.CharField(max_length=255, unique=True)
    rating = models.IntegerField(default=50)
    date   = models.DateTimeField('date', null=True)
    title  = models.CharField(max_length=255, null=True)
    text   = models.TextField(null=True, blank=True)
    created_by = models.OneToOneField(User, null=True)
    date_only = models.DateField('date', null=True)


class Tree(models.Model):
    number = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')


class TestContainer(models.Model):
    test = models.OneToOneField(Test, null=True)


class InvalidField(models.Model):
    name = models.CharField(max_length=255, unique=True)
    limit = models.IntegerField()


class NoUniqueInitField(models.Model):
    name = models.CharField(max_length=255)
    num = models.IntegerField()
