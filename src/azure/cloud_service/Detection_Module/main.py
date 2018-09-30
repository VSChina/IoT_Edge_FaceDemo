import io
import cv2
import time
import base64
import requests
import numpy as np
import dlib_detection
from PIL import Image
from flask import Flask,render_template,request,jsonify
import sys

app = Flask(__name__)

class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kw)  
        return cls._instance

class Detection(Singleton):
    detector = dlib_detection.Dlib_detection("shape_predictor_68_face_landmarks.dat")

@app.route("/detection",methods=["POST","GET"])
def detection():
    img = request.form['raw_image']

    img = str(img)
    reverse = base64.decodestring(img)
    nparr = np.fromstring(reverse, dtype=np.uint8)
    img = cv2.imdecode(nparr, 1)

    detector = Detection().detector
    aligned, dets = detector.get_img(img)

    imgs_list = []
    dets_list = []
    det_pattern = "%d %d %d %d"
    face_num = 0
    web_UI = {
        'dets':dets_list,
        'align_imgs':imgs_list,
        'num':face_num

    }
    if aligned is None:
        return jsonify(web_UI)
    face_num  = len(aligned)
    web_UI['num'] = face_num
    for i in range(len(aligned)):
        align = aligned[i]
        det = det_pattern%(dets[i].left(),dets[i].top(),dets[i].right(),dets[i].bottom())
        align_str = base64.b64encode(align)
        imgs_list.append(align_str)
        dets_list.append(det)
    
    return jsonify(web_UI)
    
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
