import sys
import tkinter as tk
from tkinter import ttk, messagebox

from dataentryapp.backend import backend
from dataentryapp.frontend import template

class MetadataFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.collection = parent.collection
        options = {'padx': 3, 'pady': 3}

        self.id_labels = ["StageId", "Site", "Treatment", "Burn", "Plotnum"]
        self.date_labels = ["Date"]
        self.transect_labels = ["One hr", "Ten hr", "Hund hr", "Thous hr", "# transects"]

        self.label_widgets = []
        for l in self.id_labels + self.transect_labels + self.date_labels:
            wid = tk.Label(self, text=l)
            self.label_widgets.append(wid)

        # arrange label widgets
        for idx, wid in enumerate(self.label_widgets):
            wid.grid(row=0, column=idx, **options)

        self.id_widgets = []
        for lab in self.id_labels:
            l = lab.lower()
            wid = tk.Label(self, text=str(self.collection[l]))
            self.id_widgets.append(wid)

        self.date_widget = tk.Entry(self)
        date = backend.get_dates(collectid=self.collection["collectid"])
        template = "MM/DD/YYYY"
        date_widget_text = date if date else template
        self.date_widget.insert(0, date_widget_text)

        self.transect_widgets = []
        for l in self.transect_labels:
            wid = tk.Entry(self, width=8, takefocus=0)
            self.transect_widgets.append(wid)

        for num, wid in zip((1, 2, 4, 10, 3), self.transect_widgets):
            wid.insert(0, num)

        self.button_widget = tk.Button(self, text="Submit")
        self.button_widget["command"] = self.submit
        second_row_widgets = [*self.id_widgets, 
            *self.transect_widgets,
            self.date_widget,
            self.button_widget]

        for n, wid in enumerate(second_row_widgets):
            wid.grid(row=1, column=n, **options)

    def submit(self):
        print("self.collection: ", self.collection)
        vals = ["onehrlen", "tenhrlen", "hundhrlen", "thoushrlen"]
        submit_vals = {k : int(v.get()) for (k, v) in zip(vals, self.transect_widgets)}
        submit_vals["collectid"] = self.collection["collectid"]
        backend.insert_fuel_metadata(**submit_vals)
        backend.insert_dates(
            self.collection["collectid"],
            self.date_widget.get(),
            only_one=True)

