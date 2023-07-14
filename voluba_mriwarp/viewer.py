import math
import tkinter as tk
import warnings
from tkinter import ttk

import numpy as np
import pandas as pd
from PIL import Image, ImageTk

from voluba_mriwarp.config import *


class ImageCanvas:
    """Canvas to interactively view an image
    Source: https://github.com/foobar167/junkyard/tree/master/manual_image_annotation1/polygon/gui_canvas.py
    """

    def __init__(self, master, image):
        """Initialize the canvas.

        :param master: tkinter parent widget
        :param numpy.ndarray image: 2D image to display
        """
        self.zoom = 1.0
        # zoom magnitude
        self.__delta = 1.3
        self.__filter = Image.LANCZOS
        self.__previous_keyboard_state = 0
        self.image = np.asarray(image, dtype=np.uint8)
        self.__annotation = (-1, -1, -1)

        # frame containing the canvas with the image
        self.__image_frame = ttk.Frame(master)

        self.canvas = tk.Canvas(
            self.__image_frame, highlightthickness=0, background=viewer_bg)
        self.canvas.grid(column=0, row=0, sticky='nswe')
        self.canvas.update()

        # Bind events to the canvas.
        self.canvas.bind('<Configure>', lambda event: self.__show_image())
        self.canvas.bind('<ButtonPress-1>', self.__move_from)
        self.canvas.bind('<Double-Button-1>', self.__annotate)
        self.canvas.bind('<B1-Motion>', self.__move_to)
        # zoom for Windows and macOS
        self.canvas.bind('<MouseWheel>', self.__wheel)
        # zoom for Linux, wheel scroll down
        self.canvas.bind('<Button-5>', self.__wheel)
        # zoom for Linux, wheel scroll up
        self.canvas.bind('<Button-4>', self.__wheel)

        # Handle keystrokes in idle mode.
        self.canvas.bind(
            '<Key>', lambda event: self.canvas.after_idle(
                self.__keystroke, event))

        Image.MAX_IMAGE_PIXELS = 1000000000
        # Suppress DecompressionBombWarning.
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.__image = Image.fromarray(self.image)
        self.image_width, self.image_height = self.__image.size
        self.__min_side = min(self.image_width, self.image_height)

        # Create an image pyramid.
        self.__pyramid = [Image.fromarray(self.image)]

        # Set the ratio coefficient for the image pyramid.
        self.__ratio = 1.0
        self.__current_image = 0
        self.__scale = self.zoom * self.__ratio
        self.__reduction = 2
        w, h = self.__pyramid[-1].size
        while w > 512 and h > 512:
            w /= self.__reduction
            h /= self.__reduction
            self.__pyramid.append(
                self.__pyramid[-1].resize((int(w), int(h)), self.__filter))

        # Put the image into a rectangle and use it to set proper coordinates 
        # to the image
        self.container = self.canvas.create_rectangle(
            (0, 0, self.image_width, self.image_height), width=0)
        self.__show_image()
        self.canvas.focus_set()

    def get_annotation(self):
        """Return coordinates of annotated point on canvas."""
        return self.__annotation

    def check_outside(self, x, y):
        """Check if the point (x, y) is outside the image area.

        :param float x: x coordinate of the point
        :param float y: y coordinate of the point
        :return: True if the point is outside, False otherwise
        :rtype: bool
        """
        bbox = self.canvas.coords(self.container)
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]:
            return False
        else:
            return True

    def crop(self, bbox):
        """Crop a rectangle from the image.

        :param list bbox: coordinates to crop at
        :return: cropped image
        :rtype: PIL.Image
        """
        return self.__pyramid[0].crop(bbox)

    def move_image_to_center(self):
        """Move the image to the center of the canvas."""
        # Fake an event.
        event_from = pd.Series(
            data={'x': self.image_width // 2, 'y': self.image_height // 2},
            index=['x', 'y'])
        event_to = pd.Series(
            data={'x': self.canvas.winfo_width() // 2,
                  'y': self.canvas.winfo_height() // 2},
            index=['x', 'y'])
        self.__move_from(event_from)
        self.__move_to(event_to)

    def __show_image(self):
        """Show the image on the canvas."""
        image_box = self.canvas.coords(self.container)
        canvas_box = (self.canvas.canvasx(0),
                      self.canvas.canvasy(0),
                      self.canvas.canvasx(self.canvas.winfo_width()),
                      self.canvas.canvasy(self.canvas.winfo_height()))
        image_box_int = tuple(map(int, image_box))
        scroll_box = [
            min(image_box_int[0],
                canvas_box[0]),
            min(image_box_int[1],
                canvas_box[1]),
            max(image_box_int[2],
                canvas_box[2]),
            max(image_box_int[3],
                canvas_box[3])]

        # horizontal part of the image in visible area
        if scroll_box[0] == canvas_box[0] and scroll_box[2] == canvas_box[2]:
            scroll_box[0] = image_box_int[0]
            scroll_box[2] = image_box_int[2]
        # vertical part of the image in visible area
        if scroll_box[1] == canvas_box[1] and scroll_box[3] == canvas_box[3]:
            scroll_box[1] = image_box_int[1]
            scroll_box[3] = image_box_int[3]

        self.canvas.configure(scrollregion=tuple(map(int, scroll_box)))

        x1 = max(canvas_box[0] - image_box[0], 0)
        y1 = max(canvas_box[1] - image_box[1], 0)
        x2 = min(canvas_box[2], image_box[2]) - image_box[0]
        y2 = min(canvas_box[3], image_box[3]) - image_box[1]

        # Show image if it in the visible area.
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:
            image = self.__pyramid[max(0, self.__current_image)].crop((
                int(x1 / self.__scale),
                int(y1 / self.__scale),
                int(x2 / self.__scale),
                int(y2 / self.__scale)))
            
            tk_image = ImageTk.PhotoImage(image.resize(
                (int(x2 - x1), int(y2 - y1)), self.__filter))
            image_id = self.canvas.create_image(
                max(canvas_box[0], image_box_int[0]), 
                max(canvas_box[1], image_box_int[1]), 
                anchor='nw', image=tk_image)
            self.canvas.lower(image_id)
            self.canvas.imagetk = tk_image

    def __wheel(self, event):
        """Zoom using the mouse wheel."""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.check_outside(x, y):
            return

        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event.
        # scroll down = zoom out
        if event.num == 5 or event.delta == -120:
            if round(self.__min_side * self.zoom) < 30:
                return
            self.zoom /= self.__delta
            scale /= self.__delta
        # scroll up = zoom in
        if event.num == 4 or event.delta == 120:
            zoom = min(
                self.canvas.winfo_width(),
                self.canvas.winfo_height()) >> 1
            if zoom < self.zoom:
                return
            self.zoom *= self.__delta
            scale *= self.__delta

        # Take an appropriate image from the pyramid.
        k = self.zoom * self.__ratio
        self.__current_image = min(
            (-1) * int(math.log(k, self.__reduction)),
            len(self.__pyramid) - 1)
        self.__scale = k * math.pow(self.__reduction,
                                    max(0, self.__current_image))

        # Rescale all objects.
        self.canvas.scale('all', x, y, scale, scale)
        # Rescale the annotated point.
        if self.canvas.find_withtag('annotation'):
            x1, y1, x2, y2 = self.canvas.coords('annotation')
            x = x1 + (x2 - x1) / 2
            y = y1 + (y2 - y1) / 2
            self.canvas.scale('annotation', x, y, 1 / scale, 1 / scale)

        self.redraw_figures()
        self.__show_image()

    def __keystroke(self, event):
        """Scrolling with the keyboard."""
        # Control-key pressed
        if event.state - self.__previous_keyboard_state == 4:
            pass
        else:
            self.__previous_keyboard_state = event.state
            # Up, Down, Left, Right keystrokes
            # scroll right: keys 'D', 'Right' or 'Numpad-6'
            if event.keycode in [68, 39, 102]:
                self.__scroll_x('scroll', 1, 'unit', event=event)
            # scroll left: keys 'A', 'Left' or 'Numpad-4'
            elif event.keycode in [65, 37, 100]:
                self.__scroll_x('scroll', -1, 'unit', event=event)
            # scroll up: keys 'W', 'Up' or 'Numpad-8'
            elif event.keycode in [87, 38, 104]:
                self.__scroll_y('scroll', -1, 'unit', event=event)
            # scroll down: keys 'S', 'Down' or 'Numpad-2'
            elif event.keycode in [83, 40, 98]:
                self.__scroll_y('scroll', 1, 'unit', event=event)

    def __scroll_x(self, *args, **kwargs):
        """Scroll canvas horizontally and redraw the image."""
        self.canvas.xview(*args)
        self.__show_image()

    def __scroll_y(self, *args, **kwargs):
        """Scroll canvas vertically and redraw the image."""
        self.canvas.yview(*args)
        self.__show_image()

    def __move_from(self, event):
        """Remember the previous coordinates for scrolling with the mouse."""
        self.canvas.scan_mark(event.x, event.y)

    def __move_to(self, event):
        """Drag the canvas to the new position."""
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.__show_image()

    def __annotate(self, event):
        """Annotate a point on the canvas.

        This method is called when a coordinate is clicked on the canvas.
        """
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.canvas.delete('annotation')
        self.canvas.create_oval(
            x - 3, y - 3, x + 3, y + 3, width=0, fill='gold', tags='annotation')

        bbox = self.canvas.coords(self.container)
        x = (x - bbox[0]) / self.zoom
        y = (y - bbox[1]) / self.zoom
        self.__annotation = (x, self.__slice, y)
        self.__image_frame.master.master.assign_regions2point(self.__annotation)

    def draw(self, x, slice, y):
        """Draw a point on the canvas.

        This method is called when a coordinate is manually entered.

        :param float x: x-coordinate of the annotation
        :param float slice: slice of the image containing the annotation
        :param float y: y-coordinate of the annotation
        """
        self.__annotation = (x, slice, y)

        bbox = self.canvas.coords(self.container)
        x = x * self.zoom + bbox[0]
        y = y * self.zoom + bbox[1]

        self.canvas.delete('annotation')
        self.canvas.create_oval(
            x - 3, y - 3, x + 3, y + 3, width=0, fill='gold', tags='annotation')

    def update(self, image, slice):
        """Update the displayed image to the specified slice.

        :param numpy.ndarray image: 2D image to display
        :param int slice: currently selected slice
        """
        self.image = np.asarray(image, dtype=np.uint8)
        old_scale = self.__scale
        self.__image = Image.fromarray(self.image)
        self.image_width, self.image_height = self.__image.size
        self.__pyramid = [Image.fromarray(self.image)]
        self.__scale = old_scale
        self.__show_image()
        self.__slice = slice

        self.redraw()

    def redraw(self):
        """Redraw the canvas considering the annotated and currently displayed
        slice.
        """
        x, slice, y = self.__annotation
        self.canvas.itemconfig('annotation', state='hidden')
        # Show the annotation if it's on the current slice.
        if self.__slice == slice:
            self.canvas.itemconfig('annotation', state='normal')

    def redraw_figures(self):
        """Dummy function to redraw figures in the children classes."""
        pass

    def pack(self, **kw):
        """Pack widget into the parent widget."""
        self.__image_frame.pack(**kw, expand=True, fill='both')
        self.__image_frame.rowconfigure(0, weight=1)
        self.__image_frame.columnconfigure(0, weight=1)

    def destroy(self):
        """Destroy the canvas and its components."""
        self.__image.close()
        map(lambda i: i.close, self.__pyramid)
        del self.__pyramid[:]
        del self.__pyramid
        self.canvas.destroy()
        self.__image_frame.destroy()


class Viewer(ttk.Frame):
    """Viewer displaying the input NIfTI"""

    def __init__(self, master, image, side, padx, pady):
        """Initialize the viewer.

        :param master: tkinter parent widget
        :param numpy.ndarray image: 2D image to display
        :param str side: side to add the widget for .pack()
        :param int padx: padding in x direction for .pack()
        :param int pady: padding in y direction for .pack()
        """
        ttk.Frame.__init__(self, master=master)
        self.canvas = ImageCanvas(self.master, image)
        self.master.pack_propagate(False)
        self.canvas.pack(side=side, padx=padx, pady=pady)

    def move_image_to_center(self):
        """Move the image to the center of the canvas."""
        self.canvas.move_image_to_center()

    def update_image(self, image, slice):
        """Update the displayed image to the specified slice.

        :param numpy.ndarray image: 2D image to display
        :param int slice: currently selected slice
        """
        self.canvas.update(image, slice)

    def get_annotation(self):
        """Return the current annotation."""
        return self.canvas.get_annotation()

    def draw_annotation(self, x, slice, y):
        """Draw the given annotation onto the canvas.

        :param float x: x-coordinate of the annotation in voxel space
        :param float slice: slice of the image containing the annotation
        :param float y: y-coordinate of the annotation in voxel space
        """
        self.canvas.draw(x, slice, y)

    def redraw_canvas(self):
        """Redraw the canvas considering the annotated and currently displayed
        slice.
        """
        self.canvas.redraw()
