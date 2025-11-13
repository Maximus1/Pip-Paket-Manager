import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import sys
import importlib.metadata
import os
import datetime
import queue
# Adminmodus-Erkennung: erlaubt direkte Deinstallation bei --uninstall-admin
if "--uninstall-admin" in sys.argv:
    try:
        pkg_index = sys.argv.index("--uninstall-admin") + 1
        pkg_name = sys.argv[pkg_index]
        subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", pkg_name])
    except Exception as e:
        print(f"Fehler bei der Admin-Deinstallation: {e}")
    sys.exit(0)
# --- Sprachtexte ---
LANG_TEXTS = {
    "de": {"title": "Pip Paket-Manager", "status_loading": "Pakete werden geladen…",
           "status_loaded": "{} Pakete geladen.", "btn_uninstall": "Deinstallieren",
           "btn_update": "Update", "btn_reinstall": "Reinstallieren", "btn_refresh": "Liste aktualisieren",
           "confirm_uninstall": "Soll '{}' wirklich deinstalliert werden?",
           "no_info": "Keine Informationen gefunden.",
           "loading_info": "Lade Informationen für '{}'…",
           "btn_install_deps": "Abhängigkeiten installieren",
           "btn_show_log": "Log anzeigen",
           "log_title": "Pip-Ausgabe",
           "missing_deps_info": "Fehlende Abhängigkeiten: {}",
           "update_available": "Update verfügbar: {} -> {}",
           "install_time": "Installationszeit (aus .dist-info): {}",
           "no_install_time": "Installationszeit: nicht ermittelbar (keine .dist-info gefunden)",
           "lang_label": "Sprache:",
           "frame_left_title": "Pakete",
           "frame_right_title": "Informationen"},
    "en": {"title": "Pip Package Manager", "status_loading": "Loading packages…",
           "status_loaded": "{} packages loaded.", "btn_uninstall": "Uninstall",
           "btn_update": "Update", "btn_reinstall": "Reinstall", "btn_refresh": "Refresh list",
           "confirm_uninstall": "Really uninstall '{}'?", "no_info": "No information found.",
           "loading_info": "Loading info for '{}' …", "btn_install_deps": "Install Dependencies",
           "missing_deps_info": "Missing Dependencies: {}",
           "btn_show_log": "Show Log",
           "log_title": "Pip Output",
           "update_available": "Update available: {} -> {}",
           "install_time": "Install time (from .dist-info): {}",
           "no_install_time": "Install time: not available (no .dist-info found)", "lang_label": "Language:",
           "frame_left_title": "Packages",
           "frame_right_title": "Information"},
    "fr": {"title": "Gestionnaire de paquets Pip", "status_loading": "Chargement des paquets…",
           "status_loaded": "{} paquets chargés.", "btn_uninstall": "Désinstaller",
           "btn_update": "Mettre à jour", "btn_reinstall": "Réinstaller", "btn_refresh": "Actualiser la liste",
           "confirm_uninstall": "Voulez-vous vraiment désinstaller '{}' ?",
           "no_info": "Aucune information trouvée.",
           "loading_info": "Chargement des informations sur '{}' …",
           "missing_deps_info": "Dépendances manquantes: {}",
           "btn_show_log": "Afficher le journal",
           "log_title": "Sortie de Pip",
           "update_available": "Mise à jour disponible: {} -> {}",
           "btn_install_deps": "Installer les dépendances",
           "install_time": "Heure d’installation (.dist-info): {}",
           "no_install_time": "Heure d’installation introuvable (pas de .dist-info)", "lang_label": "Langue :",
           "frame_left_title": "Paquets",
           "frame_right_title": "Informations"},
    "es": {"title": "Administrador de paquetes Pip", "status_loading": "Cargando paquetes…",
           "status_loaded": "{} paquetes cargados.", "btn_uninstall": "Desinstalar",
           "btn_update": "Actualizar", "btn_reinstall": "Reinstalar", "btn_refresh": "Actualizar lista",
           "confirm_uninstall": "¿Realmente desea desinstalar '{}'?", "no_info": "No se encontró información.",
           "loading_info": "Cargando información para '{}' …",
           "install_time": "Hora de instalación (.dist-info): {}",
           "missing_deps_info": "Dependencias faltantes: {}",
           "update_available": "Actualización disponible: {} -> {}",
           "btn_show_log": "Mostrar registro",
           "log_title": "Salida de Pip",
           "no_install_time": "Hora de instalación no disponible (sin .dist-info)", "lang_label": "Idioma:",
           "btn_install_deps": "Instalar dependencias"},
    "zh": {"title": "Pip 软件包管理器", "status_loading": "正在加载软件包…",
           "status_loaded": "已加载 {} 个软件包。", "btn_uninstall": "卸载", "btn_update": "更新",
           "btn_reinstall": "重新安装", "btn_refresh": "刷新列表", "confirm_uninstall": "确定要卸载 '{}' 吗？",
           "no_info": "未找到信息。", "loading_info": "正在加载 '{}' 的信息…",
           "install_time": "安装时间 (.dist-info): {}", "no_install_time": "无法确定安装时间（没有 .dist-info）",
           "btn_show_log": "显示日志",
           "log_title": "Pip 输出",
           "update_available": "可用更新: {} -> {}",
           "missing_deps_info": "缺少依赖: {}",
           "lang_label": "语言：",
           "frame_left_title": "软件包",
           "frame_right_title": "信息"},
    "ja": {"title": "Pip パッケージマネージャー", "status_loading": "パッケージを読み込み中…",
           "status_loaded": "{} 個のパッケージを読み込みました。", "btn_uninstall": "アンインストール",
           "btn_update": "更新", "btn_reinstall": "再インストール", "btn_refresh": "リストを更新",
           "confirm_uninstall": "'{}' を本当にアンインストールしますか？", "no_info": "情報が見つかりません。",
           "loading_info": "'{}' の情報を読み込み中…", "install_time": "インストール日時 (.dist-info): {}",
           "no_install_time": "インストール日時を取得できません（.dist-info がありません）", "lang_label": "言語："}
}

