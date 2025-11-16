"""
Ein GUI-Tool zur Verwaltung von Python-Paketen mit Pip, das eine grafische
Oberfläche für die Installation, Deinstallation, Aktualisierung und Suche von
Paketen bietet.
"""
# pylint: disable=invalid-name
# --- Bootstrap: Abhängigkeiten prüfen und installieren ---
import subprocess
import sys
import importlib.metadata

def check_and_install_dependencies():
    """Prüft, ob alle benötigten Pakete installiert sind, und installiert sie bei Bedarf."""
    required_packages = ["requests", "Pillow", "packaging", "beautifulsoup4"]
    missing_packages = []

    for package in required_packages:
        try:
            importlib.metadata.distribution(package)
        except importlib.metadata.PackageNotFoundError:
            missing_packages.append(package)

    if missing_packages:
        print(f"Folgende benötigte Pakete fehlen: {', '.join(missing_packages)}")
        print("Versuche, die fehlenden Pakete mit pip zu installieren...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])
            print("\nInstallation abgeschlossen. Bitte starten Sie das Skript erneut.")
        except subprocess.CalledProcessError as e:
            print(f"\nFehler bei der Installation der Pakete: {e}")
            print("Bitte installieren Sie die Pakete manuell mit: pip install " + " ".join(missing_packages))
        sys.exit()
check_and_install_dependencies()
# --- Standard-Bibliothek ---
import ctypes
import datetime
import importlib.metadata
import os
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from tkinter import ttk, messagebox

# --- Drittanbieter-Bibliotheken ---
import requests
from PIL import Image, ImageTk
import packaging.version
import packaging.tags
from packaging import utils as packaging_utils

# --- Sprachtexte ---
LANG_TEXTS = {
    "de": {
        "title": "Pip Paket-Manager",
        "status_loading": "Pakete werden geladen…",
        "status_loaded": "{} Pakete geladen.",
        "btn_uninstall": "Deinstallieren",
        "btn_update": "Update",
        "btn_reinstall": "Reinstallieren",
        "btn_refresh": "Liste aktualisieren",
        "confirm_uninstall": "Soll '{}' wirklich deinstalliert werden?",
        "no_info": "Keine Informationen gefunden.",
        "install_frame_title": "Installation",
        "loading_info": "Lade Informationen für '{}'…",
        "btn_install_deps": "Abhängigkeiten installieren",
        "btn_show_log": "Log anzeigen",
        "log_title": "Pip-Ausgabe",
        "missing_deps_info": "Fehlende Abhängigkeiten: {}",
        "btn_install_selected_version": "Ausgewählte Version installieren",
        "update_available": "Update verfügbar: {} -> {}",
        "install_time": "Installationszeit (aus .dist-info): {}",
        "confirm_install": "Möchten Sie '{pkg_name}=={version}' installieren?",
        "no_install_time": "Installationszeit: nicht ermittelbar (keine .dist-info gefunden)",
        "lang_label": "Sprache:",
        "frame_left_title": "Installierte Pakete",
        "frame_right_title": "Informationen (Lokal)",
        "actions_frame_title": "Aktionen",
        "homepage_tooltip": "PyPi Homepage besuchen",
        "search_searching": "Suche läuft...",
        "search_no_results": "Keine Ergebnisse für '{}' gefunden.",
        "search_error": "Fehler bei der Suche: {}",
        "info_latest_version": "Neueste Version",
        "info_dependencies": "Abhängigkeiten",
        "tab_manage": "Paketverwaltung",
        "tab_search": "Suche",
        "search_label": "Paket auf PyPI suchen:",
        "search_button": "Suchen",
        "search_results_title": "Suchergebnisse",
        "search_info_title": "Paketdetails (Online)",
        "search_versions_title": "Verfügbare Versionen",
        "search_no_compatible_versions": "Keine kompatiblen Versionen gefunden.",
        "python_versions_title": "Installierte Python-Versionen",
        "status_checking_updates": "Suche nach veralteten Paketen…",
        "status_loading_installed": "Lade installierte Pakete…",
        "status_loading_index": "Lade PyPI-Paketindex...",
        "progress_frame_title": "Fortschritt",
        "admin_rights_title": "Administratorrechte",
        "admin_rights_required_msg": "Für '{pkg_name}' sind Administratorrechte erforderlich.",
        "selection_required_title": "Auswahl erforderlich",
        "select_python_version_msg": "Bitte wählen Sie zuerst eine Python-Version aus der Liste aus.",
        "enter_package_name_prompt": "Geben Sie den Paketnamen für Python {version_tag_display} ein:",
        "selected_version_fallback": "ausgewählte Version",
        "select_package_version_first_msg": "Bitte wählen Sie zuerst eine Version aus der Versionsliste aus.",
        "error_title": "Fehler",
        "version_details_not_found_msg": "Konnte Details zur ausgewählten Version nicht finden.",
        "info_name": "Name", "info_version": "Version", "info_summary": "Zusammenfassung", "info_homepage": "Homepage",
        "info_author": "Autor", "info_license": "Lizenz", "info_location": "Speicherort", "info_requires": "Benötigt", "info_release_date": "Release-Datum",
        "info_yanked": "WARNUNG: Diese Version wurde zurückgezogen!", "info_yanked_reason": "Grund",
        "info_required_by": "Benötigt von","info_package_url": "Paket-URL", "info_documentation": "Dokumentation", "info_filename": "Dateiname",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Pakettyp", "info_python_version": "Python-Version",
        "info_requires_python": "Benötigt Python", "info_size": "Größe", "info_upload_time": "Upload-Zeit", "info_url": "URL",
        "info_yanked_status": "Zurückgezogen", "info_yanked_reason_full": "Grund für Zurückziehung"
    },
    "en": {
        "title": "Pip Package Manager",
        "status_loading": "Loading packages…",
        "status_loaded": "{} packages loaded.",
        "btn_uninstall": "Uninstall",
        "btn_update": "Update",
        "btn_reinstall": "Reinstall",
        "btn_refresh": "Refresh list",
        "confirm_uninstall": "Really uninstall '{}'?",
        "no_info": "No information found.",
        "install_frame_title": "Installation",
        "loading_info": "Loading info for '{}' …",
        "btn_install_deps": "Install Dependencies",
        "btn_show_log": "Show Log",
        "log_title": "Pip Output",
        "missing_deps_info": "Missing Dependencies: {}",
        "btn_install_selected_version": "Install Selected Version",
        "confirm_install": "Do you want to install '{pkg_name}=={version}'?",
        "update_available": "Update available: {} -> {}",
        "install_time": "Install time (from .dist-info): {}",
        "no_install_time": "Install time: not available (no .dist-info found)",
        "lang_label": "Language:",
        "frame_left_title": "Installed Packages",
        "frame_right_title": "Information (Local)",
        "actions_frame_title": "Actions",
        "homepage_tooltip": "Visit PyPI homepage",
        "search_versions_title": "Available Versions",
        "search_no_compatible_versions": "No compatible versions found.",
        "search_searching": "Searching...",
        "search_no_results": "No results found for '{}'.",
        "search_error": "Search error: {}",
        "info_latest_version": "Latest Version",
        "info_dependencies": "Dependencies",
        "tab_manage": "Package Management",
        "tab_search": "Search",
        "search_label": "Search for package on PyPI:",
        "progress_frame_title": "Progress",
        "search_button": "Search",
        "search_results_title": "Search Results",
        "search_info_title": "Package Details (Online)",
        "admin_rights_title": "Administrator Rights",
        "admin_rights_required_msg": "Administrator rights are required for '{pkg_name}'.",
        "selection_required_title": "Selection Required",
        "select_python_version_msg": "Please select a Python version from the list first.",
        "enter_package_name_prompt": "Enter the package name for Python {version_tag_display}:",
        "selected_version_fallback": "selected version",
        "select_package_version_first_msg": "Please select a version from the version list first.",
        "error_title": "Error",
        "version_details_not_found_msg": "Could not find details for the selected version.",
        "python_versions_title": "Installed Python Versions",
        "status_checking_updates": "Checking for outdated packages…",
        "status_loading_installed": "Loading installed packages…",
        "info_name": "Name", "info_version": "Version", "info_summary": "Summary", "info_homepage": "Home-page",
        "info_author": "Author", "info_license": "License", "info_location": "Location", "info_requires": "Requires", "info_release_date": "Release Date",
        "info_yanked": "WARNING: This version has been yanked!", "info_yanked_reason": "Reason", # Keep these for local info
        "info_required_by": "Required-by","info_package_url": "Package URL", "info_documentation": "Documentation", "info_filename": "Filename",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Package Type", "info_python_version": "Python Version",
        "info_requires_python": "Requires Python", "info_size": "Size", "info_upload_time": "Upload Time", "info_url": "URL",
        "info_yanked_status": "Yanked", "info_yanked_reason_full": "Yanked Reason"
    },
    "fr": {
        "title": "Gestionnaire de paquets Pip",
        "status_loading": "Chargement des paquets…",
        "status_loaded": "{} paquets chargés.",
        "btn_uninstall": "Désinstaller",
        "btn_update": "Mettre à jour",
        "btn_reinstall": "Réinstaller",
        "btn_refresh": "Actualiser la liste",
        "confirm_uninstall": "Voulez-vous vraiment désinstaller '{}' ?",
        "no_info": "Aucune information trouvée.",
        "install_frame_title": "Installation",
        "loading_info": "Chargement des informations sur '{}' …",
        "btn_install_deps": "Installer les dépendances",
        "btn_show_log": "Afficher le journal",
        "log_title": "Sortie de Pip",
        "missing_deps_info": "Dépendances manquantes: {}",
        "btn_install_selected_version": "Installer la version sélectionnée",
        "confirm_install": "Voulez-vous installer '{pkg_name}=={version}' ?",
        "update_available": "Mise à jour disponible: {} -> {}",
        "install_time": "Heure d’installation (.dist-info): {}",
        "no_install_time": "Heure d’installation introuvable (pas de .dist-info)",
        "lang_label": "Langue :",
        "frame_left_title": "Paquets Installés",
        "frame_right_title": "Informations (Local)",
        "actions_frame_title": "Actions",
        "homepage_tooltip": "Visiter la page d'accueil de PyPI",
        "search_versions_title": "Versions disponibles",
        "search_no_compatible_versions": "Aucune version compatible trouvée.",
        "search_searching": "Recherche en cours...",
        "search_no_results": "Aucun résultat pour '{}'.",
        "search_error": "Erreur de recherche: {}",
        "info_latest_version": "Dernière version",
        "info_dependencies": "Dépendances",
        "status_loading_index": "Chargement de l'index des paquets PyPI...",
        "tab_manage": "Gestion des paquets",
        "tab_search": "Recherche",
        "search_label": "Chercher un paquet sur PyPI:",
        "progress_frame_title": "Progression",
        "search_button": "Chercher",
        "search_results_title": "Résultats de recherche",
        "search_info_title": "Détails du paquet (En ligne)",
        "admin_rights_title": "Droits d'administrateur",
        "admin_rights_required_msg": "Des droits d'administrateur sont requis pour '{pkg_name}'.",
        "selection_required_title": "Sélection requise",
        "select_python_version_msg": "Veuillez d'abord sélectionner une version de Python dans la liste.",
        "enter_package_name_prompt": "Entrez le nom du paquet pour Python {version_tag_display}:",
        "selected_version_fallback": "version sélectionnée",
        "select_package_version_first_msg": "Veuillez d'abord sélectionner une version dans la liste des versions.",
        "error_title": "Erreur",
        "version_details_not_found_msg": "Impossible de trouver les détails de la version sélectionnée.",
        "python_versions_title": "Versions Python installées",
        "status_checking_updates": "Recherche de paquets obsolètes…",
        "status_loading_installed": "Chargement des paquets installés…",
        "info_name": "Nom", "info_version": "Version", "info_summary": "Résumé", "info_homepage": "Page d'accueil",
        "info_author": "Auteur", "info_license": "Licence", "info_location": "Emplacement", "info_requires": "Requiert", "info_release_date": "Date de sortie",
        "info_yanked": "ATTENTION : Cette version a été retirée !", "info_yanked_reason": "Raison", # Keep these for local info
        "info_required_by": "Requis par","info_package_url": "URL du paquet", "info_documentation": "Documentation", "info_filename": "Nom de fichier",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Type de paquet", "info_python_version": "Version Python",
        "info_requires_python": "Nécessite Python", "info_size": "Taille", "info_upload_time": "Heure de téléchargement", "info_url": "URL",
        "info_yanked_status": "Retiré", "info_yanked_reason_full": "Raison du retrait"
    },
    "es": {
        "title": "Administrador de paquetes Pip",
        "status_loading": "Cargando paquetes…",
        "status_loaded": "{} paquetes cargados.",
        "btn_uninstall": "Desinstalar",
        "btn_update": "Actualizar",
        "btn_reinstall": "Reinstalar",
        "btn_refresh": "Actualizar lista",
        "confirm_uninstall": "¿Realmente desea desinstalar '{}'?",
        "no_info": "No se encontró información.",
        "install_frame_title": "Instalación",
        "loading_info": "Cargando información para '{}' …",
        "btn_install_deps": "Instalar dependencias",
        "btn_show_log": "Mostrar registro",
        "log_title": "Salida de Pip",
        "missing_deps_info": "Dependencias faltantes: {}",
        "btn_install_selected_version": "Instalar versión seleccionada",
        "confirm_install": "¿Quieres instalar '{pkg_name}=={version}'?",
        "update_available": "Actualización disponible: {} -> {}",
        "install_time": "Hora de instalación (.dist-info): {}",
        "no_install_time": "Hora de instalación no disponible (sin .dist-info)",
        "lang_label": "Idioma:",
        "frame_left_title": "Paquetes Instalados",
        "frame_right_title": "Información (Local)",
        "actions_frame_title": "Acciones",
        "homepage_tooltip": "Visitar la página de inicio de PyPI",
        "search_versions_title": "Versiones disponibles",
        "search_no_compatible_versions": "No se encontraron versiones compatibles.",
        "search_searching": "Buscando...",
        "search_no_results": "No se encontraron resultados para '{}'.",
        "search_error": "Error de búsqueda: {}",
        "info_latest_version": "Última versión",
        "info_dependencies": "Dependencias",
        "status_loading_index": "Cargando índice de paquetes de PyPI...",
        "tab_manage": "Gestión de Paquetes",
        "tab_search": "Búsqueda",
        "search_label": "Buscar paquete en PyPI:",
        "progress_frame_title": "Progreso",
        "search_button": "Buscar",
        "search_results_title": "Resultados de Búsqueda",
        "search_info_title": "Detalles del Paquete (Online)",
        "admin_rights_title": "Derechos de administrador",
        "admin_rights_required_msg": "Se requieren derechos de administrador para '{pkg_name}'.",
        "selection_required_title": "Selección requerida",
        "select_python_version_msg": "Por favor, seleccione primero una versión de Python de la lista.",
        "enter_package_name_prompt": "Introduzca el nombre del paquete para Python {version_tag_display}:",
        "selected_version_fallback": "versión seleccionada",
        "select_package_version_first_msg": "Por favor, seleccione primero una versión de la lista de versiones.",
        "error_title": "Error",
        "version_details_not_found_msg": "No se pudieron encontrar los detalles de la versión seleccionada.",
        "python_versions_title": "Versiones de Python instaladas",
        "status_checking_updates": "Buscando paquetes obsoletos…",
        "status_loading_installed": "Cargando paquetes instalados…",
        "info_name": "Nombre", "info_version": "Versión", "info_summary": "Resumen", "info_homepage": "Página de inicio",
        "info_author": "Autor", "info_license": "Licencia", "info_location": "Ubicación", "info_requires": "Requiere", "info_release_date": "Fecha de lanzamiento",
        "info_yanked": "¡ADVERTENCIA: Esta versión ha sido retirada!", "info_yanked_reason": "Razón", # Keep these for local info
        "info_required_by": "Requerido por","info_package_url": "URL del paquete", "info_documentation": "Documentación", "info_filename": "Nombre de archivo",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Tipo de paquete", "info_python_version": "Versión de Python",
        "info_requires_python": "Requiere Python", "info_size": "Tamaño", "info_upload_time": "Hora de subida", "info_url": "URL",
        "info_yanked_status": "Retirado", "info_yanked_reason_full": "Razón del retiro"
    },
    "zh": {
        "title": "Pip 软件包管理器",
        "status_loading": "正在加载软件包…",
        "status_loaded": "已加载 {} 个软件包。",
        "btn_uninstall": "卸载",
        "btn_update": "更新",
        "btn_reinstall": "重新安装",
        "btn_refresh": "刷新列表",
        "confirm_uninstall": "确定要卸载 '{}' 吗？",
        "no_info": "未找到信息。",
        "install_frame_title": "安装",
        "loading_info": "正在加载 '{}' 的信息…",
        "btn_install_deps": "安装依赖",
        "btn_show_log": "显示日志",
        "log_title": "Pip 输出",
        "missing_deps_info": "缺少依赖: {}",
        "btn_install_selected_version": "安装所选版本",
        "confirm_install": "你要安装 '{pkg_name}=={version}'吗？",
        "update_available": "可用更新: {} -> {}",
        "install_time": "安装时间 (.dist-info): {}",
        "no_install_time": "无法确定安装时间（没有 .dist-info）",
        "lang_label": "语言：",
        "frame_left_title": "已安装的软件包",
        "frame_right_title": "信息 (本地)",
        "actions_frame_title": "操作",
        "homepage_tooltip": "访问 PyPI 主页",
        "search_versions_title": "可用版本",
        "search_no_compatible_versions": "未找到兼容版本。",
        "search_searching": "正在搜索...",
        "search_no_results": "未找到 '{}' 的结果。",
        "search_error": "搜索出错: {}",
        "info_latest_version": "最新版本",
        "info_dependencies": "依赖关系",
        "status_loading_index": "正在加载 PyPI 包索引...",
        "tab_manage": "软件包管理",
        "tab_search": "搜索",
        "search_label": "在 PyPI 上搜索包:",
        "progress_frame_title": "进度",
        "search_button": "搜索",
        "search_results_title": "搜索结果",
        "search_info_title": "包详细信息 (在线)",
        "admin_rights_title": "管理员权限",
        "admin_rights_required_msg": "需要管理员权限才能操作 '{pkg_name}'。",
        "selection_required_title": "需要选择",
        "select_python_version_msg": "请先从列表中选择一个 Python 版本。",
        "enter_package_name_prompt": "请输入 Python {version_tag_display} 的软件包名称：",
        "selected_version_fallback": "所选版本",
        "select_package_version_first_msg": "请先从版本列表中选择一个版本。",
        "error_title": "错误",
        "version_details_not_found_msg": "找不到所选版本的详细信息。",
        "python_versions_title": "已安装的 Python 版本",
        "status_checking_updates": "正在检查过时的软件包…",
        "status_loading_installed": "正在加载已安装的软件包…",
        "info_name": "名称", "info_version": "版本", "info_summary": "摘要", "info_homepage": "主页",
        "info_author": "作者", "info_license": "许可证", "info_location": "位置", "info_requires": "需要", "info_release_date": "发布日期",
        "info_yanked": "警告：此版本已被撤回！", "info_yanked_reason": "原因", # Keep these for local info
        "info_required_by": "被需要", "info_package_url": "软件包网址", "info_documentation": "文档", "info_filename": "文件名",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "软件包类型", "info_python_version": "Python 版本",
        "info_requires_python": "需要 Python", "info_size": "大小", "info_upload_time": "上传时间", "info_url": "网址",
        "info_yanked_status": "已撤回", "info_yanked_reason_full": "撤回原因",
    },
    "ja": {
        "title": "Pip パッケージマネージャー",
        "status_loading": "パッケージを読み込み中…",
        "status_loaded": "{} 個のパッケージを読み込みました。",
        "btn_uninstall": "アンインストール",
        "btn_update": "更新",
        "btn_reinstall": "再インストール",
        "btn_refresh": "リストを更新",
        "confirm_uninstall": "'{}' を本当にアンインストールしますか？",
        "no_info": "情報が見つかりません。",
        "install_frame_title": "インストール",
        "loading_info": "'{}' の情報を読み込み中…",
        "btn_install_deps": "依存関係をインストール",
        "btn_show_log": "ログを表示",
        "log_title": "Pip 出力",
        "missing_deps_info": "不足している依存関係: {}",
        "btn_install_selected_version": "選択したバージョンをインストール",
        "confirm_install": "'{pkg_name}=={version}' をインストールしますか？",
        "update_available": "利用可能なアップデート: {} -> {}",
        "install_time": "インストール日時 (.dist-info): {}",
        "no_install_time": "インストール日時を取得できません（.dist-info がありません）",
        "lang_label": "言語：",
        "frame_left_title": "インストールされたパッケージ",
        "frame_right_title": "情報 (ローカル)",
        "actions_frame_title": "アクション",
        "homepage_tooltip": "PyPIホームページにアクセス",
        "search_versions_title": "利用可能なバージョン",
        "search_no_compatible_versions": "互換性のあるバージョンが見つかりませんでした。",
        "search_searching": "検索中...",
        "search_no_results": "'{}' の結果が見つかりませんでした。",
        "search_error": "検索エラー: {}",
        "info_latest_version": "最新バージョン",
        "info_dependencies": "依存関係",
        "status_loading_index": "PyPIパッケージインデックスを読み込んでいます...",
        "tab_manage": "パッケージ管理",
        "tab_search": "検索",
        "search_label": "PyPIでパッケージを検索:",
        "progress_frame_title": "進捗",
        "search_button": "検索",
        "search_results_title": "検索結果",
        "search_info_title": "パッケージの詳細 (オンライン)",
        "admin_rights_title": "管理者権限",
        "admin_rights_required_msg": "'{pkg_name}' には管理者権限が必要です。",
        "selection_required_title": "選択が必要です",
        "select_python_version_msg": "最初にリストからPythonバージョンを選択してください。",
        "enter_package_name_prompt": "Python {version_tag_display} のパッケージ名を入力してください：",
        "selected_version_fallback": "選択したバージョン",
        "select_package_version_first_msg": "最初にバージョンリストからバージョンを選択してください。",
        "error_title": "エラー",
        "version_details_not_found_msg": "選択したバージョンの詳細が見つかりませんでした。",
        "python_versions_title": "インストールされた Python バージョン",
        "status_checking_updates": "古いパッケージを確認しています…",
        "status_loading_installed": "インストール済みのパッケージを読み込んでいます…",
        "info_name": "名前", "info_version": "バージョン", "info_summary": "概要", "info_homepage": "ホームページ",
        "info_author": "作者", "info_license": "ライセンス", "info_location": "場所", "info_requires": "依存関係", "info_release_date": "リリース日",
        "info_yanked": "警告：このバージョンは取り下げられました！", "info_yanked_reason": "理由", # Keep these for local info
        "info_required_by": "被依存関係", "info_package_url": "パッケージURL", "info_documentation": "ドキュメント", "info_filename": "ファイル名",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "パッケージタイプ", "info_python_version": "Pythonバージョン",
        "info_requires_python": "必要なPython", "info_size": "サイズ", "info_upload_time": "アップロード時間", "info_url": "URL",
        "info_yanked_status": "取り下げ済み", "info_yanked_reason_full": "取り下げ理由"
    }
}

current_lang = "de"
log_records = []
icon_tooltip = None # Globale Variable für den Tooltip
python_versions_cache = {} # Cache für Python-Versionen: {'-V:3.11': 'C:\Path\python.exe'}
pypi_index_cache = [] # Cache für den PyPI-Paketindex
pypi_package_releases_cache = {} # NEU: Cache für vollständige Release-Daten eines Pakets
current_system_tags = set() # NEU: Cache für kompatible Wheel-Tags des aktuellen Systems
current_package_version_details_cache = {} # NEU: Cache für Details der aktuell angezeigten Paketversionen (filename -> data)
current_searched_pkg_name = None # NEU: Merkt sich das aktuell im Such-Tab ausgewählte Paket
progress_label = None # NEU: Zentrales Label für Fortschrittsanzeigen in der Statusleiste

def update_status_label(text_key, show=True):
    """
    Aktualisiert das zentrale Status-Label sicher aus jedem Thread.
    Wird für Ladeanzeigen wie "Lade Index..." verwendet.
    """
    if show:
        message = t(text_key)
        log_message(message)
        if progress_label:
            progress_label.config(text=message)
    else:
        if progress_label:
            progress_label.config(text="")

# --- Tooltip-Klasse ---
class ToolTip:
    """
    Erstellt einen Tooltip für ein gegebenes Widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def update_text(self, new_text):
        """Aktualisiert den Text des Tooltips."""
        self.text = new_text

    def show_tooltip(self, event=None):
        """Zeigt das Tooltip-Fenster an (robuste Positionsbestimmung)."""
        # Bestimme Position: wenn Event vorhanden, verwende event-root-Koordinaten,
        # ansonsten verwende Fallback auf Widget-Position. Vermeide bbox("insert").
        try:
            if event and getattr(event, "x_root", None) is not None:
                x = event.x_root + 20
                y = event.y_root + 20
            else:
                # Fallback: benutze widget.winfo_rootx/winfo_rooty
                x = self.widget.winfo_rootx() + 20
                y = self.widget.winfo_rooty() + 20

            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")

            label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                             background="#ffffe0", relief='solid', borderwidth=1,
                             font=("tahoma", "8", "normal"))
            label.pack(ipadx=1)
        except (tk.TclError, RuntimeError):
            # Silent fail: Tooltip darf nicht zum Absturz der App führen.
            self.tooltip_window = None

    def hide_tooltip(self, _event=None):
        """Versteckt das Tooltip-Fenster."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except (tk.TclError, RuntimeError):
                pass
        self.tooltip_window = None

def open_pypi_homepage(_event=None):
    """Öffnet die PyPI-Homepage in einem neuen Browser-Tab."""
    webbrowser.open_new_tab("https://pypi.org/")


def get_current_system_tags_set():
    """
    Gibt eine Menge von kompatiblen Wheel-Tags (als Tag-Objekte) für das aktuelle System zurück.
    """
    # packaging.tags.sys_tags() gibt eine Liste von Tag-Objekten zurück
    return set(packaging.tags.sys_tags())


def log_message(message, level="INFO"):
    """Fügt eine Nachricht zum In-Memory-Log hinzu (robuste GUI-Updates)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"{timestamp} [{level}] {message}"
    log_records.append(full_message)

    # Sichere GUI-Aktualisierung: prüfe global auf 'root' und 'log_window'.
    def append_to_log_safely():
        try:
            lw = globals().get("log_window")
            if lw and getattr(lw, "winfo_exists", lambda: False)():
                lw.log_text_widget.insert(tk.END, full_message + "\n")
                lw.log_text_widget.see(tk.END)
        except (tk.TclError, RuntimeError):
            # Nicht fatal; Log-Eintrag bleibt im Speicher.
            pass

    try:
        r = globals().get("root")
        if r and getattr(r, "winfo_exists", lambda: False)():
            r.after(0, append_to_log_safely)
    except (RuntimeError, tk.TclError):
        # GUI existiert nicht oder wurde gerade zerstört -> nichts weiter tun.
        pass

def t(key):
    """Gibt den übersetzten Text für einen Schlüssel in der aktuellen Sprache zurück."""
    return LANG_TEXTS[current_lang].get(key, f"<{key}>")


def resource_path(relative_path):
    """ Ermittelt den absoluten Pfad zu einer Ressource, funktioniert für den Entwicklungsmodus und für PyInstaller. """
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        # pylint: disable=protected-access
        base_path = sys._MEIPASS
    except AttributeError:
        # _MEIPASS ist nicht gesetzt, wir sind im normalen Entwicklungsmodus.
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- GUI Aufbau ---
root = tk.Tk()
root.title(t("title"))
# 1. Icon für Titelleiste und Taskleiste setzen
try:
    root.iconbitmap(resource_path('PyPi-128px.ico'))
except tk.TclError:
    print("Warnung: PyPi-128px.ico nicht gefunden oder konnte nicht geladen werden.")
root.geometry("950x650")  # etwas höher für Versionsfeld

# --- Tab-Struktur ---
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text=t("tab_manage"))
notebook.add(tab2, text=t("tab_search"))

# --- Tab 1: Paketverwaltung (Grid-Layout) ---
# Konfiguriere das Grid-Layout für die drei Spalten in Tab 1
tab1.columnconfigure(0, weight=1, minsize=270)  # Linke Spalte (Paketliste)
tab1.columnconfigure(1, weight=0)               # Mittlere Spalte (Aktionen), feste Breite
tab1.columnconfigure(2, weight=2, minsize=300)  # Rechte Spalte (Infos), bekommt mehr Platz
tab1.rowconfigure(0, weight=1)                  # Die Zeile soll sich in der Höhe anpassen

# Linke Spalte – Paketliste (in Tab 1)
frame_left = ttk.LabelFrame(tab1, text=t("frame_left_title"))
frame_left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
package_listbox = tk.Listbox(frame_left, width=50)
package_listbox.pack(side=tk.LEFT, fill=tk.Y)
scrollbar = ttk.Scrollbar(frame_left, orient="vertical", command=package_listbox.yview)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
package_listbox.config(yscrollcommand=scrollbar.set)

# Mittlere Spalte – Buttons + Sprache (in Tab 1)
frame_middle = ttk.Frame(tab1)
frame_middle.grid(row=0, column=1, sticky="ns", padx=5, pady=10)

# Frame für die Sprachauswahl.
lang_frame = ttk.Frame(frame_middle)
lang_frame.pack(side=tk.TOP, pady=10)
lang_label = ttk.Label(lang_frame, text=t("lang_label"))
lang_label.pack(side=tk.LEFT, padx=5)
lang_var = tk.StringVar(value="Deutsch")
# KORREKTUR: Die Sprachliste wird dynamisch aus den Schlüsseln von LANG_TEXTS generiert.
lang_display_names = {"de": "Deutsch", "en": "English", "fr": "Français", "es": "Español", "zh": "中文", "ja": "日本語"}
lang_combo = ttk.Combobox(lang_frame, textvariable=lang_var, state="readonly",
                          values=list(lang_display_names.values()), width=12)
lang_combo.pack(side=tk.LEFT)

# Frame für die Aktions-Buttons.
btn_frame = ttk.LabelFrame(frame_middle, text=t("actions_frame_title"))
btn_frame.pack(pady=20, padx=5)

# 2. Icon im Button-Frame anzeigen
try:
    # Lade das Bild mit Pillow
    img = Image.open(resource_path('PyPi-128px.ico'))
    # Vergrößere das Bild für eine bessere Darstellung
    img_resized = img.resize((128, 128), Image.Resampling.LANCZOS)
    # Konvertiere es für Tkinter
    root.icon_image = ImageTk.PhotoImage(img_resized)

    # Erstelle ein Label, um das Bild im btn_frame anzuzeigen
    icon_label = ttk.Label(btn_frame, image=root.icon_image)
    icon_label.config(cursor="hand2")  # Mauszeiger zur Hand ändern
    icon_label.pack(side=tk.BOTTOM, pady=10)  # Unten im Frame platzieren
    # Binde das Klick-Event an die Funktion zum Öffnen der Webseite
    icon_label.bind("<Button-1>", open_pypi_homepage)
    # Erstelle den Tooltip für das Icon-Label
    icon_tooltip = ToolTip(icon_label, t("homepage_tooltip"))
except (FileNotFoundError, tk.TclError):
    print("Warnung: PyPi-128px.ico nicht gefunden, Icon im Frame wird nicht angezeigt.")

# --- Log-Fenster Logik ---
log_window = None
def show_log_window():
    """Erstellt und zeigt das Log-Fenster an. Stellt sicher, dass nur ein Fenster geöffnet wird."""
    global log_window
    if log_window and log_window.winfo_exists():
        log_window.lift()
        return

    log_window = tk.Toplevel(root)
    log_window.title(t("log_title"))
    log_window.geometry("800x500")

    # Ein Text-Widget mit Scrollbar zur Anzeige der Log-Einträge.
    log_window.log_text_widget = tk.Text(log_window, wrap=tk.WORD, font=("Courier New", 9))
    log_scrollbar = ttk.Scrollbar(log_window, orient="vertical", command=log_window.log_text_widget.yview)
    log_window.log_text_widget.config(yscrollcommand=log_scrollbar.set)

    log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    log_window.log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    log_window.log_text_widget.insert(tk.END, "\n".join(log_records) + "\n")
    log_window.log_text_widget.see(tk.END) # Scrollt automatisch zum Ende.

# --- Kernfunktion für Pip-Befehle ---
def run_pip_command(command_list, on_finish=None):
    """
    Führt einen Pip-Befehl in einem separaten Prozess aus.
    Zeigt den Fortschritt live im 'update_info_label' an.
    :param command_list: Die an pip zu übergebenden Argumente.
    """
    def update_label(text):
        """Sichere Hilfsfunktion, um das zentrale Fortschritts-Label aus dem Hauptthread zu aktualisieren."""
        if progress_label:
            progress_label.config(text=text)

    # Startmeldung im Label anzeigen
    start_msg = f"Running: {os.path.basename(sys.executable)} -m pip {' '.join(command_list)}..."
    log_message(start_msg)
    try:
        if root.winfo_exists():
            root.after(0, lambda: update_label(start_msg))
    except RuntimeError:
        pass # GUI wurde bereits geschlossen

    process = subprocess.Popen([sys.executable, "-m", "pip"] + command_list,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')

    for line in iter(process.stdout.readline, ''):
        # Jede Zeile der Ausgabe im Label anzeigen
        cleaned_line = line.strip()
        log_message(cleaned_line, level="PIP")
        try:
            if cleaned_line and root.winfo_exists():
                    root.after(0, lambda l=cleaned_line: update_label(l))
        except RuntimeError:
            pass # GUI wurde bereits geschlossen

    process.stdout.close()
    process.wait()
    # Abschlussmeldung im Label anzeigen
    end_msg = f"Finished with exit code {process.returncode}"
    log_message(end_msg, level="STATUS")
    try:
        if root.winfo_exists():
            root.after(0, lambda: update_label(end_msg))
            if on_finish:
                root.after(100, on_finish) # Ruft die Callback-Funktion nach Abschluss auf
    except RuntimeError:
        pass # GUI wurde bereits geschlossen

def is_admin():
    """Prüft, ob das aktuelle Python mit Administratorrechten läuft."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_package_path(pkg_name: str) -> str:
    """Gibt den Installationspfad eines Pakets zurück."""
    try:
        dist = importlib.metadata.distribution(pkg_name)
        return str(dist.locate_file(''))
    except importlib.metadata.PackageNotFoundError:
        return ""
# --- Buttons ---
def uninstall_package(pkg_name):
    """
    Deinstalliert ein ausgewähltes Paket. Fordert bei Bedarf Administratorrechte an.
    """
    if not pkg_name:
        return

    confirm = messagebox.askyesno(t("btn_uninstall"), t("confirm_uninstall").format(pkg_name))
    if not confirm:
        return

    # Prüfe, ob das Paket in einem geschützten Verzeichnis liegt.
    pkg_path = get_package_path(pkg_name)
    needs_admin = pkg_path.lower().startswith(r"c:\program files")

    # Wenn Adminrechte benötigt werden, aber nicht vorhanden sind:
    if needs_admin and not is_admin():
        log_message(f"Admin rights required for uninstalling {pkg_name} ({pkg_path})")
        messagebox.showinfo(t("admin_rights_title"), t("admin_rights_required_msg").format(pkg_name=pkg_name))
        # KORREKTUR: Starte direkt den pip-Befehl mit Admin-Rechten, anstatt das ganze Skript neu zu starten.
        # Dies ist sauberer und entfernt die Notwendigkeit für den '--uninstall-admin'-Block am Skriptanfang.
        pip_args = f'-m pip uninstall -y "{pkg_name}"'
        subprocess.run([ # pylint: disable=subprocess-run-check
            "powershell", "-Command", "Start-Process", sys.executable,
            "-ArgumentList", f'"{pip_args}"', "-Verb", "runAs", "-Wait"
        ])
        # KORREKTUR: Nach dem Warten auf den Admin-Prozess die Liste aktualisieren.
        refresh_package_list()
        return

    # Wenn Adminrechte vorhanden oder nicht erforderlich: direkt deinstallieren
    # KORREKTUR: Übergibt refresh_package_list als on_finish-Callback.
    threading.Thread(target=run_pip_command, args=(["uninstall", "-y", pkg_name], refresh_package_list), daemon=True).start()

def update_package(pkg_name):
    """Aktualisiert ein ausgewähltes Paket auf die neueste Version."""
    if not pkg_name:
        return
    threading.Thread(target=run_pip_command, args=(["install", "--upgrade", pkg_name],), daemon=True).start()

def reinstall_package(pkg_name):
    """
    Installiert die aktuell installierte Version eines Pakets neu, anstatt auf die neueste zu aktualisieren.
    """
    if not pkg_name:
        return

    try:
        # Ermittle die aktuell installierte Version des Pakets
        current_version = importlib.metadata.version(pkg_name)
        log_message(f"Starting reinstall for {pkg_name}=={current_version}")

        # Baue den Befehl zusammen, der explizit diese Version neu installiert
        command = ["install", "--force-reinstall", "--no-deps", f"{pkg_name}=={current_version}"]
        threading.Thread(target=run_pip_command, args=(command,), daemon=True).start()

    except importlib.metadata.PackageNotFoundError:
        log_message(
            f"Could not determine version for '{pkg_name}'. Falling back to standard reinstall.",
            "WARNING"
        )
        command = ["install", "--force-reinstall", "--no-deps", pkg_name]
        threading.Thread(target=run_pip_command, args=(command,), daemon=True).start()

def install_dependencies(deps_to_install):
    """Installiert eine Liste von Abhängigkeitspaketen."""
    if not deps_to_install:
        return
    threading.Thread(target=run_pip_command, args=(["install"] + deps_to_install,), daemon=True).start()

# Funktion zum Aktualisieren der Paketliste in der GUI.
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
btn_refresh.pack(fill=tk.X, pady=2)

btn_install_deps = ttk.Button(btn_frame, text=t("btn_install_deps"), width=25, state=tk.DISABLED)
btn_install_deps.pack(fill=tk.X, pady=2)

# Button zum Anzeigen des Log-Fensters.
btn_show_log = ttk.Button(btn_frame, text=t("btn_show_log"), width=25, command=show_log_window)
btn_show_log.pack(fill=tk.X, pady=2)

# --- Rechte Spalte (in Tab 1): Infofeld (Lokal) und Python-Versionen ---
frame_right = ttk.Frame(tab1)
frame_right.grid(row=0, column=2, sticky="nsew", padx=(10, 5), pady=10)

info_frame = ttk.LabelFrame(frame_right, text=t("frame_right_title"))
info_frame.pack(fill=tk.BOTH, expand=True)

info_text_scrollbar = ttk.Scrollbar(info_frame)
info_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
info_text = tk.Text(frame_right, wrap=tk.WORD)
info_text.pack(in_=info_frame, side=tk.LEFT, fill=tk.BOTH, expand=True)
info_text_scrollbar.config(command=info_text.yview)
info_text.config(yscrollcommand=info_text_scrollbar.set)


# Python-Versionen-Anzeige (reine Textanzeige)
py_version_frame = ttk.LabelFrame(frame_right, text=t("python_versions_title"))
py_version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, ipady=2)
py_version_text = tk.Text(py_version_frame, height=4, wrap=tk.NONE, font=("Courier New", 10), state=tk.DISABLED)
py_version_text.pack(fill=tk.X, padx=5, pady=5)


