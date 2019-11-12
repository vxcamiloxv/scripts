#! /usr/bin/env python2
# -----------------------------------------------------------------------------
# Copyright:  (c) 2012 Felipe Lopez AKA sirgazil
# e-mail:     introsmedia@gmail.com
# License:    http://creativecommons.org/publicdomain/zero/1.0/
#
#             Put in the public domain. You may use, modify and share this
#             program under the Creative Commons Zero legal code.
# -----------------------------------------------------------------------------

"""Export Inkscape file layers to PNG files.

This script ask the user for an Inkscape generated SVG file and exports all
layers as individual PNG files. This was written as solution for:

https://bitbucket.org/introsmedia/pylab/issue/6/

"""

import argparse
import os
import sys


# DEFINE CLI OPTIONS
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-v", "--version", action="version", version="1.0.0",
                    help="version of the program")
parser.add_argument("-i", "--input", type=str, required=True,
                    help="absolute path to the SVG file")
parser.add_argument("-x", "--width", type=int,
                    help="width in pixels to use for layers")
parser.add_argument("-y", "--height", type=int,
                    help="width in pixels to use for layers")
args = parser.parse_args()
display = Display()  # a custom display to show text in color


# FUNCTION DEFINITIONS
def main():
    """Main program function."""
    # Open SVG source
    svg = SVG(args.input)

    # Show basic SVG info
    msg = "Working with {}".format(svg.filename)
    display.print_in_color(msg, "Yellow")
    print("{} layer(s) found...".format(svg.count_layers()))

    # Export layers
    if args.width and args.height:
        layersize = [args.width, args.height]
    else:
        layersize = []
    
    try:
        svg.export_layers(size=layersize)
    except OSError as error:
        msg = "ERROR: couldn't create layers directory"
        display.print_in_color(msg, "Red")
        print(error)
        sys.exit()
    except IOError as error:
        display.print_in_color("ERROR: couldn't export all layers", "Red")
        print(error)
        sys.exit()
    else:
        display.print_in_color("Layers exported", "Yellow")


# MAIN PROGRAM
if os.path.exists(args.input):
    if os.path.isfile(args.input):
        main()
    else:
        display.print_in_color("ERROR: input must be a file", "Red")
        sys.exit()
else:
    display.print_in_color("ERROR: could not find the file", "Red")
    sys.exit()
    
    

"""Inky core functionality."""

import math
import os
import subprocess
import sys

from lxml import etree
from PIL import Image


# XML namespaces in lxml syntax
SVG_SPACE = "{http://www.w3.org/2000/svg}"
INK_SPACE = "{http://www.inkscape.org/namespaces/inkscape}"