class FuelFrame(ttk.Frame):
    def __init__(self, parent, parent2=None):
        super().__init__(parent)
        options = {'padx': 3, 'pady': 3}
        self.parent = parent2 if parent2 else parent
        self.collection = self.parent.collection

        # give dataview widget its own frame and make sure the 
        # widget resizes with frame
        self.dataview_frame = ttk.Frame(self)
        self.dataview_frame.grid(row=0, column=0, sticky="nsew")
        self.dataview_frame.rowconfigure(0, weight=1)
        self.dataview_frame.columnconfigure(0, weight=1)

        # Create widget
        self.dataview = ttk.Treeview(self.dataview_frame,
                                     columns=self.columns,
                                     show="headings",
                                     takefocus=0,
                                     height=6)
        for i in range(len(self.columns)):
            text = self.columns[i]
            self.dataview.heading(self.columns[i], text=text)
            self.dataview.column(
                self.columns[i],
                width=tk.font.Font().measure(self.columns[i].title()),
                stretch=True
            )

        self.dataview.bind('<<TreeviewSelect>>', self.on_select_row)
        self.dataview.grid(sticky=tk.NSEW)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # add a scrollbar
        scrollbar = ttk.Scrollbar(self.dataview_frame, orient=tk.VERTICAL, command=self.dataview.yview)
        self.dataview.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Populate dataview
        self.update_dataview()

        # label widgets

        # One frame for the bottom widgets
        self.bottom_widgets_frame = tk.Frame(self)
        self.bottom_widgets_frame.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=0)

        if not hasattr(self, "entry_labels"):
            self.entry_labels = self.columns

        self.label_widgets = []
        for l in self.entry_labels:
            wid = tk.Label(self.bottom_widgets_frame, text=l)
            self.label_widgets.append(wid)

        # arrange label widgets
        for idx, wid in enumerate(self.label_widgets):
            wid.grid(row=0, column=idx, **options)

        # Entry widgets
        self.entry_widgets = []
        for l in self.entry_labels:
            wid = tk.Entry(self.bottom_widgets_frame, width=5)
            self.entry_widgets.append(wid)

        # arrange entry widgets
        for idx, w in enumerate(self.entry_widgets):
            w.grid(row=1, column=idx, **options)

        # Fill entire frame
        for i in range(len(self.label_widgets)):
            self.bottom_widgets_frame.columnconfigure(i, weight=1)

        # bottom row buttons
        self.button_frame = tk.Frame(self.bottom_widgets_frame)
        # this frame needs to span all the columns in the entry frame in order
        # to center the buttons
        self.button_frame.grid(row=3, column=0, columnspan=len(self.columns))

        self.button_widgets2 = []
        for b in self.button_labels2:
            # command for each button is the same as the label for that button
            # with lower case and underscore.
            func = getattr(self, b.lower().replace(" ", "_"))
            wid = tk.Button(self.button_frame, text=b, command=func)
            self.button_widgets2.append(wid)

        # arrange widgets
        for idx, w in enumerate(self.button_widgets2):
            w.grid(row=0, column=idx, **options)

    def on_select_row(self, event):
        """push selected dataview row contents to entry widgets"""
        row = self.dataview.selection()
        values = self.dataview.item(row, "values")
        # don't need to input transect number a second time, omit that entry widget
        if self.columns[0] == "#":
            values = values[1:]
        values = [v if v != "\u2757" else "" for v in values]
        for wid, value in zip(self.entry_widgets, values):
            wid.delete(0, "end")
            wid.insert(0, value)
        if hasattr(self, "select_row_extra"):
            self.select_row_extra(row)


    def update_dataview(self):
        collectid = self.collection["collectid"]
        for child in self.dataview.get_children():
            self.dataview.delete(child)
        data = self.data_getter(collectid)
        for row in data:
            row = [item if item is not None else "\u2757" for item in row]
            self.dataview.insert("", "end", values=row)

    def clear_entries(self):
        for wid in self.entry_widgets:
            wid.delete(0, "end")
    
class FWDFrame(FuelFrame):
    def __init__(self, parent, swap=False):
        self.swap = swap
        if swap:
            self.columns = (
                "Azimuth",
                "Crew",
                "Transect",
                "Slope",
                "One hr",
                "Ten hr",
                "Hund hr",
                "Duff/litter 10",
                "% Litter 10",
                "FBD 10",
                "Duff/litter 5",
                "% Litter 5",
                "FBD 5"
            )
            self.button_labels2 = []
            self.data_getter = backend.get_fwd_swap
        else:    
            self.columns = (
                "Azimuth",
                "Crew",
                "Transect",
                "Slope",
                "One hr",
                "Ten hr",
                "Hund hr",
                "Duff/litter 5",
                "% Litter 5",
                "FBD 5",
                "Duff/litter 10",
                "% Litter 10",
                "FBD 10"
            )
            self.button_labels2 = []
            self.data_getter = backend.get_fwd
        super().__init__(parent)

    def submit(self, transectid, transectnum):
        # this function needs to insert into transects, collectcrew,
        # fwd, and station
        collectid = self.collection["collectid"]
        azimuth, slope = (self.entry_widgets[n].get() for n in (0, 3))
        azimuth, slope = (int(val) if val != "" else None for val in (azimuth, slope))
        if azimuth is None:
            if transectnum == 1:
                azimuth = 0
            elif transectnum == 2:
                azimuth = 120
            elif transectnum == 3:
                azimuth = 240
        backend.insert_slope_azimuth(transectid, slope, azimuth)
        crew = self.entry_widgets[1].get()
        backend.insert_crew(collectid, "fwd", crew, transectid)
        fwd = (int(w.get()) if w.get() != "" else None for w in self.entry_widgets[4:7])
        backend.insert_fwd(transectid, *fwd)
        # using indexes of entry widgets, covert wide to long data
        # swap metermark labels if necessayr to match widget order
        meterMarkOrder = (10, 5) if self.swap else (5, 10)
        for mm, slc in zip(meterMarkOrder, (7, 10)):
            dufflitterfbd = [w.get() for w in self.entry_widgets[slc:slc+3]]
            dufflitterfbd = [float(val) if val != "" else None for val in dufflitterfbd]
            backend.insert_dufflitterfbd(transectid, mm, *dufflitterfbd)

    def select_row_extra(self, row):
        self.parent.veg_frame.dataview.selection_set(row)

