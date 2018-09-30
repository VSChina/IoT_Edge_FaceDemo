#coding=utf-8
import time
from PyQt4.QtCore import *
from PyQt4.QtGui import * 
import os
import sys
import numpy
import cv2
import base64
import dlib_detection
import queue
from PIL import Image
import multiprocessing as mp
import requests
sys.path.insert(1,'/usr/local/lib/python3.5/dist-packages')
from azure.eventhub import EventHubClient, Receiver, Offset
from iothub_client import IoTHubClient,IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider,IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue

SAVEPATH = "./regions_tmp/"


ADDRESS = "amqps://autoresultdemo.servicebus.windows.net/faceresultdemo"

USER = "RootManageSharedAccessKey"
KEY = "rd/X+LTHjELtPmmZ6l/eBWEuWMIaS3VZaxYBI74N0KM="
CONSUMER_GROUP = "$default"
OFFSET = Offset('@latest')
PARTITION = "0"

TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_to_output.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

RECEIVE_CONTEXT = 0
RECEIVED_COUNT = 0
TWIN_CONTEXT = 0
METHOD_CONTEXT = 0

# global counters
SEND_CALLBACKS = 0


MSG_TXT = "{\"frame_index\": \"%s\",\"type\": \"%s\",\"images\":%s,\"rect_index\":%s}"
recog_or_regis = "recognition"
exit_value = mp.Value("i",0)
CONNECTION_STRING = "HostName=autoiotdemo.azure-devices.net;DeviceId=videoUpload;SharedAccessKey=/77sG5xYe/eUHvNwjHUifV0QTe75G6VPgAIEHE9fqE8=;GatewayHostName=fanqiu-Precision-Tower-5810"



def iothubClientInit(protocol,connection_string):
    # Create an IoT Hub client
    client = IoTHubClient(connection_string, protocol)
    return client

