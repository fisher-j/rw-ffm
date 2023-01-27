import tkinter as tk
from tkinter import Toplevel, ttk
import re

from dataentryapp.backend import backend

class SimpleEntry(tk.Toplevel):
    def __init__(self, parent, columns, widths=None, hide=1):
        super().__init__(parent)
        # self.title("Crew entry")
        # self.geometry("400x400")
        options = {'padx': 4, 'pady':4}

        self.parent = parent
        self.selector = None
        self.inserter = None
        self.do_update = True
        
        # position window within parent
        xpos = parent.winfo_toplevel().winfo_rootx()
        ypos = parent.winfo_toplevel().winfo_rooty()
        print("position: ", xpos, ypos)
        self.geometry(f"+{xpos}+{ypos}")
        
        # separate frames
        self.data_frame = tk.Frame(self)
        self.data_frame.grid(row=0, column=0, sticky="nsew")
        self.data_frame.rowconfigure(0, weight=1)
        self.data_frame.columnconfigure(0, weight=1)

        self.entry_frame = tk.Frame(self)
        self.entry_frame.grid(row=1, column=0)
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=2, column=0)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        
        # dataview (treeview) widget
        # hide first n columns
        visible = columns[hide:]
        self.visible_columns = visible
        self.dataview = ttk.Treeview(self.data_frame, columns=columns, show="headings")
        self.dataview.config(displaycolumns=visible)
        self.dataview.grid(row=0, column=0, sticky=tk.NSEW)

        for i, c in enumerate(visible):
            self.dataview.heading(c, text=c)
            if widths:
                self.dataview.column(c, width=widths[i])

        # label widgets
        self.label_widgets = []
        for n, c in enumerate(visible):
            lab = tk.Label(self.entry_frame, text=c)
            lab.grid(row=0, column=n, **options)
            self.label_widgets.append(lab)
        
        # TODO: implement AutocompleteEntry for these
        # Entry widgets
        self.entry_widgets = []
        for n, c in enumerate(visible):
            lab = tk.Entry(self.entry_frame)
            lab.grid(row=1, column=n, **options)
            self.entry_widgets.append(lab)

        self.submit = tk.Button(self.button_frame, text="Submit")
        self.submit.config(command=self.on_submit)
        self.submit.grid(row=0, column=0, **options)
        self.close = tk.Button(self.button_frame, text="Close")
        self.close.config(command=self.on_close)
        self.close.grid(row=0, column=1, **options)
        self.delete = tk.Button(self.button_frame, text="delete")
        self.delete.config(command=self.on_delete)
        self.delete.grid(row=0, column=2, **options)

        # add a scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.dataview.yview)
        self.dataview.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky='ns')
            
        # initialize new window
        # self.wait_visibility()
        self.focus()
        self.grab_set()
        self.entry_widgets[0].focus()

        # Update parent on close, save id to remove this binding if needed
        self.bind("<Destroy>", self.on_destroy)
        # Other bindings for faster entry
        self.bind("<Return>", self.on_submit)
        self.bind("<Escape>", self.on_close)

    def cur_selection(self):
        """Dictionary of col names: values for selected row with col names converted to variable names"""
        # get values for selected row
        cur_row = self.dataview.focus()
        cur_row = self.dataview.item(cur_row)["values"]
        columns = (self.clean(col) for col in self.dataview["columns"])
        cur_row_dict = dict(zip(columns, cur_row))
        return cur_row_dict

    def set_selector(self, func, **kwargs):
        """Sets data retrieval function and its arguments"""
        self.selector_func = func
        self.selector_args = kwargs
        # populate dataview
        self.update_dataview()
    
    def set_inserter(self, func, **kwargs):
        """Sets data insertion function and some of it's arguments.
        Other arguments are taken from entry widget(s)."""
        self.inserter_func = func
        self.inserter_args = kwargs

    def set_deleter(self, func, **kwargs):
        """Sets deletion function and some of its arguments.
        Other arguments are taken from entry widget(s)."""
        self.deleter_func = func
        self.deleter_args = kwargs
    
    def on_close(self, event=None):
        self.destroy()

    def on_destroy(self, event=None):
        if event.widget == self:
            if self.do_update:
                self.parent.update_dataview()
            self.parent.grab_set()

    def update_dataview(self):
        if self.selector_func:
            for child in self.dataview.get_children():
                self.dataview.delete(child)
            data = self.selector_func(**self.selector_args)
            for d in data:
                d = [d if d is not None else "" for d in d]
                self.dataview.insert("", "end", values=d)

    def clean(self, col_name):
        """Convert dataview column names to valid variable names.
        
        Returns a lower case version of name with spaces stripped.
        """
        out = re.sub("\W", "", col_name.lower())
        return out

    def on_submit(self, event=None):
        """Prepare arguments and call function for inserting values
        
        Combines values passed from parent with values found in entry
        widgets into named dictionary of arguemnts used in calling the
        specified inserter function."""
        for col, wid in zip(self.visible_columns, self.entry_widgets):
            self.inserter_args.update({self.clean(col): wid.get()})
        if self.inserter_func:
            print(self.inserter_args)
            self.inserter_func(**self.inserter_args)
        self.update_dataview()
        for wid in self.entry_widgets:
            wid.delete(0, "end")
        self.entry_widgets[0].focus()
        self.entry_widgets[0].select_range(0, tk.END)

    def on_delete(self):
        """Delete currently selected row, if there is one."""
        cur_selection = self.cur_selection()
        if cur_selection and self.deleter_func:
            self.deleter_args.update(cur_selection)
            self.deleter_func(**self.deleter_args)
        self.update_dataview()
    
