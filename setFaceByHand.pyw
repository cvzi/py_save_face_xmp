#!python3
# https://github.com/cvzi/py_save_face_xmp

import time
import os
import cv2
import re
import numpy as np
try:
    import tkinter
except:
    import Tkinter
    tkinter = Tkinter

from picaseXMPFaceReader import XMPFace


"""
Reads images JPG from current directory

Left mouse:      draw rectangle around face
Right mouse:     reset rectangle
Middle mouse:    select detected face
Enter:           save face to image metadata
Left arrow:      previous image
Right arrow:     skip image

"""


def point_in_rect(px, py, rect, rect_y0=None, rect_x1=None, rect_y1=None):
    if rect_y0 is None:
        if len(rect) == 2:
            (x0, y0), (x1, y1) = rect
        else:
            x0, y0, x1, y1 = rect
    else:
        x0, y0, x1, y1 = rect, rect_y0, rect_x1, rect_y0
    
    return px >= x0 and px <= x1 and py >= y0 and py <= y1

def detectFace(image, grayscaleImage, faceCascade, scale=1.0):
    # Detect faces with opencv

    try:
        detected_faces = faceCascade.detectMultiScale(
            grayscaleImage,
            scaleFactor=1.1,
            minNeighbors=2,
            minSize=(5, 5),
            flags = cv2.CASCADE_SCALE_IMAGE
        )
    except cv2.error as e:
        print("Error while trying to detect faces: detectMultiScale() throw error:")
        print(e)
        return []

    # Draw a rectangle around the detectedfaces
    result = []
    for (x, y, w, h) in detected_faces:
        cv2.rectangle(image, (int(scale*x), int(scale*y)), (int(scale*(x+w)), int(scale*(y+h))), (100, 255, 70), 1)
        result.append((int(scale*x), int(scale*y), int(scale*(x+w)), int(scale*(y+h))))

    return result

def selectFace(imagePath):
    # Open image in window
    global faces
    global orgimage
    global image
    global image2
    global resultRect
    global detectedFaces
    global screenscale
    global ctrl_image
    global ctrl_input_active
    global ctrl_input_str
    global ctrl_changed

    # Set window title
    cv2.setWindowTitle("image", "File: %s" % os.path.basename(imagePath))
    cv2.setWindowTitle("control", "Wait...  Skipping...")
    
    # Read the image
    try:
        image = cv2.imread(imagePath)
        orgimage = image.copy()
    except:
        print("Cannot load %s. Error 01" % imagePath)
        return 1 # error, skip
    
    # Read existing faces from tags
    try:
        facereader = XMPFace(imagePath)
        faces = facereader.getFaces()
        index = len(faces)
    except gi.repository.GLib.Error as e:
        print("Cannot load %s. Error 02" % imagePath)
        return 1 # error, skip

    #if len(faces) > 0:
    #    return 1 # a face exists, skip
    

    # Try to detect faces with opencv
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

    cv2.setWindowTitle("control", "Faces: %d, Detected: %d" % (len(faces), len(detectedFaces)))
        
    # Draw rectangles around the existing faces
    for (x, y, w, h, name) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 120), 3)
        cv2.putText(image, name, (x, y-3), 5, 0.7, (0, 255, 120), 1, 1);


    # Get a name from the filename
    try:
        name = re.sub(r"\s*\d+\.jpe?g$", "", os.path.basename(imagePath).split(",")[index]).strip()
    except:
        name = re.sub(r"\s*\d+\.jpe?g$", "", os.path.basename(imagePath)).strip()
    ctrl_input_str = name
    ctrl_changed = True
        

    # Copy for mouse drawing
    image2 = image.copy()

    resultRect = None

    # Scale image to screen size
    screenscale = min(1.0, screenheight/float(len(image)), screenwidth/float(len(image[0])))

    # Show image in window
    while True:
        screenimage = cv2.resize(image, (0,0), fx=screenscale, fy=screenscale)
        cv2.imshow('image',screenimage)
        ctrl_show_controls()
        k = cv2.waitKey(10)
        if k == -1:
            continue
        
        if not ctrl_input_active:
            if k == ord('q'): # q -> Quit
                cv2.destroyAllWindows()
                raise RuntimeError("Ctrl-C")
            elif k == 10 or k == 13: # Enter -> Save faces
                break
            elif k == 65363 or k == 2555904: # Right arrow -> Skip image
                return 1
            elif k== 65361 or k == 2424832: # Left arrow -> Previous image
                return -1
        elif ctrl_input_active:
            ctrl_changed = True
            if k == 10 or k == 13: # Enter
                ctrl_input_active = False
            elif k == 8 or k == 65288: # Backspace
                ctrl_input_str = ctrl_input_str[0:-1]
            elif k > 27 and k < 127: # Ascii, opencv does not support other characters
                ctrl_input_str += chr(k)
            elif k-65504 > 27 and k-65504 < 127:
                ctrl_input_str += chr(k-65504).upper()
            else:
                ctrl_changed = False
                
            
            

    if resultRect is not None:
        # Save face to metadata
        cv2.setWindowTitle("control", "Saving changes...")
        img_width = len(image[0])
        img_height = len(image)
        
        facereader.setDim(img_width, img_height)

        (x0,y0),(x1,y1) = resultRect
        w = x1 - x0
        h = y1 - y0
        
        facereader.setFace(x0, y0, w, h, ctrl_input_str, index)
        print("Saving to file...")
        facereader.save_file(imagePath)
    return 1

