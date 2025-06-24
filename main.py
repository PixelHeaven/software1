import tkinter as tk
from tkinter import messagebox, ttk
import requests
import subprocess
import sys
import os
import json
import threading
from pathlib import Path

CURRENT_VERSION = "1.1.0"
VERSION_URL = "https://raw.githubusercontent.com/yourusername/yourapp/main/version.json"
APP_NAME = "MyApp"

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{CURRENT_VERSION}")
        self.root.geometry("600x400")
        
        # Create main interface
        self.create_widgets()
        
    def create_widgets(self):
        # Main content
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        tk.Label(main_frame, text=f"Welcome to {APP_NAME}!", 
                font=("Arial", 16)).pack(pady=20)
        
        tk.Label(main_frame, text=f"Current Version: {CURRENT_VERSION}",
                font=("Arial", 12)).pack(pady=10)
        
        # Your app content goes here
        tk.Label(main_frame, text="Your application content goes here...",
                fg="gray").pack(pady=20)
        
        # Settings/Update section
        settings_frame = tk.Frame(main_frame)
        settings_frame.pack(pady=20)
        
        tk.Label(settings_frame, text="Settings", 
                font=("Arial", 14, "bold")).pack()
        
        self.update_btn = tk.Button(settings_frame, text="Check for Updates",
                                  command=self.check_for_updates_threaded,
                                  bg="#4CAF50", fg="white", padx=20, pady=5)
        self.update_btn.pack(pady=10)
        
        # Progress bar (hidden initially)
        self.progress_frame = tk.Frame(settings_frame)
        self.progress_label = tk.Label(self.progress_frame, text="")
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        
    def check_for_updates_threaded(self):
        """Run update check in a separate thread to avoid freezing UI"""
        self.update_btn.config(state='disabled', text="Checking...")
        threading.Thread(target=self.check_for_updates, daemon=True).start()
        
    def check_for_updates(self):
        try:
            self.show_progress("Checking for updates...")
            
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            
            latest_info = response.json()
            latest_version = latest_info["version"]
            
            if self.is_newer_version(latest_version, CURRENT_VERSION):
                self.hide_progress()
                self.root.after(0, lambda: self.prompt_update(latest_info))
            else:
                self.hide_progress()
                self.root.after(0, lambda: messagebox.showinfo(
                    "Up to Date", f"You have the latest version ({CURRENT_VERSION})"))
                
        except requests.RequestException as e:
            self.hide_progress()
            self.root.after(0, lambda: messagebox.showerror(
                "Update Check Failed", f"Could not check for updates:\n{str(e)}"))
        except Exception as e:
            self.hide_progress()
            self.root.after(0, lambda: messagebox.showerror(
                "Error", f"An error occurred:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.update_btn.config(
                state='normal', text="Check for Updates"))
    
    def is_newer_version(self, latest, current):
        """Simple version comparison (works for x.y.z format)"""
        latest_parts = [int(x) for x in latest.split('.')]
        current_parts = [int(x) for x in current.split('.')]
        
        # Pad shorter version with zeros
        max_len = max(len(latest_parts), len(current_parts))
        latest_parts.extend([0] * (max_len - len(latest_parts)))
        current_parts.extend([0] * (max_len - len(current_parts)))
        
        return latest_parts > current_parts
    
    def prompt_update(self, update_info):
        """Ask user if they want to update"""
        result = messagebox.askyesno(
            "Update Available",
            f"New version {update_info['version']} is available!\n"
            f"Current version: {CURRENT_VERSION}\n\n"
            f"Would you like to update now?",
            icon="question"
        )
        
        if result:
            threading.Thread(target=self.download_and_update, 
                           args=(update_info,), daemon=True).start()
    
    def download_and_update(self, update_info):
        try:
            self.show_progress("Downloading update...")
            installer_url = update_info["installer_url"]
            installer_name = "update_installer.exe"
            
            # Download the installer
            response = requests.get(installer_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(installer_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.root.after(0, lambda: self.update_progress_text(
                                f"Downloaded: {progress:.1f}%"))
            
            self.hide_progress()
            
            # Show final confirmation
            self.root.after(0, lambda: self.run_installer(installer_name))
            
        except Exception as e:
            self.hide_progress()
            self.root.after(0, lambda: messagebox.showerror(
                "Download Failed", f"Could not download update:\n{str(e)}"))
    
    def run_installer(self, installer_path):
        """Run the installer and close the application"""
        result = messagebox.showinfo(
            "Ready to Update",
            "Update downloaded successfully!\n"
            "The application will now close and the installer will run.",
            type="ok"
        )
        
        try:
            # Run installer in silent mode
            subprocess.Popen([installer_path, "/SILENT", "/CLOSEAPPLICATIONS"])
            self.root.quit()
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Update Failed", f"Could not run installer:\n{str(e)}")
    
    def show_progress(self, text):
        """Show progress bar and text"""
        self.root.after(0, lambda: self.progress_label.config(text=text))
        self.root.after(0, lambda: self.progress_frame.pack(pady=10))
        self.root.after(0, lambda: self.progress_label.pack())
        self.root.after(0, lambda: self.progress_bar.pack(pady=5))
        self.root.after(0, lambda: self.progress_bar.start())
    
    def hide_progress(self):
        """Hide progress bar"""
        self.root.after(0, lambda: self.progress_bar.stop())
        self.root.after(0, lambda: self.progress_frame.pack_forget())
    
    def update_progress_text(self, text):
        """Update progress text"""
        self.progress_label.config(text=text)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApp()
    app.run()