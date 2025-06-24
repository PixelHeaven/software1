import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext
import requests
import subprocess
import sys
import os
import json
import threading
import webbrowser
from datetime import datetime
import tempfile


# Version and configuration
CURRENT_VERSION = "1.0.2"
VERSION_URL = "https://raw.githubusercontent.com/PixelHeaven/software1/main/version.json"
APP_NAME = "Advanced Text & PDF Editor"
CONFIG_FILE = "config.json"

# Optional dependencies
try:
    import fitz  # PyMuPDF
    HAS_PDF_SUPPORT = True
except ImportError:
    HAS_PDF_SUPPORT = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_PDF_EXPORT = True
except ImportError:
    HAS_PDF_EXPORT = False

class ThemeManager:
    def __init__(self):
        self.themes = {
            'dark': {
                'bg': '#2b2b2b',
                'fg': '#ffffff',
                'select_bg': '#404040',
                'select_fg': '#ffffff',
                'primary': '#0078d4',
                'secondary': '#ffc107',
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#fd7e14',
                'editor_bg': '#1e1e1e',
                'editor_fg': '#d4d4d4',
                'sidebar_bg': '#252526',
                'tab_bg': '#2d2d30'
            },
            'light': {
                'bg': '#f0f0f0',
                'fg': '#000000',
                'select_bg': '#e3f2fd',
                'select_fg': '#000000',
                'primary': '#2196f3',
                'secondary': '#ff9800',
                'success': '#4caf50',
                'danger': '#f44336',
                'warning': '#ff5722',
                'editor_bg': '#ffffff',
                'editor_fg': '#000000',
                'sidebar_bg': '#fafafa',
                'tab_bg': '#e0e0e0'
            }
        }
        self.current_theme = 'dark'
    
    def get_colors(self):
        return self.themes[self.current_theme]
    
    def switch_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
    
    def apply_theme_to_widget(self, widget):
        colors = self.get_colors()
        try:
            widget.configure(bg=colors['bg'])
        except:
            pass

class AdvancedTextEditor:
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.search_window = None
        self.current_search = ""
        self.search_index = "1.0"
        
        # Create editor frame
        self.editor_frame = tk.Frame(parent, bg=self.theme.get_colors()['bg'])
        
        # Create text editor with line numbers
        self.create_editor()
        
        # Language for syntax highlighting
        self.language_var = tk.StringVar(value='text')
        self.setup_syntax_highlighting()
    
    def create_editor(self):
        # Editor container
        editor_container = tk.Frame(self.editor_frame, bg=self.theme.get_colors()['bg'])
        editor_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Line numbers frame
        line_frame = tk.Frame(editor_container, bg=self.theme.get_colors()['editor_bg'], width=50)
        line_frame.pack(side='left', fill='y')
        line_frame.pack_propagate(False)
        
        self.line_numbers = tk.Text(
            line_frame,
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
        self.line_numbers.pack(fill='y', expand=True)
        
        # Text editor
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
            maxundo=50
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
        
        # Context menu
        self.create_context_menu()
        
        # Update line numbers initially
        self.update_line_numbers()
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.text_editor, tearoff=0)
        self.context_menu.add_command(label="Cut", command=lambda: self.text_editor.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Copy", command=lambda: self.text_editor.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Paste", command=lambda: self.text_editor.event_generate("<<Paste>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Select All", command=lambda: self.text_editor.tag_add(tk.SEL, "1.0", tk.END))
        
        self.text_editor.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def sync_scroll(self, *args):
        self.text_editor.yview(*args)
        self.line_numbers.yview(*args)
    
    def on_mousewheel(self, event):
        self.line_numbers.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def on_text_change(self, event=None):
        self.update_line_numbers()
        if hasattr(self.parent.master, 'on_text_change'):
            self.parent.master.on_text_change()
    
    def update_line_numbers(self):
        line_count = int(self.text_editor.index('end-1c').split('.')[0])
        line_numbers_content = '\n'.join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', 'end')
        self.line_numbers.insert('1.0', line_numbers_content)
        self.line_numbers.config(state='disabled')
    
    def setup_syntax_highlighting(self):
        # Define syntax highlighting tags
        self.text_editor.tag_configure('keyword', foreground='#569cd6')
        self.text_editor.tag_configure('string', foreground='#ce9178')
        self.text_editor.tag_configure('comment', foreground='#6a9955')
        self.text_editor.tag_configure('number', foreground='#b5cea8')
        self.text_editor.tag_configure('constant', foreground='#4fc1ff')
    
    def apply_syntax_highlighting(self):
        language = self.language_var.get()
        if language == 'python':
            self.highlight_python()
    
    def highlight_python(self):
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'import', 'from', 'return', 'break', 'continue']
        content = self.text_editor.get('1.0', 'end')
        
        # Clear existing tags
        for tag in ['keyword', 'string', 'comment', 'number']:
            self.text_editor.tag_remove(tag, '1.0', 'end')
        
        # Highlight keywords
        for keyword in keywords:
            start = '1.0'
            while True:
                pos = self.text_editor.search(keyword, start, 'end')
                if not pos:
                    break
                end = f"{pos}+{len(keyword)}c"
                self.text_editor.tag_add('keyword', pos, end)
                start = end
    
    def show_replace_dialog(self):
        if self.search_window:
            self.search_window.lift()
            return
        
        self.search_window = tk.Toplevel(self.parent)
        self.search_window.title("Find & Replace")
        self.search_window.geometry("400x200")
        self.search_window.resizable(False, False)
        self.search_window.configure(bg=self.theme.get_colors()['bg'])
        
        # Find section
        tk.Label(self.search_window, text="Find:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(pady=5)
        self.find_entry = tk.Entry(self.search_window, width=40, font=('Segoe UI', 10))
        self.find_entry.pack(pady=5)
        
        # Replace section
        tk.Label(self.search_window, text="Replace:", bg=self.theme.get_colors()['bg'], fg=self.theme.get_colors()['fg']).pack(pady=5)
        self.replace_entry = tk.Entry(self.search_window, width=40, font=('Segoe UI', 10))
        self.replace_entry.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.search_window, bg=self.theme.get_colors()['bg'])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Find Next", command=self.find_next).pack(side='left', padx=5)
        tk.Button(button_frame, text="Replace", command=self.replace_current).pack(side='left', padx=5)
        tk.Button(button_frame, text="Replace All", command=self.replace_all).pack(side='left', padx=5)
        
        self.search_window.protocol("WM_DELETE_WINDOW", self.close_search)
        self.find_entry.focus()
    
    def find_next(self):
        search_term = self.find_entry.get()
        if not search_term:
            return
        
        start_pos = self.text_editor.index(tk.INSERT)
        pos = self.text_editor.search(search_term, start_pos, 'end')
        
        if pos:
            end_pos = f"{pos}+{len(search_term)}c"
            self.text_editor.tag_remove(tk.SEL, '1.0', 'end')
            self.text_editor.tag_add(tk.SEL, pos, end_pos)
            self.text_editor.mark_set(tk.INSERT, end_pos)
            self.text_editor.see(pos)
    
    def replace_current(self):
        try:
            if self.text_editor.tag_ranges(tk.SEL):
                self.text_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.text_editor.insert(tk.INSERT, self.replace_entry.get())
        except tk.TclError:
            pass
    
    def replace_all(self):
        search_term = self.find_entry.get()
        replace_term = self.replace_entry.get()
        if not search_term:
            return
        
        content = self.text_editor.get('1.0', 'end')
        new_content = content.replace(search_term, replace_term)
        
        self.text_editor.delete('1.0', 'end')
        self.text_editor.insert('1.0', new_content)
    
    def close_search(self):
        self.search_window.destroy()
        self.search_window = None
    
    def toggle_line_numbers(self):
        if self.line_numbers.winfo_viewable():
            self.line_numbers.pack_forget()
        else:
            self.line_numbers.pack(side='left', fill='y')
    
    def get_frame(self):
        return self.editor_frame

