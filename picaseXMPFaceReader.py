#!/usr/bin/env python
# https://github.com/cvzi/py_save_face_xmp

import gi
import os
import platform
import tempfile
import random
import shutil
import subprocess

gi.require_version('GExiv2', '0.10')
from gi.repository import GExiv2


#https://git.gnome.org/browse/gexiv2/tree/gexiv2/gexiv2-metadata.h
class Imagedata(GExiv2.Metadata):
    def __init__(self, filename):
        super(Imagedata, self).__init__()
        self.open_path(filename)
    
    def save_file(self, path):
        super(Imagedata, self).save_file(path)
        
    def get_tags(self):
        return self.get_exif_tags() + self.get_iptc_tags() + self.get_xmp_tags()
    
    def get(self, key, default=None):
        return self.get_tag_string(key) if self.has_tag(key) else default

    def set(self, key, value):
        return self.set_tag_string(key,value)

    def set_float(self, key, value):
        return self.set_tag_long(key,value)  

    def get_multiple(self, key, default=None):
        return self.get_tag_multiple(key) if self.has_tag(key) else default

    def set_multiple(self, key, values):
        return self.set_tag_multiple(key, values)
    
    def __iter__(self):
        return iter(self.get_tags())
    
    def __contains__(self, key):
        return self.has_tag(key)
    
    def __len__(self):
        return len(self.get_tags())
    
    def __getitem__(self, key):
        if self.has_tag(key):
            return self.get_tag_string(key)
        else:
            raise KeyError('%s: Unknown tag' % key)
    
    def __delitem__(self, key):
        if self.has_tag(key):
            self.clear_tag(key)
        else:
            raise KeyError('%s: Unknown tag' % key)
    
    __setitem__ = GExiv2.Metadata.set_tag_string


def copyFile(src, dest):
    buffer_size = min(1024*1024,os.path.getsize(src))
    if(buffer_size == 0):
        buffer_size = 1024
    with open(src, 'rb') as fsrc:
        with open(dest, 'wb') as fdest:
            shutil.copyfileobj(fsrc, fdest, buffer_size)

