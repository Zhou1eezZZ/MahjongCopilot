""" Help Window for tkinter GUI"""

from typing import Callable
import tkinter as tk
from tkinter import ttk, messagebox
from tkhtmlview import HTMLScrolledText

from common.log_helper import LOGGER
from common.settings import Settings
from common import utils
from updater import Updater, UpdateStatus
from .utils import GUI_STYLE
from .widgets import Card


class HelpWindow(tk.Toplevel):
    """ dialog window for help information and update """
    def __init__(self, parent:tk.Frame, st:Settings, updater:Updater):
        super().__init__(parent)
        self.st = st            # Settings object
        self.updater = updater
        
        title_str = f"{st.lan().HELP} {st.lan().APP_TITLE} v{self.updater.local_version}"
        self.title(title_str)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f'+{parent_x+10}+{parent_y+10}')
        self.win_size = (820, 720)
        self.geometry(f"{self.win_size[0]}x{self.win_size[1]}")  # Set the window size
        self.minsize(680, 520)
        self.configure(bg=GUI_STYLE.palette["bg"])

        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style)

        root = ttk.Frame(self, padding=(18, 16, 18, 14))
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.html_text:str = None
        content_card = Card(root, padding=(12, 12))
        content_card.grid(row=0, column=0, sticky=tk.NSEW)
        content_card.columnconfigure(0, weight=1)
        content_card.rowconfigure(0, weight=1)
        self.html_box = HTMLScrolledText(
            content_card, html=st.lan().HELP+st.lan().LOADING,
            wrap=tk.CHAR, font=GUI_STYLE.font_normal(), height=25,
            state=tk.DISABLED)
        self.html_box.grid(row=0, column=0, sticky=tk.NSEW)

        self.frame_bot = ttk.Frame(root)
        self.frame_bot.grid(row=1, column=0, sticky=tk.EW, pady=(14, 0))
        self.frame_bot.grid_columnconfigure(1, weight=1)
        
        # Updater button
        self.update_button = ttk.Button(
            self.frame_bot,
            text=st.lan().CHECK_FOR_UPDATE,
            state=tk.DISABLED,
            width=18,
            style="Accent.TButton",
        )
        self.update_button.grid(row=0, column=0, sticky=tk.W, padx=(0, 12))
        # label
        self.update_str_var = tk.StringVar(value="")
        self.update_label = ttk.Label(self.frame_bot, textvariable=self.update_str_var, style="TLabel")
        self.update_label.grid(row=0, column=1, sticky=tk.EW, padx=(0, 12))
        self.update_cmd:Callable = lambda: None
        # OK Button
        self.ok_button = ttk.Button(self.frame_bot, text="OK", command=self._on_close, width=8)
        self.ok_button.grid(row=0, column=2, sticky=tk.E)
        
        self.after_idle(self._refresh_ui)
              
            
    def _check_for_update(self):
        LOGGER.info("Checking for update.")
        self.update_button.configure(state=tk.DISABLED)
        self.updater.check_update()
        
    
    def _download_update(self):
        LOGGER.info("Download and unzip update.")
        self.update_button.configure(state=tk.DISABLED)
        self.updater.prepare_update()
        
        
    def _start_update(self):
        LOGGER.info("Starting update process. will kill program and restart.")
        self.update_button.configure(state=tk.DISABLED)
        if messagebox.askokcancel(self.st.lan().START_UPDATE, self.st.lan().UPDATE_PREPARED):
            self.updater.start_update()

    def _open_update_site(self):
        """Open website for manual update guidance."""
        ok, err = utils.open_file_with_os(utils.WEBSITE + "/help")
        if not ok:
            messagebox.showerror(self.st.lan().HELP, err, parent=self)
            
    
    def _refresh_ui(self):
        lan = self.st.lan()
        # Update html text if available
        if not self.html_text:  
            if self.updater.help_html:
                self.html_text = self.updater.help_html
                self.html_box.set_html(self.html_text)

        if not utils.can_auto_update():
            self.update_str_var.set(
                getattr(lan, "MANUAL_UPDATE_ONLY",
                        "Auto update is unavailable on this platform. Open website for manual update.")
            )
            self.update_button.configure(
                text=getattr(lan, "OPEN_WEBSITE", "Open Website"),
                state=tk.NORMAL,
                command=self._open_update_site
            )
            self.after(100, self._refresh_ui)
            return
        
        # update button and status
        match self.updater.update_status:
            case UpdateStatus.NONE:
                self.update_str_var.set("")
                self._check_for_update()
            case UpdateStatus.CHECKING:
                self.update_str_var.set(lan.CHECKING_UPDATE)
            case UpdateStatus.NO_UPDATE:
                self.update_str_var.set(lan.NO_UPDATE_FOUND)
                self.update_button.configure(
                    text = lan.CHECK_FOR_UPDATE,
                    state=tk.NORMAL,
                    command=self._check_for_update)
            case UpdateStatus.NEW_VERSION:
                self.update_str_var.set(lan.UPDATE_AVAILABLE + f" v{self.updater.web_version}")
                self.update_button.configure(
                    text=lan.DOWNLOAD_UPDATE,
                    state=tk.NORMAL,
                    command=self._download_update
                    )
                self.update_cmd = self.updater.prepare_update
            case UpdateStatus.DOWNLOADING:
                self.update_str_var.set(lan.DOWNLOADING + f"  {self.updater.dl_progress}")
            case UpdateStatus.UNZIPPING:
                self.update_str_var.set(lan.UNZIPPING)
            case UpdateStatus.PREPARED:
                self.update_str_var.set(lan.UPDATE_PREPARED)
                self.update_button.configure(
                    text=lan.START_UPDATE,
                    state=tk.NORMAL,
                    command = self.updater.start_update)
            case UpdateStatus.ERROR:
                self.update_str_var.set(str(self.updater.update_exception))
                self.update_button.configure(
                    text=lan.CHECK_FOR_UPDATE,
                    state=tk.NORMAL,
                    command=self._check_for_update)
            case _:
                pass
            
        self.after(100, self._refresh_ui)
        
    
    def _on_close(self):
        self.destroy()        
    
