"""
Ein GUI-Tool zur Verwaltung von Python-Paketen mit Pip, das eine grafische
Oberfläche für die Installation, Deinstallation, Aktualisierung und Suche von
Paketen bietet.
"""
# pylint: disable=invalid-name, too-many-lines, wrong-import-position
# --- Versionierung ---
# Diese Nummer wird bei jeder Code-Änderung manuell erhöht.
__version__ = 3

# --- Bootstrap: Abhängigkeiten prüfen und installieren ---
import subprocess
import sys
import importlib.metadata

def check_and_install_dependencies():
    """Check if all required packages are installed and install them if not."""
    REQUIRED_PACKAGES = ["requests", "Pillow", "packaging", "beautifulsoup4"]
    missing_packages = []

    for package in REQUIRED_PACKAGES:
        try:
            importlib.metadata.distribution(package)
        except importlib.metadata.PackageNotFoundError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
        except subprocess.CalledProcessError as e:
            print(f"Error installing packages: {e}")
            print(f"Please install the packages manually with: pip install {' '.join(missing_packages)}")

check_and_install_dependencies()

# --- Pfad-Konfiguration für lokale Module ---
# Fügt das Projekt-Stammverzeichnis zum Python-Pfad hinzu, um Import-Fehler
# wie "Unable to import 'utils.helpers'" in IDEs und bei der Ausführung zu vermeiden.
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Standard-Bibliothek ---
import datetime
import json
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox, filedialog

# --- Drittanbieter-Bibliotheken ---
import requests
import packaging.version
from PIL import Image, ImageTk
from packaging import utils as packaging_utils

# --- Eigene Module ---
from logic.package_manager import PackageManager
from logic.pypi_api import PyPiAPI
from gui.tab1_widgets import create_tab1_widgets
from gui.tab2_widgets import create_tab2_widgets
from utils.config import ConfigManager
from utils.helpers import resource_path, is_admin, get_package_path, get_current_system_tags_set

