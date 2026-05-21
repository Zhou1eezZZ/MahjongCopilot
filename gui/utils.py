"""GUI common/utility functions."""
import sys
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageDraw, ImageFont, ImageTk

from common.mj_helper import MJAI_TILE_2_UNICODE, ActionUnicode
from common.log_helper import LOGGER


class GuiStyle:
    """Shared visual language for the tkinter UI."""

    COLORS = {
        "bg": "#f5f5f7",
        "surface": "#ffffff",
        "surface_alt": "#fbfbfd",
        "stroke": "#d2d2d7",
        "stroke_subtle": "#e5e5ea",
        "text": "#1d1d1f",
        "muted": "#6e6e73",
        "accent": "#007aff",
        "accent_hover": "#0a84ff",
        "accent_soft": "#e8f2ff",
        "green": "#34c759",
        "yellow": "#ffcc00",
        "red": "#ff3b30",
        "gray": "#8e8e93",
        "ready": "#5ac8fa",
    }

    def __init__(self, std_font_size:int=12):
        self.std_font_size = std_font_size
        self.font_size = std_font_size
        self.dpi_scale:float = 1.0
        self._font_family = "Microsoft YaHei"
        self._mono_family = "Consolas"
        self._emoji_family = "Segoe UI Emoji"
        

    def set_style_normal(self, style:ttk.Style):
        """Set the ttk theme and shared widget styles."""
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass

        self._configure_fonts()
        base_font = self.font_normal()
        small_font = self.font_normal(size=10)
        title_font = self.font_normal(size=16, weight="bold")

        style.configure(".", font=base_font)
        style.configure("TFrame", background=self.COLORS["bg"])
        style.configure("Surface.TFrame", background=self.COLORS["surface"])
        style.configure("TLabel", background=self.COLORS["bg"], foreground=self.COLORS["text"], font=base_font)
        style.configure("Surface.TLabel", background=self.COLORS["surface"], foreground=self.COLORS["text"], font=base_font)
        style.configure("Muted.TLabel", background=self.COLORS["surface"], foreground=self.COLORS["muted"], font=small_font)
        style.configure("Title.TLabel", background=self.COLORS["bg"], foreground=self.COLORS["text"], font=title_font)
        style.configure("Section.TLabel", background=self.COLORS["surface"], foreground=self.COLORS["text"],
                        font=self.font_normal(size=13, weight="bold"))
        style.configure(
            "TButton",
            background=self.COLORS["surface_alt"],
            foreground=self.COLORS["text"],
            borderwidth=1,
            focusthickness=1,
            focuscolor=self.COLORS["accent"],
            padding=(12, 8),
            relief="flat",
        )
        style.map(
            "TButton",
            background=[("active", self.COLORS["stroke_subtle"]), ("disabled", self.COLORS["surface_alt"])],
            foreground=[("disabled", self.COLORS["gray"])],
        )
        style.configure(
            "Toolbar.TButton",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            borderwidth=0,
            padding=(10, 6),
            relief="flat",
        )
        style.map(
            "Toolbar.TButton",
            background=[("active", self.COLORS["stroke_subtle"]), ("disabled", self.COLORS["bg"])],
            foreground=[("disabled", self.COLORS["gray"])],
        )
        style.configure(
            "Accent.TButton",
            background=self.COLORS["accent"],
            foreground="#ffffff",
            borderwidth=0,
            padding=(14, 9),
            relief="flat",
        )
        style.map(
            "Accent.TButton",
            background=[("active", self.COLORS["accent_hover"]), ("disabled", self.COLORS["stroke"])],
            foreground=[("disabled", self.COLORS["muted"])],
        )
        style.configure(
            "Sidebar.TButton",
            anchor="w",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            borderwidth=0,
            padding=(12, 10),
            relief="flat",
        )
        style.map("Sidebar.TButton", background=[("active", self.COLORS["stroke_subtle"])])
        style.configure(
            "SidebarSelected.TButton",
            anchor="w",
            background=self.COLORS["accent_soft"],
            foreground=self.COLORS["accent"],
            borderwidth=0,
            padding=(12, 10),
            relief="flat",
        )
        style.map("SidebarSelected.TButton", background=[("active", self.COLORS["accent_soft"])])
        style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["stroke"],
            lightcolor=self.COLORS["stroke"],
            darkcolor=self.COLORS["stroke"],
            padding=(8, 7),
        )
        style.configure(
            "TCombobox",
            fieldbackground="#ffffff",
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["stroke"],
            lightcolor=self.COLORS["stroke"],
            darkcolor=self.COLORS["stroke"],
            padding=(8, 6),
            arrowsize=14,
        )
        style.configure(
            "Form.TEntry",
            fieldbackground=self.COLORS["surface_alt"],
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["stroke_subtle"],
            lightcolor=self.COLORS["stroke_subtle"],
            darkcolor=self.COLORS["stroke_subtle"],
            padding=(9, 8),
        )
        style.configure(
            "Form.TCombobox",
            fieldbackground=self.COLORS["surface_alt"],
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["stroke_subtle"],
            lightcolor=self.COLORS["stroke_subtle"],
            darkcolor=self.COLORS["stroke_subtle"],
            padding=(9, 7),
            arrowsize=14,
        )
        style.configure("TCheckbutton", background=self.COLORS["surface"], foreground=self.COLORS["text"],
                        padding=(0, 4), font=base_font)
        style.configure("Horizontal.TScrollbar", troughcolor=self.COLORS["bg"], background=self.COLORS["stroke"])
        style.configure("Vertical.TScrollbar", troughcolor=self.COLORS["bg"], background=self.COLORS["stroke"])
        
    def _configure_fonts(self):
        if sys.platform == "darwin":
            self._font_family = "SF Pro Text"
            self._mono_family = "Menlo"
            self._emoji_family = "Apple Color Emoji"
        elif sys.platform == "win32":
            self._font_family = "Segoe UI"
            self._mono_family = "Consolas"
            self._emoji_family = "Segoe UI Emoji"
        else:
            self._font_family = "Noto Sans"
            self._mono_family = "DejaVu Sans Mono"
            self._emoji_family = "Noto Color Emoji"

        try:
            for named_font in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont"):
                font.nametofont(named_font).configure(family=self._font_family, size=self.font_size)
        except Exception:
            pass

    def font_normal(self, family:str=None, size:int=None, weight:str="normal"):
        """Return a tuple usable as a tkinter font."""
        if not family:
            family = self._font_family
        if not size:
            size = self.font_size
        else:
            size = max(8, int(size / self.dpi_scale))
        return (family, size, weight)

    def font_mono(self, size:int=None, weight:str="normal"):
        """Return a monospaced font tuple."""
        return self.font_normal(self._mono_family, size, weight)

    def font_emoji(self, size:int=None, weight:str="normal"):
        """Return a platform-preferred emoji/symbol font tuple."""
        return self.font_normal(self._emoji_family, size, weight)
    

    def set_dpi_scaling(self, scale:float=1.0):
        """Set DPI scaling while keeping readable minimum sizes."""
        self.dpi_scale = max(0.75, min(2.5, scale))
        self.font_size = max(10, int(self.std_font_size / self.dpi_scale))

    @property
    def palette(self):
        """Color palette accessor."""
        return self.COLORS


