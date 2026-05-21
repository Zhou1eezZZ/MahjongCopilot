"""Settings window for the tkinter GUI."""

import sys
import tkinter as tk
from tkinter import ttk, messagebox

from common import utils
from common.utils import Folder, list_children
from common.log_helper import LOGGER
from common.settings import Settings
from common.lan_str import LAN_OPTIONS
from bot import MODEL_TYPE_STRINGS
from .utils import GUI_STYLE, add_hover_text
from .widgets import Card


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

        self.geometry("980x720")
        self.minsize(780, 560)
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        self.geometry(f"+{parent_x + 18}+{parent_y + 18}")
        self.configure(bg=GUI_STYLE.palette["bg"])

        self.exit_save = False
        self.gui_need_reload = False
        self.model_updated = False
        self.mitm_proxinject_updated = False

        self._active_section = ""
        self._syncing_preset = False
        self._automation_advanced_visible = False

        self._sections = {}
        self._section_contents = {}
        self._section_buttons = {}
        self._section_canvases = {}

        style = ttk.Style(self)
        GUI_STYLE.set_style_normal(style)
        self.create_widgets()

    def create_widgets(self):
        """Create widgets for settings dialog."""
        self.title(self.st.lan().SETTINGS)

        root = ttk.Frame(self, padding=(18, 16, 18, 14))
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        sidebar = ttk.Frame(root, width=210)
        sidebar.grid(row=0, column=0, sticky=tk.NS, padx=(0, 14))
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)

        content_host = ttk.Frame(root)
        content_host.grid(row=0, column=1, sticky=tk.NSEW)
        content_host.columnconfigure(0, weight=1)
        content_host.rowconfigure(0, weight=1)

        footer = ttk.Frame(root)
        footer.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(14, 0))
        footer.columnconfigure(0, weight=1)

        self._build_nav(sidebar)
        self._build_sections(content_host)

        cancel_button = ttk.Button(footer, text=self.st.lan().CANCEL, command=self._on_cancel)
        cancel_button.grid(row=0, column=1, sticky="e", padx=(0, 8))
        save_button = ttk.Button(footer, text=self.st.lan().SAVE, command=self._on_save, style="Accent.TButton")
        save_button.grid(row=0, column=2, sticky="e")

        self._show_section("basic")

    def _build_nav(self, parent: ttk.Frame):
        """Build left navigation buttons."""
        ttk.Label(parent, text=self.st.lan().SETTINGS, style="Title.TLabel").grid(
            row=0, column=0, sticky="w", padx=8, pady=(2, 16)
        )

        definitions = [
            ("basic", self.st.lan().SECTION_BASIC),
            ("model", self.st.lan().SECTION_MODEL),
            ("automation", self.st.lan().SECTION_AUTOMATION),
            ("advanced", self.st.lan().SECTION_ADVANCED),
        ]
        for row, (key, text) in enumerate(definitions, start=1):
            button = ttk.Button(
                parent,
                text=text,
                command=lambda k=key: self._show_section(k),
                style="Sidebar.TButton",
            )
            button.grid(row=row, column=0, sticky=tk.EW, padx=2, pady=3)
            self._section_buttons[key] = button

        parent.rowconfigure(len(definitions) + 1, weight=1)

    def _build_sections(self, parent: ttk.Frame):
        """Build right-side section pages."""
        for key in ("basic", "model", "automation", "advanced"):
            page, content, canvas = self._create_scrollable_page(parent)
            page.grid(row=0, column=0, sticky=tk.NSEW)
            page.grid_remove()
            self._sections[key] = page
            self._section_contents[key] = content
            self._section_canvases[key] = canvas

        self._build_basic_section(self._section_contents["basic"])
        self._build_model_section(self._section_contents["model"])
        self._build_automation_section(self._section_contents["automation"])
        self._build_advanced_section(self._section_contents["advanced"])
        for key, content in self._section_contents.items():
            self._bind_mousewheel_tree(content, self._section_canvases[key])
            self._bind_mousewheel_tree(self._sections[key], self._section_canvases[key])

    def _create_scrollable_page(self, parent: ttk.Frame):
        """Create a scrollable content page."""
        page = ttk.Frame(parent)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(0, weight=1)

        canvas = tk.Canvas(page, highlightthickness=0, bg=GUI_STYLE.palette["bg"])
        content = ttk.Frame(canvas, padding=(2, 2, 12, 8))
        content.columnconfigure(0, weight=1)

        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_configure(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_resize(event):
            canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", _on_configure)
        canvas.bind("<Configure>", _on_canvas_resize)

        canvas.grid(row=0, column=0, sticky=tk.NSEW)
        return page, content, canvas

    def _bind_mousewheel_tree(self, widget: tk.Widget, canvas: tk.Canvas):
        """Bind mouse-wheel scrolling to every widget inside a scroll page."""
        for sequence in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            widget.bind(sequence, lambda event, c=canvas: self._on_mousewheel(event, c), add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_tree(child, canvas)

    def _on_mousewheel(self, event, canvas: tk.Canvas):
        delta = 0
        if getattr(event, "num", None) == 4:
            delta = -1
        elif getattr(event, "num", None) == 5:
            delta = 1
        elif getattr(event, "delta", 0):
            if sys.platform == "darwin":
                delta = -1 if event.delta > 0 else 1
            else:
                delta = int(-1 * (event.delta / 120))
        if delta:
            canvas.yview_scroll(delta, "units")
            return "break"
        return None

    def _show_section(self, section: str):
        """Switch visible section page."""
        if section not in self._sections or self._active_section == section:
            return

        for key, page in self._sections.items():
            if key == section:
                page.grid()
            else:
                page.grid_remove()

        self._active_section = section
        for key, button in self._section_buttons.items():
            button.configure(style="SidebarSelected.TButton" if key == section else "Sidebar.TButton")

    def _section_title(self, parent: ttk.Frame, row: int, title: str):
        ttk.Label(parent, text=title, style="Title.TLabel").grid(row=row, column=0, sticky="w", pady=(0, 14))

    def _group(self, parent: ttk.Frame, row: int, title: str) -> ttk.Frame:
        group = Card(parent, padding=(18, 16))
        group.grid(row=row, column=0, sticky=tk.EW, pady=(0, 12))
        group.columnconfigure(1, weight=1)
        ttk.Label(group, text=title, style="Section.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        return group

    def _row(self, group: ttk.Frame, row: int, label: str, widget: tk.Widget, hint: str = ""):
        label_widget = ttk.Label(group, text=label, style="Surface.TLabel", wraplength=190, justify=tk.LEFT)
        label_widget.grid(row=row, column=0, sticky=tk.NW, padx=(0, 18), pady=(6, 6))
        widget.grid(row=row, column=1, sticky=tk.EW, pady=(4, 4))
        if hint:
            ttk.Label(group, text=hint, style="Muted.TLabel", wraplength=420, justify=tk.LEFT).grid(
                row=row + 1, column=1, sticky=tk.EW, pady=(0, 6)
            )

    def _check_row(self, group: ttk.Frame, row: int, variable: tk.BooleanVar, text: str, state=tk.NORMAL):
        check = ttk.Checkbutton(group, variable=variable, text=text, state=state)
        check.grid(row=row, column=1, sticky=tk.W, pady=(4, 4))
        return check

    def _entry(self, parent: ttk.Frame, variable: tk.Variable) -> ttk.Entry:
        return ttk.Entry(parent, textvariable=variable, style="Form.TEntry")

    def _combo(self, parent: ttk.Frame, variable: tk.StringVar, values: list[str], state: str = "readonly") -> ttk.Combobox:
        return ttk.Combobox(parent, textvariable=variable, values=values, state=state, style="Form.TCombobox")

    def _build_basic_section(self, frame: ttk.Frame):
        row = 0
        self._section_title(frame, row, self.st.lan().SECTION_BASIC)

        row += 1
        browser_group = self._group(frame, row, self.st.lan().BROWSER)
        self.auto_launch_var = tk.BooleanVar(value=self.st.auto_launch_browser)
        self._check_row(browser_group, 1, self.auto_launch_var, self.st.lan().AUTO_LAUNCH_BROWSER)

        options = ["960 x 540", "1280 x 720", "1600 x 900", "1920 x 1080", "2560 x 1440", "3840 x 2160"]
        setting_size = f"{self.st.browser_width} x {self.st.browser_height}"
        self.client_size_var = tk.StringVar(value=setting_size)
        self._row(
            browser_group,
            2,
            self.st.lan().CLIENT_SIZE,
            self._combo(browser_group, self.client_size_var, options),
        )

        self.ms_url_var = tk.StringVar(value=self.st.ms_url)
        self._row(browser_group, 3, self.st.lan().MAJSOUL_URL, self._entry(browser_group, self.ms_url_var))

        self.enable_extension_var = tk.BooleanVar(value=self.st.enable_chrome_ext)
        self._check_row(browser_group, 4, self.enable_extension_var, self.st.lan().ENABLE_CHROME_EXT)

        row += 1
        interface_group = self._group(frame, row, self.st.lan().LANGUAGE)
        options = [v.LANGUAGE_NAME for v in LAN_OPTIONS.values()]
        self.language_var = tk.StringVar(value=LAN_OPTIONS[self.st.language].LANGUAGE_NAME)
        self._row(
            interface_group,
            1,
            self.st.lan().LANGUAGE,
            self._combo(interface_group, self.language_var, options),
        )

    def _build_model_section(self, frame: ttk.Frame):
        row = 0
        self._section_title(frame, row, self.st.lan().SECTION_MODEL)
        model_files = [""] + list_children(str(utils.sub_folder(Folder.MODEL)))

        row += 1
        engine_group = self._group(frame, row, self.st.lan().MODEL_TYPE)
        self.model_type_var = tk.StringVar(value=self.st.model_type)
        self._row(
            engine_group,
            1,
            self.st.lan().MODEL_TYPE,
            self._combo(engine_group, self.model_type_var, MODEL_TYPE_STRINGS),
        )

        self.model_file_var = tk.StringVar(value=self.st.model_file)
        self._row(
            engine_group,
            2,
            self.st.lan().AI_MODEL_FILE,
            self._combo(engine_group, self.model_file_var, model_files),
        )

        self.model_file_3p_var = tk.StringVar(value=self.st.model_file_3p)
        self._row(
            engine_group,
            3,
            self.st.lan().AI_MODEL_FILE_3P,
            self._combo(engine_group, self.model_file_3p_var, model_files),
        )

        row += 1
        akagi_group = self._group(frame, row, "AkagiOT")
        self.akagiot_url_var = tk.StringVar(value=self.st.akagi_ot_url)
        self._row(akagi_group, 1, self.st.lan().AKAGI_OT_URL, self._entry(akagi_group, self.akagiot_url_var))
        self.akagiot_apikey_var = tk.StringVar(value=self.st.akagi_ot_apikey)
        self._row(
            akagi_group,
            2,
            self.st.lan().AKAGI_OT_APIKEY,
            self._entry(akagi_group, self.akagiot_apikey_var),
        )

        row += 1
        mjapi_group = self._group(frame, row, "MJAPI")
        self.mjapi_url_var = tk.StringVar(value=self.st.mjapi_url)
        self._row(mjapi_group, 1, self.st.lan().MJAPI_URL, self._entry(mjapi_group, self.mjapi_url_var))
        self.mjapi_user_var = tk.StringVar(value=self.st.mjapi_user)
        self._row(mjapi_group, 2, self.st.lan().MJAPI_USER, self._entry(mjapi_group, self.mjapi_user_var))
        self.mjapi_secret_var = tk.StringVar(value=self.st.mjapi_secret)
        self._row(
            mjapi_group,
            3,
            self.st.lan().MJAPI_SECRET,
            self._entry(mjapi_group, self.mjapi_secret_var),
        )
        self.mjapi_model_select_var = tk.StringVar(value=self.st.mjapi_model_select)
        self._row(
            mjapi_group,
            4,
            self.st.lan().MJAPI_MODEL_SELECT,
            self._combo(mjapi_group, self.mjapi_model_select_var, self.st.mjapi_models),
            self.st.lan().LOGIN_TO_REFRESH,
        )

    def _build_automation_section(self, frame: ttk.Frame):
        row = 0
        self._section_title(frame, row, self.st.lan().SECTION_AUTOMATION)

        preset_labels = self._preset_label_map()
        self.ai_style_preset_var = tk.StringVar(
            value=preset_labels[
                self._detect_preset_code(
                    self.st.ai_randomize_choice,
                    self.st.ai_randomize_top_n,
                    self.st.ai_near_tie_prefer_low,
                )
            ]
        )

        row += 1
        strategy_group = self._group(frame, row, self.st.lan().AI_STYLE_PRESET)
        self.preset_combo = self._combo(strategy_group, self.ai_style_preset_var, list(preset_labels.values()))
        self._row(strategy_group, 1, self.st.lan().AI_STYLE_PRESET, self.preset_combo)
        self.preset_combo.bind("<<ComboboxSelected>>", self._on_preset_changed)

        self.btn_toggle_adv = ttk.Button(
            strategy_group,
            text=self.st.lan().SHOW_ADVANCED,
            command=self._toggle_automation_advanced,
        )
        self.btn_toggle_adv.grid(row=2, column=1, sticky="w", pady=(4, 8))

        self.automation_adv_frame = ttk.Frame(strategy_group, style="Surface.TFrame")
        self.automation_adv_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, pady=(2, 0))
        self.automation_adv_frame.columnconfigure(1, weight=1)
        self.automation_adv_frame.grid_remove()

        self.randomized_choice_var = tk.StringVar(value=str(self.st.ai_randomize_choice))
        self._row(
            self.automation_adv_frame,
            0,
            self.st.lan().RANDOM_CHOICE,
            self._combo(self.automation_adv_frame, self.randomized_choice_var, [str(i) for i in range(6)]),
        )

        self.randomize_top_n_var = tk.StringVar(value=str(self.st.ai_randomize_top_n))
        self._row(
            self.automation_adv_frame,
            1,
            self.st.lan().AI_RANDOMIZE_TOP_N,
            self._combo(self.automation_adv_frame, self.randomize_top_n_var, ["3", "4", "5", "6"]),
        )

        self.near_tie_prefer_low_var = tk.BooleanVar(value=self.st.ai_near_tie_prefer_low)
        self._check_row(
            self.automation_adv_frame,
            2,
            self.near_tie_prefer_low_var,
            self.st.lan().AI_NEAR_TIE_PREFER_LOW,
        )

        self.randomized_choice_var.trace_add("write", self._on_strategy_values_changed)
        self.randomize_top_n_var.trace_add("write", self._on_strategy_values_changed)
        self.near_tie_prefer_low_var.trace_add("write", self._on_strategy_values_changed)

        row += 1
        behavior_group = self._group(frame, row, self.st.lan().AUTO_PLAY_SETTINGS)
        self.random_move_var = tk.BooleanVar(value=self.st.auto_random_move)
        self._check_row(behavior_group, 1, self.random_move_var, self.st.lan().MOUSE_RANDOM_MOVE)
        self.auto_idle_move_var = tk.BooleanVar(value=self.st.auto_idle_move)
        self._check_row(behavior_group, 2, self.auto_idle_move_var, self.st.lan().AUTO_IDLE_MOVE)
        self.auto_drag_dahai_var = tk.BooleanVar(value=self.st.auto_dahai_drag)
        self._check_row(behavior_group, 3, self.auto_drag_dahai_var, self.st.lan().DRAG_DAHAI)
        self.auto_profile_peek_var = tk.BooleanVar(value=self.st.auto_profile_peek)
        self._check_row(behavior_group, 4, self.auto_profile_peek_var, self.st.lan().AUTO_PROFILE_PEEK)

        row += 1
        emoji_group = self._group(frame, row, self.st.lan().REPLY_EMOJI_CHANCE)
        emoji_options = [f"{i * 10}%" for i in range(11)]
        emoji_options[0] = "0% (off)"
        self.reply_emoji_var = tk.StringVar(value=f"{int(self.st.auto_reply_emoji_rate * 100)}%")
        self._row(
            emoji_group,
            1,
            self.st.lan().REPLY_EMOJI_CHANCE,
            self._combo(emoji_group, self.reply_emoji_var, emoji_options),
        )
        self.auto_emoji_before_hu_var = tk.BooleanVar(value=self.st.auto_emoji_before_hu)
        self._check_row(emoji_group, 2, self.auto_emoji_before_hu_var, self.st.lan().AUTO_EMOJI_BEFORE_HU)
        self.auto_emoji_on_chi_robbed_var = tk.BooleanVar(value=self.st.auto_emoji_on_chi_robbed)
        self._check_row(
            emoji_group,
            3,
            self.auto_emoji_on_chi_robbed_var,
            self.st.lan().AUTO_EMOJI_ON_CHI_ROBBED,
        )

        row += 1
        timing_group = self._group(frame, row, self.st.lan().RANDOM_DELAY_RANGE)
        delay_frame = ttk.Frame(timing_group, style="Surface.TFrame")
        delay_frame.columnconfigure(0, weight=1)
        delay_frame.columnconfigure(1, weight=1)
        self.delay_random_lower_var = tk.DoubleVar(value=self.st.delay_random_lower)
        self.delay_random_upper_var = tk.DoubleVar(value=self.st.delay_random_upper)
        self._entry(delay_frame, self.delay_random_lower_var).grid(
            row=0, column=0, sticky=tk.EW, padx=(0, 8)
        )
        self._entry(delay_frame, self.delay_random_upper_var).grid(row=0, column=1, sticky=tk.EW)
        self._row(timing_group, 1, self.st.lan().RANDOM_DELAY_RANGE, delay_frame)

    def _build_advanced_section(self, frame: ttk.Frame):
        row = 0
        self._section_title(frame, row, self.st.lan().SECTION_ADVANCED)

        row += 1
        network_group = self._group(frame, row, self.st.lan().MITM_SERVICE)
        self.mitm_port_var = tk.StringVar(value=self.st.mitm_port)
        self._row(network_group, 1, self.st.lan().MITM_PORT, self._entry(network_group, self.mitm_port_var))

        self.upstream_proxy_var = tk.StringVar(value=self.st.upstream_proxy)
        self._row(
            network_group,
            2,
            self.st.lan().UPSTREAM_PROXY,
            self._entry(network_group, self.upstream_proxy_var),
        )

        self.proxy_inject_var = tk.BooleanVar(value=self.st.enable_proxinject)
        state = tk.NORMAL if utils.can_proxinject() else tk.DISABLED
        self.check_proxy_inject = self._check_row(
            network_group,
            3,
            self.proxy_inject_var,
            self.st.lan().CLIENT_INJECT_PROXY,
            state=state,
        )
        if not utils.can_proxinject():
            self.proxy_inject_var.set(False)
            add_hover_text(
                self.check_proxy_inject,
                getattr(self.st.lan(), "PROXY_INJECT_UNSUPPORTED", "Only available on Windows"),
            )

        ttk.Label(network_group, text=self.st.lan().SETTINGS_TIPS, style="Muted.TLabel", wraplength=520).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky=tk.EW,
            pady=(8, 0),
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
            messagebox.showerror(self.st.lan().SETTINGS, self.st.lan().MITM_PORT_ERROR_PROMPT, parent=self)
            return
        if not self.st.valid_mitm_port(mitm_port_new):
            messagebox.showerror(self.st.lan().SETTINGS, self.st.lan().MITM_PORT_ERROR_PROMPT, parent=self)
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
            messagebox.showerror(self.st.lan().SETTINGS, self.st.lan().RANDOM_DELAY_RANGE, parent=self)
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
        self.st.auto_profile_peek = self.auto_profile_peek_var.get()
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
            messagebox.showinfo(self.st.lan().SETTINGS, self.st.lan().SETTINGS_TIPS, parent=self)
        self.destroy()

    def _on_cancel(self):
        LOGGER.info("Closing settings window without saving")
        self.exit_save = False
        self.destroy()
