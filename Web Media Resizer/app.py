from flask import Flask, jsonify, request
from google.cloud import storage
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

#makes a GCS client and initializes buckets from google project
client = storage.Client()
input_bucket = client.bucket("media_image_initial_bucket")
output_bucket = client.bucket("media_image_resized_bucket")

@app.route("/upload", methods=["POST"])
def upload():
    #gets file user inputted
    file = request.files["file"]

    filename = file.filename
    #puts file into input bucket and uploads it with its file type
    blob = input_bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)
    #successful upload
    return jsonify({
        "filename": filename
    }), 200

@app.route("/list", methods=["GET"])
def list_files():
    #requests the parameter from URL
    filename = request.args.get("name")
    #if file name isnt given, return error message
    if not filename:
        return jsonify({"error": "missing filename"}), 400
    #extracts just the name, not the full file name
    base = filename.rsplit(".", 1)[0]
    #chekcs through output bucket to see if the resized images are there, so the name + NEW
    blobs = output_bucket.list_blobs(prefix=base + "_NEW_")
    #if found, puts the files in a list
    files = [blob.name for blob in blobs]
    #returns files
    return jsonify({
        "files": files
    }), 200
#starts the server and listens for requests
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