# --- Tab 2: Suche & Werkzeuge ---
# Ein Haupt-Frame, der die drei Spalten aufnimmt.
search_main_frame = ttk.Frame(tab2)
search_main_frame.pack(fill=tk.BOTH, expand=True)

# Konfiguriere das Grid-Layout für die drei Spalten
search_main_frame.columnconfigure(0, weight=1, minsize=270) # Linke Spalte (Suche)
search_main_frame.columnconfigure(1, weight=1, minsize=200) # Mittlere Spalte (Versionen)
search_main_frame.columnconfigure(2, weight=2, minsize=300) # Rechte Spalte (Details), bekommt mehr Platz
search_main_frame.rowconfigure(0, weight=1) # Die Zeile soll sich in der Höhe anpassen

# Linke Seite von Tab 2: Suche und Paketnamen-Ergebnisse
search_left_frame = ttk.Frame(search_main_frame)
# Platziere den Frame im Grid
search_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)

# Suchleiste
search_bar_frame = ttk.LabelFrame(search_left_frame, text=t("search_label")) # Dieser Frame ist jetzt im search_left_frame
search_bar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
search_entry_var = tk.StringVar()
search_entry = ttk.Entry(search_bar_frame, textvariable=search_entry_var)
search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
search_button = ttk.Button(search_bar_frame, text=t("search_button"), width=10)
search_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)

