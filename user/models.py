from django.db import models

class QR_genration(models.Model):
    link = models.URLField(max_length=200)
    image = models.ImageField(upload_to='qr/')  # QR codes will be stored in the 'media/qr/' directory

    def __str__(self):
        return self.link

class UploadedFile(models.Model):
    file = models.FileField(upload_to='file_detection/')
    uploaded_at = models.DateTimeField(auto_now_add=True)


import string
import random

class url_shortener(models.Model):
    original_url = models.URLField(max_length=200)
    shorten_url = models.URLField(max_length=200)

    def __str__(self):
        return self.original_url