current_lang = "de"
log_records = []

def log_message(message, level="INFO"):
    """Fügt eine Nachricht zum In-Memory-Log hinzu."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_records.append(f"{timestamp} [{level}] {message}")

def t(key): return LANG_TEXTS[current_lang][key]

# --- GUI Aufbau ---
root = tk.Tk()
root.title(t("title"))
root.geometry("950x650")  # etwas höher für Versionsfeld

# Linke Spalte – Paketliste
frame_left = ttk.LabelFrame(root, text=t("frame_left_title"))
frame_left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
package_listbox = tk.Listbox(frame_left, width=50)
package_listbox.pack(side=tk.LEFT, fill=tk.Y)
scrollbar = ttk.Scrollbar(frame_left, orient="vertical", command=package_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
package_listbox.config(yscrollcommand=scrollbar.set)

# Mittlere Spalte – Buttons + Sprache
frame_middle = ttk.Frame(root)
frame_middle.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

lang_frame = ttk.Frame(frame_middle)
lang_frame.pack(side=tk.TOP, pady=5)
lang_label = ttk.Label(lang_frame, text=t("lang_label"))
lang_label.pack(side=tk.LEFT, padx=5)
lang_var = tk.StringVar(value="Deutsch")
lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, state="readonly",
                          values=["Deutsch", "English", "Français", "Español", "中文", "日本語"], width=12)
lang_combo.pack(side=tk.LEFT)

btn_frame = ttk.LabelFrame(frame_middle, text="Aktionen")
btn_frame.pack(pady=20, padx=5)

# Label für Update-Informationen
update_info_label = tk.Label(frame_middle, height=6,text="", foreground="blue", justify=tk.CENTER, wraplength=180)
update_info_label.pack(pady=10)
update_info_label.pack_forget() # Standardmäßig ausblenden

log_window = None
def show_log_window():
    """Erstellt und zeigt das Log-Fenster an."""
    global log_window
    if log_window and log_window.winfo_exists():
        log_window.lift()
        return

    log_window = tk.Toplevel(root)
    log_window.title(t("log_title"))
    log_window.geometry("800x500")

    log_text_widget = tk.Text(log_window, wrap=tk.WORD, font=("Courier New", 9))
    log_scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=log_text_widget.yview)
    log_text_widget.config(yscrollcommand=log_scrollbar.set)
    
    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_text_widget.insert(tk.END, "\n".join(log_records))
    log_text_widget.see(tk.END)

def run_pip_command(command_list):
    """Führt einen Pip-Befehl aus und zeigt den Fortschritt im Info-Label an."""
    
    def update_label(text):
        """Sichere Funktion zum Aktualisieren des Labels aus dem Hauptthread."""
        update_info_label.config(text=text)
        update_info_label.pack(pady=10) # Sicherstellen, dass es sichtbar ist

    # Startmeldung im Label anzeigen
    start_msg = f"Running: pip {' '.join(command_list)}..."
    log_message(start_msg)
    root.after(0, lambda: update_label(start_msg))
    
    process = subprocess.Popen([sys.executable, "-m", "pip"] + command_list,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')
    
    for line in iter(process.stdout.readline, ''):
        # Jede Zeile der Ausgabe im Label anzeigen
        cleaned_line = line.strip()
        log_message(cleaned_line, level="PIP")
        if cleaned_line:
            root.after(0, lambda l=cleaned_line: update_label(l))
    
    process.stdout.close()
    process.wait()
    # Abschlussmeldung im Label anzeigen
    end_msg = f"Finished with exit code {process.returncode}"
    log_message(end_msg, level="STATUS")
    root.after(0, lambda: update_label(end_msg))
import ctypes

def is_admin():
    """Prüft, ob das aktuelle Python mit Administratorrechten läuft."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_package_path(pkg_name):
    """Gibt den Installationspfad eines Pakets zurück."""
    try:
        dist = importlib.metadata.distribution(pkg_name)
        return str(dist.locate_file(''))
    except importlib.metadata.PackageNotFoundError:
        return ""