# Suchergebnisse (mit fester Breite)
search_results_frame = ttk.LabelFrame(
    search_left_frame,
    text=t("search_results_title")
)
search_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# Feste Breite setzen (z. B. 300 px) - Sie können diesen Wert anpassen
search_results_frame.configure(width=270)

# Verhindert, dass der Frame sich an die Inhalte anpasst
search_results_frame.pack_propagate(False)

# Innerer Container (wichtig, damit pack_propagate nicht stört)
inner_frame = tk.Frame(search_results_frame)
inner_frame.pack(fill=tk.BOTH, expand=True)

# Listbox + Scrollbar im inneren Container
search_results_listbox = tk.Listbox(inner_frame)
search_results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
search_results_scrollbar = ttk.Scrollbar(
    inner_frame,
    orient="vertical",
    command=search_results_listbox.yview
)
search_results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
search_results_listbox.config(yscrollcommand=search_results_scrollbar.set)

# NEU: Mittlere Seite von Tab 2: Versionen des ausgewählten Pakets
search_versions_frame = ttk.LabelFrame(search_main_frame, text=t("search_versions_title"))
search_versions_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
search_versions_listbox = tk.Listbox(search_versions_frame)
search_versions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
search_versions_scrollbar = ttk.Scrollbar(search_versions_frame, orient="vertical", command=search_versions_listbox.yview)
search_versions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
search_versions_listbox.config(yscrollcommand=search_versions_scrollbar.set)