class XMPFace:
    def __init__(self, imgdata):
        if type(imgdata) == type(""):
            self.img = Imagedata(imgdata)
        else:
            self.img = imgdata
        self.facetags_keys = {
            "dim_u" : "Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:unit",
            "dim_w" : "Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:w",
            "dim_h" : "Xmp.mwg-rs.Regions/mwg-rs:AppliedToDimensions/stDim:h",
            "area_u" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:unit",
            "area_w" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:w",
            "area_h" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:h",
            "area_x" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:x",
            "area_y" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Area/stArea:y",
            "name" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Name",
            "type" : "Xmp.mwg-rs.Regions/mwg-rs:RegionList[%d]/mwg-rs:Type"            
            }

        self.dim_w = None
        self.dim_h = None
        self.cmds = []

    def printTags(self):
        print(self.img.get_xmp_packet())
        
        alltags = self.img.get_tags()
        for s in self.facetags_keys:
            tagname = self.facetags_keys[s].replace("%d","1")
            tagvalue = self.img.get(tagname)
            print("%s" % tagname)
            print("%s" % tagvalue)

    def __getFace(self, index=1):

        key = lambda s: self.facetags_keys[s].replace("%d","%d" % index)

        alltags = self.img.get_tags()
        for s in self.facetags_keys:
            tagname = key(s)
            tagvalue = self.img.get(tagname)
            if tagvalue is None: # all tags must be set, otherwise we assume there is no face saved yet
                return None

        name = self.img.get(key("name")).strip()
        
        img_w = float(self.img.get(key("dim_w")))
        img_h = float(self.img.get(key("dim_h")))
        center_x = float(self.img.get(key("area_x")))
        center_y = float(self.img.get(key("area_y")))
        area_w = float(self.img.get(key("area_w")))
        area_h = float(self.img.get(key("area_h")))

        top_left_x = int((center_x - area_w/2.0) * img_w)
        top_left_y = int((center_y - area_h/2.0) * img_h)

        return (top_left_x, top_left_y, int(area_w * img_w), int(area_h * img_h), name)
        

    def getFaces(self):
        results = []
        j = 0
        for i in range(0,100):
            result = self.__getFace(i)
            if result is not None:
                results.append(result)
            elif result is None and i > 5: # Check only first 5, if nothing was found
                break
                
        
        
        return results

        

    def setDim(self, width, height):
        key = lambda s: self.facetags_keys[s]
        
        self.dim_w = float(width)
        self.dim_h = float(height)
        """
        # This does not work! Cannot set XMP tags with GExiv2.Metadata from gi
        self.img.set(self.facetags_keys["dim_u"], "pixel")
        self.img.set(self.facetags_keys["dim_w"], "%d" % width) 
        self.img.set(self.facetags_keys["dim_h"], "%d" % height)
        """
        # Let's use exiv2 instead
        self.cmds.append("set Xmp.mwg-rs.Regions/mwg-rs:RegionList XmpText type=Bag")
        self.cmds.append("set %s %s" % (key("dim_u"), "pixel"))
        self.cmds.append("set %s %s" % (key("dim_w"), "%d" % width))      
        self.cmds.append("set %s %s" % (key("dim_h"), "%d" % height))

    def setFace(self, top_left_x, top_left_y, area_width, area_height, name, index=0):

        # XMP arrays start at 1 not 0
        index += 1

        regiontype = "Face"

        key = lambda s: self.facetags_keys[s].replace("%d","%d" % index)

        center_x = float(top_left_x) + float(area_width)/2.0
        center_y = float(top_left_y) + float(area_height)/2.0
        rel_x = center_x / self.dim_w
        rel_y = center_y / self.dim_h
        rel_w = float(area_width) / self.dim_w
        rel_h = float(area_height) / self.dim_h
        """
        # This does not work! Cannot set XMP tags with GExiv2.Metadata from gi
        self.img.set(key("area_u"), "normalized")
        self.img.set(key("area_w"), "%f" % rel_w)
        self.img.set(key("area_h"), "%f" % rel_h)
        self.img.set(key("area_x"), "%f" % rel_x) 
        self.img.set(key("area_y"), "%f" % rel_y)
        self.img.set(key("name"), name) 
        self.img.set(key("type"), regiontype)
        """
        # Let's use exiv2 instead
        self.cmds.append("set %s %s" % (key("area_u"), "normalized"))
        self.cmds.append("set %s %s" % (key("area_w"), "%f" % rel_w))
        self.cmds.append("set %s %s" % (key("area_h"), "%f" % rel_h))
        self.cmds.append("set %s %s" % (key("area_x"), "%f" % rel_x))
        self.cmds.append("set %s %s" % (key("area_y"), "%f" % rel_y))
        self.cmds.append("set %s %s" % (key("name"), name))
        self.cmds.append("set %s %s" % (key("type"), regiontype))

    def save_file(self, filename):
        # Save file via temporary file
        temp_dir = tempfile.gettempdir()
        tmpfile = os.path.join(temp_dir, os.path.basename(filename) + (".%d.tmp" % random.randint(0,10000)))
        copyFile(filename,tmpfile)
        
        # Create command file for exiv2
        with open("exiv2.txt", "w") as f:
            f.write("\n".join(self.cmds))
        self.cmds = []

        # Write tags with exiv2
        cmd = 'exiv2 mo -m "exiv2.txt" "%s"' % tmpfile
        if platform.system() == "Windows":
            DETACHED_PROCESS = 0x00000008
            x = subprocess.call(cmd, creationflags=DETACHED_PROCESS)
        else:
            x = subprocess.call(cmd, shell=True)
        
        if x != 0:
            print("Errors occured while editing file with exiv2!")
        
        # Copy file back to orginal file
        copyFile(tmpfile,filename)
        os.remove(tmpfile)
        os.remove("exiv2.txt")
        
    
if __name__ == "__main__":
    # Read tags for all .jpg files in working dir
    images = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.lower().endswith('.jpg'):
                images.append(os.path.join(root, file))
                
    for filename in images:
        print(filename)
        imgdata = Imagedata(filename)
        face = XMPFace(imgdata)
        print (face.getFaces())


