import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext
import requests
import subprocess
import sys
import os
import json
import threading
from pathlib import Path
import webbrowser
from datetime import datetime
import tempfile

CURRENT_VERSION = "1.0.1"
VERSION_URL = "https://raw.githubusercontent.com/PixelHeaven/software1/main/version.json"
APP_NAME = "MyAwesome App"
CONFIG_FILE = "config.json"

class ModernApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{CURRENT_VERSION}")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # App icon (if you have one)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Color scheme
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#2196F3',
            'secondary': '#FFC107',
            'success': '#4CAF50',
            'danger': '#F44336',
            'dark': '#212121',
            'light': '#FFFFFF'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Configuration
        self.config = self.load_config()
        
        # Create interface
        self.create_menu()
        self.create_widgets()
        self.create_status_bar()
        
        # Check for updates on startup if enabled
        if self.config.get('check_updates_on_startup', True):
            self.root.after(2000, self.check_for_updates_silent)
    
    def load_config(self):
        """Load application configuration"""
        default_config = {
            'check_updates_on_startup': True,
            'theme': 'light',
            'last_update_check': '',
            'user_name': '',
            'auto_save': True
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
        except:
            pass
        
        return default_config
    
    def save_config(self):
        """Save application configuration"""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Could not save config: {e}")
    
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Preferences", command=self.show_preferences)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Check for Updates", command=self.check_for_updates_threaded)
        help_menu.add_command(label="Visit GitHub", command=self.open_github)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
    
    def create_widgets(self):
        """Create main application widgets"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Title section
        title_frame = tk.Frame(main_container, bg=self.colors['bg'])
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_label = tk.Label(
            title_frame,
            text=f"Welcome to {APP_NAME}!",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark']
        )
        title_label.pack()
        
        version_label = tk.Label(
            title_frame,
            text=f"Version {CURRENT_VERSION}",
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        version_label.pack()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill='both', expand=True, pady=(0, 10))
        
        # Tab 1: Main functionality
        self.create_main_tab()
        
        # Tab 2: Text editor
        self.create_editor_tab()
        
        # Tab 3: Settings
        self.create_settings_tab()
        
        # Button frame
        button_frame = tk.Frame(main_container, bg=self.colors['bg'])
        button_frame.pack(fill='x', pady=(0, 5))
        
        # Modern styled buttons
        self.update_btn = tk.Button(
            button_frame,
            text="🔄 Check for Updates",
            command=self.check_for_updates_threaded,
            bg=self.colors['primary'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        self.update_btn.pack(side='right', padx=(5, 0))
        
        info_btn = tk.Button(
            button_frame,
            text="ℹ️ About",
            command=self.show_about,
            bg=self.colors['secondary'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        info_btn.pack(side='right', padx=(5, 0))
        
        # Progress frame (initially hidden)
        self.progress_frame = tk.Frame(main_container, bg=self.colors['bg'])
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 9),
            bg=self.colors['bg'],
            fg=self.colors['dark']
        )
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=300
        )
    
    def create_main_tab(self):
        """Create main functionality tab"""
        main_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(main_tab, text="🏠 Home")
        
        # Welcome message
        welcome_frame = tk.LabelFrame(
            main_tab,
            text="Welcome",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            padx=10,
            pady=10
        )
        welcome_frame.pack(fill='x', padx=10, pady=5)
        
        welcome_text = tk.Label(
            welcome_frame,
            text=f"Hello {self.config.get('user_name', 'User')}! 👋\n\n"
                 f"This is {APP_NAME} v{CURRENT_VERSION}.\n"
                 "A modern Python application with auto-update functionality.",
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            justify='left'
        )
        welcome_text.pack(anchor='w')
        
        # Features section
        features_frame = tk.LabelFrame(
            main_tab,
            text="Features",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            padx=10,
            pady=10
        )
        features_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        features = [
            "✅ Modern, user-friendly interface",
            "🔄 Automatic update checking",
            "📝 Built-in text editor",
            "⚙️ Customizable settings",
            "💾 Auto-save functionality",
            "🎨 Clean, professional design"
        ]
        
        for feature in features:
            feature_label = tk.Label(
                features_frame,
                text=feature,
                font=("Segoe UI", 10),
                bg=self.colors['bg'],
                fg=self.colors['dark'],
                anchor='w'
            )
            feature_label.pack(fill='x', pady=2)
    
    def create_editor_tab(self):
        """Create text editor tab"""
        editor_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(editor_tab, text="📝 Editor")
        
        # Editor toolbar
        toolbar = tk.Frame(editor_tab, bg=self.colors['bg'])
        toolbar.pack(fill='x', padx=5, pady=5)
        
        tk.Button(
            toolbar,
            text="New",
            command=self.new_file,
            bg=self.colors['light'],
            relief='flat',
            padx=10
        ).pack(side='left', padx=2)
        
        tk.Button(
            toolbar,
            text="Open",
            command=self.open_file,
            bg=self.colors['light'],
            relief='flat',
            padx=10
        ).pack(side='left', padx=2)
        
        tk.Button(
            toolbar,
            text="Save",
            command=self.save_file,
            bg=self.colors['light'],
            relief='flat',
            padx=10
        ).pack(side='left', padx=2)
        
        # Text editor
        editor_frame = tk.Frame(editor_tab, bg=self.colors['bg'])
        editor_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            bg=self.colors['light'],
            fg=self.colors['dark'],
            insertbackground=self.colors['primary'],
            selectbackground=self.colors['primary'],
            selectforeground='white'
        )
        self.text_editor.pack(fill='both', expand=True)
        
        # Auto-save functionality
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.current_file = None
        self.unsaved_changes = False
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(settings_tab, text="⚙️ Settings")
        
        # Settings sections
        settings_scroll = tk.Canvas(settings_tab, bg=self.colors['bg'])
        settings_scroll.pack(fill='both', expand=True, padx=10, pady=10)
        
        settings_frame = tk.Frame(settings_scroll, bg=self.colors['bg'])
        settings_scroll.create_window((0, 0), window=settings_frame, anchor='nw')
        
        # User preferences
        user_frame = tk.LabelFrame(
            settings_frame,
            text="User Preferences",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            padx=10,
            pady=10
        )
        user_frame.pack(fill='x', pady=5)
        
        tk.Label(
            user_frame,
            text="Your Name:",
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['dark']
                ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.name_var = tk.StringVar(value=self.config.get('user_name', ''))
        name_entry = tk.Entry(
            user_frame,
            textvariable=self.name_var,
            font=("Segoe UI", 10),
            width=30
        )
        name_entry.grid(row=0, column=1, sticky='w', padx=(10, 0), pady=5)
        name_entry.bind('<KeyRelease>', self.on_name_change)
        
        # Update preferences
        update_frame = tk.LabelFrame(
            settings_frame,
            text="Update Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            padx=10,
            pady=10
        )
        update_frame.pack(fill='x', pady=5)
        
        self.auto_update_var = tk.BooleanVar(value=self.config.get('check_updates_on_startup', True))
        auto_update_cb = tk.Checkbutton(
            update_frame,
            text="Check for updates on startup",
            variable=self.auto_update_var,
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            activebackground=self.colors['bg'],
            command=self.on_auto_update_change
        )
        auto_update_cb.pack(anchor='w', pady=5)
        
        # Editor preferences
        editor_frame = tk.LabelFrame(
            settings_frame,
            text="Editor Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            padx=10,
            pady=10
        )
        editor_frame.pack(fill='x', pady=5)
        
        self.auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', True))
        auto_save_cb = tk.Checkbutton(
            editor_frame,
            text="Auto-save changes",
            variable=self.auto_save_var,
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['dark'],
            activebackground=self.colors['bg'],
            command=self.on_auto_save_change
        )
        auto_save_cb.pack(anchor='w', pady=5)
        
        # Update settings scroll region
        settings_frame.update_idletasks()
        settings_scroll.configure(scrollregion=settings_scroll.bbox("all"))
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = tk.Frame(self.root, bg=self.colors['dark'], height=25)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.colors['dark'],
            fg='white',
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10, pady=2)
        
        # Last update check
        last_check = self.config.get('last_update_check', '')
        if last_check:
            self.update_status_label = tk.Label(
                self.status_frame,
                text=f"Last update check: {last_check}",
                font=("Segoe UI", 9),
                bg=self.colors['dark'],
                fg='white',
                anchor='e'
            )
            self.update_status_label.pack(side='right', padx=10, pady=2)
    
    def set_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def show_progress(self, message):
        """Show progress indicator"""
        self.progress_label.config(text=message)
        self.progress_frame.pack(fill='x', pady=(0, 5))
        self.progress_label.pack()
        self.progress_bar.pack(pady=(5, 0))
        self.progress_bar.start(10)
        self.root.update_idletasks()
    
    def hide_progress(self):
        """Hide progress indicator"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
    
    def on_name_change(self, event=None):
        """Handle name change"""
        self.config['user_name'] = self.name_var.get()
        self.save_config()
    
    def on_auto_update_change(self):
        """Handle auto-update setting change"""
        self.config['check_updates_on_startup'] = self.auto_update_var.get()
        self.save_config()
    
    def on_auto_save_change(self):
        """Handle auto-save setting change"""
        self.config['auto_save'] = self.auto_save_var.get()
        self.save_config()
    
    def on_text_change(self, event=None):
        """Handle text editor changes"""
        self.unsaved_changes = True
        if self.config.get('auto_save', True) and self.current_file:
            self.root.after(2000, self.auto_save)  # Auto-save after 2 seconds
    
    def auto_save(self):
        """Auto-save current file"""
        if self.unsaved_changes and self.current_file and self.config.get('auto_save', True):
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.get(1.0, tk.END))
                self.unsaved_changes = False
                self.set_status(f"Auto-saved: {os.path.basename(self.current_file)}")
            except Exception as e:
                self.set_status(f"Auto-save failed: {str(e)}")
    
    def new_file(self):
        """Create new file"""
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Continue?"):
                return
        
        self.text_editor.delete(1.0, tk.END)
        self.current_file = None
        self.unsaved_changes = False
        self.set_status("New file created")
    
    def open_file(self):
        """Open file"""
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Continue?"):
                return
        
        file_path = filedialog.askopenfilename(
            title="Open File",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(1.0, content)
                self.current_file = file_path
                self.unsaved_changes = False
                self.set_status(f"Opened: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{str(e)}")
    
    def save_file(self):
        """Save file"""
        if not self.current_file:
            self.save_file_as()
        else:
            try:
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.get(1.0, tk.END))
                self.unsaved_changes = False
                self.set_status(f"Saved: {os.path.basename(self.current_file)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{str(e)}")
    
    def save_file_as(self):
        """Save file as"""
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.get(1.0, tk.END))
                self.current_file = file_path
                self.unsaved_changes = False
                self.set_status(f"Saved as: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{str(e)}")
    
    def show_preferences(self):
        """Show preferences (switch to settings tab)"""
        self.notebook.select(2)  # Select settings tab
    
    def open_github(self):
        """Open GitHub repository"""
        github_url = VERSION_URL.replace("/raw.githubusercontent.com/", "/github.com/").replace("/main/version.json", "")
        webbrowser.open(github_url)
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""{APP_NAME}
Version {CURRENT_VERSION}

