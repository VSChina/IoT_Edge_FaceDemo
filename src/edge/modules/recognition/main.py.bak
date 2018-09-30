# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import random
import time
import sys
import iothub_client
from iothub_client import IoTHubClient,IoTHubModuleClient, IoTHubClientError, IoTHubTransportProvider,IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
import threading
import base64
import Queue
import json
import requests

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubModuleClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0

# Choose HTTP, AMQP or MQTT as transport protocol.  Currently only MQTT is supported.
PROTOCOL = IoTHubTransportProvider.MQTT
CONNECTION_STRING = "HostName=autoiotdemo.azure-devices.net;DeviceId=featUpload;SharedAccessKey=0PlxEK9bNiUQD/dgs/K3t3AVJ7OGA//NUz1XUuRzkDo="

recognition_url = "http://172.18.0.5"
MSG_TXT = "{\"deviceId\": \"myFeatureDevice\",\"frameIndex\": \"%s\",\"featureVectors\": \"%s\",\"rectIndex\": \"%s\"}"

def iothub_client_init(protocol,connection_string):
    # Create an IoT Hub client
    # connection_string = "HostName=finaldemo.azure-devices.net;DeviceId=featUpload;SharedAccessKey=XLnUqoIpV8MjmYjAKWtk0COHhuFe43qyb3XZ+o4nGS0="
    print "start create IoTHubClinet"
    client = IoTHubClient(connection_string, protocol)
    print "create IoTHubClinet success"
    return client

# Callback received when the message that we're forwarding is processed.
def send_confirmation_callback(message, result, user_context):
    global SEND_CALLBACKS
    print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    SEND_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )

def test_call_back(message, result, user_context):
    print("    Total calls confirmed: %d" % SEND_CALLBACKS)


# receive_message_callback is invoked when an incoming message arrives on the specified 
# input queue (in the case of this sample, "input1").  Because this is a filter module, 
# we will forward this message onto the "output1" queue.
def receive_message_callback(message,hubManager):
    global RECEIVE_CALLBACKS
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    oneMessage = message_buffer[:size].decode('utf-8')
    #print("oneMessage's size: ",size)
    #print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode('utf-8'), size) )
    if not hubManager.output_buffer.full():
        hubManager.output_buffer.put(oneMessage)
    #hubManager.forward_event_to_output("output1", message, 0)
    return IoTHubMessageDispositionResult.ACCEPTED


def feat_to_string(feat):
    feat_string = "["
    for i in range(feat.shape[0]):
        feat_string += (str(feat[i]) + " ")
    feat_string = feat_string.strip()
    feat_string += "]"
    return feat_string

def bbox_to_string(bbox):
    bbox_string = "["
    for j in range(4):
        bbox_string += (str(bbox[j]) + " ")
    bbox_string = bbox_string.strip()
    bbox_string += "]"
    return bbox_string

def rectIndex_to_string(rectIndex):
    bbox_string = "["
    bbox_string += str(rectIndex)
    bbox_string = bbox_string.strip()
    bbox_string += "]"
    return bbox_string

def genMessage(frameIndex,feat_strs,bbox_strs):
    frameIndexMessage = frameIndex
    featMessage = ""
    for j in range(len(feat_strs)):
        featMessage += (feat_strs[j] + "&")
    featMessage = featMessage[:-1]
    bboxMessage = ""
    for j in range(len(bbox_strs)):
        bboxMessage += (bbox_strs[j] + "&")
    bboxMessage = bboxMessage[:-1]
    message = MSG_TXT%(frameIndexMessage,featMessage,bboxMessage)
    return message


