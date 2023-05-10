import sys
import tkinter as tk
from tkinter import ttk, messagebox

from dataentryapp.backend import backend
from dataentryapp.frontend import template


class DataviewFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.collection = parent.collection
        self.datasheetid = parent.datasheetid

        # Include frame for metadata and plot infor at top treelist frame
        self.plotinfoframe = ttk.Frame(self)

        self.id_labels = ["Stageid", "Site", "Treatment", "Burn"]
        self.label_widgets = []
        for lab in self.id_labels:
            lab = lab.lower()
            wid = tk.Label(
                self.plotinfoframe,
                text=lab + ": " + str(self.collection[0][lab])
            )
            self.label_widgets.append(wid)

        self.button_labels = ["Metadata"]
        self.button_widgets = []
        if self.button_labels:
            for b in self.button_labels:
                but = tk.Button(self.plotinfoframe, text=b)
                self.button_widgets.append(but)

        self.button_widgets[0]["command"] = self.on_metadata

        for n, wid in enumerate(self.label_widgets + self.button_widgets):
            wid.grid(row=0, column=n, padx=4, pady=4)

        columns = (
            "Plot",
            "Species",
            "<BH",
            "<2.5","ht1",
            "<5","ht2",
            "<6","ht3",
            "<7","ht4",
            "<8","ht5",
            "<9","ht6",
            "<10","ht7")
        col_widths = (45, 45, 45, 35, 45, 35, 45, 35, 45, 35, 45, 35, 45, 35, 45, 35, 45)

        # Create widget
        self.dataview = ttk.Treeview(self, columns=columns, show="headings")
        self.dataview["height"] = 25

        for i in range(len(columns)):
            text = columns[i] if not columns[i].startswith("ht") else ""
            self.dataview.heading(columns[i], text=text)
            self.dataview.column(columns[i], width=col_widths[i], stretch=True)

        self.dataview.bind('<<TreeviewSelect>>', self.on_select_row)

        # arrange in frame: plotinfo frame on top
        # dataview widget below, 1 column, 2 rows
        self.plotinfoframe.grid(row=0, column=0)
        self.dataview.grid(row=1, column=0, sticky=tk.NSEW)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # add a scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.dataview.yview)
        self.dataview[ "yscroll" ] = scrollbar.set
        scrollbar.grid(row=1, column=1, sticky='ns')

        # Populate my dataview (ttk.Treeview)
        self.update_dataview()

    def on_metadata(self):
        columns = ["Plotnum", "Date", "Seedling radius", "Sapling radius", "Notes"]
        widths = [90, 90, 90, 90, 90]
        self.newWin = template.SimpleEntry(self, widths=widths, columns=columns, hide=0)
        self.newWin.entry_widgets[2].insert(0, 5.64)
        self.newWin.entry_widgets[3].insert(0, 11.28)
        self.newWin.set_selector(
            func=backend.get_regen_metadata,
            datasheetid=self.datasheetid
        )
        self.newWin.set_inserter(
            func=backend.insert_regen_metadata,
            datasheetid=self.datasheetid
        )
        self.newWin.set_deleter(
            func=backend.delete_regen_metadata,
            datasheetid=self.datasheetid
        )

    def on_select_row(self, event):
        """push selected dataview row contents to entry widgets in other class"""
        target = self.parent.entry_frame.entry_widgets
        keys = self.dataview["columns"]
        row = self.dataview.selection()
        values = self.dataview.item(row, "values")
        row = dict(zip(keys, values))
        # make sure these names match entry widget names in target
        col_subset = ("Plot", "Species", "<BH", "<2.5", "<5", "<6", "<7", "<8", "<9", "<10")
        for col, wid in zip(col_subset, target):
            wid.delete(0, "end")
            wid.insert(0, row[col])

    def update_dataview(self):
        for child in self.dataview.get_children():
            self.dataview.delete(child)
        data = backend.get_datasheet_regen_counts(self.datasheetid)
        data = [list(map(lambda x:
                    "\u2610" if x == "missing" else 
                    "\u2611" if x == "gotit" else
                    "\u2757" if x == "uhoh" else
                    x, row)
                ) for row in data]
        for d in data:
            d = [d if d is not None else '' for d in d]
            self.dataview.insert("", "end", values=d)