class PDFViewer:
    def __init__(self, parent, theme_manager):
        self.parent = parent
        self.theme = theme_manager
        self.current_pdf = None
        self.current_page = 0
        self.zoom_level = 1.0
        
        if HAS_PDF_SUPPORT:
            self.create_pdf_viewer()
        else:
            self.create_placeholder()
    
    def create_pdf_viewer(self):
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        # Toolbar
        toolbar = tk.Frame(self.pdf_frame, bg=self.theme.get_colors()['sidebar_bg'], height=50)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        tk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side='left', padx=5, pady=10)
        tk.Button(toolbar, text="Previous", command=self.prev_page).pack(side='left', padx=5)
        tk.Button(toolbar, text="Next", command=self.next_page).pack(side='left', padx=5)
        tk.Button(toolbar, text="Zoom In", command=self.zoom_in).pack(side='left', padx=5)
        tk.Button(toolbar, text="Zoom Out", command=self.zoom_out).pack(side='left', padx=5)
        
        self.page_label = tk.Label(toolbar, text="No PDF loaded", bg=self.theme.get_colors()['sidebar_bg'], fg=self.theme.get_colors()['fg'])
        self.page_label.pack(side='right', padx=10)
        
        # PDF display area
        self.pdf_canvas = tk.Canvas(self.pdf_frame, bg='white')
        pdf_scrollbar_v = tk.Scrollbar(self.pdf_frame, orient='vertical', command=self.pdf_canvas.yview)
        pdf_scrollbar_h = tk.Scrollbar(self.pdf_frame, orient='horizontal', command=self.pdf_canvas.xview)
        
        self.pdf_canvas.configure(yscrollcommand=pdf_scrollbar_v.set, xscrollcommand=pdf_scrollbar_h.set)
        
        pdf_scrollbar_v.pack(side='right', fill='y')
        pdf_scrollbar_h.pack(side='bottom', fill='x')
        self.pdf_canvas.pack(fill='both', expand=True)
    
    def create_placeholder(self):
        self.pdf_frame = tk.Frame(self.parent, bg=self.theme.get_colors()['bg'])
        
        tk.Label(
            self.pdf_frame,
            text="PDF Viewer Not Available",
            font=("Segoe UI", 16, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(expand=True)
        
        tk.Label(
            self.pdf_frame,
            text="Install PyMuPDF to enable PDF viewing:\npip install PyMuPDF",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            justify=tk.CENTER
        ).pack(expand=True)
    
    def open_pdf(self):
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
                self.display_page()
            except Exception as e:
                messagebox.showerror("Error", f"Could not open PDF: {str(e)}")
    
    def display_page(self):
        if not self.current_pdf:
            return
        
        try:
            page = self.current_pdf[self.current_page]
            mat = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            
            # Update canvas
            self.pdf_canvas.delete("all")
            self.pdf_image = tk.PhotoImage(data=img_data)
            self.pdf_canvas.create_image(0, 0, anchor='nw', image=self.pdf_image)
            self.pdf_canvas.configure(scrollregion=self.pdf_canvas.bbox("all"))
            
            # Update page label
            self.page_label.config(text=f"Page {self.current_page + 1} of {len(self.current_pdf)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not display page: {str(e)}")
    
    def prev_page(self):
        if self.current_pdf and self.current_page > 0:
            self.current_page -= 1
            self.display_page()
    
    def next_page(self):
        if self.current_pdf and self.current_page < len(self.current_pdf) - 1:
            self.current_page += 1
            self.display_page()
    
    def zoom_in(self):
        self.zoom_level *= 1.2
        self.display_page()
    
    def zoom_out(self):
        self.zoom_level /= 1.2
        self.display_page()
    
    def get_frame(self):
        return self.pdf_frame

class ModernApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{CURRENT_VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize theme manager
        self.theme = ThemeManager()
        
        # App icon
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Configuration
        self.config = self.load_config()
        self.theme.switch_theme(self.config.get('theme', 'dark'))
        
        # File management
        self.current_file = None
        self.unsaved_changes = False
        
        # Create interface
        self.create_menu()
        self.create_modern_interface()
        self.create_status_bar()
        
        # Check for updates on startup
        if self.config.get('check_updates_on_startup', True):
            self.root.after(2000, self.check_for_updates_silent)
        
        # Start document stats updater
        self.root.after(1000, self.update_document_stats)
    
    def create_modern_interface(self):
        """Create modern interface with sidebar and main content"""
        # Main container
        main_container = tk.Frame(self.root, bg=self.theme.get_colors()['bg'])
        main_container.pack(fill='both', expand=True)
        
        # Sidebar
        self.create_sidebar(main_container)
        
        # Main content area
        content_frame = tk.Frame(main_container, bg=self.theme.get_colors()['bg'])
        content_frame.pack(side='right', fill='both', expand=True)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_home_tab()
        self.create_editor_tab()
        if HAS_PDF_SUPPORT:
            self.create_pdf_tab()
        self.create_enhanced_settings_tab()
        
        # Progress frame (hidden by default)
        self.progress_frame = tk.Frame(content_frame, bg=self.theme.get_colors()['bg'])
        self.progress_label = tk.Label(
            self.progress_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        )
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='indeterminate',
            length=400
        )
    
    def create_sidebar(self, parent):
        """Create sidebar with navigation and stats"""
        sidebar = tk.Frame(parent, bg=self.theme.get_colors()['sidebar_bg'], width=250)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        
        # App logo/title
        title_frame = tk.Frame(sidebar, bg=self.theme.get_colors()['primary'], height=80)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text=APP_NAME,
            font=("Segoe UI", 14, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=20)
        
        # Quick actions
        actions_frame = tk.LabelFrame(
            sidebar,
            text="Quick Actions",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        actions_frame.pack(fill='x', padx=10, pady=10)
        
        # Action buttons
        actions = [
            ("📄 New File", self.new_file),
            ("📂 Open File", self.open_file),
            ("💾 Save File", self.save_file),
            ("🔍 Find", self.show_find_replace)
        ]
        
        for text, command in actions:
            btn = tk.Button(
                actions_frame,
                text=text,
                command=command,
                bg=self.theme.get_colors()['select_bg'],
                fg=self.theme.get_colors()['fg'],
                font=("Segoe UI", 9),
                relief='flat',
                padx=10,
                pady=5,
                anchor='w'
            )
            btn.pack(fill='x', pady=2)
        
        # Document stats
        stats_frame = tk.LabelFrame(
            sidebar,
            text="Document Stats",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = tk.Label(
            stats_frame,
            text="Lines: 0\nWords: 0\nCharacters: 0",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            justify='left'
        )
        self.stats_label.pack(anchor='w')
        
        # Recent files
        recent_frame = tk.LabelFrame(
            sidebar,
            text="Recent Files",
            font=("Segoe UI", 10, "bold"),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            padx=10,
            pady=10
        )
        recent_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.recent_listbox = tk.Listbox(
            recent_frame,
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg'],
            font=("Segoe UI", 9),
            selectbackground=self.theme.get_colors()['primary'],
            relief='flat',
            height=6
        )
        self.recent_listbox.pack(fill='both', expand=True)
        self.recent_listbox.bind('<Double-Button-1>', self.open_recent_from_list)
        
        self.update_recent_files_list()
    
    def create_home_tab(self):
        """Create enhanced home tab"""
        home_tab = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(home_tab, text="🏠 Home")
        
        # Scrollable content
        canvas = tk.Canvas(home_tab, bg=self.theme.get_colors()['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(home_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.get_colors()['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Welcome section
        welcome_frame = tk.Frame(scrollable_frame, bg=self.theme.get_colors()['primary'], height=150)
        welcome_frame.pack(fill='x', padx=20, pady=20)
        welcome_frame.pack_propagate(False)
        
        tk.Label(
            welcome_frame,
            text=f"Welcome to {APP_NAME}! 🎉",
            font=("Segoe UI", 20, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=30)
        
        tk.Label(
            welcome_frame,
            text=f"Version {CURRENT_VERSION} • Modern Text & PDF Editor",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack()
        
        # Features section
        features_frame = tk.Frame(scrollable_frame, bg=self.theme.get_colors()['bg'])
        features_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            features_frame,
            text="Features & Capabilities",
            font=("Segoe UI", 16, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=(0, 20))
        
        # Feature cards using pack layout
        features = [
            ("📝 Advanced Text Editor", "Syntax highlighting, find & replace, line numbers", self.theme.get_colors()['success']),
            ("📄 PDF Viewer", "View PDF documents with zoom and navigation", self.theme.get_colors()['primary']),
            ("🎨 Modern Themes", "Dark and light themes with professional styling", self.theme.get_colors()['secondary']),
            ("🔄 Auto-Updates", "Automatic update checking and installation", self.theme.get_colors()['warning']),
            ("💾 Smart Saving", "Auto-save, backup creation, recent files", self.theme.get_colors()['success']),
            ("⚙️ Customizable", "Fonts, themes, editor preferences", self.theme.get_colors()['primary'])
        ]
        
        # Create rows of feature cards
        for i in range(0, len(features), 2):
            row_frame = tk.Frame(features_frame, bg=self.theme.get_colors()['bg'])
            row_frame.pack(fill='x', pady=5)
            
            # First card in row
            if i < len(features):
                title, desc, color = features[i]
                card_frame = tk.Frame(
                    row_frame,
                    bg=color,
                    relief='raised',
                    bd=1
                )
                card_frame.pack(side='left', fill='both', expand=True, padx=(0, 5))
                
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
                    wraplength=250
                ).pack(pady=(0, 15), padx=15)
            
            # Second card in row
            if i + 1 < len(features):
                title, desc, color = features[i + 1]
                card_frame = tk.Frame(
                    row_frame,
                    bg=color,
                    relief='raised',
                    bd=1
                )
                card_frame.pack(side='right', fill='both', expand=True, padx=(5, 0))
                
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
                    wraplength=250
                ).pack(pady=(0, 15), padx=15)
        
        # Getting started section
        getting_started_frame = tk.LabelFrame(
            scrollable_frame,
            text="Getting Started",
            font=("Segoe UI", 14, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=20,
            pady=20
        )
        getting_started_frame.pack(fill='x', padx=20, pady=20)
        
        steps = [
            "1. 📄 Create a new file or open an existing one",
            "2. ✏️ Use the advanced editor with syntax highlighting",
            "3. 📋 Export your work to PDF format",
            "4. ⚙️ Customize themes and settings to your preference",
            "5. 🔄 Keep your app updated automatically"
        ]
        
        for step in steps:
            tk.Label(
                getting_started_frame,
                text=step,
                font=("Segoe UI", 11),
                bg=self.theme.get_colors()['bg'],
                fg=self.theme.get_colors()['fg'],
                anchor='w'
            ).pack(fill='x', pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return home_tab
    
    def create_editor_tab(self):
        """Create advanced editor tab"""
        editor_tab = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(editor_tab, text="📝 Editor")
        
        # Editor toolbar
        toolbar = tk.Frame(editor_tab, bg=self.theme.get_colors()['tab_bg'], height=50)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # File operations
        file_buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Save As", self.save_file_as)
        ]
        
        for text, command in file_buttons:
            tk.Button(
                toolbar,
                text=text,
                command=command,
                bg=self.theme.get_colors()['select_bg'],
                fg=self.theme.get_colors()['fg'],
                font=("Segoe UI", 9),
                relief='flat',
                padx=15,
                pady=5
            ).pack(side='left', padx=2, pady=10)
        
        # Separator
        tk.Frame(toolbar, bg=self.theme.get_colors()['fg'], width=1).pack(side='left', fill='y', padx=10, pady=5)
        
        # Edit operations
        edit_buttons = [
            ("Find", self.show_find_replace),
            ("Word Count", self.show_word_count)
        ]
        
        if HAS_PDF_EXPORT:
            edit_buttons.append(("Export PDF", self.export_to_pdf))
        
        for text, command in edit_buttons:
            tk.Button(
                toolbar,
                text=text,
                command=command,
                bg=self.theme.get_colors()['select_bg'],
                fg=self.theme.get_colors()['fg'],
                font=("Segoe UI", 9),
                relief='flat',
                padx=15,
                pady=5
            ).pack(side='left', padx=2, pady=10)
        
        # Language selector
        tk.Label(
            toolbar,
            text="Language:",
            bg=self.theme.get_colors()['tab_bg'],
            fg=self.theme.get_colors()['fg'],
            font=("Segoe UI", 9)
        ).pack(side='right', padx=(10, 5), pady=10)
        
        # Create advanced text editor
        self.advanced_editor = AdvancedTextEditor(editor_tab, self.theme)
        self.advanced_editor.get_frame().pack(fill='both', expand=True)
        
        return editor_tab
    
    def create_pdf_tab(self):
        """Create PDF viewer tab"""
        pdf_tab = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(pdf_tab, text="📄 PDF Viewer")
        
        # Create PDF viewer
        self.pdf_viewer = PDFViewer(pdf_tab, self.theme)
        self.pdf_viewer.get_frame().pack(fill='both', expand=True)
        
        return pdf_tab
    
    def create_enhanced_settings_tab(self):
        """Create enhanced settings tab"""
        settings_tab = tk.Frame(self.notebook, bg=self.theme.get_colors()['bg'])
        self.notebook.add(settings_tab, text="⚙️ Settings")
        
        # Scrollable settings
        canvas = tk.Canvas(settings_tab, bg=self.theme.get_colors()['bg'], highlightthickness=0)
        scrollbar = tk.Scrollbar(settings_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.theme.get_colors()['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Settings header
        header_frame = tk.Frame(scrollable_frame, bg=self.theme.get_colors()['primary'], height=80)
        header_frame.pack(fill='x', padx=20, pady=20)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="⚙️ Application Settings",
            font=("Segoe UI", 18, "bold"),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=20)
        
        # User preferences
        user_frame = tk.LabelFrame(
            scrollable_frame,
            text="User Preferences",
            font=("Segoe UI", 12, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        user_frame.pack(fill='x', padx=20, pady=10)
        
        # User name setting
        name_row = tk.Frame(user_frame, bg=self.theme.get_colors()['bg'])
        name_row.pack(fill='x', pady=10)
        
        tk.Label(
            name_row,
            text="Display Name:",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(side='left')
        
        self.name_var = tk.StringVar(value=self.config.get('user_name', ''))
        name_entry = tk.Entry(
            name_row,
            textvariable=self.name_var,
            font=("Segoe UI", 10),
            width=30,
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        )
        name_entry.pack(side='left', padx=(20, 0))
        name_entry.bind('<KeyRelease>', self.on_name_change)
        
        # Theme settings
        theme_frame = tk.LabelFrame(
            scrollable_frame,
            text="Appearance",
            font=("Segoe UI", 12, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        theme_frame.pack(fill='x', padx=20, pady=10)
        
        theme_row = tk.Frame(theme_frame, bg=self.theme.get_colors()['bg'])
        theme_row.pack(fill='x', pady=10)
        
        tk.Label(
            theme_row,
            text="Theme:",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(side='left')
        
        self.theme_var = tk.StringVar(value=self.config.get('theme', 'dark'))
        theme_combo = ttk.Combobox(
            theme_row,
            textvariable=self.theme_var,
            values=['dark', 'light'],
            width=15,
            font=("Segoe UI", 10)
        )
        theme_combo.pack(side='left', padx=(20, 0))
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self.on_theme_change())
        
        self.theme_indicator = tk.Label(
            theme_row,
            text=f"Current: {self.theme.current_theme.title()}",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
        )
        self.theme_indicator.pack(side='left', padx=(20, 0))
        
        # Editor settings
        editor_frame = tk.LabelFrame(
            scrollable_frame,
            text="Editor Settings",
            font=("Segoe UI", 12, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        editor_frame.pack(fill='x', padx=20, pady=10)
        
        # Font family
        font_family_row = tk.Frame(editor_frame, bg=self.theme.get_colors()['bg'])
        font_family_row.pack(fill='x', pady=5)
        
        tk.Label(
            font_family_row,
            text="Font Family:",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(side='left')
        
        self.font_family_var = tk.StringVar(value=self.config.get('editor_font_family', 'Consolas'))
        font_combo = ttk.Combobox(
            font_family_row,
            textvariable=self.font_family_var,
            values=['Consolas', 'Courier New', 'Monaco', 'Source Code Pro', 'Fira Code'],
            width=15,
            font=("Segoe UI", 10)
        )
        font_combo.pack(side='left', padx=(20, 0))
        font_combo.bind('<<ComboboxSelected>>', self.on_font_change)
        
        # Font size
        font_size_row = tk.Frame(editor_frame, bg=self.theme.get_colors()['bg'])
        font_size_row.pack(fill='x', pady=5)
        
        tk.Label(
            font_size_row,
            text="Font Size:",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(side='left')
        
        self.font_size_var = tk.IntVar(value=self.config.get('editor_font_size', 11))
        font_size_spinbox = tk.Spinbox(
            font_size_row,
            from_=8,
            to=24,
            textvariable=self.font_size_var,
            width=5,
            font=("Segoe UI", 10),
            command=self.on_font_change
        )
        font_size_spinbox.pack(side='left', padx=(20, 0))
        
        # Auto-save setting
        autosave_row = tk.Frame(editor_frame, bg=self.theme.get_colors()['bg'])
        autosave_row.pack(fill='x', pady=10)
        
        self.auto_save_var = tk.BooleanVar(value=self.config.get('auto_save', True))
        auto_save_cb = tk.Checkbutton(
            autosave_row,
            text="Enable auto-save",
            variable=self.auto_save_var,
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg'],
            command=self.on_auto_save_change
        )
        auto_save_cb.pack(side='left')
        
        # Update settings
        update_frame = tk.LabelFrame(
            scrollable_frame,
            text="Update Settings",
            font=("Segoe UI", 12, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            padx=15,
            pady=15
        )
        update_frame.pack(fill='x', padx=20, pady=10)
        
        self.auto_update_var = tk.BooleanVar(value=self.config.get('check_updates_on_startup', True))
        auto_update_cb = tk.Checkbutton(
            update_frame,
            text="Check for updates on startup",
            variable=self.auto_update_var,
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            activebackground=self.theme.get_colors()['bg'],
                        command=self.on_auto_update_change
        )
        auto_update_cb.pack(anchor='w', pady=5)
        
        # Manual update check button
        update_btn = tk.Button(
            update_frame,
            text="🔄 Check for Updates Now",
            command=self.check_for_updates_threaded,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=("Segoe UI", 10, "bold"),
            padx=20,
            pady=8,
            relief='flat',
            cursor='hand2'
        )
        update_btn.pack(pady=5)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        return settings_tab
    
    def load_config(self):
        """Load application configuration"""
        default_config = {
            'check_updates_on_startup': True,
            'theme': 'dark',
            'last_update_check': '',
            'user_name': '',
            'auto_save': True,
            'editor_font_family': 'Consolas',
            'editor_font_size': 11,
            'recent_files': [],
            'window_geometry': '1200x800',
            'window_state': 'normal'
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
            # Save window geometry
            self.config['window_geometry'] = self.root.geometry()
            self.config['window_state'] = self.root.state()
            
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
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace", command=self.show_find_replace, accelerator="Ctrl+F")
        edit_menu.add_command(label="Word Count", command=self.show_word_count)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Line Numbers", command=self.toggle_line_numbers)
        view_menu.add_separator()
        view_menu.add_command(label="Dark Theme", command=lambda: self.switch_theme('dark'))
        view_menu.add_command(label="Light Theme", command=lambda: self.switch_theme('light'))
        
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
        self.root.bind('<Control-Shift-S>', lambda e: self.save_file_as())
        self.root.bind('<Control-f>', lambda e: self.show_find_replace())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_frame = tk.Frame(self.root, bg=self.theme.get_colors()['sidebar_bg'], height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['fg'],
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Version label
        version_label = tk.Label(
            self.status_frame,
            text=f"v{CURRENT_VERSION}",
            font=("Segoe UI", 9),
            bg=self.theme.get_colors()['sidebar_bg'],
            fg=self.theme.get_colors()['primary']
        )
        version_label.pack(side='right', padx=10, pady=5)
    
    def set_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def show_progress(self, message):
        """Show progress indicator"""
        self.progress_label.config(text=message)
        self.progress_frame.pack(fill='x', pady=(0, 10))
        self.progress_label.pack()
        self.progress_bar.pack(pady=(5, 0))
        self.progress_bar.start(10)
        self.root.update_idletasks()
    
    def hide_progress(self):
        """Hide progress indicator"""
        self.progress_bar.stop()
        self.progress_frame.pack_forget()
    
    # File operations
    def new_file(self):
        """Create new file"""
        if self.unsaved_changes:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Continue?"):
                return
        
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.text_editor.delete(1.0, tk.END)
        self.current_file = None
        self.unsaved_changes = False
        self.set_status("New file created")
        self.root.title(f"{APP_NAME} v{CURRENT_VERSION} - Untitled")
    
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
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.load_file(file_path)
    
    def load_file(self, file_path):
        """Load file content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if hasattr(self, 'advanced_editor'):
                self.advanced_editor.text_editor.delete(1.0, tk.END)
                self.advanced_editor.text_editor.insert(1.0, content)
            
            self.current_file = file_path
            self.unsaved_changes = False
            self.add_to_recent_files(file_path)
            self.set_status(f"Opened: {os.path.basename(file_path)}")
            self.root.title(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(file_path)}")
            
            # Set language for syntax highlighting
            if hasattr(self, 'advanced_editor'):
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.py':
                    self.advanced_editor.language_var.set('python')
                    self.advanced_editor.apply_syntax_highlighting()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{str(e)}")
    
    def save_file(self):
        """Save file"""
        if not self.current_file:
            self.save_file_as()
        else:
            try:
                content = ""
                if hasattr(self, 'advanced_editor'):
                    content = self.advanced_editor.text_editor.get(1.0, tk.END)
                
                # Create backup
                if os.path.exists(self.current_file):
                    backup_path = self.current_file + '.backup'
                    import shutil
                    shutil.copy2(self.current_file, backup_path)
                
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.unsaved_changes = False
                self.set_status(f"Saved: {os.path.basename(self.current_file)}")
                self.root.title(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)}")
                
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
                ("JavaScript files", "*.js"),
                ("HTML files", "*.html"),
                ("CSS files", "*.css"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                content = ""
                if hasattr(self, 'advanced_editor'):
                    content = self.advanced_editor.text_editor.get(1.0, tk.END)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.current_file = file_path
                self.unsaved_changes = False
                self.add_to_recent_files(file_path)
                self.set_status(f"Saved as: {os.path.basename(file_path)}")
                self.root.title(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{str(e)}")
    
    def export_to_pdf(self):
        """Export text to PDF"""
        if not HAS_PDF_EXPORT:
            messagebox.showerror("Error", "PDF export not available. Install ReportLab: pip install reportlab")
            return
        
        if not hasattr(self, 'advanced_editor'):
            messagebox.showerror("Error", "No text editor available")
            return
        
        content = self.advanced_editor.text_editor.get(1.0, tk.END).strip()
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
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.units import inch
                
                c = canvas.Canvas(file_path, pagesize=letter)
                width, height = letter
                
                # Set up text
                text_object = c.beginText(inch, height - inch)
                text_object.setFont("Courier", 10)
                
                # Add content line by line
                lines = content.split('\n')
                for line in lines:
                    text_object.textLine(line)
                
                c.drawText(text_object)
                c.save()
                
                self.set_status(f"Exported to PDF: {os.path.basename(file_path)}")
                messagebox.showinfo("Success", f"File exported to:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not export to PDF:\n{str(e)}")
    
        # Edit operations
    def undo(self):
        """Undo last action"""
        if hasattr(self, 'advanced_editor'):
            try:
                self.advanced_editor.text_editor.edit_undo()
            except tk.TclError:
                pass
    
    def redo(self):
        """Redo last undone action"""
        if hasattr(self, 'advanced_editor'):
            try:
                self.advanced_editor.text_editor.edit_redo()
            except tk.TclError:
                pass
    
    def cut(self):
        """Cut selected text"""
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.text_editor.event_generate("<<Cut>>")
    
    def copy(self):
        """Copy selected text"""
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.text_editor.event_generate("<<Copy>>")
    
    def paste(self):
        """Paste text from clipboard"""
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.text_editor.event_generate("<<Paste>>")
    
    def show_find_replace(self):
        """Show find and replace dialog"""
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.show_replace_dialog()
    
    def toggle_line_numbers(self):
        """Toggle line numbers visibility"""
        if hasattr(self, 'advanced_editor'):
            self.advanced_editor.toggle_line_numbers()
    
    def show_word_count(self):
        """Show word count dialog"""
        if not hasattr(self, 'advanced_editor'):
            return
        
        content = self.advanced_editor.text_editor.get(1.0, tk.END).strip()
        
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
        
        messagebox.showinfo("Document Statistics", stats_text)
    
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
        self.update_recent_menu()
        self.update_recent_files_list()
    
    def update_recent_menu(self):
        """Update recent files menu"""
        if not hasattr(self, 'recent_menu'):
            return
        
        # Clear existing items
        self.recent_menu.delete(0, 'end')
        
        recent_files = self.config.get('recent_files', [])
        if not recent_files:
            self.recent_menu.add_command(label="No recent files", state='disabled')
        else:
            for file_path in recent_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    self.recent_menu.add_command(
                        label=filename,
                        command=lambda fp=file_path: self.load_file(fp)
                    )
    
    def update_recent_files_list(self):
        """Update recent files listbox"""
        if not hasattr(self, 'recent_listbox'):
            return
        
        self.recent_listbox.delete(0, tk.END)
        recent_files = self.config.get('recent_files', [])
        
        for file_path in recent_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                self.recent_listbox.insert(tk.END, filename)
    
    def open_recent_from_list(self, event):
        """Open recent file from listbox"""
        selection = self.recent_listbox.curselection()
        if selection:
            index = selection[0]
            recent_files = self.config.get('recent_files', [])
            if index < len(recent_files):
                file_path = recent_files[index]
                if os.path.exists(file_path):
                    self.load_file(file_path)
    
    # Document statistics
    def update_document_stats(self):
        """Update document statistics in sidebar"""
        if hasattr(self, 'advanced_editor') and hasattr(self, 'stats_label'):
            try:
                content = self.advanced_editor.text_editor.get(1.0, tk.END).strip()
                lines = len(content.split('\n')) if content else 0
                words = len(content.split()) if content else 0
                chars = len(content)
                
                stats_text = f"Lines: {lines:,}\nWords: {words:,}\nCharacters: {chars:,}"
                self.stats_label.config(text=stats_text)
            except:
                pass
        
        # Schedule next update
        self.root.after(2000, self.update_document_stats)
    
    # Text change handling
    def on_text_change(self, event=None):
        """Handle text editor changes"""
        self.unsaved_changes = True
        if self.current_file:
            title = f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)} *"
        else:
            title = f"{APP_NAME} v{CURRENT_VERSION} - Untitled *"
        self.root.title(title)
        
        # Auto-save
        if self.config.get('auto_save', True) and self.current_file:
            self.root.after(3000, self.auto_save)
    
    def auto_save(self):
        """Auto-save current file"""
        if self.unsaved_changes and self.current_file and self.config.get('auto_save', True):
            try:
                content = ""
                if hasattr(self, 'advanced_editor'):
                    content = self.advanced_editor.text_editor.get(1.0, tk.END)
                
                with open(self.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.unsaved_changes = False
                self.set_status(f"Auto-saved: {os.path.basename(self.current_file)}")
                
                # Update title to remove asterisk
                self.root.title(f"{APP_NAME} v{CURRENT_VERSION} - {os.path.basename(self.current_file)}")
                
            except Exception as e:
                self.set_status(f"Auto-save failed: {str(e)}")
    
    # Settings event handlers
    def on_name_change(self, event=None):
        """Handle name change"""
        self.config['user_name'] = self.name_var.get()
        self.save_config()
    
    def on_theme_change(self):
        """Handle theme change"""
        new_theme = self.theme_var.get()
        self.switch_theme(new_theme)
    
    def switch_theme(self, theme_name):
        """Switch application theme"""
        self.theme.switch_theme(theme_name)
        self.config['theme'] = theme_name
        self.save_config()
        
        # Update theme indicator
        if hasattr(self, 'theme_indicator'):
            self.theme_indicator.config(text=f"Current: {theme_name.title()}")
        
        # Apply theme to all widgets
        self.apply_theme_to_app()
        
        messagebox.showinfo("Theme Changed", f"Theme changed to {theme_name.title()}.\nRestart the application for full effect.")
    
    def apply_theme_to_app(self):
        """Apply current theme to all application widgets"""
        colors = self.theme.get_colors()
        
        # Update root window
        self.root.configure(bg=colors['bg'])
        
        # Update status bar
        if hasattr(self, 'status_frame'):
            self.status_frame.configure(bg=colors['sidebar_bg'])
            self.status_label.configure(bg=colors['sidebar_bg'], fg=colors['fg'])
    
    def on_font_change(self, event=None):
        """Handle font change"""
        self.config['editor_font_family'] = self.font_family_var.get()
        self.config['editor_font_size'] = self.font_size_var.get()
        self.save_config()
        
        # Apply font changes
        if hasattr(self, 'advanced_editor'):
            font = (self.font_family_var.get(), self.font_size_var.get())
            self.advanced_editor.text_editor.configure(font=font)
            self.advanced_editor.line_numbers.configure(font=font)
    
    def on_auto_save_change(self):
        """Handle auto-save setting change"""
        self.config['auto_save'] = self.auto_save_var.get()
        self.save_config()
    
    def on_auto_update_change(self):
        """Handle auto-update setting change"""
        self.config['check_updates_on_startup'] = self.auto_update_var.get()
        self.save_config()
    
    # Update functionality
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
        update_window.configure(bg=self.theme.get_colors()['bg'])
        update_window.transient(self.root)
        update_window.grab_set()
        
        # Center the window
        update_window.update_idletasks()
        x = (update_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (update_window.winfo_screenheight() // 2) - (400 // 2)
        update_window.geometry(f"500x400+{x}+{y}")
        
        # Update icon and title
        title_frame = tk.Frame(update_window, bg=self.theme.get_colors()['bg'])
        title_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            title_frame,
            text="🚀 Update Available!",
            font=("Segoe UI", 16, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['success']
        ).pack()
        
        tk.Label(
            title_frame,
            text=f"Version {latest_version} is now available",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=(5, 0))
        
        tk.Label(
            title_frame,
            text=f"Current version: {CURRENT_VERSION}",
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
        ).pack()
        
                # Release notes
        notes_frame = tk.LabelFrame(
            update_window,
            text="What's New",
            font=("Segoe UI", 11, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        )
        notes_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        notes_text = scrolledtext.ScrolledText(
            notes_frame,
            wrap=tk.WORD,
            height=8,
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['editor_bg'],
            fg=self.theme.get_colors()['editor_fg']
        )
        notes_text.pack(fill='both', expand=True, padx=10, pady=10)
        notes_text.insert(1.0, release_notes)
        notes_text.config(state='disabled')
        
        # Buttons
        button_frame = tk.Frame(update_window, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        update_btn = tk.Button(
            button_frame,
            text="📥 Download & Install",
            command=lambda: self._download_update(download_url, update_window),
            bg=self.theme.get_colors()['success'],
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
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
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
        download_window.configure(bg=self.theme.get_colors()['bg'])
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
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
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
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
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
                    bg=self.theme.get_colors()['danger'],
                    fg='white',
                    font=("Segoe UI", 10),
                    padx=20,
                    pady=5,
                    relief='flat'
                ).pack(pady=10)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    # Helper functions
    def open_github(self):
        """Open GitHub repository"""
        github_url = VERSION_URL.replace("/raw.githubusercontent.com/", "/github.com/").replace("/main/version.json", "")
        webbrowser.open(github_url)
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("450x500")
        about_window.resizable(False, False)
        about_window.configure(bg=self.theme.get_colors()['bg'])
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center the window
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (450 // 2)
        y = (about_window.winfo_screenheight() // 2) - (500 // 2)
        about_window.geometry(f"450x500+{x}+{y}")
        
        # App icon section
        icon_frame = tk.Frame(about_window, bg=self.theme.get_colors()['primary'], height=100)
        icon_frame.pack(fill='x')
        icon_frame.pack_propagate(False)
        
        tk.Label(
            icon_frame,
            text="🚀",
            font=("Segoe UI", 32),
            bg=self.theme.get_colors()['primary'],
            fg='white'
        ).pack(pady=30)
        
        # App info
        info_frame = tk.Frame(about_window, bg=self.theme.get_colors()['bg'])
        info_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        tk.Label(
            info_frame,
            text=APP_NAME,
            font=("Segoe UI", 18, "bold"),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg']
        ).pack(pady=(0, 5))
        
        tk.Label(
            info_frame,
            text=f"Version {CURRENT_VERSION}",
            font=("Segoe UI", 12),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['primary']
        ).pack(pady=(0, 20))
        
        about_text = """A modern, feature-rich text editor and PDF viewer built with Python and Tkinter.

Features:
• Advanced text editing with syntax highlighting
• PDF viewing capabilities
• Auto-save and backup functionality
• Dark and light themes
• Automatic updates
• Professional, modern interface

Built with:
• Python 3.x
• Tkinter (GUI framework)
• PyMuPDF (PDF support)
• ReportLab (PDF export)
• Requests (updates)

© 2025 PixelHeaven
Open source software"""
        
        tk.Label(
            info_frame,
            text=about_text,
            font=("Segoe UI", 10),
            bg=self.theme.get_colors()['bg'],
            fg=self.theme.get_colors()['fg'],
            justify='left',
            wraplength=380
        ).pack(pady=(0, 20))
        
        # Buttons
        button_frame = tk.Frame(info_frame, bg=self.theme.get_colors()['bg'])
        button_frame.pack(fill='x')
        
        tk.Button(
            button_frame,
            text="🌐 Visit GitHub",
            command=self.open_github,
            bg=self.theme.get_colors()['primary'],
            fg='white',
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            relief='flat'
        ).pack(side='left')
        
        tk.Button(
            button_frame,
            text="Close",
            command=about_window.destroy,
            bg=self.theme.get_colors()['select_bg'],
            fg=self.theme.get_colors()['fg'],
            font=("Segoe UI", 10),
            padx=20,
            pady=8,
            relief='flat'
        ).pack(side='right')
    
    def on_closing(self):
        """Handle application closing"""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?"
            )
            if result is True:  # Yes - save
                self.save_file()
                if self.unsaved_changes:  # Save was cancelled
                    return
            elif result is None:  # Cancel
                return
        
        # Save window state
        self.save_config()
        self.root.quit()
    
    def run(self):
        """Start the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Restore window geometry
        try:
            geometry = self.config.get('window_geometry', '1200x800')
            self.root.geometry(geometry)
            
            window_state = self.config.get('window_state', 'normal')
            if window_state == 'zoomed':
                self.root.state('zoomed')
        except:
            # Fallback to center window
            self.root.update_idletasks()
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Apply current theme
        self.apply_theme_to_app()
        
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
            f"An error occurred while starting the application:\n\n{str(e)}\n\nPlease check that all dependencies are installed:\n"
            f"pip install requests\n"
            f"pip install PyMuPDF (optional, for PDF support)\n"
            f"pip install reportlab (optional, for PDF export)"
        )
        sys.exit(1)

if __name__ == "__main__":
    main()