class HubManager(object):

    def __init__(
            self,
            output_buffer,
            protocol=IoTHubTransportProvider.MQTT):
        self.client_protocol = protocol
        self.client = IoTHubModuleClient()
        self.client.create_from_environment(protocol)
        self.output_buffer = output_buffer
        # set the time until a message times out
        self.client.set_option("messageTimeout", MESSAGE_TIMEOUT)
        
        # sets the callback when a message arrives on "input1" queue.  Messages sent to 
        # other inputs or to the default will be silently discarded.
        self.client.set_message_callback("input1", receive_message_callback,self)

    # Forwards the message received onto the next stage in the process.
    def forward_event_to_output(self, outputQueueName, event, send_context):
        self.client.send_event_async(
            outputQueueName, event, send_confirmation_callback, send_context)

class ExtractFeat(threading.Thread):
    def __init__(self,input_buffer,output_buffer_recog):
        threading.Thread.__init__(self)
        self.input_buffer = input_buffer
        self.output_buffer_recog = output_buffer_recog
        self.call_count = 0
        self.cosume_time = 0
        self.tcp_connect = requests.Session()

    def run(self):
        while True:
            if not self.input_buffer.empty():
                time_start = time.clock()

                oneMessage = self.input_buffer.get(1,5)
                content = json.loads(oneMessage)


                imgs_list = content['images']
                rects_list = content['rect_index']
                frame_index = str(content['frame_index'])
                recog_or_regis = str(content['type'])

                def mystrip(x):
                    return str(str(x))
                imgs_list = list(map(mystrip, imgs_list))
                rects_list = list(map(mystrip, rects_list))

                recog_response = self.tcp_connect.post(recognition_url+"/extract", data = {'images':imgs_list})

                features_list = json.loads(recog_response.content)['features']
                #print rects_list
                #print features_list
                print frame_index
                #print recog_or_regis
                self.call_count += 1
                self.cosume_time += (time.clock() - time_start - self.cosume_time) * 1.0 / self.call_count
                
                if not self.output_buffer_recog.full():
                    self.output_buffer_recog.put([frame_index,features_list,rects_list,recog_or_regis])
                print "extractFeatures ",self.call_count," cost time: ", self.cosume_time


class SendFeature(threading.Thread):
    def __init__(self,input_buffer,HubManager,protocol,connection_string):
        threading.Thread.__init__(self)
        self.input_buffer = input_buffer
        #self.hub_manager = HubManager
        self.normalclient = iothub_client_init(protocol,connection_string)
        self.call_count = 0
        self.cosume_time = 0
        self.message_counter = 0

    def run(self):
        while True:
            # send a few messages every minute
            if not self.input_buffer.empty():
                [frameIndex,feats,rects_list,recog_or_regis] = self.input_buffer.get(1,5)
                feat_strs = []
                bbox_strs = []
                
                for j in range(len(feats)):
                    feat_strs.append("[%s]"%str(feats[j]))
                    bbox_strs.append("[%s]"%str(rects_list[j]))

                msg_txt_formatted = genMessage(frameIndex,feat_strs,bbox_strs)
               
                msg_properties = {}

                message = IoTHubMessage(msg_txt_formatted)
                self.normalclient.send_event_async(message, test_call_back, self.message_counter)

                #self.hub_manager.forward_event_to_output("featureOutput", message, 0)
                self.message_counter += 1
                print "message send ",self.message_counter
            time.sleep(0.05)

def main(protocol,connection_string):
    try:
        raw_image_buffer =Queue.Queue(2)
        decoded_images_buffer = Queue.Queue(1)
        feat_buffer_recog = Queue.Queue(1)

        hub_manager = HubManager(raw_image_buffer,protocol)

        print ( "Starting the IoT Hub Python sample using protocol %s..." % hub_manager.client_protocol )

        recognize_face_thread = ExtractFeat(raw_image_buffer,feat_buffer_recog)
        send_feature_thread = SendFeature(feat_buffer_recog,hub_manager,protocol,connection_string)

        recognize_face_thread.start()
        send_feature_thread.start()

        while True:
            time.sleep(1)

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubModuleClient sample stopped" )

if __name__ == '__main__':
    main(PROTOCOL,CONNECTION_STRING)