# Rechte Seite von Tab 2: Details, Installation und Fortschrittsanzeige
search_right_frame = ttk.Frame(search_main_frame)
search_right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)

# Konfiguriere das Grid-Layout für die rechte Spalte
search_right_frame.rowconfigure(0, weight=2) # Oberer Teil (Details) bekommt 2/3 des Platzes
search_right_frame.rowconfigure(1, weight=1) # Unterer Teil (Installation) bekommt 1/3 des Platzes
search_right_frame.columnconfigure(0, weight=1)

# Unterer Teil: Installation und Fortschrittsanzeige
search_right_bottom_frame = ttk.Frame(search_right_frame)
search_right_bottom_frame.grid(row=1, column=0, sticky="ew")

# Oberer Teil: Paketdetails (Textbox)
search_info_frame = ttk.LabelFrame(search_right_frame, text=t("search_info_title"))
search_info_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))

# Widgets für die Textbox
search_info_text_scrollbar = ttk.Scrollbar(search_info_frame)
search_info_text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
search_info_text = tk.Text(search_info_frame, wrap=tk.WORD)
search_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
search_info_text_scrollbar.config(command=search_info_text.yview)
search_info_text.config(yscrollcommand=search_info_text_scrollbar.set)

def install_selected_version():
    """Installiert die ausgewählte Version eines Pakets für die aktuell laufende Python-Umgebung."""
    version_selection = search_versions_listbox.curselection()

    if not current_searched_pkg_name or not version_selection:
        messagebox.showwarning(t("install_frame_title"), t("select_package_version_first_msg"))
        return

    pkg_name = current_searched_pkg_name
    selected_filename = search_versions_listbox.get(version_selection[0])

    file_data = current_package_version_details_cache.get(selected_filename)
    if not file_data:
        messagebox.showerror(t("error_title"), t("select_package_version_first_msg"))
        return

    version_to_install = file_data.get('version')
    if not version_to_install:
        try:
            _name, parsed_version, _build, _tags = packaging_utils.parse_wheel_filename(selected_filename)
            version_to_install = str(parsed_version)
        except (packaging_utils.InvalidWheelFilename, IndexError):
            version_to_install = t("selected_version_fallback")

    confirm_msg = t("confirm_install").format(pkg_name=pkg_name, version=version_to_install)
    if not messagebox.askyesno(t("install_frame_title"), confirm_msg):
        return

    threading.Thread(target=run_pip_command, args=(["install", f"{pkg_name}=={version_to_install}"],), daemon=True).start()