class VegFrame(FuelFrame):
    def __init__(self, parent, swap=False):
        self.swap = swap
        if swap:
            self.columns = (
                "#",
                "Crew",
                "Live wdy. 10",
                "Dead wdy. 10",
                "Wdy. ht. 10",
                "Live hrb. 10",
                "Dead hrb. 10",
                "Hrb. ht. 10",
                "Live wdy. 5",
                "Dead wdy. 5",
                "Wdy. ht. 5",
                "Live hrb. 5",
                "Dead hrb. 5",
                "Hrb. ht. 5"
            )
            # Don't enter transect again, so there are different number of entry widgets and 
            # dataview columns
            self.entry_labels = self.columns[1:]
            self.button_labels2 = []
            self.data_getter = backend.get_veg_swap
        else:
            self.columns = (
                "#",
                "Crew",
                "Live wdy. 5",
                "Dead wdy. 5",
                "Wdy. ht. 5",
                "Live hrb. 5",
                "Dead hrb. 5",
                "Hrb. ht. 5",
                "Live wdy. 10",
                "Dead wdy. 10",
                "Wdy. ht. 10",
                "Live hrb. 10",
                "Dead hrb. 10",
                "Hrb. ht. 10"
            )
            # Don't enter transect again, so there are different number of entry widgets and 
            # dataview columns
            self.entry_labels = self.columns[1:]
            self.button_labels2 = []
            self.data_getter = backend.get_veg
        super().__init__(parent)

    def submit(self, transectid):
        collectid = self.collection["collectid"]
        crew = self.entry_widgets[0].get()
        backend.insert_crew(collectid, "veg", crew, transectid)
        # swap metermark labels if necessayr to match widget order
        meterMarkOrder = (10, 5) if self.swap else (5, 10)
        for mm, slc in zip(meterMarkOrder, (1, 7)):
            veg = [w.get() for w in self.entry_widgets[slc:slc+6]]
            veg = [float(val) if val != "" else None for val in veg]
            backend.insert_veg(transectid, mm, *veg)
    
    def select_row_extra(self, row):
        if not self.parent.fwd_frame.dataview.selection() == row:
            self.parent.fwd_frame.dataview.selection_set(row)

class CWDFrame(FuelFrame):
    def __init__(self, parent, parent2):
        self.columns = (
            "Transect",
            "Diameter",
            "Decay class"
        )
        self.button_labels2 = ["Submit", "Delete entry"]
        self.data_getter = backend.get_cwd
        super().__init__(parent, parent2=parent2)
        self.dataview["height"] = 11

    def submit(self):
        if not self.update_transectnum(): return
        transectnum = self.transectnum
        collectid = self.collection["collectid"]
        backend.insert_transect(collectid, transectnum)
        transectid = backend.get_transectid(collectid, transectnum)
        cwd = [w.get() for w in self.entry_widgets[1:]]
        cwd[0] = float(cwd[0])
        cwd[1] = int(cwd[1])
        backend.insert_cwd(transectid, *cwd)
        self.parent.update_all_dataviews()
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()

    def delete_entry(self):
        if not self.update_transectnum(): return
        transectnum = self.transectnum
        collectid = self.collection["collectid"]
        transectid = backend.get_transectid(collectid, transectnum)
        if not transectid:
            print("Transect doesn't exist yet.")
            return
        cwd = [w.get() for w in self.entry_widgets[1:]]
        cwd[0] = float(cwd[0])
        cwd[1] = int(cwd[1])
        backend.delete_cwd(transectid, *cwd)
        self.parent.update_all_dataviews()
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()

    def update_transectnum(self):
        collectid = self.collection["collectid"]
        transectnum = self.entry_widgets[0].get()
        if not transectnum:
            print("need to provide a transect number")
            return
        self.transectnum = int(transectnum)
        return 1

class ButtonFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.collection = parent.collection
        options = {'padx': 3, 'pady': 3}
        self.button_labels2 = [
            "Submit",
            "Delete transect",
            "Clear entries",
            "Swap stations",
            "Mark and Close"
        ]
        self.button_widgets2 = []
        for b in self.button_labels2:
            # command for each button is the same as the label for that button
            # with lower case and underscore.
            func = getattr(self, b.lower().replace(" ", "_"))
            wid = tk.Button(self, text=b, command=func)
            self.button_widgets2.append(wid)

        # allow to set status
        cbvals = ["Not started", "Started", "Complete"]
        cb = ttk.Combobox(self, state="readonly", values=cbvals)
        self.button_widgets2.insert(4, cb)
        status = backend.get_datasheet_status(self.parent.datasheetid)[0]
        self.button_widgets2[4].set(status)

        # arrange widgets
        for idx, w in enumerate(self.button_widgets2):
            w.grid(row=0, column=idx, **options)

    def update_transectnum(self):
        transectnum = self.parent.fwd_frame.entry_widgets[2].get()
        if not transectnum:
            print("need to provide a transect number")
            return
        self.transectnum = int(transectnum)
        return 1

    def submit(self):
        if not self.update_transectnum(): return
        transectnum = self.transectnum
        collectid = self.collection["collectid"]
        backend.insert_transect(collectid, transectnum)
        transectid = int(backend.get_transectid(collectid, transectnum))
        self.parent.fwd_frame.submit(transectid, transectnum)
        self.parent.veg_frame.submit(transectid)
        self.clear_entries()
        self.parent.update_all_dataviews()

    def delete_transect(self):
        # more deleting needs to happen here
        if not self.update_transectnum(): return
        collectid = self.collection["collectid"]
        transectnum = self.transectnum
        transectid = backend.get_transectid(collectid, transectnum)
        if not transectid:
            print("Transect does not exist yet.")
            return
        backend.delete_fuel_crew(transectid, "fwd")
        backend.delete_fuel_crew(transectid, "veg")
        backend.delete_fwd(transectid)
        backend.delete_station(transectid)
        backend.delete_transect(transectid)
        backend.delete_all_cwd(transectid)
        self.parent.update_all_dataviews()
        self.clear_entries()

    def clear_entries(self):
        self.parent.fwd_frame.clear_entries()
        self.parent.veg_frame.clear_entries()
        self.parent.fwd_frame.entry_widgets[1].focus()

    def mark_and_close(self):
        status = self.button_widgets2[4].get()
        datasheetid = self.parent.datasheetid
        backend.insert_datasheet_status(datasheetid, status)
        self.parent.destroy()

    def swap_stations(self):
        self.parent.swap_frame()

class NotesFrame(FuelFrame):
    def __init__(self, parent, parent2=None):
        self.columns = (
            "Transect",
            "Notes"
        )
        self.button_labels2 = ["Submit", "Delete entry"]
        self.data_getter = backend.get_transect_notes
        super().__init__(parent, parent2=parent2)
        self.dataview["height"] = 6
        self.dataview.column(
            "Transect",
            width=tk.font.Font().measure("Transect"),
            stretch=False
        )
        self.dataview.column(
            "Notes",
            stretch=True
        )
        self.entry_widgets[1]["width"] = 75

    def submit(self):
        if not self.update_transectnum(): return
        transectnum = self.transectnum
        collectid = self.collection["collectid"]
        backend.insert_transect(collectid, transectnum)
        transectid = backend.get_transectid(collectid, transectnum)
        notes = self.entry_widgets[1].get()
        backend.insert_transect_notes(transectid, notes)
        self.parent.update_all_dataviews()
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()

    def delete_entry(self):
        if not self.update_transectnum(): return
        transectnum = self.transectnum
        collectid = self.collection["collectid"]
        transectid = backend.get_transectid(collectid, transectnum)
        if not transectid:
            print("Transect doesn't exist yet.")
            return
        backend.insert_transect_notes(transectid, "")
        self.parent.update_all_dataviews()
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()

    def update_transectnum(self):
        transectnum = self.entry_widgets[0].get()
        if not transectnum:
            print("need to provide a transect number")
            return
        self.transectnum = int(transectnum)
        return 1 