# --- Buttons ---
def uninstall_package(pkg_name):
    if not pkg_name:
        return

    confirm = messagebox.askyesno(t("btn_uninstall"), t("confirm_uninstall").format(pkg_name))
    if not confirm:
        return

    pkg_path = get_package_path(pkg_name)
    needs_admin = pkg_path.lower().startswith(r"c:\program files")

    if needs_admin and not is_admin():
        log_message(f"Adminrechte erforderlich für Deinstallation von {pkg_name} ({pkg_path})")
        messagebox.showinfo("Administratorrechte", f"Für '{pkg_name}' sind Administratorrechte erforderlich.")
        # Startet sich selbst mit Adminrechten und übergibt das Paket
        subprocess.run([
            "powershell", "Start-Process", sys.executable,
            "-ArgumentList", f'"{__file__}" --uninstall-admin "{pkg_name}"',
            "-Verb", "runAs"
        ])
        return

    # Wenn Adminrechte vorhanden oder nicht erforderlich: direkt deinstallieren
    threading.Thread(target=run_pip_command, args=(["uninstall", "-y", pkg_name],), daemon=True).start()


def update_package(pkg_name):
    if not pkg_name: return
    threading.Thread(target=run_pip_command, args=(["install", "--upgrade", pkg_name],), daemon=True).start()

def reinstall_package(pkg_name):
    if not pkg_name: return
    threading.Thread(target=run_pip_command, args=(["install", "--force-reinstall", "--no-deps", pkg_name],), daemon=True).start()

def install_dependencies(deps_to_install):
    if not deps_to_install: return
    threading.Thread(target=run_pip_command, args=(["install"] + deps_to_install,), daemon=True).start()

def refresh_package_list():
    package_listbox.delete(0, tk.END)
    log_message("Refreshing package list...")
    threading.Thread(target=load_packages, daemon=True).start()

btn_uninstall = ttk.Button(btn_frame, text=t("btn_uninstall"), width=25,
                           command=lambda: uninstall_package(package_listbox.get(tk.ACTIVE)))
btn_uninstall.pack(fill=tk.X, pady=2)
btn_update = ttk.Button(btn_frame, text=t("btn_update"), width=25,
                        command=lambda: update_package(package_listbox.get(tk.ACTIVE)))
btn_update.pack(fill=tk.X, pady=2)
btn_reinstall = ttk.Button(btn_frame, text=t("btn_reinstall"), width=25,
                           command=lambda: reinstall_package(package_listbox.get(tk.ACTIVE)))
btn_reinstall.pack(fill=tk.X, pady=2)
btn_refresh = ttk.Button(btn_frame, text=t("btn_refresh"), width=25, command=refresh_package_list)
btn_refresh.pack(fill=tk.X, pady=5)

btn_install_deps = ttk.Button(btn_frame, text=t("btn_install_deps"), width=25, state=tk.DISABLED)
btn_install_deps.pack(fill=tk.X, pady=10)

btn_show_log = ttk.Button(btn_frame, text=t("btn_show_log"), command=show_log_window)
btn_show_log.pack(fill=tk.X, pady=5)

# Rechte Spalte – Infofeld + Versionsfeld
frame_right = ttk.LabelFrame(root, text=t("frame_right_title"))
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

info_text = tk.Text(frame_right, wrap=tk.WORD)
info_text.pack(fill=tk.BOTH, expand=True)