class EntryFrame(ttk.Frame):
    def __init__(self, parent):
        self.parent = parent
        self.collection = parent.collection
        self.datasheetid = parent.datasheetid
        super().__init__(parent)
        # field options
        options = {'padx': 3, 'pady': 3}

        # Build widget labels
        self.widget_names = ("Plot", "Species", "<BH", "<2.5", "<5", "<6", "<7", "<8", "<9", "<10")

        self.label_widgets = []
        for l in self.widget_names:
            wid = tk.Label(self, text=l)
            self.label_widgets.append(wid)

        for idx, wid in enumerate(self.label_widgets):
            wid.grid(row=0, column=idx, **options)

        # Entry widgets
        self.entry_widgets = []
        for l in self.widget_names:
            wid = tk.Entry(self, width=5)
            self.entry_widgets.append(wid)

        # arrange entry widgets
        for idx, w in enumerate(self.entry_widgets):
            w.grid(row=1, column=idx, **options)

        # Fill entire frame
        for i in range(len(self.label_widgets)):
            self.columnconfigure(i, weight=1)

        # Button widgets for heights
        self.button_widgets1 = []
        for i, sizeclass in enumerate(self.widget_names[3:10], start=3):
            wid = tk.Button(self, text="CBH/HT")
            wid["command"] = self.ht_entry_window_maker(sizeclass)
            self.button_widgets1.append(wid)

        # arrange widgets
        for idx, w in enumerate(self.button_widgets1):
            w.grid(row=2, column=idx + 3, **options)

        # bottom row buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=3, column=0, columnspan=12)
        button_labels2 = ("Submit", "Mark and close", "Delete entry")

        self.button_widgets2 = []
        for b in button_labels2:
            # command for each button is the same as the label for that button
            # with lower case and underscore.
            func = getattr(self, b.lower().replace(" ", "_"))
            wid = tk.Button(self.button_frame, text=b, command=func)
            self.button_widgets2.append(wid)
        
        # allow to set status
        cbvals = ["Not started", "Started", "Complete"]
        cb = ttk.Combobox(self.button_frame, state="readonly", values=cbvals)
        self.button_widgets2.insert(1, cb)
        status = backend.get_datasheet_status(self.parent.datasheetid)[0]
        self.button_widgets2[1].set(status)

        # arrange widgets
        for idx, w in enumerate(self.button_widgets2):
            w.grid(row=0, column=idx, **options)

        self.entry_widgets[0].focus()

        # change tab order so ht buttons come after height entry
        for i, wid in enumerate(self.button_widgets1):
            wid.lift(aboveThis=self.entry_widgets[i + 3])

    def ht_entry_window_maker(self, sizeclass):
        def make_window(self=self, sizeclass=sizeclass):
            columns = ("CBH", "Ht")
            datasheetid = self.datasheetid
            plotnum = self.entry_widgets[self.widget_names.index("Plot")].get()
            spp = self.entry_widgets[self.widget_names.index("Species")].get()
            self.newWin = template.SimpleEntry(self, columns=columns, hide=0)
            self.newWin.set_selector(
                func=backend.get_regen_heights,
                datasheetid=datasheetid,
                plotnum=plotnum,
                spp=spp,
                sizeclass=sizeclass
            )
            self.newWin.set_inserter(
                func=backend.insert_regen_heights,
                datasheetid=datasheetid,
                plotnum=plotnum,
                spp=spp,
                sizeclass=sizeclass
            )
            self.newWin.set_deleter(
                func=backend.delete_regen_heights,
                datasheetid=datasheetid,
                plotnum=plotnum,
                spp=spp,
                sizeclass=sizeclass
            )
        return make_window

    def delete_entry(self):
        datasheetid = self.datasheetid
        plotnum = self.entry_widgets[self.widget_names.index("Plot")].get()
        spp = self.entry_widgets[self.widget_names.index("Species")].get()
        backend.delete_regen(datasheetid, plotnum, spp)
        self.update_dataview()


    def mark_and_close(self):
        status = self.button_widgets2[1].get()
        datasheetid = self.datasheetid
        backend.insert_datasheet_status(datasheetid, status)
        self.parent.destroy()

    def submit(self):
        size = self.widget_names[2:10]
        counts = [w.get() if w.get() else 0 for w in self.entry_widgets[2:10]]
        plot = self.entry_widgets[0].get()
        spp = self.entry_widgets[1].get()
        backend.insert_regen_counts(self.datasheetid, plot, spp, size, counts)
        self.update_dataview()
        self.entry_widgets[0].focus()
        self.entry_widgets[0].select_range(0, tk.END)


    # buttons called from this EntryFrame need to update
    # the DataviewFrame dataview widget when they close.
    def update_dataview(self):
        self.parent.dataview_frame.update_dataview()


class App(tk.Toplevel):
    def __init__(self, parent, datasheetid):
        super().__init__(parent)

        self.title('Regen data entry')
        # self.geometry('800x400')

        self.parent = parent
        self.filename = ""
        self.datasheetid = datasheetid
        # Multiple collections for regen datasheets
        self.collection = backend.get_collection_from_datasheetid(self.datasheetid)
        # self.columns = ("Date", "Plot", "Species", "<BH", "<2.5", "<5", "<6", "<7", "<8", "<9", "<10")

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        self.dataview_frame = DataviewFrame(self)
        self.dataview_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self.entry_frame = EntryFrame(self)
        self.entry_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        self.bind("<Destroy>", self.on_destroy)

    def on_destroy(self, event):
        if event.widget == self:
            self.parent.update_dataview()


if __name__ == "__main__":
    app = App()
    app.mainloop()
