import sys
import dlib
import numpy as np
import cv2
import face_preprocess
import time

class Dlib_detection(object):
    def __init__(self,predictor_path = ""):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(predictor_path)
        #self.cvdetectore = cv2.CascadeClassifier('lbpcascade_frontalface_improved.xml')
    def get_face_dets_points(self, face_img):
        dets = self.detector(face_img)
        #dets = self.cvdetectore.detectMultiScale(face_img, scaleFactor = 1.1,minSize=(80,80))
        if len(dets)==0:
            return None, None
        #dlibFormat = []
        #for item in dets:
        #    dlibFormat.append(dlib.rectangle(int(item[0]),int(item[1]),int(item[0]+item[2]),int(item[1]+item[3])))
        #dets = dlibFormat
        points_all = []
        for j, bbox in enumerate(dets):
            shape = self.predictor(face_img, bbox)
            sevens=np.zeros((9,2))
            index=[30,39,36,42,45,48,54,37,43] # nt,lei,leo,rei,reo,lm,rm
            for i in range(len(index)):
                cord=str(shape.part(index[i])).split(',')
                x=int(cord[0][1:])
                y=int(cord[1][:-1])
                sevens[i][0]=x
                sevens[i][1]=y
            points = np.array([(sevens[1]+sevens[2])/2,(sevens[3]+sevens[4])/2,sevens[0],sevens[5],sevens[6]])
            points_all.append(points)
        return dets, points_all
    def get_img(self, face_img):
        #face_img is bgr image
        dets, points_all = self.get_face_dets_points(face_img)
        if not dets:
            return None, None
        # print dets
        #print points_all
        aligned_imgs = []
        for i, bbox in enumerate(dets):
            points = points_all[i]
            nimg = face_preprocess.preprocess(face_img, bbox, points, image_size='112,112')
            #nimg = cv2.cvtColor(nimg, cv2.COLOR_BGR2RGB)
            #nimg = np.transpose(nimg, (2,0,1))
            aligned_imgs.append(nimg)
        return aligned_imgs,dets