# -----------------------------------------------------------------------------
def load_translations():
    """
    Lädt alle Sprach-JSON-Dateien aus dem 'lang'-Verzeichnis.
    """
    translations = {}
    # Zuerst im normalen Pfad suchen
    lang_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'lang'
        )

    # Fallback für PyInstaller
    if not os.path.isdir(lang_dir):
        lang_dir = resource_path('lang')

    if os.path.isdir(lang_dir):
        for filename in os.listdir(lang_dir):
            if filename.endswith('.json'):
                lang_code = filename[:-5]
                filepath = os.path.join(lang_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        translations[lang_code] = json.load(f)
                except (json.JSONDecodeError, IOError):
                    # Im Fehlerfall eine leere Übersetzung bereitstellen
                    translations[lang_code] = {}
    # Fallback, falls keine Dateien geladen werden konnten
    if 'de' not in translations:
        translations['de'] = {"title": "Pip Paket-Manager (Fehler)",
                              "select_python_title": "Python-Version auswählen",
                              "label_select_python": "Wählen Sie eine Python-Version:",
                              "btn_ok": "OK",
                              "btn_cancel": "Abbrechen"}
    if 'en' not in translations:
        translations['en'] = {"title": "Pip Package Manager (Error)",
                              "select_python_title": "Select Python Version",
                              "label_select_python": "Select a Python version:",
                              "btn_ok": "OK",
                              "btn_cancel": "Cancel"}

    return translations

# --- Globale Variablen ---
LANG_TEXTS = load_translations()


# -----------------------------------------------------------------------------
# --- HAUPTANWENDUNGSKLASSE ---
# -----------------------------------------------------------------------------

class PipPackageManager:
    """Kapselt die gesamte Logik und die GUI des Pip Paket-Managers."""

    def __init__(self, root_window):
        """
        Initialisiert die Anwendung und die GUI des Pip Paket-Managers.

        Parameters
        ----------
        root_window : tkinter.Tk
            Das Hauptfenster der Anwendung.
        """
        self.root = root_window
        self.root.title("Pip Paket-Manager")
        self.root.geometry("950x650")
        try:
            self.root.iconbitmap(resource_path('PyPi-128px.ico'))
        except tk.TclError:
            self.log_message(self.t("warning_icon_not_found"))
        self.pypi_api = PyPiAPI(self.log_message)

        self.config_manager = ConfigManager(self.log_message)
        # --- Anwendungszustand (ersetzt globale Variablen) ---
        self.version = __version__
        self.current_lang = "de"
        self.remember_language_var = tk.BooleanVar(value=False)
        self.storage_method_var = tk.StringVar(value="config")
        self.log_records = []
        self.pypi_index_cache = []
        self.pypi_package_releases_cache = {}
        self.installed_packages_cache = []
        self.pypi_cache_path = self._get_cache_path()
        self.outdated_packages_cache = {}
        self.security_packages_cache = []
        self.security_issues_cache = {}
        self.current_system_tags = get_current_system_tags_set()
        self.current_package_version_details_cache = {}
        self.current_searched_pkg_name = None
        self.new_script_content = None
        self.update_on_exit = False
        self.script_path = os.path.abspath(__file__)
        self.remote_version = None
        self.current_displayed_pkg_name = None
        self.current_pypi_info = None
        self.current_install_time = None
        self.current_missing_deps = None
        self.found_venvs_cache = []
        self.venv_paths = []
        self.selected_python_executable = sys.executable
        self.venv_var = tk.StringVar()
        self._is_programmatic_change = False
        self.current_search_displayed_version = None

        # --- GUI-Elemente ---
        self.notebook = None
        self.venv_selection_label = None
        self.package_listbox = None
        self.info_text = None
        self.py_version_text = None
        self.search_entry_var = tk.StringVar()
        self.search_entry = None
        self.search_results_listbox = None
        self.search_versions_listbox = None
        self.search_info_text = None
        self.status_label = None
        self.progress_label = None
        self.lang_var = tk.StringVar(value="Deutsch")
        self.btn_install_deps = None
        self.btn_uninstall = None
        self.btn_reinstall = None
        self.btn_refresh = None
        self.btn_show_log = None
        self.btn_security_check = None
        self.btn_install_local = None
        self.btn_autoremove = None
        self.btn_install_selected = None
        self.btn_download_version = None
        self.progress_bar_tab1 = None
        self.progress_bar_tab2 = None
        self.progress_frame_tab1 = None
        self.progress_frame_tab2 = None
        self.frame_left = None
        self.frame_right = None
        self.info_frame = None
        self.py_version_frame = None
        self.btn_frame = None
        self.lang_label = None
        self.lang_combo = None
        self.tab3_remember_checkbox = None
        self.tab3_remember_label = None
        self.tab3_storage_registry_radio = None
        self.tab3_storage_config_radio = None
        self.tab3_storage_registry_label = None
        self.tab3_delete_registry_btn = None
        self.tab3_delete_pypi_index_btn = None
        self.tab3_delete_pypi_index_label = None
        self.tab3_paths_frame = None
        self.tab3_find_venvs_btn = None
        self.venv_selection_frame = None
        self.venv_combobox = None
        self.btn_update = None
        self.venv_selection_label = None
        self._options_paths_after_id = None
        self._options_path_entries = []

        # --- Initialisierung ---
        self.log_message(self.t("log_app_started"))
        self._create_widgets()
        self._load_startup_settings()
        self._start_background_tasks()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._schedule_periodic_update(self._update_paths_listbox, 5000)

    def t(self, key): # pylint: disable=invalid-name
        """Gibt den übersetzten Text für einen Schlüssel zurück."""
        return LANG_TEXTS[self.current_lang].get(key, f"<{key}>")

    def _create_widgets(self):
        """Erstellt alle GUI-Elemente der Anwendung."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tab1 = tk.Frame(self.notebook, relief=tk.RAISED, borderwidth=2)
        tab2 = tk.Frame(self.notebook, relief=tk.RAISED, borderwidth=2)
        tab3 = tk.Frame(self.notebook, relief=tk.RAISED, borderwidth=2)
        self.notebook.add(tab1, text=self.t("tab_manage"))
        self.notebook.add(tab2, text=self.t("tab_search"))
        self.notebook.add(tab3, text=self.t("tab_options"))

        create_tab1_widgets(self, tab1)
        create_tab2_widgets(self, tab2)
        self._create_tab3_widgets(tab3)
        self._create_statusbar()

    def _get_cache_path(self):
        """Gibt den Pfad zur Cache-Datei im Benutzerverzeichnis zurück."""
        app_dir = os.path.join(os.path.expanduser('~'), '.pip_paket_manager')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        return os.path.join(app_dir, 'pypi_index_cache.json')

    def create_middle_column(self, parent):
        """Erstellt die mittlere Spalte mit Aktionen und Sprachauswahl."""
        # Hauptcontainer für die mittlere Spalte
        main_middle_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=2)

        # Container für den oberen Teil (venv- und Sprachauswahl, Buttons, Logo)
        top_content_frame = tk.Frame(main_middle_frame)
        top_content_frame.grid(row=0, column=0, sticky="n", padx=5, pady=10)

        # Frame für venv-Auswahl
        self.venv_selection_frame = tk.Frame(top_content_frame)
        self.venv_selection_frame.pack(pady=(10, 5), fill=tk.X)
        self.venv_selection_label = ttk.Label(self.venv_selection_frame,
                                              text=self.t("venv_selection_label"))
        self.venv_selection_label.pack(anchor="w", padx=5, pady=(0, 2))
        self.venv_combobox = ttk.Combobox(
            self.venv_selection_frame, textvariable=self.venv_var, state="readonly", width=20)
        self.venv_combobox.pack(fill=tk.X, expand=True, padx=5)
        self.venv_combobox.bind("<<ComboboxSelected>>", self.on_venv_selected)

        # Frame für Sprachauswahl
        lang_frame = tk.Frame(top_content_frame)
        lang_frame.pack(pady=(0, 10), fill=tk.X)
        self.lang_label = ttk.Label(lang_frame, text=self.t("lang_label"))
        self.lang_label.pack(side=tk.LEFT, padx=(5, 5))
        code_to_display, _ = self._get_language_maps()
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            state="readonly",
            values=list(code_to_display.values()),
            width=20)
        self.lang_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        self.btn_frame = tk.LabelFrame(top_content_frame,
                                       text=self.t("actions_frame_title"),
                                       relief=tk.RAISED, borderwidth=2)
        self.btn_frame.pack(pady=10, padx=5)

        self.btn_uninstall = ttk.Button(self.btn_frame,
                                        text=self.t("btn_uninstall"),
                                        width=25,
                                        command=self.batch_uninstall_packages)
        self.btn_uninstall.pack(fill=tk.X, pady=2)
        self.btn_update = ttk.Button(self.btn_frame,
                                     text=self.t("btn_update"),
                                     width=25,
                                     command=self.batch_update_packages)
        self.btn_update.pack(fill=tk.X, pady=2)
        self.btn_reinstall = ttk.Button(
            self.btn_frame, text=self.t("btn_reinstall"), width=25,
            command=self.batch_reinstall_packages
        )
        self.btn_reinstall.pack(fill=tk.X, pady=2)
        self.btn_refresh = ttk.Button(self.btn_frame,
                                      text=self.t("btn_refresh"),
                                      width=25,
                                      command=self.refresh_package_list)
        self.btn_refresh.pack(fill=tk.X, pady=2)
        self.btn_install_deps = ttk.Button(self.btn_frame,
                                           text=self.t("btn_install_deps"),
                                           width=25,
                                           state=tk.DISABLED)
        self.btn_install_deps.pack(fill=tk.X, pady=2)
        self.btn_show_log = ttk.Button(self.btn_frame,
                                       text=self.t("btn_show_log"),
                                       width=25,
                                       command=self.show_log_window)
        self.btn_show_log.pack(fill=tk.X, pady=2)
        self.btn_security_check = ttk.Button(self.btn_frame,
                                             text=self.t("security_check_title"),
                                             width=25,
                                             command=self.check_security_vulnerabilities)
        self.btn_security_check.pack(fill=tk.X, pady=2)
        self.btn_install_local = ttk.Button(self.btn_frame,
                                            text=self.t("btn_install_local"),
                                            width=25,
                                            command=self.install_local_package)
        self.btn_install_local.pack(fill=tk.X, pady=2)
        self.btn_autoremove = ttk.Button(self.btn_frame,
                                         text=self.t("btn_autoremove"),
                                         width=25,
                                         command=self.autoremove_packages)
        self.btn_autoremove.pack(fill=tk.X, pady=2)

        try:
            img = Image.open(resource_path('PyPi-128px.ico')).resize(
                (128, 128), Image.Resampling.LANCZOS
                )
            self.root.icon_image = ImageTk.PhotoImage(img)
            icon_label = ttk.Label(self.btn_frame, image=self.root.icon_image, cursor="hand2")
            icon_label.pack(side=tk.BOTTOM, pady=10)
            icon_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://pypi.org/"))
        except (FileNotFoundError, tk.TclError):
            pass # Icon ist optional

        return main_middle_frame

    def _create_venv_action_widgets(self, parent_frame):
        """Erstellt die Widgets für die venv-Suche und -Auswahl."""
        venv_action_frame = tk.Frame(parent_frame)
        venv_action_frame.grid(row=self.tab3_row_counter, column=0, sticky="ew", pady=5, padx=5)
        venv_action_frame.columnconfigure(1, weight=1)

        self.tab3_find_venvs_btn = ttk.Button(venv_action_frame, command=self.start_venv_search,
                                              text=self.t("btn_find_venvs"))
        self.tab3_find_venvs_btn.grid(row=0, column=0, sticky="w")
        self.tab3_row_counter += 1

        self.tab3_venv_search_status_label = ttk.Label(parent_frame, text="",
                                                       font=("Segoe UI", 8))
        self.tab3_venv_search_status_label.grid(
            row=self.tab3_row_counter, column=0, sticky="w", pady=(0, 5), padx=5)
        self.tab3_row_counter += 1

    def _create_tab3_widgets(self, parent_tab):
        """Erstellt die Widgets für den 'Optionen'-Tab."""
        parent_tab.columnconfigure(0, weight=1)
        parent_tab.rowconfigure(0, weight=0)
        parent_tab.rowconfigure(1, weight=1)

        main_frame = tk.Frame(parent_tab, relief=tk.RAISED, borderwidth=2)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        main_frame.columnconfigure(0, weight=1)

        storage_frame = tk.Frame(main_frame)
        storage_frame.grid(row=0, column=0, sticky="w", pady=(2, 5), padx=5)
        storage_frame.columnconfigure(0, weight=0)
        storage_frame.columnconfigure(1, weight=0)
        storage_frame.columnconfigure(2, weight=0)
        storage_frame.columnconfigure(3, weight=0)

        self.tab3_storage_registry_radio = ttk.Radiobutton(storage_frame,
                                                           variable=self.storage_method_var,
                                                           value="registry",
                                                           command=self._on_storage_method_changed,
                                                           state=tk.DISABLED)
        self.tab3_storage_registry_label = ttk.Label(storage_frame, text="")

        self.tab3_storage_config_radio = ttk.Radiobutton(storage_frame,
                                                         variable=self.storage_method_var,
                                                         value="config",
                                                         command=self._on_storage_method_changed,
                                                         state=tk.DISABLED)

        self.tab3_row_counter = 1
        if sys.platform == "win32":
            self.tab3_storage_registry_radio.grid(row=0, column=0, sticky="w", padx=5)
            self.tab3_storage_registry_label.grid(row=0, column=1, sticky="w", padx=5)

            self.tab3_storage_config_radio.grid(row=0, column=2, sticky="w", padx=5)
            # Das Label für Config wird hier nicht benötigt, da es dasselbe wie für Registry ist.

            self.tab3_delete_registry_btn = ttk.Button(main_frame,
                                                       command=self._delete_registry_entry,
                                                       state=tk.DISABLED)
            self.tab3_delete_registry_btn.grid(
                row=self.tab3_row_counter, column=0, sticky="w", pady=5, padx=5
                )
            self.tab3_row_counter += 1

            self.tab3_delete_pypi_index_btn = ttk.Button(main_frame,
                                                         command=self._delete_pypi_index,
                                                         state=tk.NORMAL)
            self.tab3_delete_pypi_index_btn.grid(
                row=self.tab3_row_counter, column=0, sticky="w", pady=5, padx=5
                )
            self.tab3_row_counter += 1

            self._create_venv_action_widgets(main_frame)
        else:
            self.tab3_storage_config_radio.grid(row=0, column=0, sticky="w", padx=5)
            # Das Label für Config wird hier nicht benötigt.
            self.tab3_delete_registry_btn = None

            self._create_venv_action_widgets(main_frame)

        # Frame für wichtige Pfade
        self.tab3_paths_frame = tk.LabelFrame(main_frame,
                                              relief=tk.RAISED, borderwidth=2)
        self.tab3_paths_frame.grid(
            row=self.tab3_row_counter, column=0, sticky="ew", pady=(10, 5), padx=5
            )
        self.tab3_paths_listbox = tk.Listbox(self.tab3_paths_frame,
                                             height=3,
                                             font=("Courier New", 9))
        self.tab3_paths_listbox.pack(fill=tk.X, expand=True, padx=5, pady=5)

    def _create_statusbar(self):
        """Erstellt die Statusleiste am unteren Rand des Fensters."""
        status_frame = tk.Frame(self.root, relief=tk.RAISED, borderwidth=2)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=2)
        self.status_label = ttk.Label(status_frame, text=self.t("status_loading"),
                                      anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")
        self.progress_label = ttk.Label(status_frame, text="", anchor="e")
        self.progress_label.grid(row=0, column=1, sticky="ew")

    def _start_background_tasks(self):
        """Startet die initialen Ladevorgänge in Hintergrundthreads."""
        threading.Thread(target=self.load_packages, daemon=True).start()
        threading.Thread(target=self.load_python_versions, daemon=True).start()
        self.root.after(
            2000, lambda: threading.Thread(target=self.load_pypi_index, daemon=True).start()
            )
        self.root.after(
            3000, lambda: threading.Thread(target=self.check_for_updates, daemon=True).start()
            )

    def _enable_storage_method_radios(self):
        """Aktiviert die Radio buttons für die Speichermethode."""
        if self.tab3_storage_config_radio:
            self.tab3_storage_config_radio.config(state=tk.NORMAL)
        if self.tab3_storage_registry_radio:
            self.tab3_storage_registry_radio.config(state=tk.NORMAL)

    def _load_startup_settings(self):
        """Lädt alle Einstellungen beim Start über den ConfigManager."""
        self._is_programmatic_change = True
        settings = self.config_manager.load_settings()

        self.current_lang = settings.get("language", "de")
        self.remember_language_var.set(settings.get("remember_language", False))
        self.storage_method_var.set(settings.get("storage_method", "config"))
        self.venv_paths = settings.get("venvs", [])

        self._update_all_labels()
        self._update_venv_combobox_values() # <-- HIER WIEDER EINGEFÜGT
        self.root.after(10, lambda: setattr(self, '_is_programmatic_change', False))

    def _get_language_maps(self):
        """Erstellt dynamisch Mapping-Wörterbücher für Sprachen."""
        code_to_display = {code: data.get("language_name", code) for code,
                           data in LANG_TEXTS.items()}
        display_to_code = {name: code for code, name in code_to_display.items()}
        return code_to_display, display_to_code

    def change_language(self, event=None):
        """Ändert die Sprache und speichert sie, falls 'merken' aktiv ist.""" # pylint: disable=unused-argument
        _, display_to_code = self._get_language_maps()
        lang_code = display_to_code.get(self.lang_var.get(), "de")
        self.current_lang = lang_code

        self._update_all_labels()

        # Speichere nur, wenn die Checkbox aktiv ist.
        if not self._is_programmatic_change:
            self._save_settings()

    def _update_all_labels(self):
        """Aktualisiert alle Texte in der GUI."""
        try:
            self.root.title(self.t("title"))
            self.notebook.tab(0, text=self.t("tab_manage"))
            self.notebook.tab(1, text=self.t("tab_search"))
            self.notebook.tab(2, text=self.t("tab_options"))

            # Combobox-Werte und Auswahl aktualisieren
            code_to_display, _ = self._get_language_maps()
            self.lang_combo['values'] = list(code_to_display.values())
            self.lang_var.set(code_to_display.get(self.current_lang, "Deutsch"))

            self.lang_label.config(text=self.t("lang_label"))
            self.frame_left.config(text=self.t("frame_left_title"))
            self.info_frame.config(text=self.t("frame_right_title"))
            self.py_version_frame.config(text=self.t("python_versions_title"))
            self.btn_frame.config(text=self.t("actions_frame_title"))

            self.btn_uninstall.config(text=self.t("btn_uninstall"))
            self.btn_update.config(text=self.t("btn_update"))
            self.btn_reinstall.config(text=self.t("btn_reinstall"))
            self.btn_refresh.config(text=self.t("btn_refresh"))
            self.btn_install_deps.config(text=self.t("btn_install_deps"))
            self.btn_show_log.config(text=self.t("btn_show_log"))
            self.btn_security_check.config(text=self.t("security_check_title"))
            self.btn_install_local.config(text=self.t("btn_install_local"))
            self.btn_autoremove.config(text=self.t("btn_autoremove"))

            self.progress_frame_tab1.config(text=self.t("progress_frame_title"))
            self.progress_frame_tab2.config(text=self.t("progress_frame_title"))

            self.search_bar_frame.config(text=self.t("search_label"))
            self.search_results_frame.config(text=self.t("search_results_title"))
            self.search_button.config(text=self.t("search_button"))

            self.search_versions_frame.config(text=self.t("search_versions_title"))
            self.search_info_frame.config(text=self.t("search_info_title"))
            self.install_frame.config(text=self.t("install_frame_title"))

            self.btn_install_selected.config(
                text=self.t("btn_install_selected_version")
            )
            self.btn_download_version.config(text=self.t("btn_download_version"))

            self.status_label.config(text=self.t("status_loading"))

            if self.tab3_remember_label:
                self.tab3_remember_label.config(text=self.t("remember_language_label"))
            if self.tab3_storage_registry_label:
                self.tab3_storage_registry_label.config(text=self.t("storage_registry_label"))
            if self.tab3_delete_registry_btn:
                self.tab3_delete_registry_btn.config(text=self.t("delete_registry_btn"))
            if self.tab3_delete_pypi_index_btn:
                self.tab3_delete_pypi_index_btn.config(
                    text=self.t("delete_pypi_index_btn"))
            if self.tab3_paths_frame:
                self.tab3_paths_frame.config(text=self.t("options_paths_title"))
            if self.tab3_find_venvs_btn:
                self.tab3_find_venvs_btn.config(text=self.t("btn_find_venvs"))
            if self.venv_selection_frame:
                self.venv_selection_label.config(text=self.t("venv_selection_label"))

        except (tk.TclError, AttributeError) as e:
            self.log_message(self.t("log_gui_update_error").format(e=e), "ERROR")

    def _on_remember_language_toggled(self):
        """Wird aufgerufen, wenn die 'Sprache merken' Checkbox geändert wird."""
        if self._is_programmatic_change:
            return

        if self.remember_language_var.get():
            self._enable_storage_method_radios()
            # Speichere die aktuelle Einstellung, wenn die Checkbox aktiviert wird
            self._save_settings()
        else:
            if self.tab3_storage_registry_radio:
                self.tab3_storage_registry_radio.config(state=tk.DISABLED)
            if self.tab3_storage_config_radio:
                self.tab3_storage_config_radio.config(state=tk.DISABLED)
            # Lösche alle gespeicherten Einstellungen, wenn die Checkbox deaktiviert wird
            self._save_settings()

    def _on_storage_method_changed(self):
        """Wird aufgerufen, wenn die Speichermethode geändert wird."""
        if self._is_programmatic_change or not self.remember_language_var.get():
            return
        self._save_settings()

    def _save_settings(self):
        """Speichert alle relevanten Einstellungen über den ConfigManager."""
        self.config_manager.save_settings(
            lang_code=self.current_lang,
            remember=self.remember_language_var.get(),
            method=self.storage_method_var.get(),
            venv_paths=self.venv_paths
        )

    def _verify_registry_deletion(self):
        """Überprüft, ob der Registry-Eintrag gelöscht wurde."""
        if sys.platform != "win32":
            return
        try:
            import winreg
            try:
                winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Pip_Package_Manager")
                self.tab3_delete_registry_btn.config(state=tk.NORMAL)
            except OSError:
                self.tab3_delete_registry_btn.config(state=tk.DISABLED)
        except ImportError:
            pass

    def _delete_pypi_index(self):
        """Löscht den Pip Index Cache."""
        def delete_in_thread():
            try:
                cache_path = self._get_cache_path()
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    self.pypi_index_cache = []
                    self.pypi_package_releases_cache = {}
                    self.log_message(self.t("log_pypi_index_deleted"))
            except (IOError, OSError):
                pass

        threading.Thread(target=delete_in_thread, daemon=True).start()

    def _save_venvs_to_config(self):
        """Speichert die aktuelle Liste der venvs in der Konfigurationsdatei."""
        self.config_manager.save_venvs(self.venv_paths)

    # --- Logging und Status ---

    def log_message(self, message, level="INFO"):
        """Fügt eine Nachricht zum In-Memory-Log hinzu."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{timestamp} [{level}] {message}"
        self.log_records.append(full_message)
        if hasattr(self, 'log_window') and self.log_window and self.log_window.winfo_exists():
            self.log_window.log_text_widget.insert(tk.END, full_message + "\n")

    def show_log_window(self):
        """Erstellt und zeigt das Log-Fenster an."""
        self.log_window = getattr(self, 'log_window', None) # Ensure log_window exists or is None
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return
        self.log_window = tk.Toplevel(self.root)
        self.log_window.title(self.t("log_title"))
        self.log_window.geometry("800x500")
        self.log_window.log_text_widget = tk.Text(
            self.log_window, wrap=tk.WORD, font=("Courier New", 9))
        log_scrollbar = ttk.Scrollbar(
            self.log_window,
            orient="vertical",
            command=self.log_window.log_text_widget.yview
        )
        self.log_window.log_text_widget.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_window.log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_window.log_text_widget.bind(
            "<Button-3>", lambda e: self.show_text_context_menu(e, self.log_window.log_text_widget))
        self.log_window.log_text_widget.insert(tk.END, "\n".join(self.log_records) + "\n")
        self.log_window.log_text_widget.see(tk.END)

    def update_status_label(self, text_key, show=True):
        """Aktualisiert das zentrale Status-Label sicher aus jedem Thread.""" # pylint: disable=unused-private-member
        if not self.progress_label:
            return
        try:
            if self.root.winfo_exists():
                if show:
                    message = self.t(text_key)
                    self.log_message(message)
                    self.progress_label.config(text=message)
                else:
                    self.progress_label.config(text="")
        except (tk.TclError, RuntimeError):
            pass

    def start_progress(self):
        """Macht die Fortschrittsbalken sichtbar und startet die Animation."""
        if self.progress_frame_tab1:
            self.progress_frame_tab1.grid()
            self.progress_bar_tab1.start()
        if self.progress_frame_tab2:
            self.progress_frame_tab2.grid()
            self.progress_bar_tab2.start()

    def stop_progress(self):
        """Stoppt die Animation und blendet die Fortschrittsbalken aus."""
        if self.progress_frame_tab1:
            self.progress_bar_tab1.stop()
            self.progress_frame_tab1.grid_remove()
        if self.progress_frame_tab2:
            self.progress_bar_tab2.stop()
            self.progress_frame_tab2.grid_remove()

    # --- Pip- und Daten-Logik ---

    def run_pip_command(self, command_list, on_finish=None, show_progress=True):
        """Führt einen Pip-Befehl in einem separaten Prozess aus."""
        def task():
            if show_progress:
                self.root.after(0, self.start_progress)

            pm = PackageManager(self.selected_python_executable, self.log_message)

            def line_handler(line):
                self.log_message(line, level="PIP")
                if show_progress and self.progress_label:
                    self.root.after(0, lambda l=line: self.progress_label.config(text=l))

            start_msg = self.t("log_pip_command_start").format(
                executable=os.path.basename(pm.python_executable),
                command=' '.join(command_list))
            self.log_message(start_msg)
            if show_progress and self.progress_label:
                self.root.after(0, lambda: self.progress_label.config(text=start_msg))

            return_code = pm.run_command(command_list, line_callback=line_handler)

            end_msg = self.t("log_pip_command_finish").format(code=return_code)
            self.log_message(end_msg, level="STATUS")
            if show_progress and self.progress_label:
                self.root.after(0, lambda: self.progress_label.config(text=end_msg))

            try:
                if on_finish:
                    self.root.after(100, on_finish)
            finally:
                if show_progress:
                    self.root.after(0, self.stop_progress)
        threading.Thread(target=task, daemon=True).start()

    def load_packages(self, on_finish=None):
        """Lädt installierte und veraltete Pakete und aktualisiert die GUI."""
        def do_load():
            self.root.after(0, self.start_progress)
            try:
                self.log_message(self.t("log_loading_packages"))
                self.root.after(
                    0, lambda: self.progress_label.config(text=self.t("status_loading_installed")))
                pm = PackageManager(self.selected_python_executable, self.log_message)
                packages = pm.get_installed()
                self.installed_packages_cache = packages
                self.root.after(0, lambda: self.update_listbox_safely(packages))
                self.root.after(0, lambda: self.update_status_label(None, show=False))

                self.root.after(100, lambda: self.update_status_label("status_checking_updates"))
                self.root.after(
                    100, lambda: self.progress_label.config(text=self.t("status_checking_updates")))
                self.outdated_packages_cache = pm.get_outdated()
                self.load_security_packages_check(pm)

                self.root.after(0, self.colorize_outdated_packages)
                self.root.after(0, lambda: self.update_status_label(None, show=False))
                self.root.after(0, lambda: self.progress_label.config(text=""))
                self.log_message(self.t("log_finished_loading"))
                if on_finish:
                    self.root.after(100, on_finish)
            finally:
                self.root.after(0, self.stop_progress)
        threading.Thread(target=do_load, daemon=True).start()

    # --- Aktionen und Event-Handler ---

    def refresh_package_list(self, on_finish=None):
        """Leert die Paketliste und startet den Ladevorgang neu."""
        self.package_listbox.delete(0, tk.END)
        self.log_message(self.t("log_refreshing"))
        self.load_packages(on_finish=on_finish)

    def uninstall_package(self, pkg_name):
        """Deinstalliert ein Paket."""
        if not pkg_name:
            return
        if not messagebox.askyesno(
            self.t("btn_uninstall"), self.t("confirm_uninstall").format(pkg_name)):
            return

        removable_deps = self.find_removable_packages(pkg_name)
        remove_deps = False
        if removable_deps:
            msg = f"Die folgenden Abhängigkeiten werden nur von '{pkg_name}' benötigt:\n\n"
            msg += "\n".join(removable_deps[:10])
            if len(removable_deps) > 10:
                msg += f"\n{self.t('msg_remove_more_deps').format(len(removable_deps) - 10)}"
            msg += f"\n\n{self.t('msg_remove_deps_ask')}"
            remove_deps = messagebox.askyesno(self.t("dialog_uninstall_dependencies"), msg)
        pkg_path = get_package_path(pkg_name)
        needs_admin = pkg_path.lower().startswith(r"c:\program files")
        if needs_admin and not is_admin():
            self.log_message(self.t("log_admin_required").format(pkg_name, pkg_path))
            messagebox.showinfo(
                self.t("admin_rights_title"),
                self.t("admin_rights_required_msg").format(pkg_name=pkg_name)
            )
            packages_to_remove = [pkg_name]
            if remove_deps:
                packages_to_remove.extend(removable_deps)
            pip_args = (
                f'-m pip uninstall -y {" ".join(packages_to_remove)}')
            subprocess.run(["powershell", "-Command", "Start-Process", sys.executable,
                            "-ArgumentList", f'"{pip_args}"',
                            "-Verb", "runAs", "-Wait"], check=False)
            self.refresh_package_list()
            return

        packages_to_remove = [pkg_name]
        if remove_deps:
            packages_to_remove.extend(removable_deps)
        self.run_pip_command(["uninstall", "-y"] + packages_to_remove, self.refresh_package_list)

    def _handle_conflicts(self, pkg_name, pkg_version, cancel_msg_key):
        """Verarbeitet Abhängigkeitskonflikte. Returns True wenn fortfahren."""
        _can_install, _required_packages, conflicts, cross_conflicts = self.resolve_dependencies(
            pkg_name, pkg_version)
        if not (conflicts or cross_conflicts):
            return True

        proceed, action = self.show_dependency_conflict_dialog(pkg_name, conflicts, cross_conflicts)
        if not proceed:
            self.log_message(self.t(cancel_msg_key).format(pkg_name), "INFO")
            return False

        if action == 'upgrade_deps':
            for pkg, _, required_spec in conflicts:
                cmd = ["install", f"{pkg}{required_spec}" if required_spec else "--upgrade", pkg]
                self.run_pip_command(cmd)
        return True

    def update_package(self, pkg_name):
        """Aktualisiert ein Paket mit Dependency Resolution."""
        if not pkg_name:
            return

        def do_update():
            # Wrapper-Funktion, um nach dem Refresh das Paket wieder auszuwählen
            def reselect_after_refresh():
                """Wird aufgerufen, nachdem die Paketliste neu geladen wurde."""
                try:
                    try:
                        items = self.package_listbox.get(0, tk.END)
                        if pkg_name in items:
                            idx = items.index(pkg_name)
                            self.package_listbox.selection_clear(0, tk.END)
                            self.package_listbox.selection_set(idx)
                            self.package_listbox.see(idx)
                            self.on_package_selection_changed()  # Aktualisiere die Info-Anzeige
                    except (ValueError, tk.TclError):
                        pass  # Paket nicht gefunden oder Fenster geschlossen
                finally:
                    self.root.after(0, self.stop_progress)

            if self._handle_conflicts(pkg_name, None, "log_update_cancelled"):
                self.run_pip_command(["install", "--upgrade", pkg_name],
                lambda: self.refresh_package_list(on_finish=reselect_after_refresh))

        threading.Thread(target=do_update, daemon=True).start()

    def reinstall_package(self, pkg_name):
        """Installiert ein Paket neu mit Dependency Resolution."""
        if not pkg_name:
            return

        def do_reinstall():
            try:
                current_version = importlib.metadata.version(pkg_name)
                self.log_message(self.t("log_starting_reinstall").format(pkg_name, current_version))

                if self._handle_conflicts(
                    pkg_name, current_version, "log_reinstall_cancelled"):
                    cmd = ["install", "--force-reinstall", "--no-deps",
                           f"{pkg_name}=={current_version}"]
                    self.run_pip_command(cmd, self.refresh_package_list)
            except importlib.metadata.PackageNotFoundError:
                self.log_message(
                    self.t("log_could_not_determine_version").format(pkg_name), "WARNING")
                self.run_pip_command(
                    ["install", "--force-reinstall",
                     "--no-deps", pkg_name], self.refresh_package_list)

        threading.Thread(target=do_reinstall, daemon=True).start()

    def get_selected_packages(self):
        """Gibt eine Liste der ausgewählten Pakete zurück."""
        selection = self.package_listbox.curselection()
        return [self.package_listbox.get(i) for i in selection]

    def _batch_operation(self, msg_key, btn_key, action_method):
        """Generische Batch-Operation für mehrere Pakete."""
        packages = self.get_selected_packages()
        if not packages:
            return
        count = len(packages)
        list_preview = ", ".join(packages[:5]) + ("..." if count > 5 else "") # pylint: disable=unused-variable
        msg = self.t(msg_key).format(count=count) + "\n" + list_preview
        if messagebox.askyesno(self.t(btn_key), msg):
            for pkg_name in packages:
                action_method(pkg_name)

    def batch_uninstall_packages(self):
        """Deinstalliert mehrere ausgewählte Pakete."""
        self._batch_operation("batch_uninstall_confirm", "btn_uninstall", self.uninstall_package)

    def batch_update_packages(self):
        """Aktualisiert mehrere ausgewählte Pakete."""
        self._batch_operation("batch_update_confirm", "btn_update", self.update_package)

    def batch_reinstall_packages(self):
        """Installiert mehrere ausgewählte Pakete neu."""
        self._batch_operation("batch_reinstall_confirm", "btn_reinstall", self.reinstall_package)

    def install_local_package(self):
        """Installiert ein lokales Paketfile (.whl oder .tar.gz) mit Dependency Resolution."""
        file_path = filedialog.askopenfilename(
            title=self.t("install_local_title"),
            filetypes=[("Paketdateien", "*.whl *.tar.gz"),
                       ("Alle Dateien", "*.*")]
        )
        if not file_path:
            return
        if not os.path.exists(file_path):
            messagebox.showerror(self.t("error_title"), f"Datei nicht gefunden: {file_path}")
            return

        def do_install_local():
            filename = os.path.basename(file_path)
            pkg_name = None
            version = None

            try:
                if filename.endswith('.whl'):
                    _name, parsed_version, _build, _tags = \
                        packaging_utils.parse_wheel_filename(filename)
                    pkg_name = _name
                    version = str(parsed_version)
                else:
                    parts = filename.split('-')
                    if len(parts) >= 2:
                        pkg_name = parts[0]
                        version = (parts[1].split('.tar.gz')[0] if '.tar.gz'
                                   in filename else parts[1])
            except (packaging_utils.InvalidWheelFilename, IndexError, ValueError):
                pass

            if pkg_name and version:
                _can_install, _required_packages, conflicts, cross_conflicts = self.resolve_dependencies(pkg_name, version)

                if conflicts or cross_conflicts:
                    proceed, action = self.show_dependency_conflict_dialog(
                        pkg_name, conflicts, cross_conflicts)
                    if not proceed:
                        self.log_message(
                            self.t("log_install_file_cancelled").format(filename), "INFO")
                        return

                    if action == 'upgrade_deps':
                        for pkg, _current_ver, required_spec in conflicts:
                            if required_spec:
                                req_string = f"{pkg}{required_spec}"
                                self.run_pip_command(["install", req_string])
                            else:
                                self.run_pip_command(["install", "--upgrade", pkg])

            self.log_message(self.t("log_install_local_file").format(file_path))
            self.run_pip_command(["install", file_path], on_finish=self.refresh_package_list)

        threading.Thread(target=do_install_local, daemon=True).start()

    def install_dependencies(self, deps_to_install):
        """Installiert eine Liste von Abhängigkeiten mit Dependency Resolution."""
        if not deps_to_install:
            return

        def do_install_deps():
            all_conflicts = []
            conflict_details = {}

            self.log_message(
                self.t("log_install_dependencies").format(', '.join(deps_to_install)), "DEBUG")

            for dep_spec in deps_to_install:
                try:
                    from packaging.requirements import Requirement, InvalidRequirement
                    parsed = Requirement(dep_spec)
                    pkg_name = parsed.name

                    _can_install, _required_packages, conflicts, cross_conflicts = self.resolve_dependencies(pkg_name)
                    if conflicts or cross_conflicts:
                        all_conflicts.append((pkg_name, conflicts, cross_conflicts))
                        for pkg, current, required in conflicts:
                            conflict_details[pkg] = (current, required)
                except InvalidRequirement as e:
                    self.log_message(self.t("log_process_dep_error").format(dep_spec, e), "DEBUG")

            if all_conflicts:
                self.log_message(
                    self.t("log_conflicts_detected").format(len(all_conflicts)), "DEBUG")
                msg = self.t("dependency_conflicts_msg") # pylint: disable=unused-variable
                for pkg_name, conflicts in all_conflicts[:5]:
                    msg += f"• {pkg_name}\n"
                if len(all_conflicts) > 5:
                    msg += self.t("dependency_conflicts_and_more").format(len(all_conflicts) - 5)

                proceed = messagebox.askyesno(
                    self.t("dependency_conflicts_title"),
                    msg + "\n\n" + self.t("dependency_conflicts_ask")
                )
                if not proceed:
                    self.log_message(self.t("log_install_deps_cancelled"), "INFO")
                    return

                self.log_message(self.t("log_update_conflicting_deps"))
                for pkg_name in conflict_details:
                    self.run_pip_command(["install", "--upgrade", pkg_name])

            self.log_message(self.t("log_install_deps_pip").format(deps_to_install), "DEBUG")
            self.run_pip_command(
                ["install"] + deps_to_install, on_finish=self.refresh_package_list
            )

        threading.Thread(target=do_install_deps, daemon=True).start()

    def on_package_selection_changed(self, _event=None):
        """Wird aufgerufen, wenn sich die Paketauswahl ändert."""
        self.show_package_info()
        self.update_batch_button_text()

    def update_batch_button_text(self):
        """Aktualisiert die Text der Batch-Operation Buttons basierend auf Mehrfachauswahl."""
        count = len(self.get_selected_packages())
        buttons = [
            (self.btn_uninstall, "btn_uninstall", "btn_batch_uninstall"),
            (self.btn_update, "btn_update", "btn_batch_update"),
            (self.btn_reinstall, "btn_reinstall", "btn_batch_reinstall"),
        ]
        for btn, single_key, batch_key in buttons:
            key = batch_key if count > 1 else single_key
            text = f"{self.t(key)} ({count})" if count > 1 else self.t(key)
            btn.config(text=text)

    def show_package_listbox_context_menu(self, event):
        """Zeigt ein Kontextmenü bei Rechtsklick auf die Paket-Listbox."""
        selection = self.package_listbox.curselection()
        if not selection:
            self.package_listbox.selection_set(self.package_listbox.nearest(event.y))
            selection = self.package_listbox.curselection()

        if not selection:
            return

        pkg_name = self.package_listbox.get(selection[0])

        context_menu = tk.Menu(self.root, tearoff=False)
        context_menu.add_command(
            label=self.t("context_copy"), command=lambda: self.copy_package_name(pkg_name))
        context_menu.add_separator()
        context_menu.add_command(
            label=self.t("context_search"), command=lambda: self.search_package(pkg_name))

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_package_name(self, pkg_name):
        """Kopiert den Paketnamen in die Zwischenablage."""
        self.root.clipboard_clear()
        self.root.clipboard_append(pkg_name)
        self.log_message(self.t("log_copied_to_clipboard").format(pkg_name), "DEBUG")

    def search_package(self, pkg_name):
        """Sucht nach einem Paket und wechselt zum Suchen-Tab."""
        self.search_entry_var.set(pkg_name)
        self.notebook.select(1)
        self.perform_search()
        self.log_message(self.t("log_search_started").format(pkg_name), "DEBUG")

    def show_text_context_menu(self, event, text_widget):
        """Zeigt ein Kontextmenü für ein Text-Widget (Kopieren)."""
        context_menu = tk.Menu(self.root, tearoff=False)

        selected_text = ""
        try:
            selected_text = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass

        if selected_text:
            context_menu.add_command(
                label=self.t("context_copy"), command=lambda: self.copy_text(selected_text))
        else:
            context_menu.add_command(label=self.t("context_copy"), state=tk.DISABLED)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_text(self, text):
        """Kopiert Text in die Zwischenablage."""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message(self.t("log_text_copied"), "DEBUG")

    def show_search_entry_context_menu(self, event):
        """Zeigt ein Kontextmenü für das Suchfeld (Kopieren, Einfügen)."""
        context_menu = tk.Menu(self.root, tearoff=False)

        try:
            selected_text = self.search_entry.selection_get()
            context_menu.add_command(
                label=self.t("context_copy"), command=lambda: self.copy_text(selected_text))
        except tk.TclError:
            context_menu.add_command(label=self.t("context_copy"), state=tk.DISABLED)

        context_menu.add_command(label=self.t("context_paste"), command=self.paste_to_search_entry)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def paste_to_search_entry(self):
        """Fügt Text aus der Zwischenablage in das Suchfeld ein."""
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                current_text = self.search_entry_var.get() # pylint: disable=unused-variable
                insert_pos = self.search_entry.index(tk.INSERT) # pylint: disable=unused-variable
                new_text = (current_text[:insert_pos] +
                            clipboard_content + current_text[insert_pos:])
                self.search_entry_var.set(new_text)
                self.log_message(self.t("log_text_pasted"), "DEBUG")
        except tk.TclError:
            self.log_message(self.t("log_clipboard_access_error"), "WARNING")

    def show_package_info(self, _event=None):
        """Zeigt Informationen zu einem ausgewählten Paket an."""
        selection = self.package_listbox.curselection()
        if not selection:
            return
        if self.progress_label:
            self.progress_label.config(text="")
        pkg_name = self.package_listbox.get(selection[0])
        self.info_text.delete("1.0", tk.END)
        self.log_message(self.t("log_fetching_info").format(pkg_name))
        self.info_text.insert(tk.END, self.t("loading_info").format(pkg_name) + "\n")

        def fetch_and_show():
            """
            Fetches package info and displays it in the GUI.

            Disables the 'Install dependencies' button while fetching the package information.
            If the package has missing dependencies, it enables the button with a command
            to install the dependencies.
            If the package is outdated, updates the progress label with an update message.
            Finally, calls display_formatted_info with the fetched information to display it
            in the GUI.
            """
            self.root.after(
                0, lambda: self.btn_install_deps.config(state=tk.DISABLED, command=None))
            dist = importlib.metadata.distribution(pkg_name)
            info_string = self.get_package_info_string(pkg_name, dist)

            pypi_data = self.pypi_api.get_package_info(pkg_name)
            pypi_info = None
            if pypi_data:
                pypi_info = {'data': pypi_data.get('info', {})}
                if dist.version and dist.version in pypi_data.get("releases", {}):
                    release_data = pypi_data["releases"][dist.version]
                    if release_data:
                        pypi_info["yanked"] = release_data[0].get(
                            "yanked", False
                        )
                        pypi_info["yanked_reason"] = release_data[0].get(
                            "yanked_reason", "N/A"
                        )

            install_time = self.get_install_time(pkg_name)
            missing_deps = self.get_missing_deps(dist)

            if missing_deps:
                def on_install_deps():
                    self.install_dependencies(missing_deps)

                self.root.after(0, lambda: self.btn_install_deps.config(
                    state=tk.NORMAL,
                    command=on_install_deps
                ))

            if pkg_name in self.outdated_packages_cache:
                update_info = self.outdated_packages_cache[pkg_name]
                update_text = self.t("update_available").format(
                    update_info['current'], update_info['latest']
                )
                if self.progress_label:
                    self.root.after(0, lambda: self.progress_label.config(text=update_text))

            self.root.after(
                0, lambda: self.display_formatted_info(info_string, pypi_info, install_time, missing_deps, pkg_name)
            )
        threading.Thread(target=fetch_and_show, daemon=True).start()

    def get_package_info_string(self, pkg_name, dist):
        """Erstellt den Info-String für ein Paket."""
        metadata = dist.metadata

        # --- Robuste Extraktion der Metadaten ---
        # Homepage: Prüft zuerst Project-URL (Homepage, dann Source), dann Home-page
        homepage = "N/A"
        project_urls = metadata.get_all('Project-URL') or []

        for url_entry in project_urls:
            if url_entry.lower().startswith("homepage,"):
                homepage = url_entry.split(',')[1].strip()
                break
        # Priorität 2 (NEU): Suche nach "Source" oder "Source code" als Fallback
        if homepage == "N/A":
            for url_entry in project_urls:
                if (url_entry.lower().startswith("source,") or
                        url_entry.lower().startswith("source code,")):
                    homepage = url_entry.split(',')[1].strip()
                    break
        # Priorität 3: Fallback auf das alte "Home-page"-Feld
        if homepage == "N/A":
            homepage = metadata.get('Home-page', 'N/A')

        # Author: Prüft zuerst Author-email, dann Author
        author = metadata.get('Author-email') or metadata.get('Author', 'N/A')

        # KORREKTUR: Mehrstufige, robuste Lizenz-Extraktion
        license_info = "N/A"
        # Priorität 1 (NEU): Das präzise 'License-Expression'-Feld.
        license_expression = metadata.get(
            'License-Expression'
        )
        if license_expression:
            license_info = license_expression
        else:
            # Priorität 2 (NEU): Lese die erste Zeile aus der Lizenzdatei.
            license_files = getattr(dist, 'license_files', [])
            if license_files:
                try:
                    license_text = dist.read_text(license_files[0])
                    # Nimm die erste Zeile, aber nur wenn sie nicht Ã¼bermÃ¤Ãig lang ist
                    # und nicht wie eine URL aussieht.
                    if license_text and len(
                        license_text.splitlines()[0]
                        )< 100 and "http" not in license_text.splitlines()[0]:
                        license_info = license_text.splitlines()[0].strip()
                except (FileNotFoundError, OSError, IndexError):
                    pass  # Wenn das Lesen fehlschlägt, gehen wir zum nächsten Fallback.
        if license_info == "N/A":
            # Priorität 3 (Fallback): Das alte 'License'-Feld.
            license_info = metadata.get('License', 'N/A')

        requires_dist = metadata.get_all('Requires-Dist') or []
        dependencies_str = ', '.join(requires_dist) if requires_dist else ''

        info_lines = [
            f"{self.t('info_name')}: {metadata.get('Name', 'N/A')}",
            f"{self.t('info_version')} (installiert): {metadata.get('Version', 'N/A')}",
            f"{self.t('info_summary')}: {metadata.get('Summary', 'N/A')}",
            f"{self.t('info_homepage')}: {homepage}",
            f"{self.t('info_author')}: {author}",
            f"{self.t('info_license')}: {license_info}",
            f"{self.t('info_location')}: {dist.locate_file('')}",
            f"{self.t('info_dependencies')}: {dependencies_str}",
            f"{self.t('info_required_by')}: {', '.join(self.get_required_by(pkg_name))}"
        ]
        return "\n\n".join(info_lines)

    def get_install_time(self, pkg_name):
        """Liest das Installationsdatum eines Pakets."""
        try:
            dist = importlib.metadata.distribution(pkg_name)
            path = dist.locate_file('')
            if path and os.path.exists(path):
                return datetime.datetime.fromtimestamp(os.path.getmtime(path))
        except (importlib.metadata.PackageNotFoundError, FileNotFoundError, OSError):
            pass
        return None

    def get_missing_deps(self, dist):
        """Prüft auf fehlende Abhängigkeiten für eine Distribution."""
        missing_deps = []
        requires_dist = dist.metadata.get_all('Requires-Dist') or []
        if requires_dist:
            installed_normalized = {
                p.lower().replace("_", "-") for p in self.installed_packages_cache}
            for req in requires_dist:
                try:
                    from packaging.requirements import Requirement, InvalidRequirement
                    parsed = Requirement(req)
                    req_name = parsed.name
                    req_spec = req.split(';')[0].strip() if ';' in req else req # pylint: disable=unused-variable
                except InvalidRequirement:
                    req_name = req.split(' ')[0].split('[')[0].split(';')[0].split(
                        '!=')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                    req_spec = req.split(';')[0].strip() if ';' in req else req
                if req_name.lower().replace("_", "-") not in installed_normalized:
                    missing_deps.append(req_spec)
        return missing_deps

    def get_required_by(self, pkg_name):
        """Findet alle Pakete, die von `pkg_name` abhängen."""
        requiring_packages = []
        normalized_pkg_name = pkg_name.replace("_", "-").lower()
        for dist in importlib.metadata.distributions():
            requires_dist = dist.metadata.get_all('Requires-Dist') or []
            if requires_dist:
                for req in requires_dist:
                    try:
                        from packaging.requirements import Requirement, InvalidRequirement
                        parsed = Requirement(req)
                        req_name = parsed.name
                    except InvalidRequirement:
                        req_name = req.split(' ')[0].split('[')[0].split(';')[0].split(
                            '!=')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                    if req_name.replace("_", "-").lower() == normalized_pkg_name:
                        requiring_packages.append(dist.metadata['name'])
        return sorted(requiring_packages, key=str.lower)

    def get_all_dependencies(self, pkg_name, visited=None):
        """Sammelt alle direkten Abhängigkeiten eines Pakets."""
        if visited is None: # pylint: disable=singleton-comparison
            visited = set()
        if pkg_name.lower() in visited:
            return []
        visited.add(pkg_name.lower())

        dependencies = []
        try:
            dist = importlib.metadata.distribution(pkg_name)
            requires_dist = dist.metadata.get_all('Requires-Dist') or []
            for req in requires_dist:
                try:
                    from packaging.requirements import Requirement, InvalidRequirement
                    parsed = Requirement(req)
                    req_name = parsed.name
                except InvalidRequirement:
                    req_name = req.split(' ')[0].split('[')[0].split(';')[0].split(
                        '!=')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                dependencies.append(req_name)
        except importlib.metadata.PackageNotFoundError:
            pass
        return dependencies

    def find_removable_packages(self, pkg_name):
        """Findet Abhängigkeiten, die nur von pkg_name benötigt werden."""
        dependencies = self.get_all_dependencies(pkg_name)
        if not dependencies:
            return []

        removable = []
        for dep in dependencies:
            required_by = self.get_required_by(dep)
            if required_by == [pkg_name]:
                removable.append(dep)

        return removable

    def _should_apply_requirement(self, marker_part):
        """Prüft, ob ein Requirement-Marker auf das aktuelle System zutrifft."""
        if not marker_part:
            return True

        # Vereinfachte Prüfung für die häufigsten Fälle
        if 'sys_platform' in marker_part:
            is_windows = sys.platform.startswith('win')
            if "'win32'" in marker_part and not is_windows:
                return False
            if "'linux'" in marker_part and is_windows:
                return False
            if "'darwin'" in marker_part and not sys.platform.startswith('darwin'):
                return False
        return True

    def autoremove_packages(self):
        """Entfernt Abhängigkeiten, die von keinem anderen Paket mehr benötigt werden."""
        all_packages = self.installed_packages_cache.copy() if self.installed_packages_cache else []
        packages_to_remove = []

        for pkg in all_packages:
            required_by = self.get_required_by(pkg)
            if not required_by:
                dependencies_of = []
                for other_pkg in all_packages:
                    if other_pkg.lower() != pkg.lower():
                        if pkg in self.get_all_dependencies(other_pkg):
                            dependencies_of.append(other_pkg)

                if not dependencies_of and pkg not in ['pip', 'setuptools', 'wheel']:
                    packages_to_remove.append(pkg)

        if packages_to_remove:
            msg = self.t(
                "autoremove_unreferenced_packages"
                ) + "\n\n" + "\n".join(
                    packages_to_remove[:10]
                    )
            if len(packages_to_remove) > 10:
                msg += "\n\n" + self.t(
                    "autoremove_and_more").format(count=len(packages_to_remove) - 10)
            if messagebox.askyesno(
                    self.t("autoremove_dialog_title"),
                    msg + "\n\n" + self.t("autoremove_confirm_question")):
                def uninstall_packages():
                    """Deinstalliert alle markierten Pakete synchron und fängt Fehler ab."""
                    self.root.after(0, self.start_progress)
                    successful_removals = []
                    failed_removals = []

                    for pkg in packages_to_remove:
                        try:
                            result = subprocess.run(
                                [sys.executable, "-m", "pip", "uninstall", "-y", pkg],
                                capture_output=True,
                                text=True,
                                check=False,
                                timeout=60
                            )
                            if result.returncode == 0:
                                successful_removals.append(pkg)
                                self.log_message(self.t("log_autoremove_success").format(pkg=pkg))
                            else:
                                error_text = result.stderr if result.stderr else result.stdout
                                failed_removals.append((pkg, error_text))
                                self.log_message(
                                    self.t(
                                        "log_autoremove_error").format(pkg=pkg, error=error_text),
                                        "ERROR")
                        except subprocess.TimeoutExpired:
                            error_text = self.t("log_autoremove_timeout").format(pkg=pkg)
                            failed_removals.append((pkg, error_text))
                            self.log_message(error_text, "ERROR")
                        except subprocess.SubprocessError as e:
                            failed_removals.append((pkg, str(e)))
                            self.log_message(
                                self.t("log_autoremove_error").format(pkg=pkg, error=e), "ERROR")

                    self.root.after(0, self.refresh_package_list)

                    def show_result():
                        if failed_removals:
                            error_msg = self.t("autoremove_partial_fail_msg").format(
                                success_count=len(successful_removals),
                                fail_count=len(failed_removals))
                            error_msg += "\n\n" + self.t("autoremove_failed_packages_header") + "\n"
                            for pkg, _ in failed_removals[:10]:
                                error_msg += f"- {pkg}\n"
                            if len(failed_removals) > 10:
                                error_msg += "\n" + self.t("autoremove_and_more").format(
                                    count=len(failed_removals) - 10)
                            messagebox.showwarning(
                                self.t("autoremove_partial_fail_title"),
                                error_msg
                            )
                        else:
                            messagebox.showinfo(
                                self.t("autoremove_success_title"),
                                self.t("autoremove_success_msg").format(
                                    count=len(successful_removals))
                            )

                    self.root.after(3500, show_result)

                threading.Thread(target=uninstall_packages, daemon=True).start()
        else:
            messagebox.showinfo(self.t("autoremove_dialog_title"),
                self.t("autoremove_no_packages_found"))

    def check_cross_package_conflicts(self, target_dep_name, target_specifier):
        """Prüft, ob andere installierte Pakete
        eine inkompatible Version einer Abhängigkeit benötigen.

        Returns: List of (package_name, their_requirement_string) tuples that conflict
        """
        from packaging.requirements import Requirement, InvalidRequirement
        from packaging.specifiers import SpecifierSet

        conflicting_packages = []

        try:
            target_spec = SpecifierSet(target_specifier) if target_specifier else None

            for dist in importlib.metadata.distributions():
                requires_dist = dist.metadata.get_all('Requires-Dist') or []
                pkg_dist_name = dist.metadata['name']

                for req in requires_dist:
                    try:
                        req_clean = req.split(';')[0].strip()
                        marker_part = req.split(';')[1].strip() if ';' in req else None
                        if not self._should_apply_requirement(marker_part):
                            continue

                        parsed = Requirement(req_clean)
                        if parsed.name.lower().replace("_", "-") == target_dep_name.lower().replace("_", "-"):
                            other_spec = str(parsed.specifier) if parsed.specifier else ""

                            if target_spec and other_spec:
                                other_spec_obj = SpecifierSet(other_spec)
                                if not target_spec & other_spec_obj:
                                    self.log_message(
                                        self.t("log_cross_package_conflict").format(
                                            pkg_dist_name=pkg_dist_name, req_clean=req_clean,
                                            target_dep_name=target_dep_name,
                                            target_specifier=target_specifier),
                                        "DEBUG"
                                    )
                    except InvalidRequirement: # pylint: disable=broad-except
                        pass
        except (ValueError, KeyError) as e:
            self.log_message(self.t("log_cross_package_conflict_error").format(e), "DEBUG")

        return conflicting_packages

    def _get_package_requirements(self, pkg_name, version=None):
        """Holt die Liste der Abhängigkeiten für ein Paket, entweder lokal oder von PyPI."""
        try:
            dist_name = f"{pkg_name}=={version}" if version else pkg_name
            dist = importlib.metadata.distribution(dist_name)
            self.log_message(self.t("log_using_local_metadata").format(pkg_name), "DEBUG")
            return dist.metadata.get_all('Requires-Dist') or []
        except importlib.metadata.PackageNotFoundError:
            self.log_message(self.t("log_local_metadata_unavailable"), "DEBUG")
            data = self.pypi_api.get_package_info(pkg_name)
            if data:
                return data.get('info', {}).get('requires_dist') or []
            return []

    def _process_single_requirement(self, req, required_packages, conflicts, cross_conflicts):
        """Verarbeitet eine einzelne Anforderung, prüft Marker und findet Konflikte."""
        from packaging.requirements import InvalidRequirement, Requirement
        from packaging.specifiers import SpecifierSet

        try:
            req_clean = req.split(';')[0].strip()
            if not req_clean:
                return

            marker_part = req.split(';')[1].strip() if ';' in req else None
            if not self._should_apply_requirement(marker_part):
                return

            parsed_req = Requirement(req_clean)
            req_name = parsed_req.name
            specifier = str(parsed_req.specifier) if parsed_req.specifier else ""

            if req_name.lower().replace(
                "_", "-") not in {p.lower().replace(
                    "_", "-") for p in ['pip', 'setuptools', 'wheel']}:
                required_packages.append((req_name, specifier))

                try:
                    current_version = importlib.metadata.version(req_name)
                    if specifier and current_version not in SpecifierSet(specifier):
                        conflicts.append((req_name, current_version, specifier))
                        self.log_message(
                            self.t("log_dependency_conflict").format(
                                req_name, current_version, specifier), "DEBUG")
                except importlib.metadata.PackageNotFoundError:
                    self.log_message(
                        self.t("log_dependency_not_installed").format(req_name), "DEBUG")

                cross_pkg_conflicts = self.check_cross_package_conflicts(req_name, specifier)
                if cross_pkg_conflicts:
                    cross_conflicts[req_name] = cross_pkg_conflicts

        except InvalidRequirement as e:
            self.log_message(self.t("log_parse_requirement_error").format(req, e), "DEBUG")

    def resolve_dependencies(self, pkg_name, version=None):
        """Resolves dependencies for a package and detects conflicts.

        Returns: (can_install, required_packages, conflicts)
        """
        required_packages = []
        conflicts = []
        cross_conflicts = {}

        try:
            requires_dist = self._get_package_requirements(pkg_name, version)
            for req in requires_dist:
                self._process_single_requirement(req, required_packages, conflicts, cross_conflicts)
        except (packaging.specifiers.InvalidSpecifier, requests.RequestException) as e:
            self.log_message(self.t("log_dependency_resolution_error").format(e), "WARNING")

        return (len(conflicts) == 0 and len(cross_conflicts) == 0,
                required_packages, conflicts, cross_conflicts)

    def _build_conflict_message(self, conflicts, cross_conflicts):
        """Erstellt die formatierte Textnachricht für den Konfliktdialog."""
        message_parts = []
        if conflicts:
            message_parts.append((self.t("conflict_header_version") + "\n", "header"))
            for pkg, current, required in conflicts:
                message_parts.append((f"• {pkg}\n", ""))
                message_parts.append((self.t(
                    "conflict_installed_version").format(current=current) + "\n", ""))
                message_parts.append(
                    (self.t("conflict_required_version").format(required=required) + "\n\n", ""))

        if cross_conflicts:
            header_text = self.t("conflict_header_dependency")
            header = f"\n{header_text}\n" if conflicts else f"{header_text}\n"
            message_parts.append((header, "header"))
            for dep_pkg, conflicting_packages in cross_conflicts.items():
                message_parts.append(
                    (self.t("conflict_package_bullet").format(dep_pkg=dep_pkg) + "\n", ""))
                for pkg_name, req_string in conflicting_packages:
                    message_parts.append(
                        (self.t("conflict_package_requires").format(pkg_name=pkg_name,
                        req_string=req_string) + "\n", "")
                    )
                message_parts.append(("\n", ""))
        return message_parts

    def _create_conflict_dialog_widgets(self, pkg_name):
        """Erstellt die GUI-Elemente für den Abhängigkeitskonflikt-Dialog."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("dependency_conflicts_title"))
        dialog.geometry("700x550")
        dialog.resizable(True, True)
        dialog.minsize(600, 450)

        main_frame = tk.Frame(dialog, relief=tk.RAISED, borderwidth=2)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        label = ttk.Label(
            main_frame,
            text=self.t("conflict_dialog_title").format(pkg_name=pkg_name),
            font=("Arial", 10, "bold"))
        label.pack(anchor=tk.W, pady=5)

        text_frame = tk.Frame(main_frame, relief=tk.RAISED, borderwidth=1)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_widget = tk.Text(
            text_frame, height=12, wrap=tk.WORD, yscrollcommand=scrollbar.set
        )
        scrollbar.config(command=text_widget.yview)
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        options_frame = tk.LabelFrame(
            main_frame, text=self.t("label_options"),
            relief=tk.RAISED, borderwidth=2, padx=10, pady=10)
        options_frame.pack(fill=tk.X, pady=(10, 5))

        action_var = tk.StringVar(value="install")

        r1 = ttk.Radiobutton(
            options_frame, text=self.t("radio_install_anyway"), variable=action_var, value="install"
        )
        r1.pack(anchor=tk.W, pady=2)
        r2 = ttk.Radiobutton(
            options_frame, text=self.t("radio_upgrade_deps"),
            variable=action_var, value="upgrade_deps"
        )
        r2.pack(anchor=tk.W, pady=2)
        r3 = ttk.Radiobutton(
            options_frame, text=self.t("btn_cancel"), variable=action_var, value="cancel"
        )
        r3.pack(anchor=tk.W, pady=2)

        button_frame = tk.Frame(main_frame, relief=tk.FLAT, borderwidth=0)
        button_frame.pack(fill=tk.X, pady=(15, 5))

        ok_btn = ttk.Button(button_frame, text=self.t("btn_ok"), width=10)
        ok_btn.pack(side=tk.LEFT, padx=5)
        cancel_btn = ttk.Button(button_frame, text=self.t("btn_cancel"), width=10)
        cancel_btn.pack(side=tk.LEFT, padx=5)

        return {
            "dialog": dialog,
            "text_widget": text_widget,
            "action_var": action_var,
            "ok_btn": ok_btn,
            "cancel_btn": cancel_btn
        }

    def show_dependency_conflict_dialog(self, pkg_name, conflicts, cross_conflicts=None):
        """Shows a dialog with dependency conflicts and asks for resolution.

        Returns: (proceed, action)
            proceed: Boolean whether to proceed with installation
            action: 'install' (continue), 'upgrade_deps' (upgrade conflicting packages), 'cancel'
        """
        if cross_conflicts is None:
            cross_conflicts = {} # pylint: disable=unused-variable

        if not conflicts and not cross_conflicts:
            return (True, 'install')

        widgets = self._create_conflict_dialog_widgets(pkg_name)
        dialog = widgets["dialog"]
        text_widget = widgets["text_widget"]
        action_var = widgets["action_var"]

        message_parts = self._build_conflict_message(conflicts, cross_conflicts)
        for part, tag in message_parts:
            text_widget.insert(tk.END, part, tag)
        text_widget.tag_config(
            "header", foreground="#CC0000", font=("Arial", 9, "bold")
        )
        text_widget.config(state=tk.DISABLED)

        result = {'proceed': False, 'action': 'cancel'}

        def on_ok():
            result['action'] = action_var.get()
            result['proceed'] = result['action'] != 'cancel'
            dialog.destroy()

        def on_cancel():
            result['proceed'] = False
            result['action'] = 'cancel'
            dialog.destroy()

        widgets["ok_btn"].config(command=on_ok)
        widgets["cancel_btn"].config(command=on_cancel)

        dialog.transient(self.root)
        dialog.grab_set()
        dialog.focus()
        self.root.wait_window(dialog)

        return (result['proceed'], result['action'])

    def _display_details_in_text_widget(self, text_widget, details, url_labels=None):
        """
        Eine generische Funktion, um eine Liste von Key-Value-Paaren
        formatiert in einem Text-Widget darzustellen.

        :param text_widget: Das tk.Text-Widget, das aktualisiert werden soll.
        :param details: Eine Liste von Tupeln (label_key, value, optional_tag).
        :param url_labels: Eine Liste von Label-Keys, deren Werte als URLs behandelt werden sollen.
        """
        if url_labels is None:
            url_labels = []

        text_widget.config(state=tk.NORMAL)
        text_widget.delete("1.0", tk.END)

        for label_key, value, *tag in details:
            label = self.t(label_key)
            current_tag = tag[0] if tag else None
            text_widget.insert(tk.END, f"{label}: {value}\n\n", current_tag)

            if label_key in url_labels:
                line_start = text_widget.search(f"{label}:", "1.0", tk.END)
                if line_start:
                    url_start_index = text_widget.index(
                        f"{line_start} + {len(label) + 2}c"
                    )
                    url_end_index = text_widget.index(f"{line_start} lineend")
                    url_value = text_widget.get(url_start_index, url_end_index).strip()
                    if url_value.startswith("http"):
                        text_widget.tag_add("hyperlink", url_start_index, url_end_index)

        text_widget.config(state=tk.DISABLED)

    def display_formatted_info(self, info, pypi_info, install_time, missing_deps, pkg_name):
        """Formatiert und zeigt die gesammelten Paketinformationen an."""
        try:
            if not self.root.winfo_exists():
                return
            self.current_displayed_pkg_name = pkg_name
            self.current_pypi_info = pypi_info
            self.current_install_time = install_time
            self.current_missing_deps = missing_deps
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, info + "\n\n")

            if pkg_name in self.security_issues_cache:
                security_issue = self.security_issues_cache[pkg_name]
                self.info_text.insert(
                    tk.END, f"\nâ  SICHERHEITSPROBLEM: {security_issue}\n", "security_warning"
                )
                pypi_url = f"https://pypi.org/project/{pkg_name}/"
                self.info_text.insert(tk.END, f"PyPI Seite: {pypi_url}\n", "security_warning")
                start_idx = self.info_text.search(pypi_url, "1.0", tk.END)
                end_idx = f"{start_idx} lineend"
                self.info_text.tag_add("hyperlink", start_idx, end_idx)
                self.info_text.insert(tk.END, "\n")

            if pypi_info and pypi_info.get("yanked"):
                self.info_text.insert(tk.END, f"\n{self.t('info_yanked')}\n", "yanked_warning")
                self.info_text.insert(
                    tk.END, f"{self.t('info_yanked_reason')}: {pypi_info.get('yanked_reason')}\n"
                )

            if pkg_name in self.outdated_packages_cache:
                update_info = self.outdated_packages_cache[pkg_name]
                update_text = self.t(
                    "update_available").format(update_info['current'], update_info['latest'])
                version_line_start = self.info_text.search(
                    f"{self.t('info_version')} (installiert):", "1.0", tk.END
                )
                if version_line_start:
                    line_end_index = self.info_text.index(f"{version_line_start} lineend")
                    self.info_text.insert(
                        f"{line_end_index}\n", f"  -> {update_text}\n", "update_info")

            if install_time:
                fmt = {"de": "%d.%m.%Y %H:%M:%S"}.get(self.current_lang, "%Y-%m-%d %H:%M:%S")
                self.info_text.insert(
                    tk.END, f"\n{self.t('install_time').format(install_time.strftime(fmt))}\n")
            else:
                self.info_text.insert(tk.END, f"\n{self.t('no_install_time')}\n")

            homepage_line_start = self.info_text.search(
                f"{self.t('info_homepage')}:", "1.0", tk.END)
            if homepage_line_start:
                url_start_index = self.info_text.index(
                    f"{homepage_line_start} + {len(self.t('info_homepage')) + 2}c"
                )
                url_end_index = self.info_text.index(f"{homepage_line_start} lineend")
                url = self.info_text.get(url_start_index, url_end_index).strip()
                if url.startswith("http"):
                    self.info_text.tag_add("hyperlink", url_start_index, url_end_index)

            if missing_deps:
                self.info_text.insert(
                    tk.END, f"\n{self.t('missing_deps_info').format(', '.join(missing_deps))}\n")
        except (tk.TclError, RuntimeError):
            pass

    def open_url_from_text(self, event):
        """Öffnet eine URL aus einem Text-Widget."""
        index = event.widget.index(f"@{event.x},{event.y}")
        tag_ranges = event.widget.tag_ranges("hyperlink")
        for i in range(0, len(tag_ranges), 2):
            start, end = tag_ranges[i], tag_ranges[i+1]
            if event.widget.compare(index, ">=", start) and event.widget.compare(index, "<", end):
                url = event.widget.get(start, end).strip()
                if url.startswith("http"):
                    self.log_message(self.t("log_opening_url").format(url))
                    webbrowser.open_new_tab(url)
                return

    def setup_text_widget_tags(self, text_widget):
        """Definiert Tags für Text-Widgets."""
        text_widget.tag_config("update_info", foreground="#006400", font=("Segoe UI", 9, "bold"))
        text_widget.tag_config("yanked_warning", foreground="red", font=("Segoe UI", 9, "bold"))
        text_widget.tag_config("security_warning",
                               foreground="#CC0000", font=("Segoe UI", 9, "bold"))
        text_widget.tag_config("hyperlink", foreground="blue", underline=True)
        text_widget.tag_bind("hyperlink", "<Enter>",
                             lambda e, w=text_widget: w.config(cursor="hand2"))
        text_widget.tag_bind("hyperlink", "<Leave>", lambda e, w=text_widget: w.config(cursor=""))
        text_widget.tag_bind("hyperlink", "<Button-1>", self.open_url_from_text)

    def load_python_versions(self):
        """Lädt installierte Python-Versionen."""
        def do_load():
            """Lädt installierte Python-Versionen und aktualisiert das Text-Widget."""
            try:
                result = subprocess.run(["py", "-0p"], capture_output=True, text=True, check=False)
                lines = result.stdout.splitlines() if result.returncode == 0 else [
                    self.t("log_python_launcher_not_found")]
            except FileNotFoundError:
                lines = [self.t("log_python_launcher_not_found")]
            self.root.after(0, lambda: self.update_python_version_display(lines))
        threading.Thread(target=do_load, daemon=True).start()

    def update_python_version_display(self, lines):
        """Aktualisiert die Anzeige der Python-Versionen."""
        try:
            if not self.root.winfo_exists():
                return

            # Widget aktivieren, Inhalt löschen
            self.py_version_text.config(state=tk.NORMAL)
            self.py_version_text.delete("1.0", tk.END)

            # Alle Zeilen einfügen
            for line in lines:
                self.py_version_text.insert(tk.END, line.strip() + "\n")

            # Widget wieder deaktivieren – jetzt nach dem Loop!
            self.py_version_text.config(state=tk.DISABLED)
        except (tk.TclError, RuntimeError):
            pass

    def _on_storage_method_changed(self):
        """Speichert die Sprache in der neuen Methode und löscht aus der alten."""

        if not self.remember_language_var.get():
            return

        method = self.storage_method_var.get()

        if method == "registry":
            self._save_language_to_registry()
            self._delete_config_file()
        elif method == "config":
            self._save_language_to_config()
            if sys.platform == "win32":
                self._delete_language_from_registry_only()

    def _save_language_to_registry(self):
        try:
            import winreg
            reg_path = r"Software\Pip_Package_Manager"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                winreg.SetValueEx(key, "Language", 0, winreg.REG_SZ, self.current_lang)
                winreg.SetValueEx(key, "RememberLanguage", 0, winreg.REG_SZ, "1")
            self.log_message(self.t("lang_saved_registry"))
            self._delete_config_file()
        except (OSError, ImportError) as e:
            self.log_message(self.t("log_registry_save_error").format(e=e), "ERROR")

    def _load_language_from_registry(self):
        """Lädt die Sprache aus der Windows Registry."""
        if sys.platform != "win32":
            return None

        try:
            import winreg
            reg_path = r"Software\Pip_Package_Manager"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                lang, _ = winreg.QueryValueEx(key, "Language")
                return lang
        except (OSError, ImportError):
            return None

    def _is_language_remembered_registry(self):
        """Prüft, ob die Sprache in der Registry als "merken" markiert ist."""
        if sys.platform != "win32":
            return False

        try:
            import winreg
            reg_path = r"Software\Pip_Package_Manager"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
            remember, _ = winreg.QueryValueEx(key, "RememberLanguage")
            winreg.CloseKey(key)
            return remember == "1"
        except (OSError, ImportError):
            return False

    def _delete_language_from_registry_only(self):
        """Löscht nur die Spracheinstellungen aus der Registry."""
        if sys.platform != "win32":
            return

        try:
            import winreg
            reg_path = r"Software\Pip_Package_Manager"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
                winreg.DeleteValue(key, "Language")
                winreg.DeleteValue(key, "RememberLanguage")
                winreg.CloseKey(key)
                self.log_message(self.t("log_registry_settings_removed"))
            except WindowsError:
                pass
        except (OSError, ImportError) as e:
            self.log_message(self.t("log_registry_delete_error").format(e=e), "ERROR")

    def _delete_registry_entry(self):
        """Löscht den kompletten Registry-Eintrag aus der Windows Registry."""
        if sys.platform != "win32":
            return

        def do_delete(): # pylint: disable=unused-variable
            try:
                import winreg
                reg_path = r"Software\Pip_Package_Manager"
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
                except WindowsError:
                    key = winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_ALL_ACCESS)
                    winreg.DeleteValue(key, "Language")
                    winreg.DeleteValue(key, "RememberLanguage")
                    winreg.CloseKey(key)
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)

                self.root.after(3000, self._verify_registry_deletion)
            except (OSError, ImportError) as e:
                self.log_message(self.t("log_registry_delete_error").format(e=e), "ERROR")

        threading.Thread(target=do_delete, daemon=True).start()

    def _verify_registry_deletion(self):
        """Prüft nach 3 Sekunden, ob die Registry gelöscht wurde."""
        if sys.platform != "win32":
            return

        try:
            import winreg
            reg_path = r"Software\Pip_Package_Manager"
            try:
                winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path)
                self.log_message(self.t("log_registry_delete_incomplete"))
            except WindowsError:
                self.log_message(self.t("lang_deleted_registry"))

            self._update_delete_button_state()
        except (OSError, ImportError) as e:
            self.log_message(self.t("log_verification_error").format(e=e), "ERROR")

    def _update_delete_button_state(self):
        """Aktualisiert den Status des Delete-Buttons basierend auf Registry/Config Existenz."""
        if not self.tab3_delete_registry_btn:
            return

        has_registry = self._is_language_remembered_registry()
        has_config = self._is_language_remembered_config()

        if has_registry or has_config: # pylint: disable=unused-variable
            self.tab3_delete_registry_btn.config(state=tk.NORMAL)
        else:
            self.tab3_delete_registry_btn.config(state=tk.DISABLED)

    def _delete_pypi_index(self):
        """Löscht den PyPI Index."""
        def do_delete():
            try:
                cache_path = self._get_cache_path()
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                    self.log_message(self.t("log_pypi_index_deleted_path").format(path=cache_path))
                    self.pypi_index_cache = []
                    self.pypi_package_releases_cache = {}
                else:
                    self.log_message(self.t("log_pypi_index_not_found"))
            except (IOError, OSError) as e:
                self.log_message(self.t("log_pypi_index_delete_error").format(e=e), "ERROR")

        threading.Thread(target=do_delete, daemon=True).start()

    def _get_config_file_path(self):
        """Gibt den Pfad zur Konfigurationsdatei zurück."""
        if os.name == 'nt':
            config_dir = os.path.expandvars(r"%APPDATA%\Pip_Package_Manager")
        else:
            config_dir = os.path.expandvars("~/.config/Pip_Package_Manager")

        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "config.json")

    def _save_language_to_config(self):
        """Speichert die Sprache in der Konfigurationsdatei und löscht aus Registry."""
        try:
            config_path = self._get_config_file_path()
            config_data = {}

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)


            config_data['language'] = self.current_lang
            config_data['remember_language'] = True

            config_dir = os.path.dirname(config_path)
            os.makedirs(config_dir, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=4)

            self.log_message(self.t("lang_saved_config"))

            self.log_message(self.t("lang_saved_config"))

            if sys.platform == "win32":
                self._delete_language_from_registry_only()
        except (IOError, json.JSONDecodeError) as e:
            self.log_message(self.t("log_config_save_error").format(e=e), "ERROR")

    def _delete_config_file(self):
        """Löscht die Konfigurationsdatei wenn keine anderen Einstellungen stehen."""
        try:
            config_path = self._get_config_file_path()
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)

                config_data.pop('language', None)
                config_data.pop('remember_language', None)

                if not config_data:
                    os.remove(config_path)
                    self.log_message(self.t("log_config_file_deleted"))
                else:
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=4)
                    self.log_message(self.t("log_config_file_settings_removed"))
        except (IOError, OSError, json.JSONDecodeError) as e:
            self.log_message(self.t("log_config_delete_error").format(e=e), "ERROR")

    def _load_language_from_config(self):
        """Lädt die Sprache aus der Konfigurationsdatei."""
        try:
            config_path = self._get_config_file_path()

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return config_data.get('language')
        except (IOError, json.JSONDecodeError):
            pass

        return None

    def _is_language_remembered_config(self):
        """Prüft, ob die Sprache in der Config als "merken" markiert ist."""
        try:
            config_path = self._get_config_file_path()

            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return config_data.get('remember_language', False)
        except (IOError, json.JSONDecodeError):
            pass

        return False

    def _load_saved_language_on_startup_v2(self):
        """[DEPRECATED] Zweite Implementierung - nutze die erste Version stattdessen."""
        if sys.platform == "win32":
            if self._is_language_remembered_registry():
                lang = self._load_language_from_registry()
                if lang:
                    self.current_lang = lang
                    self.remember_language_var.set(True)
                    self.storage_method_var.set("registry")
                    self._enable_storage_method_radios()
                    return

        if self._is_language_remembered_config():
            lang = self._load_language_from_config()
            if lang:
                self.current_lang = lang
                self.remember_language_var.set(True)
                self.storage_method_var.set("config")
                self._enable_storage_method_radios()
                return

    def update_listbox_safely(self, packages):
        """Aktualisiert die Paket-Listbox sicher im GUI-Thread."""
        try:
            if not self.root.winfo_exists():
                return
            self.package_listbox.delete(0, tk.END)
            for pkg in packages:
                self.package_listbox.insert(tk.END, pkg)
            self.status_label.config(text=self.t("status_loaded").format(len(packages)))
        except (tk.TclError, RuntimeError):
            pass

    def colorize_outdated_packages(self):
        """Färbt veraltete Pakete in der Liste ein."""
        for i in range(self.package_listbox.size()):
            pkg_name = self.package_listbox.get(i)
            if pkg_name in self.security_packages_cache:
                self.package_listbox.itemconfig(i, {'bg': '#FF7F7F'})
            elif pkg_name in self.outdated_packages_cache:
                self.package_listbox.itemconfig(i, {'bg': '#B6F0A5'})
            else:
                self.package_listbox.itemconfig(i, {'bg': ''})

    def colorize_security_packages(self):
        """Färbt Pakete mit Sicherheitslücken rot ein."""
        for i in range(self.package_listbox.size()):
            pkg_name = self.package_listbox.get(i)
            if pkg_name in self.security_packages_cache:
                self.package_listbox.itemconfig(i, {'bg': '#FF7F7F'})
            elif pkg_name in self.outdated_packages_cache:
                self.package_listbox.itemconfig(i, {'bg': '#B6F0A5'})
            else:
                self.package_listbox.itemconfig(i, {'bg': ''})

    # --- Methoden für Tab 2 (Suche) ---

    def perform_search(self, _event=None):
        """Führt die Paketsuche durch."""
        self.search_versions_listbox.delete(0, tk.END)
        self.search_info_text.config(state=tk.NORMAL)
        self.search_info_text.delete("1.0", tk.END)
        query = self.search_entry_var.get()
        if not query:
            self.update_search_results([], "")
            return
        if not self.pypi_index_cache:
            self.log_message(self.t("log_pypi_not_loaded"))
            self.load_pypi_index()
            return
        self.log_message(self.t("log_filtering_index").format(query))
        filtered_packages = [pkg for pkg in self.pypi_index_cache if query.lower() in pkg.lower()]
        self.root.after(0, lambda: self.update_search_results(filtered_packages, query))

    def _read_pypi_cache_from_disk(self):
        """Liest den PyPI-Index-Cache von der Festplatte."""
        if os.path.exists(self.pypi_cache_path):
            try:
                with open(self.pypi_cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.log_message(self.t("log_cache_read_error").format(e), "WARNING")
        return None

    def _write_pypi_cache_to_disk(self, data):
        """Schreibt den PyPI-Index-Cache auf die Festplatte."""
        try:
            with open(self.pypi_cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except IOError as e:
            self.log_message(self.t("log_cache_write_error").format(e), "ERROR")

    def load_pypi_index(self): # NEU: Umbenannt von get_pypi_info
        """Lädt den PyPI-Paketindex vom lokalen Cache und aktualisiert ihn mit Delta-Updates."""
        def do_load():
            """
            Loads the PyPI package index from the local cache and updates it with delta updates.
            Lädt den PyPI-Paketindex vom lokalen Cache und aktualisiert ihn mit Delta-Updates.
            Falls der Cache leer ist, wird der volle Index von PyPI geladen.
            Ansonsten wird nur der delta-Update von PyPI geladen und in den Cache gespeichert.
            Der Cache wird nur aktualisiert, wenn die geladene Daten neuere sind als die im Cache.
            """

            self.root.after(0, self.start_progress)
            cache_data = self._read_pypi_cache_from_disk()
            last_serial = 0
            if cache_data:
                self.pypi_index_cache = cache_data.get('packages', [])
                last_serial = cache_data.get('last_serial', 0)
                self.log_message(self.t("log_loaded_from_cache").format(len(self.pypi_index_cache)))
            elif not last_serial:
                self.root.after(0, lambda: self.update_status_label("status_loading_index"))

            if last_serial:
                self.log_message(self.t("log_checking_updates_since").format(last_serial))

            data = self.pypi_api.update_package_index(last_serial)

            if data:
                new_serial = data.get('meta', {}).get('_last-serial', last_serial)
                new_packages = [p['name'] for p in data.get('projects', [])]

                if new_packages:
                    if last_serial == 0:  # Full load
                        self.pypi_index_cache = sorted(new_packages, key=str.lower)
                        self.log_message(
                            self.t("log_full_index_loaded").format(len(self.pypi_index_cache)))
                    else:  # Delta update
                        existing_packages_set = set(self.pypi_index_cache)
                        added_packages = [
                            pkg for pkg in new_packages if pkg not in existing_packages_set]
                        if added_packages:
                            self.pypi_index_cache.extend(added_packages)
                            self.pypi_index_cache.sort(key=str.lower)
                            self.log_message(f"Applied {len(added_packages)} updates. Total: {len(self.pypi_index_cache)}.")

                if new_serial > last_serial:
                    self._write_pypi_cache_to_disk(
                        {'last_serial': new_serial, 'packages': self.pypi_index_cache})

            if self.progress_frame_tab1.winfo_ismapped() or self.progress_frame_tab2.winfo_ismapped():
                self.root.after(0, self.stop_progress)
        threading.Thread(target=do_load, daemon=True).start()

    def update_search_results(self, packages, query):
        """Aktualisiert die Suchergebnis-Listbox."""
        self.search_results_listbox.delete(0, tk.END)
        if packages:
            for pkg in packages:
                self.search_results_listbox.insert(tk.END, pkg)
        elif query:
            self.search_results_listbox.insert(tk.END, self.t("search_no_results").format(query))

    def show_package_versions(self, _event=None):
        """Zeigt verfügbare Versionen für ein Suchergebnis an."""
        selection = self.search_results_listbox.curselection()
        if not selection:
            return
        pkg_name = self.search_results_listbox.get(selection[0])
        self.current_searched_pkg_name = pkg_name
        self.search_versions_listbox.delete(0, tk.END)
        self.search_info_text.config(state=tk.NORMAL)
        self.search_info_text.delete("1.0", tk.END)
        self.search_info_text.insert(tk.END, self.t("loading_info").format(pkg_name))
        self.search_info_text.config(state=tk.DISABLED)
        threading.Thread(
            target=self._fetch_and_display_versions, args=(pkg_name,), daemon=True).start()

    def _fetch_and_display_versions(self, pkg_name):
        """Hintergrund-Task zum Abrufen und Anzeigen von Versionen."""
        self.current_package_version_details_cache.clear()
        pypi_data = self.fetch_pypi_package_releases(pkg_name)
        if not pypi_data:
            self.root.after(0, self._update_search_info_text, self.t("no_info"))
            return
        releases = pypi_data.get('releases', {})
        compatible_versions_info = []
        for version_str, distributions in releases.items():
            for dist_data in distributions:
                filename = dist_data.get('filename')
                if not filename:
                    continue
                if self._is_compatible(filename, dist_data.get('packagetype')):
                    compatible_versions_info.append(
                        (packaging.version.parse(version_str), filename, dist_data))
                    self.current_package_version_details_cache[filename] = dist_data
        compatible_versions_info.sort(key=lambda x: x[0], reverse=True)
        self.root.after(0, self._update_version_listbox, compatible_versions_info)

    def _is_compatible(self, filename, packagetype):
        """Prüft, ob ein Release-File mit dem System kompatibel ist."""
        if packagetype == 'sdist':
            return True
        if packagetype == 'bdist_wheel':
            try:
                _name, _version, _build, wheel_tags = packaging_utils.parse_wheel_filename(filename)
                return not self.current_system_tags.isdisjoint(wheel_tags)
            except (packaging.utils.InvalidWheelFilename,
                    packaging.version.InvalidVersion, ValueError):
                return "any" in filename or "none" in filename
        return False

    def _update_version_listbox(self, compatible_versions_info):
        """Aktualisiert die Versions-Listbox im GUI-Thread."""
        self.search_versions_listbox.delete(0, tk.END)
        if compatible_versions_info:
            for _, filename, _ in compatible_versions_info:
                self.search_versions_listbox.insert(tk.END, filename)
        else:
            self.search_versions_listbox.insert(tk.END, self.t("search_no_compatible_versions"))
        self._update_search_info_text("") # Info-Text leeren

    def _update_search_info_text(self, text):
        """Aktualisiert die Such-Info-Textbox sicher."""
        self.search_info_text.config(state=tk.NORMAL)
        self.search_info_text.delete("1.0", tk.END)
        if text:
            self.search_info_text.insert(tk.END, text)
        self.search_info_text.config(state=tk.DISABLED)

    def fetch_pypi_package_releases(self, pkg_name):
        """Ruft Release-Daten von PyPI ab und speichert sie im Cache."""
        if pkg_name in self.pypi_package_releases_cache:
            return self.pypi_package_releases_cache[pkg_name]
        data = self.pypi_api.get_package_info(pkg_name)
        if data:
            self.pypi_package_releases_cache[pkg_name] = data
        return data

    def show_version_details(self, _event=None):
        """Zeigt Details für eine ausgewählte Version an."""
        selection = self.search_versions_listbox.curselection()
        if not selection:
            return
        selected_filename = self.search_versions_listbox.get(selection[0])
        file_data = self.current_package_version_details_cache.get(selected_filename)
        if not file_data:
            self._update_search_info_text(self.t("no_info"))
            return
        pypi_full_data = self.pypi_package_releases_cache.get(self.current_searched_pkg_name) # pylint: disable=unused-variable
        if not pypi_full_data:
            self._update_search_info_text(self.t("no_info"))
            return
        info = pypi_full_data.get('info', {})
        self.current_search_displayed_version = selected_filename

        # KORREKTUR: Die fehlende Logik zum Füllen der Textbox wird hier wieder eingefügt.
        description_text = info.get('summary') or info.get('description', 'N/A')
        project_urls = info.get('project_urls') or {}
        package_url = project_urls.get(
            'Homepage') or project_urls.get('Home') or info.get('home_page') or 'N/A'
        documentation_url = project_urls.get('Documentation') or 'N/A'
        requires_dist_list = info.get('requires_dist')
        requires_dist = ", ".join(requires_dist_list) if requires_dist_list else 'N/A'

        size_bytes = file_data.get('size')
        size_kb = f"{size_bytes / 1024:.2f} KB" if size_bytes is not None else 'N/A'

        upload_time_str = file_data.get('upload_time_iso_8601')
        formatted_upload_time = 'N/A'
        if upload_time_str:
            try:
                dt_object = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
                fmt = {"de": "%d.%m.%Y %H:%M:%S"}.get(self.current_lang, "%Y-%m-%d %H:%M:%S")
                formatted_upload_time = dt_object.strftime(fmt)
            except ValueError:
                formatted_upload_time = upload_time_str

        yanked = file_data.get('yanked', False)
        yanked_reason = file_data.get('yanked_reason', 'N/A')

        details_to_display = [
            ('info_name', info.get('name', 'N/A')),
            ('info_summary', description_text),
            ('info_package_url', package_url),
            ('info_documentation', documentation_url),
            ('info_dependencies', requires_dist),
            ('info_filename', file_data.get('filename', 'N/A')),
            ('info_md5', file_data.get('md5_digest', 'N/A')),
            ('info_sha256', file_data.get('digests', {}).get('sha256', 'N/A')),
            ('info_packagetype', file_data.get('packagetype', 'N/A')),
            ('info_python_version', file_data.get('python_version', 'N/A')),
            ('info_requires_python', file_data.get('requires_python', 'N/A')),
            ('info_size', size_kb),
            ('info_upload_time', formatted_upload_time),
            ('info_url', file_data.get('url', 'N/A')),
            ('info_yanked_status', str(yanked)),
        ]

        if yanked:
            details_to_display.append(('info_yanked_reason_full', yanked_reason, 'yanked_warning'))

        self._display_details_in_text_widget(
            self.search_info_text,
            details_to_display,
            url_labels=['info_package_url', 'info_documentation', 'info_url']
        )

    def install_selected_version(self):
        """Installiert die ausgewählte Version eines Pakets."""
        version_selection = self.search_versions_listbox.curselection()
        if not self.current_searched_pkg_name or not version_selection:
            messagebox.showwarning(
                self.t("install_frame_title"), self.t("select_package_version_first_msg")
            )
            return
        pkg_name = self.current_searched_pkg_name
        selected_filename = self.search_versions_listbox.get(version_selection[0])
        file_data = self.current_package_version_details_cache.get(selected_filename)
        if not file_data:
            messagebox.showerror(self.t("error_title"), self.t("select_package_version_first_msg"))
            return

        version_to_install = self.t("selected_version_fallback")
        try:
            _name, parsed_version, _build, _tags = packaging_utils.parse_wheel_filename(
                selected_filename)
            version_to_install = str(parsed_version)
        except packaging.utils.InvalidWheelFilename:
            if pkg_name in selected_filename:
                version_part = selected_filename.replace(pkg_name, "").lstrip("-").split(".tar.gz")[0]
                if version_part:
                    version_to_install = version_part

        self.log_message(self.t("log_version_select").format(pkg_name, version_to_install), "DEBUG")

        confirm_msg = self.t(
            "confirm_install").format(pkg_name=pkg_name, version=version_to_install)
        if messagebox.askyesno(self.t("install_frame_title"), confirm_msg):
            self.log_message(self.t("log_start_install").format(pkg_name, version_to_install))
            def do_install():
                _can_install, _required_packages, conflicts, cross_conflicts = self.resolve_dependencies(pkg_name, version_to_install)

                if conflicts or cross_conflicts:
                    proceed, action = self.show_dependency_conflict_dialog(
                        pkg_name, conflicts, cross_conflicts)
                    if not proceed:
                        self.log_message(
                            self.t("log_install_cancelled").format(
                                pkg_name, version_to_install), "INFO")
                        return

                    if action == 'upgrade_deps':
                        for pkg_name_conflict, _current_ver, required_spec in conflicts:
                            if required_spec:
                                req_string = f"{pkg_name_conflict}{required_spec}"
                                self.log_message(self.t("log_install_package").format(req_string))
                                self.run_pip_command(["install", req_string])
                            else:
                                self.log_message(
                                    self.t("log_upgrade_package").format(pkg_name_conflict))
                                self.run_pip_command(["install", "--upgrade", pkg_name_conflict])

                self.run_pip_command(
                    ["install", f"{pkg_name}=={version_to_install}"],
                    on_finish=self.refresh_package_list)

            threading.Thread(target=do_install, daemon=True).start()

    def _schedule_periodic_update(self, update_function, interval_ms):
        """Plant eine Funktion zur periodischen Ausführung."""
        def wrapper():
            try: # pylint: disable=unused-variable
                if self.root.winfo_exists():
                    update_function()
                    self._options_paths_after_id = self.root.after(interval_ms, wrapper)
            except (tk.TclError, RuntimeError):
                # Fenster wurde möglicherweise geschlossen
                pass
        # Starten Sie die erste Ausführung
        self._options_paths_after_id = self.root.after(interval_ms, wrapper)

    def _get_pip_cache_dir(self):
        """Ermittelt das Pip-Cache-Verzeichnis."""
        try:
            # Führen Sie den Befehl aus, um das Cache-Verzeichnis zu erhalten
            result = subprocess.run(
                [sys.executable, "-m", "pip", "cache", "dir"],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            return result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def _update_paths_listbox(self):
        """Aktualisiert die Listbox mit den wichtigen Pfaden."""
        new_entries = [] # pylint: disable=unused-variable

        # 1. Pip Cache Pfad
        pip_cache_path = self._get_pip_cache_dir()
        if pip_cache_path:
            label = self.t('options_paths_pypi_index') # pylint: disable=unused-variable
            entry = f"{label}: {pip_cache_path}" # pylint: disable=unused-variable
            new_entries.append(entry)

        # 2. Konfigurationsdatei-Pfad
        config_path = self.config_manager.config_path
        if os.path.exists(config_path):
            entry = (f"{self.t('options_paths_config_file')}: " +
                     config_path)
            new_entries.append(entry)

        # Nur aktualisieren, wenn sich etwas geändert hat
        if new_entries != self._options_path_entries:
            self._options_path_entries = new_entries
            self.tab3_paths_listbox.delete(0, tk.END)
            for entry in new_entries:
                self.tab3_paths_listbox.insert(tk.END, entry)

    def _format_venv_path(self, path):
        """Kürzt einen langen venv-Pfad auf einen signifikanten Teil."""
        from pathlib import Path
        if not path or path == "global":
            return self.t("global_environment_label")

        parts = Path(path).parts
        if len(parts) > 3:
            # z.B. '.../Projektname/subfolder/venv'
            return f".../{'/'.join(parts[-3:])}"
        return path

    def _update_venv_combobox_values(self):
        """Aktualisiert die Einträge im venv-Dropdown-Menü."""
        if not self.venv_combobox:
            return

        display_paths = [self.t(
            "global_environment_label")] + [self._format_venv_path(p) for p in self.venv_paths]
        self.venv_combobox['values'] = display_paths

        # Aktuelle Auswahl wiederherstellen oder auf Global setzen
        if self.selected_python_executable == sys.executable:
            self.venv_var.set(self.t("global_environment_label"))
        else:
            from pathlib import Path
            # Finde den passenden Anzeigepfad für den ausgewählten Executable-Pfad
            selected_venv_path = str(Path(self.selected_python_executable).parent.parent)
            formatted_selected = self._format_venv_path(selected_venv_path)
            if formatted_selected in display_paths:
                self.venv_var.set(formatted_selected)
            else:
                self.venv_var.set(self.t("global_environment_label"))

    def on_venv_selected(self, event=None):
        """Wird aufgerufen, wenn eine venv im Dropdown ausgewählt wird.""" # pylint: disable=unused-argument
        selected_display_path = self.venv_var.get()
        from pathlib import Path

        self.log_message(f"--- VENV SELECTION DIAGNOSTICS ---", "DEBUG")
        self.log_message(f"Selected display path: '{selected_display_path}'", "DEBUG")

        if selected_display_path == self.t("global_environment_label"):
            self.selected_python_executable = sys.executable
            self.log_message(f"Switched to global environment: {self.selected_python_executable}", "DEBUG")
        else:
            found_match = False
            # Finde den vollständigen Pfad basierend auf dem angezeigten Pfad
            for full_path in self.venv_paths:
                formatted_path = self._format_venv_path(full_path)
                self.log_message(f"Comparing with stored path: '{full_path}' (formatted: '{formatted_path}')", "DEBUG")
                if formatted_path == selected_display_path:
                    # Normalisiere den Pfad, um gemischte Slashes zu korrigieren
                    full_path = os.path.normpath(full_path)
                    self.log_message(f"MATCH FOUND! Using normalized full path: {full_path}", "DEBUG")

                    scripts_path = Path(full_path) / 'Scripts'
                    # Suche flexibel nach python.exe oder pythonw.exe
                    if (scripts_path / 'python.exe').exists():
                        self.selected_python_executable = str(scripts_path / 'python.exe')
                    elif (scripts_path / 'pythonw.exe').exists():
                        self.selected_python_executable = str(scripts_path / 'pythonw.exe')
                    else:
                        # Fallback, falls keine der beiden gefunden wird
                        self.selected_python_executable = str(scripts_path / 'python.exe')
                    found_match = True
                    break
            if not found_match:
                self.log_message(f"NO MATCH FOUND for '{selected_display_path}'. Keeping previous executable.", "ERROR")

        self.refresh_package_list()

    def find_venvs_in_path(self, search_path, progress_callback=None):
        """Durchsucht einen Pfad rekursiv nach venv-Ordnern."""
        found_venvs = []
        for root, dirs, files in os.walk(search_path):
            # Ignoriere häufige, große Ordner, um die Suche zu beschleunigen
            if progress_callback: # pylint: disable=unused-variable
                # Kürze den Pfad für eine bessere Anzeige
                display_path = root if len(root) < 70 else "..." + root[-67:] # pylint: disable=unused-variable
                progress_callback(display_path, len(found_venvs))
            dirs[:] = [d for d in dirs if d not in ['$RECYCLE.BIN',
                                                    'System Volume Information',
                                                    'node_modules', '.git']]

            if 'pyvenv.cfg' in files:
                # Wir haben einen venv-Ordner gefunden!
                # Der Pfad 'root' ist der Pfad zum venv-Ordner.
                found_venvs.append(root)

                # Nicht weiter in diesem Ordner suchen, um Zeit zu sparen
                dirs[:] = []

        return found_venvs

    def start_venv_search(self):
        """Startet die Suche nach venvs in einem Hintergrundthread."""
        search_directory = filedialog.askdirectory(title=self.t("find_venvs_title"))
        if not search_directory:
            return

        def update_progress_label(path, count): # pylint: disable=unused-variable
            """Sicheres Aktualisieren des GUI-Labels aus einem Thread."""
            status_text = (
                f"{self.t('venv_search_found_label').format(count)} | "
                f"{self.t('venv_search_path_label').format(path)}")
            if self.tab3_venv_search_status_label:
                self.root.after(
                    0, lambda: self.tab3_venv_search_status_label.config(text=status_text))

        def search_task():
            self.root.after(0, self.start_progress)
            self.log_message(self.t("log_searching_venvs").format(search_directory))

            try:
                venvs = self.find_venvs_in_path(
                    search_directory, progress_callback=update_progress_label)
                self.found_venvs_cache = venvs
                # Füge neue, einzigartige venvs zur Hauptliste hinzu und speichere
                newly_found = [v for v in venvs if v not in self.venv_paths]
                if newly_found:
                    self.venv_paths.extend(newly_found)
                    self.venv_paths.sort()
                    self._update_venv_combobox_values() # <-- HIER WIEDER EINGEFÜGT
                    self._save_venvs_to_config()
                self.root.after(0, lambda: self.show_found_venvs(venvs))
            finally:
                self.root.after(0, self.stop_progress)
                # Labels nach der Suche zurücksetzen
                if self.tab3_venv_search_status_label:
                    self.root.after(
                        1000, lambda: self.tab3_venv_search_status_label.config(text=""))
                self.log_message(self.t("log_venvs_found").format(len(self.found_venvs_cache)))

        threading.Thread(target=search_task, daemon=True).start()

    def show_found_venvs(self, venvs):
        """Zeigt die gefundenen venvs in einer Messagebox an."""
        if not venvs:
            messagebox.showinfo(
                self.t("venvs_found_title"), self.t("search_no_results").format("venv"))
            return
        self._update_venv_combobox_values()
        messagebox.showinfo(self.t("venvs_found_title"), "\n".join(venvs))

    def download_package_file(self):
        """Lädt die ausgewählte Paketversion herunter und speichert sie lokal."""
        version_selection = self.search_versions_listbox.curselection()
        if not self.current_searched_pkg_name or not version_selection:
            messagebox.showwarning(
                self.t("install_frame_title"), self.t("select_package_version_first_msg")
            )
            return
        selected_filename = self.search_versions_listbox.get(version_selection[0])
        file_data = self.current_package_version_details_cache.get(selected_filename)
        if not file_data:
            messagebox.showerror(self.t(
                "error_title"), self.t("version_details_not_found_msg")) # noqa: E501
            return

        download_url = file_data.get('url', '')
        if not download_url:
            messagebox.showerror(self.t("error_title"), self.t("download_url_not_available"))
            return

        save_path = filedialog.asksaveasfilename(
            title=self.t("download_version_title"),
            defaultextension=(".whl" if selected_filename.endswith(".whl")
                               else ".tar.gz"),
            initialfile=selected_filename,
            filetypes=[("Wheel files", "*.whl"),
                       ("Source distributions", "*.tar.gz"), ("All files", "*.*")]
        )

        if not save_path:
            return

        def progress_handler(progress_percentage):
            self.log_message(self.t("log_download_progress").format(progress_percentage))

        def do_download():
            try:
                self.log_message(self.t("log_download_url").format(download_url))
                self.pypi_api.download_package(download_url, save_path, progress_handler)
                self.log_message(self.t("log_download_success").format(save_path))
                messagebox.showinfo(self.t("install_frame_title"),
                                    self.t("download_success_message").format(save_path=save_path))
            except (requests.RequestException, OSError, IOError) as e:
                error_msg = self.t("download_failed").format(e=e)
                self.log_message(error_msg, "ERROR")
                messagebox.showerror(self.t("error_title"), error_msg)

        threading.Thread(target=do_download, daemon=True).start()

    # --- Sicherheitsprüfung ---

    def load_security_packages_check(self, pm=None):
        """Prüft Pakete auf Sicherheitslücken (silent check ohne Messageboxen)."""
        if not pm:
            pm = PackageManager(self.selected_python_executable, self.log_message)

        issues_str = pm.check_security()
        if issues_str:
            issues = issues_str.split("\n")
            self.security_packages_cache = []
            self.security_issues_cache = {}
            for issue in issues:
                if issue.strip():
                    parts = issue.split()
                    if parts:
                        pkg_name = parts[0]
                        if pkg_name not in self.security_packages_cache:
                            self.security_packages_cache.append(pkg_name)
                            self.security_issues_cache[pkg_name] = issue.strip()
        else:
            self.security_packages_cache = []
            self.security_issues_cache = {}

    def check_security_vulnerabilities(self):
        """Prüft installierte Pakete auf bekannte Sicherheitslücken."""
        self.log_message(self.t("security_check_message"))
        pm = PackageManager(self.selected_python_executable, self.log_message)
        issues_str = pm.check_security()

        if issues_str:
            issues = issues_str.split("\n")
            self.security_packages_cache = []
            self.security_issues_cache = {}
            for issue in issues:
                if issue.strip():
                    parts = issue.split()
                    if parts:
                        pkg_name = parts[0]
                        if pkg_name not in self.security_packages_cache:
                            self.security_packages_cache.append(pkg_name)
                            self.security_issues_cache[pkg_name] = issue.strip()
            msg = self.t("security_vulnerabilities_count").format(len(issues),
                                                                  len(self.security_packages_cache))
            self.log_message(msg, "WARNING")
            messagebox.showwarning(self.t("security_check_title"), msg)
            self.colorize_security_packages()
            return False

        self.security_packages_cache = []
        self.security_issues_cache = {}
        msg = self.t("security_no_vulnerabilities")
        self.log_message(msg)
        messagebox.showinfo(self.t("security_check_title"), msg)
        self.colorize_security_packages()
        return True

    # --- Update-Funktionalität ---

    def check_for_updates(self):
        """Prüft auf GitHub, ob eine neue Version des Skripts verfügbar ist."""
        def do_check():
            remote_version, new_content = self.pypi_api.check_app_update(self.version)
            if remote_version and new_content:
                self.log_message(
                    self.t("log_new_version_found").format(self.version, remote_version))
                self.remote_version = remote_version
                self.new_script_content = new_content
                self.root.after(0, self._show_update_dialog)
            elif remote_version is None: # Nur loggen, wenn kein Update gefunden wurde
                self.log_message(self.t("log_app_up_to_date"))
        threading.Thread(target=do_check, daemon=True).start()

    def _show_update_dialog(self):
        """Zeigt einen benutzerdefinierten Dialog für das Update an."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("update_title"))
        dialog.transient(self.root)
        dialog.grab_set()

        version_info = ""
        if self.remote_version:
            version_info = (f"Lokale Version: {self.version}\n"
                            f"Neue Version: {self.remote_version}")

        full_message = (f"{self.t('update_message')}\n\n{version_info}"
                        if version_info else self.t("update_message"))
        message = ttk.Label(dialog, text=full_message, wraplength=350, justify=tk.CENTER)
        message.pack(padx=20, pady=20)

        btn_frame = tk.Frame(dialog, relief=tk.FLAT, borderwidth=0)
        btn_frame.pack(pady=10)

        def handle_choice(choice):
            dialog.destroy()
            if choice == "now":
                self._handle_update_now()
            elif choice == "later":
                self._handle_update_later()
            elif choice == "no":
                self._handle_update_no()

        btn_now = ttk.Button(
            btn_frame, text=self.t("update_btn_now"), command=lambda: handle_choice("now"))
        btn_now.pack(side=tk.LEFT, padx=10)
        btn_later = ttk.Button(
            btn_frame, text=self.t("update_btn_later"), command=lambda: handle_choice("later"))
        btn_later.pack(side=tk.LEFT, padx=10)
        btn_no = ttk.Button(
            btn_frame, text=self.t("update_btn_no"), command=lambda: handle_choice("no"))
        btn_no.pack(side=tk.LEFT, padx=10)

    def _handle_update_now(self):
        self.log_message(self.t("log_applying_update"))
        if self._apply_update():
            self._restart_app()
        else:
            messagebox.showerror(
                self.t("error_title"), f"{self.t('update_failed')} {self.t('try_again_later')}")

    def _handle_update_later(self):
        self.log_message(self.t("log_update_on_exit"))
        self.update_on_exit = True
        messagebox.showinfo(self.t("update_title"), self.t("update_later_message"))

    def _handle_update_no(self):
        self.log_message(self.t("log_update_declined"))
        self.new_script_content = None

    def _apply_update(self):
        if not self.new_script_content:
            return False
        try:
            with open(self.script_path, "wb") as f:
                f.write(self.new_script_content)
            self.log_message(self.t("log_script_updated"))
            return True
        except IOError as e:
            self.log_message(self.t("log_update_write_failed").format(e), "ERROR")
            return False

    def _restart_app(self):
        self.log_message(self.t("log_restarting_app"))
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _on_closing(self):
        if self.update_on_exit:
            try:
                self.log_message(self.t("log_applying_on_exit"))
                if self._apply_update():
                    messagebox.showinfo(
                        self.t(
                            "update_title"
                            ), f"{self.t('update_successful')} {self.t('update_restart')}"
                    )
                    self.root.destroy()
                    self._restart_app()
                    return
            except (IOError, OSError) as e:
                messagebox.showerror(self.t("error_title"), f"{self.t('update_failed')}: {e}")
        self.root.destroy()


def get_available_python_versions():
    """Gibt eine Liste aller verfügbaren Python-Versionen zurück (Windows 'py' Launcher)."""
    try:
        result = subprocess.run(["py", "-0p"], capture_output=True, text=True, check=False)
        versions = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and not line.lower().startswith('requested'):
                versions.append(line)
        return versions
    except FileNotFoundError:
        return []

def select_python_version():
    """Zeigt einen Dialog zur Auswahl der Python-Version und startet das Programm mit dieser neu."""
    env_var = os.environ.get("PIP_MANAGER_PYTHON_SELECTED")
    if env_var == "1":
        return

    versions = get_available_python_versions()
    if not versions or len(versions) <= 1:
        return

    root_temp = tk.Tk()
    root_temp.title(LANG_TEXTS["de"]["select_python_title"])
    root_temp.geometry("350x200")
    root_temp.resizable(False, False)

    label = tk.Label(
        root_temp, text=LANG_TEXTS["de"]["label_select_python"],
        font=("Arial", 10, "bold"))
    label.pack(pady=10)

    selected_version = tk.StringVar(value=versions[0])

    frame = tk.Frame(root_temp)
    frame.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)

    for version in versions:
        rb = tk.Radiobutton(
            frame, text=version, variable=selected_version,
            value=version, font=("Arial", 9))
        rb.pack(anchor=tk.W, pady=3)

    button_frame = tk.Frame(root_temp)
    button_frame.pack(pady=10)

    def on_ok():
        if selected_version.get():
            env = os.environ.copy()
            env["PIP_MANAGER_PYTHON_SELECTED"] = "1"
            try:
                version_str = selected_version.get()
                version_num = version_str.split()[0]
                subprocess.Popen(["py", version_num, __file__], env=env)
                sys.exit(0)
            except OSError:
                pass
        root_temp.destroy()

    def on_cancel():
        root_temp.destroy()
        sys.exit(0)

    ok_btn = tk.Button(button_frame, text=LANG_TEXTS["de"]["btn_ok"], width=10, command=on_ok)
    ok_btn.pack(side=tk.LEFT, padx=5)

    cancel_btn = tk.Button(
        button_frame, text=LANG_TEXTS["de"]["btn_cancel"],
        width=10, command=on_cancel)
    cancel_btn.pack(side=tk.LEFT, padx=5)

    root_temp.protocol("WM_DELETE_WINDOW", on_cancel)
    root_temp.mainloop()

if __name__ == "__main__":
    select_python_version()
    main_root = tk.Tk()
    app = PipPackageManager(main_root)
    main_root.mainloop()