def add_hover_text(widget:tk.Widget, text:str):
    """Compatibility shim for old tooltip calls.

    The redesigned desktop UI uses visible labels instead of custom tooltip
    popups, which looked out of place on macOS and Windows alike.
    """
    return
    
    
def _on_hover(wdg:tk.Widget, text:str):
    # display a hover label with text
    if not text:
        return
    try:
        toplvl = wdg.winfo_toplevel()
        try:
            wdg.original_bg = wdg.cget("background")
            wdg.configure(background=GUI_STYLE.palette["accent_soft"])
        except Exception:
            wdg.original_bg = None

        if hasattr(wdg, "hover_text") and wdg.hover_text is not None:
            try:
                wdg.hover_text.destroy()
            except Exception:
                ...
        wdg.hover_text = tk.Label(
            toplvl,
            text=text,
            bg=GUI_STYLE.palette["surface_alt"],
            fg=GUI_STYLE.palette["text"],
            highlightbackground=GUI_STYLE.palette["stroke"],
            highlightthickness=1,
            padx=8,
            pady=4,
            font=GUI_STYLE.font_normal(size=10),
        )
        x = wdg.winfo_rootx() - toplvl.winfo_rootx() + wdg.winfo_width()
        y = wdg.winfo_rooty() - toplvl.winfo_rooty() + wdg.winfo_height() //2
        wdg.hover_text.place(x=x, y=y, anchor=tk.W)
    except Exception as e:
        LOGGER.warning("Failed to create hover tooltip for widget %s: %s", wdg, e, exc_info=True)
    

def _on_leave_hover(wdg:tk.Widget):
    # destroy the hover label
    try:
        if hasattr(wdg, "hover_text") and wdg.hover_text is not None:
            wdg.hover_text.destroy()
            wdg.hover_text = None
    except Exception as e:
        LOGGER.warning("Failed to destroy hover tooltip for widget %s: %s", wdg, e, exc_info=True)

    try:
        if hasattr(wdg, "original_bg") and wdg.original_bg is not None:
            wdg.configure(background=wdg.original_bg)
    except Exception as e:
        LOGGER.warning("Failed to restore background for widget %s: %s", wdg, e, exc_info=True)
        

def crop_image_from_top_left(image:Image, width, height):
    # Get the size of the original image
    original_width, original_height = image.size
    
    # Calculate the coordinates of the cropping box
    left = 0
    top = 0
    right = min(original_width, width)
    bottom = min(original_height, height)
    
    # Crop the image
    cropped_image = image.crop((left, top, right, bottom))    
    return cropped_image

def text_to_image(size:int, text:str, width:int=800, height:int=600):
    """ create image based on the text content"""
    
    # draw emojis and regular text in different fonts
    ft_emj = ImageFont.truetype(font="seguiemj.ttf", size=size)
    ft_txt = ImageFont.truetype(font="msyh.ttf", size=size)
    line_spacing = int(size/2)
    pad_x = int(size/2)
    pad_y = int(size/2)
    dummy_img = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)   

    cur_x = pad_x
    cur_y = pad_y + line_spacing
    
    # Create the image with calculated dimensions
    im = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(im)
    
    # draw text each line and each character, record line width and total height
    max_width = 1
    lines = text.split("\n")
    for l in lines:
        for c in l:
            if c in MJAI_TILE_2_UNICODE.values():
                ft = ft_emj
            else:
                ft = ft_txt
            bbox = dummy_draw.textbbox((0, 0), c, font=ft, embedded_color=True, spacing=line_spacing)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.text((cur_x,cur_y), c, font=ft, embedded_color=True, anchor="lm", fill="black", spacing=line_spacing)
            cur_x += text_w
        max_width = max(cur_x,max_width)
        cur_x = pad_x
        cur_y += size + line_spacing
        
    # crop image to fit the text
    max_width += pad_x
    max_height = cur_y - line_spacing   # mid > top    
    im = crop_image_from_top_left(im, max_width, max_height)

    return ImageTk.PhotoImage(im)


GUI_STYLE = GuiStyle()
