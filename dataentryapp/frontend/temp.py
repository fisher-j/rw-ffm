import tkinter as tk


class SampleApp(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        e1 = tk.Entry(self)
        e2 = tk.Entry(self)
        e3 = tk.Entry(self)

        e1.insert(0,"1")
        e2.insert(0,"2")
        e3.insert(0,"3")

        e1.pack()
        e2.pack()
        e3.pack()

        # reverse the stacking order to show how
        # it affects tab order
        new_order = (e3, e2, e1)
        for widget in new_order:
            widget.lift()


if __name__ == "__main__":
    app = SampleApp()
    app.mainloop()
