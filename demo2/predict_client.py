import requests
from tensorflow import keras
import json

fileName = '/home/edgarpe/Downloads/zombie_180.jpeg'

server_url = 'http://localhost:8501/v1/models/cats_vs_dogs:predict'


# with open(fileName, mode='rb') as file: # b is important -> binary
#     fileContent = file.read()

img = keras.preprocessing.image.load_img(
    fileName, target_size=(180, 180)
)
img_array = keras.preprocessing.image.img_to_array(img)
data = json.dumps({"signature_name": "serving_default", "instances": [img_array.tolist()]})

response = requests.post(server_url, data=data)
response.raise_for_status()

print(response.json()['predictions'][0])
