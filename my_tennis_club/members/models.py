from django.db import models

# Create your models here.


class BlastEmail(models.Model):
    email = models.CharField(max_length=255, unique=True)
    status = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'blastemail'

    def __str__(self):
        return self.email


class LastVisitedUrl(models.Model):
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'last_visited_urls'

    def __str__(self):
        return self.url


class ControlFlag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=False)

    class Meta:
        db_table = 'control_flags'

    def __str__(self):
        return self.name


class SkipExtension(models.Model):
    extension = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skip_extensions'


class SkipSite(models.Model):
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skip_sites'


class VisitedUrls(models.Model):
    url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'visited_urls'

    def __str__(self):
        return self.url
