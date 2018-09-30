import io
import cv2
import time
import base64
import numpy as np
from PIL import Image
from flask import Flask,render_template,request,jsonify
import sys
import face_model
import argparse
import random

app = Flask(__name__)

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)  
        return cls._instance

class Recognition(Singleton):
    parser = argparse.ArgumentParser(description='face model test')
    parser.add_argument('--image-size', default='112,112', help='')
    parser.add_argument('--model', default='./insightface/models/model-r34-amf/model,0', help='path to load model.')
    parser.add_argument('--ga-model', default='', help='path to load model.')
    parser.add_argument('--gpu', default=0, type=int, help='gpu id')
    parser.add_argument('--det', default=0, type=int, help='mtcnn option, 1 means using R+O, 0 means detect from begining')
    parser.add_argument('--flip', default=0, type=int, help='whether do lr flip aug')
    parser.add_argument('--threshold', default=1.24, type=float, help='ver dist threshold')
    args = parser.parse_args()
    extractor = face_model.FaceModel(args)

def feat_to_string(feat):
    feat_string = ""
    for i in range(feat.shape[0]):
        feat_string += (str(feat[i]) + " ")
    feat_string = feat_string.strip()
    return feat_string

@app.route("/extract",methods=["POST","GET"])
def extract():
    data_file = request.form.to_dict(flat=False)

    imgs_list = data_file['images']
    imgs = []
    for i in range(len(imgs_list)):
        reverse = base64.decodestring(imgs_list[i])
        rever_img = np.frombuffer(reverse,dtype=np.uint8).reshape((112, 112, 3))
        rever_img= cv2.cvtColor(rever_img, cv2.COLOR_BGR2RGB)
        img= np.transpose(rever_img, (2,0,1))
        imgs.append(img)

    features_list = []

    web_UI = {
        'features':features_list
    }

    extractor = Recognition().extractor
    for j in range(len(imgs)):
        feat = extractor.get_feature(imgs[j])
        features_list.append(feat_to_string(feat))
    return jsonify(web_UI)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
