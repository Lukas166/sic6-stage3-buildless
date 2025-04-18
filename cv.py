import cv2
import urllib.request
import numpy as np
import time
import requests

# Replace the URL with the IP camera's stream URL
url = 'http://192.168.6.107:80/cam-lo.jpg'
# cv2.namedWindow("live Cam Testing", cv2.WINDOW_AUTOSIZE)

# # Set parameters
# timeout = 5  # 5 seconds timeout
# fps = 30  # Target frames per second
# frame_time = 1.0/fps  # Time per frame

# print("Attempting to connect to camera at:", url)

# while True:
#     start_time = time.time()  # Start time for this frame
    
#     try:
#         # Try to read from the IP camera with a timeout
#         img_resp = urllib.request.urlopen(url, timeout=timeout)
#         imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
#         im = cv2.imdecode(imgnp, -1)
        
#         if im is None:
#             raise Exception("Failed to decode image")
            
#         # Display the frame
#         cv2.imshow('live Cam Testing', im)
        
#     except Exception as e:
#         print(f"Error: {e}")
#         # Create a black image with error text
#         im = np.zeros((480, 640, 3), dtype=np.uint8)
#         cv2.putText(im, "Connection Error", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
#         cv2.putText(im, "Check camera IP and network", (120, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
#         cv2.imshow('live Cam Testing', im)
#         time.sleep(2)  # Wait before retrying
    
#     # Control frame rate
#     elapsed = time.time() - start_time
#     wait_time = max(1, int((frame_time - elapsed) * 1000)) if elapsed < frame_time else 1
    
#     # Check for quit key with dynamic wait time
#     key = cv2.waitKey(wait_time)
#     if key == ord('q'):
#         print("Exiting...")
#         break

# # Clean up
# cv2.destroyAllWindows()

cap = cv2.VideoCapture(url)
whT=320
confThreshold = 0.5
nmsThreshold = 0.3
classesfile='coco.names'
classNames=[]
with open(classesfile,'rt') as f:
    classNames=f.read().rstrip('\n').split('\n')
#print(classNames)
 
modelConfig = 'yolov3.cfg'
modelWeights= 'yolov3.weights'
net = cv2.dnn.readNetFromDarknet(modelConfig,modelWeights)
net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

def findObject(outputs,im):
    hT,wT,cT = im.shape
    bbox = []
    classIds = []
    confs = []
    found_cat = False
    found_bird = False
    for output in outputs:
        for det in output:
            scores = det[5:]
            classId = np.argmax(scores)
            confidence = scores[classId]
            if confidence > confThreshold:
                w,h = int(det[2]*wT), int(det[3]*hT)
                x,y = int((det[0]*wT)-w/2), int((det[1]*hT)-h/2)
                bbox.append([x,y,w,h])
                classIds.append(classId)
                confs.append(float(confidence))
    
    # Handle empty case
    if len(bbox) == 0:
        return
        
    indices = cv2.dnn.NMSBoxes(bbox,confs,confThreshold,nmsThreshold)
    print(indices)
    
    # Handle both old and new OpenCV NMSBoxes return format
    for i in indices:
        try:
            # Old OpenCV version (array of arrays)
            idx = i[0]
        except:
            # New OpenCV version (flat array)
            idx = i
            
        box = bbox[idx]
        x,y,w,h = box[0],box[1],box[2],box[3]
        if classNames[classIds[idx]] == 'bird':
            found_bird = True
        elif classNames[classIds[idx]] == 'cat':
            found_cat = True
            
        if classNames[classIds[idx]]=='bird':
            cv2.rectangle(im,(x,y),(x+w,y+h),(255,0,255),2)
            cv2.putText(im, f'{classNames[classIds[idx]].upper()} {int(confs[idx]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,255), 2)
            print('bird')
            print(found_bird)
            
        if classNames[classIds[idx]]=='cat':
            cv2.rectangle(im,(x,y),(x+w,y+h),(255,0,255),2)
            cv2.putText(im, f'{classNames[classIds[idx]].upper()} {int(confs[idx]*100)}%', (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,255), 2)
            print('cat')
            print(found_cat)
            
        if found_cat and found_bird:
            print('alert')
            # Kirim pesan kalau ada objek
            # try:
            #     esp32_url = "http://192.168.6.101/buzzer" # Replace with your ESP32 IP
            #     response = requests.get(f"{esp32_url}?state=on", timeout=1)
            #     print(f"Alert sent to ESP32: {response.status_code}")
            # except Exception as e:
            #     print(f"Failed to send alert to ESP32: {e}")
 
while True:
    img_resp=urllib.request.urlopen(url)
    imgnp=np.array(bytearray(img_resp.read()),dtype=np.uint8)
    im = cv2.imdecode(imgnp,-1)
    sucess, img= cap.read()
    blob=cv2.dnn.blobFromImage(im,1/255,(whT,whT),[0,0,0],1,crop=False)
    net.setInput(blob)
    layernames=net.getLayerNames()
    
    # Handle both OpenCV format types (scalar and non-scalar)
    output_layers = net.getUnconnectedOutLayers()
    try:
        outputNames = [layernames[i[0]-1] for i in output_layers]
    except:
        # For newer OpenCV versions
        outputNames = [layernames[i-1] for i in output_layers]
 
    outputs = net.forward(outputNames)
    findObject(outputs,im)
 
    cv2.imshow('IMage',im)
    cv2.waitKey(1)