import io
import cv2
import time
import base64
import requests
import numpy as np
import json
from PIL import Image
from flask import Flask,render_template,request,jsonify
import sys
import pydocumentdb.documents as documents
import pydocumentdb.document_client as document_client
import pydocumentdb.errors as errors
import os

app = Flask(__name__)
detection_url=""
recognition_url = ""
detection_port = ":80"
recognition_port = ":80"

client = document_client.DocumentClient("https://autosqldemo.documents.azure.com:443/",{'masterKey': "YuRmSXCpdyCp4RUpkf0fsErrdHymFz45dfoCYyErOZEY2vCGbGCbpPKzCzCN5Y0D9oAXq3WEBeEJB4UhX4iNCg=="})
collection_link = "dbs/sample_data/colls/collection_1"

def updateDatabase(feat_str,name):
    name = name.strip()
    newline = feat_str.strip()
    document1 = client.UpsertDocument(collection_link,
    { 
    'id': name,
    'name': name,
    'feature': newline
    })
    print "Resiger success"

@app.route("/")
def loadRegisterPage():
    return render_template('registeration.html')

@app.route("/detection",methods=["POST","GET"])
def detection():
    img = request.form['raw_image']
    frame_index = request.form['frame_index']
    recog_or_regis = request.form['type']
    img = str(img.split(',')[1])
    frame_index = str(frame_index)
    recog_or_regis = str(recog_or_regis)

    detection_response = requests.post(detection_url+detection_port+"/detection", data = {'raw_image':img})
    return detection_response.content

@app.route("/registeration",methods=["POST","GET"])
def register():
    img = request.form['img']
    name = request.form['name']
    bbox = request.form['det']
    frame_index = request.form['frame_index']

    img = str(img)
    name = str(name)
    imgs_list = [img]

    recog_response = requests.post(recognition_url+recognition_port+"/extract", data = {'images':imgs_list})
    features_list = json.loads(str(recog_response.content))['features']

    feature = str(features_list[0])
    updateDatabase(feature,name)
    return "register success"
    

if __name__ == "__main__":
    if len(sys.argv)>1:
        detection_url = sys.argv[1]
        recognition_url = sys.argv[2]
    detection_url = "http://detection"
    recognition_url = "http://feature"
    env_dist = os.environ
    print env_dist
    app.run(host='0.0.0.0', debug=True, port=80)
