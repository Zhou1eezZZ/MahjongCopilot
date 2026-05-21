"""Custom widgets for the Mahjong Copilot desktop UI."""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk
from typing import Callable

from common.log_helper import LOGGER
from .utils import GUI_STYLE, add_hover_text


class Card(tk.Frame):
    """A lightweight surface container with consistent padding."""

    def __init__(self, master, padding: int | tuple[int, ...] = 16):
        if isinstance(padding, tuple):
            padx = max(padding[0], padding[2] if len(padding) > 2 else padding[0])
            pady = max(padding[1], padding[3] if len(padding) > 3 else padding[1])
        else:
            padx = pady = padding
        super().__init__(
            master,
            bg=GUI_STYLE.palette["surface"],
            highlightbackground=GUI_STYLE.palette["stroke_subtle"],
            highlightcolor=GUI_STYLE.palette["stroke_subtle"],
            highlightthickness=1,
            padx=padx,
            pady=pady,
        )


class ToolBar(ttk.Frame):
    """Modern text toolbar that keeps the old add_button/set_img API."""

    def __init__(self, master, height: int = 44):
        super().__init__(master, style="Surface.TFrame")
        self.height = height
        self.columnconfigure(99, weight=1)
        self._count = 0

    def add_button(self, text: str, img_file: str, command) -> ttk.Button:
        """Add a command button to the toolbar."""
        style = "Accent.TButton" if img_file == "majsoul.png" else "Toolbar.TButton"
        btn = ttk.Button(self, text=text, command=command, style=style)
        btn.img_file = img_file
        btn.tooltip_text = text
        btn.grid(row=0, column=self._count, sticky="w", padx=(0, 6), pady=2)
        add_hover_text(btn, text)
        self._count += 1
        return btn

    def set_img(self, btn: ttk.Button, img_file: str):
        """Update the symbolic button affordance."""
        if getattr(btn, "img_file", None) == img_file:
            return
        text = getattr(btn, "tooltip_text", btn.cget("text"))
        btn.configure(text=text)
        btn.img_file = img_file

    def add_sep(self):
        """Add visual spacing between toolbar groups."""
        spacer = ttk.Frame(self, width=6, style="Surface.TFrame")
        spacer.grid(row=0, column=self._count, sticky="ns")
        self._count += 1


class ToggleSwitch(ttk.Frame):
    """Accessible switch with canvas-drawn state and legacy switch methods."""

    def __init__(self, master, text: str, height: int, font_size: int = 12, command: Callable | None = None):
        super().__init__(master, style="Surface.TFrame")
        self.command = command
        self.is_on = False
        self._state = "off"
        self._enabled = True
        self._width = max(48, int(height * 0.78))
        self._height = 28

        self.canvas = tk.Canvas(
            self,
            width=self._width,
            height=self._height,
            highlightthickness=0,
            bg=GUI_STYLE.palette["surface"],
        )
        self.canvas.grid(row=0, column=0, sticky="w")
        self.text_label = ttk.Label(self, text=text, style="Surface.TLabel", font=GUI_STYLE.font_normal(size=font_size))
        self.text_label.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.columnconfigure(1, weight=1)

        if command:
            for widget in (self, self.canvas, self.text_label):
                widget.bind("<Button-1>", self._on_click)
                widget.bind("<Return>", self._on_click)
                widget.bind("<space>", self._on_click)

        self._draw()

    def switch_on(self):
        """Switch on."""
        if not self.is_on or self._state != "on":
            self.is_on = True
            self._state = "on"
            self._draw()

    def switch_off(self):
        """Switch off."""
        if self.is_on or self._state != "off":
            self.is_on = False
            self._state = "off"
            self._draw()

    def switch_mid(self):
        """Switch to transient pending state."""
        self._state = "mid"
        self._draw()

    def set_enabled(self, enabled: bool):
        """Enable or disable pointer interaction."""
        self._enabled = enabled
        self._draw()

    def _on_click(self, _event=None):
        if self.command and self._enabled:
            self.command()

    def _draw(self):
        self.canvas.delete("all")
        palette = GUI_STYLE.palette
        if not self._enabled:
            track = palette["stroke"]
            knob = palette["surface_alt"]
        elif self._state == "on":
            track = palette["green"]
            knob = "#ffffff"
        elif self._state == "mid":
            track = palette["yellow"]
            knob = "#ffffff"
        else:
            track = palette["stroke"]
            knob = "#ffffff"

        radius = self._height // 2
        self.canvas.create_oval(1, 1, 1 + self._height - 2, self._height - 1, fill=track, outline=track)
        self.canvas.create_oval(
            self._width - self._height + 1,
            1,
            self._width - 1,
            self._height - 1,
            fill=track,
            outline=track,
        )
        self.canvas.create_rectangle(radius, 1, self._width - radius, self._height - 1, fill=track, outline=track)

        knob_size = self._height - 8
        x = self._width - knob_size - 5 if self._state == "on" else 5
        if self._state == "mid":
            x = (self._width - knob_size) // 2
        self.canvas.create_oval(x, 4, x + knob_size, 4 + knob_size, fill=knob, outline=knob)


