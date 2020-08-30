# Copyright 2019 Google, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START run_imageproc_controller]
import base64
import json
import os

from flask import Flask, request
import requests
import logging

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential


app = Flask(__name__)


from google.cloud import storage


def download_blob(bucket_name, source_blob_name):
    """Downloads a blob from the bucket."""

    filename = '/tmp/tmp'

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(filename)

    return filename


def predict(bucket, filename):
    server_url = 'http://localhost:8501/v1/models/cats_vs_dogs:predict'
    f_name = download_blob(bucket, filename)

    img = keras.preprocessing.image.load_img(
        f_name, target_size=(180, 180)
    )
    img_array = keras.preprocessing.image.img_to_array(img)
    data = json.dumps({"signature_name": "serving_default", "instances": [img_array.tolist()]})

    response = requests.post(server_url, data=data)
    response.raise_for_status()

    print('PREDICTION OUTPUT: ' + str(response.json()['predictions'][0]))

    return response.json()['predictions'][0]

def pubsub_send(filename, prediction):

    from google.cloud import pubsub_v1

    project_id = "edgar-prunk-eger-sandbox"
    topic_id = "ottoPredictionTopic"

    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, topic_id)

    data = json.dumps({
        'filename': filename,
        'prediction': prediction,
    })
    future = publisher.publish(
        topic_path, data=data.encode("utf-8")  # data must be a bytestring.
    )


@app.route('/', methods=['POST'])
def index():

    envelope = request.get_json()

    if not envelope:
        msg = 'no Pub/Sub message received'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    if not isinstance(envelope, dict) or 'message' not in envelope:
        msg = 'invalid Pub/Sub message format'
        print(f'error: {msg}')
        return f'Bad Request: {msg}', 400

    # Decode the Pub/Sub message.
    pubsub_message = envelope['message']

    print('ENVELOPE: ', str(json.dumps(envelope)))

    if isinstance(pubsub_message, dict) and 'data' in pubsub_message:
        try:
            data = json.loads(
                base64.b64decode(pubsub_message['data']).decode())

        except Exception as e:
            msg = ('Invalid Pub/Sub message: '
                   'data property is not valid base64 encoded JSON')
            print(f'error: {e}')
            return f'Bad Request: {msg}', 400

        # Validate the message is a Cloud Storage event.
        if not data["name"] or not data["bucket"]:
            msg = ('Invalid Cloud Storage notification: '
                   'expected name and bucket properties')
            print(f'error: {msg}')
            return f'Bad Request: {msg}', 400

        if envelope['message']['attributes']['eventType'] != "OBJECT_FINALIZE":
            # We don't care if event type not OBJECT_FINALIZE
            return ('', 204)

        try:
            print('DATA: ', str(json.dumps(data)))

            prediction = predict(data["bucket"], data["name"])
            pubsub_send(data["name"], prediction)

            return ('', 204)

        except Exception as e:
            print(f'error: {e}')
            return ('', 500)

    return ('', 500)


if __name__ == '__main__':
    PORT = int(os.getenv('PORT')) if os.getenv('PORT') else 8080

    app.run(host='127.0.0.1', port=PORT, debug=True)
