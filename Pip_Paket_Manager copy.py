"""
Ein GUI-Tool zur Verwaltung von Python-Paketen mit Pip, das eine grafische
Oberfläche für die Installation, Deinstallation, Aktualisierung und Suche von
Paketen bietet.
"""
# pylint: disable=invalid-name, too-many-lines
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
import json
import hashlib
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
        "title": "Pip Paket-Manager", "status_loading": "Pakete werden geladen…", "status_loaded": "{} Pakete geladen.",
        "btn_uninstall": "Deinstallieren", "btn_update": "Update", "btn_reinstall": "Reinstallieren", "btn_refresh": "Liste aktualisieren",
        "confirm_uninstall": "Soll '{}' wirklich deinstalliert werden?", "no_info": "Keine Informationen gefunden.", "install_frame_title": "Installation",
        "loading_info": "Lade Informationen für '{}'…", "btn_install_deps": "Abhängigkeiten installieren",
        "btn_show_log": "Log anzeigen", "log_title": "Pip-Ausgabe", "missing_deps_info": "Fehlende Abhängigkeiten: {}", "btn_install_selected_version": "Ausgewählte Version installieren",
        "update_available": "Update verfügbar: {} -> {}", "install_time": "Installationszeit (aus .dist-info): {}", "confirm_install": "Möchten Sie '{pkg_name}=={version}' installieren?",
        "no_install_time": "Installationszeit: nicht ermittelbar (keine .dist-info gefunden)", "lang_label": "Sprache:",
        "frame_left_title": "Installierte Pakete", "frame_right_title": "Informationen (Lokal)", "actions_frame_title": "Aktionen", "homepage_tooltip": "PyPi Homepage besuchen",
        "search_searching": "Suche läuft...", "search_no_results": "Keine Ergebnisse für '{}' gefunden.", "search_error": "Fehler bei der Suche: {}", "info_latest_version": "Neueste Version", "info_dependencies": "Abhängigkeiten",
        "tab_manage": "Paketverwaltung", "tab_search": "Suche", "search_label": "Paket auf PyPI suchen:",
        "search_button": "Suchen", "search_results_title": "Suchergebnisse", "search_info_title": "Paketdetails (Online)",
        "search_versions_title": "Verfügbare Versionen", "search_no_compatible_versions": "Keine kompatiblen Versionen gefunden.",
        "python_versions_title": "Installierte Python-Versionen",
        "status_checking_updates": "Suche nach veralteten Paketen…", "status_loading_installed": "Lade installierte Pakete…", "status_loading_index": "Lade PyPI-Paketindex...", "progress_frame_title": "Fortschritt",
        "admin_rights_title": "Administratorrechte", "admin_rights_required_msg": "Für '{pkg_name}' sind Administratorrechte erforderlich.",
        "selection_required_title": "Auswahl erforderlich", "select_python_version_msg": "Bitte wählen Sie zuerst eine Python-Version aus der Liste aus.",
        "enter_package_name_prompt": "Geben Sie den Paketnamen für Python {version_tag_display} ein:", "selected_version_fallback": "ausgewählte Version",
        "select_package_version_first_msg": "Bitte wählen Sie zuerst eine Version aus der Versionsliste aus.", "error_title": "Fehler", "version_details_not_found_msg": "Konnte Details zur ausgewählten Version nicht finden.",
        "info_name": "Name", "info_version": "Version", "info_summary": "Zusammenfassung", "info_homepage": "Homepage",
        "info_author": "Autor", "info_license": "Lizenz", "info_location": "Speicherort", "info_requires": "Benötigt", "info_release_date": "Release-Datum",
        "info_yanked": "WARNUNG: Diese Version wurde zurückgezogen!", "info_yanked_reason": "Grund",
        "info_required_by": "Benötigt von","info_package_url": "Paket-URL", "info_documentation": "Dokumentation", "info_filename": "Dateiname",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Pakettyp", "info_python_version": "Python-Version",
        "info_requires_python": "Benötigt Python", "info_size": "Größe", "info_upload_time": "Upload-Zeit", "info_url": "URL", "update_title": "Update verfügbar",
        "update_message": "Eine neue Version des Pip Paket-Managers ist verfügbar. Möchten Sie jetzt aktualisieren?",
        "update_btn_now": "Jetzt",
        "update_btn_later": "Später",
        "update_btn_no": "Nein",
        "info_yanked_status": "Zurückgezogen", "info_yanked_reason_full": "Grund für Zurückziehung"
    },
    "en": {
        "title": "Pip Package Manager", "status_loading": "Loading packages…", "status_loaded": "{} packages loaded.",
        "btn_uninstall": "Uninstall", "btn_update": "Update", "btn_reinstall": "Reinstall", "btn_refresh": "Refresh list",
        "confirm_uninstall": "Really uninstall '{}'?", "no_info": "No information found.", "install_frame_title": "Installation",
        "loading_info": "Loading info for '{}' …", "btn_install_deps": "Install Dependencies", "btn_show_log": "Show Log",
        "log_title": "Pip Output", "missing_deps_info": "Missing Dependencies: {}", "btn_install_selected_version": "Install Selected Version", "confirm_install": "Do you want to install '{pkg_name}=={version}'?",
        "update_available": "Update available: {} -> {}", "install_time": "Install time (from .dist-info): {}",
        "no_install_time": "Install time: not available (no .dist-info found)", "lang_label": "Language:",
        "frame_left_title": "Installed Packages", "frame_right_title": "Information (Local)", "actions_frame_title": "Actions", "homepage_tooltip": "Visit PyPI homepage",
        "search_versions_title": "Available Versions", "search_no_compatible_versions": "No compatible versions found.",
        "search_searching": "Searching...", "search_no_results": "No results found for '{}'.", "search_error": "Search error: {}", "info_latest_version": "Latest Version", "info_dependencies": "Dependencies",
        "tab_manage": "Package Management", "tab_search": "Search", "search_label": "Search for package on PyPI:", "progress_frame_title": "Progress",
        "search_button": "Search", "search_results_title": "Search Results", "search_info_title": "Package Details (Online)",
        "admin_rights_title": "Administrator Rights", "admin_rights_required_msg": "Administrator rights are required for '{pkg_name}'.",
        "selection_required_title": "Selection Required", "select_python_version_msg": "Please select a Python version from the list first.",
        "enter_package_name_prompt": "Enter the package name for Python {version_tag_display}:", "selected_version_fallback": "selected version",
        "select_package_version_first_msg": "Please select a version from the version list first.", "error_title": "Error", "version_details_not_found_msg": "Could not find details for the selected version.",
        "python_versions_title": "Installed Python Versions",
        "status_checking_updates": "Checking for outdated packages…", "status_loading_installed": "Loading installed packages…",
        "info_name": "Name", "info_version": "Version", "info_summary": "Summary", "info_homepage": "Home-page",
        "info_author": "Author", "info_license": "License", "info_location": "Location", "info_requires": "Requires", "info_release_date": "Release Date",
        "info_yanked": "WARNING: This version has been yanked!", "info_yanked_reason": "Reason", # Keep these for local info
        "info_required_by": "Required-by","info_package_url": "Package URL", "info_documentation": "Documentation", "info_filename": "Filename",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Package Type", "info_python_version": "Python Version", "update_title": "Update Available",
        "update_message": "A new version of the Pip Package Manager is available. Do you want to update now?",
        "update_btn_now": "Now",
        "update_btn_later": "Later",
        "update_btn_no": "No",
        "info_requires_python": "Requires Python", "info_size": "Size", "info_upload_time": "Upload Time", "info_url": "URL",
        "info_yanked_status": "Yanked", "info_yanked_reason_full": "Yanked Reason"
    },
    "fr": {
        "title": "Gestionnaire de paquets Pip", "status_loading": "Chargement des paquets…", "status_loaded": "{} paquets chargés.",
        "btn_uninstall": "Désinstaller", "btn_update": "Mettre à jour", "btn_reinstall": "Réinstaller", "btn_refresh": "Actualiser la liste",
        "confirm_uninstall": "Voulez-vous vraiment désinstaller '{}' ?", "no_info": "Aucune information trouvée.", "install_frame_title": "Installation",
        "loading_info": "Chargement des informations sur '{}' …", "btn_install_deps": "Installer les dépendances", "btn_show_log": "Afficher le journal",
        "log_title": "Sortie de Pip", "missing_deps_info": "Dépendances manquantes: {}", "btn_install_selected_version": "Installer la version sélectionnée", "confirm_install": "Voulez-vous installer '{pkg_name}=={version}' ?",
        "update_available": "Mise à jour disponible: {} -> {}", "install_time": "Heure d’installation (.dist-info): {}",
        "no_install_time": "Heure d’installation introuvable (pas de .dist-info)", "lang_label": "Langue :",
        "frame_left_title": "Paquets Installés", "frame_right_title": "Informations (Local)", "actions_frame_title": "Actions", "homepage_tooltip": "Visiter la page d'accueil de PyPI",
        "search_versions_title": "Versions disponibles", "search_no_compatible_versions": "Aucune version compatible trouvée.",
        "search_searching": "Recherche en cours...", "search_no_results": "Aucun résultat pour '{}'.", "search_error": "Erreur de recherche: {}", "info_latest_version": "Dernière version", "info_dependencies": "Dépendances", "status_loading_index": "Chargement de l'index des paquets PyPI...",
        "tab_manage": "Gestion des paquets", "tab_search": "Recherche", "search_label": "Chercher un paquet sur PyPI:", "progress_frame_title": "Progression",
        "search_button": "Chercher", "search_results_title": "Résultats de recherche", "search_info_title": "Détails du paquet (En ligne)",
        "admin_rights_title": "Droits d'administrateur", "admin_rights_required_msg": "Des droits d'administrateur sont requis pour '{pkg_name}'.",
        "selection_required_title": "Sélection requise", "select_python_version_msg": "Veuillez d'abord sélectionner une version de Python dans la liste.",
        "enter_package_name_prompt": "Entrez le nom du paquet pour Python {version_tag_display}:", "selected_version_fallback": "version sélectionnée",
        "select_package_version_first_msg": "Veuillez d'abord sélectionner une version dans la liste des versions.", "error_title": "Erreur", "version_details_not_found_msg": "Impossible de trouver les détails de la version sélectionnée.",
        "python_versions_title": "Versions Python installées",
        "status_checking_updates": "Recherche de paquets obsolètes…", "status_loading_installed": "Chargement des paquets installés…",
        "info_name": "Nom", "info_version": "Version", "info_summary": "Résumé", "info_homepage": "Page d'accueil",
        "info_author": "Auteur", "info_license": "Licence", "info_location": "Emplacement", "info_requires": "Requiert", "info_release_date": "Date de sortie",
        "info_yanked": "ATTENTION : Cette version a été retirée !", "info_yanked_reason": "Raison", # Keep these for local info
        "info_required_by": "Requis par","info_package_url": "URL du paquet", "info_documentation": "Documentation", "info_filename": "Nom de fichier",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Type de paquet", "info_python_version": "Version Python", "update_title": "Mise à jour disponible",
        "update_message": "Une nouvelle version du Gestionnaire de paquets Pip est disponible. Voulez-vous mettre à jour maintenant ?",
        "update_btn_now": "Maintenant",
        "update_btn_later": "Plus tard",
        "update_btn_no": "Non",
        "info_requires_python": "Nécessite Python", "info_size": "Taille", "info_upload_time": "Heure de téléchargement", "info_url": "URL",
        "info_yanked_status": "Retiré", "info_yanked_reason_full": "Raison du retrait"
    },
    "es": {
        "title": "Administrador de paquetes Pip", "status_loading": "Cargando paquetes…", "status_loaded": "{} paquetes cargados.",
        "btn_uninstall": "Desinstalar", "btn_update": "Actualizar", "btn_reinstall": "Reinstalar", "btn_refresh": "Actualizar lista",
        "confirm_uninstall": "¿Realmente desea desinstalar '{}'?", "no_info": "No se encontró información.", "install_frame_title": "Instalación",
        "loading_info": "Cargando información para '{}' …", "btn_install_deps": "Instalar dependencias", "btn_show_log": "Mostrar registro",
        "log_title": "Salida de Pip", "missing_deps_info": "Dependencias faltantes: {}", "btn_install_selected_version": "Instalar versión seleccionada", "confirm_install": "¿Quieres instalar '{pkg_name}=={version}'?",
        "update_available": "Actualización disponible: {} -> {}", "install_time": "Hora de instalación (.dist-info): {}",
        "no_install_time": "Hora de instalación no disponible (sin .dist-info)", "lang_label": "Idioma:",
        "frame_left_title": "Paquetes Instalados", "frame_right_title": "Información (Local)", "actions_frame_title": "Acciones", "homepage_tooltip": "Visitar la página de inicio de PyPI",
        "search_versions_title": "Versiones disponibles", "search_no_compatible_versions": "No se encontraron versiones compatibles.",
        "search_searching": "Buscando...", "search_no_results": "No se encontraron resultados para '{}'.", "search_error": "Error de búsqueda: {}", "info_latest_version": "Última versión", "info_dependencies": "Dependencias", "status_loading_index": "Cargando índice de paquetes de PyPI...",
        "tab_manage": "Gestión de Paquetes", "tab_search": "Búsqueda", "search_label": "Buscar paquete en PyPI:", "progress_frame_title": "Progreso",
        "search_button": "Buscar", "search_results_title": "Resultados de Búsqueda", "search_info_title": "Detalles del Paquete (Online)",
        "admin_rights_title": "Derechos de administrador", "admin_rights_required_msg": "Se requieren derechos de administrador para '{pkg_name}'.",
        "selection_required_title": "Selección requerida", "select_python_version_msg": "Por favor, seleccione primero una versión de Python de la lista.",
        "enter_package_name_prompt": "Introduzca el nombre del paquete para Python {version_tag_display}:", "selected_version_fallback": "versión seleccionada",
        "select_package_version_first_msg": "Por favor, seleccione primero una versión de la lista de versiones.", "error_title": "Error", "version_details_not_found_msg": "No se pudieron encontrar los detalles de la versión seleccionada.",
        "python_versions_title": "Versiones de Python instaladas",
        "status_checking_updates": "Buscando paquetes obsoletos…", "status_loading_installed": "Cargando paquetes instalados…",
        "info_name": "Nombre", "info_version": "Versión", "info_summary": "Resumen", "info_homepage": "Página de inicio",
        "info_author": "Autor", "info_license": "Licencia", "info_location": "Ubicación", "info_requires": "Requiere", "info_release_date": "Fecha de lanzamiento",
        "info_yanked": "¡ADVERTENCIA: Esta versión ha sido retirada!", "info_yanked_reason": "Razón", # Keep these for local info
        "info_required_by": "Requerido por","info_package_url": "URL del paquete", "info_documentation": "Documentación", "info_filename": "Nombre de archivo",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "Tipo de paquete", "info_python_version": "Versión de Python", "update_title": "Actualización disponible",
        "update_message": "Una nueva versión del Administrador de paquetes Pip está disponible. ¿Desea actualizar ahora?",
        "update_btn_now": "Ahora",
        "update_btn_later": "Más tarde",
        "update_btn_no": "No",
        "info_requires_python": "Requiere Python", "info_size": "Tamaño", "info_upload_time": "Hora de subida", "info_url": "URL",
        "info_yanked_status": "Retirado", "info_yanked_reason_full": "Razón del retiro"
    },
    "zh": {
        "title": "Pip 软件包管理器", "status_loading": "正在加载软件包…", "status_loaded": "已加载 {} 个软件包。",
        "btn_uninstall": "卸载", "btn_update": "更新", "btn_reinstall": "重新安装", "btn_refresh": "刷新列表",
        "confirm_uninstall": "确定要卸载 '{}' 吗？", "no_info": "未找到信息。", "install_frame_title": "安装",
        "loading_info": "正在加载 '{}' 的信息…", "btn_install_deps": "安装依赖",
        "btn_show_log": "显示日志", "log_title": "Pip 输出", "missing_deps_info": "缺少依赖: {}", "btn_install_selected_version": "安装所选版本", "confirm_install": "你要安装 '{pkg_name}=={version}'吗？",
        "update_available": "可用更新: {} -> {}", "install_time": "安装时间 (.dist-info): {}",
        "no_install_time": "无法确定安装时间（没有 .dist-info）", "lang_label": "语言：",
        "frame_left_title": "已安装的软件包", "frame_right_title": "信息 (本地)", "actions_frame_title": "操作", "homepage_tooltip": "访问 PyPI 主页",
        "search_versions_title": "可用版本", "search_no_compatible_versions": "未找到兼容版本。",
        "search_searching": "正在搜索...", "search_no_results": "未找到 '{}' 的结果。", "search_error": "搜索出错: {}", "info_latest_version": "最新版本", "info_dependencies": "依赖关系", "status_loading_index": "正在加载 PyPI 包索引...",
        "tab_manage": "软件包管理", "tab_search": "搜索", "search_label": "在 PyPI 上搜索包:", "progress_frame_title": "进度",
        "search_button": "搜索", "search_results_title": "搜索结果", "search_info_title": "包详细信息 (在线)",
        "admin_rights_title": "管理员权限", "admin_rights_required_msg": "需要管理员权限才能操作 '{pkg_name}'。",
        "selection_required_title": "需要选择", "select_python_version_msg": "请先从列表中选择一个 Python 版本。",
        "enter_package_name_prompt": "请输入 Python {version_tag_display} 的软件包名称：", "selected_version_fallback": "所选版本",
        "select_package_version_first_msg": "请先从版本列表中选择一个版本。", "error_title": "错误", "version_details_not_found_msg": "找不到所选版本的详细信息。",
        "python_versions_title": "已安装的 Python 版本",
        "status_checking_updates": "正在检查过时的软件包…", "status_loading_installed": "正在加载已安装的软件包…",
        "info_name": "名称", "info_version": "版本", "info_summary": "摘要", "info_homepage": "主页",
        "info_author": "作者", "info_license": "许可证", "info_location": "位置", "info_requires": "需要", "info_release_date": "发布日期",
        "info_yanked": "警告：此版本已被撤回！", "info_yanked_reason": "原因", # Keep these for local info
        "info_required_by": "被需要", "info_package_url": "软件包网址", "info_documentation": "文档", "info_filename": "文件名",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "软件包类型", "info_python_version": "Python 版本", "update_title": "有可用更新",
        "update_message": "Pip 软件包管理器有新版本可用。您想现在更新吗？",
        "update_btn_now": "现在",
        "update_btn_later": "稍后",
        "update_btn_no": "不",
        "info_requires_python": "需要 Python", "info_size": "大小", "info_upload_time": "上传时间", "info_url": "网址",
        "info_yanked_status": "已撤回", "info_yanked_reason_full": "撤回原因",
    },
    "ja": {
        "title": "Pip パッケージマネージャー", "status_loading": "パッケージを読み込み中…", "status_loaded": "{} 個のパッケージを読み込みました。",
        "btn_uninstall": "アンインストール", "btn_update": "更新", "btn_reinstall": "再インストール", "btn_refresh": "リストを更新",
        "confirm_uninstall": "'{}' を本当にアンインストールしますか？", "no_info": "情報が見つかりません。", "install_frame_title": "インストール",
        "loading_info": "'{}' の情報を読み込み中…", "btn_install_deps": "依存関係をインストール",
        "btn_show_log": "ログを表示", "log_title": "Pip 出力", "missing_deps_info": "不足している依存関係: {}", "btn_install_selected_version": "選択したバージョンをインストール", "confirm_install": "'{pkg_name}=={version}' をインストールしますか？",
        "update_available": "利用可能なアップデート: {} -> {}", "install_time": "インストール日時 (.dist-info): {}",
        "no_install_time": "インストール日時を取得できません（.dist-info がありません）", "lang_label": "言語：",
        "frame_left_title": "インストールされたパッケージ", "frame_right_title": "情報 (ローカル)", "actions_frame_title": "アクション", "homepage_tooltip": "PyPIホームページにアクセス",
        "search_versions_title": "利用可能なバージョン", "search_no_compatible_versions": "互換性のあるバージョンが見つかりませんでした。",
        "search_searching": "検索中...", "search_no_results": "'{}' の結果が見つかりませんでした。", "search_error": "検索エラー: {}", "info_latest_version": "最新バージョン", "info_dependencies": "依存関係", "status_loading_index": "PyPIパッケージインデックスを読み込んでいます...",
        "tab_manage": "パッケージ管理", "tab_search": "検索", "search_label": "PyPIでパッケージを検索:", "progress_frame_title": "進捗",
        "search_button": "検索", "search_results_title": "検索結果", "search_info_title": "パッケージの詳細 (オンライン)",
        "admin_rights_title": "管理者権限", "admin_rights_required_msg": "'{pkg_name}' には管理者権限が必要です。",
        "selection_required_title": "選択が必要です", "select_python_version_msg": "最初にリストからPythonバージョンを選択してください。",
        "enter_package_name_prompt": "Python {version_tag_display} のパッケージ名を入力してください：", "selected_version_fallback": "選択したバージョン",
        "select_package_version_first_msg": "最初にバージョンリストからバージョンを選択してください。", "error_title": "エラー", "version_details_not_found_msg": "選択したバージョンの詳細が見つかりませんでした。",
        "python_versions_title": "インストールされた Python バージョン",
        "status_checking_updates": "古いパッケージを確認しています…", "status_loading_installed": "インストール済みのパッケージを読み込んでいます…",
        "info_name": "名前", "info_version": "バージョン", "info_summary": "概要", "info_homepage": "ホームページ",
        "info_author": "作者", "info_license": "ライセンス", "info_location": "場所", "info_requires": "依存関係", "info_release_date": "リリース日",
        "info_yanked": "警告：このバージョンは取り下げられました！", "info_yanked_reason": "理由", # Keep these for local info
        "info_required_by": "被依存関係", "info_package_url": "パッケージURL", "info_documentation": "ドキュメント", "info_filename": "ファイル名",
        "info_md5": "MD5", "info_sha256": "SHA256", "info_packagetype": "パッケージタイプ", "info_python_version": "Pythonバージョン", "update_title": "アップデートがあります",
        "update_message": "Pip パッケージマネージャーの新しいバージョンが利用可能です。今すぐアップデートしますか？",
        "update_btn_now": "今すぐ",
        "update_btn_later": "後で",
        "update_btn_no": "いいえ",
        "info_requires_python": "必要なPython", "info_size": "サイズ", "info_upload_time": "アップロード時間", "info_url": "URL",
        "info_yanked_status": "取り下げ済み", "info_yanked_reason_full": "取り下げ理由"
    }
}

