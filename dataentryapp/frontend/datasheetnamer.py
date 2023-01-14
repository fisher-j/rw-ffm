"""
@created: 2018-08-19 18:00:00
@author: (c) 2018-2019 Jorj X. McKie
Display a PyMuPDF Document using Tkinter
-------------------------------------------------------------------------------
Dependencies:
-------------
PyMuPDF v1.14.5+, Tkinter

License:
--------
GNU GPL V3+

Description
------------
Get filename and start displaying page 1. Please note that all file types
of MuPDF are supported (including EPUB e-books and HTML files for example).
Pages can be directly jumped to, or buttons can be used for paging.

This version contains enhancements:
* PIL no longer needed
* Zooming is now flexible: only one button serves as a toggle. Keyboard arrow keys can
  be used for moving through the window when zooming.

We also interpret keyboard events (PageDown / PageUp) and mouse wheel actions
to support paging as if a button was clicked. Similarly, we do not include
a 'Quit' button. Instead, the ESCAPE key can be used, or cancelling the form.
To improve paging performance, we are not directly creating pixmaps from
pages, but instead from the fitz.DisplayList of the page. Each display list
will be stored in a list and looked up by page number. This way, zooming
pixmaps and page re-visits will re-use a once-created display list.

 """

import sys
sys.path.append("dataentryapp/backend")
import fitz
from pathlib import Path

if not list(map(int, fitz.VersionBind.split("."))) >= [1, 14, 5]:
    raise SystemExit("need PyMuPDF v1.14.5 for this script")

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

import tkinter as tk
from tkinter import OptionMenu, filedialog as fd
from tkinter import messagebox as mb
from tkinter import ttk

from dataentryapp.backend import backend

from ttkwidgets.autocomplete import AutocompleteCombobox


class PdfFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent
        self.filename = parent.filename
        self.doc = fitz.open(self.filename)
        self.page_count = len(self.doc)
        self.cur_page = 0
        self.zoom = False
        self.cur_pos = (0, 0)
        self.move = (0, 0)
        self.rotation = 0
        self.max_size = parent.max_size

        self.pdf_frame_widgets()

# ------------------------------------------------------------------------------
# Reload rendered View of page of current page
# ------------------------------------------------------------------------------
    def get_page(self):
        """Return a tkinter.PhotoImage or a PNG image for a document page number.
        :arg int pno: 0-based page number
        :arg zoom: top-left of old clip rect, and one of -1, 0, +1 for dim. x or y
                to indicate the arrow key pressed
        :arg max_size: (width, height) of available image area
        :arg bool first: if True, we cannot use tkinter
        """
        # set page rotation
        rot_angle = [0, 90, 180, 270]
        self.doc[self.cur_page].set_rotation(rot_angle[self.rotation % len(rot_angle)])
        pdfpage = self.doc[self.cur_page]
        r = pdfpage.rect
        
        # ensure image fits screen:
        # exploit, but do not exceed width or height
        zoom_0 = 1
        if self.max_size:
            zoom_0 = min(1, self.max_size[0] / r.width, self.max_size[1] / r.height)
            if zoom_0 == 1:
                zoom_0 = min(self.max_size[0] / r.width, self.max_size[1] / r.height)

        mat_0 = fitz.Matrix(zoom_0, zoom_0)

        if not self.zoom:  # show the total page
            pix = pdfpage.get_pixmap(matrix=mat_0, alpha=False)
            clip = r
        else:
            w2 = self.max_size[0] / (2 * zoom_0)  # clip size before zoom
            h2 = self.max_size[1] / (2 * zoom_0)  # ...
            tl = self.cur_pos  # old top-left
            tl.x += self.move[0] * (r.width - w2) / 2  # adjust topl-left ...
            tl.x = max(0, tl.x)  # according to ...
            tl.x = min(r.width - w2, tl.x)  # arrow key ...
            tl.y += self.move[1] * (r.height - h2) / 2 # provided, but ...
            tl.y = max(0, tl.y)  # stay within ...
            tl.y = min(r.height - h2, tl.y)  # the page rect
            clip = fitz.Rect(tl, tl.x + w2, tl.y + h2)
            # clip rect is ready, now fill it
            mat = mat_0 * fitz.Matrix(2, 2)  # zoom matrix
            # pix = dlist.get_pixmap(alpha=False, matrix=mat, clip=clip)
            pix = pdfpage.get_pixmap(alpha=False, matrix=mat, clip=clip)
        
        img = pix.tobytes("ppm")  # make PPM image from pixmap for tkinter

        self.cur_pos = clip.tl
        self.move = (0, 0)
        page_img = tk.PhotoImage(data = img)
        return page_img
       
    def update_pdf_image(self):
        self.page_image = self.get_page()
        self.canvas.itemconfig(self.image_container, image=self.page_image)
        pg_lab = "page " + str(self.cur_page + 1) + " of " + str(self.page_count)
        self.cur_pg_lab.config(text=pg_lab)