install_frame = ttk.LabelFrame(search_right_bottom_frame, text=t("install_frame_title"))
install_frame.pack(fill=tk.X, padx=5, pady=5)
btn_install_selected = ttk.Button(install_frame, text=t("btn_install_selected_version"), command=install_selected_version)
btn_install_selected.pack(pady=5, padx=5)

# --- Logik für Tab 2 ---
def perform_search(_event=None):
    """Führt die eigentliche Suche im lokalen Index durch."""
    search_versions_listbox.delete(0, tk.END) # NEU: Versionsliste leeren
    search_info_text.config(state=tk.NORMAL) # NEU: Textbox bearbeitbar machen
    search_info_text.delete("1.0", tk.END) # NEU: Info-Textbox leeren
    query = search_entry_var.get()
    if not query:
        # Bei leerer Suche die Liste leeren, anstatt alles anzuzeigen.
        update_search_results([], "")
        return

    if not pypi_index_cache:
        log_message("PyPI index not loaded yet. Starting load...")
        load_pypi_index()
        return # Die Suche wird ausgeführt, sobald der Index geladen ist.

    log_message(f"Filtering local index for '{query}'...")
    # Die Suche wird nun offline gegen den lokalen Cache durchgeführt.
    filtered_packages = [pkg for pkg in pypi_index_cache if query.lower() in pkg.lower()]
    root.after(0, lambda: update_search_results(filtered_packages, query)) # NEU: GUI-Update im Hauptthread

def load_pypi_index(): # NEU: Umbenannt von get_pypi_info
    """Lädt den vollständigen Paketindex von PyPI und speichert ihn im Cache."""
    global pypi_index_cache # NEU: Globaler Zugriff auf den Cache
    if pypi_index_cache:
        log_message("PyPI index already in cache.")
        return

    def do_load():
        try:
            if root.winfo_exists():
                root.after(0, lambda: update_status_label("status_loading_index"))
        except RuntimeError:
            return # Breche ab, wenn die GUI geschlossen wurde
        try:
            # Die Simple API liefert eine Liste aller Pakete.
            url = "https://pypi.org/simple/"
            headers = {'Accept': 'application/vnd.pypi.simple.v1+json'}
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # Extrahiere die Namen aus der Projektliste
            package_names = sorted([project['name'] for project in data['projects']], key=str.lower)

            # Speichere im globalen Cache
            global pypi_index_cache
            pypi_index_cache = package_names

            # Die Liste wird nicht mehr automatisch gefüllt, um die GUI nicht zu blockieren.
            # Der Benutzer kann nun eine Suche starten.
            # root.after(0, lambda: update_search_results(pypi_index_cache, ""))
            log_message(f"PyPI index loaded successfully with {len(pypi_index_cache)} packages.")
        except requests.exceptions.RequestException as e:
            log_message(f"Failed to load PyPI index: {e}", "ERROR")
        finally:
            try:
                if root.winfo_exists():
                    root.after(0, lambda: update_status_label(None, show=False))
            except RuntimeError:
                pass # GUI wurde bereits geschlossen

    threading.Thread(target=do_load, daemon=True).start()

def fetch_pypi_package_releases(pkg_name):
    """Ruft alle Paketinformationen und Releases von der PyPI JSON API ab."""
    global pypi_package_releases_cache
    if pkg_name in pypi_package_releases_cache:
        return pypi_package_releases_cache[pkg_name]

    try:
        response = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=10)
        response.raise_for_status()
        data = response.json()
        pypi_package_releases_cache[pkg_name] = data # Cache the full data
        return data
    except requests.exceptions.RequestException as e:
        log_message(f"Fehler beim Abrufen der PyPI-Informationen für {pkg_name}: {e}", "ERROR")
        return None

def update_search_results(packages, query):
    """Aktualisiert die Listbox mit den Suchergebnissen."""
    search_results_listbox.delete(0, tk.END)
    if packages:
        for pkg in packages:
            search_results_listbox.insert(tk.END, pkg)
    elif query:  # Zeige "Keine Ergebnisse" nur an, wenn auch gesucht wurde
        search_results_listbox.insert(tk.END, t("search_no_results").format(query))

