import sys
import os
import json
import logging
import threading
import tempfile
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLabel, QPushButton, QMenuBar, QMenu,
    QAction, QFileDialog, QMessageBox, QFrame, QSplitter,
    QStatusBar, QToolBar, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QGroupBox, QGridLayout, QScrollArea, QListWidget,
    QDialog, QFormLayout, QProgressBar, QTextBrowser
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTextCursor

# Version and configuration
CURRENT_VERSION = "1.1.0"
VERSION_URL = "https://raw.githubusercontent.com/PixelHeaven/software1/main/version.json"
APP_NAME = "Advanced Text Editor"
CONFIG_FILE = "config.json"

# Safe import function for optional dependencies
def safe_import_requests():
    """Safely import requests library"""
    try:
        import requests
        return requests
    except ImportError:
        return None

class UpdateChecker(QObject):
    """Update checker that runs in a separate thread"""
    update_available = pyqtSignal(dict)  # Emits update info
    update_error = pyqtSignal(str)       # Emits error message
    no_update = pyqtSignal(str)          # Emits when no update available
    
    def __init__(self, silent=False):
        super().__init__()
        self.silent = silent
    
    def check_for_updates(self):
        """Check for updates in background thread"""
        try:
            requests = safe_import_requests()
            if not requests:
                raise Exception("Requests library not available")
            
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            
            version_info = response.json()
            latest_version = version_info.get("version", "")
            
            if self._is_newer_version(latest_version, CURRENT_VERSION):
                self.update_available.emit(version_info)
            else:
                self.no_update.emit(f"You're running the latest version ({CURRENT_VERSION})!")
                
        except Exception as e:
            error_msg = f"Could not check for updates: {str(e)}"
            self.update_error.emit(error_msg)
    
    def _is_newer_version(self, latest, current):
        """Compare version numbers"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False

class UpdateDialog(QDialog):
    """Dialog to show update information"""
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.update_info = update_info
        self.setWindowTitle("Update Available")
        self.setModal(True)
        self.resize(500, 400)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the update dialog UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_frame = QFrame()
        header_frame.setObjectName("updateHeader")
        header_layout = QVBoxLayout(header_frame)
        
        title_label = QLabel("🚀 Update Available!")
        title_label.setObjectName("updateTitle")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {self.update_info.get('version', 'Unknown')} is now available")
        version_label.setObjectName("updateVersion")
        version_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(version_label)
        
        current_label = QLabel(f"Current version: {CURRENT_VERSION}")
        current_label.setObjectName("updateCurrent")
        current_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(current_label)
        
        layout.addWidget(header_frame)
        
        # Release notes
        notes_label = QLabel("What's New:")
        notes_label.setObjectName("notesLabel")
        layout.addWidget(notes_label)
        
        self.notes_browser = QTextBrowser()
        self.notes_browser.setObjectName("notesBrowser")
        self.notes_browser.setPlainText(self.update_info.get('release_notes', 'No release notes available.'))
        layout.addWidget(self.notes_browser)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        later_btn = QPushButton("⏰ Later")
        later_btn.setObjectName("laterButton")
        later_btn.clicked.connect(self.reject)
        button_layout.addWidget(later_btn)
        
        download_btn = QPushButton("📥 Download & Install")
        download_btn.setObjectName("downloadButton")
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        layout.addLayout(button_layout)
    
    def apply_styles(self):
        """Apply styles to the update dialog"""
        style = """
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QFrame#updateHeader {
            background-color: #007acc;
            border-radius: 8px;
            margin: 10px;
            padding: 20px;
        }
        
        QLabel#updateTitle {
            color: white;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        QLabel#updateVersion {
            color: #e3f2fd;
            font-size: 12px;
            margin-bottom: 5px;
        }
        
        QLabel#updateCurrent {
            color: #bbdefb;
            font-size: 10px;
        }
        
        QLabel#notesLabel {
            color: #ffffff;
            font-size: 12px;
            font-weight: bold;
            margin: 10px 0 5px 0;
        }
        
        QTextBrowser#notesBrowser {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            border-radius: 4px;
            padding: 10px;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
        }
        
        QPushButton#laterButton {
            background-color: #404040;
            color: #ffffff;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 11px;
        }
        
        QPushButton#laterButton:hover {
            background-color: #4a4a4a;
        }
        
        QPushButton#downloadButton {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        
        QPushButton#downloadButton:hover {
            background-color: #218838;
        }
        """
        self.setStyleSheet(style)
    
    def download_update(self):
        """Download and install the update"""
        download_url = self.update_info.get('installer_url', '')
        if not download_url:
            QMessageBox.warning(self, "Error", "No download URL available")
            return
        
        # Show download dialog
        self.accept()
        self.parent().show_download_dialog(download_url)

class DownloadDialog(QDialog):
    """Dialog to show download progress"""
    def __init__(self, parent, download_url):
        super().__init__(parent)
        self.download_url = download_url
        self.setWindowTitle("Downloading Update")
        self.setModal(True)
        self.resize(400, 200)
        self.setup_ui()
        self.apply_styles()
        self.start_download()
    
    def setup_ui(self):
        """Setup the download dialog UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel("📥 Downloading Update...")
        title_label.setObjectName("downloadTitle")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing download...")
        self.status_label.setObjectName("downloadStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
    
    def apply_styles(self):
        """Apply styles to the download dialog"""
        style = """
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QLabel#downloadTitle {
            color: #007acc;
            font-size: 14px;
            font-weight: bold;
            margin: 20px;
        }
        
        QLabel#downloadStatus {
            color: #cccccc;
            font-size: 11px;
            margin: 20px;
        }
        
        QProgressBar {
            border: 1px solid #3e3e42;
            border-radius: 4px;
            text-align: center;
            margin: 10px;
        }
        
        QProgressBar::chunk {
            background-color: #007acc;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(style)
    
    def start_download(self):
        """Start downloading the update"""
        def download_thread():
            try:
                requests = safe_import_requests()
                if not requests:
                    raise Exception("Requests library not available")
                
                self.status_label.setText("Downloading installer...")
                
                response = requests.get(self.download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Save to temp directory
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, f"{APP_NAME.replace(' ', '_')}_Setup.exe")
                
                with open(installer_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                self.status_label.setText("Download complete! Starting installer...")
                
                # Start installer
                subprocess.Popen([installer_path])
                
                # Close application
                QApplication.quit()
                
            except Exception as e:
                self.progress_bar.setRange(0, 1)
                self.progress_bar.setValue(0)
                self.status_label.setText(f"Download failed: {str(e)}")
                
                # Add close button
                close_btn = QPushButton("Close")
                close_btn.clicked.connect(self.reject)
                self.layout().addWidget(close_btn)
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=download_thread, daemon=True)
        self.download_thread.start()

class ModernApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize components
        self.config = self.load_config()
        self.current_file = None
        self.unsaved_changes = False
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
        # Connect signals
        self.setup_connections()
        
        # Check for updates on startup if enabled
        if self.config.get('check_updates_on_startup', True):
            QTimer.singleShot(5000, self.check_for_updates_silent)  # Wait 5 seconds
    
    def setup_ui(self):
        """Setup the main user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create sidebar
        self.create_sidebar(splitter)
        
        # Create main content area
        self.create_main_content(splitter)
        
        # Set splitter proportions
        splitter.setSizes([250, 950])
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.create_status_bar()
    
    def create_sidebar(self, parent):
        """Create sidebar with navigation and stats"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        # App header
        header_frame = QFrame()
        header_frame.setObjectName("sidebarHeader")
        header_frame.setFixedHeight(80)
        header_layout = QVBoxLayout(header_frame)
        
        app_title = QLabel(APP_NAME)
        app_title.setObjectName("appTitle")
        app_title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(app_title)
        
        sidebar_layout.addWidget(header_frame)
        
                # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_group.setObjectName("actionsGroup")
        actions_layout = QVBoxLayout(actions_group)
        
        # Action buttons
        actions = [
            ("📄 New File", self.new_file),
            ("📂 Open File", self.open_file),
            ("💾 Save File", self.save_file),
            ("🔍 Find", self.show_find_dialog)
        ]
        
        for text, command in actions:
            btn = QPushButton(text)
            btn.setObjectName("actionButton")
            btn.clicked.connect(command)
            actions_layout.addWidget(btn)
        
        sidebar_layout.addWidget(actions_group)
        
        # Document Stats
        stats_group = QGroupBox("Document Stats")
        stats_group.setObjectName("statsGroup")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("Lines: 0\nWords: 0\nCharacters: 0")
        self.stats_label.setObjectName("statsLabel")
        stats_layout.addWidget(self.stats_label)
        
        sidebar_layout.addWidget(stats_group)
        
        # Recent Files
        recent_group = QGroupBox("Recent Files")
        recent_group.setObjectName("recentGroup")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("recentList")
        self.recent_list.itemDoubleClicked.connect(self.open_recent_file)
        recent_layout.addWidget(self.recent_list)
        
        sidebar_layout.addWidget(recent_group)
        
        # Add stretch to push everything up
        sidebar_layout.addStretch()
        
        parent.addWidget(sidebar)
        
        # Update recent files list
        self.update_recent_files_list()
    
    def create_main_content(self, parent):
        """Create main content area with tabs"""
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        
        # Create tabs
        self.create_home_tab()
        self.create_editor_tab()
        self.create_settings_tab()
        
        parent.addWidget(self.tab_widget)
    
    def create_home_tab(self):
        """Create home tab"""
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        
        # Scroll area for home content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Welcome section
        welcome_frame = QFrame()
        welcome_frame.setObjectName("welcomeFrame")
        welcome_frame.setFixedHeight(150)
        welcome_layout = QVBoxLayout(welcome_frame)
        
        welcome_title = QLabel(f"Welcome to {APP_NAME}! 🎉")
        welcome_title.setObjectName("welcomeTitle")
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_title)
        
        welcome_subtitle = QLabel(f"Version {CURRENT_VERSION} • Modern Text Editor")
        welcome_subtitle.setObjectName("welcomeSubtitle")
        welcome_subtitle.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(welcome_subtitle)
        
        scroll_layout.addWidget(welcome_frame)
        
        # Features section
        features_title = QLabel("Features & Capabilities")
        features_title.setObjectName("sectionTitle")
        scroll_layout.addWidget(features_title)
        
        # Feature cards in a grid
        features_widget = QWidget()
        features_grid = QGridLayout(features_widget)
        
        features = [
            ("📝 Advanced Text Editor", "Syntax highlighting, find & replace, line numbers"),
            ("🎨 Modern Themes", "Dark, light, and blue themes with professional styling"),
            ("🔄 Auto-Updates", "Automatic update checking and installation"),
            ("💾 Smart Saving", "Auto-save, backup creation, recent files"),
            ("⚙️ Customizable", "Fonts, themes, editor preferences"),
            ("🚀 Modern Interface", "Built with PyQt5 and CSS-like styling")
        ]
        
        for i, (title, description) in enumerate(features):
            row = i // 2
            col = i % 2
            
            card = QFrame()
            card.setObjectName("featureCard")
            card_layout = QVBoxLayout(card)
            
            card_title = QLabel(title)
            card_title.setObjectName("featureTitle")
            card_layout.addWidget(card_title)
            
            card_desc = QLabel(description)
            card_desc.setObjectName("featureDescription")
            card_desc.setWordWrap(True)
            card_layout.addWidget(card_desc)
            
            features_grid.addWidget(card, row, col)
        
        scroll_layout.addWidget(features_widget)
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        home_layout.addWidget(scroll)
        
        self.tab_widget.addTab(home_widget, "🏠 Home")
    
    def create_editor_tab(self):
        """Create editor tab"""
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)
        
        # Editor toolbar
        toolbar = QFrame()
        toolbar.setObjectName("editorToolbar")
        toolbar.setFixedHeight(50)
        toolbar_layout = QHBoxLayout(toolbar)
        
        # File operations
        file_buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Save As", self.save_file_as)
        ]
        
        for text, command in file_buttons:
            btn = QPushButton(text)
            btn.setObjectName("toolbarButton")
            btn.clicked.connect(command)
            toolbar_layout.addWidget(btn)
        
        toolbar_layout.addStretch()
        
        # Edit operations
        edit_buttons = [
            ("Find", self.show_find_dialog),
            ("Word Count", self.show_word_count)
        ]
        
        for text, command in edit_buttons:
            btn = QPushButton(text)
            btn.setObjectName("toolbarButton")
            btn.clicked.connect(command)
            toolbar_layout.addWidget(btn)
        
        editor_layout.addWidget(toolbar)
        
        # Text editor
        self.text_editor = QTextEdit()
        self.text_editor.setObjectName("textEditor")
        self.text_editor.setFont(QFont(self.config.get('font_family', 'Consolas'), 
                                     self.config.get('font_size', 11)))
        self.text_editor.textChanged.connect(self.on_text_changed)
        editor_layout.addWidget(self.text_editor)
        
        self.tab_widget.addTab(editor_widget, "📝 Editor")
    
    def create_settings_tab(self):
        """Create settings tab with update preferences"""
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        # Settings scroll area
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Theme settings
        theme_group = QGroupBox("Appearance")
        theme_group.setObjectName("settingsGroup")
        theme_layout = QGridLayout(theme_group)
        
        theme_layout.addWidget(QLabel("Theme:"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "Blue"])
        self.theme_combo.setCurrentText(self.config.get('theme', 'Dark'))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        scroll_layout.addWidget(theme_group)
        
        # Editor settings
        editor_group = QGroupBox("Editor")
        editor_group.setObjectName("settingsGroup")
        editor_layout = QGridLayout(editor_group)
        
        editor_layout.addWidget(QLabel("Font Family:"), 0, 0)
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Courier New", "Monaco", "Source Code Pro"])
        self.font_combo.setCurrentText(self.config.get('font_family', 'Consolas'))
        self.font_combo.currentTextChanged.connect(self.change_font)
        editor_layout.addWidget(self.font_combo, 0, 1)
        
        editor_layout.addWidget(QLabel("Font Size:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(self.config.get('font_size', 11))
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        editor_layout.addWidget(self.font_size_spin, 1, 1)
        
        self.auto_save_check = QCheckBox("Enable auto-save")
        self.auto_save_check.setChecked(self.config.get('auto_save', True))
        self.auto_save_check.toggled.connect(self.toggle_auto_save)
        editor_layout.addWidget(self.auto_save_check, 2, 0, 1, 2)
        
        scroll_layout.addWidget(editor_group)
        
        # Update settings
        update_group = QGroupBox("Updates")
        update_group.setObjectName("settingsGroup")
        update_layout = QVBoxLayout(update_group)
        
        self.auto_update_check = QCheckBox("Check for updates on startup")
        self.auto_update_check.setChecked(self.config.get('check_updates_on_startup', True))
        self.auto_update_check.toggled.connect(self.toggle_auto_update)
        update_layout.addWidget(self.auto_update_check)
        
        # Last update check info
        last_check = self.config.get('last_update_check', 'Never')
        self.last_check_label = QLabel(f"Last checked: {last_check}")
        self.last_check_label.setObjectName("lastCheckLabel")
        update_layout.addWidget(self.last_check_label)
        
        # Manual update check button
        check_now_btn = QPushButton("🔄 Check for Updates Now")
        check_now_btn.setObjectName("checkUpdateButton")
        check_now_btn.clicked.connect(self.check_for_updates_manual)
        update_layout.addWidget(check_now_btn)
        
        scroll_layout.addWidget(update_group)
        
        # App info
        info_group = QGroupBox("Application Info")
        info_group.setObjectName("settingsGroup")
        info_layout = QVBoxLayout(info_group)
        
        version_label = QLabel(f"Version: {CURRENT_VERSION}")
        version_label.setObjectName("versionInfoLabel")
        info_layout.addWidget(version_label)
        
        github_btn = QPushButton("🌐 Visit GitHub Repository")
        github_btn.setObjectName("githubButton")
        github_btn.clicked.connect(self.open_github)
        info_layout.addWidget(github_btn)
        
        scroll_layout.addWidget(info_group)
        
        scroll_layout.addStretch()
        
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        settings_layout.addWidget(scroll)
        
        self.tab_widget.addTab(settings_widget, "⚙️ Settings")
    
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        new_action = QAction('New', self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction('Open', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('Save', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction('Save As', self)
        save_as_action.setShortcut('Ctrl+Shift+S')
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('Edit')
        
        undo_action = QAction('Undo', self)
        undo_action.setShortcut('Ctrl+Z')
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction('Redo', self)
        redo_action.setShortcut('Ctrl+Y')
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        cut_action = QAction('Cut', self)
        cut_action.setShortcut('Ctrl+X')
        cut_action.triggered.connect(self.cut)
        edit_menu.addAction(cut_action)
        
        copy_action = QAction('Copy', self)
        copy_action.setShortcut('Ctrl+C')
        copy_action.triggered.connect(self.copy)
        edit_menu.addAction(copy_action)
        
        paste_action = QAction('Paste', self)
        paste_action.setShortcut('Ctrl+V')
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction('Find & Replace', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.show_find_dialog)
        edit_menu.addAction(find_action)
        
                # View menu
        view_menu = menubar.addMenu('View')
        
        theme_submenu = view_menu.addMenu('Theme')
        
        dark_theme_action = QAction('Dark Theme', self)
        dark_theme_action.triggered.connect(lambda: self.change_theme('Dark'))
        theme_submenu.addAction(dark_theme_action)
        
        light_theme_action = QAction('Light Theme', self)
        light_theme_action.triggered.connect(lambda: self.change_theme('Light'))
        theme_submenu.addAction(light_theme_action)
        
        blue_theme_action = QAction('Blue Theme', self)
        blue_theme_action.triggered.connect(lambda: self.change_theme('Blue'))
        theme_submenu.addAction(blue_theme_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        check_updates_action = QAction('Check for Updates', self)
        check_updates_action.triggered.connect(self.check_for_updates_manual)
        help_menu.addAction(check_updates_action)
        
        help_menu.addSeparator()
        
        github_action = QAction('Visit GitHub', self)
        github_action.triggered.connect(self.open_github)
        help_menu.addAction(github_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Version label on right
        version_label = QLabel(f"v{CURRENT_VERSION}")
        version_label.setObjectName("versionLabel")
        self.status_bar.addPermanentWidget(version_label)
        
        # Document stats timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_document_stats)
        self.stats_timer.start(2000)  # Update every 2 seconds
    
    def setup_connections(self):
        """Setup signal connections"""
        pass  # Additional connections can be added here
    
    def load_config(self):
        """Load application configuration"""
        default_config = {
            'theme': 'Dark',
            'auto_save': True,
            'font_family': 'Consolas',
            'font_size': 11,
            'recent_files': [],
            'window_geometry': [100, 100, 1200, 800],
            'check_updates_on_startup': True,
            'last_update_check': ''
        }
        
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
        except Exception as e:
            print(f"Could not load config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save application configuration"""
        try:
            # Save window geometry
            geometry = self.geometry()
            self.config['window_geometry'] = [geometry.x(), geometry.y(), geometry.width(), geometry.height()]
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")
    
    # File operations
    def new_file(self):
        """Create new file"""
        if self.unsaved_changes:
            reply = QMessageBox.question(self, 'Unsaved Changes', 
                                       'You have unsaved changes. Continue?',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        self.text_editor.clear()
        self.current_file = None
        self.unsaved_changes = False
        self.status_label.setText("New file created")
        self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION} - Untitled")
    
    def open_file(self):
        """Open file"""
        if self.unsaved_changes:
            reply = QMessageBox.question(self, 'Unsaved Changes', 
                                       'You have unsaved changes. Continue?',
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Open File",
            "",
            "Text files (*.txt);;Python files (*.py);;All files (*.*)"
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.text_editor.setPlainText(content)
            self.current_file = file_path
            self.unsaved_changes = False
            self.add_to_recent_files(file_path)
            self.status_label.setText(f"Opened: {os.path.basename(file_path)}")
            self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(file_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open file:\n{str(e)}")
    
    def save_file(self):
        """Save file"""
        if not self.current_file:
            self.save_file_as()
        else:
            try:
                content = self.text_editor.toPlainText()
                
                # Create backup
                if os.path.exists(self.current_file):
                    backup_path = self.current_file + '.backup'
                    import shutil
                    shutil.copy2(self.current_file, backup_path)
                
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.unsaved_changes = False
                self.status_label.setText(f"Saved: {os.path.basename(self.current_file)}")
                self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
    
    def save_file_as(self):
        """Save file as"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File As",
            "",
            "Text files (*.txt);;Python files (*.py);;All files (*.*)"
        )
        
        if file_path:
            try:
                content = self.text_editor.toPlainText()
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.current_file = file_path
                self.unsaved_changes = False
                self.add_to_recent_files(file_path)
                self.status_label.setText(f"Saved as: {os.path.basename(file_path)}")
                self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save file:\n{str(e)}")
    
    # Edit operations
    def undo(self):
        """Undo last action"""
        self.text_editor.undo()
    
    def redo(self):
        """Redo last undone action"""
        self.text_editor.redo()
    
    def cut(self):
        """Cut selected text"""
        self.text_editor.cut()
    
    def copy(self):
        """Copy selected text"""
        self.text_editor.copy()
    
    def paste(self):
        """Paste text from clipboard"""
        self.text_editor.paste()
    
    def show_find_dialog(self):
        """Show find and replace dialog"""
        # Simple find dialog implementation
        text, ok = QFileDialog.getOpenFileName(self, 'Find Text', '')
        if ok and text:
            cursor = self.text_editor.textCursor()
            found = self.text_editor.find(text)
            if not found:
                QMessageBox.information(self, "Find", "Text not found")
    
    def show_word_count(self):
        """Show word count dialog"""
        content = self.text_editor.toPlainText()
        
        # Calculate statistics
        lines = len(content.split('\n')) if content else 0
        words = len(content.split()) if content else 0
        chars = len(content)
        chars_no_spaces = len(content.replace(' ', '').replace('\n', '').replace('\t', ''))
        
        stats_text = f"""Document Statistics:

Lines: {lines:,}
Words: {words:,}
Characters: {chars:,}
Characters (no spaces): {chars_no_spaces:,}

Paragraphs: {len([p for p in content.split('\n\n') if p.strip()]) if content else 0}
"""
        
        QMessageBox.information(self, "Document Statistics", stats_text)
    
    # Recent files management
    def add_to_recent_files(self, file_path):
        """Add file to recent files list"""
        recent_files = self.config.get('recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only last 10 files
        recent_files = recent_files[:10]
        
        self.config['recent_files'] = recent_files
        self.save_config()
        self.update_recent_files_list()
    
    def update_recent_files_list(self):
        """Update recent files listbox"""
        self.recent_list.clear()
        recent_files = self.config.get('recent_files', [])
        
        for file_path in recent_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                self.recent_list.addItem(filename)
    
    def open_recent_file(self, item):
        """Open recent file from list"""
        filename = item.text()
        recent_files = self.config.get('recent_files', [])
        
        for file_path in recent_files:
            if os.path.basename(file_path) == filename:
                if os.path.exists(file_path):
                    self.load_file(file_path)
                break
    
    # Document statistics
    def update_document_stats(self):
        """Update document statistics in sidebar"""
        try:
            content = self.text_editor.toPlainText()
            lines = len(content.split('\n')) if content else 0
            words = len(content.split()) if content else 0
            chars = len(content)
            
            stats_text = f"Lines: {lines:,}\nWords: {words:,}\nCharacters: {chars:,}"
            self.stats_label.setText(stats_text)
        except:
            pass
    
    # Text change handling
    def on_text_changed(self):
        """Handle text editor changes"""
        self.unsaved_changes = True
        if self.current_file:
            title = f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)} *"
        else:
            title = f"{APP_NAME} v{CURRENT_VERSION} - Untitled *"
        self.setWindowTitle(title)
        
        # Auto-save
        if self.config.get('auto_save', True) and self.current_file:
            QTimer.singleShot(3000, self.auto_save)
    
    def auto_save(self):
        """Auto-save current file"""
        if self.unsaved_changes and self.current_file and self.config.get('auto_save', True):
            try:
                content = self.text_editor.toPlainText()
                
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.unsaved_changes = False
                self.status_label.setText(f"Auto-saved: {os.path.basename(self.current_file)}")
                
                # Update title to remove asterisk
                self.setWindowTitle(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)}")
                
            except Exception as e:
                self.status_label.setText(f"Auto-save failed: {str(e)}")
    
    # Settings event handlers
    def change_theme(self, theme_name):
        """Change application theme"""
        self.config['theme'] = theme_name
        self.save_config()
        self.apply_styles()
        self.status_label.setText(f"Theme changed to {theme_name}")
    
    def change_font(self):
        """Change editor font family"""
        font_family = self.font_combo.currentText()
        self.config['font_family'] = font_family
        self.save_config()
        
        # Update text editor font
        current_size = self.text_editor.font().pointSize()
        new_font = QFont(font_family, current_size)
        self.text_editor.setFont(new_font)
        
        self.status_label.setText(f"Font changed to {font_family}")
    
    def change_font_size(self):
        """Change editor font size"""
        font_size = self.font_size_spin.value()
        self.config['font_size'] = font_size
        self.save_config()
        
        # Update text editor font
        current_font = self.text_editor.font()
        current_font.setPointSize(font_size)
        self.text_editor.setFont(current_font)
        
        self.status_label.setText(f"Font size changed to {font_size}")
    
    def toggle_auto_save(self, checked):
        """Toggle auto-save setting"""
        self.config['auto_save'] = checked
        self.save_config()
        
        status = "enabled" if checked else "disabled"
        self.status_label.setText(f"Auto-save {status}")
    
    def toggle_auto_update(self, checked):
        """Toggle auto-update checking"""
        self.config['check_updates_on_startup'] = checked
        self.save_config()
        
        status = "enabled" if checked else "disabled"
        self.status_label.setText(f"Auto-update check {status}")
    
    # Update checking methods
    def check_for_updates_silent(self):
        """Check for updates silently (no user interaction if up to date)"""
        self.update_checker = UpdateChecker(silent=True)
        self.update_thread = QThread()
        
        # Move checker to thread
        self.update_checker.moveToThread(self.update_thread)
        
        # Connect signals
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.update_error.connect(self.on_update_error_silent)
        self.update_checker.no_update.connect(self.on_no_update_silent)
        
        # Start checking
        self.update_thread.started.connect(self.update_checker.check_for_updates)
        self.update_thread.start()
    
    def check_for_updates_manual(self):
        """Check for updates manually (show result to user)"""
        self.status_label.setText("Checking for updates...")
        
        self.update_checker = UpdateChecker(silent=False)
        self.update_thread = QThread()
        
        # Move checker to thread
        self.update_checker.moveToThread(self.update_thread)
        
        # Connect signals
        self.update_checker.update_available.connect(self.on_update_available)
        self.update_checker.update_error.connect(self.on_update_error)
        self.update_checker.no_update.connect(self.on_no_update)
        
        # Start checking
        self.update_thread.started.connect(self.update_checker.check_for_updates)
        self.update_thread.start()
    
    def on_update_available(self, update_info):
        """Handle when update is available"""
        self.update_thread.quit()
        self.status_label.setText(f"Update available: v{update_info.get('version', 'Unknown')}")
        
        # Update last check time
        self.config['last_update_check'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save_config()
        
        # Update the label in settings if it exists
        if hasattr(self, 'last_check_label'):
            self.last_check_label.setText(f"Last checked: {self.config['last_update_check']}")
        
        # Show update dialog
        dialog = UpdateDialog(self, update_info)
        dialog.exec_()
    
    def on_update_error(self, error_message):
        """Handle update check error (manual check)"""
        self.update_thread.quit()
        self.status_label.setText("Update check failed")
        QMessageBox.warning(self, "Update Check Failed", error_message)
    
    def on_update_error_silent(self, error_message):
        """Handle update check error (silent check)"""
        self.update_thread.quit()
        self.status_label.setText("Update check failed")
        print(f"Silent update check failed: {error_message}")
    
    def on_no_update(self, message):
        """Handle when no update is available (manual check)"""
        self.update_thread.quit()
        self.status_label.setText("Up to date")
        QMessageBox.information(self, "No Updates", message)
    
    def on_no_update_silent(self, message):
        """Handle when no update is available (silent check)"""
        self.update_thread.quit()
        self.status_label.setText("Up to date")
        
        # Update last check time
        self.config['last_update_check'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.save_config()
        
        # Update the label in settings if it exists
        if hasattr(self, 'last_check_label'):
            self.last_check_label.setText(f"Last checked: {self.config['last_update_check']}")
        
        print(f"Silent update check: {message}")
    
    def show_download_dialog(self, download_url):
        """Show download dialog"""
        dialog = DownloadDialog(self, download_url)
        dialog.exec_()
    
    def open_github(self):
        """Open GitHub repository"""
        github_url = VERSION_URL.replace("/raw.githubusercontent.com/", "/github.com/").replace("/main/version.json", "")
        webbrowser.open(github_url)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""
        <h2>{APP_NAME}</h2>
        <p><b>Version:</b> {CURRENT_VERSION}</p>
        <p><b>Description:</b> A modern, feature-rich text editor built with PyQt5.</p>
        
        <h3>Features:</h3>
        <ul>
        <li>Advanced text editing with syntax highlighting</li>
        <li>Auto-save and backup functionality</li>
        <li>Dark, light, and blue themes</li>
        <li>Automatic updates</li>
        <li>Professional, modern interface</li>
        </ul>
        
        <h3>Built with:</h3>
        <ul>
        <li>Python 3.x</li>
        <li>PyQt5 (GUI framework)</li>
        <li>Requests (updates)</li>
        </ul>
        
        <p><b>© 2025 PixelHeaven</b><br>
        Open source software</p>
        """
        
        msg = QMessageBox()
        msg.setWindowTitle("About")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    def apply_styles(self):
        """Apply theme-based styles"""
        theme = self.config.get('theme', 'Dark')
        
        if theme == 'Dark':
            self.apply_dark_theme()
        elif theme == 'Light':
            self.apply_light_theme()
        elif theme == 'Blue':
            self.apply_blue_theme()
    
    def apply_dark_theme(self):
        """Apply dark theme styles"""
        style = """
        /* Main Application */
        QMainWindow {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        /* Sidebar */
        QFrame#sidebar {
            background-color: #252526;
            border-right: 1px solid #3e3e42;
        }
        
        QFrame#sidebarHeader {
            background-color: #007acc;
            border: none;
        }
        
        QLabel#appTitle {
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }
        
        /* Welcome Section */
        QFrame#welcomeFrame {
            background-color: #007acc;
            border-radius: 8px;
            margin: 10px;
        }
        
        QLabel#welcomeTitle {
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin: 20px;
        }
        
        QLabel#welcomeSubtitle {
            color: #e3f2fd;
            font-size: 12px;
            margin: 10px;
        }
        
        QLabel#sectionTitle {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            margin: 20px 10px 10px 10px;
        }
        
        /* Feature Cards */
        QFrame#featureCard {
            background-color: #3c3c3c;
            border: 1px solid #5a5a5a;
            border-radius: 8px;
            margin: 5px;
            padding: 10px;
        }
        
        QLabel#featureTitle {
            color: #4fc3f7;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        QLabel#featureDescription {
            color: #cccccc;
            font-size: 10px;
            margin-bottom: 10px;
        }
        
        /* Groups */
        QGroupBox {
            color: #cccccc;
            border: 1px solid #3e3e42;
            border-radius: 5px;
            margin: 10px 5px;
            padding-top: 10px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QGroupBox#actionsGroup, QGroupBox#statsGroup, QGroupBox#recentGroup, QGroupBox#settingsGroup {
            background-color: #2d2d30;
        }
        
        /* Buttons */
        QPushButton#actionButton, QPushButton#toolbarButton {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 8px 16px;
            border-radius: 4px;
            text-align: left;
            margin: 2px;
        }
        
        QPushButton#actionButton:hover, QPushButton#toolbarButton:hover {
            background-color: #4a4a4a;
            border-color: #666666;
        }
        
        QPushButton#actionButton:pressed, QPushButton#toolbarButton:pressed {
            background-color: #555555;
        }
        
        /* Settings Labels */
        QLabel#lastCheckLabel {
            color: #cccccc;
            font-size: 10px;
            font-style: italic;
            margin: 5px 0;
        }
        
        QLabel#versionInfoLabel {
            color: #007acc;
            font-size: 12px;
            font-weight: bold;
        }
        
        QLabel#versionLabel {
            color: #007acc;
            font-size: 10px;
            font-weight: bold;
        }
        
        /* Update Buttons */
        QPushButton#checkUpdateButton {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin: 5px 0;
        }
        
        QPushButton#checkUpdateButton:hover {
            background-color: #1177bb;
        }
        
        QPushButton#githubButton {
            background-color: #6f42c1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            margin: 5px 0;
        }
        
        QPushButton#githubButton:hover {
            background-color: #8a63d2;
        }
        
        /* Text Editor */
        QTextEdit#textEditor {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            selection-background-color: #264f78;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Toolbar */
        QFrame#editorToolbar {
            background-color: #2d2d30;
            border-bottom: 1px solid #3e3e42;
        }
        
        /* Tab Widget */
        QTabWidget#mainTabWidget {
            background-color: #2b2b2b;
        }
        
        QTabWidget#mainTabWidget::pane {
            border: 1px solid #3e3e42;
            background-color: #2b2b2b;
        }
        
        QTabWidget#mainTabWidget::tab-bar {
            left: 5px;
        }
        
        QTabBar::tab {
            background-color: #2d2d30;
            color: #cccccc;
            border: 1px solid #3e3e42;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #3e3e42;
        }
        
        /* Lists */
        QListWidget#recentList {
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid #3e3e42;
            alternate-background-color: #2a2a2a;
        }
        
        QListWidget#recentList::item {
            padding: 5px;
            border-bottom: 1px solid #3e3e42;
        }
        
        QListWidget#recentList::item:selected {
            background-color: #007acc;
        }
        
        QListWidget#recentList::item:hover {
            background-color: #3e3e42;
        }
        
        /* Labels */
        QLabel#statsLabel {
            color: #cccccc;
            font-size: 11px;
            margin: 10px;
        }
        
        /* Combo Boxes */
        QComboBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox::down-arrow {
            image: none;
            border: none;
        }
        
        /* Spin Boxes */
        QSpinBox {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Checkboxes */
        QCheckBox {
            color: #cccccc;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #404040;
            border: 1px solid #555555;
        }
        
        QCheckBox::indicator:checked {
            background-color: #007acc;
            border: 1px solid #007acc;
        }
        
        /* Scroll Areas */
        QScrollArea {
            background-color: #2b2b2b;
            border: none;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #252526;
            color: #cccccc;
            border-top: 1px solid #3e3e42;
        }
        
        /* Menu Bar */
        QMenuBar {
                        background-color: #2d2d30;
            color: #cccccc;
            border-bottom: 1px solid #3e3e42;
        }
        
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        
        QMenuBar::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #2d2d30;
            color: #cccccc;
            border: 1px solid #3e3e42;
        }
        
        QMenu::item {
            padding: 6px 20px;
        }
        
        QMenu::item:selected {
            background-color: #007acc;
            color: #ffffff;
        }
        
        QMenu::separator {
            height: 1px;
            background-color: #3e3e42;
            margin: 2px 0;
        }
        """
        self.setStyleSheet(style)
    
    def apply_light_theme(self):
        """Apply light theme styles"""
        style = """
        /* Main Application */
        QMainWindow {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Sidebar */
        QFrame#sidebar {
            background-color: #f5f5f5;
            border-right: 1px solid #e0e0e0;
        }
        
        QFrame#sidebarHeader {
            background-color: #2196f3;
            border: none;
        }
        
        QLabel#appTitle {
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }
        
        /* Welcome Section */
        QFrame#welcomeFrame {
            background-color: #2196f3;
            border-radius: 8px;
            margin: 10px;
        }
        
        QLabel#welcomeTitle {
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin: 20px;
        }
        
        QLabel#welcomeSubtitle {
            color: #e3f2fd;
            font-size: 12px;
            margin: 10px;
        }
        
        QLabel#sectionTitle {
            color: #000000;
            font-size: 16px;
            font-weight: bold;
            margin: 20px 10px 10px 10px;
        }
        
        /* Feature Cards */
        QFrame#featureCard {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            margin: 5px;
            padding: 10px;
        }
        
        QLabel#featureTitle {
            color: #1976d2;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        QLabel#featureDescription {
            color: #666666;
            font-size: 10px;
            margin-bottom: 10px;
        }
        
        /* Groups */
        QGroupBox {
            color: #333333;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            margin: 10px 5px;
            padding-top: 10px;
            font-weight: bold;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
        
        QGroupBox#actionsGroup, QGroupBox#statsGroup, QGroupBox#recentGroup, QGroupBox#settingsGroup {
            background-color: #fafafa;
        }
        
        /* Buttons */
        QPushButton#actionButton, QPushButton#toolbarButton {
            background-color: #e3f2fd;
            color: #1976d2;
            border: 1px solid #bbdefb;
            padding: 8px 16px;
            border-radius: 4px;
            text-align: left;
            margin: 2px;
        }
        
        QPushButton#actionButton:hover, QPushButton#toolbarButton:hover {
            background-color: #bbdefb;
            border-color: #90caf9;
        }
        
        QPushButton#actionButton:pressed, QPushButton#toolbarButton:pressed {
            background-color: #90caf9;
        }
        
        /* Settings Labels */
        QLabel#lastCheckLabel {
            color: #666666;
            font-size: 10px;
            font-style: italic;
            margin: 5px 0;
        }
        
        QLabel#versionInfoLabel {
            color: #2196f3;
            font-size: 12px;
            font-weight: bold;
        }
        
        QLabel#versionLabel {
            color: #2196f3;
            font-size: 10px;
            font-weight: bold;
        }
        
        /* Update Buttons */
        QPushButton#checkUpdateButton {
            background-color: #2196f3;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin: 5px 0;
        }
        
        QPushButton#checkUpdateButton:hover {
            background-color: #1976d2;
        }
        
        QPushButton#githubButton {
            background-color: #673ab7;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            margin: 5px 0;
        }
        
        QPushButton#githubButton:hover {
            background-color: #5e35b1;
        }
        
        /* Text Editor */
        QTextEdit#textEditor {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            selection-background-color: #bbdefb;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Toolbar */
        QFrame#editorToolbar {
            background-color: #f5f5f5;
            border-bottom: 1px solid #e0e0e0;
        }
        
        /* Tab Widget */
        QTabWidget#mainTabWidget {
            background-color: #ffffff;
        }
        
        QTabWidget#mainTabWidget::pane {
            border: 1px solid #e0e0e0;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f5f5f5;
            color: #333333;
            border: 1px solid #e0e0e0;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #2196f3;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #e3f2fd;
        }
        
        /* Lists */
        QListWidget#recentList {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            alternate-background-color: #f8f9fa;
        }
        
        QListWidget#recentList::item {
            padding: 5px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        QListWidget#recentList::item:selected {
            background-color: #2196f3;
            color: #ffffff;
        }
        
        QListWidget#recentList::item:hover {
            background-color: #e3f2fd;
        }
        
        /* Labels */
        QLabel#statsLabel {
            color: #333333;
            font-size: 11px;
            margin: 10px;
        }
        
        /* Combo Boxes */
        QComboBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Spin Boxes */
        QSpinBox {
            background-color: #ffffff;
            color: #000000;
            border: 1px solid #e0e0e0;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Checkboxes */
        QCheckBox {
            color: #333333;
            spacing: 8px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
        }
        
        QCheckBox::indicator:checked {
            background-color: #2196f3;
            border: 1px solid #2196f3;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #f5f5f5;
            color: #333333;
            border-top: 1px solid #e0e0e0;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #ffffff;
            color: #333333;
            border-bottom: 1px solid #e0e0e0;
        }
        
        QMenuBar::item:selected {
            background-color: #2196f3;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #e0e0e0;
        }
        
        QMenu::item:selected {
            background-color: #2196f3;
            color: #ffffff;
        }
        """
        self.setStyleSheet(style)
    
    def apply_blue_theme(self):
        """Apply blue theme styles"""
        style = """
        /* Main Application */
        QMainWindow {
            background-color: #0d1b2a;
            color: #ffffff;
        }
        
        /* Sidebar */
        QFrame#sidebar {
            background-color: #1b263b;
            border-right: 1px solid #415a77;
        }
        
        QFrame#sidebarHeader {
            background-color: #0077be;
            border: none;
        }
        
        QLabel#appTitle {
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }
        
        /* Welcome Section */
        QFrame#welcomeFrame {
            background-color: #0077be;
            border-radius: 8px;
            margin: 10px;
        }
        
        QLabel#welcomeTitle {
            color: white;
            font-size: 20px;
            font-weight: bold;
            margin: 20px;
        }
        
        QLabel#welcomeSubtitle {
            color: #cce7f0;
            font-size: 12px;
            margin: 10px;
        }
        
        QLabel#sectionTitle {
            color: #ffffff;
            font-size: 16px;
            font-weight: bold;
            margin: 20px 10px 10px 10px;
        }
        
        /* Feature Cards */
        QFrame#featureCard {
            background-color: #415a77;
            border: 1px solid #778da9;
            border-radius: 8px;
            margin: 5px;
            padding: 10px;
        }
        
        QLabel#featureTitle {
            color: #00b4d8;
            font-size: 12px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        QLabel#featureDescription {
            color: #e0e1dd;
            font-size: 10px;
            margin-bottom: 10px;
        }
        
        /* Groups */
        QGroupBox {
            color: #e0e1dd;
            border: 1px solid #415a77;
            border-radius: 5px;
            margin: 10px 5px;
            padding-top: 10px;
            font-weight: bold;
        }
        
        QGroupBox#actionsGroup, QGroupBox#statsGroup, QGroupBox#recentGroup, QGroupBox#settingsGroup {
            background-color: #1b263b;
        }
        
        /* Buttons */
        QPushButton#actionButton, QPushButton#toolbarButton {
            background-color: #415a77;
            color: #ffffff;
            border: 1px solid #778da9;
            padding: 8px 16px;
            border-radius: 4px;
            text-align: left;
            margin: 2px;
        }
        
        QPushButton#actionButton:hover, QPushButton#toolbarButton:hover {
            background-color: #778da9;
            border-color: #0077be;
        }
        
        /* Update Buttons */
        QPushButton#checkUpdateButton {
            background-color: #0077be;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            margin: 5px 0;
        }
        
        QPushButton#checkUpdateButton:hover {
            background-color: #005f99;
        }
        
        QPushButton#githubButton {
            background-color: #6a4c93;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 11px;
            margin: 5px 0;
        }
        
        QPushButton#githubButton:hover {
            background-color: #8b5a9e;
        }
        
        /* Text Editor */
        QTextEdit#textEditor {
            background-color: #0d1b2a;
            color: #e0e1dd;
            border: 1px solid #415a77;
            selection-background-color: #0077be;
            font-family: 'Consolas', 'Courier New', monospace;
        }
        
        /* Toolbar */
        QFrame#editorToolbar {
            background-color: #1b263b;
            border-bottom: 1px solid #415a77;
        }
        
        /* Tab Widget */
        QTabWidget#mainTabWidget {
            background-color: #0d1b2a;
        }
        
        QTabBar::tab {
            background-color: #1b263b;
            color: #e0e1dd;
            border: 1px solid #415a77;
            padding: 8px 16px;
                        margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #0077be;
            color: #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #415a77;
        }
        
        /* Lists */
        QListWidget#recentList {
            background-color: #0d1b2a;
            color: #e0e1dd;
            border: 1px solid #415a77;
            alternate-background-color: #1b263b;
        }
        
        QListWidget#recentList::item {
            padding: 5px;
            border-bottom: 1px solid #415a77;
        }
        
        QListWidget#recentList::item:selected {
            background-color: #0077be;
            color: #ffffff;
        }
        
        QListWidget#recentList::item:hover {
            background-color: #415a77;
        }
        
        /* Labels */
        QLabel#statsLabel {
            color: #e0e1dd;
            font-size: 11px;
            margin: 10px;
        }
        
        QLabel#lastCheckLabel {
            color: #e0e1dd;
            font-size: 10px;
            font-style: italic;
            margin: 5px 0;
        }
        
        QLabel#versionInfoLabel {
            color: #00b4d8;
            font-size: 12px;
            font-weight: bold;
        }
        
        QLabel#versionLabel {
            color: #00b4d8;
            font-size: 10px;
            font-weight: bold;
        }
        
        /* Combo Boxes */
        QComboBox {
            background-color: #415a77;
            color: #ffffff;
            border: 1px solid #778da9;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Spin Boxes */
        QSpinBox {
            background-color: #415a77;
            color: #ffffff;
            border: 1px solid #778da9;
            padding: 5px;
            border-radius: 3px;
        }
        
        /* Checkboxes */
        QCheckBox {
            color: #e0e1dd;
            spacing: 8px;
        }
        
        QCheckBox::indicator:unchecked {
            background-color: #415a77;
            border: 1px solid #778da9;
        }
        
        QCheckBox::indicator:checked {
            background-color: #0077be;
            border: 1px solid #0077be;
        }
        
        /* Status Bar */
        QStatusBar {
            background-color: #1b263b;
            color: #e0e1dd;
            border-top: 1px solid #415a77;
        }
        
        /* Menu Bar */
        QMenuBar {
            background-color: #1b263b;
            color: #e0e1dd;
            border-bottom: 1px solid #415a77;
        }
        
        QMenuBar::item:selected {
            background-color: #0077be;
            color: #ffffff;
        }
        
        QMenu {
            background-color: #1b263b;
            color: #e0e1dd;
            border: 1px solid #415a77;
        }
        
        QMenu::item:selected {
            background-color: #0077be;
            color: #ffffff;
        }
        """
        self.setStyleSheet(style)
    
    def closeEvent(self, event):
        """Handle application closing"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, 'Unsaved Changes',
                'You have unsaved changes. Do you want to save before closing?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_file()
                if self.unsaved_changes:  # Save was cancelled
                    event.ignore()
                    return
            elif reply == QMessageBox.Cancel:
                event.ignore()
                return
        
        # Save configuration before closing
        self.save_config()
        
        # Stop any running threads
        if hasattr(self, 'update_thread') and self.update_thread.isRunning():
            self.update_thread.quit()
            self.update_thread.wait()
        
        event.accept()
    
    def restore_window_state(self):
        """Restore window geometry and state"""
        try:
            geometry = self.config.get('window_geometry', [100, 100, 1200, 800])
            self.setGeometry(geometry[0], geometry[1], geometry[2], geometry[3])
        except:
            # Fallback to center window
            self.resize(1200, 800)
            screen = QApplication.desktop().screenGeometry()
            size = self.geometry()
            self.move(
                (screen.width() - size.width()) // 2,
                (screen.height() - size.height()) // 2
            )

class FindReplaceDialog(QDialog):
    """Find and Replace dialog"""
    def __init__(self, parent, text_editor):
        super().__init__(parent)
        self.text_editor = text_editor
        self.setWindowTitle("Find & Replace")
        self.setModal(True)
        self.resize(400, 200)
        self.setup_ui()
        self.apply_styles()
    
    def setup_ui(self):
        """Setup the find/replace dialog UI"""
        layout = QVBoxLayout(self)
        
        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_edit = QLineEdit()
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        
        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        find_btn = QPushButton("Find Next")
        find_btn.clicked.connect(self.find_next)
        button_layout.addWidget(find_btn)
        
        replace_btn = QPushButton("Replace")
        replace_btn.clicked.connect(self.replace_current)
        button_layout.addWidget(replace_btn)
        
        replace_all_btn = QPushButton("Replace All")
        replace_all_btn.clicked.connect(self.replace_all)
        button_layout.addWidget(replace_all_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Focus on find edit
        self.find_edit.setFocus()
    
    def apply_styles(self):
        """Apply styles to the dialog"""
        style = """
        QDialog {
            background-color: #2b2b2b;
            color: #ffffff;
        }
        
        QLabel {
            color: #ffffff;
            margin: 5px;
        }
        
        QLineEdit {
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555555;
            padding: 5px;
            border-radius: 3px;
            margin: 5px;
        }
        
        QPushButton {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            margin: 5px;
        }
        
        QPushButton:hover {
            background-color: #1177bb;
        }
        """
        self.setStyleSheet(style)
    
    def find_next(self):
        """Find next occurrence"""
        text = self.find_edit.text()
        if text:
            found = self.text_editor.find(text)
            if not found:
                QMessageBox.information(self, "Find", "Text not found")
    
    def replace_current(self):
        """Replace current selection"""
        if self.text_editor.textCursor().hasSelection():
            cursor = self.text_editor.textCursor()
            cursor.insertText(self.replace_edit.text())
    
    def replace_all(self):
        """Replace all occurrences"""
        find_text = self.find_edit.text()
        replace_text = self.replace_edit.text()
        
        if find_text:
            content = self.text_editor.toPlainText()
            new_content = content.replace(find_text, replace_text)
            self.text_editor.setPlainText(new_content)
            
            count = content.count(find_text)
            QMessageBox.information(self, "Replace All", f"Replaced {count} occurrences")

def setup_logging():
    """Setup application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(CURRENT_VERSION)
        app.setOrganizationName("PixelHeaven")
        app.setOrganizationDomain("pixelheaven.io")
        
        # Set application icon if available
        try:
            if os.path.exists("icon.ico"):
                app.setWindowIcon(QIcon("icon.ico"))
        except Exception as e:
            logger.warning(f"Could not load application icon: {e}")
        
        # Create and show main window
        logger.info(f"Starting {APP_NAME} v{CURRENT_VERSION}")
        window = ModernApp()
        window.restore_window_state()
        window.show()
        
        # Apply initial theme
        window.apply_styles()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        
        # Show error dialog if possible
        try:
            error_app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Application Error",
                f"An error occurred while starting the application:\n\n{str(e)}\n\n"
                f"Please check that all dependencies are installed:\n"
                f"pip install PyQt5\n"
                f"pip install requests"
            )
        except:
            print(f"Critical error: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()





