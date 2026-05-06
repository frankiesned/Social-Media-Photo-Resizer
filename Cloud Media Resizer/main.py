import os
import tempfile
from PIL import Image
from PIL import ImageOps
from PIL import ImageFilter
from google.cloud import storage
import functions_framework

#deploy function
"""gcloud functions deploy image_resizer --gen2 --runtime=python311 --region=us-west1 --source="Cloud Media Resizer" --entry-point=resize_image --trigger-event-filters="type=google.cloud.storage.object.v1.finalized" --trigger-event-filters="bucket=media_image_initial_bucket" --set-env-vars=RESIZED_BUCKET=media_image_resized_bucket --memory 512MB --timeout=240s --max-instances=10  """

#run function with image
#gsutil cp "C:\Users\Frank\Downloads\sample.png" gs://media_image_initial_bucket
#gsutil cp ""C:\Users\Frank\Downloads\greed-apple-cat.png"" gs://media_image_initial_bucket

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

#to make readability easier, we decided to seperate each function into their own functions.

#Original idea, simple resize to specific aspect ratio
def resize(image, target_w, target_h):
    img = image.copy()
    img.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    return img

#Proposed idea, crop image to ratio, may loose some parts of the image, but useful if the center of the image is the main focus.
def crop(image, target_w, target_h):
    return ImageOps.fit(image, (target_w, target_h), method=Image.Resampling.LANCZOS, centering = (0.5,0.5))

#New idea after second sprint, change ratio but fill outsides that don't fit with blur. Example, vertical post would have bars on the side to fit into a horizontal post.
def fill(image, target_w, target_h):
    background = ImageOps.fit(image, (target_w, target_h), method=Image.Resampling.LANCZOS)
    background = background.filter(ImageFilter.GaussianBlur(int(min(target_w, target_h)/20)))
    foreground = image.copy()
    foreground.thumbnail((target_w, target_h), Image.Resampling.LANCZOS)
    x = (target_w-foreground.width) // 2
    y = (target_h-foreground.height) // 2
    
    background.paste(foreground, (x, y))
    return background

#uploads the image path to the output bucket. 
def upload(image_final, bucket, path):
    with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_output:
        image_final.save(temp_output.name, 'JPEG', quality=85, optimize=True)

        blob = bucket.blob(path)
        blob.upload_from_filename(temp_output.name, content_type='image/jpeg')

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
    
    
    with tempfile.NamedTemporaryFile() as temp_file:
        initial_blob.download_to_filename(temp_file.name) 
        
        #preseve RGB for pngs
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
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            
            
            #w is weight, h is height
            for w, h in IMAGE_SIZES:
    
                #create each formatting option with images
                resized = resize(image, w, h)
                cropped = crop(image, w, h)
                filled = fill(image,w, h)
                
                
                #create the file name for each image
                resize_path = f"{base_name}/{w}x{h}/fit.jpg"
                crop_path = f"{base_name}/{w}x{h}/crop.jpg"
                fill_path = f"{base_name}/{w}x{h}/fill.jpg"
                
                #upload each specific file type to the bucket
                upload(resized, output_bucket, resize_path)
                upload(cropped, output_bucket, crop_path)
                upload(filled, output_bucket, fill_path)
                
                
                
            print("success with:", file_name)
                
        
        


    

