import sys
import tkinter as tk
from tkinter import ttk, messagebox

from dataentryapp.backend import backend
from dataentryapp.frontend import template


class TreeListFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.collection = parent.collection

        # Include frame for metadata and plot infor at top treelist frame
        self.plotinfoframe = ttk.Frame(self)

        l_stage = tk.Label(self.plotinfoframe, text="Stage: " + str(self.collection["stageid"]))
        l_site = tk.Label(self.plotinfoframe, text="Site: " + self.collection["site"])
        l_treatment = tk.Label(self.plotinfoframe, text="Treatment: " + self.collection["treatment"])
        l_burn = tk.Label(self.plotinfoframe, text="Burn: " + self.collection["burn"])
        l_plotnum = tk.Label(self.plotinfoframe, text="Plot #: " + str(self.collection["plotnum"]))

        b_crew = tk.Button(self.plotinfoframe, text="Crew", command=self.open_crew_entry)
        b_date = tk.Button(self.plotinfoframe, text="Date(s)", command=self.open_dates_entry)
        b_reftree = tk.Button(self.plotinfoframe, text="Ref. trees", command=self.open_ref_tree_entry)
        self.e_notes = tk.Entry(self.plotinfoframe, width=70)
        self.e_notes.insert(0, backend.get_tree_notes(self.collection["collectid"]))
        b_update_notes = tk.Button(self.plotinfoframe, text="Update notes", command=self.update_notes)

        l_stage.grid(row=0, column=0,padx=4, pady=4)
        l_site.grid(row=0, column=1,padx=4, pady=4)
        l_treatment.grid(row=0, column=2, padx=4, pady=4)
        l_burn.grid(row=0, column=3, padx=4, pady=4)
        l_plotnum.grid(row=0, column=4, padx=4, pady=4)

        b_crew.grid(row=0, column=5, padx=4, pady=4)
        b_date.grid(row=0, column=6, padx=4, pady=4)
        b_reftree.grid(row=0, column=7, padx=4, pady=4)

        self.e_notes.grid(row=1, column=0, columnspan=6, padx=4, pady=4)
        b_update_notes.grid(row=1, column=8, padx=4, pady=4)

        # Create dataview widget (ttk.Treeview)
        # columns and headings
        columns = ("treeid", "spp", "dbh", "ht", "cbh", "clumpid", "damage", "clumpsaplings", "notes")
        col_names = ("Tree ID", "Species", "DBH", "HT", "Crown base", "Clump ID", "Damage", "Clump saplings", "Notes")
        col_widths = (60, 60, 50, 50, 90, 80, 115, 80, 220)

        # Create widget
        self.dataview = ttk.Treeview(self, columns=columns, show="headings")
        for i in range(len(columns)):
            self.dataview.heading(columns[i], text=col_names[i])
            self.dataview.column(columns[i], width=col_widths[i], stretch=True)

        self.dataview.bind('<<TreeviewSelect>>', self.on_select_row)

        # arrange in frame
        self.plotinfoframe.grid(row=0, column=0)
        self.dataview.grid(row=1, column=0, sticky=tk.NSEW)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)


        # add a scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.dataview.yview)
        self.dataview.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky='ns')

        # Populate my dataview (ttk.Treeview)
        self.update_dataview()


    def on_select_row(self, event):
        row = self.dataview.selection()
        keys = self.dataview["columns"]
        values = self.dataview.item(row, "values")
        row = dict(zip(keys, values))
        col_names = ("treeid", "spp", "dbh", "ht", "cbh", "clumpid", "notes")
        for col, wid in zip(col_names, self.parent.e_frame.entry_widgets):
            wid.delete(0, "end")
            wid.insert(0, row[col])


    def open_crew_entry(self):
        columns = ["Role", "Member"]
        self.newWin = template.SimpleEntry(self, columns=columns, hide=1)
        # When I close these windows, I don't want to update anything in the parent frame
        self.newWin.unbind("<Destroy>", self.newWin.bindid)
        self.newWin.set_selector(
            func=backend.get_crew,
            collectid=self.collection["collectid"]
        )
        self.newWin.set_inserter(
            func=backend.insert_crew,
            collectid=self.collection["collectid"],
            role="cuiser"
        )
        self.newWin.set_deleter(
            func=backend.delete_crew,
            collectid=self.collection["collectid"],
            role="cuiser"
        )

    def open_dates_entry(self):
        columns = ["Date"]
        self.newWin = template.SimpleEntry(self, columns=columns, hide=0)
        self.newWin.unbind("<Destroy>", self.newWin.bindid)
        self.newWin.set_selector(
            func=backend.get_dates,
            collectid=self.collection["collectid"]
        )
        self.newWin.set_inserter(
            func=backend.insert_dates,
            collectid=self.collection["collectid"]
        )
        self.newWin.set_deleter(
            func=backend.delete_dates,
            collectid=self.collection["collectid"]
        )


    def open_ref_tree_entry(self):
        columns = ["Tree ID", "Distance", "Azimuth"]
        self.newWin = template.SimpleEntry(self, columns=columns, hide=0)
        self.newWin.unbind("<Destroy>", self.newWin.bindid)
        self.newWin.set_selector(
            func=backend.get_reftrees,
            collectid=self.collection["collectid"]
        )
        self.newWin.set_inserter(
            func=backend.insert_reftrees,
            collectid=self.collection["collectid"]
        )
        self.newWin.set_deleter(
            func=backend.delete_reftrees,
            collectid=self.collection["collectid"]
        )

    def update_notes(self):
        notes = self.e_notes.get()
        backend.insert_tree_notes(self.collection["collectid"], notes)


    def update_dataview(self):
        for child in self.dataview.get_children():
            self.dataview.delete(child)

        for d in backend.get_datasheet_trees(self.collection["collectid"]):
            d = [d if d is not None else '' for d in d]
            self.dataview.insert("", "end", values=d)