A modern Python application with:
• Beautiful, intuitive interface
• Automatic update functionality  
• Built-in text editor
• Customizable settings
• Professional design

Built with Python & Tkinter
© 2024 Your Name"""
        
        messagebox.showinfo("About", about_text)
    
    def check_for_updates_silent(self):
        """Check for updates silently (no loading indicator)"""
        threading.Thread(target=self._check_updates, args=(True,), daemon=True).start()
    
    def check_for_updates_threaded(self):
        """Check for updates in background thread"""
        threading.Thread(target=self._check_updates, args=(False,), daemon=True).start()
    
    def _check_updates(self, silent=False):
        """Check for updates (runs in background thread)"""
        if not silent:
            self.root.after(0, lambda: self.show_progress("Checking for updates..."))
            self.root.after(0, lambda: self.update_btn.config(state='disabled'))
        
        try:
            self.root.after(0, lambda: self.set_status("Checking for updates..."))
            
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            
            version_info = response.json()
            latest_version = version_info.get("version", "")
            download_url = version_info.get("installer_url", "")
            release_notes = version_info.get("release_notes", "")
            
            # Update last check time
            self.config['last_update_check'] = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.save_config()
            
            if self._is_newer_version(latest_version, CURRENT_VERSION):
                self.root.after(0, lambda: self._show_update_dialog(latest_version, download_url, release_notes))
            else:
                if not silent:
                    self.root.after(0, lambda: messagebox.showinfo(
                        "No Updates", 
                        f"You're running the latest version ({CURRENT_VERSION})! 🎉"
                    ))
                self.root.after(0, lambda: self.set_status("Up to date"))
        
        except requests.exceptions.RequestException as e:
            error_msg = "Could not check for updates. Please check your internet connection."
            if not silent:
                self.root.after(0, lambda: messagebox.showerror("Update Check Failed", error_msg))
            self.root.after(0, lambda: self.set_status("Update check failed"))
        
        except Exception as e:
            error_msg = f"Update check failed: {str(e)}"
            if not silent:
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.root.after(0, lambda: self.set_status("Update check failed"))
        
        finally:
            if not silent:
                self.root.after(0, self.hide_progress)
                self.root.after(0, lambda: self.update_btn.config(state='normal'))
    
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
    
    def _show_update_dialog(self, latest_version, download_url, release_notes):
        """Show update available dialog"""
        self.hide_progress()
        self.set_status(f"Update available: v{latest_version}")
        
        update_window = tk.Toplevel(self.root)
        update_window.title("Update Available")
        update_window.geometry("500x400")
        update_window.resizable(False, False)
        update_window.configure(bg=self.colors['bg'])
        update_window.transient(self.root)
        update_window.grab_set()
        
        # Center the window
        update_window.update_idletasks()
        x = (update_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (update_window.winfo_screenheight() // 2) - (400 // 2)
        update_window.geometry(f"500x400+{x}+{y}")
        
        # Update icon and title
        title_frame = tk.Frame(update_window, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            title_frame,
            text="🚀 Update Available!",
            font=("Segoe UI", 16, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['success']
        ).pack()
        
        tk.Label(
            title_frame,
            text=f"Version {latest_version} is now available",
            font=("Segoe UI", 12),
            bg=self.colors['bg'],
            fg=self.colors['dark']
        ).pack(pady=(5, 0))
        
        tk.Label(
            title_frame,
            text=f"Current version: {CURRENT_VERSION}",
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        ).pack()
        
        # Release notes
        notes_frame = tk.LabelFrame(
            update_window,
            text="What's New",
            font=("Segoe UI", 11, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['dark']
        )
        notes_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        notes_text = scrolledtext.ScrolledText(
            notes_frame,
            wrap=tk.WORD,
            height=8,
            font=("Segoe UI", 10),
            bg=self.colors['light'],
            fg=self.colors['dark']
        )
        notes_text.pack(fill='both', expand=True, padx=10, pady=10)
        notes_text.insert(1.0, release_notes)
        notes_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(update_window, bg=self.colors['bg'])
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        update_btn = tk.Button(
            button_frame,
            text="📥 Download & Install",
            command=lambda: self._download_update(download_url, update_window),
            bg=self.colors['success'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        update_btn.pack(side='right', padx=(10, 0))
        
        later_btn = tk.Button(
            button_frame,
            text="⏰ Later",
            command=update_window.destroy,
            bg=self.colors['light'],
            fg=self.colors['dark'],
            font=("Segoe UI", 11),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        )
        later_btn.pack(side='right')
    
    def _download_update(self, download_url, parent_window):
        """Download and install update"""
        parent_window.destroy()
        
        # Create download dialog
        download_window = tk.Toplevel(self.root)
        download_window.title("Downloading Update")
        download_window.geometry("400x200")
        download_window.resizable(False, False)
        download_window.configure(bg=self.colors['bg'])
        download_window.transient(self.root)
        download_window.grab_set()
        
        # Center the window
        download_window.update_idletasks()
        x = (download_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (download_window.winfo_screenheight() // 2) - (200 // 2)
        download_window.geometry(f"400x200+{x}+{y}")
        
        # Download UI
        tk.Label(
            download_window,
            text="📥 Downloading Update...",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        ).pack(pady=20)
        
        progress = ttk.Progressbar(
            download_window,
            mode='indeterminate',
            length=300
        )
        progress.pack(pady=10)
        progress.start(10)
        
        status_label = tk.Label(
            download_window,
            text="Preparing download...",
            font=("Segoe UI", 10),
            bg=self.colors['bg'],
            fg=self.colors['dark']
        )
        status_label.pack(pady=10)
        
        # Start download in background
        def download_thread():
            try:
                status_label.config(text="Downloading installer...")
                download_window.update()
                
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Save to temp directory
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, "MyApp_Setup.exe")
                
                with open(installer_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                status_label.config(text="Download complete! Starting installer...")
                download_window.update()
                
                # Start installer
                subprocess.Popen([installer_path])
                
                # Close application
                self.root.after(1000, self.root.quit)
                
            except Exception as e:
                progress.stop()
                status_label.config(text=f"Download failed: {str(e)}")
                tk.Button(
                    download_window,
                    text="Close",
                    command=download_window.destroy,
                    bg=self.colors['danger'],
                    fg='white',
                    font=("Segoe UI", 10),
                    padx=20,
                    pady=5,
                    relief='flat'
                ).pack(pady=10)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def on_closing(self):
        """Handle application closing"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            if result is True:  # Yes - save
                self.save_file()
            elif result is None:  # Cancel
                return
        
        self.save_config()
        self.root.quit()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = ModernApp()
        app.run()
    except Exception as e:
        # Show error dialog if GUI fails
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Application Error",
            f"An error occurred while starting the application:\n\n{str(e)}"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()