def show_package_versions(_event):
    """
    Wird aufgerufen, wenn ein Paket in der Suchergebnis-Listbox ausgewählt wird.
    Lädt die Versionen und zeigt kompatible in der Versions-Listbox an.
    """
    selection = search_results_listbox.curselection()
    if not selection:
        return
    pkg_name = search_results_listbox.get(selection[0])
    global current_searched_pkg_name
    current_searched_pkg_name = pkg_name # Den Namen des ausgewählten Pakets global merken

    search_versions_listbox.delete(0, tk.END)
    search_info_text.config(state=tk.NORMAL) # NEU: Textbox bearbeitbar machen
    search_info_text.delete("1.0", tk.END)
    search_info_text.insert(tk.END, t("loading_info").format(pkg_name))
    search_info_text.config(state=tk.DISABLED) # NEU: Textbox wieder schreibgeschützt

    def do_fetch_versions():
        global current_package_version_details_cache
        current_package_version_details_cache.clear() # Cache für vorheriges Paket leeren

        pypi_data = fetch_pypi_package_releases(pkg_name)
        if not pypi_data:
            try:
                if root.winfo_exists():
                    root.after(0, lambda: search_info_text.config(state=tk.NORMAL))
                    root.after(0, lambda: search_info_text.delete("1.0", tk.END))
                    root.after(0, lambda: search_info_text.insert(tk.END, t("no_info")))
                    root.after(0, lambda: search_info_text.config(state=tk.DISABLED))
            except RuntimeError: pass
            return

        releases = pypi_data.get('releases', {})
        compatible_versions_info = [] # Speichert (version_obj, filename, dist_data)

        system_tags = get_current_system_tags_set() # Aktuelle System-Tags abrufen

        for version_str, distributions in releases.items():
            for dist_data in distributions:
                filename = dist_data.get('filename')
                packagetype = dist_data.get('packagetype')

                if not filename:
                    continue

                is_compatible = False
                if packagetype == 'sdist':
                    # Source-Distributionen sind im Allgemeinen universell, prüfen auf 'any' Tag
                    if any(tag.platform == 'any' for tag in system_tags):
                        is_compatible = True
                elif packagetype == 'bdist_wheel':
                    # KORREKTUR: Verwende die offizielle Methode, um die Kompatibilität zu prüfen.
                    try:
                        # Nutze die offizielle Funktion, um die Tags aus dem Wheel-Namen zu parsen.
                        # Gibt (name, version, build, tags) zurück.
                        _name, _version, _build, wheel_tags = packaging_utils.parse_wheel_filename(filename)

                        # Prüfe, ob es eine Schnittmenge zwischen den Tags des Wheels und den System-Tags gibt.
                        # isdisjoint() ist sehr schnell und prüft, ob zwei Mengen keine gemeinsamen Elemente haben.
                        if not system_tags.isdisjoint(wheel_tags):
                            is_compatible = True
                    except packaging.utils.InvalidWheelFilename:
                        # Fallback für 'any' oder 'none' in Dateinamen, die nicht dem Standard entsprechen, oder für sdist.
                        if "any" in filename or "none" in filename:
                            is_compatible = True
                    except (packaging.version.InvalidVersion, ValueError) as e:
                        log_message(f"Fehler beim Parsen des Wheel-Dateinamens '{filename}': {e}", "WARNING")

                if is_compatible:
                    compatible_versions_info.append((packaging.version.parse(version_str), filename, dist_data))
                    current_package_version_details_cache[filename] = dist_data

        # Kompatible Versionen nach Versionsnummer (absteigend) sortieren
        compatible_versions_info.sort(key=lambda x: x[0], reverse=True)

        try:
            if root.winfo_exists():
                root.after(0, lambda: search_versions_listbox.delete(0, tk.END))
                if compatible_versions_info:
                    for _, filename, _ in compatible_versions_info:
                        root.after(0, lambda f=filename: search_versions_listbox.insert(tk.END, f))
                else:
                    root.after(0, lambda: search_versions_listbox.insert(tk.END, t("search_no_compatible_versions")))
                root.after(0, lambda: search_info_text.config(state=tk.NORMAL))
                root.after(0, lambda: search_info_text.delete("1.0", tk.END))
                root.after(0, lambda: search_info_text.config(state=tk.DISABLED))
        except RuntimeError: pass

    threading.Thread(target=do_fetch_versions, daemon=True).start()

def show_version_details(_event):
    """
    Wird aufgerufen, wenn eine Version in der Versions-Listbox ausgewählt wird.
    Zeigt detaillierte Informationen zu dieser Version an.
    """
    selection = search_versions_listbox.curselection()
    if not selection:
        return
    selected_filename = search_versions_listbox.get(selection[0])

    file_data = current_package_version_details_cache.get(selected_filename)
    if not file_data:
        search_info_text.config(state=tk.NORMAL)
        search_info_text.delete("1.0", tk.END)
        search_info_text.insert(tk.END, t("no_info"))
        search_info_text.config(state=tk.DISABLED)
        return

    # Den global gespeicherten Paketnamen verwenden, anstatt die Listbox erneut abzufragen
    pypi_full_data = pypi_package_releases_cache.get(current_searched_pkg_name)
    if not pypi_full_data:
        search_info_text.config(state=tk.NORMAL)
        search_info_text.delete("1.0", tk.END)
        search_info_text.insert(tk.END, t("no_info"))
        search_info_text.config(state=tk.DISABLED)
        return

    info = pypi_full_data.get('info', {})

    search_info_text.config(state=tk.NORMAL) # Textbox bearbeitbar machen
    search_info_text.delete("1.0", tk.END)

    # "name"
    search_info_text.insert(tk.END, f"{t('info_name')}: {info.get('name', 'N/A')}\n\n")
    # "description" (using summary for brevity, or full description if available)
    description_text = info.get('summary')
    if not description_text:
        description_text = info.get('description', 'N/A')
    search_info_text.insert(tk.END, f"{t('info_summary')}: {description_text}\n\n")

    # KORREKTUR: Robuste URL-Extraktion mit .get() und mehreren Fallbacks
    project_urls = info.get('project_urls') or {}
    package_url = project_urls.get('Homepage') or \
                  project_urls.get('Home') or \
                  info.get('home_page') or 'N/A'
    search_info_text.insert(tk.END, f"{t('info_package_url')}: {package_url}\n\n")

    # KORREKTUR: Robuste URL-Extraktion für Dokumentation
    documentation_url = project_urls.get('Documentation') or 'N/A'
    search_info_text.insert(tk.END, f"{t('info_documentation')}: {documentation_url}\n\n")

    # "requires_dist"
    requires_dist_list = info.get('requires_dist')
    requires_dist = ", ".join(requires_dist_list) if requires_dist_list else 'N/A'
    search_info_text.insert(tk.END, f"{t('info_dependencies')}: {requires_dist}\n\n")

    # Spezifische file_data Details
    search_info_text.insert(tk.END, f"{t('info_filename')}: {file_data.get('filename', 'N/A')}\n\n")
    search_info_text.insert(tk.END, f"{t('info_md5')}: {file_data.get('md5_digest', 'N/A')}\n\n")
    search_info_text.insert(tk.END, f"{t('info_sha256')}: {file_data.get('digests', {}).get('sha256', 'N/A')}\n\n")
    search_info_text.insert(tk.END, f"{t('info_packagetype')}: {file_data.get('packagetype', 'N/A')}\n\n")
    search_info_text.insert(tk.END, f"{t('info_python_version')}: {file_data.get('python_version', 'N/A')}\n\n")
    search_info_text.insert(tk.END, f"{t('info_requires_python')}: {file_data.get('requires_python', 'N/A')}\n\n")

    # "size" (in KB)
    size_bytes = file_data.get('size')
    size_kb = f"{size_bytes / 1024:.2f} KB" if size_bytes is not None else 'N/A'
    search_info_text.insert(tk.END, f"{t('info_size')}: {size_kb}\n\n")

    # "upload_time" (formatiert)
    upload_time_str = file_data.get('upload_time_iso_8601')
    formatted_upload_time = 'N/A'
    fmt = "%Y-%m-%d %H:%M:%S" # KORREKTUR: Standardformat definieren
    if upload_time_str:
        try:
            dt_object = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
            # Datum entsprechend der Sprache formatieren
            if current_lang == "de":
                fmt = "%d.%m.%Y %H:%M:%S"
            elif current_lang == "en":
                fmt = "%Y-%m-%d %H:%M:%S" # Standard
            elif current_lang == "fr":
                fmt = "%d/%m/%Y %H:%M:%S"
            elif current_lang == "es":
                fmt = "%d/%m/%Y %H:%M:%S"
            elif current_lang == "ja":
                fmt = "%Y/%m/%d %H:%M:%S"
            formatted_upload_time = dt_object.strftime(fmt)
        except ValueError:
            formatted_upload_time = upload_time_str # Fallback, wenn das Parsen fehlschlägt
    search_info_text.insert(tk.END, f"{t('info_upload_time')}: {formatted_upload_time}\n\n")

    # "url"
    search_info_text.insert(tk.END, f"{t('info_url')}: {file_data.get('url', 'N/A')}\n\n")

    # "yanked" und "yanked_reason"
    yanked = file_data.get('yanked', False)
    search_info_text.insert(tk.END, f"{t('info_yanked_status')}: {yanked}\n")
    # KORREKTUR: Die auskommentierte Zeile wurde korrigiert und aktiviert.
    if yanked:
        search_info_text.insert(tk.END, f"{t('info_yanked_reason_full')}: {file_data.get('yanked_reason', 'N/A')}\n\n")

    # NEU: URLs im Such-Tab anklickbar machen
    def tag_url_in_widget(widget, label_key):
        line_start = widget.search(f"{t(label_key)}:", "1.0", tk.END)
        if line_start:
            url_start_index = widget.index(f"{line_start} + {len(t(label_key)) + 2}c") # noqa: E226
            url_end_index = widget.index(f"{line_start} lineend")
            url = widget.get(url_start_index, url_end_index).strip()
            if url.startswith("http"):
                widget.tag_add("hyperlink", url_start_index, url_end_index)

    # Wende das Tagging für die relevanten Felder an
    tag_url_in_widget(search_info_text, 'info_package_url')
    tag_url_in_widget(search_info_text, 'info_documentation')
    tag_url_in_widget(search_info_text, 'info_url')


    search_info_text.config(state=tk.DISABLED) # Textbox wieder schreibgeschützt

# --- Statusleiste am unteren Rand ---
status_frame = ttk.Frame(root)
status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
status_frame.columnconfigure(0, weight=1) # Linker Bereich für permanente Status
status_frame.columnconfigure(1, weight=2) # Rechter Bereich für temporäre Fortschrittsanzeigen