class App(tk.Toplevel):
    def __init__(self, parent, datasheetid):
        super().__init__(parent)

        self.title('Fuel data entry')
        # self.geometry('800x400')

        self.parent = parent
        self.filename = ""
        self.datasheetid = datasheetid
        # Multiple collections for regen datasheets
        self.collection = backend.get_collection_from_datasheetid(self.datasheetid)[0]

        self.columnconfigure(0, weight=1)

        self.rowconfigure(0, weight=0)
        self.metadata_frame = MetadataFrame(self)
        self.metadata_frame.grid(column=0, row=0, sticky="ns", padx=4, pady=4)

        self.rowconfigure(1, weight=1)
        self.fwd_frame = FWDFrame(self)
        self.fwd_frame.grid(column=0, row=1, sticky="ns", padx=4, pady=4)

        self.rowconfigure(2, weight=1)
        self.veg_frame = VegFrame(self)
        self.veg_frame.grid(column=0, row=2, sticky="ns", padx=4, pady=4)

        self.rowconfigure(3, weight=0)
        self.buttom_frame = ButtonFrame(self)
        self.buttom_frame.grid(column=0, row=3, sticky="ns", padx=4, pady=4)

        self.rowconfigure(4, weight=1)
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.grid(column=0, row=4, sticky="nsew")
        self.bottom_frame.rowconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(0, weight=1)
        self.bottom_frame.columnconfigure(1, weight=1)

        self.cwd_frame = CWDFrame(self.bottom_frame, parent2=self)
        self.cwd_frame.grid(column=0, row=0, sticky="ns", padx=4, pady=4)

        self.notes_frame = NotesFrame(self.bottom_frame, parent2=self)
        self.notes_frame.grid(column=1, row=0, sticky="ns", padx=4, pady=4)

        self.metadata_frame.date_widget.select_range(0, tk.END)
        self.metadata_frame.date_widget.focus()

        self.bind("<Destroy>", self.on_destroy)
        # set initial state for widgets that can swap
        self.swap = False

    def swap_frame(self):
        if self.swap:
            self.swap = False
            self.fwd_frame.destroy()
            self.fwd_frame = FWDFrame(self)
            self.fwd_frame.grid(column=0, row=1, sticky="ns", padx=4, pady=4)
            self.veg_frame = VegFrame(self, swap=False)
            self.veg_frame.grid(column=0, row=2, sticky="ns", padx=4, pady=4)
        else:
            self.swap = True
            self.fwd_frame.destroy()
            self.fwd_frame = FWDFrame(self, swap=True)
            self.fwd_frame.grid(column=0, row=1, sticky="ns", padx=4, pady=4)
            self.veg_frame = VegFrame(self, swap=True)
            self.veg_frame.grid(column=0, row=2, sticky="ns", padx=4, pady=4)

    def update_all_dataviews(self):
        self.fwd_frame.update_dataview()
        self.veg_frame.update_dataview()
        self.cwd_frame.update_dataview()
        self.notes_frame.update_dataview()

    def on_select_row(self, row):
        self.fwd_frame.after_select_row(row)
        self.veg_frame.after_select_row(row)

    def on_destroy(self, event):
        if event.widget == self:
            self.parent.update_dataview()
    #
    # def report_callback_exception(self, *args):
    #     err = traceback.format_exception(*args)
    #     print("i'm inside report_callback_exception in fueldataentry.")
    #     messagebox.showerror("Exception", err)


if __name__ == "__main__":
    app = App()
    app.mainloop()