class EntryFrame(ttk.Frame):
    def __init__(self, parent):
        self.parent = parent
        self.collection = parent.collection
        super().__init__(parent)
        # field options
        options = {'padx': 3, 'pady': 3}
        labels = ("Tree ID", "Species", "DBH", "HT", "Crown base", "Clump ID", "Damage", "Clump saplings", "Notes")

        # Build widget labels
        self.label_list = [tk.Label(self, text=labels[i]) for i in range(len(labels))]

        for obj in enumerate(self.label_list):
            obj[1].grid(row=0, column=obj[0], **options)

        # Fill entire frame
        for i in range(len(self.label_list)):
            self.columnconfigure(i, weight=1)

        # Entry and button widgets
        self.treeid_e = tk.Entry(self, width=6)
        self.spp_e = tk.Entry(self, width=4)
        self.dbh_e = tk.Entry(self, width=6)
        self.ht_e = tk.Entry(self, width=6)
        self.cbh_e = tk.Entry(self, width=6)
        self.clumpid_e = tk.Entry(self, width=6)
        self.clumpsap_b = tk.Button(self, text="Enter", command=self.open_clump_sapling_entry)
        self.damage_b = tk.Button(self, text="Enter", command=self.open_damage_entry)
        self.notes_e = tk.Entry(self, width=42)

        # This list is a list (in order) of entry widgets used for iterating
        # over them as in the on_select_row method
        self.entry_widgets = [
            self.treeid_e,
            self.spp_e,
            self.dbh_e,
            self.ht_e,
            self.cbh_e,
            self.clumpid_e,
            self.notes_e]

        # arrange widgets
        self.treeid_e.grid(row=2, column=0, **options)
        self.spp_e.grid(row=2, column=1, **options)
        self.dbh_e.grid(row=2, column=2, **options)
        self.ht_e.grid(row=2, column=3, **options)
        self.cbh_e.grid(row=2, column=4, **options)
        self.clumpid_e.grid(row=2, column=5, **options)
        self.damage_b.grid(row=2, column=6, **options)
        self.clumpsap_b.grid(row=2, column=7, **options)
        self.notes_e.grid(row=2, column=8, **options)

        # bottom row buttons
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=3, column=0, columnspan=9)
        self.button1 = tk.Button(self.button_frame, text="Submit", command=self.submit)
        self.button2 = tk.Button(self.button_frame, text="Close", command=parent.destroy)
        self.button3 = tk.Button(self.button_frame, text="Delete entry", command=self.delete)
        self.button1.grid(row=0, column=0, **options)
        self.button2.grid(row=0, column=1, **options)
        self.button3.grid(row=0, column=2, **options)

        self.treeid_e.focus()

    def delete(self):
        treeid = self.treeid_e.get()
        collectid = self.collection["collectid"]
        if treeid:
            mb = messagebox.askyesno(
                "Real?",
                "Are you sure you want to delete treeid: " + treeid + "?",
                parent=self)
            if mb:
                backend.delete_tree_entry(collectid=collectid, treeid=treeid)
                self.update_dataview()

    def close(self):
        self.destroy()

    def open_damage_entry(self):
        columns = ["Tree id", "Location", "Defect type"]
        treeid = self.treeid_e.get()
        collectid = self.collection["collectid"]
        if treeid and collectid:
            self.newWin = template.SimpleEntry(self, columns=columns)

            self.newWin.set_selector(
                func=backend.get_tree_defect,
                collectid=collectid,
                treeid=treeid
            )
            self.newWin.set_inserter(
                func=backend.insert_tree_defect,
                collectid=collectid,
                treeid=treeid
            )
            self.newWin.set_deleter(
                func=backend.delete_treedefect,
                collectid=self.collection["collectid"]
            )

    def open_clump_sapling_entry(self):
        treeid = self.treeid_e.get()
        clumpid = self.clumpid_e.get()
        if not (treeid and clumpid) or not (treeid.isdigit() and clumpid.isdigit()):
            messagebox.showinfo("Need more info", "must supply integer clumpid and treeid")
            return
        args = {
            "collectid": self.collection["collectid"],
            "clumpid": int(clumpid)
        }
        if not backend.match_tree_clump(treeid=treeid, **args):
            messagebox.showinfo("Wrong clumpid", "Clumpid mismatch, check clumpid.")
            return
        columns = ["Sap DBH"]
        self.newWin = template.SimpleEntry(self, columns=columns, hide=0)
        self.newWin.set_selector(
            func=backend.get_clumpsaplings,
            **args
        )
        self.newWin.set_inserter(
            func=backend.insert_clumpsaplings,
            treeid=int(treeid),
            **args
        )
        self.newWin.set_deleter(
            backend.delete_clumpsaplings,
            **args
        )


    def submit(self):
        values = [w.get() if w.get() != "" else None for w in self.entry_widgets]
        values.append(self.collection["collectid"])
        backend.insert_tree_data(values)
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()
        self.update_dataview()

    # buttons called from this EntryFrame (e_frame) need to update
    # the TreeListFrame (tl_frame) dataview widget when they close.
    def update_dataview(self):
        self.parent.tl_frame.update_dataview()


class App(tk.Toplevel):
    def __init__(self, parent, datasheetid):
        super().__init__(parent)

        self.title('Tree data entry')
        # self.geometry('800x400')

        self.parent = parent
        self.filename = ""
        self.datasheetid = datasheetid
        # there will only be one collectid for these data so i'm extracting from list
        self.collection = backend.get_collection_from_datasheetid(self.datasheetid)[0]


        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure(0, weight=1)

        self.tl_frame = TreeListFrame(self)
        self.tl_frame.grid(column=0, sticky="nsew", padx=4, pady=4)

        self.e_frame = EntryFrame(self)
        self.e_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        self.bind("<Destroy>", self.on_destroy)

    def on_destroy(self, event):
        if event.widget == self:
            self.parent.update_dataview()


if __name__ == "__main__":
    app = App()
    app.mainloop()
