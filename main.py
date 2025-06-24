#!/usr/bin/env python3
"""
Advanced Text & PDF Editor - Advanced Text Editor & PDF Viewer
Version 1.1.0

A modern, feature-rich text editor and PDF viewer built with Python and Tkinter.
Features: Advanced text editing, PDF viewing, auto-save, themes, and more.

Author: PixelHeaven
License: MIT
"""

import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext
import subprocess
import sys
import os
import json
import threading
from pathlib import Path
import webbrowser
from datetime import datetime
import tempfile
import time
import re
from collections import deque

# Application Configuration
CURRENT_VERSION = "1.1.0"
VERSION_URL = "https://raw.githubusercontent.com/PixelHeaven/software1/main/version.json"
APP_NAME = "Advanced Text & PDF Editor"
CONFIG_FILE = "config.json"
BACKUP_DIR = "backups"

# Safe import functions for optional dependencies
def safe_import(module_name, package_name=None):
    """Safely import a module with fallback handling"""
    try:
        if package_name:
            exec(f"import {module_name}")
            return sys.modules[module_name]
        else:
            __import__(module_name)
            return sys.modules[module_name]
    except ImportError:
        return None

# Optional dependencies with safe imports
requests = safe_import('requests')
HAS_REQUESTS = requests is not None

# PDF support
try:
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    fitz = None
    HAS_PDF_SUPPORT = False

# PDF export support
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    HAS_PDF_EXPORT = True
except ImportError:
    canvas = None
    letter = None
    inch = None
    HAS_PDF_EXPORT = False

class Logger:
    """Simple logging system for debugging"""
    def __init__(self):
        self.logs = deque(maxlen=1000)
    
    def log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}"
        self.logs.append(log_entry)
        print(log_entry)
    
    def info(self, message):
        self.log("INFO", message)
    
    def error(self, message):
        self.log("ERROR", message)
    
    def warning(self, message):
        self.log("WARNING", message)

logger = Logger()

class ThemeManager:
    """Advanced theme management system"""
    
    def __init__(self):
        self.themes = {
            'dark': {
                'name': 'Dark Professional',
                'bg': '#2b2b2b',
                'fg': '#ffffff',
                'select_bg': '#404040',
                'select_fg': '#ffffff',
                'primary': '#0078d4',
                'secondary': '#ffc107',
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#fd7e14',
                'info': '#17a2b8',
                'editor_bg': '#1e1e1e',
                'editor_fg': '#d4d4d4',
                'sidebar_bg': '#252526',
                'tab_bg': '#2d2d30',
                'accent': '#007acc',
                'border': '#3e3e42'
            },
            'light': {
                'name': 'Light Professional',
                'bg': '#f8f9fa',
                'fg': '#212529',
                'select_bg': '#e3f2fd',
                'select_fg': '#1565c0',
                'primary': '#2196f3',
                'secondary': '#ff9800',
                'success': '#4caf50',
                'danger': '#f44336',
                'warning': '#ff5722',
                'info': '#00bcd4',
                'editor_bg': '#ffffff',
                'editor_fg': '#000000',
                'sidebar_bg': '#f5f5f5',
                'tab_bg': '#e0e0e0',
                'accent': '#1976d2',
                'border': '#dee2e6'
            },
            'high_contrast': {
                'name': 'High Contrast',
                'bg': '#000000',
                'fg': '#ffffff',
                'select_bg': '#ffffff',
                'select_fg': '#000000',
                'primary': '#ffff00',
                'secondary': '#00ffff',
                'success': '#00ff00',
                'danger': '#ff0000',
                'warning': '#ff8800',
                'info': '#0088ff',
                'editor_bg': '#000000',
                'editor_fg': '#ffffff',
                'sidebar_bg': '#333333',
                'tab_bg': '#444444',
                'accent': '#ffffff',
                'border': '#ffffff'
            }
        }
        self.current_theme = 'dark'
        logger.info("ThemeManager initialized")
    
    def get_colors(self):
        """Get current theme colors"""
        return self.themes[self.current_theme]
    
    def get_theme_names(self):
        """Get list of available theme names"""
        return [theme['name'] for theme in self.themes.values()]
    
    def switch_theme(self, theme_name):
        """Switch to a different theme"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            logger.info(f"Theme switched to: {theme_name}")
        else:
            logger.warning(f"Theme not found: {theme_name}")

class SyntaxHighlighter:
    """Advanced syntax highlighting system"""
    
    def __init__(self, text_widget, theme_manager):
        self.text_widget = text_widget
        self.theme = theme_manager
        self.current_language = 'text'
        self.setup_tags()
        
    def setup_tags(self):
        """Setup syntax highlighting tags"""
        colors = self.theme.get_colors()
        
        # Configure tags for different syntax elements
        self.text_widget.tag_configure('keyword', foreground='#569cd6', font=('Consolas', 11, 'bold'))
        self.text_widget.tag_configure('string', foreground='#ce9178')
        self.text_widget.tag_configure('comment', foreground='#6a9955', font=('Consolas', 11, 'italic'))
        self.text_widget.tag_configure('number', foreground='#b5cea8')
        self.text_widget.tag_configure('function', foreground='#dcdcaa')
        self.text_widget.tag_configure('class', foreground='#4ec9b0')
        self.text_widget.tag_configure('operator', foreground='#d4d4d4')
        self.text_widget.tag_configure('builtin', foreground='#569cd6')
        
    def set_language(self, language):
        """Set the programming language for highlighting"""
        self.current_language = language.lower()
        self.highlight_all()
        
    def highlight_all(self):
        """Apply syntax highlighting to entire document"""
        if self.current_language == 'text':
            return
            
        content = self.text_widget.get('1.0', 'end')
        
        # Clear existing tags
        for tag in ['keyword', 'string', 'comment', 'number', 'function', 'class', 'operator', 'builtin']:
            self.text_widget.tag_remove(tag, '1.0', 'end')
        
        if self.current_language == 'python':
            self._highlight_python(content)
        elif self.current_language == 'javascript':
            self._highlight_javascript(content)
        elif self.current_language == 'html':
            self._highlight_html(content)
        elif self.current_language == 'css':
            self._highlight_css(content)
            
    def _highlight_python(self, content):
        """Highlight Python syntax"""
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 
                   'finally', 'import', 'from', 'return', 'break', 'continue', 'pass',
                   'and', 'or', 'not', 'in', 'is', 'lambda', 'with', 'as', 'yield',
                   'global', 'nonlocal', 'assert', 'del', 'raise']
        
        builtins = ['print', 'len', 'str', 'int', 'float', 'list', 'dict', 'tuple',
                   'set', 'bool', 'type', 'isinstance', 'hasattr', 'getattr', 'setattr']
        
        self._highlight_patterns(content, [
            (r'\b(' + '|'.join(keywords) + r')\b', 'keyword'),
            (r'\b(' + '|'.join(builtins) + r')\b', 'builtin'),
            (r'#.*?$', 'comment'),
            (r'""".*?"""', 'string'),
            (r"'''.*?'''", 'string'),
            (r'".*?"', 'string'),
            (r"'.*?'", 'string'),
            (r'\b\d+\.?\d*\b', 'number'),
            (r'\bdef\s+(\w+)', 'function'),
            (r'\bclass\s+(\w+)', 'class'),
        ])
    
    def _highlight_javascript(self, content):
        """Highlight JavaScript syntax"""
        keywords = ['function', 'var', 'let', 'const', 'if', 'else', 'for', 'while',
                   'do', 'switch', 'case', 'default', 'break', 'continue', 'return',
                   'try', 'catch', 'finally', 'throw', 'new', 'this', 'typeof',
                   'instanceof', 'in', 'of', 'class', 'extends', 'super']
        
        self._highlight_patterns(content, [
            (r'\b(' + '|'.join(keywords) + r')\b', 'keyword'),
            (r'//.*?$', 'comment'),
            (r'/\*.*?\*/', 'comment'),
            (r'".*?"', 'string'),
            (r"'.*?'", 'string'),
            (r'`.*?`', 'string'),
            (r'\b\d+\.?\d*\b', 'number'),
            (r'\bfunction\s+(\w+)', 'function'),
        ])
    
    def _highlight_patterns(self, content, patterns):
        """Apply regex patterns for syntax highlighting"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, tag in patterns:
                matches = re.finditer(pattern, line, re.MULTILINE)
                for match in matches:
                    start = f"{line_num}.{match.start()}"
                    end = f"{line_num}.{match.end()}"
                    
                    if tag in ['function', 'class'] and match.groups():
                        # Highlight the function/class name specifically
                        start = f"{line_num}.{match.start(1)}"
                        end = f"{line_num}.{match.end(1)}"
                    
                    self.text_widget.tag_add(tag, start, end)