class SVG:
    """Represents an Inkscape SVG file."""
    def __init__(self, path):
        """Constructor method.
        
        Parameters
        
        path (string)
            Absolute path to the SVG file.
            
            If the path cannot be opened, an IOError is raised.
        
        """
        self.path = path
        self.dir = os.path.dirname(path)
        self.filename = os.path.basename(path)
        self.tree = etree.parse(path) # SVG element tree
    
    
    def get_layers(self):
        """Return the list of layers from the SVG file."""
        root = self.tree.getroot()
        
        return list(root.iterchildren(SVG_SPACE + "g"))
            
    
    def count_layers(self):
        """Return the number of layers in the SVG file."""        
        return len(self.get_layers())
    
    
    def separate_layers(self, path=""):
        """Create a separate SVG file for each layer in the SVG file.

        Parameters

        path (string)
            An optional absolute path to the directory where the layers will
            be saved.
            
            If ``path`` is not provided, all layers are saved at the same
            level of the source file (``SVG.dir``), in a directory called
            ``[SVG.filename]_svg_layers``.

        Return

        (string) an absolute path to the directory where the layers were
        saved.
        
        Exceptions
        
        OSError
            If the path cannot be created, an OSError is raised.
        
        IOError
            If any SVG layer file cannot be written to disk, IOError is
            raised.

        """
        # Create a directory to store the SVGs
        print("Creating SVG layers directory...")
        dirname = "{}_svg_layers".format(self.filename.replace(".svg", ""))
        layerspath = os.path.join(self.dir, dirname)
        os.mkdir(layerspath)
        print(layerspath)

        # Write each layer as an SVG file
        # NOTE: this actually writes copies of the source SVG file with the
        # appropriate layers visible.
        print("Separating layers into individual SVGs...")
        root = self.tree.getroot()
        root_children = list(root.iterchildren())
        
        for i in range(len(root_children)):
            # If SVG root[i] element is a layer (an SVG g element)
            if root[i].tag == SVG_SPACE + "g":
                layer_id = root[i].get("id")
                layer_label = root[i].get(INK_SPACE + "label")
                
                # Ignore layers according to tags in their name
                if ("(ignore)" in layer_label or
                    "(fg)" in layer_label or
                    "(bg)" in layer_label):
                    continue
                else:
                    print("{}: {}...".format(layer_id, layer_label))
                
                # Create a copy of root
                modroot = root
                
                # Make invisible all but the current layer from modroot and
                # layers whose names contain foreground '(fg)' or background
                # '(bg)' tags.
                for j in range(len(root_children)):
                    if (modroot[j].tag == SVG_SPACE + "g" and
                        modroot[j] != root[i]):
                        if ("(fg)" in modroot[j].get(INK_SPACE + "label") or
                            "(bg)" in modroot[j].get(INK_SPACE + "label")):
                            modroot[j].set("style", "display:inline")
                        else:
                            modroot[j].set("style", "display:none")
                    else:
                        # Make current layer visible
                        modroot[j].set("style", "display:inline")
                
                # Convert root copy to string and save to disk as a layer
                svglayer = etree.tostring(modroot, encoding="UTF-8",
                                          standalone=False, pretty_print=True)
                filename = "layer_{}.svg".format(str(i).zfill(4))
                filepath = os.path.join(layerspath, filename)

                layer_file = open(filepath, "w")
                layer_file.write(svglayer)
                layer_file.close()
                
                # Inform status
                print(filepath)

        
        return layerspath
    
    
    def export_layers(self, path="", size=[]):
        """Convert layers in the SVG file to a PNG images.

        path (string)
            An optional absolute path to the directory where the layers will
            be saved.
            
            If ``path`` is not provided, all layers are saved at the same
            level of the source file (``SVG.dir``), in a directory called
            ``[SVG.filename]_png_layers``.
        
        size (list)
            An optional 2 elements list indicating exported images width and
            size.
            
            If not provided, images size will default to source SVG page
            size.

        Return

        (string) an absolute path to the directory where the layers were
        saved.
        
        Exceptions
        
        OSError
            If the path cannot be created, an OSError is raised.

        """
        # Create a directory to store the PNGs
        print("Creating PNG layers directory...")
        dirname = "{}_png_layers".format(self.filename.replace(".svg", ""))
        pngspath = os.path.join(self.dir, dirname)
        os.mkdir(pngspath)
        print(pngspath)

        # Convert layers to SVG and get the path to them
        print("Exporting layers into individual PNGs...")
        layerspath = self.separate_layers()
        
        # Call Inkscape to export each layer to PNG
        layers = os.listdir(layerspath)
        
        for layer in layers:
            print("{}...".format(layer))
            layerpath = os.path.join(layerspath, layer)
            pngpath = os.path.join(pngspath, layer.replace(".svg", ".png"))
            
            if size:
                command = "inkscape -C -e {} -d 200 -w {} -h {} -f {}"
                command = command.format(pngpath, size[0], size[1], layerpath)
            else:
                command = "inkscape -C -e {} -d 200 -f {}"
                command = command.format(pngpath, layerpath)
            
            process = subprocess.Popen(command, shell=True)
            result = process.wait()

            if result == 0:
                print(pngpath)
            else:
                print("Failed")
        
        
        return pngspath


"""ANSI escape sequences module.

This module provides some classes to format, color and control text
output in text terminals.

For more information about ANSI escape sequences, read
http://en.wikipedia.org/wiki/ANSI_escape_code

"""

import sys


class Display(object):
    """Represent the terminal screen.

    Instances of this class provide the main methods for manipulating
    cursor position, erase the screen, update and append output and
    display mode such as forground and background colors.

    """    
    def __init__(self):
        """Initialize the object."""
        pass

    def print_in_bold(self, string):
        """Print a string in bold."""
        self.turn_bold()
        print(string)
        self.turn_fx_off()

    def print_in_color(self, string, fg_color="White", bg_color="",
                       bold=False):
        """Print a colored string."""
        self.set_fg_color(fg_color)
        self.set_bg_color(bg_color)
        if bold:
            self.turn_bold()
        print(string)
        self.turn_fx_off()

    def turn_bold(self):
        """Turn text output bold."""
        sys.stdout.write("\033[1m")

    def turn_fx_off(self):
        """Turn all attributes off."""
        sys.stdout.write("\033[0m")

    def erase(self):
        """Erase display.

        Clear the screen and move the cursor to the home position
        (line 0, column 0).

        """
        sys.stdout.write("\033[2J")

    def set_fg_color(self, color):
        """Set forground color.

        Parameters:

        color (str) -- The name of the color. It can be Black, Red,
        Green, Yellow, Blue, Magenta, Cyan and White.

        """
        colors = {"Black": 30, "Red": 31, "Green": 32, "Yellow": 33,
                  "Blue": 34, "Magenta": 35, "Cyan": 36, "White": 37}

        if color in colors:
            sys.stdout.write("\033[{0}m".format(colors[color]))

    def set_bg_color(self, color):
        """Set background color.

        Parameters:

        color (str) -- The name of the color. It can be Black, Red,
        Green, Yellow, Blue, Magenta, Cyan and White.

        """
        colors = {"Black": 40, "Red": 41, "Green": 42, "Yellow": 43,
                  "Blue": 44, "Magenta": 45, "Cyan": 46, "White": 47}

        if color in colors:
            sys.stdout.write("\033[{0}m".format(colors[color]))