status_label = ttk.Label(status_frame, text=t("status_loading"), anchor="w")
status_label.grid(row=0, column=0, sticky="ew")

progress_label = ttk.Label(status_frame, text="", anchor="e")
progress_label.grid(row=0, column=1, sticky="ew")

# --- Datenabruf-Funktionen ---
def get_installed_packages():
    """
    Ruft die Liste aller installierten Pakete mit 'pip list' ab,
    füllt den Cache und gibt eine sortierte Liste der Paketnamen zurück.
    """
    global installed_packages_cache
    result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"],
                            capture_output=True, text=True, check=False)
    packages = sorted([line.split("==")[0] for line in result.stdout.splitlines()], key=str.lower)
    installed_packages_cache = packages  # Cache direkt hier füllen
    return packages
outdated_packages_cache = {} # Cache für veraltete Pakete

def load_outdated_packages():
    """Lädt die Liste der veralteten Pakete und speichert sie im Cache."""
    global outdated_packages_cache
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"],
                                 capture_output=True, text=True, check=False)
        outdated_list = {}
        # Die ersten beiden Zeilen (Header) überspringen
        for line in result.stdout.splitlines()[2:]:
            parts = line.split()
            if len(parts) >= 3:
                outdated_list[parts[0]] = {"current": parts[1], "latest": parts[2]}
        outdated_packages_cache = outdated_list
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"Fehler beim Prüfen auf veraltete Pakete: {e}")

def get_required_by(pkg_name):
    """
    Findet alle installierten Pakete, die von `pkg_name` abhängen (Reverse-Dependency-Check).
    Dies ist die programmatische Entsprechung zum 'Required-by'-Feld von 'pip show'.
    """
    requiring_packages = []
    # Normalisiere den Paketnamen für den Vergleich (ersetzt '_' durch '-')
    normalized_pkg_name = pkg_name.replace("_", "-").lower()

    for dist in importlib.metadata.distributions():
        if dist.requires:
            for req in dist.requires:
                # Extrahiere den reinen Namen der Anforderung (z.B. 'requests' aus 'requests>=2.0').
                req_name = req.split(' ')[0].split('[')[0].split(';')[0] \
                                .split('<')[0].split('>')[0].split('=')[0].strip()

                if req_name.replace("_", "-").lower() == normalized_pkg_name:
                    requiring_packages.append(dist.metadata['name'])
    return sorted(requiring_packages, key=str.lower)

def get_package_info(pkg_name):
    """Liest Paketinformationen direkt über importlib.metadata, ohne pip show aufzurufen."""
    # Diese Methode ist schneller und sicherer als 'pip show', da sie keine Dateien verändert.
    try:
        # Holt das Distribution-Objekt für das angegebene Paket.
        dist = importlib.metadata.distribution(pkg_name)
        # Greift auf die Metadaten des Pakets zu.
        metadata = dist.metadata

        # Baue einen String, der der Ausgabe von 'pip show' ähnelt
        info_lines = [
            f"{t('info_name')}: {metadata.get('Name', 'N/A')}",
            f"{t('info_version')} (installiert): {metadata.get('Version', 'N/A')}",
            f"{t('info_summary')}: {metadata.get('Summary', 'N/A')}",
            f"{t('info_homepage')}: {metadata.get('Project-URL: Homepage', 'N/A')}",
            f"{t('info_author')}: {metadata.get('Author-email', 'N/A')}",
            f"{t('info_license')}: {metadata.get('License', 'N/A')}",
            f"{t('info_location')}: {dist.locate_file('')}",
            f"{t('info_dependencies')}: {', '.join(dist.requires) if dist.requires else ''}",
            f"{t('info_required_by')}: {', '.join(get_required_by(pkg_name))}"
        ]
        return "\n\n".join(info_lines)
    except importlib.metadata.PackageNotFoundError:
        return t("no_info")