# mouse callback function
def mouse_draw_rect(event,x,y,flags,param):
    global image,image2,ix,iy,drawing
    global resultRect
    global detectedFaces
    global ctrl_changed
    
    x = int(x*1.0/screenscale)
    y = int(y*1.0/screenscale)
    
    if event == cv2.EVENT_MBUTTONDOWN: # Middle mouse button
        # Use detected face, if clicked into rectangle
        for rect in detectedFaces:
            if point_in_rect(x, y, rect):
                cv2.rectangle(image,(rect[0],rect[1]),(rect[2],rect[3]),(255,255,0),2)
                resultRect = [(rect[0],rect[1]),(rect[2],rect[3])]
                ctrl_changed = True
                break
        
    
    elif event == cv2.EVENT_RBUTTONDOWN: # Right mouse button
        # Reset image
        drawing = False
        image = image2.copy()
        resultRect = None
        ctrl_changed = True
        
    elif event == cv2.EVENT_LBUTTONDOWN: # Left mouse button pressed
        # Start rectangle
        drawing = True
        ix,iy = x,y

    if event == cv2.EVENT_MOUSEMOVE: # Moving mouse
        # Drag rectangle
        if drawing == True:
            image = image2.copy()
            if ix < x and iy < y:
                cv2.rectangle(image,(ix,iy),(x,y),(255,255,0),2)

    if event == cv2.EVENT_LBUTTONUP: # Left mouse button released
        # Stop rectangle
        if ix < x and iy < y:
            drawing = False
            cv2.rectangle(image,(ix,iy),(x,y),(255,255,0),2)
            resultRect = [(ix,iy),(x,y)]
            ctrl_changed = True

# mouse callback function
def ctrl_mouse_draw_rect(event,x,y,flags,param):
    global ctrl_input_rect
    global ctrl_input_active
    global ctrl_changed
    
    x = x
    y = y
    
    if event == cv2.EVENT_LBUTTONDOWN: # Left mouse button pressed
        if point_in_rect(x, y, ctrl_input_rect):
            ctrl_input_active = True
            ctrl_changed = True

    ctrl_show_controls()

