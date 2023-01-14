"""
@created: 2018-08-19 18:00:00
@author: (c) 2018-2019 Jorj X. McKie
Display a PyMuPDF Document using Tkinter
-------------------------------------------------------------------------------
Dependencies:
-------------
PyMuPDF v1.14.5+, PySimpleGUI, Tkinter

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
import fitz
from pathlib import Path

if not list(map(int, fitz.VersionBind.split("."))) >= [1, 14, 5]:
    raise SystemExit("need PyMuPDF v1.14.5 for this script")

if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox as mb
from tkinter import ttk

from ttkwidgets.autocomplete import AutocompleteCombobox


def select_file():
    global filename
    filetypes = (
        ("Pdf files", '*.pdf'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Open PDF',
        initialdir='./',
        filetypes=filetypes)
    
    if not filename:
        filename = "No file selected."

    root.destroy()

def open_file_quick():
    global filename
    filename = "C:/Users/walki/Desktop/db_learn/data/datasheets/raw/DONE_all_sheets_07242022.pdf"
    root.destroy()

root = Tk()
root.iconbitmap("./dataentryapp/frontend/tree_icon.ico")
root.title('Open PDF')
root.resizable(False, False)
root.geometry('300x150')

# open button
open_button = Button(
    root,
    text='Open a File',
    # command=select_file
    command=open_file_quick
)

open_button.pack(expand=True)


if len(sys.argv) == 1:
    root.mainloop()
else:
    filename = sys.argv[1]


doc = fitz.open(filename)

d = {
    "page_count": len(doc),
    "cur_page": 0,
    "zoom": False,
    "cur_pos": (0, 0),
    "move": (0, 0),
    "rotation": 0,
    "max_size": None
}

d["page_cound"] = len(doc)

title = "PyMuPDF display of '%s', pages: %i" % (filename, d["page_count"])

# ------------------------------------------------------------------------------
# read the page data
# ------------------------------------------------------------------------------
def get_page():
    """Return a tkinter.PhotoImage or a PNG image for a document page number.
    :arg int pno: 0-based page number
    :arg zoom: top-left of old clip rect, and one of -1, 0, +1 for dim. x or y
               to indicate the arrow key pressed
    :arg max_size: (width, height) of available image area
    :arg bool first: if True, we cannot use tkinter
    """
    global d
    rot_angle = [0, 90, 180, 270]
    
    # set page rotation
    doc[d["cur_page"]].set_rotation(rot_angle[d["rotation"] % len(rot_angle)])
    pdfpage = doc[d["cur_page"]]
    r = pdfpage.rect
    
    # ensure image fits screen:
    # exploit, but do not exceed width or height
    zoom_0 = 1
    if d["max_size"]:
        zoom_0 = min(1, d["max_size"][0] / r.width, d["max_size"][1] / r.height)
        if zoom_0 == 1:
            zoom_0 = min(d["max_size"][0] / r.width, d["max_size"][1] / r.height)

    mat_0 = fitz.Matrix(zoom_0, zoom_0)

    if not d["zoom"]:  # show the total page
        pix = pdfpage.get_pixmap(matrix=mat_0, alpha=False)
        clip = r
    else:
        w2 = d["max_size"][0] / (2 * zoom_0)  # clip size before zoom
        h2 = d["max_size"][1] / (2 * zoom_0)  # ...
        tl = d["cur_pos"]  # old top-left
        tl.x += d["move"][0] * (r.width - w2) / 2  # adjust topl-left ...
        tl.x = max(0, tl.x)  # according to ...
        tl.x = min(r.width - w2, tl.x)  # arrow key ...
        tl.y += d["move"][1] * (r.height - h2) / 2 # provided, but ...
        tl.y = max(0, tl.y)  # stay within ...
        tl.y = min(r.height - h2, tl.y)  # the page rect
        clip = fitz.Rect(tl, tl.x + w2, tl.y + h2)
        # clip rect is ready, now fill it
        mat = mat_0 * fitz.Matrix(2, 2)  # zoom matrix
        # pix = dlist.get_pixmap(alpha=False, matrix=mat, clip=clip)
        pix = pdfpage.get_pixmap(alpha=False, matrix=mat, clip=clip)
    
    img = pix.tobytes("ppm")  # make PPM image from pixmap for tkinter

    d["cur_pos"] = clip.tl
    d["move"] = (0, 0)
    page_img = PhotoImage(data = img)
    return page_img  # return image, clip position


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# get physical screen dimension to determine the page image max size
# ------------------------------------------------------------------------------

def getScreenSize():
    root = Tk()
    max_width = root.winfo_screenwidth() - 20
    max_height = root.winfo_screenheight() - 135
    # max size is a square
    sm_side = min(max_height, max_width)
    max_size = (sm_side, sm_side)
    root.destroy()
    del root
    return max_size

d["max_size"] = getScreenSize()

# define the buttons / events we want to handle

def press_Next():
    global d
    global page_image
    d["cur_page"] += 1

    # sanitize page number
    if d["cur_page"] >= d["page_cound"]: # don't wrap around
        d["cur_page"] = d["page_cound"] - 1
    if d["cur_page"] < 0:  # pages < 0 are valid but look bad
        d["cur_page"] = 0

    # Refresh page image
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)
    pg_lab = "page " + str(d["cur_page"] + 1) + " of " + str(d["page_count"])
    cur_pg_lab.config(text=pg_lab)


def press_Prior():
    global d
    global page_image
    d["cur_page"] -= 1

    # sanitize page number
    if d["cur_page"] >= d["page_cound"]:  # don't wrap around
        d["cur_page"] = d["page_cound"] - 1
    while d["cur_page"] < 0:  # pages < 0 are valid but look bad
        d["cur_page"] = 0

    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)
    pg_lab = "page " + str(d["cur_page"] + 1) + " of " + str(d["page_count"])
    cur_pg_lab.config(text=pg_lab)


def press_Zoom():
    global d
    global page_image
    if not d["zoom"]:
        d["zoom"] = True
    else:
        d["zoom"] = False
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Rotate():
    global d
    global page_image
    d["rotation"] += 1
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Left(event):
    global d
    global page_image
    if d["zoom"]:
        d["move"] = (-1, 0)
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Right(event):
    global d
    global page_image
    if d["zoom"]:
        d["move"] = (1, 0)
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Up(event):
    global d
    global page_image
    # dlist_tab[d["cur_page"]] = None
    if d["zoom"]:
        d["move"] = (0, -1)
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Down(event):
    global d
    global page_image
    # dlist_tab[d["cur_page"]] = None
    if d["zoom"]:
        d["move"] = (0, 1)
    page_image = get_page()
    canvas.itemconfig(image_container, image=page_image)

def press_Save():
    global d
    global comp_opt

    input_values = [
        e_type.get(),
        e_site.get(),
        e_treatment.get(),
        e_burn.get(),
        e_plot.get()
    ]

    entries = input_values[:-1]

    bad = [
        entries[idx] + " not in " + list(comp_opt.keys())[idx]
        for idx in range(len(entries))
        if entries[idx] not in list(comp_opt.values())[idx] or not entries[idx]
    ]

    pltnum=input_values[4]

    def plot_num_test(num):
        if num.isnumeric():
            if int(num) < 1 or int(num) > 30:
                return num + " not valid plot number"
        else:
            return num + " not valid plot number"

    # don't use plot number for regen datasheets
    if input_values[0] == "regen":
        del input_values[4]
    else:
        t = plot_num_test(pltnum)
        if t:
            bad.append(t)

    if bad:
        response = mb.askquestion("Real?", "\n".join(bad) + "\n continue?")
        if response == "no": 
            return

    fn = "data/datasheets/final/" + "_".join(input_values) + ".pdf"
    if Path(fn).exists():
        if mb.askquestion("", fn + " exists. Append?") == "yes":
            outdoc = fitz.open(fn)
            outdoc.insert_pdf(doc, from_page = d["cur_page"], to_page = d["cur_page"])
            outdoc.saveIncr()
        else:
            return
    else:
        outdoc = fitz.open()
        outdoc.insert_pdf(doc, from_page = d["cur_page"], to_page = d["cur_page"])
        outdoc.save(fn)
        mb.showinfo(title="File saved", message=fn + " saved.")
    
    # return focus for more data entry
    e_type.focus_set()
    e_type.select_range(0, "end")
    press_Next()

def press_Complete():
    if mb.askquestion("Finished?", "Close and mark as DONE?") == "yes":
        doc.close()
        p = Path(filename)
        done = Path(p.parent, "DONE_" + p.name)
        p.rename(done)
        root.destroy()

    
#######################################################
############### Begin GUI #############################
#######################################################

root = Tk()
root.title("Rename datasheets")
root.iconbitmap("./dataentryapp/frontend/tree_icon.ico")
# Create frames
left_frame = Frame(root, bg="lavender")
right_frame = Frame(root, bg="lightgreen")
right_top = Frame(root, bg="lightgreen")


# layout frames
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

left_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
right_frame.grid(row=1, column=1, sticky="nsew")
right_top.grid(row=0, column=1, sticky="nsew")


# Left frame widgets
pg_lab = "page " + str(d["cur_page"] + 1) + " of " + str(d["page_cound"])
cur_pg_lab = Label(left_frame, text = pg_lab)

page_image = get_page()
canvas = Canvas(left_frame, width=d["max_size"][0], 
            height=d["max_size"][1], bg="lavender", highlightbackground="black")
image_container = canvas.create_image(1, 1, anchor = "nw", image=page_image)

canvas.bind("<1>", lambda event: canvas.focus_set())
canvas.bind("<Left>", press_Left)
canvas.bind("<Right>", press_Right)
canvas.bind("<Up>", press_Up)
canvas.bind("<Down>", press_Down)

# Left frame widget layout
left_frame.columnconfigure(0, weight=1)
cur_pg_lab.grid(row=0, column=0, padx=5, pady=5)
canvas.grid(row=1, column=0)

# right-top frame widgets
b_prev = Button(right_top, text = "Prev", width=7, command=press_Prior)
b_next = Button(right_top, text = "Next", width=7, command=press_Next)
b_zoom = Button(right_top, text = "Zoom", width=7, command=press_Zoom)
b_rotate = Button(right_top, text = "Rotate", width=7, command=press_Rotate)


# right-top frame widget layout

right_top.rowconfigure(0, weight=1)
right_top.columnconfigure(0, weight=1)
right_top.columnconfigure(1, weight=1)
right_top.columnconfigure(2, weight=1)
right_top.columnconfigure(3, weight=1)

b_prev.grid(row=0, column=0, sticky="s", pady=10)
b_next.grid(row=0, column=1, sticky="s", pady=10)
b_zoom.grid(row=0, column=2, sticky="s", pady=10)
b_rotate.grid(row=0, column=3, sticky="s", pady=10)


# right frame widgets
l_type = Label(right_frame, text="Datatsheet type")
l_site = Label(right_frame, text="Site")
l_treatment = Label(right_frame, text="Treatment", anchor="w")
l_burn = Label(right_frame, text="Burn/No burn", anchor="w")
l_plot = Label(right_frame, text="Plot number", anchor="w")

comp_opt = {
    "type": ["fuel", "veg", "wood", "tree", "regen",],
    "site": ["bob", "camp8", "crib", "dun", "fair", "hare"],
    "treatment": ["ls", "m", "np"],
    "burn": ["b", "nb"]
}

e_type = AutocompleteCombobox(right_frame)
e_site = AutocompleteCombobox(right_frame)
e_treatment = AutocompleteCombobox(right_frame)
e_burn = AutocompleteCombobox(right_frame)
e_plot = ttk.Entry(right_frame)

e_type.set_completion_list(comp_opt["type"])
e_site.set_completion_list(comp_opt["site"])
e_treatment.set_completion_list(comp_opt["treatment"])
e_burn.set_completion_list(comp_opt["burn"])

b_save = Button(right_frame, text="Save and next", command=press_Save)
b_complete = Button(right_frame, text="Close and mark DONE", command=press_Complete)

# right frame widget layout
l_type.grid(row=0, column=0, sticky="ew", padx=4)
l_site.grid(row=1, column=0, sticky="ew", padx=4)
l_treatment.grid(row=2, column=0, sticky="ew", padx=4)
l_burn.grid(row=3, column=0, sticky="ew", padx=4)
l_plot.grid(row=4, column=0, sticky="ew", padx=4)

e_type.grid(row=0, column=1, sticky="ew", padx=4, pady=2)
e_site.grid(row=1, column=1, sticky="ew", padx=4, pady=2)
e_treatment.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
e_burn.grid(row=3, column=1, sticky="ew", padx=4, pady=2)
e_plot.grid(row=4, column=1, sticky="ew", padx=4, pady=2)

b_save.grid(row=5, column=0, columnspan=2, pady=4)
b_complete.grid(row=6, column=0, columnspan=2, pady=4)

# e_type.focus_set()

# for child in right_frame.winfo_children():
#     child.grid_configure(padx=4, pady=4)

root.mainloop()