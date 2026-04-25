import os
import tempfile
from PIL import Image
from google.cloud import storage
import functions_framework

#deploy function
"""gcloud functions deploy image_resizer --gen2 --runtime=python311 --region=us-west1 --source="Cloud Media Resizer" --entry-point=resize_image --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" --trigger-event-filters="bucket=media_image_initial_bucket" --set-env-vars=RESIZED_BUCKET=media_image_resized_bucket --memory 512MB --timeout=240s --max-instances=10  """

#run function with image
#gsutil cp "C:\Users\Frank\Downloads\sample.png" gs://media_image_initial_bucket

#IAM permissions
#gsutil iam ch serviceAccount:service-10189932669@gcp-sa-eventarc.iam.gserviceaccount.com:objectViewer gs://media_image_initial_bucket
#gsutil iam ch serviceAccount:service-10189932669@gcp-sa-eventarc.iam.gserviceaccount.com:objectAdmin gs://media_image_resized_bucket
#gcloud projects add-iam-policy-binding social-media-photo-resizer --member="serviceAccount:service-10189932669@gs-project-accounts.iam.gserviceaccount.com" --role="roles/pubsub.publisher"

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
        return
        
    #calls initial bucket with the file path
    initial_bucket = storage_client.bucket(bucket_name)
    initial_blob = initial_bucket.blob(file_name)
    
    #we want to create a temp file to work with so we can perserve the original file
    with tempfile.NamedTemporaryFile() as temp_file:
        initial_blob.download_to_filename(temp_file.name) 
        
        #make image same format
        with Image.open(temp_file.name) as image:
            if image.mode != 'RGB':
                image = image.convert('RGB')
        
            #figuring out if output bucket is correct or not
            #output_name = "media_image_resized_bucket"
            output_name = os.environ.get("RESIZED_BUCKET")
            if not output_name:
                print("incorrect bucket name")
                return
            #set the bucket
            output_bucket = storage_client.bucket(output_name)
            
            #w is weight, h is height
            for w, h in IMAGE_SIZES:
                org_ratio = image.width / image.height
                cur_ratio = w/h
                
                
                #used to check if image ratio is too wide or too tall
                if org_ratio > cur_ratio:
                    width = w
                    height = int(w/org_ratio)
                else:
                    width = int(h*org_ratio)
                    height = h
                    
                resized = image.resize((width, height), Image.Resampling.LANCZOS)
                
                name = os.path.splitext(file_name)
                new_name = f"{name[0]}_NEW_{w}x{h}{name[1]}"
                
                with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_output:
                    resized.save(temp_output.name, 'JPEG', quality=80, optimize=True)
                
                    output_blob = output_bucket.blob(new_name)
                    output_blob.upload_from_filename(temp_output.name, content_type = 'image/jpeg')
                    
                    print(f"Output created, resized image: {new_name} ({w}x{h})")
            
            print("success with:", file_name)
                
        
        


    

