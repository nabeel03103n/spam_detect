from django.shortcuts import render,redirect,HttpResponse
from . import models
import qrcode
from django.core.files.base import ContentFile
from io import BytesIO
import hashlib
import vt
from django.http import JsonResponse
from django.core.mail import send_mail
import requests

def send_email(request,email,subject,message):
    recipient_list = [email]
    send_mail(
        subject=subject,
        message=message,
        from_email='nabeelalikhan314@gmail.com',
        recipient_list=recipient_list,
        fail_silently=False,
    )
    return HttpResponse("Message Sent! Successfully")

def send_sms(phone_number,message):
    api_key = "e304cd3d0deca82bac6d856ba70f70d5530d9ff9b966ccc5"
    url = "https://api.smsmobileapi.com/sendsms/"
    payload = {
    "recipients": f"{phone_number}",
    "message": f"{message}",
    "apikey": f"{api_key}"
    }

    response = requests.post(url, data=payload)

    return response.text


def home(request):
    return render(request, 'home.html')

def qr(request):
    if request.method == "POST":
        link_for_qr = request.POST.get("input_link")
        
        # Check if QR already exists
        existing_qr = models.QR_genration.objects.filter(link=link_for_qr)
        
        if existing_qr.exists():
            # If QR already exists, pass the existing QR code(s) to the template
            return render(request, 'qr.html', {'objects': existing_qr})

        else:
            # Generate the QR code
            qr_image = qrcode.make(link_for_qr)

            # Save the QR code to an in-memory file
            buffer = BytesIO()
            qr_image.save(buffer, format="PNG")
            buffer.seek(0)

            # Generate a sanitized filename using a hash
            sanitized_filename = hashlib.md5(link_for_qr.encode()).hexdigest()[:10] + "_qr.png"

            # Create a new QR_genration object and save the image
            qr_instance = models.QR_genration(link=link_for_qr)
            qr_instance.image.save(sanitized_filename, ContentFile(buffer.read()), save=True)
            buffer.close()

            # Fetch the newly created QR code (not all QR codes)
            objects = models.QR_genration.objects.filter(link=link_for_qr)

            return render(request, 'qr.html', {'objects': objects})

    # Render the template for GET requests
    return render(request, 'qr.html', {'objects': []})


def link_detection(request):
    if request.method == "POST":
        # Initialize the VirusTotal client
        client = vt.Client("480e3b4565c3444d7c425e3832ab21a4ee55fbbf9738ea3385108e0d1e6b9177")
        link = request.POST.get('link')  # Get the link from the POST request

        try:
            # Get the URL ID for the provided link
            url_id = vt.url_id(link)
            # Fetch the URL object from VirusTotal
            url_object = client.get_object(f"/urls/{url_id}")
            
            # Access the `last_analysis_stats` dictionary
            analysis_stats = url_object.last_analysis_stats # Dict
            analysis_stats['url'] = link
            print(analysis_stats)  # Debug: Check the type of the stats
            # print(type(analysis_stats))  # Debug: Check the type of the stats

            model = models.link_detection.objects.create(**analysis_stats)

            # Render the link details in the template
            return render(request, "link_detection.html", {"link_details": analysis_stats,"url":link})
        
        except Exception as e:
            print(f"Error: {e}")  # Log the error for debugging purposes
            return render(request, "link_detection.html", {"error": "An error occurred while processing the link."})
    return render(request, "link_detection.html")

from django.core.files.storage import FileSystemStorage
import os

def file_detection(request):
    if request.method == "POST" and 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)  # Save file to media folder
        full_file_path = fs.path(file_path)

        try:
            # Use VirusTotal API to scan the file
            with open(full_file_path, "rb") as f:
                client = vt.Client("480e3b4565c3444d7c425e3832ab21a4ee55fbbf9738ea3385108e0d1e6b9177")
                analysis = client.scan_file(f)
                client.close()

            # Wait for the analysis to complete and fetch the results
            analysis_id = analysis.id
            with vt.Client("480e3b4565c3444d7c425e3832ab21a4ee55fbbf9738ea3385108e0d1e6b9177") as client:
                result = client.get_object(f"/analyses/{analysis_id}")
                stats = result.stats  # Retrieve detailed scan statistics

            # Prepare data for rendering
            context = {
                "message": "File uploaded and scanned successfully!",
                "file_name": uploaded_file.name,
                "scan_results": stats,  # Pass detailed scan results to the template
            }
        except Exception as e:
            context = {"message": f"Error during file scan: {str(e)}"}
        finally:
            # Remove the uploaded file after scanning
            if os.path.exists(full_file_path):
                os.remove(full_file_path)

        return render(request, "file_detection.html", context)

    return render(request, "file_detection.html", {"message": "Please upload a file."})

import pyshorteners
from . import web_scrap_for_url_shortner

def shorten_url(request):
    short_url = None  # Default value if no URL is shortened
    if request.method == "POST":
        
        original_url = request.POST.get("original_url")
        existing_ulr = models.url_shortener.objects.filter(original_url=original_url).values_list('shorten_url',flat=True)

        if existing_ulr:
            return render(request, "url_shortener.html", {"short_url": existing_ulr[0]})

        else:
            if original_url:
                # Use pyshorteners to generate a shortened URL
                s = pyshorteners.Shortener()
                short_url = s.tinyurl.short(original_url)
                # short_url = web_scrap_for_url_shortner.long_url(short_url)

                urls = {
                    'original_url':original_url,
                    'shorten_url':short_url
                }

                
                model = models.url_shortener.objects.create(**urls)
                return render(request, "url_shortener.html", {"short_url": short_url})

    return render(request, "url_shortener.html", {"short_url": 'Please Enter a url'})

def anonymous_mail(request):

    if request.method == "POST":
        email_to = request.POST.get('email_to')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        return HttpResponse(send_email(request,email_to,subject,message))


    return render(request,'anonymous_mail.html')

def contact(request):

    if request.method == "POST":
        user_data = {
            "name":request.POST.get("name"),
            "email":request.POST.get("email"),
            "phone":request.POST.get("phone"),
            "message":request.POST.get("message"),
                     }
        
        ins = models.Contact.objects.create(**user_data)
        ins.save()

    return render(request,'contact.html')

def anonymous_sms(request):
    if request.method == "POST":
        phone = request.POST.get("phone")
        message = request.POST.get("msg")
        response = send_sms(f"+91{phone}",message)
        return render(request,"anonymous_sms.html",{'response':response})

    return render(request,"anonymous_sms.html",{'response':'Failed to fetch'})