def get_pypi_info(pkg_name, version):
    """Ruft Paketinformationen von der PyPI JSON API ab."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        pypi_info = {}
        pypi_info['data'] = data.get('info', {})

        # Wenn eine spezifische Version angefragt wurde, suche nach Yanked-Status und Release-Datum
        if version:
            if version in data.get("releases", {}):
                release_data = data["releases"][version]
                if release_data:
                    # Nimm das Upload-Datum des ersten Release-Files
                    upload_time_str = release_data[0].get("upload_time_iso_8601")
                    if upload_time_str:
                        pypi_info["release_date"] = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))

                    # Prüfen, ob die spezifische Version "yanked" (zurückgezogen) ist
                    if release_data[0].get("yanked", False):
                        pypi_info["yanked"] = True
                        pypi_info["yanked_reason"] = release_data[0].get("yanked_reason", "N/A")
        # Wenn keine Version angegeben ist (für die Suche), nimm das Datum der neuesten Version
        else:
            latest_version = data.get('info', {}).get('version')
            if latest_version and latest_version in data.get("releases", {}):
                 release_data = data["releases"][latest_version]
                 if release_data:
                    upload_time_str = release_data[0].get("upload_time_iso_8601")
                    if upload_time_str:
                        pypi_info["release_date"] = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
        return pypi_info
    except (requests.exceptions.RequestException, ValueError):
        return None # Fehler bei der Netzwerkanfrage
def get_install_time(pkg_name):
    """Liest das Änderungsdatum des Metadaten-Verzeichnisses eines Pakets (Installationszeit)."""
    try:
        dist = importlib.metadata.distribution(pkg_name)
        path = dist.locate_file('')
        if path and os.path.exists(path):
            ts = os.path.getmtime(path)
            return datetime.datetime.fromtimestamp(ts)
    except (importlib.metadata.PackageNotFoundError, FileNotFoundError, OSError):
        pass
    return None

def update_listbox_safely(packages):
    """Aktualisiert die Listbox sicher aus dem Haupt-GUI-Thread, um Race Conditions zu vermeiden."""
    package_listbox.delete(0, tk.END)
    for pkg in packages:
        package_listbox.insert(tk.END, pkg)
    status_label.config(text=t("status_loaded").format(len(packages)))

def colorize_outdated_packages():
    """Geht die Paketliste durch und färbt veraltete Pakete ein."""
    if not outdated_packages_cache:
        return
    # Gehe jeden Eintrag in der Listbox durch
    for i in range(package_listbox.size()):
        pkg_name = package_listbox.get(i)
        if pkg_name in outdated_packages_cache:
            package_listbox.itemconfig(i, {'bg': '#B6F0A5'})  # Heller Grünton
        else:
            package_listbox.itemconfig(i, {'bg': ''}) # Standardhintergrund zurücksetzen

def load_packages():
    """
    Lädt zuerst die Liste der installierten Pakete und zeigt sie an.
    Sucht danach im Hintergrund nach veralteten Paketen.
    """
    log_message("Loading package lists...")

    try:
        # Schritt 1: Installierte Pakete laden und sofort in der GUI anzeigen.
        try:
            if root.winfo_exists():
                root.after(0, lambda: update_status_label("status_loading_installed"))
        except RuntimeError:
            return
        packages = get_installed_packages()
        try:
            if root.winfo_exists():
                root.after(0, lambda: update_listbox_safely(packages))
                root.after(0, lambda: update_status_label(None, show=False))
        except RuntimeError:
            return

        # Schritt 2: Jetzt die langsamere Suche nach veralteten Paketen durchführen.
        try:
            if root.winfo_exists():
                root.after(100, lambda: update_status_label("status_checking_updates"))
        except RuntimeError:
            return
        load_outdated_packages()

        # NEU: Nach dem Laden der veralteten Pakete die Liste einfärben.
        try:
            if root.winfo_exists():
                root.after(0, colorize_outdated_packages)
        except RuntimeError:
            pass

        # Schritt 3: Status-Label am Ende ausblenden.
        try:
            if root.winfo_exists():
                root.after(0, lambda: update_status_label(None, show=False))
        except RuntimeError:
            pass
    
        log_message("Finished loading all package data.")
    except (subprocess.SubprocessError, RuntimeError) as e:
        log_message(f"Error loading packages: {e}", level="ERROR")
        try:
            if status_label:
                status_label.config(text=f"Fehler: {e}")
        except (tk.TclError, RuntimeError):
            pass
    
# --- Event-Handler und GUI-Logik ---
def show_package_info(_event):
    selection = package_listbox.curselection()
    if not selection:
        return

    # NEU: Fortschritts-Label bei jeder neuen Auswahl sofort zurücksetzen
    if progress_label:
        progress_label.config(text="")

    pkg_name = package_listbox.get(selection[0])
    info_text.delete("1.0", tk.END)
    log_message(f"Fetching info for '{pkg_name}'")
    info_text.insert(tk.END, t("loading_info").format(pkg_name) + "\n")

    # Startet einen neuen Thread, um die Informationen zu laden, damit die GUI nicht blockiert wird.
    def fetch_and_show():
        # GUI-Updates werden über root.after() sicher im Hauptthread geplant.
        # Zuerst werden die dynamischen UI-Elemente zurückgesetzt.
        try:
            if root.winfo_exists(): # NEU: Nur noch den Button deaktivieren
                root.after(0, lambda: btn_install_deps.config(state=tk.DISABLED, command=None))
        except RuntimeError:
            return

        dist = importlib.metadata.distribution(pkg_name)
        # Sammelt alle Informationen zum Paket.
        info = get_package_info(pkg_name)
        install_time = get_install_time(pkg_name)
        pypi_info = get_pypi_info(pkg_name, dist.version)

        # Fehlende Abhängigkeiten prüfen
        missing_deps = []
        if dist.requires:
            # Normalisiere die Liste der installierten Pakete für einen robusten Vergleich
            # (kleingeschrieben, Unterstriche durch Bindestriche ersetzt). Ein Set ist schneller für die Suche.
            installed_normalized = {p.lower().replace("_", "-") for p in installed_packages_cache}
            for req in dist.requires:
                req_name = req.split(' ')[0].split('[')[0].split(';')[0] \
                                .split('<')[0].split('>')[0].split('=')[0].strip()

                # Normalisiere auch den Anforderungsnamen auf die gleiche Weise für einen korrekten Vergleich.
                if req_name.lower().replace("_", "-") not in installed_normalized:
                    missing_deps.append(req_name)

        if missing_deps:
            try:
                if root.winfo_exists():
                    root.after(
                        0, lambda: btn_install_deps.config(state=tk.NORMAL, command=lambda: install_dependencies(missing_deps))
                    )
            except RuntimeError: pass

        # Update-Informationen prüfen und anzeigen
        if pkg_name in outdated_packages_cache:
            update_info = outdated_packages_cache[pkg_name]
            update_text = t("update_available").format(update_info['current'], update_info['latest'])
            try: # NEU: Update-Info im zentralen Fortschrittslabel anzeigen
                if root.winfo_exists() and progress_label:
                    root.after(0, lambda: progress_label.config(text=update_text))
            except RuntimeError: pass

        try:
            if root.winfo_exists():

                # Hauptinformationen einfügen
                info_text.delete("1.0", tk.END)
                info_text.insert(tk.END, info + "\n\n")

                if pypi_info:
                    if "release_date" in pypi_info:
                        info_text.insert(
                            tk.END, f"{t('info_release_date')}: {pypi_info['release_date'].strftime('%d.%m.%Y')}\n"
                        )
                    if pypi_info.get("yanked"):
                        info_text.insert(tk.END, f"\n{t('info_yanked')}\n", "yanked_warning")
                        info_text.insert(
                            tk.END, f"{t('info_yanked_reason')}: {pypi_info.get('yanked_reason')}\n"
                        )

                # NEU: Update-Hinweis direkt unter der Version einfügen
                if pkg_name in outdated_packages_cache:
                    update_info = outdated_packages_cache[pkg_name]
                    update_text = t("update_available").format(update_info['current'], update_info['latest'])
                    # Suche die Zeile mit der installierten Version
                    version_line_start = info_text.search(f"{t('info_version')} (installiert):", "1.0", tk.END)
                    if version_line_start:
                        # Füge den Hinweis in der Zeile danach ein
                        line_end_index = info_text.index(f"{version_line_start} lineend")
                        info_text.insert(f"{line_end_index}\n", f"  -> {update_text}\n", "update_info")
                if install_time:
                    fmt = "%Y-%m-%d %H:%M:%S" # Standardformat
                    # Datum entsprechend der Sprache formatieren
                    if current_lang == "de": fmt = "%d.%m.%Y %H:%M:%S"
                    elif current_lang == "en": fmt = "%Y-%m-%d %H:%M:%S"
                    elif current_lang == "fr": fmt = "%d/%m/%Y %H:%M:%S"
                    elif current_lang == "es": fmt = "%d/%m/%Y %H:%M:%S"
                    elif current_lang == "ja": fmt = "%Y/%m/%d %H:%M:%S"
                    info_text.insert(tk.END, f"\n{t('install_time').format(install_time.strftime(fmt))}\n")
                else:
                    info_text.insert(
                        tk.END, "\n" + t("no_install_time") + "\n"
                    )

                # NEU: URLs anklickbar machen
                homepage_line_start = info_text.search(f"{t('info_homepage')}:", "1.0", tk.END)
                if homepage_line_start:
                    # Finde den Start der URL (nach "Homepage: ")
                    url_start_index = info_text.index(f"{homepage_line_start} + {len(t('info_homepage')) + 2}c")
                    # Finde das Ende der Zeile
                    url_end_index = info_text.index(f"{homepage_line_start} lineend")
                    # Hole die URL und prüfe, ob sie gültig ist
                    url = info_text.get(url_start_index, url_end_index).strip()
                    if url.startswith("http"):
                        # Füge das 'hyperlink'-Tag hinzu
                        info_text.tag_add("hyperlink", url_start_index, url_end_index)

                if missing_deps:
                    info_text.insert(
                        tk.END, "\n" + t("missing_deps_info").format(", ".join(missing_deps)) + "\n"
                    )
        except RuntimeError: pass

    threading.Thread(target=fetch_and_show, daemon=True).start()

def open_url_from_text(_event):
    """Öffnet eine URL, die mit dem 'hyperlink'-Tag markiert ist, im Browser."""
    # Hole den Index des Klicks
    index = _event.widget.index(f"@{_event.x},{_event.y}")

    # Finde die Bereiche, die mit 'hyperlink' getaggt sind
    tag_ranges = _event.widget.tag_ranges("hyperlink")

    # Prüfe, ob der Klick innerhalb eines dieser Bereiche war
    for i in range(0, len(tag_ranges), 2):
        start, end = tag_ranges[i], tag_ranges[i+1]
        if _event.widget.compare(index, ">=", start) and _event.widget.compare(index, "<", end):
            url = _event.widget.get(start, end).strip()
            if url.startswith("http"):
                log_message(f"Opening URL: {url}")
                webbrowser.open_new_tab(url)
            else:
                log_message(f"Not a valid URL to open: {url}", "WARNING")
            return

def setup_text_widget_tags(text_widget):
    """Definiert die Tags für die farbliche Hervorhebung und Hyperlinks für ein gegebenes Text-Widget."""
    text_widget.tag_config("update_info", foreground="#006400", font=("Segoe UI", 9, "bold"))
    text_widget.tag_config("yanked_warning", foreground="red", font=("Segoe UI", 9, "bold"))

    # Tags für Hyperlinks einrichten
    text_widget.tag_config("hyperlink", foreground="blue", underline=True)
    text_widget.tag_bind("hyperlink", "<Enter>", lambda e, w=text_widget: w.config(cursor="hand2"))
    text_widget.tag_bind("hyperlink", "<Leave>", lambda e, w=text_widget: w.config(cursor=""))
    text_widget.tag_bind("hyperlink", "<Button-1>", open_url_from_text)

def load_python_versions():
    """Sucht mit dem 'py' Launcher nach allen installierten Python-Versionen und zeigt sie an."""

    def do_load_versions():
        try:
            result = subprocess.run(["py", "-0p"], capture_output=True, text=True, check=False)
            lines = result.stdout.splitlines() if result.returncode == 0 else ["Python-Launcher (py.exe) nicht gefunden."]
        except FileNotFoundError:
            lines = ["Python-Launcher (py.exe) nicht gefunden."]

        # GUI-Updates sicher im Hauptthread ausführen
        def update_gui():
            global python_versions_cache
            python_versions_cache.clear()

            # Aktualisiere Textfeld in Tab 1
            py_version_text.config(state=tk.NORMAL)
            py_version_text.delete("1.0", tk.END)
            for line in lines:
                py_version_text.insert(tk.END, line.strip() + "\n")
            py_version_text.config(state=tk.DISABLED)

        try:
            if root.winfo_exists():
                root.after(0, update_gui)
        except RuntimeError:
            pass # GUI wurde bereits geschlossen

    threading.Thread(target=do_load_versions, daemon=True).start()

# --- Sprache wechseln ---
def change_language(_event=None):
    """Aktualisiert alle textbasierten Widgets in der GUI mit den Texten der ausgewählten Sprache."""
    global current_lang
    selected_display_name = lang_var.get()
    # KORREKTUR: Findet den Sprachcode (z.B. "de") zum Anzeigenamen (z.B. "Deutsch")
    for code, display_name in lang_display_names.items():
        if display_name == selected_display_name:
            current_lang = code
            break

    root.title(t("title"))
    lang_label.config(text=t("lang_label"))
    btn_uninstall.config(text=t("btn_uninstall"))
    btn_update.config(text=t("btn_update"))
    btn_reinstall.config(text=t("btn_reinstall"))
    btn_refresh.config(text=t("btn_refresh"))
    btn_show_log.config(text=t("btn_show_log"))
    btn_install_deps.config(text=t("btn_install_deps"))
    status_label.config(text=t("status_loading"))

    # Tab 1
    notebook.tab(tab1, text=t("tab_manage"))
    frame_left.config(text=t("frame_left_title"))
    info_frame.config(text=t("frame_right_title"))
    py_version_frame.config(text=t("python_versions_title"))

    # Tab 2
    notebook.tab(tab2, text=t("tab_search"))
    search_bar_frame.config(text=t("search_label"))
    search_button.config(text=t("search_button"))
    search_results_frame.config(text=t("search_results_title"))
    search_info_frame.config(text=t("search_info_title"))
    install_frame.config(text=t("install_frame_title"))
    btn_install_selected.config(text=t("btn_install_selected_version"))

    # Aktualisiere den Tooltip-Text, falls er existiert
    if icon_tooltip: # NEU: Tooltip-Text aktualisieren
        icon_tooltip.update_text(t("homepage_tooltip"))
    btn_frame.config(text=t("actions_frame_title"))
    search_versions_frame.config(text=t("search_versions_title")) # NEU: Versions-Frame Titel aktualisieren

# --- Event-Bindungen ---
lang_combo.bind("<<ComboboxSelected>>", change_language)
package_listbox.bind("<<ListboxSelect>>", show_package_info) # noqa: E1120
search_button.config(command=perform_search)
search_entry.bind("<Return>", perform_search) # Suche bei Enter-Tastendruck
search_results_listbox.bind("<<ListboxSelect>>", show_package_versions) # NEU: Bindung an show_package_versions
search_versions_listbox.bind("<<ListboxSelect>>", show_version_details) # NEU: Bindung an show_version_details
# NEU: Tags für beide Infofenster einmalig einrichten
setup_text_widget_tags(info_text)
setup_text_widget_tags(search_info_text)

log_message("Application started.")

# --- Start der Anwendung ---
# Startet die initialen Ladevorgänge in Hintergrundthreads.
threading.Thread(target=load_packages, daemon=True).start()
threading.Thread(target=load_pypi_index, daemon=True).start()
current_system_tags = get_current_system_tags_set() # NEU: System-Tags beim Start laden
threading.Thread(target=load_python_versions, daemon=True).start()

# Startet die Haupt-Ereignisschleife von Tkinter. Das Programm wartet hier auf Benutzerinteraktionen.
root.mainloop()