class Timer(ttk.Frame):
    """A compact hh:mm:ss countdown widget."""

    START = "Start"
    STOP = "Stop"

    def __init__(self, master: tk.Frame, height: int, font_size: int = 10, hover_text: str | None = None):
        super().__init__(master, style="Surface.TFrame")
        self.font_size = font_size
        self.hover_text = hover_text
        self.callback: Callable | None = None
        self.timer_running = False
        self.timer_id = None
        self.stop_time: float | None = None

        self.hour_var = tk.StringVar(value="01")
        self.minute_var = tk.StringVar(value="00")
        self.second_var = tk.StringVar(value="00")

        time_frame = ttk.Frame(self, style="Surface.TFrame")
        time_frame.grid(row=0, column=0, sticky="w")
        self.entries: list[ttk.Entry] = []
        self._setup_entry(time_frame, self.hour_var, 23)
        ttk.Label(time_frame, text=":", style="Surface.TLabel").pack(side=tk.LEFT)
        self._setup_entry(time_frame, self.minute_var, 59)
        ttk.Label(time_frame, text=":", style="Surface.TLabel").pack(side=tk.LEFT)
        self._setup_entry(time_frame, self.second_var, 59)

        self.the_btn = ttk.Button(self, text=Timer.START, command=self._toggle_timer, width=8)
        self.the_btn.grid(row=0, column=1, sticky="w", padx=(8, 0))
        if self.hover_text:
            add_hover_text(self.the_btn, self.hover_text)

    def set_callback(self, callback: Callable):
        """Set callback function to be called when the timer finishes."""
        self.callback = callback

    def _setup_entry(self, parent: ttk.Frame, var: tk.StringVar, max_val: int):
        def validate_time(value):
            try:
                val = int(value)
                if 0 <= val <= max_val:
                    self.after_idle(lambda: var.set(f"{val:02}"))
                    return True
                self.after_idle(lambda: var.set(f"{min(max_val, max(0, val)):02}"))
                return False
            except Exception:
                self.after_idle(lambda: var.set("00"))
                return False

        entry = ttk.Entry(
            parent,
            textvariable=var,
            validatecommand=(self.register(validate_time), "%P"),
            validate="focusout",
            style="Form.TEntry",
            width=3,
            justify=tk.CENTER,
            font=GUI_STYLE.font_mono(size=self.font_size),
        )
        entry.pack(side=tk.LEFT, padx=1)
        self.entries.append(entry)

    def _toggle_timer(self):
        if self.timer_running:
            self._stop_timer()
        else:
            self._start_timer()

    def _start_timer(self):
        self.timer_running = True
        self.the_btn.configure(text=Timer.STOP)
        hours = int(self.hour_var.get())
        minutes = int(self.minute_var.get())
        seconds = int(self.second_var.get())
        LOGGER.info("Timer set %d:%d:%d", hours, minutes, seconds)
        self.stop_time = time.time() + hours * 3600 + minutes * 60 + seconds
        for entry in self.entries:
            entry.configure(state=tk.DISABLED)
        self._run_timer()

    def _run_timer(self):
        """Run timer and update the time display."""
        if self.timer_running and self.stop_time is not None:
            remaining_time = int(self.stop_time - time.time())
            if remaining_time > 0:
                hours = remaining_time // 3600
                minutes = (remaining_time % 3600) // 60
                seconds = remaining_time % 60
                self.hour_var.set(f"{hours:02}")
                self.minute_var.set(f"{minutes:02}")
                self.second_var.set(f"{seconds:02}")
                self.timer_id = self.after(200, self._run_timer)
            else:
                self._clear_time()
                if self.callback:
                    self.callback()
                self._stop_timer()

    def _clear_time(self):
        self.hour_var.set("01")
        self.minute_var.set("00")
        self.second_var.set("00")

    def _stop_timer(self):
        if self.timer_id is not None:
            self.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_running = False
        self.the_btn.configure(text=Timer.START)
        for entry in self.entries:
            entry.configure(state=tk.NORMAL)
        self.stop_time = None
        LOGGER.info("Timer stopped.")


class StatusBar(ttk.Frame):
    """Status bar with adaptive columns."""

    def __init__(self, master, n_cols: int):
        super().__init__(master, style="Surface.TFrame", padding=(8, 6))
        self.n_cols = n_cols
        self.columns: list[ttk.Label] = []
        for i in range(n_cols):
            weight = 2 if i == n_cols - 1 else 1
            self.columnconfigure(i, weight=weight, uniform="status")
            label = ttk.Label(
                self,
                text="",
                style="Surface.TLabel",
                anchor="w",
                padding=(6, 2),
            )
            label.grid(row=0, column=i, sticky="ew", padx=(0, 8 if i < n_cols - 1 else 0))
            label.image_file = "placeholder"
            self.columns.append(label)

    def update_column(self, index: int, text: str, icon_path: str | None = None):
        """Update column text and optional legacy icon status."""
        if not 0 <= index < len(self.columns):
            return

        label = self.columns[index]
        prefix = ""
        color = GUI_STYLE.palette["text"]
        if icon_path:
            lower = icon_path.lower()
            if "green" in lower:
                prefix = "● "
                color = GUI_STYLE.palette["green"]
            elif "yellow" in lower:
                prefix = "● "
                color = "#b88300"
            elif "red" in lower:
                prefix = "● "
                color = GUI_STYLE.palette["red"]
            elif "gray" in lower:
                prefix = "● "
                color = GUI_STYLE.palette["gray"]
            elif "ready" in lower:
                prefix = "● "
                color = GUI_STYLE.palette["ready"]
        label.configure(text=prefix + str(text), foreground=color)
        label.image_file = icon_path or "placeholder"
