# py_save_face_xmp
Python tool to detect or select faces on jpg images and save the position in the XMP metadata of the image file.

The faces are stored in the JPG metadata in XMP tags. The standard is defined by the [Metadata Working Group Regions schema](http://exiv2.org/tags-xmp-mwg-rs.html). These tags are for example supported by Picasa which can also read and write them. An example path looks like this: `Xmp.mwg-rs.Regions/mwg-rs:RegionList[1]/mwg-rs:Name`

The script uses the GExiv2 python API to read the XMP tags and exiv2 in the command line to write the tags (because writing XMP arrays/bags is not possible with GExiv2).

The images are displayed using opencv and the face detection is also done with opencv


Tested with/required software:
 * [Python](https://www.python.org/downloads/release/python-27/) 2.7 or 3.4
 * [opencv](https://github.com/Itseez/opencv) 3.0.0 for Python
 * [exiv2](http://www.exiv2.org/)  0.25
 * GExiv2 0.10 (on Windows it is included in [PyGObject](http://pygtk.org))


 
Run with `pythonw setFaceByHand.pyw` in the directory of the jpg files.

Controls:
 * Left mouse:      draw rectangle around face
 * Right mouse:     reset rectangle
 * Middle mouse:    select detected face
 * Enter:           save face to image metadata
 * Left arrow:      previous image
 * Right arrow:     skip image
 * q or Ctrl-c:     quit

Currently the name for the faces is taken from the filename like this: `Thomas,Peter,Jake.jpg` results in the first face beeing named Thomas, the second named Peter and the third face named Jake.



This software is licensed under GPLv3, except for the files haarcascade_profileface.xml and haarcascade_frontalface_alt.xml which were taken from [opencv](https://github.com/Itseez/opencv/tree/master/data/haarcascades). Look into the files for details on their licenses.