class AdvancedTextEditor:
    """Advanced text editor with modern features"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.search_window = None
        self.find_index = "1.0"
        self.zoom_level = 100
        
        # Create main editor frame
        self.editor_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        
        # Create the editor interface
        self.create_editor()
        self.create_toolbar()
        
        # Initialize syntax highlighter
        self.highlighter = SyntaxHighlighter(self.text_editor, self.theme)
        
        logger.info("AdvancedTextEditor initialized")
    
    def create_toolbar(self):
        """Create editor toolbar"""
        toolbar = tk.Frame(self.editor_frame, bg=self.theme.get_colors()['tab_bg'], height=45)
        toolbar.pack(fill='x', side='top')
        toolbar.pack_propagate(False)
        
        # Language selector
        tk.Label(
            toolbar,
            text="Language:",
            bg=self.theme.get_colors()['tab_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9)
        ).pack(side='left', padx=(10, 5), pady=12)
        
        self.language_var = tk.StringVar(value='text')
        language_combo = ttk.Combobox(
            toolbar,
            textvariable=self.language_var,
            values=['text', 'python', 'javascript', 'html', 'css', 'json', 'xml'],
            width=12,
            state='readonly'
        )
        language_combo.pack(side='left', padx=(0, 10), pady=12)
        language_combo.bind('<<ComboboxSelected>>', self.on_language_change)
        
        # Zoom controls
        tk.Label(
            toolbar,
            text="Zoom:",
            bg=self.theme.get_colors()['tab_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9)
        ).pack(side='left', padx=(10, 5), pady=12)
        
        zoom_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['tab_bg'])
        zoom_frame.pack(side='left', pady=12)
        
        tk.Button(
            zoom_frame,
            text="-",
            command=self.zoom_out,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9, 'bold'),
            width=2,
            relief='flat'
        ).pack(side='left')
        
        self.zoom_label = tk.Label(
            zoom_frame,
            text="100%",
            bg=self.theme.get_colors()['tab_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            width=6
        )
        self.zoom_label.pack(side='left', padx=5)
        
        tk.Button(
            zoom_frame,
            text="+",
            command=self.zoom_in,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9, 'bold'),
            width=2,
            relief='flat'
        ).pack(side='left')
        
        # Word wrap toggle
        self.wrap_var = tk.BooleanVar(value=False)
        wrap_cb = tk.Checkbutton(
            toolbar,
            text="Word Wrap",
            variable=self.wrap_var,
            command=self.toggle_word_wrap,
            bg=self.theme.get_colors()['tab_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            activebackground=self.theme.get_colors()['tab_bg']
        )
        wrap_cb.pack(side='right', padx=10, pady=12)
    
    def create_editor(self):
        """Create the main text editor interface"""
        # Main editor container
        editor_container = tk.Frame(self.editor_frame, bg=self.theme.get_colors()['bg'])
        editor_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Line numbers frame
        line_frame = tk.Frame(editor_container, bg=self.theme.get_colors()['sidebar_bg'], width=60)
        line_frame.pack(side='left', fill='y')
        line_frame.pack_propagate(False)
        
        # Line numbers text widget
        self.line_numbers = tk.Text(
            line_frame,
            width=5,
            padx=8,
            pady=5,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            font=('Consolas', 11),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            cursor='arrow'
        )
        self.line_numbers.pack(fill='both', expand=True)
        
        # Main text editor
        self.text_editor = tk.Text(
            editor_container,
            wrap='none',
            font=('Consolas', 11),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg'],
            insertbackground=self.theme.get_colors()['primary'],
            selectbackground=self.theme.get_colors()['primary'],
            selectforeground='white',
            undo=True,
            maxundo=100,
            padx=10,
            pady=5,
            spacing1=2,
            spacing3=2
        )
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(editor_container, orient='vertical', command=self.sync_scroll)
        h_scrollbar = tk.Scrollbar(editor_container, orient='horizontal', command=self.text_editor.xview)
        
        # Configure scrollbars
        self.text_editor.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack elements
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.text_editor.pack(fill='both', expand=True)
        
        # Bind events
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.text_editor.bind('<Button-1>', self.on_text_change)
        self.text_editor.bind('<MouseWheel>', self.on_mousewheel)
        self.text_editor.bind('<Control-f>', lambda e: self.show_find_replace())
        self.text_editor.bind('<Control-h>', lambda e: self.show_find_replace())
        self.text_editor.bind('<F3>', lambda e: self.find_next())
        
        # Context menu
        self.create_context_menu()
        
        # Initial line numbers update
        self.update_line_numbers()
    
    def create_context_menu(self):
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self.text_editor, tearoff=0)
        self.context_menu.add_command(label="Undo", command=self.undo)
        self.context_menu.add_command(label="Redo", command=self.redo)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", command=self.cut)
        self.context_menu.add_command(label="Copy", command=self.copy)
        self.context_menu.add_command(label="Paste", command=self.paste)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all)
        self.context_menu.add_command(label="Find & Replace", command=self.show_find_replace)
        
        self.text_editor.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def sync_scroll(self, *args):
        """Synchronize scrolling between text editor and line numbers"""
        self.text_editor.yview(*args)
        self.line_numbers.yview(*args)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if event.state & 0x4:  # Ctrl key pressed
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Normal scrolling
            self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_text_change(self, event=None):
        """Handle text changes"""
        self.update_line_numbers()
        
        # Apply syntax highlighting with delay to avoid performance issues
        if hasattr(self, 'highlight_timer'):
            self.text_editor.after_cancel(self.highlight_timer)
        self.highlight_timer = self.text_editor.after(500, self.highlighter.highlight_all)
        
        # Notify parent of changes
        if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'on_text_change'):
            self.parent.master.on_text_change()
    
    def update_line_numbers(self):
        """Update line numbers display"""
        try:
            line_count = int(self.text_editor.index('end-1c').split('.')[0])
            line_numbers_content = '\n'.join(str(i) for i in range(1, line_count + 1))
            
            self.line_numbers.config(state='normal')
            self.line_numbers.delete('1.0', 'end')
            self.line_numbers.insert('1.0', line_numbers_content)
            self.line_numbers.config(state='disabled')
        except Exception as e:
            logger.error(f"Error updating line numbers: {e}")
    
    def on_language_change(self, event=None):
        """Handle language selection change"""
        language = self.language_var.get()
        self.highlighter.set_language(language)
        logger.info(f"Language changed to: {language}")
    
    def zoom_in(self):
        """Increase font size"""
        if self.zoom_level < 200:
            self.zoom_level += 10
            self.apply_zoom()
    
    def zoom_out(self):
        """Decrease font size"""
        if self.zoom_level > 50:
            self.zoom_level -= 10
            self.apply_zoom()
    
    def apply_zoom(self):
        """Apply current zoom level"""
        base_size = 11
        new_size = int(base_size * (self.zoom_level / 100))
        
        font_family = self.text_editor.cget('font').split()[0] if isinstance(self.text_editor.cget('font'), str) else 'Consolas'
        new_font = (font_family, new_size)
        
        self.text_editor.configure(font=new_font)
        self.line_numbers.configure(font=new_font)
        self.zoom_label.config(text=f"{self.zoom_level}%")
        
        # Update syntax highlighting tags
        self.highlighter.setup_tags()
    
    def toggle_word_wrap(self):
        """Toggle word wrap mode"""
        if self.wrap_var.get():
            self.text_editor.configure(wrap='word')
        else:
            self.text_editor.configure(wrap='none')
    
    def show_find_replace(self):
        """Show find and replace dialog"""
        if self.search_window and self.search_window.winfo_exists():
            self.search_window.lift()
            self.search_window.focus()
            return
        
        self.search_window = tk.Toplevel(self.parent)
        self.search_window.title("Find & Replace")
        self.search_window.geometry("450x250")
        self.search_window.resizable(False, False)
        self.search_window.configure(bg=self.theme.get_colors()['bg'])
        self.search_window.transient(self.parent)
        
        # Center the window
        self.search_window.update_idletasks()
        x = (self.search_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.search_window.winfo_screenheight() // 2) - (250 // 2)
        self.search_window.geometry(f"450x250+{x}+{y}")
        
        # Find section
        find_frame = tk.LabelFrame(
            self.search_window,
            text="Find",
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 10, 'bold')
        )
        find_frame.pack(fill='x', padx=15, pady=10)
        
        self.find_entry = tk.Entry(
            find_frame,
            width=40,
            font=('Segoe UI', 11),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        )
        self.find_entry.pack(padx=10, pady=10)
        self.find_entry.bind('<Return>', lambda e: self.find_next())
        
        # Replace section
        replace_frame = tk.LabelFrame(
            self.search_window,
            text="Replace",
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 10, 'bold')
        )
        replace_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.replace_entry = tk.Entry(
            replace_frame,
            width=40,
            font=('Segoe UI', 11),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        )
        self.replace_entry.pack(padx=10, pady=10)
        self.replace_entry.bind('<Return>', lambda e: self.replace_current())
        
        # Options
        options_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        options_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.case_sensitive_var = tk.BooleanVar()
        case_cb = tk.Checkbutton(
            options_frame,
            text="Case sensitive",
            variable=self.case_sensitive_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9)
        )
        case_cb.pack(side='left')
        
        # Buttons
        button_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        buttons = [
            ("Find Next", self.find_next, self.theme.get_colors()['primary']),
            ("Find All", self.find_all, self.theme.get_colors()['info']),
            ("Replace", self.replace_current, self.theme.get_colors()['warning']),
            ("Replace All", self.replace_all, self.theme.get_colors()['success'])
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=('Segoe UI', 9, 'bold'),
                padx=15,
                pady=5,
                relief='flat'
            )
            btn.pack(side='left', padx=2)
        
        # Close button
        tk.Button(
            button_frame,
            text="Close",
            command=self.close_search,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            padx=15,
            pady=5,
            relief='flat'
        ).pack(side='right')
        
        self.search_window.protocol("WM_DELETE_WINDOW", self.close_search)
        self.find_entry.focus()
    
    def find_next(self):
        """Find next occurrence"""
        search_term = self.find_entry.get() if hasattr(self, 'find_entry') else ""
        if not search_term:
            return
        
        # Get search options
        case_sensitive = getattr(self, 'case_sensitive_var', tk.BooleanVar()).get()
        
        # Start search from current cursor position
        start_pos = self.text_editor.index(tk.INSERT)
        
        # Perform search
        if case_sensitive:
            pos = self.text_editor.search(search_term, start_pos, 'end')
        else:
            pos = self.text_editor.search(search_term, start_pos, 'end', nocase=True)
        
                # If not found from cursor, search from beginning
        if not pos:
            if case_sensitive:
                pos = self.text_editor.search(search_term, '1.0', start_pos)
            else:
                pos = self.text_editor.search(search_term, '1.0', start_pos, nocase=True)
        
        if pos:
            # Select found text
            end_pos = f"{pos}+{len(search_term)}c"
            self.text_editor.tag_remove(tk.SEL, '1.0', 'end')
            self.text_editor.tag_add(tk.SEL, pos, end_pos)
            self.text_editor.mark_set(tk.INSERT, end_pos)
            self.text_editor.see(pos)
            self.find_index = end_pos
        else:
            messagebox.showinfo("Find", f"'{search_term}' not found.")
    
    def find_all(self):
        """Find and highlight all occurrences"""
        search_term = self.find_entry.get() if hasattr(self, 'find_entry') else ""
        if not search_term:
            return
        
        # Clear previous highlights
        self.text_editor.tag_remove('find_highlight', '1.0', 'end')
        
        # Configure highlight tag
        self.text_editor.tag_configure('find_highlight', 
                                     background=self.theme.get_colors()['warning'],
                                     foreground='black')
        
        case_sensitive = getattr(self, 'case_sensitive_var', tk.BooleanVar()).get()
        count = 0
        start = '1.0'
        
        while True:
            if case_sensitive:
                pos = self.text_editor.search(search_term, start, 'end')
            else:
                pos = self.text_editor.search(search_term, start, 'end', nocase=True)
            
            if not pos:
                break
                
            end_pos = f"{pos}+{len(search_term)}c"
            self.text_editor.tag_add('find_highlight', pos, end_pos)
            count += 1
            start = end_pos
        
        if count > 0:
            messagebox.showinfo("Find All", f"Found {count} occurrence(s) of '{search_term}'.")
        else:
            messagebox.showinfo("Find All", f"'{search_term}' not found.")
    
    def replace_current(self):
        """Replace currently selected text"""
        try:
            if self.text_editor.tag_ranges(tk.SEL):
                replace_text = self.replace_entry.get() if hasattr(self, 'replace_entry') else ""
                self.text_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.insert(tk.INSERT, replace_text)
        except tk.TclError:
            messagebox.showwarning("Replace", "No text selected to replace.")
    
    def replace_all(self):
        """Replace all occurrences"""
        search_term = self.find_entry.get() if hasattr(self, 'find_entry') else ""
        replace_term = self.replace_entry.get() if hasattr(self, 'replace_entry') else ""
        
        if not search_term:
            return
        
        content = self.text_editor.get('1.0', 'end-1c')
        case_sensitive = getattr(self, 'case_sensitive_var', tk.BooleanVar()).get()
        
        if case_sensitive:
            new_content = content.replace(search_term, replace_term)
            count = content.count(search_term)
        else:
            # Case insensitive replacement
            import re
            pattern = re.compile(re.escape(search_term), re.IGNORECASE)
            new_content = pattern.sub(replace_term, content)
            count = len(pattern.findall(content))
        
        if count > 0:
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert('1.0', new_content)
            messagebox.showinfo("Replace All", f"Replaced {count} occurrence(s).")
        else:
            messagebox.showinfo("Replace All", f"'{search_term}' not found.")
    
    def close_search(self):
        """Close search dialog"""
        # Clear highlights
        self.text_editor.tag_remove('find_highlight', '1.0', 'end')
        if self.search_window and self.search_window.winfo_exists():
            self.search_window.destroy()
        self.search_window = None
    
    # Text operations
    def undo(self):
        """Undo last action"""
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
    
    def redo(self):
        """Redo last undone action"""
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
    
    def cut(self):
        """Cut selected text"""
        self.text_editor.event_generate("<<Cut>>")
    
    def copy(self):
        """Copy selected text"""
        self.text_editor.event_generate("<<Copy>>")
    
    def paste(self):
        """Paste text from clipboard"""
        self.text_editor.event_generate("<<Paste>>")
    
    def select_all(self):
        """Select all text"""
        self.text_editor.tag_add(tk.SEL, "1.0", tk.END)
        self.text_editor.mark_set(tk.INSERT, "1.0")
        self.text_editor.see(tk.INSERT)
    
    def insert_text(self, text):
        """Insert text at current cursor position"""
        self.text_editor.insert(tk.INSERT, text)
    
    def get_text(self):
        """Get all text from editor"""
        return self.text_editor.get('1.0', 'end-1c')
    
    def set_text(self, text):
        """Set text in editor"""
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert('1.0', text)
    
    def clear_text(self):
        """Clear all text"""
        self.text_editor.delete('1.0', 'end')
    
    def get_frame(self):
        """Get the main editor frame"""
        return self.editor_frame

class PDFViewer:
    """Advanced PDF viewer with zoom and navigation"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.current_pdf = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.rotation = 0
        
        if HAS_PDF_SUPPORT:
            self.create_pdf_viewer()
        else:
            self.create_placeholder()
        
        logger.info("PDFViewer initialized")
    
    def create_pdf_viewer(self):
        """Create PDF viewer interface"""
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        # Toolbar
        self.create_toolbar()
        
        # PDF display area with scrollbars
        display_frame = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['bg'])
        display_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Canvas for PDF display
        self.pdf_canvas = tk.Canvas(
            display_frame,
            bg='white',
            highlightthickness=1,
            highlightbackground=self.theme.get_colors()['border']
        )
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(display_frame, orient='vertical', command=self.pdf_canvas.yview)
        h_scrollbar = tk.Scrollbar(display_frame, orient='horizontal', command=self.pdf_canvas.xview)
        
        self.pdf_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.pdf_canvas.pack(fill='both', expand=True)
        
        # Bind mouse events
        self.pdf_canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.pdf_canvas.bind('<Button-1>', lambda e: self.pdf_canvas.focus_set())
    
    def create_toolbar(self):
        """Create PDF viewer toolbar"""
        toolbar = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['sidebar_bg'], height=60)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # File operations
        file_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        file_frame.pack(side='left', padx=10, pady=10)
        
        tk.Button(
            file_frame,
            text="📂 Open PDF",
            command=self.open_pdf,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            padx=15,
            pady=8,
            relief='flat'
        ).pack(side='left', padx=2)
        
        # Navigation
        nav_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        nav_frame.pack(side='left', padx=20, pady=10)
        
        tk.Button(
            nav_frame,
            text="⬅ Previous",
            command=self.prev_page,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        tk.Button(
            nav_frame,
            text="Next ➡",
            command=self.next_page,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            padx=10,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        # Page info
        self.page_label = tk.Label(
            nav_frame,
            text="No PDF loaded",
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 10, 'bold')
        )
        self.page_label.pack(side='left', padx=15)
        
        # Zoom controls
        zoom_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        zoom_frame.pack(side='right', padx=10, pady=10)
        
        tk.Button(
            zoom_frame,
            text="🔍-",
            command=self.zoom_out,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            width=4,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        self.zoom_display = tk.Label(
            zoom_frame,
            text="100%",
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            width=6
        )
        self.zoom_display.pack(side='left', padx=5)
        
        tk.Button(
            zoom_frame,
            text="🔍+",
            command=self.zoom_in,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=('Segoe UI', 9),
            width=4,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        # Rotation button
        tk.Button(
            zoom_frame,
            text="🔄",
            command=self.rotate_page,
            bg=self.theme.get_colors()['info'],
            fg='white',
            font=('Segoe UI', 9),
            width=4,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=(10, 2))
    
    def create_placeholder(self):
        """Create placeholder when PDF support is not available"""
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        # Center container
        center_frame = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['bg'])
        center_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Icon
        tk.Label(
            center_frame,
            text="📄",
            font=("Segoe UI", 48),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
        ).pack(pady=20)
        
        # Title
        tk.Label(
            center_frame,
            text="PDF Viewer Not Available",
            font=("Segoe UI", 18, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=10)
        
        # Instructions
        tk.Label(
            center_frame,
            text="To enable PDF viewing, please install PyMuPDF:",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=5)
        
        # Command
        command_frame = tk.Frame(center_frame, bg=self.theme.get_colors()['editor_bg'], relief='solid', bd=1)
        command_frame.pack(pady=10, padx=20)
        
        tk.Label(
            command_frame,
            text="pip install PyMuPDF",
            font=("Consolas", 12, "bold"),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['success'],
            padx=15,
            pady=8
        ).pack()
        
                # Install button
        tk.Button(
            center_frame,
            text="📥 Install PyMuPDF",
            command=self.install_pymupdf,
            bg=self.theme.get_colors()['success'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat',
            cursor='hand2'
        ).pack(pady=15)
    
    def install_pymupdf(self):
        """Install PyMuPDF package"""
        def install_thread():
            try:
                import subprocess
                result = subprocess.run([sys.executable, "-m", "pip", "install", "PyMuPDF"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    messagebox.showinfo("Success", "PyMuPDF installed successfully!\nPlease restart the application.")
                else:
                    messagebox.showerror("Error", f"Installation failed:\n{result.stderr}")
            except Exception as e:
                messagebox.showerror("Error", f"Installation failed:\n{str(e)}")
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def open_pdf(self):
        """Open PDF file"""
        if not HAS_PDF_SUPPORT:
            messagebox.showerror("Error", "PDF support not available. Install PyMuPDF first.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Open PDF File",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.current_pdf = fitz.open(file_path)
                self.current_page = 0
                self.zoom_level = 1.0
                self.rotation = 0
                self.display_page()
                logger.info(f"PDF opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF file:\n{str(e)}")
                logger.error(f"Error opening PDF: {e}")
    
    def display_page(self):
        """Display current PDF page"""
        if not self.current_pdf or not HAS_PDF_SUPPORT:
            return
        
        try:
            page = self.current_pdf[self.current_page]
            
            # Apply transformations
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            if self.rotation != 0:
                mat = mat * fitz.Matrix(self.rotation)
            
            # Render page
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # Update canvas
            self.pdf_canvas.delete("all")
            self.pdf_image = tk.PhotoImage(data=img_data)
            
            # Center the image
            canvas_width = self.pdf_canvas.winfo_width()
            canvas_height = self.pdf_canvas.winfo_height()
            img_width = self.pdf_image.width()
            img_height = self.pdf_image.height()
            
            x = max(0, (canvas_width - img_width) // 2)
            y = max(0, (canvas_height - img_height) // 2)
            
            self.pdf_canvas.create_image(x, y, anchor='nw', image=self.pdf_image)
            self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))
            
            # Update page info
            self.page_label.config(text=f"Page {self.current_page + 1} of {len(self.current_pdf)}")
            self.zoom_display.config(text=f"{int(self.zoom_level * 100)}%")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not display page:\n{str(e)}")
            logger.error(f"Error displaying page: {e}")
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_pdf and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        """Go to next page"""
        if self.current_pdf and self.current_page < len(self.current_pdf) - 1:
            self.current_page += 1
            self.display_page()
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 3.0:
            self.zoom_level *= 1.2
            self.display_page()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.2:
            self.zoom_level /= 1.2
            self.display_page()
    
    def rotate_page(self):
        """Rotate page 90 degrees clockwise"""
        self.rotation += 90
        if self.rotation >= 360:
            self.rotation = 0
        self.display_page()
    
    def on_mouse_wheel(self, event):
        """Handle mouse wheel events"""
        if event.state & 0x4:  # Ctrl key pressed
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            # Normal scrolling
            self.pdf_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def get_frame(self):
        """Get the main PDF frame"""
        return self.pdf_frame

class ConfigManager:
    """Advanced configuration management"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()
        logger.info("ConfigManager initialized")
    
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'version': CURRENT_VERSION,
            'theme': 'dark',
            'window_geometry': '1200x800',
            'window_state': 'normal',
            'window_maximized': False,
            'editor_font_family': 'Consolas',
            'editor_font_size': 11,
            'editor_zoom': 100,
            'editor_word_wrap': False,
            'editor_syntax_highlighting': True,
            'auto_save': True,
            'auto_save_interval': 30,
            'create_backups': True,
            'check_updates_on_startup': True,
            'last_update_check': '',
            'recent_files': [],
            'max_recent_files': 10,
            'user_name': '',
            'user_email': '',
            'pdf_zoom_level': 1.0,
            'pdf_rotation': 0,
            'show_line_numbers': True,
            'show_status_bar': True,
            'show_toolbar': True,
            'language_preferences': {},
            'custom_shortcuts': {}
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create backup of existing config
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                import shutil
                shutil.copy2(self.config_file, backup_file)
            
            # Save new config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Configuration saved")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update(updates)

class FileManager:
    """Advanced file management with backup and recovery"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.current_file = None
        self.unsaved_changes = False
        self.auto_save_timer = None
        
        # Create backup directory
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        logger.info("FileManager initialized")
    
    def new_file(self):
        """Create new file"""
        if self.unsaved_changes:
            if not self.ask_save_changes():
                return False
        
        self.current_file = None
        self.unsaved_changes = False
        self.stop_auto_save()
        return True
    
    def open_file(self, file_path=None):
        """Open file"""
        if self.unsaved_changes:
            if not self.ask_save_changes():
                return None
        
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Open File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("JavaScript files", "*.js"),
                    ("HTML files", "*.html"),
                    ("CSS files", "*.css"),
                    ("JSON files", "*.json"),
                    ("XML files", "*.xml"),
                    ("Markdown files", "*.md"),
                    ("All files", "*.*")
                ]
            )
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                self.current_file = file_path
                self.unsaved_changes = False
                self.add_to_recent_files(file_path)
                self.start_auto_save()
                
                logger.info(f"File opened: {file_path}")
                return content
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{str(e)}")
                logger.error(f"Error opening file: {e}")
        
        return None
    
    def save_file(self, content, file_path=None):
        """Save file"""
        if not file_path:
            file_path = self.current_file
        
        if not file_path:
            return self.save_file_as(content)
        
        try:
            # Create backup if enabled
            if self.config.get('create_backups', True) and os.path.exists(file_path):
                self.create_backup(file_path)
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.current_file = file_path
            self.unsaved_changes = False
            self.add_to_recent_files(file_path)
            
            logger.info(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{str(e)}")
            logger.error(f"Error saving file: {e}")
            return False
    
    def save_file_as(self, content):
        """Save file as"""
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JSON files", "*.json"),
                ("XML files", "*.xml"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            return self.save_file(content, file_path)
        
        return False
    
    def create_backup(self, file_path):
        """Create backup of file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_name = f"{filename}.{timestamp}.backup"
            backup_path = os.path.join(BACKUP_DIR, backup_name)
            
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # Clean old backups (keep only last 10)
            self.cleanup_backups(filename)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
    
    def cleanup_backups(self, filename):
        """Clean up old backup files"""
        try:
            backup_files = []
            for f in os.listdir(BACKUP_DIR):
                if f.startswith(filename + '.') and f.endswith('.backup'):
                    backup_path = os.path.join(BACKUP_DIR, f)
                    backup_files.append((backup_path, os.path.getmtime(backup_path)))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups (keep only 10 most recent)
            for backup_path, _ in backup_files[10:]:
                os.remove(backup_path)
                
        except Exception as e:
            logger.error(f"Error cleaning backups: {e}")
    
    def add_to_recent_files(self, file_path):
        """Add file to recent files list"""
        recent_files = self.config.get('recent_files', [])
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only specified number of recent files
        max_recent = self.config.get('max_recent_files', 10)
        recent_files = recent_files[:max_recent]
        
        self.config.set('recent_files', recent_files)
        self.config.save_config()
    
    def get_recent_files(self):
        """Get list of recent files (existing only)"""
        recent_files = self.config.get('recent_files', [])
        return [f for f in recent_files if os.path.exists(f)]
    
    def start_auto_save(self):
        """Start auto-save timer"""
        if self.config.get('auto_save', True) and self.current_file:
            interval = self.config.get('auto_save_interval', 30) * 1000  # Convert to milliseconds
            self.stop_auto_save()  # Stop any existing timer
            # Note: auto_save_timer will be set by the main app
    
    def stop_auto_save(self):
        """Stop auto-save timer"""
        if self.auto_save_timer:
            # This will be handled by the main app
            pass
    
    def ask_save_changes(self):
        """Ask user if they want to save changes"""
        if not self.unsaved_changes:
            return True
        
        result = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save before continuing?"
        )
        
        if result is True:  # Yes - save
            return self.save_current_file()
        elif result is False:  # No - don't save
            return True
        else:  # Cancel
            return False
    
    def save_current_file(self):
        """Save current file (placeholder - will be implemented by main app)"""
        return True
    
    def set_unsaved_changes(self, has_changes):
        """Set unsaved changes flag"""
        self.unsaved_changes = has_changes

class UpdateManager:
    """Advanced update management system"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.update_window = None
        logger.info("UpdateManager initialized")
    
    def check_for_updates(self, silent=False):
        """Check for updates"""
        if not HAS_REQUESTS:
            if not silent:
                messagebox.showerror("Error", "Requests library not available for update checking.")
            return
        
        def check_thread():
            try:
                response = requests.get(VERSION_URL, timeout=10)
                response.raise_for_status()
                
                version_info = response.json()
                latest_version = version_info.get("version", "")
                download_url = version_info.get("installer_url", "")
                release_notes = version_info.get("release_notes", "")
                
                # Update last check time
                self.config.set('last_update_check', datetime.now().strftime("%Y-%m-%d %H:%M"))
                self.config.save_config()
                
                if self.is_newer_version(latest_version, CURRENT_VERSION):
                    if not silent:
                        self.show_update_dialog(latest_version, download_url, release_notes)
                    return True
                else:
                    if not silent:
                        messagebox.showinfo("No Updates", f"You're running the latest version ({CURRENT_VERSION})! 🎉")
                    return False
                    
            except Exception as e:
                error_msg = f"Could not check for updates: {str(e)}"
                if not silent:
                    messagebox.showerror("Update Check Failed", error_msg)
                logger.error(error_msg)
                return False
        
        threading.Thread(target=check_thread, daemon=True).start()
    
    def is_newer_version(self, latest, current):
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
    
    def show_update_dialog(self, latest_version, download_url, release_notes):
        """Show update available dialog"""
        if self.update_window and self.update_window.winfo_exists():
            self.update_window.lift()
            return
        
        self.update_window = tk.Toplevel()
        self.update_window.title("Update Available")
        self.update_window.geometry("600x500")
        self.update_window.resizable(False, False)
        self.update_window.configure(bg='#2b2b2b')
        self.update_window.transient()
        self.update_window.grab_set()
        
        # Center the window
        self.update_window.update_idletasks()
        x = (self.update_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.update_window.winfo_screenheight() // 2) - (500 // 2)
        self.update_window.geometry(f"600x500+{x}+{y}")
        
        # Header
        header_frame = tk.Frame(self.update_window, bg='#0078d4', height=100)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🚀 Update Available!",
            font=("Segoe UI", 20, "bold"),
            bg='#0078d4',
            fg='white'
        ).pack(pady=20)
        
        tk.Label(
            header_frame,
            text=f"Version {latest_version} is now available (Current: {CURRENT_VERSION})",
            font=("Segoe UI", 12),
            bg='#0078d4',
            fg='white'
        ).pack()
        
        # Release notes
        notes_frame = tk.LabelFrame(
            self.update_window,
            text="What's New",
            font=("Segui UI", 12, "bold"),
            bg='#2b2b2b',
            fg='white'
        )
        notes_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        notes_text = scrolledtext.ScrolledText(
            notes_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            height=12
        )
        notes_text.pack(fill='both', expand=True, padx=10, pady=10)
        notes_text.insert(1.0, release_notes)
        notes_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(self.update_window, bg='#2b2b2b')
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        tk.Button(
            button_frame,
            text="📥 Download & Install",
            command=lambda: self.download_update(download_url),
            bg='#28a745',
            fg='white',
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=10,
            relief='flat'
        ).pack(side='right', padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="⏰ Later",
            command=self.update_window.destroy,
            bg='#6c757d',
            fg='white',
            font=("Segoe UI", 12),
            padx=20,
            pady=10,
            relief='flat'
        ).pack(side='right')
    
    def download_update(self, download_url):
        """Download and install update"""
        self.update_window.destroy()
        
        def download_thread():
            try:
                # Show download progress (simplified)
                messagebox.showinfo("Download", "Download started. The installer will launch automatically.")
                
                response = requests.get(download_url, stream=True)
                response.raise_for_status()
                
                # Save to temp directory
                temp_dir = tempfile.gettempdir()
                installer_path = os.path.join(temp_dir, "MyApp_Setup.exe")
                
                with open(installer_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Launch installer
                subprocess.Popen([installer_path])
                
                # Close application
                messagebox.showinfo("Update", "Installer launched. Application will close now.")
                os._exit(0)
                
            except Exception as e:
                messagebox.showerror("Download Failed", f"Could not download update:\n{str(e)}")
        
        threading.Thread(target=download_thread, daemon=True).start()

class ModernApp:
    """Main application class with modern UI and advanced features"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{CURRENT_VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize managers
        self.config = ConfigManager()
        self.theme = ThemeManager()
        self.file_manager = FileManager(self.config)
        self.update_manager = UpdateManager(self.config)
        
        # Apply saved theme
        saved_theme = self.config.get('theme', 'dark')
        self.theme.switch_theme(saved_theme)
        
        # Set application icon
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Initialize UI
        self.create_ui()
        self.apply_theme()
        
        # Auto-save timer
        self.auto_save_timer = None
        
        # Start auto-save if enabled
        if self.config.get('auto_save', True):
            self.start_auto_save_timer()
        
        # Check for updates on startup
        if self.config.get('check_updates_on_startup', True):
            self.root.after(5000, lambda: self.update_manager.check_for_updates(silent=True))
        
        logger.info("ModernApp initialized")
    
    def create_ui(self):
        """Create the main user interface"""
        # Create menu bar
        self.create_menu_bar()
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.theme.get_colors()['bg'])
        main_container.pack(fill='both', expand=True)
        
        # Create sidebar
        self.create_sidebar(main_container)
        
        # Create main content area
        self.create_main_content(main_container)
        
        # Create status bar
        self.create_status_bar()
    
    def create_menu_bar(self):
        """Create application menu bar"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As", command=self.save_file_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self.update_recent_menu()
        
        file_menu.add_separator()
        if HAS_PDF_EXPORT:
            file_menu.add_command(label="Export to PDF", command=self.export_to_pdf)
            file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace", command=self.show_find_replace, accelerator="Ctrl+F")
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)
        
        # Theme submenu
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Themes", menu=theme_menu)
        theme_menu.add_command(label="Dark Professional", command=lambda: self.switch_theme('dark'))
        theme_menu.add_command(label="Light Professional", command=lambda: self.switch_theme('light'))
        theme_menu.add_command(label="High Contrast", command=lambda: self.switch_theme('high_contrast'))
        
        view_menu.add_separator()
        view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers)
        view_menu.add_command(label="Word Count", command=self.show_word_count)
        
        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self.show_settings)
        tools_menu.add_command(label="Check for Updates", command=lambda: self.update_manager.check_for_updates())
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="View Logs", command=self.show_logs)
        help_menu.add_command(label="Visit GitHub", command=self.open_github)
        
        # Bind keyboard shortcuts
        self.bind_shortcuts()
    
    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        shortcuts = {
            '<Control-n>': lambda e: self.new_file(),
            '<Control-o>': lambda e: self.open_file(),
            '<Control-s>': lambda e: self.save_file(),
            '<Control-Shift-S>': lambda e: self.save_file_as(),
            '<Control-z>': lambda e: self.undo(),
            '<Control-y>': lambda e: self.redo(),
            '<Control-x>': lambda e: self.cut(),
            '<Control-c>': lambda e: self.copy(),
            '<Control-v>': lambda e: self.paste(),
            '<Control-a>': lambda e: self.select_all(),
            '<Control-f>': lambda e: self.show_find_replace(),
            '<Control-h>': lambda e: self.show_find_replace(),
            '<F5>': lambda e: self.update_manager.check_for_updates(),
            '<F11>': lambda e: self.toggle_fullscreen(),
            '<Control-plus>': lambda e: self.zoom_in(),
            '<Control-minus>': lambda e: self.zoom_out(),
            '<Control-0>': lambda e: self.reset_zoom()
        }
        
        for shortcut, command in shortcuts.items():
            self.root.bind(shortcut, command)
    
    def create_sidebar(self, parent):
        """Create application sidebar"""
        self.sidebar = tk.Frame(parent, bg=self.theme.get_colors()['sidebar_bg'], width=280)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        
        # App header
        header_frame = tk.Frame(self.sidebar, bg=self.theme.get_colors()['primary'], height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🚀",
            font=("Segoe UI", 24),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(side='left', padx=15, pady=20)
        
        title_frame = tk.Frame(header_frame, bg=self.theme.get_colors()['primary'])
        title_frame.pack(side='left', fill='both', expand=True, pady=20)
        
        tk.Label(
            title_frame,
            text=APP_NAME,
            font=("Segoe UI", 14, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white',
            anchor='w'
        ).pack(fill='x')
        
        tk.Label(
            title_frame,
            text=f"v{CURRENT_VERSION}",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['primary'],
            fg='white',
            anchor='w'
        ).pack(fill='x')
        
        # Quick actions
        self.create_quick_actions()
        
        # Document stats
        self.create_document_stats()
        
        # Recent files
        self.create_recent_files_section()
    
    def create_quick_actions(self):
        """Create quick actions section"""
        actions_frame = tk.LabelFrame(
            self.sidebar,
            text="Quick Actions",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        actions_frame.pack(fill='x', padx=15, pady=15)
        
        actions = [
            ("📄 New File", self.new_file, self.theme.get_colors()['success']),
            ("📂 Open File", self.open_file, self.theme.get_colors()['primary']),
            ("💾 Save File", self.save_file, self.theme.get_colors()['info']),
            ("🔍 Find & Replace", self.show_find_replace, self.theme.get_colors()['warning'])
        ]
        
        for text, command, color in actions:
            btn = tk.Button(
                actions_frame,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=("Segoe UI", 10, "bold"),
                relief='flat',
                padx=15,
                pady=8,
                anchor='w',
                cursor='hand2'
            )
            btn.pack(fill='x', pady=2)
            
            # Hover effects
            def on_enter(e, button=btn, orig_color=color):
                button.configure(bg=self.lighten_color(orig_color))
            
            def on_leave(e, button=btn, orig_color=color):
                button.configure(bg=orig_color)
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
    
    def create_document_stats(self):
        """Create document statistics section"""
        stats_frame = tk.LabelFrame(
            self.sidebar,
            text="Document Statistics",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        stats_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.stats_labels = {}
        stats_info = [
            ("lines", "Lines: 0"),
            ("words", "Words: 0"),
            ("chars", "Characters: 0"),
            ("selected", "Selected: 0")
        ]
        
        for key, text in stats_info:
            label = tk.Label(
                stats_frame,
                text=text,
                font=("Segoe UI", 10),
                bg=self.theme.get_colors()['sidebar_bg'],
                fg=self.theme.get_colors()['fg'],
                anchor='w'
            )
            label.pack(fill='x', pady=2)
            self.stats_labels[key] = label
        
        # Update stats regularly
        self.update_document_stats()
    
    def create_recent_files_section(self):
        """Create recent files section"""
        recent_frame = tk.LabelFrame(
            self.sidebar,
            text="Recent Files",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        recent_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Recent files listbox
        listbox_frame = tk.Frame(recent_frame, bg=self.theme.get_colors()['sidebar_bg'])
        listbox_frame.pack(fill='both', expand=True)
        
        self.recent_listbox = tk.Listbox(
            listbox_frame,
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg'],
            font=("Segoe UI", 9),
            selectbackground=self.theme.get_colors()['primary'],
            selectforeground='white',
            relief='flat',
            activestyle='none'
        )
        
        recent_scrollbar = tk.Scrollbar(listbox_frame, orient='vertical', command=self.recent_listbox.yview)
        self.recent_listbox.configure(yscrollcommand=recent_scrollbar.set)
        
        recent_scrollbar.pack(side='right', fill='y')
        self.recent_listbox.pack(fill='both', expand=True)
        
        self.recent_listbox.bind('<Double-Button-1>', self.open_recent_from_list)
        self.recent_listbox.bind('<Return>', self.open_recent_from_list)
        
        self.update_recent_files_list()
    
    def create_main_content(self, parent):
        """Create main content area"""
        content_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        content_frame.pack(side='right', fill='both', expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_editor_tab()
        self.create_pdf_viewer_tab()
        self.create_welcome_tab()
        
        # Set welcome tab as default
        self.notebook.select(2)  # Welcome tab
    
    def create_welcome_tab(self):
        """Create welcome/home tab"""
        welcome_frame = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(welcome_frame, text="🏠 Welcome")
        
        # Scrollable content
        canvas = tk.Canvas(welcome_frame, bg=self.theme.get_colors()['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(welcome_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.get_colors()['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Welcome header
        header_frame = tk.Frame(scrollable_frame, bg=self.theme.get_colors()['primary'], height=120)
        header_frame.pack(fill='x', padx=20, pady=20)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🎉 Welcome to MyAwesome App!",
            font=("Segoe UI", 20, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=30)
        
        tk.Label(
            header_frame,
            text=f"Version {CURRENT_VERSION} • Your Modern Text Editor & PDF Viewer",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack()
        
        # Features grid
        features_frame = tk.Frame(scrollable_frame, bg=self.theme.get_colors()['bg'])
        features_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            features_frame,
            text="✨ Features & Capabilities",
            font=("Segoe UI", 16, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=(0, 20))
        
        # Feature cards
        features = [
            ("📝 Advanced Text Editor", "Syntax highlighting, auto-complete, multiple themes", self.theme.get_colors()['success']),
            ("📄 PDF Viewer", "View, zoom, rotate PDF documents with ease", self.theme.get_colors()['info']),
            ("🎨 Modern Themes", "Professional dark, light, and high contrast themes", self.theme.get_colors()['primary']),
            ("🔄 Auto-Save", "Never lose your work with intelligent auto-saving", self.theme.get_colors()['warning']),
            ("🔍 Advanced Search", "Powerful find & replace with regex support", self.theme.get_colors()['secondary']),
            ("⚡ Performance", "Fast, responsive interface with optimized rendering", self.theme.get_colors()['success'])
        ]
        
        for i, (title, desc, color) in enumerate(features):
            if i % 2 == 0:
                row_frame = tk.Frame(features_frame, bg=self.theme.get_colors()['bg'])
                row_frame.pack(fill='x', pady=5)
            
            card_frame = tk.Frame(row_frame, bg=color, relief='flat', bd=0)
            card_frame.pack(side='left' if i % 2 == 0 else 'right', fill='both', expand=True, padx=(0, 5) if i % 2 == 0 else (5, 0))
            
            tk.Label(
                card_frame,
                text=title,
                font=("Segoe UI", 12, "bold"),
                bg=color,
                fg='white'
            ).pack(pady=(15, 5))
            
            tk.Label(
                card_frame,
                text=desc,
                font=("Segoe UI", 10),
                bg=color,
                fg='white',
                wraplength=280,
                justify='center'
            ).pack(pady=(0, 15), padx=15)
        
        # Getting started section
        start_frame = tk.LabelFrame(
            scrollable_frame,
            text="🚀 Getting Started",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=20,
            pady=20
        )
        start_frame.pack(fill='x', padx=20, pady=20)
        
        steps = [
            "1. 📄 Create a new file or open an existing document",
            "2. ✏️ Use the advanced editor with syntax highlighting and auto-completion",
            "3. 🔍 Use Ctrl+F to find and replace text with powerful search options",
            "4. 💾 Save your work automatically or manually with Ctrl+S",
            "5. 📋 Export to PDF format for professional document sharing",
            "6. 🎨 Customize your experience with themes and settings"
        ]
        
        for step in steps:
            step_frame = tk.Frame(start_frame, bg=self.theme.get_colors()['bg'])
            step_frame.pack(fill='x', pady=5)
            
            tk.Label(
                step_frame,
                text=step,
                font=("Segoe UI", 11),
                bg=self.theme.get_colors()['bg'],
                fg=self.theme.get_colors()['fg'],
                anchor='w'
            ).pack(fill='x')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_editor_tab(self):
        """Create text editor tab"""
        editor_frame = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(editor_frame, text="📝 Text Editor")
        
                # Create advanced text editor
        self.text_editor = AdvancedTextEditor(editor_frame, self.theme)
        self.text_editor.get_frame().pack(fill='both', expand=True)
        
        # Connect file manager to editor
        self.file_manager.save_current_file = self.save_current_file_content
    
    def create_pdf_viewer_tab(self):
        """Create PDF viewer tab"""
        pdf_frame = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(pdf_frame, text="📄 PDF Viewer")
        
        # Create PDF viewer
        self.pdf_viewer = PDFViewer(pdf_frame, self.theme)
        self.pdf_viewer.get_frame().pack(fill='both', expand=True)
    
    def create_status_bar(self):
        """Create application status bar"""
        self.status_frame = tk.Frame(self.root, bg=self.theme.get_colors()['sidebar_bg'], height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        # Status message
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # File info
        self.file_label = tk.Label(
            self.status_frame,
            text="No file loaded",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['primary']
        )
        self.file_label.pack(side='left', padx=20, pady=5)
        
        # Cursor position
        self.cursor_label = tk.Label(
            self.status_frame,
            text="Ln 1, Col 1",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg']
        )
        self.cursor_label.pack(side='right', padx=10, pady=5)
        
        # Update cursor position
        self.update_cursor_position()
    
    # File operations
    def new_file(self):
        """Create new file"""
        if self.file_manager.new_file():
            self.text_editor.clear_text()
            self.update_title()
            self.set_status("New file created")
            logger.info("New file created")
    
    def open_file(self):
        """Open file"""
        content = self.file_manager.open_file()
        if content is not None:
            self.text_editor.set_text(content)
            self.update_title()
            self.set_status(f"Opened: {os.path.basename(self.file_manager.current_file)}")
            self.update_recent_files_list()
            self.update_recent_menu()
    
    def save_file(self):
        """Save current file"""
        content = self.text_editor.get_text()
        if self.file_manager.save_file(content):
            self.update_title()
            self.set_status(f"Saved: {os.path.basename(self.file_manager.current_file)}")
            return True
        return False
    
    def save_file_as(self):
        """Save file with new name"""
        content = self.text_editor.get_text()
        if self.file_manager.save_file_as(content):
            self.update_title()
            self.set_status(f"Saved as: {os.path.basename(self.file_manager.current_file)}")
            self.update_recent_files_list()
            self.update_recent_menu()
            return True
        return False
    
    def save_current_file_content(self):
        """Save current file content (for file manager)"""
        return self.save_file()
    
    def export_to_pdf(self):
        """Export text to PDF"""
        if not HAS_PDF_EXPORT:
            messagebox.showerror("Error", "PDF export not available. Install ReportLab: pip install reportlab")
            return
        
        content = self.text_editor.get_text().strip()
        if not content:
            messagebox.showwarning("Warning", "No content to export")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Export to PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                c = canvas.Canvas(file_path, pagesize=letter)
                width, height = letter
                
                # Set up text
                text_object = c.beginText(inch, height - inch)
                text_object.setFont("Courier", 10)
                
                # Add content line by line
                lines = content.split('\n')
                line_height = 12
                current_y = height - inch
                
                for line in lines:
                    if current_y < inch:  # Start new page
                        c.drawText(text_object)
                        c.showPage()
                        text_object = c.beginText(inch, height - inch)
                        text_object.setFont("Courier", 10)
                        current_y = height - inch
                    
                    text_object.textLine(line)
                    current_y -= line_height
                
                c.drawText(text_object)
                c.save()
                
                self.set_status(f"Exported to PDF: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"File exported to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not export to PDF:\n{str(e)}")
                logger.error(f"PDF export error: {e}")
    
    # Edit operations
    def undo(self):
        """Undo last action"""
        if hasattr(self.text_editor, 'undo'):
            self.text_editor.undo()
    
    def redo(self):
        """Redo last undone action"""
        if hasattr(self.text_editor, 'redo'):
            self.text_editor.redo()
    
    def cut(self):
        """Cut selected text"""
        if hasattr(self.text_editor, 'cut'):
            self.text_editor.cut()
    
    def copy(self):
        """Copy selected text"""
        if hasattr(self.text_editor, 'copy'):
            self.text_editor.copy()
    
    def paste(self):
        """Paste text from clipboard"""
        if hasattr(self.text_editor, 'paste'):
            self.text_editor.paste()
    
    def select_all(self):
        """Select all text"""
        if hasattr(self.text_editor, 'select_all'):
            self.text_editor.select_all()
    
    def show_find_replace(self):
        """Show find and replace dialog"""
        if hasattr(self.text_editor, 'show_find_replace'):
            self.text_editor.show_find_replace()
    
    # View operations
    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        if hasattr(self.text_editor, 'toggle_line_numbers'):
            self.text_editor.toggle_line_numbers()
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        current_state = self.root.attributes('-fullscreen')
        self.root.attributes('-fullscreen', not current_state)
    
    def zoom_in(self):
        """Increase font size"""
        if hasattr(self.text_editor, 'zoom_in'):
            self.text_editor.zoom_in()
    
    def zoom_out(self):
        """Decrease font size"""
        if hasattr(self.text_editor, 'zoom_out'):
            self.text_editor.zoom_out()
    
    def reset_zoom(self):
        """Reset zoom to default"""
        if hasattr(self.text_editor, 'zoom_level'):
            self.text_editor.zoom_level = 100
            self.text_editor.apply_zoom()
    
    def switch_theme(self, theme_name):
        """Switch application theme"""
        self.theme.switch_theme(theme_name)
        self.config.set('theme', theme_name)
        self.config.save_config()
        
        # Apply theme to all components
        self.apply_theme()
        
        messagebox.showinfo("Theme Changed", f"Theme changed to {theme_name.title()}.\nSome changes may require restart for full effect.")
    
    def apply_theme(self):
        """Apply current theme to all UI elements"""
        colors = self.theme.get_colors()
        
        # Update root window
        self.root.configure(bg=colors['bg'])
        
        # Update status bar
        if hasattr(self, 'status_frame'):
            self.status_frame.configure(bg=colors['sidebar_bg'])
            self.status_label.configure(bg=colors['sidebar_bg'], fg=colors['fg'])
            if hasattr(self, 'file_label'):
                self.file_label.configure(bg=colors['sidebar_bg'], fg=colors['primary'])
            if hasattr(self, 'cursor_label'):
                self.cursor_label.configure(bg=colors['sidebar_bg'], fg=colors['fg'])
        
        # Update sidebar
        if hasattr(self, 'sidebar'):
            self.sidebar.configure(bg=colors['sidebar_bg'])
        
        # Refresh editor and PDF viewer themes
        if hasattr(self, 'text_editor'):
            self.text_editor.theme = self.theme
        if hasattr(self, 'pdf_viewer'):
            self.pdf_viewer.theme = self.theme
    
    def show_word_count(self):
        """Show word count dialog"""
        content = self.text_editor.get_text().strip()
        
        # Calculate statistics
        lines = len(content.split('\n')) if content else 0
        words = len(content.split()) if content else 0
        chars = len(content)
        chars_no_spaces = len(content.replace(' ', '').replace('\n', '').replace('\t', ''))
        paragraphs = len([p for p in content.split('\n\n') if p.strip()]) if content else 0
        
        # Show selected text stats if any
        try:
            selected = self.text_editor.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            selected_words = len(selected.split()) if selected else 0
            selected_chars = len(selected) if selected else 0
        except tk.TclError:
            selected_words = 0
            selected_chars = 0
        
        stats_text = f"""Document Statistics:

Total:
• Lines: {lines:,}
• Words: {words:,}
• Characters: {chars:,}
• Characters (no spaces): {chars_no_spaces:,}
• Paragraphs: {paragraphs:,}
"""
        
        if selected_words > 0:
            stats_text += f"""
Selected:
• Words: {selected_words:,}
• Characters: {selected_chars:,}"""
        
        messagebox.showinfo("Document Statistics", stats_text)
    
    # Recent files management
    def update_recent_menu(self):
        """Update recent files menu"""
        if not hasattr(self, 'recent_menu'):
            return
        
        # Clear existing items
        self.recent_menu.delete(0, 'end')
        
        recent_files = self.file_manager.get_recent_files()
        if not recent_files:
            self.recent_menu.add_command(label="No recent files", state='disabled')
        else:
            for file_path in recent_files:
                filename = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=filename,
                    command=lambda fp=file_path: self.open_recent_file(fp)
                )
    
    def update_recent_files_list(self):
        """Update recent files listbox"""
        if not hasattr(self, 'recent_listbox'):
            return
        
        self.recent_listbox.delete(0, tk.END)
        recent_files = self.file_manager.get_recent_files()
        
        for file_path in recent_files:
            filename = os.path.basename(file_path)
            self.recent_listbox.insert(tk.END, filename)
    
    def open_recent_file(self, file_path):
        """Open recent file"""
        content = self.file_manager.open_file(file_path)
        if content is not None:
            self.text_editor.set_text(content)
            self.update_title()
            self.set_status(f"Opened: {os.path.basename(file_path)}")
    
    def open_recent_from_list(self, event):
        """Open recent file from listbox"""
        selection = self.recent_listbox.curselection()
        if selection:
            index = selection[0]
            recent_files = self.file_manager.get_recent_files()
            if index < len(recent_files):
                self.open_recent_file(recent_files[index])
    
    # UI updates and status
    def update_title(self):
        """Update window title"""
        if self.file_manager.current_file:
            filename = os.path.basename(self.file_manager.current_file)
            modified = " *" if self.file_manager.unsaved_changes else ""
            title = f"{APP_NAME} v{CURRENT_VERSION} - {filename}{modified}"
            self.file_label.config(text=filename + modified)
        else:
            modified = " *" if self.file_manager.unsaved_changes else ""
            title = f"{APP_NAME} v{CURRENT_VERSION} - Untitled{modified}"
            self.file_label.config(text="Untitled" + modified)
        
        self.root.title(title)
    
    def set_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
        
        # Clear status after 5 seconds
        self.root.after(5000, lambda: self.status_label.config(text="Ready"))
    
    def update_document_stats(self):
        """Update document statistics in sidebar"""
        if hasattr(self, 'stats_labels') and hasattr(self, 'text_editor'):
            try:
                content = self.text_editor.get_text()
                lines = len(content.split('\n')) if content else 0
                words = len(content.split()) if content else 0
                chars = len(content)
                
                                # Get selected text info
                try:
                    selected = self.text_editor.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
                    selected_count = len(selected.split()) if selected else 0
                except tk.TclError:
                    selected_count = 0
                
                # Update labels
                self.stats_labels['lines'].config(text=f"Lines: {lines:,}")
                self.stats_labels['words'].config(text=f"Words: {words:,}")
                self.stats_labels['chars'].config(text=f"Characters: {chars:,}")
                self.stats_labels['selected'].config(text=f"Selected: {selected_count} words")
                
            except Exception as e:
                logger.error(f"Error updating document stats: {e}")
        
        # Schedule next update
        self.root.after(2000, self.update_document_stats)
    
    def update_cursor_position(self):
        """Update cursor position in status bar"""
        if hasattr(self, 'text_editor') and hasattr(self, 'cursor_label'):
            try:
                cursor_pos = self.text_editor.text_editor.index(tk.INSERT)
                line, col = cursor_pos.split('.')
                self.cursor_label.config(text=f"Ln {line}, Col {int(col) + 1}")
            except:
                pass
        
        # Schedule next update
        self.root.after(100, self.update_cursor_position)
    
    def on_text_change(self):
        """Handle text editor changes"""
        self.file_manager.set_unsaved_changes(True)
        self.update_title()
        
        # Restart auto-save timer
        if self.config.get('auto_save', True):
            self.restart_auto_save_timer()
    
    # Auto-save functionality
    def start_auto_save_timer(self):
        """Start auto-save timer"""
        if self.config.get('auto_save', True):
            interval = self.config.get('auto_save_interval', 30) * 1000
            self.auto_save_timer = self.root.after(interval, self.auto_save)
    
    def restart_auto_save_timer(self):
        """Restart auto-save timer"""
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        self.start_auto_save_timer()
    
    def auto_save(self):
        """Perform auto-save"""
        if (self.file_manager.unsaved_changes and 
            self.file_manager.current_file and 
            self.config.get('auto_save', True)):
            
            content = self.text_editor.get_text()
            if self.file_manager.save_file(content, self.file_manager.current_file):
                self.update_title()
                self.set_status(f"Auto-saved: {os.path.basename(self.file_manager.current_file)}")
        
        # Schedule next auto-save
        self.start_auto_save_timer()
    
    # Settings and configuration
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("600x700")
        settings_window.resizable(False, False)
        settings_window.configure(bg=self.theme.get_colors()['bg'])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Center the window
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - (600 // 2)
        y = (settings_window.winfo_screenheight() // 2) - (700 // 2)
        settings_window.geometry(f"600x700+{x}+{y}")
        
        # Create notebook for settings categories
        settings_notebook = ttk.Notebook(settings_window)
        settings_notebook.pack(fill='both', expand=True, padx=20, pady=20)
        
        # General settings
        self.create_general_settings(settings_notebook)
        
        # Editor settings
        self.create_editor_settings(settings_notebook)
        
        # Theme settings
        self.create_theme_settings(settings_notebook)
        
        # Advanced settings
        self.create_advanced_settings(settings_notebook)
    
    def create_general_settings(self, parent):
        """Create general settings tab"""
        general_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        parent.add(general_frame, text="General")
        
        # User information
        user_frame = tk.LabelFrame(
            general_frame,
            text="User Information",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        user_frame.pack(fill='x', padx=20, pady=10)
        
        # Name
        tk.Label(user_frame, text="Name:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=self.config.get('user_name', ''))
        tk.Entry(user_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # Email
        tk.Label(user_frame, text="Email:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).grid(row=1, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar(value=self.config.get('user_email', ''))
        tk.Entry(user_frame, textvariable=self.email_var, width=30).grid(row=1, column=1, padx=(10, 0), pady=5)
        
        # Auto-save settings
        save_frame = tk.LabelFrame(
            general_frame,
            text="Auto-Save Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        save_frame.pack(fill='x', padx=20, pady=10)
        
        self.auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', True))
        tk.Checkbutton(
            save_frame,
            text="Enable auto-save",
            variable=self.auto_save_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=5)
        
        interval_frame = tk.Frame(save_frame, bg=self.theme.get_colors()['bg'])
        interval_frame.pack(fill='x', pady=5)
        
        tk.Label(interval_frame, text="Auto-save interval (seconds):", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left')
        self.auto_save_interval_var = tk.IntVar(value=self.config.get('auto_save_interval', 30))
        tk.Spinbox(interval_frame, from_=10, to=300, textvariable=self.auto_save_interval_var, width=10).pack(side='left', padx=(10, 0))
        
        # Backup settings
        self.create_backups_var = tk.BooleanVar(value=self.config.get('create_backups', True))
        tk.Checkbutton(
            save_frame,
            text="Create backup files",
            variable=self.create_backups_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=5)
        
        # Update settings
        update_frame = tk.LabelFrame(
            general_frame,
            text="Update Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        update_frame.pack(fill='x', padx=20, pady=10)
        
        self.check_updates_var = tk.BooleanVar(value=self.config.get('check_updates_on_startup', True))
        tk.Checkbutton(
            update_frame,
            text="Check for updates on startup",
            variable=self.check_updates_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=5)
        
        # Save button
        save_btn = tk.Button(
            general_frame,
            text="💾 Save Settings",
            command=self.save_general_settings,
            bg=self.theme.get_colors()['success'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat'
        )
        save_btn.pack(pady=20)
    
    def create_editor_settings(self, parent):
        """Create editor settings tab"""
        editor_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        parent.add(editor_frame, text="Editor")
        
        # Font settings
        font_frame = tk.LabelFrame(
            editor_frame,
            text="Font Settings",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        font_frame.pack(fill='x', padx=20, pady=10)
        
        # Font family
        font_family_frame = tk.Frame(font_frame, bg=self.theme.get_colors()['bg'])
        font_family_frame.pack(fill='x', pady=5)
        
        tk.Label(font_family_frame, text="Font Family:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left')
        self.font_family_var = tk.StringVar(value=self.config.get('editor_font_family', 'Consolas'))
        font_combo = ttk.Combobox(font_family_frame, textvariable=self.font_family_var, 
                                 values=['Consolas', 'Courier New', 'Monaco', 'Source Code Pro', 'Fira Code', 'JetBrains Mono'])
        font_combo.pack(side='left', padx=(10, 0))
        
        # Font size
        font_size_frame = tk.Frame(font_frame, bg=self.theme.get_colors()['bg'])
        font_size_frame.pack(fill='x', pady=5)
        
        tk.Label(font_size_frame, text="Font Size:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left')
        self.font_size_var = tk.IntVar(value=self.config.get('editor_font_size', 11))
        tk.Spinbox(font_size_frame, from_=8, to=72, textvariable=self.font_size_var, width=10).pack(side='left', padx=(10, 0))
        
        # Editor behavior
        behavior_frame = tk.LabelFrame(
            editor_frame,
            text="Editor Behavior",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        behavior_frame.pack(fill='x', padx=20, pady=10)
        
        self.show_line_numbers_var = tk.BooleanVar(value=self.config.get('show_line_numbers', True))
        tk.Checkbutton(
            behavior_frame,
            text="Show line numbers",
            variable=self.show_line_numbers_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=2)
        
        self.word_wrap_var = tk.BooleanVar(value=self.config.get('editor_word_wrap', False))
        tk.Checkbutton(
            behavior_frame,
            text="Word wrap",
            variable=self.word_wrap_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=2)
        
        self.syntax_highlighting_var = tk.BooleanVar(value=self.config.get('editor_syntax_highlighting', True))
        tk.Checkbutton(
            behavior_frame,
            text="Syntax highlighting",
            variable=self.syntax_highlighting_var,
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg']
        ).pack(anchor='w', pady=2)
        
        # Save button
        save_btn = tk.Button(
            editor_frame,
            text="💾 Save Settings",
            command=self.save_editor_settings,
            bg=self.theme.get_colors()['success'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat'
        )
        save_btn.pack(pady=20)
    
    def create_theme_settings(self, parent):
        """Create theme settings tab"""
        theme_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        parent.add(theme_frame, text="Themes")
        
                # Theme selection
        selection_frame = tk.LabelFrame(
            theme_frame,
            text="Select Theme",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        selection_frame.pack(fill='x', padx=20, pady=10)
        
        self.theme_var = tk.StringVar(value=self.config.get('theme', 'dark'))
        
        themes = [
            ('dark', 'Dark Professional', 'Modern dark theme with blue accents'),
            ('light', 'Light Professional', 'Clean light theme with subtle colors'),
            ('high_contrast', 'High Contrast', 'High contrast theme for accessibility')
        ]
        
        for theme_id, theme_name, description in themes:
            theme_radio = tk.Radiobutton(
                selection_frame,
                text=theme_name,
                variable=self.theme_var,
                value=theme_id,
                bg=self.theme.get_colors()['bg'],
                fg=self.theme.get_colors()['fg'],
                activebackground=self.theme.get_colors()['bg'],
                selectcolor=self.theme.get_colors()['primary'],
                font=("Segoe UI", 10, "bold")
            )
            theme_radio.pack(anchor='w', pady=5)
            
            tk.Label(
                selection_frame,
                text=f"  {description}",
                bg=self.theme.get_colors()['bg'],
                fg=self.theme.get_colors()['secondary'],
                font=("Segoe UI", 9)
            ).pack(anchor='w', padx=(20, 0))
        
        # Theme preview
        preview_frame = tk.LabelFrame(
            theme_frame,
            text="Theme Preview",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        preview_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Preview area
        self.preview_area = tk.Frame(preview_frame, height=200, bg=self.theme.get_colors()['editor_bg'])
        self.preview_area.pack(fill='both', expand=True, pady=10)
        self.preview_area.pack_propagate(False)
        
        # Sample text
        tk.Label(
            self.preview_area,
            text="Sample Editor Text",
            font=("Consolas", 12, "bold"),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        ).pack(pady=20)
        
        # Apply and save buttons
        button_frame = tk.Frame(theme_frame, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(
            button_frame,
            text="🎨 Apply Theme",
            command=self.apply_theme_selection,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat'
        ).pack(side='left')
        
        tk.Button(
            button_frame,
            text="💾 Save Settings",
            command=self.save_theme_settings,
            bg=self.theme.get_colors()['success'],
            fg='white',
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=10,
            relief='flat'
        ).pack(side='right')
    
    def create_advanced_settings(self, parent):
        """Create advanced settings tab"""
        advanced_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        parent.add(advanced_frame, text="Advanced")
        
        # Performance settings
        perf_frame = tk.LabelFrame(
            advanced_frame,
            text="Performance",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        perf_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            perf_frame,
            text="Maximum recent files:",
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        self.max_recent_var = tk.IntVar(value=self.config.get('max_recent_files', 10))
        tk.Spinbox(
            perf_frame,
            from_=5,
            to=50,
            textvariable=self.max_recent_var,
            width=10
        ).grid(row=0, column=1, padx=(10, 0), pady=5)
        
        # File associations
        assoc_frame = tk.LabelFrame(
            advanced_frame,
            text="File Associations",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        assoc_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            assoc_frame,
            text="Associate common file types with this application:",
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(anchor='w', pady=5)
        
        # Logging settings
        log_frame = tk.LabelFrame(
            advanced_frame,
            text="Logging",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        log_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(
            log_frame,
            text="📋 View Logs",
            command=self.show_logs,
            bg=self.theme.get_colors()['info'],
            fg='white',
            font=("Segoe UI", 10),
            padx=15,
            pady=5,
            relief='flat'
        ).pack(side='left', pady=5)
        
        tk.Button(
            log_frame,
            text="🗑️ Clear Logs",
            command=self.clear_logs,
            bg=self.theme.get_colors()['warning'],
            fg='white',
            font=("Segoe UI", 10),
            padx=15,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=(10, 0), pady=5)
        
        # Reset settings
        reset_frame = tk.LabelFrame(
            advanced_frame,
            text="Reset",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        reset_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Button(
            reset_frame,
            text="🔄 Reset All Settings",
            command=self.reset_all_settings,
            bg=self.theme.get_colors()['danger'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief='flat'
        ).pack(pady=5)
        
        tk.Label(
            reset_frame,
            text="This will reset all settings to default values",
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['warning'],
            font=("Segoe UI", 9)
        ).pack()
    
    # Settings save methods
    def save_general_settings(self):
        """Save general settings"""
        self.config.update({
            'user_name': self.name_var.get(),
            'user_email': self.email_var.get(),
            'auto_save': self.auto_save_var.get(),
            'auto_save_interval': self.auto_save_interval_var.get(),
            'create_backups': self.create_backups_var.get(),
            'check_updates_on_startup': self.check_updates_var.get()
        })
        self.config.save_config()
        messagebox.showinfo("Settings", "General settings saved successfully!")
    
    def save_editor_settings(self):
        """Save editor settings"""
        self.config.update({
            'editor_font_family': self.font_family_var.get(),
            'editor_font_size': self.font_size_var.get(),
            'show_line_numbers': self.show_line_numbers_var.get(),
            'editor_word_wrap': self.word_wrap_var.get(),
            'editor_syntax_highlighting': self.syntax_highlighting_var.get()
        })
        self.config.save_config()
        
        # Apply editor settings immediately
        if hasattr(self, 'text_editor'):
            self.text_editor.apply_settings(self.config.config)
        
        messagebox.showinfo("Settings", "Editor settings saved successfully!")
    
    def apply_theme_selection(self):
        """Apply selected theme"""
        theme_name = self.theme_var.get()
        self.switch_theme(theme_name)
    
    def save_theme_settings(self):
        """Save theme settings"""
        theme_name = self.theme_var.get()
        self.config.set('theme', theme_name)
        self.config.save_config()
        messagebox.showinfo("Settings", "Theme settings saved successfully!")
    
    def reset_all_settings(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to default values?"):
            try:
                # Remove config file
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                
                # Reload default config
                self.config = ConfigManager()
                
                # Apply default theme
                self.theme.switch_theme('dark')
                self.apply_theme()
                
                messagebox.showinfo("Settings", "All settings have been reset to defaults. Please restart the application.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not reset settings:\n{str(e)}")
    
    # Logging functionality
    def show_logs(self):
        """Show application logs"""
        log_window = tk.Toplevel(self.root)
        log_window.title("Application Logs")
        log_window.geometry("800x600")
        log_window.configure(bg=self.theme.get_colors()['bg'])
        
        # Log text area
        log_text = scrolledtext.ScrolledText(
            log_window,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        )
        log_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Load log content
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                log_text.insert(1.0, log_content)
            else:
                log_text.insert(1.0, "No log file found.")
        except Exception as e:
            log_text.insert(1.0, f"Error reading log file: {str(e)}")
        
        log_text.config(state='disabled')
        
        # Scroll to bottom
        log_text.see(tk.END)
    
    def clear_logs(self):
        """Clear application logs"""
        if messagebox.askyesno("Clear Logs", "Are you sure you want to clear all logs?"):
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, 'w') as f:
                        f.write("")
                logger.info("Logs cleared by user")
                messagebox.showinfo("Success", "Logs cleared successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear logs:\n{str(e)}")
    
    # Utility methods
    def lighten_color(self, color):
        """Lighten a hex color by 20%"""
        try:
            # Remove # if present
            color = color.lstrip('#')
            # Convert to RGB
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            # Lighten by 20%
            r = min(255, int(r * 1.2))
            g = min(255, int(g * 1.2))
            b = min(255, int(b * 1.2))
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("500x600")
        about_window.resizable(False, False)
        about_window.configure(bg=self.theme.get_colors()['bg'])
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center the window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (600 // 2)
        about_window.geometry(f"500x600+{x}+{y}")
        
        # App icon and title
        header_frame = tk.Frame(about_window, bg=self.theme.get_colors()['primary'], height=120)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🚀",
            font=("Segoe UI", 40),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=20)
        
        tk.Label(
            header_frame,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack()
        
        # App information
        info_frame = tk.Frame(about_window, bg=self.theme.get_colors()['bg'])
        info_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        tk.Label(
            info_frame,
            text=f"Version {CURRENT_VERSION}",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
        ).pack(pady=(0, 20))
        
        about_text = """A modern, feature-rich text editor and PDF viewer built with Python and Tkinter.

🌟 Key Features:
• Advanced text editing with syntax highlighting
• PDF viewing and navigation capabilities
• Professional themes (Dark, Light, High Contrast)
• Auto-save with backup functionality
• Automatic update checking
• Customizable interface and settings
• Document statistics and word count
• Find & replace with advanced search
• Recent files management
• Export to PDF functionality

🛠️ Built With:
• Python 3.x
• Tkinter (GUI Framework)
• PyMuPDF (PDF Support)
• ReportLab (PDF Export)
• Requests (Updates)

📝 License:
Open Source Software

© 2025 PixelHeaven
All rights reserved."""
        
        tk.Label(
            info_frame,
            text=about_text,
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            justify='left',
            wraplength=440
        ).pack()
        
        # Buttons
        button_frame = tk.Frame(info_frame, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x', pady=20)
        
        tk.Button(
            button_frame,
            text="🌐 Visit GitHub",
            command=self.open_github,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            relief='flat'
        ).pack(side='left')
        
        tk.Button(
            button_frame,
            text="🔄 Check Updates",
            command=lambda: self.update_manager.check_for_updates(),
            bg=self.theme.get_colors()['info'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            relief='flat'
        ).pack(side='left', padx=(10, 0))
        
        tk.Button(
            button_frame,
            text="Close",
            command=about_window.destroy,
            bg=self.theme.get_colors()['secondary'],
            fg='white',
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            relief='flat'
        ).pack(side='right')
    
    def open_github(self):
        """Open GitHub repository"""
        github_url = "https://github.com/PixelHeaven/software1"
        webbrowser.open(github_url)
    
    def on_closing(self):
        """Handle application closing"""
        if self.file_manager.ask_save_changes():
            # Save configuration
            self.config.save_config()
            
            # Cancel auto-save timer
            if self.auto_save_timer:
                self.root.after_cancel(self.auto_save_timer)
            
            logger.info("Application closing")
            self.root.quit()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Connect text editor change callback
        if hasattr(self, 'text_editor'):
            self.text_editor.set_change_callback(self.on_text_change)
        
        # Restore window geometry
        try:
            geometry = self.config.get('window_geometry', '1200x800')
            self.root.geometry(geometry)
            
            window_state = self.config.get('window_state', 'normal')
            if window_state == 'zoomed':
                self.root.state('zoomed')
        except:
            # Center window on screen
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        logger.info(f"Application started - Version {CURRENT_VERSION}")
        self.root.mainloop()

# Enhanced AdvancedTextEditor class with additional methods
class AdvancedTextEditor:
    """Advanced text editor with syntax highlighting and modern features"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.change_callback = None
        self.search_window = None
        self.zoom_level = 100
        
        # Create the editor interface
        self.create_editor()
        
        # Initialize syntax highlighting
        self.setup_syntax_highlighting()
        
        logger.info("AdvancedTextEditor created")
    
    def create_editor(self):
        """Create the editor interface"""
        self.editor_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        # Toolbar
        self.create_toolbar()
        
        # Editor area
        editor_container = tk.Frame(self.editor_frame, bg=self.theme.get_colors()['bg'])
        editor_container.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Line numbers
        self.line_numbers = tk.Text(
            editor_container,
            width=4,
            padx=5,
            pady=5,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            font=('Consolas', 11),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg']
        )
        self.line_numbers.pack(side='left', fill='y')
        
        # Main text editor
        self.text_editor = tk.Text(
            editor_container,
            wrap='none',
            font=('Consolas', 11),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg'],
            insertbackground=self.theme.get_colors()['primary'],
            selectbackground=self.theme.get_colors()['primary'],
            selectforeground='white',
            undo=True,
            maxundo=100,
            tabs=('1c', '2c', '3c', '4c', '5c', '6c', '7c', '8c')
        )
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(editor_container, orient='vertical', command=self.sync_scroll)
        h_scrollbar = tk.Scrollbar(editor_container, orient='horizontal', command=self.text_editor.xview)
        
        self.text_editor.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and editor
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.text_editor.pack(fill='both', expand=True)
        
        # Bind events
        self.text_editor.bind('<KeyRelease>', self.on_text_change)
        self.text_editor.bind('<Button-1>', self.on_text_change)
        self.text_editor.bind('<MouseWheel>', self.on_mousewheel)
        self.text_editor.bind('<Control-MouseWheel>', self.on_ctrl_mousewheel)
        
        # Context menu
        self.create_context_menu()
        
        # Update line numbers initially
        self.update_line_numbers()
    
    def create_toolbar(self):
        """Create editor toolbar"""
        toolbar = tk.Frame(self.editor_frame, bg=self.theme.get_colors()['sidebar_bg'], height=40)
        toolbar.pack(fill='x', padx=10, pady=(10, 0))
        toolbar.pack_propagate(False)
        
        # File operations
        file_buttons = [
            ("📄", "New file", None),
            ("📂", "Open file", None),
            ("💾", "Save file", None),
            ("📋", "Export PDF", None)
        ]
        
        for icon, tooltip, command in file_buttons:
            btn = tk.Button(
                toolbar,
                text=icon,
                font=("Segoe UI", 12),
                bg=self.theme.get_colors()['sidebar_bg'],
                fg=self.theme.get_colors()['fg'],
                relief='flat',
                padx=8,
                pady=5,
                cursor='hand2'
            )
            btn.pack(side='left', padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=self.theme.get_colors()['fg'], width=1).pack(side='left', fill='y', padx=5, pady=5)
        
        # Edit operations
        edit_buttons = [
            ("↶", "Undo", self.undo),
            ("↷", "Redo", self.redo),
            ("🔍", "Find", self.show_find_replace),
            ("🔢", "Line numbers", self.toggle_line_numbers)
        ]
        
        for icon, tooltip, command in edit_buttons:
            btn = tk.Button(
                toolbar,
                text=icon,
                font=("Segoe UI", 12),
                bg=self.theme.get_colors()['sidebar_bg'],
                fg=self.theme.get_colors()['fg'],
                relief='flat',
                padx=8,
                pady=5,
                cursor='hand2',
                command=command
            )
            btn.pack(side='left', padx=2)
        
        # Zoom controls
        tk.Frame(toolbar, bg=self.theme.get_colors()['fg'], width=1).pack(side='left', fill='y', padx=5, pady=5)
        
        zoom_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        zoom_frame.pack(side='right', padx=10)
        
        tk.Button(
            zoom_frame,
            text="🔍+",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            relief='flat',
            padx=5,
            pady=2,
            command=self.zoom_in
        ).pack(side='left')
        
        self.zoom_label = tk.Label(
            zoom_frame,
            text="100%",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['primary']
        )
        self.zoom_label.pack(side='left', padx=5)
        
        tk.Button(
            zoom_frame,
            text="🔍-",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            relief='flat',
            padx=5,
            pady=2,
            command=self.zoom_out
        ).pack(side='left')
    
    def create_context_menu(self):
        """Create context menu for text editor"""
        self.context_menu = tk.Menu(self.text_editor, tearoff=0)
        self.context_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        self.context_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        self.context_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        self.context_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        self.context_menu.add_command(label="Find & Replace", command=self.show_find_replace, accelerator="Ctrl+F")
        
        self.text_editor.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Show context menu"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def setup_syntax_highlighting(self):
        """Setup syntax highlighting tags"""
        # Define syntax highlighting colors
        colors = self.theme.get_colors()
        
        self.text_editor.tag_configure('keyword', foreground='#569cd6', font=('Consolas', 11, 'bold'))
        self.text_editor.tag_configure('string', foreground='#ce9178')
        self.text_editor.tag_configure('comment', foreground='#6a9955', font=('Consolas', 11, 'italic'))
        self.text_editor.tag_configure('number', foreground='#b5cea8')
        self.text_editor.tag_configure('function', foreground='#dcdcaa', font=('Consolas', 11, 'bold'))
        self.text_editor.tag_configure('class', foreground='#4ec9b0', font=('Consolas', 11, 'bold'))
    
    def sync_scroll(self, *args):
        """Synchronize scrolling between text editor and line numbers"""
        self.text_editor.yview(*args)
        self.line_numbers.yview(*args)
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_ctrl_mousewheel(self, event):
        """Handle Ctrl+mouse wheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_text_change(self, event=None):
        """Handle text changes"""
        self.update_line_numbers()
        if self.change_callback:
            self.change_callback()
    
    def update_line_numbers(self):
        """Update line numbers display"""
        line_count = int(self.text_editor.index('end-1c').split('.')[0])
        line_numbers_content = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert('1.0', line_numbers_content)
        self.line_numbers.config(state='disabled')
    
    def show_find_replace(self):
        """Show find and replace dialog"""
        if self.search_window and self.search_window.winfo_exists():
            self.search_window.lift()
            return
        
        self.search_window = tk.Toplevel(self.parent)
        self.search_window.title("Find & Replace")
        self.search_window.geometry("450x250")
        self.search_window.resizable(False, False)
        self.search_window.configure(bg=self.theme.get_colors()['bg'])
        self.search_window.transient(self.parent)
        
        # Center the window
        self.search_window.update_idletasks()
        x = (self.search_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.search_window.winfo_screenheight() // 2) - (250 // 2)
        self.search_window.geometry(f"450x250+{x}+{y}")
        
        # Find section
        find_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        find_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(find_frame, text="Find:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(anchor='w')
        self.find_entry = tk.Entry(find_frame, width=50, font=('Segoe UI', 10))
        self.find_entry.pack(fill='x', pady=(5, 0))
        
        # Replace section
        replace_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        replace_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(replace_frame, text="Replace:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(anchor='w')
        self.replace_entry = tk.Entry(replace_frame, width=50, font=('Segoe UI', 10))
        self.replace_entry.pack(fill='x', pady=(5, 0))
        
        # Options
        options_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        options_frame.pack(fill='x', padx=20, pady=10)
        
        self.case_sensitive_var = tk.BooleanVar()
        self.whole_word_var = tk.BooleanVar()
        self.regex_var = tk.BooleanVar()
        
        tk.Checkbutton(options_frame, text="Case sensitive", variable=self.case_sensitive_var,
                      bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left')
        tk.Checkbutton(options_frame, text="Whole word", variable=self.whole_word_var,
                      bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left', padx=(20, 0))
        tk.Checkbutton(options_frame, text="Regex", variable=self.regex_var,
                      bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(side='left', padx=(20, 0))
        
        # Buttons
        button_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Button(button_frame, text="Find Next", command=self.find_next,
                 bg=self.theme.get_colors()['primary'], fg='white', padx=15).pack(side='left')
        tk.Button(button_frame, text="Replace", command=self.replace_current,
                 bg=self.theme.get_colors()['info'], fg='white', padx=15).pack(side='left', padx=(10, 0))
        tk.Button(button_frame, text="Replace All", command=self.replace_all,
                 bg=self.theme.get_colors()['success'], fg='white', padx=15).pack(side='left', padx=(10, 0))
        tk.Button(button_frame, text="Close", command=self.close_search,
                 bg=self.theme.get_colors()['secondary'], fg='white', padx=15).pack(side='right')
        
        self.search_window.protocol("WM_DELETE_WINDOW", self.close_search)
        self.find_entry.focus()
        self.find_entry.bind('<Return>', lambda e: self.find_next())
        self.replace_entry.bind('<Return>', lambda e: self.replace_current())
    
    def find_next(self):
        """Find next occurrence"""
        search_term = self.find_entry.get()
        if not search_term:
            return
        
        # Get search options
        case_sensitive = self.case_sensitive_var.get()
        whole_word = self.whole_word_var.get()
        use_regex = self.regex_var.get()
        
        start_pos = self.text_editor.index(tk.INSERT)
        
        if use_regex:
            # Regex search
            import re
            flags = 0 if case_sensitive else re.IGNORECASE
            try:
                pattern = re.compile(search_term, flags)
            except re.error:
                messagebox.showerror("Error", "Invalid regular expression")
                return
            
            content = self.text_editor.get(start_pos, tk.END)
            match = pattern.search(content)
            if match:
                start_idx = start_pos + f"+{match.start()}c"
                end_idx = start_pos + f"+{match.end()}c"
                self.text_editor.tag_remove(tk.SEL, '1.0', tk.END)
                self.text_editor.tag_add(tk.SEL, start_idx, end_idx)
                self.text_editor.mark_set(tk.INSERT, end_idx)
                self.text_editor.see(start_idx)
        else:
            # Normal search
            pos = self.text_editor.search(search_term, start_pos, tk.END, nocase=not case_sensitive)
            if pos:
                end_pos = f"{pos}+{len(search_term)}c"
                self.text_editor.tag_remove(tk.SEL, '1.0', tk.END)
                self.text_editor.tag_add(tk.SEL, pos, end_pos)
                self.text_editor.mark_set(tk.INSERT, end_pos)
                self.text_editor.see(pos)
            else:
                messagebox.showinfo("Find", "No more occurrences found")
    
    def replace_current(self):
        """Replace current selection"""
        try:
            if self.text_editor.tag_ranges(tk.SEL):
                self.text_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.insert(tk.INSERT, self.replace_entry.get())
                self.find_next()
        except tk.TclError:
            self.find_next()
    
    def replace_all(self):
        """Replace all occurrences"""
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()
        if not search_term:
            return
        
        content = self.text_editor.get('1.0', tk.END)
        
        if self.regex_var.get():
            import re
            flags = 0 if self.case_sensitive_var.get() else re.IGNORECASE
            try:
                new_content, count = re.subn(search_term, replace_term, content, flags=flags)
            except re.error:
                messagebox.showerror("Error", "Invalid regular expression")
                return
        else:
            if self.case_sensitive_var.get():
                new_content = content.replace(search_term, replace_term)
            else:
                # Case-insensitive replace
                import re
                new_content = re.sub(re.escape(search_term), replace_term, content, flags=re.IGNORECASE)
            
            count = content.count(search_term)
        
        self.text_editor.delete('1.0', tk.END)
        self.text_editor.insert('1.0', new_content)
        
        messagebox.showinfo("Replace All", f"Replaced {count} occurrences")
    
    def close_search(self):
        """Close search dialog"""
        if self.search_window:
            self.search_window.destroy()
            self.search_window = None
    
    # Text editor operations
    def get_text(self):
        """Get all text from editor"""
        return self.text_editor.get('1.0', tk.END + '-1c')
    
    def set_text(self, text):
        """Set text in editor"""
        self.text_editor.delete('1.0', tk.END)
        self.text_editor.insert('1.0', text)
        self.update_line_numbers()
    
    def clear_text(self):
        """Clear all text"""
        self.text_editor.delete('1.0', tk.END)
        self.update_line_numbers()
    
    def undo(self):
        """Undo last action"""
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass
    
    def redo(self):
        """Redo last undone action"""
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass
    
    def cut(self):
        """Cut selected text"""
        self.text_editor.event_generate("<<Cut>>")
    
    def copy(self):
        """Copy selected text"""
        self.text_editor.event_generate("<<Copy>>")
    
    def paste(self):
        """Paste text from clipboard"""
        self.text_editor.event_generate("<<Paste>>")
    
    def select_all(self):
        """Select all text"""
        self.text_editor.tag_add(tk.SEL, "1.0", tk.END)
    
    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        if self.line_numbers.winfo_viewable():
            self.line_numbers.pack_forget()
        else:
            self.line_numbers.pack(side='left', fill='y', before=self.text_editor)
    
    def zoom_in(self):
        """Increase font size"""
        if self.zoom_level < 300:
            self.zoom_level += 10
            self.apply_zoom()
    
    def zoom_out(self):
        """Decrease font size"""
        if self.zoom_level > 50:
            self.zoom_level -= 10
            self.apply_zoom()
    
    def apply_zoom(self):
        """Apply current zoom level"""
        base_size = 11
        new_size = int(base_size * (self.zoom_level / 100))
        font = ('Consolas', new_size)
        
        self.text_editor.configure(font=font)
        self.line_numbers.configure(font=font)
        self.zoom_label.config(text=f"{self.zoom_level}%")
    
    def apply_settings(self, settings):
        """Apply editor settings"""
        font_family = settings.get('editor_font_family', 'Consolas')
        font_size = settings.get('editor_font_size', 11)
        
        # Apply font
        font = (font_family, font_size)
        self.text_editor.configure(font=font)
        self.line_numbers.configure(font=font)
        
        # Apply word wrap
        wrap_mode = 'word' if settings.get('editor_word_wrap', False) else 'none'
        self.text_editor.configure(wrap=wrap_mode)
        
        # Show/hide line numbers
        if settings.get('show_line_numbers', True):
            if not self.line_numbers.winfo_viewable():
                self.line_numbers.pack(side='left', fill='y', before=self.text_editor)
        else:
            if self.line_numbers.winfo_viewable():
                self.line_numbers.pack_forget()
    
    def set_change_callback(self, callback):
        """Set callback for text changes"""
        self.change_callback = callback
    
    def get_frame(self):
        """Get the main editor frame"""
        return self.editor_frame

# Enhanced PDFViewer class
class PDFViewer:
    """PDF viewer with navigation and zoom capabilities"""
    
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.current_pdf = None
        self.current_page = 0
        self.zoom_level = 1.0
        self.rotation = 0
        
        if HAS_PDF_SUPPORT:
            self.create_pdf_viewer()
        else:
            self.create_placeholder()
    
    def create_pdf_viewer(self):
        """Create PDF viewer interface"""
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        # Toolbar
        self.create_toolbar()
        
        # PDF display area
        display_frame = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['bg'])
        display_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.pdf_canvas = tk.Canvas(display_frame, bg='white', highlightthickness=0)
        
        # Scrollbars
        v_scrollbar = tk.Scrollbar(display_frame, orient='vertical', command=self.pdf_canvas.yview)
        h_scrollbar = tk.Scrollbar(display_frame, orient='horizontal', command=self.pdf_canvas.xview)
        
        self.pdf_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and canvas
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        self.pdf_canvas.pack(fill='both', expand=True)
        
        # Bind mouse events
        self.pdf_canvas.bind('<MouseWheel>', self.on_mousewheel)
        self.pdf_canvas.bind('<Control-MouseWheel>', self.on_ctrl_mousewheel)
        self.pdf_canvas.bind('<Button-1>', self.on_canvas_click)
    
    def create_toolbar(self):
        """Create PDF viewer toolbar"""
        toolbar = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['sidebar_bg'], height=50)
        toolbar.pack(fill='x', padx=10, pady=(10, 0))
        toolbar.pack_propagate(False)
        
        # File operations
        tk.Button(
            toolbar,
            text="📂 Open PDF",
            command=self.open_pdf,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=("Segoe UI", 10),
            padx=15,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=5, pady=10)
        
        # Navigation
        nav_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        nav_frame.pack(side='left', padx=20)
        
        tk.Button(
            nav_frame,
            text="⮜",
            command=self.prev_page,
            bg=self.theme.get_colors()['secondary'],
            fg='white',
            font=("Segoe UI", 12),
            padx=10,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        self.page_entry = tk.Entry(nav_frame, width=5, font=("Segoe UI", 10), justify='center')
        self.page_entry.pack(side='left', padx=5)
        self.page_entry.bind('<Return>', self.goto_page)
        
        self.page_label = tk.Label(
            nav_frame,
            text="/ 0",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg']
        )
        self.page_label.pack(side='left', padx=2)
        
        tk.Button(
            nav_frame,
            text="⮞",
            command=self.next_page,
            bg=self.theme.get_colors()['secondary'],
            fg='white',
            font=("Segoe UI", 12),
            padx=10,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        # Zoom controls
        zoom_frame = tk.Frame(toolbar, bg=self.theme.get_colors()['sidebar_bg'])
        zoom_frame.pack(side='left', padx=20)
        
        tk.Button(
            zoom_frame,
            text="🔍-",
            command=self.zoom_out,
            bg=self.theme.get_colors()['info'],
            fg='white',
            font=("Segoe UI", 10),
            padx=8,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        self.zoom_label = tk.Label(
            zoom_frame,
            text="100%",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['primary'],
            width=6
        )
        self.zoom_label.pack(side='left', padx=5)
        
        tk.Button(
            zoom_frame,
            text="🔍+",
            command=self.zoom_in,
            bg=self.theme.get_colors()['info'],
            fg='white',
            font=("Segoe UI", 10),
            padx=8,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=2)
        
        # Rotation
        tk.Button(
            toolbar,
            text="🔄",
            command=self.rotate_page,
            bg=self.theme.get_colors()['warning'],
            fg='white',
            font=("Segoe UI", 10),
            padx=10,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=(20, 5))
        
        # Status
        self.status_label = tk.Label(
            toolbar,
            text="No PDF loaded",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg']
        )
        self.status_label.pack(side='right', padx=10)
    
    def create_placeholder(self):
        """Create placeholder when PDF support is not available"""
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        placeholder_frame = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['bg'])
        placeholder_frame.pack(expand=True, fill='both')
        
        tk.Label(
            placeholder_frame,
            text="📄",
            font=("Segoe UI", 48),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['secondary']
        ).pack(expand=True, pady=(100, 20))
        
        tk.Label(
            placeholder_frame,
            text="PDF Viewer Not Available",
            font=("Segoe UI", 18, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(expand=True)
        
        tk.Label(
            placeholder_frame,
            text="Install PyMuPDF to enable PDF viewing:",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['secondary']
        ).pack(expand=True, pady=10)
        
        tk.Label(
            placeholder_frame,
            text="pip install PyMuPDF",
            font=("Consolas", 11, "bold"),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['primary'],
            padx=20,
            pady=10,
            relief='solid',
            bd=1
        ).pack(expand=True)
    
    def open_pdf(self):
        """Open PDF file"""
        if not HAS_PDF_SUPPORT:
            messagebox.showerror("Error", "PDF support not available. Install PyMuPDF.")
            return
        
        file_path = filedialog.askopenfilename(
            title="Open PDF",
            filetypes=[("PDF files", "*.pdf")]
        )
        
        if file_path:
            try:
                self.current_pdf = fitz.open(file_path)
                self.current_page = 0
                self.zoom_level = 1.0
                self.rotation = 0
                self.display_page()
                self.update_navigation()
                self.status_label.config(text=f"Loaded: {os.path.basename(file_path)}")
                logger.info(f"PDF opened: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF:\n{str(e)}")
                logger.error(f"PDF open error: {e}")
    
    def display_page(self):
        """Display current PDF page"""
        if not self.current_pdf:
            return
        
        try:
            page = self.current_pdf[self.current_page]
            
            # Apply rotation and zoom
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            if self.rotation != 0:
                mat = mat * fitz.Matrix(self.rotation)
            
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # Clear canvas and display image
            self.pdf_canvas.delete("all")
            self.pdf_image = tk.PhotoImage(data=img_data)
            
            # Center the image
            canvas_width = self.pdf_canvas.winfo_width()
            canvas_height = self.pdf_canvas.winfo_height()
            img_width = self.pdf_image.width()
            img_height = self.pdf_image.height()
            
            x = max(0, (canvas_width - img_width) // 2)
            y = max(0, (canvas_height - img_height) // 2)
            
            self.pdf_canvas.create_image(x, y, anchor='nw', image=self.pdf_image)
            self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))
            
            # Update zoom label
            self.zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not display page:\n{str(e)}")
            logger.error(f"PDF display error: {e}")
    
    def update_navigation(self):
        """Update navigation controls"""
        if self.current_pdf:
            total_pages = len(self.current_pdf)
            self.page_label.config(text=f"/ {total_pages}")
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(self.current_page + 1))
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_pdf and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
            self.update_navigation()
    
    def next_page(self):
        """Go to next page"""
        if self.current_pdf and self.current_page < len(self.current_pdf) - 1:
            self.current_page += 1
            self.display_page()
            self.update_navigation()
    
    def goto_page(self, event=None):
        """Go to specific page"""
        if not self.current_pdf:
            return
        
        try:
            page_num = int(self.page_entry.get()) - 1
            if 0 <= page_num < len(self.current_pdf):
                self.current_page = page_num
                self.display_page()
                self.update_navigation()
            else:
                messagebox.showerror("Error", f"Page number must be between 1 and {len(self.current_pdf)}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid page number")
    
    def zoom_in(self):
        """Increase zoom level"""
        if self.zoom_level < 5.0:
            self.zoom_level *= 1.25
            self.display_page()
    
    def zoom_out(self):
        """Decrease zoom level"""
        if self.zoom_level > 0.2:
            self.zoom_level /= 1.25
            self.display_page()
    
    def rotate_page(self):
        """Rotate page 90 degrees"""
        self.rotation = (self.rotation + 90) % 360
        self.display_page()
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.pdf_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_ctrl_mousewheel(self, event):
        """Handle Ctrl+mouse wheel for zooming"""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()
    
    def on_canvas_click(self, event):
        """Handle canvas click"""
        self.pdf_canvas.focus_set()
    
    def get_frame(self):
        """Get the main PDF viewer frame"""
        return self.pdf_frame

# Application entry point and main function
def main():
    """Main function to run the application"""
    try:
        # Set up logging
        setup_logging()
        
        # Create and run the application
        app = ModernApp()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        # Show error dialog if GUI fails
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Application Error",
                f"An error occurred while starting the application:\n\n{str(e)}\n\n"
                f"Please check that all dependencies are installed:\n"
                f"• pip install requests (for updates)\n"
                f"• pip install PyMuPDF (for PDF support)\n"
                f"• pip install reportlab (for PDF export)\n\n"
                f"Check the log file for more details: {LOG_FILE}"
            )
        except:
            # If even the error dialog fails, print to console
            print(f"Critical error: {e}")
            print("Please ensure Python and tkinter are properly installed.")
        
        logger.error(f"Application startup failed: {e}", exc_info=True)
        sys.exit(1)

import logging
import os
import sys

def setup_logging():
    """Set up application logging"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set up logger
    global logger
    logger = logging.getLogger(APP_NAME)
    logger.info("="*50)
    logger.info(f"{APP_NAME} v{CURRENT_VERSION} - Session Started")
    logger.info("="*50)
def safe_import_fitz():
    """Safely import fitz module"""
    try:
        import fitz
        return True
    except ImportError:
        return False

def safe_import_requests():
    """Safely import requests module"""
    try:
        import requests
        return True
    except ImportError:
        return False

def check_dependencies():
    """Check for optional dependencies and log status"""
    dependencies = {
        'requests': safe_import_requests(),
        'PyMuPDF': safe_import_fitz(),
        'reportlab': canvas is not None
    }
    
    logger.info("Dependency check:")
    for name, available in dependencies.items():
        status = "✓ Available" if available else "✗ Not available"
        logger.info(f"  {name}: {status}")
    
    return dependencies# Enhanced ConfigManager class
class ConfigManager:
    """Enhanced configuration manager with validation and defaults"""
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()
        self.default_config = self.get_default_config()
    
    def get_default_config(self):
        """Get default configuration"""
        return {
            # User preferences
            'user_name': '',
            'user_email': '',
            
            # Appearance
            'theme': 'dark',
            'window_geometry': '1200x800',
            'window_state': 'normal',
            
            # Editor settings
            'editor_font_family': 'Consolas',
            'editor_font_size': 11,
            'show_line_numbers': True,
            'editor_word_wrap': False,
            'editor_syntax_highlighting': True,
            
            # File management
            'auto_save': True,
            'auto_save_interval': 30,
            'create_backups': True,
            'max_recent_files': 10,
            'recent_files': [],
            
            # Updates
            'check_updates_on_startup': True,
            'last_update_check': '',
            
            # Advanced
            'debug_mode': False,
            'log_level': 'INFO'
        }
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded from {self.config_file}")
                    return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        # Return default config if loading fails
        return self.get_default_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure all default keys exist
            for key, value in self.default_config.items():
                if key not in self.config:
                    self.config[key] = value
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, self.default_config.get(key, default))
    
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
    
    def update(self, updates):
        """Update multiple configuration values"""
        self.config.update(updates)
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config = self.get_default_config().copy()
        return self.save_config()

# Enhanced FileManager class
class FileManager:
    """Enhanced file management with backup and recovery"""
    
    def __init__(self, config_manager):
        self.config = config_manager
        self.current_file = None
        self.unsaved_changes = False
        self.backup_dir = "backups"
        
        # Create backup directory
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def new_file(self):
        """Create new file"""
        if self.ask_save_changes():
            self.current_file = None
            self.unsaved_changes = False
            logger.info("New file created")
            return True
        return False
    
    def open_file(self, file_path=None):
        """Open file with dialog or specified path"""
        if not self.ask_save_changes():
            return None
        
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Open File",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("Python files", "*.py"),
                    ("JavaScript files", "*.js"),
                    ("HTML files", "*.html"),
                    ("CSS files", "*.css"),
                    ("JSON files", "*.json"),
                    ("Markdown files", "*.md"),
                    ("All files", "*.*")
                ]
            )
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.current_file = file_path
                self.unsaved_changes = False
                self.add_to_recent_files(file_path)
                logger.info(f"File opened: {file_path}")
                return content
                
            except Exception as e:
                logger.error(f"Error opening file {file_path}: {e}")
                messagebox.showerror("Error", f"Could not open file:\n{str(e)}")
        
        return None
    
    def save_file(self, content, file_path=None):
        """Save file with optional path"""
        if not file_path:
            file_path = self.current_file
        
        if not file_path:
            return self.save_file_as(content)
        
        try:
            # Create backup if file exists and backups are enabled
            if os.path.exists(file_path) and self.config.get('create_backups', True):
                self.create_backup(file_path)
            
            # Save file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.current_file = file_path
            self.unsaved_changes = False
            self.add_to_recent_files(file_path)
            logger.info(f"File saved: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving file {file_path}: {e}")
            messagebox.showerror("Error", f"Could not save file:\n{str(e)}")
            return False
    
    def save_file_as(self, content):
        """Save file with new name"""
        file_path = filedialog.asksaveasfilename(
            title="Save File As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Python files", "*.py"),
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JSON files", "*.json"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            return self.save_file(content, file_path)
        return False
    
    def create_backup(self, file_path):
        """Create backup of file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.basename(file_path)
            backup_name = f"{filename}.{timestamp}.backup"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            
            # Clean old backups (keep last 10)
            self.cleanup_old_backups(filename)
            
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
    
    def cleanup_old_backups(self, filename, keep_count=10):
        """Clean up old backup files"""
        try:
            # Find all backups for this file
            pattern = f"{filename}.*.backup"
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.startswith(filename) and file.endswith('.backup'):
                    backup_path = os.path.join(self.backup_dir, file)
                    backups.append((backup_path, os.path.getmtime(backup_path)))
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old backups
            for backup_path, _ in backups[keep_count:]:
                os.remove(backup_path)
                logger.info(f"Old backup removed: {backup_path}")
                
        except Exception as e:
            logger.warning(f"Error cleaning up backups: {e}")
    
    def add_to_recent_files(self, file_path):
        """Add file to recent files list"""
        recent_files = self.config.get('recent_files', [])
        max_recent = self.config.get('max_recent_files', 10)
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Keep only specified number of files
        recent_files = recent_files[:max_recent]
        
        # Update config
        self.config.set('recent_files', recent_files)
        self.config.save_config()
    
    def get_recent_files(self):
        """Get list of recent files (only existing ones)"""
        recent_files = self.config.get('recent_files', [])
        return [f for f in recent_files if os.path.exists(f)]
    
    def ask_save_changes(self):
        """Ask user to save changes if there are any"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before continuing?"
            )
            
            if result is True:  # Yes - save
                # This would be handled by the calling code
                return True
            elif result is False:  # No - don't save
                return True
            else:  # Cancel
                return False
        
        return True
    
    def set_unsaved_changes(self, has_changes):
        """Set unsaved changes flag"""
        self.unsaved_changes = has_changes
    
    def get_file_info(self):
        """Get information about current file"""
        if not self.current_file:
            return {
                'name': 'Untitled',
                'path': None,
                'size': 0,
                'modified': None,
                'extension': None
            }
        
        try:
            stat = os.stat(self.current_file)
            return {
                'name': os.path.basename(self.current_file),
                'path': self.current_file,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': os.path.splitext(self.current_file)[1]
            }
        except:
            return {
                'name': os.path.basename(self.current_file),
                'path': self.current_file,
                'size': 0,
                'modified': None,
                'extension': os.path.splitext(self.current_file)[1]
            }

# Application constants and final setup
LOG_FILE = "logs/app.log"

# Initialize logger as None (will be set up in setup_logging)
logger = None

if __name__ == "__main__":
    main()