def sendConfirmationCallback(message, result, user_context):
    global SEND_CALLBACKS
    print( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print( "    Total calls confirmed: %d" % SEND_CALLBACKS )


def listToString(bboxs):
    bbox_string = "["
    for j in range(len(bboxs)):
        bbox_string += (str(bboxs[j]) + ",")
    bbox_string = bbox_string.strip(",")
    bbox_string += "]"
    return bbox_string


def deleteCacheImg(imagePath,gap,startIndex):
    for i in range(gap):
        imPath = imagePath + str(startIndex + i) + ".png"
        if os.path.exists(imPath):
            os.remove(imPath)


class MainWindow(QWidget):
    def __init__(self,readCamera,videoPlay, showRes,retriever,registerImages,img_quality):
        super(MainWindow, self).__init__()
        self.setWindowTitle('Azure IoT Face Recognition Demo')
        self.setWindowIcon(QIcon("microsoftIcon.jpg"))

        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        winWidth = 800
        winHeight = 500
        strHeight = 32
        self.maxResCount = 3

        self.readCamera = readCamera
        self.showRes = showRes
        self.retriever = retriever
        self.videoPlay = videoPlay
        self.img_quality = img_quality

        self.resize(winWidth, winHeight)
        self.videoFrame = QImage()
        self.imageDemo = QImage()
        self.videoLabel = QLabel('')
        self.resLabelImgs = []
        self.resLabelStrs = []
        for i in range(self.maxResCount):
            self.resLabelImgs.append(QLabel(""))
            self.resLabelStrs.append(QLabel(""))

        self.videoIndex = QLineEdit()
        self.videoIndex.setReadOnly(True)
        self.resIndex = QLineEdit()
        self.resIndex.setReadOnly(True)


        hbox=QHBoxLayout()
        vbox_left = QVBoxLayout()
        vbox_right = QVBoxLayout()
        vbox_left.addWidget(self.videoLabel)
        vbox_left.addWidget(self.videoIndex)
        for i in range(self.maxResCount):
            vbox_right.addWidget(self.resLabelStrs[i])
            vbox_right.addWidget(self.resLabelImgs[i])
            self.resLabelStrs[i].setAlignment(Qt.AlignCenter)
            self.resLabelImgs[i].setAlignment(Qt.AlignCenter)
            self.resLabelStrs[i].setFont(font)
            self.resLabelStrs[i].setFixedHeight(strHeight)
        vbox_right.addWidget(self.resIndex)
        hbox.addLayout(vbox_left)
        hbox.addLayout(vbox_right)
        self.setLayout(hbox)

        self.connect(self.videoPlay, SIGNAL("PlayVideo"), self.PlayVideo)
        self.connect(self.showRes, SIGNAL("ShowResult"), self.ShowRes)

        self.readCamera.start()
        self.showRes.start()
        self.retriever.start()
        self.videoPlay.start()

    def PlayVideo(self,im,frameIndex):
        self.videoFrame.loadFromData(QByteArray(im))
        self.videoLabel.setPixmap(QPixmap.fromImage(self.videoFrame))
        self.videoIndex.setText(frameIndex)
    
    def ShowRes(self,ims,strs,frameIndex):
        i = 0
        while(i < min(self.maxResCount,len(ims))):
            self.resLabelStrs[i].setText(strs[i])
            self.imageDemo.loadFromData(QByteArray(ims[i]))
            self.resLabelImgs[i].setPixmap(QPixmap.fromImage(self.imageDemo))
            i += 1
        while(i < self.maxResCount):
            self.resLabelStrs[i].clear()
            self.resLabelImgs[i].clear()
            i += 1
        self.resIndex.setText(frameIndex)

    def closeEvent(self,event):
        global exit_value
        exit_value.value = not exit_value.value
        event.accept()

class ReadCameraTimer(mp.Process):
    def __init__(self, SAVEPATH, resolution,quality, output_buffer,registerBackup, parent=None):
        mp.Process.__init__(self)
        self.daemon = True
        self.stoped = False
        self.registerBackup = registerBackup
        self.resolution = resolution
        self.img_quality = quality
        self.frameIndex = 0
        self.rectIndex = 0
        self.output_buffer = output_buffer
        self.imagePath = SAVEPATH
        self.deleteIndex = 0
        self.deleteGap = 2000
        if not os.path.exists(self.imagePath):
            os.mkdir(self.imagePath)
    def drawDetection(self,face_img,dets):
        if dets is None:
            return
        for i, bbox in enumerate(dets):
            cv2.rectangle(face_img, (int(float(bbox.left())),int(float(bbox.top()))), (int(float(bbox.right())),int(float(bbox.bottom()))), (255,0,0), 1)
    def run(self):
        self.detector = dlib_detection.Dlib_detection("shape_predictor_68_face_landmarks.dat")
        PROTOCOL = IoTHubTransportProvider.MQTT
        self.normal_client = iothubClientInit(PROTOCOL,CONNECTION_STRING)
        global exit_value
        self.camera = cv2.VideoCapture(0)
        encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),self.img_quality]
        while(exit_value.value != 1):
            if self.stoped:
                self.camera.release()      
                return
            (grabbed, self.img) = self.camera.read()
            if not grabbed:
                continue
            self.frameIndex += 1
            self.img  = cv2.resize(self.img,self.resolution)
            self.img = cv2.flip(self.img,1)
            aligned ,dets = self.detector.get_img(self.img)
            cv2_im = cv2.cvtColor(self.img,cv2.COLOR_BGR2RGB)
            self.drawDetection(cv2_im,dets)
            if not self.output_buffer.full():
                self.output_buffer.put([cv2_im,self.frameIndex])
            if aligned is None:
                continue
            try:
                imgs_list = []
                dets_list = []
                rect_list = []
                det_pattern = "\"%d %d %d %d\""
                for i in range(len(aligned)):
                    align = aligned[i]
                    if(dets[i].top()>=dets[i].bottom() or dets[i].left()>=dets[i].right()):
                        continue
                    self.registerBackup[self.rectIndex % 3] = align
                    cv2.imwrite(self.imagePath + str(self.rectIndex) + ".png",align)
                    det = det_pattern%(dets[i].left(),dets[i].top(),dets[i].right(),dets[i].bottom())
                    align_str = base64.b64encode(align)
                    imgs_list.append("\"%s\""%str(align_str.decode("utf-8")))
                    dets_list.append(det)
                    rect_list.append("\"%s\""%str(self.rectIndex))
                    self.rectIndex += 1
                global recog_or_regis
                msg_txt_formatted = MSG_TXT%(self.frameIndex,recog_or_regis,listToString(imgs_list),listToString(rect_list))
                message = IoTHubMessage(msg_txt_formatted)
                self.normal_client.send_event_async(message, sendConfirmationCallback, self.frameIndex)
            except Exception as e:
                print(e)
                self.camera.release()
                return
        try:
            self.camera.release()
            print("process finish")
            return
        except:
            return

