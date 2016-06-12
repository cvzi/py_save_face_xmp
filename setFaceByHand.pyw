#!/usr/bin/env python2
# https://github.com/cvzi/py_save_face_xmp

import os
import cv2
import re
from picaseXMPFaceReader import XMPFace

"""
Reads images JPG from current directory

Left mouse:      draw rectangle around face
Right mouse:     reset rectangle
Middle mouse:    select detected face
Enter:           save face to image metadata
Right arrow:     skip image

"""


def point_in_rect(px, py, rect, rect_y0=None, rect_x1=None, rect_y1=None):
    if rect_y0 is None:
        x0, y0, x1, y1 = rect
    else:
        x0, y0, x1, y1 = rect, rect_y0, rect_x1, rect_y0
    
    return px >= x0 and px <= x1 and py >= y0 and py <= y1

def detectFace(image, grayscaleImage, faceCascade, scale=1.0):
    # Detect faces with opencv
    
    detected_faces = faceCascade.detectMultiScale(
        grayscaleImage,
        scaleFactor=1.1,
        minNeighbors=2,
        minSize=(5, 5),
        flags = cv2.CASCADE_SCALE_IMAGE
    )

    # Draw a rectangle around the detectedfaces
    result = []
    for (x, y, w, h) in detected_faces:
        cv2.rectangle(image, (int(scale*x), int(scale*y)), (int(scale*(x+w)), int(scale*(y+h))), (100, 255, 50), 1)
        result.append((int(scale*x), int(scale*y), int(scale*(x+w)), int(scale*(y+h))))

    return result

def selectFace(imagePath):
    # Open image in window
    global image
    global image2
    global resultRect
    global detectedFaces


    # Read the image
    try:
        image = cv2.imread(imagePath)
    except:
        print("Cannot load %s" % imagePath)
        return
    
    # Read existing faces from tags
    try:
        facereader = XMPFace(imagePath)
        faces = facereader.getFaces()
        index = len(faces)
    except:
        print("Cannot load %s" % imagePath)
        return

    # If no existing images were found, try to detect faces with opencv
    if len(faces) == 0:
        print("Finding faces...")
        scale = 400.0 / len(image)
        grayscaleImage = cv2.resize(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), (0,0), fx=scale, fy=scale)
        detectedFaces = []
        for casc in cascades:
            f = detectFace(image, grayscaleImage, casc, scale=1.0/scale)
            if len(f):
                for r in f:
                    detectedFaces.append(r)
            f = detectFace(image, grayscaleImage, casc, scale=1.0/scale)
            if len(f):
                for r in f:
                    detectedFaces.append(r)
        
    # Draw rectangles around the existing faces
    for (x, y, w, h, name) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 120), 3)
        cv2.putText(image, name, (x, y-3), 5, 0.7, (0, 255, 120), 1, 1);

    # Copy for mouse drawing
    image2 = image.copy()

    resultRect = None

    while True:
        cv2.imshow('image',image)
        k = cv2.waitKey(1)
        if k == ord('q'): # q -> Quit
            cv2.destroyAllWindows()
            raise RuntimeError("Ctrl-C")
        elif k == 13: # Enter -> Save faces
            break
        elif k == 2555904: # Right arrow -> Skip image
            resultRect = None
            break  
        

    if resultRect is not None:
        # Save face to metadata
        img_width = len(image[0])
        img_height = len(image)
        
        # Find name for face from filename
        try:
            name = re.sub(r"\s*\d+\.jpe?g$", "", os.path.basename(imagePath).split(",")[index]).strip()
        except:
            name = re.sub(r"\s*\d+\.jpe?g$", "", os.path.basename(imagePath)).strip()
        
        facereader.setDim(img_width, img_height)

        (x0,y0),(x1,y1) = resultRect
        w = x1 - x0
        h = y1 - y0
        
        facereader.setFace(x0, y0, w, h, name, index)
        print("Saving to file...")
        facereader.save_file(imagePath)

# mouse callback function
def mouse_draw_rect(event,x,y,flags,param):
    global image,image2,ix,iy,drawing
    global resultRect
    global detectedFaces

    if event == cv2.EVENT_MBUTTONDOWN: # Middle mouse button
        # Use detected face, if clicked into rectangle
        for rect in detectedFaces:
            if point_in_rect(x, y, rect):
                cv2.rectangle(image,(rect[0],rect[1]),(rect[2],rect[3]),(255,255,0),2)
                resultRect = [(rect[0],rect[1]),(rect[2],rect[3])]
                break
        
    
    if event == cv2.EVENT_RBUTTONDOWN: # Right mouse button
        # Reset image
        drawing = False
        image = image2.copy()
        resultRect = None
        
    if event == cv2.EVENT_LBUTTONDOWN: # Left mouse button pressed
        # Start rectangle
        drawing = True
        ix,iy = x,y

    if event == cv2.EVENT_MOUSEMOVE: # Moving mouse
        # Drag rectangle
        if drawing == True:
            image = image2.copy()
            cv2.rectangle(image,(ix,iy),(x,y),(255,255,0),2)

    if event == cv2.EVENT_LBUTTONUP: # Left mouse button released
        # Stop rectangle
        drawing = False
        cv2.rectangle(image,(ix,iy),(x,y),(255,255,0),2)
        resultRect = [(ix,iy),(x,y)]

if __name__ == "__main__":
    # Load patterns for face detection
    cascPath0 = "haarcascade_frontalface_alt.xml"
    cascPath1 = "haarcascade_profileface.xml"

    cascades = [cv2.CascadeClassifier(cascPath0), cv2.CascadeClassifier(cascPath1)]

    # Globals for mouse callback
    drawing = False # true if mouse is pressed
    ix,iy = -1,-1

    # Create window
    cv2.namedWindow('image')
    cv2.setMouseCallback('image',mouse_draw_rect)

    # Walk directory
    fileList = []
    rootdir = '.'
    for root, subFolders, files in os.walk(rootdir):
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".jpeg"):
                fileList.append(os.path.join(root,file))

    # Open each file individually
    for filepath in fileList:
        print(filepath)
        selectFace(filepath)


    cv2.destroyAllWindows()