# Python-Versionen unterhalb Infofeld
version_frame = ttk.LabelFrame(frame_right, text="Installierte Python-Versionen")
version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
version_text = tk.Text(version_frame, height=6, wrap=tk.NONE, font=("Courier New", 10))
version_text.pack(fill=tk.X, padx=2, pady=2)

# Statuslabel
status_label = ttk.Label(root, text=t("status_loading"))
status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

# --- Datenfunktionen ---
def get_installed_packages():
    global installed_packages_cache
    result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"],
                            capture_output=True, text=True)
    packages = sorted([line.split("==")[0] for line in result.stdout.splitlines()], key=str.lower)
    installed_packages_cache = packages  # Cache direkt hier füllen
    return packages

def load_outdated_packages():
    """Lädt die Liste der veralteten Pakete und speichert sie im Cache."""
    global outdated_packages_cache
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"],
                                capture_output=True, text=True)
        outdated_list = {}
        # Die ersten beiden Zeilen (Header) überspringen
        for line in result.stdout.splitlines()[2:]:
            parts = line.split()
            if len(parts) >= 3:
                outdated_list[parts[0]] = {"current": parts[1], "latest": parts[2]}
        outdated_packages_cache = outdated_list
    except Exception as e:
        print(f"Fehler beim Prüfen auf veraltete Pakete: {e}")

def get_required_by(pkg_name):
    """
    Findet alle installierten Pakete, die von `pkg_name` abhängen.
    Dies ist die programmatische Entsprechung zum 'Required-by'-Feld von 'pip show'.
    """
    requiring_packages = []
    # Normalisiere den Paketnamen für den Vergleich (ersetzt '_' durch '-')
    normalized_pkg_name = pkg_name.replace("_", "-").lower()

    for dist in importlib.metadata.distributions():
        if dist.requires:
            for req in dist.requires:
                # Extrahiere den Namen der Anforderung (z.B. 'requests' aus 'requests>=2.0')
                req_name = req.split(' ')[0].split('[')[0].split(';')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                if req_name.replace("_", "-").lower() == normalized_pkg_name:
                    requiring_packages.append(dist.metadata['name'])
    return sorted(requiring_packages, key=str.lower)

def get_package_info(pkg_name):
    """Liest Paketinformationen direkt über importlib.metadata, ohne pip show aufzurufen."""
    try:
        dist = importlib.metadata.distribution(pkg_name)
        metadata = dist.metadata

        # Baue einen String, der der Ausgabe von 'pip show' ähnelt
        info_lines = [
            f"Name: {metadata.get('Name', 'N/A')}",
            f"Version: {metadata.get('Version', 'N/A')}",
            f"Summary: {metadata.get('Summary', 'N/A')}",
            f"Home-page: {metadata.get('Home-page', 'N/A')}",
            f"Author: {metadata.get('Author', 'N/A')}",
            f"License: {metadata.get('License', 'N/A')}",
            f"Location: {dist.locate_file('')}",
            f"Requires: {', '.join(dist.requires) if dist.requires else ''}",
            f"Required-by: {', '.join(get_required_by(pkg_name))}"
        ]
        return "\n".join(info_lines)
    except importlib.metadata.PackageNotFoundError:
        return t("no_info")

def get_install_time(pkg_name):
    try:
        dist = importlib.metadata.distribution(pkg_name)
        path = dist.locate_file('')
        if path and os.path.exists(path):
            ts = os.path.getmtime(path)
            return datetime.datetime.fromtimestamp(ts)
    except Exception:
        pass
    return None

def update_listbox_safely(packages):
    """Aktualisiert die Listbox sicher aus dem Haupt-GUI-Thread."""
    package_listbox.delete(0, tk.END)
    for pkg in packages:
        package_listbox.insert(tk.END, pkg)
    status_label.config(text=t("status_loaded").format(len(packages)))

def load_packages():
    """Lädt Pakete in einem Hintergrundthread und aktualisiert die GUI sicher."""
    log_message("Loading package lists...")
    try:
        # Lade zuerst die Update-Infos, da dies am längsten dauert.
        load_outdated_packages()
        packages = get_installed_packages()

        # GUI-Update im Hauptthread planen
        root.after(0, lambda: update_listbox_safely(packages))
    except Exception as e:
        log_message(f"Error loading packages: {e}", level="ERROR")
        status_label.config(text=f"Fehler: {e}")

