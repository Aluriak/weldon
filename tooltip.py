"""Code implementing a tooltip for tkinter.

Adapted from http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml

"""


import tkinter as tk


TOOLTIP_COLOR = '#ffffe1'
TOOLTIP_FONT = ('tahoma', '8', 'normal')


class ToolTip:

    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox('insert')
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() +27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry('+%d+%d'.format(x, y))
        try:
            # For Mac OS
            tw.tk.call("::tk::unsupported::MacWindowStyle",
                       "style", tw._w,
                       "help", "noActivates")
        except tk.TclError:
            pass
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background=TOOLTIP_COLOR,
                         relief=tk.SOLID, borderwidth=1,
                         font=TOOLTIP_FONT)
        label.pack(ipadx=1)

    def hidetip(self):
        """Hide previously shown tooltip"""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


    @staticmethod
    def on(widget, text):
        """Add a tip exposing given text when mouse is over given widget"""
        tooltip = ToolTip(widget)
        def enter(event):
            tooltip.showtip(text)
        def leave(event):
            tooltip.hidetip()
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)
        return tooltip