# -----------------------------------------------------------------------------
# --- HILFSKLASSEN UND -FUNKTIONEN (ZUSTANDSLOS) ---
# -----------------------------------------------------------------------------

class ToolTip:
    """Erstellt einen Tooltip für ein gegebenes Widget."""
    def __init__(self, widget, text):
        """Initialisiert a tooltip for a given widget.
        Parameters
        ----------
        widget : tkinter.Widget
            The widget for which the tooltip is created.
        text : str
            The text that is displayed in the tooltip.
        """
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def update_text(self, new_text):
        """Aktualisiert den Text des Tooltips."""
        self.text = new_text

    def show_tooltip(self, event=None):
        """Zeigt das Tooltip-Fenster an."""
        if self.tooltip_window or not self.text:
            return
        x = y = 0
        if event and getattr(event, "x_root", None) is not None:
            x = event.x_root + 20
            y = event.y_root + 20
        else:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + 20

        try:
            self.tooltip_window = tk.Toplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            label = tk.Label(self.tooltip_window, text=self.text, justify='left',
                             background="#ffffe0", relief='solid', borderwidth=1,
                             font=("tahoma", "8", "normal"))
            label.pack(ipadx=1)
        except (tk.TclError, RuntimeError):
            self.tooltip_window = None

    def hide_tooltip(self, _event=None):
        """Versteckt das Tooltip-Fenster."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except (tk.TclError, RuntimeError):
                pass
        self.tooltip_window = None

def resource_path(relative_path):
    """Ermittelt den absoluten Pfad zu einer Ressource (für PyInstaller)."""
    try:
        # pylint: disable=protected-access
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def is_admin():
    """Prüft, ob das Skript mit Administratorrechten läuft."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except AttributeError:
        return False