class RetrieveEventHub(QThread):
    def __init__(self,output_buffer,ADDRESS,USER,KEY,CONSUMER_GROUP,OFFSET,PARTITION,parent=None):
        super(RetrieveEventHub,self).__init__(parent)

        self.address = ADDRESS

        # SAS policy and key are not required if they are encoded in the URL
        self.user = USER
        self.key = KEY
        self.CONSUMER_GROUP = CONSUMER_GROUP
        self.OFFSET = OFFSET
        self.PARTITION = PARTITION
        self.total = 0
        self.last_sn = -1
        self.last_offset = "-1"
        self.client = EventHubClient(self.address, debug=False, username=self.user, password=self.key)
        self.receiver = self.client.add_receiver(self.CONSUMER_GROUP, self.PARTITION, prefetch=1000,offset=self.OFFSET)
    
        self.output_buffer = output_buffer
        self.last_frame = -1
    def ordered_by_index(self,elem):
        return int(elem[0])
    def run(self):
        self.client.run()
        global exit_value
        while(exit_value.value != 1):
            time.sleep(0.05)
            batched_events = self.receiver.receive(max_batch_size=10)
            contents = []
            for event in batched_events:
                oneLine = str(event.message).strip('&')
                content = oneLine.split('&')
                contents.append(content)
                #self.queue_service.delete_message(self.queue_name, message.id, message.pop_receipt)
            
            contents.sort(key=self.ordered_by_index)
            for content in contents:
                if int(content[0])>self.last_frame:
                    if not self.output_buffer.full():
                        self.output_buffer.put(content)
                    self.last_frame = int(content[0])

class ShowVideo(QThread):
    def __init__(self,input_buffer, signal = "PlayVideo", parent=None):
        super(ShowVideo, self).__init__(parent)
        self.stoped = False
        self.signal = signal
        self.input_buffer = input_buffer
    def run(self):
        global exit_value
        while(exit_value.value != 1):
            time.sleep(0.05)
            if self.stoped:    
                return
            if not self.input_buffer.empty():
                [cv2_im,frameIndex] = self.input_buffer.get(1,5)
                pil_im = Image.fromarray(cv2_im)
                im = pil_im.convert('RGB').tobytes('jpeg', 'RGB')
                self.emit(SIGNAL(self.signal),im,str(frameIndex))


class ShowResult(QThread):
    def __init__(self,SAVEPATH,input_buffer, signal = "ShowResult", parent=None):
        super(ShowResult, self).__init__(parent)
        self.stoped = False
        self.signal = signal
        self.input_buffer = input_buffer
        self.resDict = {}
        self.storeTime = 50 # 13 fps
        self.imagePath = SAVEPATH
    def run(self):
        global exit_value
        while(exit_value.value != 1):
            time.sleep(0.07)
            if self.stoped:    
                return
            if not self.input_buffer.empty():
                content = self.input_buffer.get(1,5)
            else:
                continue
            try:
                frameIndex = content[0]
                index = 1
                while(index < len(content)):
                    name = content[index]
                    rectIndex = str(content[index+1])
                    if name in self.resDict.keys():
                        self.resDict[name][0]=frameIndex
                        self.resDict[name][1]=rectIndex
                    else:
                        self.resDict[name]=[frameIndex,rectIndex]
                    index += 2
                for key,value in self.resDict.items():
                    if int(value[0]) + self.storeTime < int(frameIndex):
                        del(self.resDict[key])
                [ims,strs] = self.generateResImage()
                self.emit(SIGNAL(self.signal),ims,strs,frameIndex)
            except:
                continue
    
    def generateResImage(self):
        ims = []
        strs = []
        count = 0
        for key,value in self.resDict.items():
            if key == "Stranger":
                continue
            if not os.path.exists(self.imagePath + value[1]+ ".png"):
                continue
            rectImg = cv2.imread(self.imagePath + value[1] + ".png")
            rectImg = cv2.cvtColor(rectImg,cv2.COLOR_BGR2RGB)
            pil_im = Image.fromarray(rectImg)
            im = pil_im.convert('RGB').tobytes('jpeg', 'RGB')
            ims.append(im)
            strs.append(key)
            count += 1
        return ims,strs


if __name__ == "__main__":
    exit_value.value = 0
    imgQueue = mp.Queue(1)
    registerBackup = mp.Manager().list(range(3))
    data_buffer = queue.Queue(10)
    
    app = QApplication(sys.argv)
    reader=ReadCameraTimer(SAVEPATH,(640,480),95,imgQueue,registerBackup)
    player = ShowVideo(imgQueue,"PlayVideo")
    retriever = RetrieveEventHub(data_buffer,ADDRESS,USER,KEY,CONSUMER_GROUP,OFFSET,PARTITION)
    shower = ShowResult(SAVEPATH,data_buffer,"ShowResult")
    main = MainWindow(reader,player,shower,retriever,registerBackup,95)
    main.show()
    sys.exit(app.exec_()) 