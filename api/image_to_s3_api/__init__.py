#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# included
import os
import logging
from config import app_config
from datetime import datetime

# third-party
import boto3
import requests
import shutil
import markdown
from botocore.exceptions import ClientError
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

# Create an instance of Flask
app = Flask(__name__, instance_relative_config=True)

# Init ma
ma = Marshmallow(app)

# Fetch environment variables
env_name = os.getenv('ENV')

# Fetch app configs from config.py
app.config.from_object(app_config[env_name])

# Init boto3 session
boto_session = boto3.Session(
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['AWS_REGION']
)

# Fetch database uri
app.config['SQLALCHEMY_DATABASE_URI'] = app.config.get('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = \
  app.config.get('SQLALCHEMY_TRACK_MODIFICATIONS')

# Init db
db = SQLAlchemy(app)

# Import from models.py
from .models import Image, ImageSchema

# Init image schema
image_schema = ImageSchema(strict=True)

# S3 bucket name
S3_BUCKET = app.config['S3_BUCKET']


@app.route("/")
def index():
    """Display readme file by default"""
    # Open the README file
    with open(
            os.path.dirname(app.root_path) + '/README.md',
            'r') as markdown_file:

        # Read the content of the file
        content = markdown_file.read()

        # Convert to HTML
        return markdown.markdown(content)


@app.route('/ping', methods=['GET'])
def app_status():
    """ Handle health checks
    :return: 200 status code
    """
    return {'message': 'App is healthy'}, 200

# Take Image URL
@app.route('/', methods=['POST'])
def get_url():
    """ Accept URL as a POST request
    :args url: HTTP/HTTPS URL
    :return: Data committed to database
    """
    url = request.json['url']
    if url:
        name, url, s3_path, timestamp = download_image(url)
        new_image = Image(name, url, s3_path, timestamp)

    db.session.add(new_image)
    db.session.commit()

    return image_schema.jsonify(new_image)


# Download image from internet
def download_image(url):
    """ Download image and store to s3 bucket
    :param url: URL to download image from
    :return image: The image name with extension
    :return url: The image url
    :return s3_path: URL to s3 bucket and object
    :return timestamp: Upload time
    """
    extensions = ['jpeg', 'jpg', 'png', 'gif']
    link, image = url.rsplit('/', 1)
    image_name, extension = image.split('.')

    if extension in extensions:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(image, 'wb') as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
            state = upload_image(image)
        else:
            abort(400, description="Invalid URL")
    else:
        abort(404,
              description="Image format not found"
              "Accepted are jpeg, jpg, png, gif")

    if state:
        os.remove(image)
        s3_path = "s3://{}/{}".format(S3_BUCKET, image)
        timestamp = str(datetime.now())
    return image, url, s3_path, timestamp


# Upload image to S3 bucket
def upload_image(file_name):
    """Upload a file to an S3 bucket
    :param file_name: Name of file to upload
    :return: True if file was uploaded, else False
    """
    bucket = S3_BUCKET

    # If S3 object_name was not specified, use file_name
    object_name = file_name

    # Upload the file
    s3_client = boto_session.client('s3')
    try:
        s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

# List all files from S3 bucket
@app.route('/list', methods=['GET'])
def list_s3_objects():
    """ List all the files from bucket
    :return: Print all files store in s3 bucket
    """
    bucket = S3_BUCKET
    file_list = []

    s3 = boto_session.resource('s3')
    my_bucket = s3.Bucket(bucket)
    for file in my_bucket.objects.all():
        file_list.append(file.key)

    if not file_list:
        return 204
    else:
        return jsonify(file_list)


if __name__ == '__main__':
    app.run(debug=True)
