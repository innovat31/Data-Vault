import os
import json
import shutil
import hashlib
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext

class DataVault:
    def __init__(self, vault_dir="data_vault"):
        self.vault_dir = Path(vault_dir)
        self.vault_dir.mkdir(exist_ok=True)
        self.metadata_file = self.vault_dir / "metadata.json"
        self.files_dir = self.vault_dir / "files"
        self.files_dir.mkdir(exist_ok=True)
        self.metadata = self.load_metadata()
    
    def load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_metadata(self):
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def add_file(self, source_path):
        source = Path(source_path)
        if not source.exists():
            return False, "File does not exist"
        
        file_name = source.name
        file_hash = self.calculate_hash(source)
        timestamp = datetime.now().isoformat()
        
        if file_name not in self.metadata:
            self.metadata[file_name] = {
                "name": file_name,
                "versions": [],
                "current_version": 0
            }
        
        version_num = len(self.metadata[file_name]["versions"]) + 1
        version_dir = self.files_dir / file_name / f"v{version_num}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        dest = version_dir / file_name
        shutil.copy2(source, dest)
        
        version_info = {
            "version": version_num,
            "timestamp": timestamp,
            "size": source.stat().st_size,
            "hash": file_hash,
            "path": str(dest.relative_to(self.vault_dir))
        }
        
        self.metadata[file_name]["versions"].append(version_info)
        self.metadata[file_name]["current_version"] = version_num - 1
        self.save_metadata()
        
        return True, f"File '{file_name}' added as version {version_num}"
    
    def calculate_hash(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]
    
    def get_file_list(self):
        return list(self.metadata.keys())
    
    def get_versions(self, file_name):
        if file_name in self.metadata:
            return self.metadata[file_name]["versions"]
        return []
    
    def get_current_version_index(self, file_name):
        if file_name in self.metadata:
            return self.metadata[file_name]["current_version"]
        return -1
    
    def rollback_version(self, file_name, version_index):
        if file_name not in self.metadata:
            return False, "File not found"
        
        versions = self.metadata[file_name]["versions"]
        if version_index < 0 or version_index >= len(versions):
            return False, "Invalid version index"
        
        self.metadata[file_name]["current_version"] = version_index
        self.save_metadata()
        return True, f"Rolled back to version {version_index + 1}"
    
    def export_file(self, file_name, dest_path):
        if file_name not in self.metadata:
            return False, "File not found"
        
        current_version = self.metadata[file_name]["current_version"]
        version_info = self.metadata[file_name]["versions"][current_version]
        source = self.vault_dir / version_info["path"]
        
        if not source.exists():
            return False, "Source file not found"
        
        shutil.copy2(source, dest_path)
        return True, f"File exported to {dest_path}"
    
    def delete_file(self, file_name):
        if file_name not in self.metadata:
            return False, "File not found"
        
        file_dir = self.files_dir / file_name
        if file_dir.exists():
            shutil.rmtree(file_dir)
        
        del self.metadata[file_name]
        self.save_metadata()
        return True, f"File '{file_name}' deleted"
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"


class DataVaultGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Data Vault - File Storage & Version Control")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e2e')
        
        self.vault = DataVault()
        self.selected_file = None
        
        self.setup_ui()
        self.refresh_file_list()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#2d2d44', height=80)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        title = tk.Label(header, text="🗄️ Data Vault", font=('Arial', 24, 'bold'),
                        bg='#2d2d44', fg='#ffffff')
        title.pack(side=tk.LEFT, padx=20, pady=20)
        
        subtitle = tk.Label(header, text="File Storage & Version Control System",
                           font=('Arial', 12), bg='#2d2d44', fg='#a6a6c8')
        subtitle.pack(side=tk.LEFT, padx=5, pady=20)
        
        # Upload button
        upload_btn = tk.Button(header, text="📤 Upload File", font=('Arial', 12, 'bold'),
                              bg='#7c3aed', fg='white', command=self.upload_file,
                              relief=tk.FLAT, padx=20, pady=10, cursor='hand2')
        upload_btn.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Main content area
        content = tk.Frame(self.root, bg='#1e1e2e')
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Left panel - File list
        left_panel = tk.Frame(content, bg='#2d2d44', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        files_label = tk.Label(left_panel, text="📁 Files", font=('Arial', 14, 'bold'),
                              bg='#2d2d44', fg='#ffffff')
        files_label.pack(anchor=tk.W, padx=15, pady=10)
        
        # File listbox with scrollbar
        list_frame = tk.Frame(left_panel, bg='#2d2d44')
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(list_frame, font=('Arial', 11),
                                       bg='#1e1e2e', fg='#ffffff',
                                       selectbackground='#7c3aed',
                                       selectforeground='#ffffff',
                                       yscrollcommand=scrollbar.set,
                                       relief=tk.FLAT, highlightthickness=0)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)
        
        # File action buttons
        btn_frame = tk.Frame(left_panel, bg='#2d2d44')
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        download_btn = tk.Button(btn_frame, text="⬇️ Download", font=('Arial', 10),
                                bg='#22c55e', fg='white', command=self.download_file,
                                relief=tk.FLAT, padx=15, pady=8, cursor='hand2')
        download_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(btn_frame, text="🗑️ Delete", font=('Arial', 10),
                              bg='#ef4444', fg='white', command=self.delete_file,
                              relief=tk.FLAT, padx=15, pady=8, cursor='hand2')
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Version history
        right_panel = tk.Frame(content, bg='#2d2d44', width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        version_label = tk.Label(right_panel, text="🕐 Version History",
                                font=('Arial', 14, 'bold'),
                                bg='#2d2d44', fg='#ffffff')
        version_label.pack(anchor=tk.W, padx=15, pady=10)
        
        # Version text area
        self.version_text = scrolledtext.ScrolledText(right_panel, font=('Courier', 10),
                                                      bg='#1e1e2e', fg='#ffffff',
                                                      relief=tk.FLAT, wrap=tk.WORD,
                                                      state=tk.DISABLED)
        self.version_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready", font=('Arial', 10),
                                  bg='#2d2d44', fg='#a6a6c8', anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def refresh_file_list(self):
        self.file_listbox.delete(0, tk.END)
        files = self.vault.get_file_list()
        for file_name in files:
            versions = self.vault.get_versions(file_name)
            self.file_listbox.insert(tk.END, f"{file_name} ({len(versions)} versions)")
    
    def on_file_select(self, event):
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        file_text = self.file_listbox.get(index)
        self.selected_file = file_text.split(' (')[0]
        self.show_version_history()
    
    def show_version_history(self):
        if not self.selected_file:
            return
        
        self.version_text.config(state=tk.NORMAL)
        self.version_text.delete(1.0, tk.END)
        
        versions = self.vault.get_versions(self.selected_file)
        current_idx = self.vault.get_current_version_index(self.selected_file)
        
        self.version_text.insert(tk.END, f"File: {self.selected_file}\n")
        self.version_text.insert(tk.END, "=" * 60 + "\n\n")
        
        for idx, version in enumerate(versions):
            is_current = idx == current_idx
            marker = ">>> CURRENT" if is_current else ""
            
            self.version_text.insert(tk.END, f"Version {version['version']} {marker}\n")
            self.version_text.insert(tk.END, f"  Time: {version['timestamp']}\n")
            self.version_text.insert(tk.END, f"  Size: {self.vault.format_size(version['size'])}\n")
            self.version_text.insert(tk.END, f"  Hash: {version['hash']}\n")
            
            if not is_current:
                # Add rollback button reference
                self.version_text.insert(tk.END, f"  [To rollback, type: rollback {idx}]\n")
            
            self.version_text.insert(tk.END, "\n")
        
        # Add rollback instruction
        self.version_text.insert(tk.END, "\n" + "-" * 60 + "\n")
        self.version_text.insert(tk.END, "To rollback: Right-click and select version\n")
        
        self.version_text.config(state=tk.DISABLED)
        
        # Bind right-click for rollback
        self.version_text.bind('<Button-3>', self.show_rollback_menu)
    
    def show_rollback_menu(self, event):
        if not self.selected_file:
            return
        
        menu = tk.Menu(self.root, tearoff=0)
        versions = self.vault.get_versions(self.selected_file)
        
        for idx, version in enumerate(versions):
            menu.add_command(
                label=f"Rollback to Version {version['version']}",
                command=lambda i=idx: self.rollback_to_version(i)
            )
        
        menu.post(event.x_root, event.y_root)
    
    def rollback_to_version(self, version_index):
        if not self.selected_file:
            return
        
        success, message = self.vault.rollback_version(self.selected_file, version_index)
        if success:
            messagebox.showinfo("Success", message)
            self.show_version_history()
            self.status_bar.config(text=message)
        else:
            messagebox.showerror("Error", message)
    
    def upload_file(self):
        file_path = filedialog.askopenfilename(title="Select file to upload")
        if not file_path:
            return
        
        success, message = self.vault.add_file(file_path)
        if success:
            messagebox.showinfo("Success", message)
            self.refresh_file_list()
            self.status_bar.config(text=message)
        else:
            messagebox.showerror("Error", message)
    
    def download_file(self):
        if not self.selected_file:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        dest_path = filedialog.asksaveasfilename(
            defaultextension="",
            initialfile=self.selected_file,
            title="Save file as"
        )
        
        if not dest_path:
            return
        
        success, message = self.vault.export_file(self.selected_file, dest_path)
        if success:
            messagebox.showinfo("Success", message)
            self.status_bar.config(text=f"Downloaded: {self.selected_file}")
        else:
            messagebox.showerror("Error", message)
    
    def delete_file(self):
        if not self.selected_file:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        confirm = messagebox.askyesno("Confirm Delete",
                                     f"Delete '{self.selected_file}' and all versions?")
        if not confirm:
            return
        
        success, message = self.vault.delete_file(self.selected_file)
        if success:
            messagebox.showinfo("Success", message)
            self.selected_file = None
            self.refresh_file_list()
            self.version_text.config(state=tk.NORMAL)
            self.version_text.delete(1.0, tk.END)
            self.version_text.config(state=tk.DISABLED)
            self.status_bar.config(text=f"Deleted: {self.selected_file}")
        else:
            messagebox.showerror("Error", message)


def main():
    root = tk.Tk()
    app = DataVaultGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()