# ------------------------------------------------------------------------------
# define the buttons / events we want to handle

    def press_Next(self):
        self.cur_page += 1
        # sanitize page number
        if self.cur_page >= self.page_count: # don't wrap around
            self.cur_page = self.page_count - 1
        if self.cur_page < 0:  # pages < 0 are valid but look bad
            self.cur_page = 0
        # Refresh page image
        self.update_pdf_image()

    def press_Prior(self):
        self.cur_page -= 1
        # sanitize page number
        if self.cur_page >= self.page_count:  # don't wrap around
            self.cur_page = self.page_count - 1
        while self.cur_page < 0:  # pages < 0 are valid but look bad
            self.cur_page = 0
        self.update_pdf_image()


    def press_Zoom(self):
        if not self.zoom:
            self.zoom = True
        else:
            self.zoom = False
        self.update_pdf_image()

        
    def press_Rotate(self):
        self.rotation += 1
        self.update_pdf_image()
        

    def press_Left(self, event):
        if self.zoom:
            self.move = (-1, 0)
        self.update_pdf_image()

    def press_Right(self, event):
        if self.zoom:
            self.move = (1, 0)
        self.update_pdf_image()

    def press_Up(self, event):
        if self.zoom:
            self.move = (0, -1)
        self.update_pdf_image()

    def press_Down(self, event):
        if self.zoom:
            self.move = (0, 1)
        self.update_pdf_image()

    def save_datasheet(self, filename):
        outdoc = fitz.open()
        outdoc.insert_pdf(self.doc, from_page = self.cur_page, to_page = self.cur_page)
        outdoc.save(filename)
        outdoc.close()

    def press_Save(self):
        right_frame = self.parent.right_frame
        treatment_id = [
            right_frame.option_var.get(),
            right_frame.e_type.get(),
            right_frame.e_site.get(),
            right_frame.e_treatment.get(),
            right_frame.e_burn.get()
        ]
        
        plot_num = [v.strip() for v in right_frame.e_plot.get().split(",")]
        
        # dictionary of values pass to backend functions
        key_names = ("stage", "type", "site", "treatment", "burn")
        collection = {n: v for n, v in zip(key_names, treatment_id)}
        
        # only allow values listed in autocomplete list
        bad = backend.flag_bad_values(collection, plot_num, right_frame.comp_opt)

        if bad:
            mb.showerror(
                "Really?",
                "\n".join(bad) + "\n continue?",
                parent=self.parent)
            return None
        
        # Only single plot data sheets are named with their plot number
        # plot number is ommited for regen datasheets
        col = collection.copy()
        col["plotnum"] = plot_num
        filename = backend.make_unique_filename(col)

        # check database if combination of stage, datatype, site, treatment, burn, plot
        # exists already.
        prior_collection = []
        prior_plotid = []
        col = collection.copy()
        plot_num = [int(n) for n in plot_num]
        for p in plot_num:
            col["plotnum"] = p
            clct = backend.search_collectid(col)
            prior_collection.append(clct)
            pltid = backend.search_plotid(col)
            prior_plotid.append(pltid)
        print("prior collections: ",  prior_collection)
        print("prior plotids: ", prior_plotid)

        # Check if there is an existing corrosponding collection
        if any(prior_collection):
            collection_exists = [p[0] for p in zip(plot_num, prior_collection) if p[1]]
            print("collection exists: ", collection_exists)
            if collection_exists:
                response = mb.askquestion(
                    "Real?", 
                    "These data exist for plot(s) " + 
                        " ,".join([str(s) for s in collection_exists]) + 
                        ". Add another page?")
                if response == "no":
                    return None

        # If no further problems save datasheet and get datasheet id
        self.save_datasheet(filename)
        datasheetid = backend.insert_datasheet(filename)

        # Iterate over plots associated with datasheet and enter corrosponding plot
        # and collection table entries.
        for p in range(len(plot_num)):
            col = collection.copy()
            if prior_collection[p]:
                backend.link_datasheet(prior_collection[p], datasheetid)
            elif prior_plotid[p]:
                col["plotid"] = prior_plotid[p]
                col["plotnum"] = plot_num[p]
                collectid = backend.insert_collectid(col)
                backend.link_datasheet(collectid, datasheetid)
            else:
                col["plotnum"] = plot_num[p]
                plotid = backend.insert_plot(col)
                col["plotid"] = plotid
                collectid = backend.insert_collectid(col)
                backend.link_datasheet(collectid, datasheetid)

        mb.showinfo(title="File saved", message="Datasheet entered.")
   
        # # return focus for more data entry
        right_frame.e_type.focus_set()
        right_frame.e_type.select_range(0, "end")
        right_frame.e_plot.delete(0, "end")
        self.press_Next()

    def press_Complete(self):
        if mb.askquestion("Finished?", "Close and mark as DONE?") == "yes":
            self.doc.close()
            p = Path(self.filename)
            done = Path(p.parent, "DONE_" + p.name)
            p.rename(done)
            self.parent.destroy()