def show_package_info(event):
    selection = package_listbox.curselection()
    if not selection: return
    pkg_name = package_listbox.get(selection[0])
    info_text.delete("1.0", tk.END)
    log_message(f"Fetching info for '{pkg_name}'")
    info_text.insert(tk.END, t("loading_info").format(pkg_name) + "\n")

    def fetch_and_show():
        # Zuerst den Button deaktivieren
        root.after(0, lambda: btn_install_deps.config(state=tk.DISABLED, command=None))
        global outdated_packages_cache # Stelle sicher, dass die globale Variable bekannt ist
        root.after(0, lambda: update_info_label.pack_forget()) # Update-Label ausblenden

        info = get_package_info(pkg_name)
        install_time = get_install_time(pkg_name)

        # Fehlende Abhängigkeiten prüfen
        dist = importlib.metadata.distribution(pkg_name)
        missing_deps = []
        if dist.requires:
            # Normalisiere die Liste der installierten Pakete für einen robusten Vergleich
            # (kleingeschrieben, Unterstriche durch Bindestriche ersetzt)
            installed_normalized = {p.lower().replace("_", "-") for p in installed_packages_cache}
            for req in dist.requires:
                req_name = req.split(' ')[0].split('[')[0].split(';')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                # Normalisiere auch den Anforderungsnamen auf die gleiche Weise
                if req_name.lower().replace("_", "-") not in installed_normalized:
                    missing_deps.append(req_name)

        if missing_deps:
            root.after(0, lambda: btn_install_deps.config(state=tk.NORMAL, command=lambda: install_dependencies(missing_deps)))

        # Update-Informationen prüfen und anzeigen
        if pkg_name in outdated_packages_cache:
            update_info = outdated_packages_cache[pkg_name]
            update_text = t("update_available").format(update_info['current'], update_info['latest'])
            root.after(0, lambda: update_info_label.config(text=update_text))
            root.after(0, lambda: update_info_label.pack(pady=10))

        info_text.delete("1.0", tk.END)
        info_text.insert(tk.END, info + "\n\n")
        if install_time:
            # Datum entsprechend der Sprache formatieren
            if current_lang == "de":
                fmt = "%d.%m.%Y %H:%M:%S"
            elif current_lang == "en":
                fmt = "%Y-%m-%d %H:%M:%S"
            elif current_lang == "fr":
                fmt = "%d/%m/%Y %H:%M:%S"
            elif current_lang == "es":
                fmt = "%d/%m/%Y %H:%M:%S"
            elif current_lang == "zh":
                fmt = "%Y-%m-%d %H:%M:%S"
            elif current_lang == "ja":
                fmt = "%Y/%m/%d %H:%M:%S"
            info_text.insert(tk.END, "\n" + t("install_time").format(install_time.strftime(fmt)) + "\n")
        else:
            info_text.insert(tk.END, "\n" + t("no_install_time") + "\n")

        if missing_deps:
            info_text.insert(tk.END, t("missing_deps_info").format(", ".join(missing_deps)) + "\n")

    threading.Thread(target=fetch_and_show, daemon=True).start()

# --- Python-Versionen laden ---
def load_python_versions():
    version_text.delete("1.0", tk.END)
    try:
        result = subprocess.run(["py", "-0p"], capture_output=True, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                cleaned = " ".join(line.split())
                version_text.insert(tk.END, cleaned + "\n")
        else:
            version_text.insert(tk.END, "Python-Launcher nicht gefunden.\n")
    except FileNotFoundError:
        version_text.insert(tk.END, "Python-Launcher nicht installiert.\n")

# --- Sprache wechseln ---
def change_language(event=None):
    global current_lang
    sel = lang_var.get()
    if sel == "Deutsch": current_lang = "de"
    elif sel == "English": current_lang = "en"
    elif sel == "Français": current_lang = "fr"
    elif sel == "Español": current_lang = "es"
    elif sel == "中文": current_lang = "zh"
    elif sel == "日本語": current_lang = "ja"

    root.title(t("title"))
    lang_label.config(text=t("lang_label"))
    btn_uninstall.config(text=t("btn_uninstall"))
    btn_update.config(text=t("btn_update"))
    btn_reinstall.config(text=t("btn_reinstall"))
    btn_refresh.config(text=t("btn_refresh"))
    frame_left.config(text=t("frame_left_title"))
    frame_right.config(text=t("frame_right_title"))
    btn_show_log.config(text=t("btn_show_log"))
    btn_install_deps.config(text=t("btn_install_deps"))
    status_label.config(text=t("status_loading"))

lang_combo.bind("<<ComboboxSelected>>", change_language)
package_listbox.bind("<<ListboxSelect>>", show_package_info)

log_message("Application started.")

# --- Threads starten ---
threading.Thread(target=load_packages, daemon=True).start()
threading.Thread(target=load_python_versions, daemon=True).start()

root.mainloop()
