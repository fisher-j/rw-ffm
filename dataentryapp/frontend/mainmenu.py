import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import subprocess as sp
import platform
import traceback
from pathlib import Path
from dataentryapp.backend import backend
from dataentryapp.backend import import_from_filename
from dataentryapp.frontend import template
from dataentryapp.frontend import treedataentry
from dataentryapp.frontend import fueldataentry
from dataentryapp.frontend import regendataentry
from dataentryapp.frontend import datasheetnamer

backend.initialize_database()

class DatasheetsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        # define dataview
        columns = ("id", "filename", "date_modified", "status")
        self.datasheets = ttk.Treeview(self, columns=columns, show="headings", height=30)

        # define headings
        self.datasheets.heading('id', text="id")
        self.datasheets.heading('filename', text="Filename")
        self.datasheets.heading('date_modified', text="Date modified")
        self.datasheets.heading('status', text="Status")

        # adjust columns
        self.datasheets.column("id", width=50, stretch=False)
        self.datasheets.column("filename", width=210, stretch=False)
        self.datasheets.column("date_modified", width=210, stretch=False)
        self.datasheets.column("status", width=100, stretch=False)

        # arrange in frame
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.datasheets.grid(sticky=tk.NSEW)

        # add a scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.datasheets.yview)
        self.datasheets.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')


class ButtonsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        # field options
        options = {'padx': 5, 'pady': 5}

        self.import_button = tk.Button(self, text="Import", command=parent.open_import)
        self.impute_button = tk.Button(self, 
                                       text="Enter data",
                                       command=parent.on_enter_data)

        self.from_filename = tk.Button(self, 
                                       text="Import filenames",
                                       command=parent.import_from_filename)

        self.export = tk.Button(self, 
                                text="Export",
                                command=parent.export)


        # self.rowconfigure(0, weight=1)
        # self.columnconfigure(0, weight=1)

        self.import_button.grid(**options)
        self.impute_button.grid(**options)
        self.export.grid(**options)
        self.from_filename.grid(**options)


class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()

        self.datasheetDir = Path("../../data/datasheets/final/")

        self.title('RW Fire Mitigation Datasheet Entry')
        # self.geometry('620x400')

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self.ds_frame = DatasheetsFrame(self)
        self.ds_frame.grid(column=0, sticky=tk.NS, padx=4, pady=4)

        self.b_frame = ButtonsFrame(self)
        self.b_frame.grid(row=0, column=1, sticky="ew", padx=4, pady=4)

        self.update_dataview()

    def update_dataview(self):
        for i in self.ds_frame.datasheets.get_children():
            self.ds_frame.datasheets.delete(i)
        # get data
        datasheets = backend.get_datasheets_table()
        datasheets = [list(row) for row in datasheets]
        for idx, row in enumerate(datasheets):
            datasheets[idx][2] = row[2].strftime("%m/%d/%Y %H:%M:%S")

        # add data to the treeview
        for sheet in datasheets:
            self.ds_frame.datasheets.insert('', tk.END, values=sheet)

    def focus_entry_form(self):
        # disable main menu window
        self.dataEntryWindow.wait_visibility()
        self.dataEntryWindow.focus()
        self.dataEntryWindow.grab_set()
        # Open datasheet in default pdf viewer
        if platform.system() == 'Darwin':       # macOS
            sp.call(('open', self.filename))
        elif platform.system() == 'Windows':    # Windows
            sp.Popen(("start", self.filename), shell=True)
        else:                                   # linux variants
            sp.call(('xdg-open', self.filename))

    def on_enter_data(self):
        # get values for selected row
        cur_row = self.ds_frame.datasheets.focus()
        cur_row = self.ds_frame.datasheets.item(cur_row, "values")

        # Only if there is an active selection
        if(cur_row):
            # This should actually get datasheettype
            collection = backend.get_collection_from_datasheetid(cur_row[0])
            # get first row to identify datasheet type
            datasheettype = collection[0]["datasheettype"]
            self.filename = self.datasheetDir / cur_row[1]
            # Then open appropriate data entry form
            if datasheettype == "tree":
                self.dataEntryWindow = treedataentry.App(self, cur_row[0])
                self.focus_entry_form()
            elif datasheettype == "regen":
                self.dataEntryWindow = regendataentry.App(self, cur_row[0])
                self.focus_entry_form()
            elif datasheettype == "fuel":
                self.dataEntryWindow = fueldataentry.App(self, cur_row[0])
                self.focus_entry_form()

    def open_import(self):
        filetypes = (
            ("Pdf files", '*.pdf'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(
            title='Open PDF',
            initialdir='../data/datasheets/raw',
            filetypes=filetypes)
        # self.withdraw()
        self.datasheetnamer = datasheetnamer.App(self, filename)

    def import_from_filename(self):
        importDir = filedialog.askdirectory(
            title='Open import directory containing named pdfs',
            initialdir='.')
        if not importDir: return
        importDir = Path(importDir)
        # self.withdraw()
        import_from_filename.import_from_filename(importDir)
        self.update_dataview()

    def export(self):
        backend.export_tables()
        messagebox.showinfo("Export complete", message="Tables exported to data\\csv")

    def report_callback_exception(self, *args):
        exc, val, tb = args
        print(exc)
        print(val)
        print(tb)

        err = ('An uncaught exception has occurred!\n\n'
               + '\n'.join(traceback.format_exception(*args))
               + '\nTerminating.')
        messagebox.showerror("Exception", err)

if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()