######################################################
############## Begin GUI #############################
######################################################

    def pdf_frame_widgets(self):
        # Left frame widgets
        pg_lab = "page " + str(self.cur_page + 1) + " of " + str(self.page_count)
        self.cur_pg_lab = tk.Label(self, text = pg_lab)
        self.page_image = self.get_page()
        self.canvas = tk.Canvas(self, width=self.max_size[0], 
            height=self.max_size[1], bg="lavender", highlightbackground="black")
        self.image_container = self.canvas.create_image(1, 1, anchor = "nw", image=self.page_image)

        self.canvas.bind("<1>", lambda event: self.canvas.focus_set())
        self.canvas.bind("<Left>", self.press_Left)
        self.canvas.bind("<Right>", self.press_Right)
        self.canvas.bind("<Up>", self.press_Up)
        self.canvas.bind("<Down>", self.press_Down)

        # Left frame widget layout
        self.columnconfigure(0, weight=1)
        self.cur_pg_lab.grid(row=0, column=0, padx=5, pady=5)
        self.canvas.grid(row=1, column=0)


################ Begin right frame ##################

class RightFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.comp_opt = {
            "stage": ["1", "2", "3"],
            "type": ["fuel", "veg", "wood", "tree", "regen",],
            "site": ["bob", "camp8", "crib", "dun", "fair", "hare"],
            "treatment": ["ls", "m", "np"],
            "burn": ["b", "nb"]
        }

        self.right_top = ttk.Frame(self)
        self.right_bottom = ttk.Frame(self)
        self.right_top.grid(row=0, column=0)
        self.right_bottom.grid(row=1, column=0)

        # right-top frame widgets
        self.b_prev = tk.Button(self.right_top, text = "Prev", width=7, command=parent.pdf_frame.press_Prior)
        self.b_next = tk.Button(self.right_top, text = "Next", width=7, command=parent.pdf_frame.press_Next)
        self.b_zoom = tk.Button(self.right_top, text = "Zoom", width=7, command=parent.pdf_frame.press_Zoom)
        self.b_rotate = tk.Button(self.right_top, text = "Rotate", width=7, command=parent.pdf_frame.press_Rotate)

        # right-top frame widget layout

        self.right_top.rowconfigure(0, weight=1)
        self.right_top.columnconfigure(0, weight=1)
        self.right_top.columnconfigure(1, weight=1)
        self.right_top.columnconfigure(2, weight=1)
        self.right_top.columnconfigure(3, weight=1)

        self.b_prev.grid(row=0, column=0, sticky="s", pady=10)
        self.b_next.grid(row=0, column=1, sticky="s", pady=10)
        self.b_zoom.grid(row=0, column=2, sticky="s", pady=10)
        self.b_rotate.grid(row=0, column=3, sticky="s", pady=10)


        # right bottom frame widgets
        self.l_stage = tk.Label(self.right_bottom, text="Stage", anchor="w")
        self.l_type = tk.Label(self.right_bottom, text="Datatsheet type", anchor="w")
        self.l_site = tk.Label(self.right_bottom, text="Site", anchor="w")
        self.l_treatment = tk.Label(self.right_bottom, text="Treatment", anchor="w")
        self.l_burn = tk.Label(self.right_bottom, text="Burn/No burn", anchor="w")
        self.l_plot = tk.Label(self.right_bottom, text="Plot number", anchor="w")

        self.option_var = tk.StringVar(self)
        self.e_stage = ttk.OptionMenu(
            self.right_bottom,
            self.option_var,
            "1",
            *self.comp_opt["stage"])
        self.e_type = AutocompleteCombobox(self.right_bottom)
        self.e_site = AutocompleteCombobox(self.right_bottom)
        self.e_treatment = AutocompleteCombobox(self.right_bottom)
        self.e_burn = AutocompleteCombobox(self.right_bottom)
        self.e_plot = ttk.Entry(self.right_bottom)

        
        self.e_type.set_completion_list(self.comp_opt["type"])
        self.e_site.set_completion_list(self.comp_opt["site"])
        self.e_treatment.set_completion_list(self.comp_opt["treatment"])
        self.e_burn.set_completion_list(self.comp_opt["burn"])

        self.b_save = tk.Button(self.right_bottom, text="Save and next", command=parent.pdf_frame.press_Save)
        self.b_complete = tk.Button(self.right_bottom, text="Close and mark DONE", command=parent.pdf_frame.press_Complete)

        # right bottom frame widget layout
        self.l_stage.grid(row=0, column=0, sticky="ew", padx=4)
        self.l_type.grid(row=1, column=0, sticky="ew", padx=4)
        self.l_site.grid(row=2, column=0, sticky="ew", padx=4)
        self.l_treatment.grid(row=3, column=0, sticky="ew", padx=4)
        self.l_burn.grid(row=4, column=0, sticky="ew", padx=4)
        self.l_plot.grid(row=5, column=0, sticky="ew", padx=4)

        self.e_stage.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
        self.e_type.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
        self.e_site.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        self.e_treatment.grid(row=3, column=1, sticky="ew", padx=4, pady=2)
        self.e_burn.grid(row=4, column=1, sticky="ew", padx=4, pady=2)
        self.e_plot.grid(row=5, column=1, sticky="ew", padx=4, pady=2)

        self.b_save.grid(row=6, column=0, columnspan=2, pady=4)
        self.b_complete.grid(row=7, column=0, columnspan=2, pady=4)


class App(tk.Toplevel):
    def __init__(self, parent, filename):
        super().__init__(parent)

        self.parent = parent
        self.filename = filename
        self.wait_visibility()
        self.focus()
        self.grab_set()
        self.stage = "1"
        
        self.get_dimensions()

        self.title("Rename datasheets")
        self.iconbitmap("./dataentryapp/frontend/tree_icon.ico")
        
        # Make frames
        self.pdf_frame = PdfFrame(self)
        self.right_frame = RightFrame(self)

        # and arrange them
        self.pdf_frame.grid(row=0, column=0)
        self.right_frame.grid(row=0, column=1)

        self.bind("<Destroy>", self.on_destroy)

    def on_destroy(self, event):
        if event.widget == self:
            self.parent.update_dataview()
    
    def get_dimensions(self):
        # get physical screen dimension to determine the page image max size
        testwindow = tk.Toplevel(self)
        max_width = testwindow.winfo_screenwidth() - 20
        max_height = testwindow.winfo_screenheight() - 135
        # max size is a square
        sm_side = min(max_height, max_width)
        self.max_size = (sm_side, sm_side)
        testwindow.destroy()
        del testwindow


if __name__ == "__main__":
    pass
