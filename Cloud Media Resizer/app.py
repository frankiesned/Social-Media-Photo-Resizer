import os
import tempfile
from PIL import Image
from google.cloud import storage
import functions_framework

#https://blog.hootsuite.com/social-media-image-sizes-guide/
#for now we will just resize, if need to add crop, we can make an option on the html to choose between crop and resize
#facebook                VERTICAL POST              REELS & STORY          SQAURE      LANDSCAPE
#linkedin                                                                                                               SQAURE                                LANDSCAPE     VERTICAL
#twitter/X                                                                  POST                   LANDSCAPE POST                  LANDSCAPE     VERTICAL
#youtube                                           SHORTS THUMBNAIL
#tiktok                                          THUMBNAIL AND VIDEO
#instagram:   3:4 POST, PORTRAIT, REEL THUMBNAIL    REELS & STORY          SQUARE      LANDSCAPE
IMAGE_SIZES = [         (1080, 1440),               (1080, 1920),        (1080,1080), (1080,566),   (1600,900),      (1200, 1200), (1280, 720), (720, 1280), (1200, 627), (720, 900)]


storage_client = storage.Client()

@functions_framework.cloud_event 
def resize_image(cloud_event):
    data = cloud_event.data 
    bucket_name = data['bucket'] 
    file_name = data['name']
    
    print(f"IMAGE NAME: {file_name} BUCKET NAME: {bucket_name}")

    #has to be these 3 files, can add more if needed.
    if not file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
        print(f"Image type not supported, please choose from .jpg, .jpeg, or .png, for: {file_name}")
        quit


