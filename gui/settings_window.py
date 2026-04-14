""" GUI Settings Window """
import tkinter as tk
from tkinter import ttk, messagebox

from common import utils
from common.utils import Folder
from common.utils import list_children
from common.log_helper import LOGGER
from common.settings import Settings
from common.lan_str import LAN_OPTIONS
from bot import MODEL_TYPE_STRINGS
from .utils import GUI_STYLE, add_hover_text


class SettingsWindow(tk.Toplevel):
    """Settings dialog window."""

    PRESET_VALUES = {
        "stable": (1, 3, False),
        "balanced": (3, 4, True),
        "free": (5, 6, True),
    }

    def __init__(self, parent: tk.Frame, setting: Settings):
        super().__init__(parent)
        self.st = setting

        self.geometry("900x700")
        self.minsize(860, 640)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 10}+{parent_y + 10}")

        self.exit_save: bool = False
        self.gui_need_reload: bool = False
        self.model_updated: bool = False
        self.mitm_proxinject_updated: bool = False

        self._active_section: str = ""
        self._syncing_preset: bool = False
        self._automation_advanced_visible: bool = False

        self._sections: dict[str, ttk.Frame] = {}
        self._section_contents: dict[str, ttk.Frame] = {}
        self._section_buttons: dict[str, tk.Button] = {}

        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style)
        self.create_widgets()

    def create_widgets(self):
        """Create widgets for settings dialog."""
        self.title(self.st.lan().SETTINGS)

        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True)

        nav_frame = tk.Frame(body, width=180, bd=1, relief=tk.GROOVE)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        nav_frame.pack_propagate(False)

        right_frame = ttk.Frame(body)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_sections(right_frame)
        self._build_nav(nav_frame)

        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        cancel_button = ttk.Button(btn_frame, text=self.st.lan().CANCEL, command=self._on_cancel)
        cancel_button.pack(side=tk.LEFT, padx=8)
        save_button = ttk.Button(btn_frame, text=self.st.lan().SAVE, command=self._on_save)
        save_button.pack(side=tk.RIGHT, padx=8)

        self._show_section("basic")

    def _build_sections(self, parent: ttk.Frame):
        """Build right-side section pages."""
        for key in ("basic", "model", "automation", "advanced"):
            page, content = self._create_scrollable_page(parent)
            self._sections[key] = page
            self._section_contents[key] = content

        self._build_basic_section(self._section_contents["basic"])
        self._build_model_section(self._section_contents["model"])
        self._build_automation_section(self._section_contents["automation"])
        self._build_advanced_section(self._section_contents["advanced"])

    def _build_nav(self, parent: tk.Frame):
        """Build left navigation buttons."""
        header = tk.Label(parent, text=self.st.lan().SETTINGS, font=GUI_STYLE.font_normal(size=13))
        header.pack(fill=tk.X, padx=10, pady=(10, 8))

        btn_args = {"anchor": "w", "relief": tk.FLAT, "padx": 12, "pady": 8, "bd": 0}

        defs = [
            ("basic", self.st.lan().SECTION_BASIC),
            ("model", self.st.lan().SECTION_MODEL),
            ("automation", self.st.lan().SECTION_AUTOMATION),
            ("advanced", self.st.lan().SECTION_ADVANCED),
        ]

        for key, text in defs:
            btn = tk.Button(parent, text=text, command=lambda k=key: self._show_section(k), **btn_args)
            btn.pack(fill=tk.X, padx=8, pady=2)
            self._section_buttons[key] = btn

    def _create_scrollable_page(self, parent: ttk.Frame) -> tuple[ttk.Frame, ttk.Frame]:
        """Create a scrollable content page."""
        page = ttk.Frame(parent)
        canvas = tk.Canvas(page, highlightthickness=0)
        scrollbar = ttk.Scrollbar(page, orient=tk.VERTICAL, command=canvas.yview)
        content = ttk.Frame(canvas, padding=(4, 4))

        window_id = canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(event):
            try:
                canvas.itemconfigure(window_id, width=event.width)
            except Exception:
                pass

        content.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        return page, content

    def _show_section(self, section: str):
        """Switch visible section page."""
        if section not in self._sections:
            return
        if self._active_section == section:
            return

        for key, page in self._sections.items():
            if key == section:
                page.pack(fill=tk.BOTH, expand=True)
            else:
                page.pack_forget()

        self._active_section = section
        for key, button in self._section_buttons.items():
            if key == section:
                button.configure(bg="#d8ecff")
            else:
                button.configure(bg=self.cget("bg"))

    def _build_basic_section(self, frame: ttk.Frame):
        pad_args = {"padx": (4, 4), "pady": (5, 4)}
        args_label = {"sticky": "e", **pad_args}
        args_entry = {"sticky": "w", **pad_args}
        std_wid = 22

        row = 0
        ttk.Label(frame, text=self.st.lan().SECTION_BASIC, font=GUI_STYLE.font_normal(size=13)).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(2, 10)
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().BROWSER).grid(row=row, column=0, **args_label)
        self.auto_launch_var = tk.BooleanVar(value=self.st.auto_launch_browser)
        ttk.Checkbutton(
            frame,
            variable=self.auto_launch_var,
            text=self.st.lan().AUTO_LAUNCH_BROWSER,
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)

        ttk.Label(frame, text=self.st.lan().CLIENT_SIZE).grid(row=row, column=2, **args_label)
        options = ["960 x 540", "1280 x 720", "1600 x 900", "1920 x 1080", "2560 x 1440", "3840 x 2160"]
        setting_size = f"{self.st.browser_width} x {self.st.browser_height}"
        self.client_size_var = tk.StringVar(value=setting_size)
        ttk.Combobox(
            frame,
            textvariable=self.client_size_var,
            values=options,
            state="readonly",
            width=std_wid,
        ).grid(row=row, column=3, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().MAJSOUL_URL).grid(row=row, column=0, **args_label)
        self.ms_url_var = tk.StringVar(value=self.st.ms_url)
        ttk.Entry(frame, textvariable=self.ms_url_var, width=std_wid * 3).grid(
            row=row, column=1, columnspan=2, **args_entry
        )

        self.enable_extension_var = tk.BooleanVar(value=self.st.enable_chrome_ext)
        ttk.Checkbutton(
            frame,
            variable=self.enable_extension_var,
            text=self.st.lan().ENABLE_CHROME_EXT,
            width=std_wid + 2,
        ).grid(row=row, column=3, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().LANGUAGE).grid(row=row, column=0, **args_label)
        options = [v.LANGUAGE_NAME for v in LAN_OPTIONS.values()]
        self.language_var = tk.StringVar(value=LAN_OPTIONS[self.st.language].LANGUAGE_NAME)
        ttk.Combobox(
            frame,
            textvariable=self.language_var,
            values=options,
            state="readonly",
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)

    def _build_model_section(self, frame: ttk.Frame):
        pad_args = {"padx": (4, 4), "pady": (5, 4)}
        args_label = {"sticky": "e", **pad_args}
        args_entry = {"sticky": "w", **pad_args}
        std_wid = 22

        row = 0
        ttk.Label(frame, text=self.st.lan().SECTION_MODEL, font=GUI_STYLE.font_normal(size=13)).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(2, 10)
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().MODEL_TYPE).grid(row=row, column=0, **args_label)
        self.model_type_var = tk.StringVar(value=self.st.model_type)
        ttk.Combobox(
            frame,
            textvariable=self.model_type_var,
            values=MODEL_TYPE_STRINGS,
            state="readonly",
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)

        model_files = [""] + list_children(str(utils.sub_folder(Folder.MODEL)))
        row += 1
        ttk.Label(frame, text=self.st.lan().AI_MODEL_FILE).grid(row=row, column=0, **args_label)
        self.model_file_var = tk.StringVar(value=self.st.model_file)
        ttk.Combobox(
            frame,
            textvariable=self.model_file_var,
            values=model_files,
            state="readonly",
            width=std_wid * 3,
        ).grid(row=row, column=1, columnspan=3, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().AI_MODEL_FILE_3P).grid(row=row, column=0, **args_label)
        self.model_file_3p_var = tk.StringVar(value=self.st.model_file_3p)
        ttk.Combobox(
            frame,
            textvariable=self.model_file_3p_var,
            values=model_files,
            state="readonly",
            width=std_wid * 3,
        ).grid(row=row, column=1, columnspan=3, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().AKAGI_OT_URL).grid(row=row, column=0, **args_label)
        self.akagiot_url_var = tk.StringVar(value=self.st.akagi_ot_url)
        ttk.Entry(frame, textvariable=self.akagiot_url_var, width=std_wid * 4).grid(
            row=row, column=1, columnspan=3, **args_entry
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().AKAGI_OT_APIKEY).grid(row=row, column=0, **args_label)
        self.akagiot_apikey_var = tk.StringVar(value=self.st.akagi_ot_apikey)
        ttk.Entry(frame, textvariable=self.akagiot_apikey_var, width=std_wid * 4).grid(
            row=row, column=1, columnspan=3, **args_entry
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().MJAPI_URL).grid(row=row, column=0, **args_label)
        self.mjapi_url_var = tk.StringVar(value=self.st.mjapi_url)
        ttk.Entry(frame, textvariable=self.mjapi_url_var, width=std_wid * 4).grid(
            row=row, column=1, columnspan=3, **args_entry
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().MJAPI_USER).grid(row=row, column=0, **args_label)
        self.mjapi_user_var = tk.StringVar(value=self.st.mjapi_user)
        ttk.Entry(frame, textvariable=self.mjapi_user_var, width=std_wid).grid(row=row, column=1, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().MJAPI_SECRET).grid(row=row, column=0, **args_label)
        self.mjapi_secret_var = tk.StringVar(value=self.st.mjapi_secret)
        ttk.Entry(frame, textvariable=self.mjapi_secret_var, width=std_wid * 4).grid(
            row=row, column=1, columnspan=3, **args_entry
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().MJAPI_MODEL_SELECT).grid(row=row, column=0, **args_label)
        self.mjapi_model_select_var = tk.StringVar(value=self.st.mjapi_model_select)
        options = self.st.mjapi_models
        ttk.Combobox(
            frame,
            textvariable=self.mjapi_model_select_var,
            values=options,
            state="readonly",
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)
        ttk.Label(frame, text=self.st.lan().LOGIN_TO_REFRESH).grid(row=row, column=2, columnspan=2, **args_entry)

    def _build_automation_section(self, frame: ttk.Frame):
        pad_args = {"padx": (4, 4), "pady": (5, 4)}
        args_label = {"sticky": "e", **pad_args}
        args_entry = {"sticky": "w", **pad_args}
        std_wid = 22

        row = 0
        ttk.Label(frame, text=self.st.lan().SECTION_AUTOMATION, font=GUI_STYLE.font_normal(size=13)).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(2, 10)
        )

        preset_labels = self._preset_label_map()
        self.ai_style_preset_var = tk.StringVar(
            value=preset_labels[self._detect_preset_code(
                self.st.ai_randomize_choice,
                self.st.ai_randomize_top_n,
                self.st.ai_near_tie_prefer_low,
            )]
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().AI_STYLE_PRESET).grid(row=row, column=0, **args_label)
        self.preset_combo = ttk.Combobox(
            frame,
            textvariable=self.ai_style_preset_var,
            values=list(preset_labels.values()),
            state="readonly",
            width=std_wid * 2,
        )
        self.preset_combo.grid(row=row, column=1, columnspan=2, **args_entry)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)

        row += 1
        self.random_move_var = tk.BooleanVar(value=self.st.auto_random_move)
        ttk.Checkbutton(
            frame,
            variable=self.random_move_var,
            text=self.st.lan().MOUSE_RANDOM_MOVE,
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)

        self.auto_idle_move_var = tk.BooleanVar(value=self.st.auto_idle_move)
        ttk.Checkbutton(
            frame,
            variable=self.auto_idle_move_var,
            text=self.st.lan().AUTO_IDLE_MOVE,
            width=std_wid,
        ).grid(row=row, column=2, **args_entry)

        self.auto_drag_dahai_var = tk.BooleanVar(value=self.st.auto_dahai_drag)
        ttk.Checkbutton(
            frame,
            variable=self.auto_drag_dahai_var,
            text=self.st.lan().DRAG_DAHAI,
            width=std_wid,
        ).grid(row=row, column=3, **args_entry)

        row += 1
        self.auto_emoji_before_hu_var = tk.BooleanVar(value=self.st.auto_emoji_before_hu)
        ttk.Checkbutton(
            frame,
            variable=self.auto_emoji_before_hu_var,
            text=self.st.lan().AUTO_EMOJI_BEFORE_HU,
            width=std_wid * 2,
        ).grid(row=row, column=1, **args_entry)

        self.auto_emoji_on_chi_robbed_var = tk.BooleanVar(value=self.st.auto_emoji_on_chi_robbed)
        ttk.Checkbutton(
            frame,
            variable=self.auto_emoji_on_chi_robbed_var,
            text=self.st.lan().AUTO_EMOJI_ON_CHI_ROBBED,
            width=std_wid * 2,
        ).grid(row=row, column=2, columnspan=2, **args_entry)

        row += 1
        ttk.Label(frame, text=self.st.lan().REPLY_EMOJI_CHANCE).grid(row=row, column=0, **args_label)
        emoji_options = [f"{i * 10}%" for i in range(11)]
        emoji_options[0] = "0% (off)"
        self.reply_emoji_var = tk.StringVar(value=f"{int(self.st.auto_reply_emoji_rate * 100)}%")
        ttk.Combobox(
            frame,
            textvariable=self.reply_emoji_var,
            values=emoji_options,
            state="readonly",
            width=std_wid,
        ).grid(row=row, column=1, **args_entry)

        ttk.Label(frame, text=self.st.lan().RANDOM_DELAY_RANGE).grid(row=row, column=2, **args_label)
        self.delay_random_lower_var = tk.DoubleVar(value=self.st.delay_random_lower)
        tk.Entry(frame, textvariable=self.delay_random_lower_var, width=std_wid).grid(row=row, column=3, **args_entry)

        row += 1
        ttk.Label(frame, text="").grid(row=row, column=0, **args_label)
        self.delay_random_upper_var = tk.DoubleVar(value=self.st.delay_random_upper)
        tk.Entry(frame, textvariable=self.delay_random_upper_var, width=std_wid).grid(row=row, column=3, **args_entry)

        row += 1
        self.btn_toggle_adv = ttk.Button(frame, text=self.st.lan().SHOW_ADVANCED, command=self._toggle_automation_advanced)
        self.btn_toggle_adv.grid(row=row, column=1, **args_entry)

        row += 1
        self.automation_adv_frame = ttk.Frame(frame)
        self.automation_adv_frame.grid(row=row, column=0, columnspan=4, sticky="ew", padx=(4, 4), pady=(2, 8))
        self.automation_adv_frame.grid_remove()

        adv_row = 0
        ttk.Label(self.automation_adv_frame, text=self.st.lan().RANDOM_CHOICE).grid(row=adv_row, column=0, **args_label)
        self.randomized_choice_var = tk.StringVar(value=str(self.st.ai_randomize_choice))
        ttk.Combobox(
            self.automation_adv_frame,
            textvariable=self.randomized_choice_var,
            values=[str(i) for i in range(6)],
            state="readonly",
            width=std_wid,
        ).grid(row=adv_row, column=1, **args_entry)

        ttk.Label(self.automation_adv_frame, text=self.st.lan().AI_RANDOMIZE_TOP_N).grid(row=adv_row, column=2, **args_label)
        self.randomize_top_n_var = tk.StringVar(value=str(self.st.ai_randomize_top_n))
        ttk.Combobox(
            self.automation_adv_frame,
            textvariable=self.randomize_top_n_var,
            values=["3", "4", "5", "6"],
            state="readonly",
            width=std_wid,
        ).grid(row=adv_row, column=3, **args_entry)

        adv_row += 1
        self.near_tie_prefer_low_var = tk.BooleanVar(value=self.st.ai_near_tie_prefer_low)
        ttk.Checkbutton(
            self.automation_adv_frame,
            variable=self.near_tie_prefer_low_var,
            text=self.st.lan().AI_NEAR_TIE_PREFER_LOW,
            width=std_wid * 3,
        ).grid(row=adv_row, column=1, columnspan=3, **args_entry)

        self.randomized_choice_var.trace_add("write", self._on_strategy_values_changed)
        self.randomize_top_n_var.trace_add("write", self._on_strategy_values_changed)
        self.near_tie_prefer_low_var.trace_add("write", self._on_strategy_values_changed)

    def _build_advanced_section(self, frame: ttk.Frame):
        pad_args = {"padx": (4, 4), "pady": (5, 4)}
        args_label = {"sticky": "e", **pad_args}
        args_entry = {"sticky": "w", **pad_args}
        std_wid = 22

        row = 0
        ttk.Label(frame, text=self.st.lan().SECTION_ADVANCED, font=GUI_STYLE.font_normal(size=13)).grid(
            row=row, column=0, columnspan=4, sticky="w", pady=(2, 10)
        )

        row += 1
        ttk.Label(frame, text=self.st.lan().MITM_PORT).grid(row=row, column=0, **args_label)
        self.mitm_port_var = tk.StringVar(value=self.st.mitm_port)
        ttk.Entry(frame, textvariable=self.mitm_port_var, width=std_wid).grid(row=row, column=1, **args_entry)

        ttk.Label(frame, text=self.st.lan().UPSTREAM_PROXY).grid(row=row, column=2, **args_label)
        self.upstream_proxy_var = tk.StringVar(value=self.st.upstream_proxy)
        ttk.Entry(frame, textvariable=self.upstream_proxy_var, width=std_wid * 2).grid(row=row, column=3, **args_entry)

        row += 1
        self.proxy_inject_var = tk.BooleanVar(value=self.st.enable_proxinject)
        self.check_proxy_inject = ttk.Checkbutton(
            frame,
            variable=self.proxy_inject_var,
            text=self.st.lan().CLIENT_INJECT_PROXY,
            width=std_wid * 3,
        )
        self.check_proxy_inject.grid(row=row, column=1, columnspan=3, **args_entry)
        if not utils.can_proxinject():
            self.proxy_inject_var.set(False)
            self.check_proxy_inject.configure(state=tk.DISABLED)
            add_hover_text(
                self.check_proxy_inject,
                getattr(self.st.lan(), "PROXY_INJECT_UNSUPPORTED", "Only available on Windows"),
            )

        row += 1
        ttk.Label(frame, text=self.st.lan().SETTINGS_TIPS, width=std_wid * 4).grid(
            row=row,
            column=0,
            columnspan=4,
            **args_entry,
        )

    def _toggle_automation_advanced(self):
        self._automation_advanced_visible = not self._automation_advanced_visible
        if self._automation_advanced_visible:
            self.automation_adv_frame.grid()
            self.btn_toggle_adv.configure(text=self.st.lan().HIDE_ADVANCED)
        else:
            self.automation_adv_frame.grid_remove()
            self.btn_toggle_adv.configure(text=self.st.lan().SHOW_ADVANCED)

    def _preset_label_map(self) -> dict[str, str]:
        return {
            "stable": self.st.lan().AI_STYLE_STABLE,
            "balanced": self.st.lan().AI_STYLE_BALANCED,
            "free": self.st.lan().AI_STYLE_FREE,
        }

    def _preset_code_from_label(self, label: str) -> str:
        for code, text in self._preset_label_map().items():
            if label == text:
                return code
        return "free"

    def _detect_preset_code(self, randomize: int, top_n: int, near_tie: bool) -> str:
        if (randomize, top_n, near_tie) == self.PRESET_VALUES["stable"]:
            return "stable"
        if (randomize, top_n, near_tie) == self.PRESET_VALUES["balanced"]:
            return "balanced"
        return "free"

    def _on_preset_changed(self, _event=None):
        code = self._preset_code_from_label(self.ai_style_preset_var.get())
        values = self.PRESET_VALUES.get(code)
        if not values:
            return
        self._syncing_preset = True
        self.randomized_choice_var.set(str(values[0]))
        self.randomize_top_n_var.set(str(values[1]))
        self.near_tie_prefer_low_var.set(values[2])
        self._syncing_preset = False

    def _on_strategy_values_changed(self, *_args):
        if self._syncing_preset:
            return
        randomize = self._parse_int(self.randomized_choice_var.get(), 1, 0, 5)
        top_n = self._parse_int(self.randomize_top_n_var.get(), 3, 3, 6)
        near_tie = bool(self.near_tie_prefer_low_var.get())
        code = self._detect_preset_code(randomize, top_n, near_tie)
        self._syncing_preset = True
        self.ai_style_preset_var.set(self._preset_label_map()[code])
        self._syncing_preset = False

    @staticmethod
    def _parse_int(value, default: int, min_value: int, max_value: int) -> int:
        try:
            parsed = int(value)
        except Exception:
            return default
        return max(min_value, min(max_value, parsed))

    def _on_save(self):
        """Get values from widgets, validate, and save them."""
        try:
            size_list = self.client_size_var.get().split(" x ")
            width_new = int(size_list[0])
            height_new = int(size_list[1])
        except Exception:
            width_new = self.st.browser_width
            height_new = self.st.browser_height

        ms_url_new = self.ms_url_var.get()

        try:
            mitm_port_new = int(self.mitm_port_var.get())
        except Exception:
            messagebox.showerror("⚠", self.st.lan().MITM_PORT_ERROR_PROMPT)
            return
        if not self.st.valid_mitm_port(mitm_port_new):
            messagebox.showerror("⚠", self.st.lan().MITM_PORT_ERROR_PROMPT)
            return

        upstream_proxy_new = self.upstream_proxy_var.get()
        proxy_inject_new = self.proxy_inject_var.get()
        if not utils.can_proxinject():
            proxy_inject_new = False
        if (
            upstream_proxy_new != self.st.upstream_proxy
            or mitm_port_new != self.st.mitm_port
            or proxy_inject_new != self.st.enable_proxinject
        ):
            self.mitm_proxinject_updated = True

        language_name = self.language_var.get()
        language_new = self.st.language
        for code, lan in LAN_OPTIONS.items():
            if language_name == lan.LANGUAGE_NAME:
                language_new = code
                break
        self.gui_need_reload = self.st.language != language_new

        model_type_new = self.model_type_var.get()
        model_file_new = self.model_file_var.get()
        mode_file_3p_new = self.model_file_3p_var.get()
        akagi_url_new = self.akagiot_url_var.get()
        akagi_apikey_new = self.akagiot_apikey_var.get()
        mjapi_url_new = self.mjapi_url_var.get()
        mjapi_user_new = self.mjapi_user_var.get()
        mjapi_secret_new = self.mjapi_secret_var.get()
        mjapi_model_select_new = self.mjapi_model_select_var.get()
        if (
            self.st.model_type != model_type_new
            or self.st.model_file != model_file_new
            or self.st.model_file_3p != mode_file_3p_new
            or self.st.akagi_ot_url != akagi_url_new
            or self.st.akagi_ot_apikey != akagi_apikey_new
            or self.st.mjapi_url != mjapi_url_new
            or self.st.mjapi_user != mjapi_user_new
            or self.st.mjapi_secret != mjapi_secret_new
            or self.st.mjapi_model_select != mjapi_model_select_new
        ):
            self.model_updated = True

        randomized_choice_new = self._parse_int(self.randomized_choice_var.get(), self.st.ai_randomize_choice, 0, 5)
        randomize_top_n_new = self._parse_int(self.randomize_top_n_var.get(), self.st.ai_randomize_top_n, 3, 6)

        reply_emoji_new = self.st.auto_reply_emoji_rate
        try:
            reply_emoji_new = int(self.reply_emoji_var.get().split("%")[0]) / 100
        except Exception as e:
            LOGGER.warning("Failed to parse auto reply emoji rate: %s", e, exc_info=True)
        reply_emoji_new = max(0.0, min(1.0, reply_emoji_new))

        try:
            delay_lower_new = max(0, float(self.delay_random_lower_var.get()))
            delay_upper_new = max(delay_lower_new, float(self.delay_random_upper_var.get()))
        except Exception:
            messagebox.showerror("⚠", self.st.lan().RANDOM_DELAY_RANGE)
            return

        try:
            auto_emoji_before_hu_new = bool(self.auto_emoji_before_hu_var.get())
        except Exception as e:
            LOGGER.warning("Failed to parse auto_emoji_before_hu setting: %s", e, exc_info=True)
            auto_emoji_before_hu_new = False
        try:
            auto_emoji_on_chi_robbed_new = bool(self.auto_emoji_on_chi_robbed_var.get())
        except Exception as e:
            LOGGER.warning("Failed to parse auto_emoji_on_chi_robbed setting: %s", e, exc_info=True)
            auto_emoji_on_chi_robbed_new = False

        try:
            near_tie_prefer_low_new = bool(self.near_tie_prefer_low_var.get())
        except Exception as e:
            LOGGER.warning("Failed to parse ai_near_tie_prefer_low setting: %s", e, exc_info=True)
            near_tie_prefer_low_new = False

        ai_style_preset_new = self._detect_preset_code(
            randomized_choice_new,
            randomize_top_n_new,
            near_tie_prefer_low_new,
        )

        self.st.auto_launch_browser = self.auto_launch_var.get()
        self.st.browser_width = width_new
        self.st.browser_height = height_new
        self.st.ms_url = ms_url_new
        self.st.enable_chrome_ext = self.enable_extension_var.get()
        self.st.mitm_port = mitm_port_new
        self.st.upstream_proxy = upstream_proxy_new
        self.st.language = language_new
        self.st.enable_proxinject = proxy_inject_new

        self.st.model_type = model_type_new
        self.st.model_file = model_file_new
        self.st.model_file_3p = mode_file_3p_new
        self.st.akagi_ot_url = akagi_url_new
        self.st.akagi_ot_apikey = akagi_apikey_new
        self.st.mjapi_url = mjapi_url_new
        self.st.mjapi_user = mjapi_user_new
        self.st.mjapi_secret = mjapi_secret_new
        self.st.mjapi_model_select = mjapi_model_select_new

        self.st.auto_idle_move = self.auto_idle_move_var.get()
        self.st.auto_dahai_drag = self.auto_drag_dahai_var.get()
        self.st.auto_random_move = self.random_move_var.get()
        self.st.ai_randomize_choice = randomized_choice_new
        self.st.ai_randomize_top_n = randomize_top_n_new
        self.st.ai_near_tie_prefer_low = near_tie_prefer_low_new
        self.st.ai_style_preset = ai_style_preset_new
        self.st.auto_reply_emoji_rate = reply_emoji_new
        self.st.auto_emoji_before_hu = auto_emoji_before_hu_new
        self.st.auto_emoji_on_chi_robbed = auto_emoji_on_chi_robbed_new
        self.st.delay_random_lower = delay_lower_new
        self.st.delay_random_upper = delay_upper_new

        self.st.save_json()
        self.exit_save = True
        if self.mitm_proxinject_updated:
            messagebox.showinfo(self.st.lan().SETTINGS, self.st.lan().SETTINGS_TIPS, parent=self, icon="info", type="ok")
        self.destroy()

    def _on_cancel(self):
        LOGGER.info("Closing settings window without saving")
        self.exit_save = False
        self.destroy()