# Show controls as image
def ctrl_show_controls():
    global ctrl_image
    global ctrl_input_rect
    global ctrl_image_empty
    global ctrl_input_active
    global ctrl_input_str
    global ctrl_changed
    global resultRect
    global faces
    global image2

    if not ctrl_changed:
        return
    ctrl_changed = False

    ctrl_image = ctrl_image_empty.copy()

    # Input name field
    ctrl_input_rect = ((10,10),(400,30))
    color = (255, 50, 50) if ctrl_input_active else (50,50,50)
    cv2.rectangle(ctrl_image, ctrl_input_rect[0], ctrl_input_rect[1], color, 2)
    cv2.putText(ctrl_image, ctrl_input_str, (ctrl_input_rect[0][0], ctrl_input_rect[1][1]-3), 5, 1.0, (0, 0, 0), 1, 1);


    # Faces preview
    startx = 10
    starty = 50
    maxwidth = 70
    maxheight = 70
    for (x, y, w, h, name) in faces:
        face = orgimage[y:y+h,x:x+w]
        if h > maxheight or w > maxwidth:
            scale = min(1.0, maxheight/float(h), maxwidth/float(w))
            face = cv2.resize(face, (0,0), fx=scale, fy=scale)
            h = len(face)
            w = len(face[0])
        ctrl_image[starty:starty+h,startx:startx+w] = face
        cv2.putText(ctrl_image, name[0:12], (startx, starty+maxheight+5), 1, 0.7, (0, 0, 0), 1, 1);

        startx += maxwidth + int(maxwidth*0.1)

    # Result preview
    if resultRect:
        startx = 10
        starty += maxheight + int(maxheight*0.1)
        
        (x0,y0),(x1,y1) = resultRect
        x, y, w, h = x0, y0, x1-x0, y1-y0
        face = orgimage[y:y+h,x:x+w]
        if h > maxheight or w > maxwidth:
            scale = min(1.0, maxheight/float(h), maxwidth/float(w))
            face = cv2.resize(face, (0,0), fx=scale, fy=scale)
            h = len(face)
            w = len(face[0])
        ctrl_image[starty:starty+h,startx:startx+w] = face
        cv2.putText(ctrl_image, ctrl_input_str, (startx, starty+maxheight+5), 1, 0.7, (0, 0, 0), 1, 1);



    cv2.imshow('control', ctrl_image)


if __name__ == "__main__":
    # Walk directory
    fileList = []
    rootdir = '.'
    for root, subFolders, files in os.walk(rootdir):
        for file in files:
            if file.lower().endswith(".jpg") or file.lower().endswith(".jpeg"):
                fileList.append(os.path.join(root,file))

    
    # Detect screen resolution
    root = tkinter.Tk()
    screenwidth = root.winfo_screenwidth()
    screenheight = root.winfo_screenheight()
    root.destroy()
    root = None
    
    # Load patterns for face detection
    cascPath0 = "haarcascade_frontalface_alt.xml"
    cascPath1 = "haarcascade_profileface.xml"

    cascades = [cv2.CascadeClassifier(cascPath0), cv2.CascadeClassifier(cascPath1)]

    # Globals for mouse callback
    drawing = False # true if mouse is pressed
    ix,iy = -1,-1
    screenscale = 1.0
    faces = []
    detectedFaces = []
    orgimage = None
    resultRect = None

    # Create window
    cv2.namedWindow('image')
    cv2.setMouseCallback('image',mouse_draw_rect)
    cv2.moveWindow('image', 0, 0)

    
    # Control window
    ctrl_input_active = False
    ctrl_input_str = ""
    ctrl_changed = True
    
    
    cv2.namedWindow('control')
    cv2.moveWindow('control', 800, 0)

    ctrl_image_empty = np.array([np.array([255, 255, 255], dtype=np.uint8) for i in range(420*220)]).reshape(220,420,3)


    ctrl_show_controls()

    cv2.setMouseCallback('control', ctrl_mouse_draw_rect)


    # Open each file individually
    i = 0
    while i < len(fileList):
        filepath = fileList[i]
        print(filepath)
        resultcode = selectFace(filepath)
        if not resultcode:
            break
            
        i += resultcode
        
        if i < 0:
            i = 0


    cv2.destroyAllWindows()