def get_package_path(pkg_name: str) -> str:
    """Gibt den Installationspfad eines Pakets zurück."""
    try:
        dist = importlib.metadata.distribution(pkg_name)
        return str(dist.locate_file(''))
    except importlib.metadata.PackageNotFoundError:
        return ""

def get_current_system_tags_set():
    """Gibt eine Menge von kompatiblen Wheel-Tags für das aktuelle System zurück."""
    return set(packaging.tags.sys_tags())

# -----------------------------------------------------------------------------
# --- HAUPTANWENDUNGSKLASSE ---
# -----------------------------------------------------------------------------

class PipPackageManager:
    """Kapselt die gesamte Logik und die GUI des Pip Paket-Managers."""

    # --- Konfiguration für die Update-Prüfung ---
    # Bitte anpassen: 'YourUsername/YourRepo'
    GITHUB_REPO = "Maximus1/Pip-Paket-Manager"
    # Der Dateiname des Skripts im Repository
    SCRIPT_FILENAME = "Pip_Paket_Manager.py"

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
            print("Warnung: PyPi-128px.ico nicht gefunden.")

        # --- Anwendungszustand (ersetzt globale Variablen) ---
        self.current_lang = "de"
        self.log_records = []
        self.pypi_index_cache = []
        self.pypi_package_releases_cache = {}
        self.installed_packages_cache = []
        self.pypi_cache_path = self._get_cache_path()
        self.new_script_content = None
        self.update_on_exit = False
        self.script_path = os.path.abspath(__file__)
        self.outdated_packages_cache = {}
        self.current_system_tags = get_current_system_tags_set()
        self.current_package_version_details_cache = {}
        self.current_searched_pkg_name = None

        # --- GUI-Elemente ---
        self.notebook = None
        self.package_listbox = None
        self.info_text = None
        self.py_version_text = None
        self.search_entry_var = tk.StringVar()
        self.search_results_listbox = None
        self.search_versions_listbox = None
        self.search_info_text = None
        self.status_label = None
        self.progress_label = None
        self.lang_var = tk.StringVar(value="Deutsch")
        self.log_window = None
        self.btn_install_deps = None
        self.icon_tooltip = None
        self.progress_bar_tab1 = None
        self.progress_bar_tab2 = None
        self.progress_frame_tab1 = None

        # --- Initialisierung ---
        self._create_widgets()
        self.change_language()  # Initiales Setzen der Texte
        self.log_message("Application started.")
        self._start_background_tasks()

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    def t(self, key):
        """Gibt den übersetzten Text für einen Schlüssel zurück."""
        return LANG_TEXTS[self.current_lang].get(key, f"<{key}>")

    def _create_widgets(self):
        """Erstellt alle GUI-Elemente der Anwendung."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        tab1 = ttk.Frame(self.notebook)
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text=self.t("tab_manage"))
        self.notebook.add(tab2, text=self.t("tab_search"))

        self._create_tab1_widgets(tab1)
        self._create_tab2_widgets(tab2)
        self._create_statusbar()

    def _get_cache_path(self):
        """Gibt den Pfad zur Cache-Datei im Benutzerverzeichnis zurück."""
        app_dir = os.path.join(os.path.expanduser('~'), '.pip_paket_manager')
        if not os.path.exists(app_dir):
            os.makedirs(app_dir)
        return os.path.join(app_dir, 'pypi_index_cache.json')

    def _create_tab1_widgets(self, parent_tab):
        """Erstellt die Widgets für den 'Paketverwaltung'-Tab."""
        parent_tab.columnconfigure(0, weight=1, minsize=270)
        parent_tab.columnconfigure(1, weight=0)
        parent_tab.columnconfigure(2, weight=2, minsize=300)
        parent_tab.rowconfigure(0, weight=1)

        # Linke Spalte
        frame_left = ttk.LabelFrame(parent_tab, text=self.t("frame_left_title"))
        frame_left.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        self.package_listbox = tk.Listbox(frame_left, width=50)
        self.package_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(frame_left, orient="vertical", command=self.package_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_listbox.config(yscrollcommand=scrollbar.set)
        self.package_listbox.bind("<<ListboxSelect>>", self.show_package_info)

        # Mittlere Spalte
        frame_middle = self._create_middle_column(parent_tab)
        frame_middle.grid(row=0, column=1, sticky="ns", padx=5, pady=10)
        # Konfiguriere das Grid-Layout für die mittlere Spalte, um den Fortschrittsbalken unten zu platzieren
        frame_middle.rowconfigure(0, weight=0) # Oberer Teil mit Buttons etc.
        frame_middle.rowconfigure(1, weight=1) # Leerer, expandierender Platzhalter
        frame_middle.rowconfigure(2, weight=0) # Unterer Teil für den Fortschrittsbalken

        # Fortschrittsbalken für Tab 1
        self.progress_frame_tab1 = ttk.LabelFrame(frame_middle, text=self.t("progress_frame_title"))
        self.progress_frame_tab1.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.progress_bar_tab1 = ttk.Progressbar(self.progress_frame_tab1, mode='indeterminate')
        self.progress_bar_tab1.pack(fill=tk.X, expand=True, padx=5, pady=5)
        self.progress_frame_tab1.grid_remove() # Standardmäßig ausblenden

        # Rechte Spalte
        frame_right = ttk.Frame(parent_tab)
        frame_right.grid(row=0, column=2, sticky="nsew", padx=(10, 5), pady=10)
        info_frame = ttk.LabelFrame(frame_right, text=self.t("frame_right_title"))
        info_frame.pack(fill=tk.BOTH, expand=True)
        self.info_text = tk.Text(info_frame, wrap=tk.WORD)
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.info_text.config(yscrollcommand=info_scrollbar.set)
        self.setup_text_widget_tags(self.info_text)

        py_version_frame = ttk.LabelFrame(frame_right, text=self.t("python_versions_title"))
        py_version_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, ipady=2)
        self.py_version_text = tk.Text(py_version_frame, height=4, wrap=tk.NONE, font=("Courier New", 10), state=tk.DISABLED)
        self.py_version_text.pack(fill=tk.X, padx=5, pady=5)

    def _create_middle_column(self, parent):
        """Erstellt die mittlere Spalte mit Aktionen und Sprachauswahl."""
        # Hauptcontainer für die mittlere Spalte
        main_middle_frame = ttk.Frame(parent)

        # Container für den oberen Teil (Sprache, Buttons, Logo)
        top_content_frame = ttk.Frame(main_middle_frame)
        top_content_frame.grid(row=0, column=0, sticky="n")

        lang_frame = ttk.Frame(top_content_frame)
        lang_frame.pack(pady=10)
        self.lang_label = ttk.Label(lang_frame, text=self.t("lang_label"))
        self.lang_label.pack(side=tk.LEFT, padx=5)
        lang_display_names = {"de": "Deutsch", "en": "English", "fr": "Français", "es": "Español", "zh": "中文", "ja": "日本語"}
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, state="readonly",
                                       values=list(lang_display_names.values()), width=12)
        self.lang_combo.pack(side=tk.LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self.change_language)

        self.btn_frame = ttk.LabelFrame(top_content_frame, text=self.t("actions_frame_title"))
        self.btn_frame.pack(pady=10, padx=5)

        self.btn_uninstall = ttk.Button(self.btn_frame, text=self.t("btn_uninstall"), width=25,
                                        command=lambda: self.uninstall_package(self.package_listbox.get(tk.ACTIVE)))
        self.btn_uninstall.pack(fill=tk.X, pady=2)
        self.btn_update = ttk.Button(self.btn_frame, text=self.t("btn_update"), width=25,
                                     command=lambda: self.update_package(self.package_listbox.get(tk.ACTIVE)))
        self.btn_update.pack(fill=tk.X, pady=2)
        self.btn_reinstall = ttk.Button(self.btn_frame, text=self.t("btn_reinstall"), width=25,
                                        command=lambda: self.reinstall_package(self.package_listbox.get(tk.ACTIVE)))
        self.btn_reinstall.pack(fill=tk.X, pady=2)
        self.btn_refresh = ttk.Button(self.btn_frame, text=self.t("btn_refresh"), width=25, command=self.refresh_package_list)
        self.btn_refresh.pack(fill=tk.X, pady=2)
        self.btn_install_deps = ttk.Button(self.btn_frame, text=self.t("btn_install_deps"), width=25, state=tk.DISABLED)
        self.btn_install_deps.pack(fill=tk.X, pady=2)
        self.btn_show_log = ttk.Button(self.btn_frame, text=self.t("btn_show_log"), width=25, command=self.show_log_window)
        self.btn_show_log.pack(fill=tk.X, pady=2)

        try:
            img = Image.open(resource_path('PyPi-128px.ico')).resize((128, 128), Image.Resampling.LANCZOS)
            self.root.icon_image = ImageTk.PhotoImage(img)
            icon_label = ttk.Label(self.btn_frame, image=self.root.icon_image, cursor="hand2")
            icon_label.pack(side=tk.BOTTOM, pady=10)
            icon_label.bind("<Button-1>", lambda e: webbrowser.open_new_tab("https://pypi.org/"))
            self.icon_tooltip = ToolTip(icon_label, self.t("homepage_tooltip"))
        except (FileNotFoundError, tk.TclError):
            pass # Icon ist optional

        return main_middle_frame

    def _create_tab2_widgets(self, parent_tab):
        """Erstellt die Widgets für den 'Suche'-Tab."""
        parent_tab.columnconfigure(0, weight=1, minsize=270)
        parent_tab.columnconfigure(1, weight=1, minsize=200)
        parent_tab.columnconfigure(2, weight=2, minsize=300)
        parent_tab.rowconfigure(0, weight=1)

        # Linke Spalte
        search_left_frame = ttk.Frame(parent_tab)
        search_left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=10)
        self.search_bar_frame = ttk.LabelFrame(search_left_frame, text=self.t("search_label"))
        self.search_bar_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        search_entry = ttk.Entry(self.search_bar_frame, textvariable=self.search_entry_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.search_button = ttk.Button(self.search_bar_frame, text=self.t("search_button"), width=10, command=self.perform_search)
        self.search_button.pack(side=tk.LEFT, padx=(0, 5), pady=5)
        search_entry.bind("<Return>", self.perform_search)

        self.search_results_frame = ttk.LabelFrame(search_left_frame, text=self.t("search_results_title"))
        self.search_results_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.search_results_listbox = tk.Listbox(self.search_results_frame)
        search_results_scrollbar = ttk.Scrollbar(self.search_results_frame, orient="vertical", command=self.search_results_listbox.yview)
        search_results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_results_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_results_listbox.config(yscrollcommand=search_results_scrollbar.set)
        self.search_results_listbox.bind("<<ListboxSelect>>", self.show_package_versions)

        # Mittlere Spalte (neu strukturiert für den Fortschrittsbalken)
        search_middle_frame = ttk.Frame(parent_tab)
        search_middle_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        search_middle_frame.rowconfigure(0, weight=1) # Versionsliste expandiert
        search_middle_frame.rowconfigure(1, weight=0) # Fortschrittsbalken feste Höhe

        self.search_versions_frame = ttk.LabelFrame(search_middle_frame, text=self.t("search_versions_title"))
        self.search_versions_frame.grid(row=0, column=0, sticky="nsew")
        self.search_versions_listbox = tk.Listbox(self.search_versions_frame)
        self.search_versions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        search_versions_scrollbar = ttk.Scrollbar(self.search_versions_frame, orient="vertical", command=self.search_versions_listbox.yview)
        search_versions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_versions_listbox.config(yscrollcommand=search_versions_scrollbar.set)
        self.search_versions_listbox.bind("<<ListboxSelect>>", self.show_version_details)

        # Fortschrittsbalken für Tab 2
        self.progress_frame_tab2 = ttk.LabelFrame(search_middle_frame, text=self.t("progress_frame_title"))
        self.progress_frame_tab2.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.progress_bar_tab2 = ttk.Progressbar(self.progress_frame_tab2, mode='indeterminate')
        self.progress_bar_tab2.pack(fill=tk.X, expand=True, padx=5, pady=5)
        self.progress_frame_tab2.grid_remove() # Standardmäßig ausblenden

        # Rechte Spalte
        search_right_frame = ttk.Frame(parent_tab)
        search_right_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 10), pady=10)
        search_right_frame.rowconfigure(0, weight=2)
        search_right_frame.rowconfigure(1, weight=1)
        search_right_frame.columnconfigure(0, weight=1)

        self.search_info_frame = ttk.LabelFrame(search_right_frame, text=self.t("search_info_title"))
        self.search_info_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        self.search_info_text = tk.Text(self.search_info_frame, wrap=tk.WORD)
        search_info_scrollbar = ttk.Scrollbar(self.search_info_frame, orient="vertical", command=self.search_info_text.yview)
        search_info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.search_info_text.config(yscrollcommand=search_info_scrollbar.set)
        self.setup_text_widget_tags(self.search_info_text)

        search_right_bottom_frame = ttk.Frame(search_right_frame)
        search_right_bottom_frame.grid(row=1, column=0, sticky="ew")
        self.install_frame = ttk.LabelFrame(search_right_bottom_frame, text=self.t("install_frame_title"))
        self.install_frame.pack(fill=tk.X, padx=5, pady=5)
        self.btn_install_selected = ttk.Button(self.install_frame, text=self.t("btn_install_selected_version"), command=self.install_selected_version)
        self.btn_install_selected.pack(pady=5, padx=5)

    def _create_statusbar(self):
        """Erstellt die Statusleiste am unteren Rand des Fensters."""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=2)
        self.status_label = ttk.Label(status_frame, text=self.t("status_loading"), anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")
        self.progress_label = ttk.Label(status_frame, text="", anchor="e")
        self.progress_label.grid(row=0, column=1, sticky="ew")

    def _start_background_tasks(self):
        """Startet die initialen Ladevorgänge in Hintergrundthreads."""
        threading.Thread(target=self.load_packages, daemon=True).start()
        threading.Thread(target=self.load_pypi_index, daemon=True).start()
        threading.Thread(target=self.load_python_versions, daemon=True).start()
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    # --- Logging und Status ---

    def log_message(self, message, level="INFO"):
        """Fügt eine Nachricht zum In-Memory-Log hinzu."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_message = f"{timestamp} [{level}] {message}"
        self.log_records.append(full_message)
        self.update_log_window()

    def update_log_window(self):
        """Aktualisiert das Log-Fenster, falls es offen ist."""
        if self.log_window and self.log_window.winfo_exists():
            try:
                self.log_window.log_text_widget.insert(tk.END, self.log_records[-1] + "\n")
                self.log_window.log_text_widget.see(tk.END)
            except (tk.TclError, RuntimeError):
                pass

    def show_log_window(self):
        """Erstellt und zeigt das Log-Fenster an."""
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.lift()
            return
        self.log_window = tk.Toplevel(self.root)
        self.log_window.title(self.t("log_title"))
        self.log_window.geometry("800x500")
        self.log_window.log_text_widget = tk.Text(self.log_window, wrap=tk.WORD, font=("Courier New", 9))
        log_scrollbar = ttk.Scrollbar(self.log_window, orient="vertical", command=self.log_window.log_text_widget.yview)
        self.log_window.log_text_widget.config(yscrollcommand=log_scrollbar.set)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_window.log_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_window.log_text_widget.insert(tk.END, "\n".join(self.log_records) + "\n")
        self.log_window.log_text_widget.see(tk.END)

    def update_status_label(self, text_key, show=True):
        """Aktualisiert das zentrale Status-Label sicher aus jedem Thread."""
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

    def run_pip_command(self, command_list, on_finish=None):
        """Führt einen Pip-Befehl in einem separaten Prozess aus."""
        def task():
            """
            Führt einen Pip-Befehl in einem separaten Prozess aus und zeige den Fortschritt live im 'update_info_label' an.
            Zeigt den Abschluss live im 'update_info_label' an.
            :param command_list: Die an pip zu übergebenden Argumente.
            :param on_finish: Callback-Funktion, die nach Abschluss des Befehls aufgerufen wird.
            """

            self.root.after(0, self.start_progress)
            try:
                start_msg = f"Running: {os.path.basename(sys.executable)} -m pip {' '.join(command_list)}..."
                self.log_message(start_msg)
                if self.progress_label:
                    self.root.after(0, lambda: self.progress_label.config(text=start_msg))

                process = subprocess.Popen([sys.executable, "-m", "pip"] + command_list,
                                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                           text=True, encoding='utf-8', errors='replace')
                for line in iter(process.stdout.readline, ''):
                    cleaned_line = line.strip()
                    self.log_message(cleaned_line, level="PIP")
                    if cleaned_line and self.progress_label:
                        self.root.after(0, lambda l=cleaned_line: self.progress_label.config(text=l))
                process.wait()
                end_msg = f"Finished with exit code {process.returncode}"
                self.log_message(end_msg, level="STATUS")
                if self.progress_label:
                    self.root.after(0, lambda: self.progress_label.config(text=end_msg))
                if on_finish:
                    self.root.after(100, on_finish)
            finally:
                self.root.after(0, self.stop_progress)
        threading.Thread(target=task, daemon=True).start()

    def get_installed_packages(self):
        """Ruft die Liste aller installierten Pakete ab."""
        result = subprocess.run([sys.executable, "-m", "pip", "list", "--format=freeze"],
                                capture_output=True, text=True, check=False)
        self.installed_packages_cache = sorted([line.split("==")[0] for line in result.stdout.splitlines()], key=str.lower)
        return self.installed_packages_cache

    def load_outdated_packages(self):
        """Lädt die Liste der veralteten Pakete."""
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list", "--outdated"],
                                     capture_output=True, text=True, check=False)
            outdated_list = {}
            for line in result.stdout.splitlines()[2:]:
                parts = line.split()
                if len(parts) >= 3:
                    outdated_list[parts[0]] = {"current": parts[1], "latest": parts[2]}
            self.outdated_packages_cache = outdated_list
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            self.log_message(f"Fehler beim Prüfen auf veraltete Pakete: {e}", "ERROR")

    def load_packages(self):
        """Lädt installierte und veraltete Pakete und aktualisiert die GUI."""
        def do_load():
            self.root.after(0, self.start_progress)
            try:
                self.log_message("Loading package lists...")
                self.root.after(0, lambda: self.update_status_label("status_loading_installed"))
                packages = self.get_installed_packages()
                self.root.after(0, lambda: self.update_listbox_safely(packages))
                self.root.after(0, lambda: self.update_status_label(None, show=False))

                self.root.after(100, lambda: self.update_status_label("status_checking_updates"))
                self.load_outdated_packages()
                self.root.after(0, self.colorize_outdated_packages)
                self.root.after(0, lambda: self.update_status_label(None, show=False))
                self.log_message("Finished loading all package data.")
            finally:
                self.root.after(0, self.stop_progress)
        threading.Thread(target=do_load, daemon=True).start()

    # --- Aktionen und Event-Handler ---

    def refresh_package_list(self):
        """Leert die Paketliste und startet den Ladevorgang neu."""
        self.package_listbox.delete(0, tk.END)
        self.log_message("Refreshing package list...")
        self.load_packages()

    def uninstall_package(self, pkg_name):
        """Deinstalliert ein Paket."""
        if not pkg_name:
            return
        if not messagebox.askyesno(self.t("btn_uninstall"), self.t("confirm_uninstall").format(pkg_name)):
            return
        pkg_path = get_package_path(pkg_name)
        needs_admin = pkg_path.lower().startswith(r"c:\program files")
        if needs_admin and not is_admin():
            self.log_message(f"Admin rights required for uninstalling {pkg_name} ({pkg_path})")
            messagebox.showinfo(self.t("admin_rights_title"), self.t("admin_rights_required_msg").format(pkg_name=pkg_name))
            pip_args = f'-m pip uninstall -y "{pkg_name}"'
            subprocess.run(["powershell", "-Command", "Start-Process", sys.executable,
                            "-ArgumentList", f'"{pip_args}"', "-Verb", "runAs", "-Wait"], check=False)
            self.refresh_package_list()
            return
        self.run_pip_command(["uninstall", "-y", pkg_name], self.refresh_package_list)

    def update_package(self, pkg_name):
        """Aktualisiert ein Paket."""
        if not pkg_name:
            return
        self.run_pip_command(["install", "--upgrade", pkg_name])

    def reinstall_package(self, pkg_name):
        """Installiert ein Paket neu."""
        if not pkg_name:
            return
        try:
            current_version = importlib.metadata.version(pkg_name)
            self.log_message(f"Starting reinstall for {pkg_name}=={current_version}")
            command = ["install", "--force-reinstall", "--no-deps", f"{pkg_name}=={current_version}"]
            self.run_pip_command(command)
        except importlib.metadata.PackageNotFoundError:
            self.log_message(f"Could not determine version for '{pkg_name}'.", "WARNING")
            self.run_pip_command(["install", "--force-reinstall", "--no-deps", pkg_name])

    def install_dependencies(self, deps_to_install):
        """Installiert eine Liste von Abhängigkeiten."""
        if not deps_to_install:
            return
        self.run_pip_command(["install"] + deps_to_install)

    def show_package_info(self, _event=None):
        """Zeigt Informationen zu einem ausgewählten Paket an."""
        selection = self.package_listbox.curselection()
        if not selection:
            return
        if self.progress_label:
            self.progress_label.config(text="")
        pkg_name = self.package_listbox.get(selection[0])
        self.info_text.delete("1.0", tk.END)
        self.log_message(f"Fetching info for '{pkg_name}'")
        self.info_text.insert(tk.END, self.t("loading_info").format(pkg_name) + "\n")

        def fetch_and_show():
            """
            Fetches package info and displays it in the GUI.

            Disables the 'Install dependencies' button while fetching the package information.
            If the package has missing dependencies, enables the button with a command to install the dependencies.
            If the package is outdated, updates the progress label with an update message.
            Finally, calls display_formatted_info with the fetched information to display it in the GUI.
            """
            self.root.after(0, lambda: self.btn_install_deps.config(state=tk.DISABLED, command=None))
            dist = importlib.metadata.distribution(pkg_name)
            info = self.get_package_info_string(pkg_name, dist)
            install_time = self.get_install_time(pkg_name)
            pypi_info = self.get_pypi_info(pkg_name, dist.version)
            missing_deps = self.get_missing_deps(dist)

            if missing_deps:
                self.root.after(0, lambda: self.btn_install_deps.config(state=tk.NORMAL, command=lambda: self.install_dependencies(missing_deps)))

            if pkg_name in self.outdated_packages_cache:
                update_info = self.outdated_packages_cache[pkg_name]
                update_text = self.t("update_available").format(update_info['current'], update_info['latest'])
                if self.progress_label:
                    self.root.after(0, lambda: self.progress_label.config(text=update_text))

            self.root.after(0, lambda: self.display_formatted_info(info, pypi_info, install_time, missing_deps, pkg_name))
        threading.Thread(target=fetch_and_show, daemon=True).start()

    def get_package_info_string(self, pkg_name, dist):
        """Erstellt den Info-String für ein Paket."""
        metadata = dist.metadata

        # --- Robuste Extraktion der Metadaten ---
        # Homepage: Prüft zuerst Project-URL (Homepage, dann Source), dann Home-page
        homepage = "N/A"
        project_urls = metadata.get_all('Project-URL') or []

        # Priorität 1: Suche nach "Homepage"
        for url_entry in project_urls:
                if url_entry.lower().startswith("homepage,"):
                    homepage = url_entry.split(',')[1].strip()
                    break
        # Priorität 2 (NEU): Suche nach "Source" oder "Source code" als Fallback
        if homepage == "N/A":
            for url_entry in project_urls:
                if url_entry.lower().startswith("source,") or url_entry.lower().startswith("source code,"):
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
        license_expression = metadata.get('License-Expression')
        if license_expression:
            license_info = license_expression
        else:
            # Priorität 2 (NEU): Lese die erste Zeile aus der Lizenzdatei.
            license_files = getattr(dist, 'license_files', [])
            if license_files:
                try:
                    license_text = dist.read_text(license_files[0])
                    if license_text:
                        license_info = license_text.splitlines()[0].strip()
                except (FileNotFoundError, OSError, IndexError):
                    pass  # Wenn das Lesen fehlschlägt, gehen wir zum nächsten Fallback.
        if license_info == "N/A":
            # Priorität 3 (Fallback): Das alte 'License'-Feld.
            license_info = metadata.get('License', 'N/A')

        info_lines = [
            f"{self.t('info_name')}: {metadata.get('Name', 'N/A')}",
            f"{self.t('info_version')} (installiert): {metadata.get('Version', 'N/A')}",
            f"{self.t('info_summary')}: {metadata.get('Summary', 'N/A')}",
            f"{self.t('info_homepage')}: {homepage}",
            f"{self.t('info_author')}: {author}",
            f"{self.t('info_license')}: {license_info}",
            f"{self.t('info_location')}: {dist.locate_file('')}",
            f"{self.t('info_dependencies')}: {', '.join(dist.requires) if dist.requires else ''}",
            f"{self.t('info_required_by')}: {', '.join(self.get_required_by(pkg_name))}"
        ]
        return "\n\n".join(info_lines)

    def get_pypi_info(self, pkg_name, version):
        """Ruft Paketinformationen von der PyPI JSON API ab."""
        try:
            response = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=5)
            response.raise_for_status()
            data = response.json()
            pypi_info = {'data': data.get('info', {})}
            if version and version in data.get("releases", {}):
                release_data = data["releases"][version]
                if release_data:
                    pypi_info["yanked"] = release_data[0].get("yanked", False)
                    pypi_info["yanked_reason"] = release_data[0].get("yanked_reason", "N/A")
            return pypi_info
        except (requests.exceptions.RequestException, ValueError):
            return None

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
        if dist.requires:
            installed_normalized = {p.lower().replace("_", "-") for p in self.installed_packages_cache}
            for req in dist.requires:
                req_name = req.split(' ')[0].split('[')[0].split(';')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                if req_name.lower().replace("_", "-") not in installed_normalized:
                    missing_deps.append(req_name)
        return missing_deps

    def get_required_by(self, pkg_name):
        """Findet alle Pakete, die von `pkg_name` abhängen."""
        requiring_packages = []
        normalized_pkg_name = pkg_name.replace("_", "-").lower()
        for dist in importlib.metadata.distributions():
            if dist.requires:
                for req in dist.requires:
                    req_name = req.split(' ')[0].split('[')[0].split(';')[0].split('<')[0].split('>')[0].split('=')[0].strip()
                    if req_name.replace("_", "-").lower() == normalized_pkg_name:
                        requiring_packages.append(dist.metadata['name'])
        return sorted(requiring_packages, key=str.lower)

    def display_formatted_info(self, info, pypi_info, install_time, missing_deps, pkg_name):
        """Formatiert und zeigt die gesammelten Paketinformationen an."""
        try:
            if not self.root.winfo_exists(): return
            self.info_text.delete("1.0", tk.END)
            self.info_text.insert(tk.END, info + "\n\n")

            if pypi_info and pypi_info.get("yanked"):
                self.info_text.insert(tk.END, f"\n{self.t('info_yanked')}\n", "yanked_warning")
                self.info_text.insert(tk.END, f"{self.t('info_yanked_reason')}: {pypi_info.get('yanked_reason')}\n")

            if pkg_name in self.outdated_packages_cache:
                update_info = self.outdated_packages_cache[pkg_name]
                update_text = self.t("update_available").format(update_info['current'], update_info['latest'])
                version_line_start = self.info_text.search(f"{self.t('info_version')} (installiert):", "1.0", tk.END)
                if version_line_start:
                    line_end_index = self.info_text.index(f"{version_line_start} lineend")
                    self.info_text.insert(f"{line_end_index}\n", f"  -> {update_text}\n", "update_info")

            if install_time:
                fmt = {"de": "%d.%m.%Y %H:%M:%S"}.get(self.current_lang, "%Y-%m-%d %H:%M:%S")
                self.info_text.insert(tk.END, f"\n{self.t('install_time').format(install_time.strftime(fmt))}\n")
            else:
                self.info_text.insert(tk.END, f"\n{self.t('no_install_time')}\n")

            homepage_line_start = self.info_text.search(f"{self.t('info_homepage')}:", "1.0", tk.END)
            if homepage_line_start:
                url_start_index = self.info_text.index(f"{homepage_line_start} + {len(self.t('info_homepage')) + 2}c")
                url_end_index = self.info_text.index(f"{homepage_line_start} lineend")
                url = self.info_text.get(url_start_index, url_end_index).strip()
                if url.startswith("http"):
                    self.info_text.tag_add("hyperlink", url_start_index, url_end_index)

            if missing_deps:
                self.info_text.insert(tk.END, f"\n{self.t('missing_deps_info').format(', '.join(missing_deps))}\n")
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
                    self.log_message(f"Opening URL: {url}")
                    webbrowser.open_new_tab(url)
                return

    def setup_text_widget_tags(self, text_widget):
        """Definiert Tags für Text-Widgets."""
        text_widget.tag_config("update_info", foreground="#006400", font=("Segoe UI", 9, "bold"))
        text_widget.tag_config("yanked_warning", foreground="red", font=("Segoe UI", 9, "bold"))
        text_widget.tag_config("hyperlink", foreground="blue", underline=True)
        text_widget.tag_bind("hyperlink", "<Enter>", lambda e, w=text_widget: w.config(cursor="hand2"))
        text_widget.tag_bind("hyperlink", "<Leave>", lambda e, w=text_widget: w.config(cursor=""))
        text_widget.tag_bind("hyperlink", "<Button-1>", self.open_url_from_text)

    def load_python_versions(self):
        """Lädt installierte Python-Versionen."""
        def do_load():
            """Lädt installierte Python-Versionen und aktualisiert das Text-Widget mit den gefunden Versionen."""
        try:
            result = subprocess.run(["py", "-0p"], capture_output=True, text=True, check=False)
            lines = result.stdout.splitlines() if result.returncode == 0 else ["Python-Launcher (py.exe) nicht gefunden."]
        except FileNotFoundError:
            lines = ["Python-Launcher (py.exe) nicht gefunden."]
        self.root.after(0, lambda: self.update_python_version_display(lines))
        threading.Thread(target=do_load, daemon=True).start()

    def update_python_version_display(self, lines):
        """Aktualisiert die Anzeige der Python-Versionen."""
        try:
            if not self.root.winfo_exists(): return
            self.py_version_text.config(state=tk.NORMAL)
            self.py_version_text.delete("1.0", tk.END)
            for line in lines:
                self.py_version_text.insert(tk.END, line.strip() + "\n")
            self.py_version_text.config(state=tk.DISABLED)
        except (tk.TclError, RuntimeError):
            pass

    def change_language(self, _event=None):
        """Aktualisiert die GUI-Texte basierend auf der Sprachauswahl."""
        lang_display_names = {"de": "Deutsch", "en": "English", "fr": "Français", "es": "Español", "zh": "中文", "ja": "日本語"}
        selected_display_name = self.lang_var.get()
        for code, display_name in lang_display_names.items():
            if display_name == selected_display_name:
                self.current_lang = code
                break
        self.root.title(self.t("title"))
        self.notebook.tab(0, text=self.t("tab_manage"))
        self.notebook.tab(1, text=self.t("tab_search"))
        # ... weitere UI-Updates ...
        self.lang_label.config(text=self.t("lang_label"))
        self.btn_uninstall.config(text=self.t("btn_uninstall"))
        self.btn_update.config(text=self.t("btn_update"))
        # ... und so weiter für alle Widgets ...
        if self.icon_tooltip:
            self.icon_tooltip.update_text(self.t("homepage_tooltip"))

    def update_listbox_safely(self, packages):
        """Aktualisiert die Paket-Listbox sicher im GUI-Thread."""
        try:
            if not self.root.winfo_exists(): return
            self.package_listbox.delete(0, tk.END)
            for pkg in packages:
                self.package_listbox.insert(tk.END, pkg)
            self.status_label.config(text=self.t("status_loaded").format(len(packages)))
        except (tk.TclError, RuntimeError):
            pass

    def colorize_outdated_packages(self):
        """Färbt veraltete Pakete in der Liste ein."""
        if not self.outdated_packages_cache: return
        for i in range(self.package_listbox.size()):
            pkg_name = self.package_listbox.get(i)
            self.package_listbox.itemconfig(i, {'bg': '#B6F0A5' if pkg_name in self.outdated_packages_cache else ''})

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
            self.log_message("PyPI index not loaded yet. Starting load...")
            self.load_pypi_index()
            return
        self.log_message(f"Filtering local index for '{query}'...")
        filtered_packages = [pkg for pkg in self.pypi_index_cache if query.lower() in pkg.lower()]
        self.root.after(0, lambda: self.update_search_results(filtered_packages, query))

    def _read_pypi_cache_from_disk(self):
        """Liest den PyPI-Index-Cache von der Festplatte."""
        if os.path.exists(self.pypi_cache_path):
            try:
                with open(self.pypi_cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.log_message(f"Could not read cache file: {e}", "WARNING")
        return None

    def _write_pypi_cache_to_disk(self, data):
        """Schreibt den PyPI-Index-Cache auf die Festplatte."""
        try:
            with open(self.pypi_cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)
        except IOError as e:
            self.log_message(f"Could not write cache file: {e}", "ERROR")

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

            cache_data = self._read_pypi_cache_from_disk()
            self.root.after(0, self.start_progress)
            last_serial = 0
            if cache_data:
                self.pypi_index_cache = cache_data.get('packages', [])
                last_serial = cache_data.get('last_serial', 0)
                self.log_message(f"Loaded {len(self.pypi_index_cache)} packages from local cache.")

            url = "https://pypi.org/simple/"
            headers = {'Accept': 'application/vnd.pypi.simple.v1+json'}
            params = {}
            if last_serial > 0:
                params['since'] = last_serial
                self.log_message(f"Checking for PyPI updates since serial {last_serial}...")
            else:
                self.root.after(0, lambda: self.update_status_label("status_loading_index"))

            try:
                with requests.get(url, headers=headers, params=params, timeout=30, stream=True) as response:
                    response.raise_for_status()
                    total_size = response.headers.get('content-length')
                    if total_size:
                        total_size_mb = int(total_size) / (1024 * 1024)
                        log_msg = f"Downloading PyPI index updates (approx. {total_size_mb:.2f} MB)..." if last_serial > 0 else f"Downloading full PyPI index (approx. {total_size_mb:.2f} MB)..."
                        self.log_message(log_msg)

                    data = response.json()
                    new_serial = data.get('meta', {}).get('_last-serial', last_serial)
                    new_packages = [p['name'] for p in data.get('projects', [])]

                    if new_packages:
                        if last_serial == 0:  # Full load
                            self.pypi_index_cache = sorted(new_packages, key=str.lower)
                            self.log_message(f"Full PyPI index with {len(self.pypi_index_cache)} packages loaded.")
                        else:  # Delta update
                            old_package_count = len(self.pypi_index_cache)
                            # Erstelle ein Set für schnelles Nachschlagen
                            existing_packages_set = set(self.pypi_index_cache)
                            # Füge nur wirklich neue Pakete hinzu
                            added_packages = [pkg for pkg in new_packages if pkg not in existing_packages_set]

                            if added_packages:
                                self.pypi_index_cache.extend(added_packages)
                                self.pypi_index_cache.sort(key=str.lower)  # Halte die Liste sortiert
                                self.log_message(f"Applied {len(added_packages)} updates to PyPI index. Total packages: {len(self.pypi_index_cache)}.")
                    if new_serial > last_serial:
                        self._write_pypi_cache_to_disk({'last_serial': new_serial, 'packages': self.pypi_index_cache})

            except requests.exceptions.RequestException as e:
                self.log_message(f"Failed to load PyPI index: {e}", "ERROR")
            finally:
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
        if not selection: return
        pkg_name = self.search_results_listbox.get(selection[0])
        self.current_searched_pkg_name = pkg_name
        self.search_versions_listbox.delete(0, tk.END)
        self.search_info_text.config(state=tk.NORMAL)
        self.search_info_text.delete("1.0", tk.END)
        self.search_info_text.insert(tk.END, self.t("loading_info").format(pkg_name))
        self.search_info_text.config(state=tk.DISABLED)
        threading.Thread(target=self._fetch_and_display_versions, args=(pkg_name,), daemon=True).start()

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
                if not filename: continue
                if self._is_compatible(filename, dist_data.get('packagetype')):
                    compatible_versions_info.append((packaging.version.parse(version_str), filename, dist_data))
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
            except (packaging.utils.InvalidWheelFilename, packaging.version.InvalidVersion, ValueError):
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
        try:
            response = requests.get(f"https://pypi.org/pypi/{pkg_name}/json", timeout=10)
            response.raise_for_status()
            data = response.json()
            self.pypi_package_releases_cache[pkg_name] = data
            return data
        except requests.exceptions.RequestException as e:
            self.log_message(f"Fehler beim Abrufen der PyPI-Informationen für {pkg_name}: {e}", "ERROR")
            return None

    def show_version_details(self, _event=None):
        """Zeigt Details für eine ausgewählte Version an."""
        selection = self.search_versions_listbox.curselection()
        if not selection: return
        selected_filename = self.search_versions_listbox.get(selection[0])
        file_data = self.current_package_version_details_cache.get(selected_filename)
        if not file_data:
            self._update_search_info_text(self.t("no_info"))
            return
        pypi_full_data = self.pypi_package_releases_cache.get(self.current_searched_pkg_name)
        if not pypi_full_data:
            self._update_search_info_text(self.t("no_info"))
            return
        info = pypi_full_data.get('info', {})

        # KORREKTUR: Die fehlende Logik zum Füllen der Textbox wird hier wieder eingefügt.
        self.search_info_text.config(state=tk.NORMAL)
        self.search_info_text.delete("1.0", tk.END)

        # Allgemeine Paketinformationen
        self.search_info_text.insert(tk.END, f"{self.t('info_name')}: {info.get('name', 'N/A')}\n\n")
        description_text = info.get('summary') or info.get('description', 'N/A')
        self.search_info_text.insert(tk.END, f"{self.t('info_summary')}: {description_text}\n\n")

        project_urls = info.get('project_urls') or {}
        package_url = project_urls.get('Homepage') or project_urls.get('Home') or info.get('home_page') or 'N/A'
        self.search_info_text.insert(tk.END, f"{self.t('info_package_url')}: {package_url}\n\n")

        documentation_url = project_urls.get('Documentation') or 'N/A'
        self.search_info_text.insert(tk.END, f"{self.t('info_documentation')}: {documentation_url}\n\n")

        requires_dist_list = info.get('requires_dist')
        requires_dist = ", ".join(requires_dist_list) if requires_dist_list else 'N/A'
        self.search_info_text.insert(tk.END, f"{self.t('info_dependencies')}: {requires_dist}\n\n")

        # Spezifische Dateidetails
        self.search_info_text.insert(tk.END, f"{self.t('info_filename')}: {file_data.get('filename', 'N/A')}\n\n")
        self.search_info_text.insert(tk.END, f"{self.t('info_md5')}: {file_data.get('md5_digest', 'N/A')}\n\n")
        self.search_info_text.insert(tk.END, f"{self.t('info_sha256')}: {file_data.get('digests', {}).get('sha256', 'N/A')}\n\n")
        self.search_info_text.insert(tk.END, f"{self.t('info_packagetype')}: {file_data.get('packagetype', 'N/A')}\n\n")
        self.search_info_text.insert(tk.END, f"{self.t('info_python_version')}: {file_data.get('python_version', 'N/A')}\n\n")
        self.search_info_text.insert(tk.END, f"{self.t('info_requires_python')}: {file_data.get('requires_python', 'N/A')}\n\n")

        size_bytes = file_data.get('size')
        size_kb = f"{size_bytes / 1024:.2f} KB" if size_bytes is not None else 'N/A'
        self.search_info_text.insert(tk.END, f"{self.t('info_size')}: {size_kb}\n\n")

        upload_time_str = file_data.get('upload_time_iso_8601')
        formatted_upload_time = 'N/A'
        if upload_time_str:
            try:
                dt_object = datetime.datetime.fromisoformat(upload_time_str.replace("Z", "+00:00"))
                fmt = {"de": "%d.%m.%Y %H:%M:%S"}.get(self.current_lang, "%Y-%m-%d %H:%M:%S")
                formatted_upload_time = dt_object.strftime(fmt)
            except ValueError:
                formatted_upload_time = upload_time_str
        self.search_info_text.insert(tk.END, f"{self.t('info_upload_time')}: {formatted_upload_time}\n\n")

        self.search_info_text.insert(tk.END, f"{self.t('info_url')}: {file_data.get('url', 'N/A')}\n\n")

        yanked = file_data.get('yanked', False)
        self.search_info_text.insert(tk.END, f"{self.t('info_yanked_status')}: {yanked}\n")
        if yanked:
            self.search_info_text.insert(tk.END, f"{self.t('info_yanked_reason_full')}: {file_data.get('yanked_reason', 'N/A')}\n\n")

        # URLs anklickbar machen
        def tag_url_in_widget(widget, label_key):
            """
            Searches for a URL in a widget after a certain label and
            makes it clickable if found.

            Parameters
            ----------
            widget : tk.Text
                The widget in which to search for the URL.
            label_key : str
                The key of the label after which to search for the URL.

            Returns
            -------
            None
            """
            line_start = widget.search(f"{self.t(label_key)}:", "1.0", tk.END)
            if line_start:
                url_start_index = widget.index(f"{line_start} + {len(self.t(label_key)) + 2}c")
                url_end_index = widget.index(f"{line_start} lineend")
                url = widget.get(url_start_index, url_end_index).strip()
                if url.startswith("http"):
                    widget.tag_add("hyperlink", url_start_index, url_end_index)

        tag_url_in_widget(self.search_info_text, 'info_package_url')
        tag_url_in_widget(self.search_info_text, 'info_documentation')
        tag_url_in_widget(self.search_info_text, 'info_url')

        self.search_info_text.config(state=tk.DISABLED)

    def install_selected_version(self):
        """Installiert die ausgewählte Version eines Pakets."""
        version_selection = self.search_versions_listbox.curselection()
        if not self.current_searched_pkg_name or not version_selection:
            messagebox.showwarning(self.t("install_frame_title"), self.t("select_package_version_first_msg"))
            return
        pkg_name = self.current_searched_pkg_name
        selected_filename = self.search_versions_listbox.get(version_selection[0])
        file_data = self.current_package_version_details_cache.get(selected_filename)
        if not file_data:
            messagebox.showerror(self.t("error_title"), self.t("select_package_version_first_msg"))
            return

        # KORREKTUR: Die Versionsnummer wird zuverlässig aus dem Dateinamen extrahiert.
        version_to_install = self.t("selected_version_fallback") # Fallback-Wert
        try:
            # Versuche, die Version aus dem Wheel-Dateinamen zu parsen.
            _name, parsed_version, _build, _tags = packaging_utils.parse_wheel_filename(selected_filename)
            version_to_install = str(parsed_version)
        except packaging.utils.InvalidWheelFilename:
            # Fallback für andere Dateitypen wie .tar.gz (sdists)
            if pkg_name in selected_filename:
                # Extrahiere die Version zwischen Paketname und Dateiendung
                version_part = selected_filename.replace(pkg_name, "").lstrip("-").split(".tar.gz")[0]
                if version_part:
                    version_to_install = version_part

        confirm_msg = self.t("confirm_install").format(pkg_name=pkg_name, version=version_to_install)
        if messagebox.askyesno(self.t("install_frame_title"), confirm_msg):
            self.run_pip_command(["install", f"{pkg_name}=={version_to_install}"], on_finish=self.refresh_package_list)

    # --- Update-Funktionalität ---

    def _calculate_sha256(self, file_path=None, data=None):
        """Berechnet den SHA256-Hash einer Datei oder von Daten."""
        sha256_hash = hashlib.sha256()
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        if data:
            sha256_hash.update(data)
            return sha256_hash.hexdigest()
        return None

    def check_for_updates(self):
        """Prüft auf GitHub, ob eine neue Version des Skripts verfügbar ist."""
        self.log_message("Checking for application updates...")
        try:
            # 1. Lokalen Hash berechnen
            local_hash = self._calculate_sha256(file_path=self.script_path)
            if not local_hash:
                self.log_message("Could not calculate hash of local script.", "WARNING")
                return

            # 2. Remote-Inhalt herunterladen
            url = f"https://raw.githubusercontent.com/{self.GITHUB_REPO}/main/{self.SCRIPT_FILENAME}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            remote_content = response.content

            # 3. Remote-Hash berechnen
            remote_hash = self._calculate_sha256(data=remote_content)

            # 4. Hashes vergleichen
            if local_hash != remote_hash:
                self.log_message("New version found on GitHub!")
                self.new_script_content = remote_content
                self.root.after(0, self._show_update_dialog)
            else:
                self.log_message("Application is up to date.")

        except requests.RequestException as e:
            self.log_message(f"Could not check for updates: {e}", "WARNING")
        except Exception as e:
            self.log_message(f"An unexpected error occurred during update check: {e}", "ERROR")

    def _show_update_dialog(self):
        """Zeigt einen benutzerdefinierten Dialog für das Update an."""
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("update_title"))
        dialog.transient(self.root)
        dialog.grab_set()

        message = ttk.Label(dialog, text=self.t("update_message"), wraplength=300, justify=tk.CENTER)
        message.pack(padx=20, pady=20)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)

        def handle_choice(choice):
            dialog.destroy()
            if choice == "now":
                self._handle_update_now()
            elif choice == "later":
                self._handle_update_later()
            elif choice == "no":
                self._handle_update_no()

        btn_now = ttk.Button(btn_frame, text=self.t("update_btn_now"), command=lambda: handle_choice("now"))
        btn_now.pack(side=tk.LEFT, padx=10)
        btn_later = ttk.Button(btn_frame, text=self.t("update_btn_later"), command=lambda: handle_choice("later"))
        btn_later.pack(side=tk.LEFT, padx=10)
        btn_no = ttk.Button(btn_frame, text=self.t("update_btn_no"), command=lambda: handle_choice("no"))
        btn_no.pack(side=tk.LEFT, padx=10)

    def _handle_update_now(self):
        """Führt das Update sofort durch und startet die Anwendung neu."""
        self.log_message("Applying update and restarting...")
        if self._apply_update():
            self._restart_app()

    def _handle_update_later(self):
        """Setzt das Flag, um das Update beim Schließen durchzuführen."""
        self.log_message("Update will be applied on exit.")
        self.update_on_exit = True

    def _handle_update_no(self):
        """Verwirft das Update."""
        self.log_message("Update declined by user.")
        self.new_script_content = None

    def _apply_update(self):
        """Überschreibt die aktuelle Skript-Datei mit dem neuen Inhalt."""
        if not self.new_script_content:
            return False
        try:
            with open(self.script_path, "wb") as f:
                f.write(self.new_script_content)
            self.log_message("Script file updated successfully.")
            return True
        except IOError as e:
            self.log_message(f"Failed to write update to file: {e}", "ERROR")
            return False

    def _restart_app(self):
        """Startet die Anwendung neu."""
        self.log_message("Restarting application...")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def _on_closing(self):
        """Wird aufgerufen, wenn das Hauptfenster geschlossen wird."""
        if self.update_on_exit:
            self.log_message("Applying update on exit...")
            self._apply_update()
        self.root.destroy()


if __name__ == "__main__":
    main_root = tk.Tk()
    app = PipPackageManager(main_root)
    main_root.mainloop()
