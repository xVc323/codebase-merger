#!/usr/bin/env python3

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import tempfile
import queue
import re
import mimetypes

# Import core functionality
from codebase_merger import should_include_file, clone_repo, process_repository, SKIP_DIRS, SKIP_EXTENSIONS, MAX_FILE_SIZE

class CodebaseMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Codebase Merger")
        self.root.geometry("650x550")
        self.root.resizable(True, True)
        
        # Variables
        self.repo_url = tk.StringVar()
        self.output_file = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "merged_codebase.txt"))
        self.max_file_size = tk.IntVar(value=5)
        self.exclude_patterns = []
        self.temp_dir = None
        self.process_thread = None
        self.message_queue = queue.Queue()
        
        # Default max file size (5MB)
        self.MAX_FILE_SIZE = MAX_FILE_SIZE
        
        # File extensions/types to skip
        self.SKIP_EXTENSIONS = SKIP_EXTENSIONS

        # Directories to skip
        self.SKIP_DIRS = SKIP_DIRS
        
        # Create UI elements
        self._create_ui()
        
        # Set up periodic check for messages from worker thread
        self.root.after(100, self._check_message_queue)
        
    def _create_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Repository URL
        ttk.Label(main_frame, text="GitHub Repository URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.repo_url, width=50).grid(row=0, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Output file
        ttk.Label(main_frame, text="Output File:").grid(row=1, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=1, column=1, sticky=tk.W+tk.E, pady=5)
        ttk.Entry(output_frame, textvariable=self.output_file, width=40).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="Browse...", command=self._browse_output).pack(side=tk.RIGHT, padx=5)
        
        # Max file size
        ttk.Label(main_frame, text="Max File Size (MB):").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(main_frame, from_=1, to=100, textvariable=self.max_file_size, width=10).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Exclusions
        ttk.Label(main_frame, text="Exclude Patterns:").grid(row=3, column=0, sticky=tk.W, pady=5)
        exclude_frame = ttk.Frame(main_frame)
        exclude_frame.grid(row=3, column=1, sticky=tk.W+tk.E, pady=5)
        
        self.exclusion_entry = ttk.Entry(exclude_frame, width=30)
        self.exclusion_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(exclude_frame, text="Add", command=self._add_exclusion).pack(side=tk.RIGHT, padx=5)
        
        # Exclusion list
        ttk.Label(main_frame, text="Current Exclusions:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.exclusion_listbox = tk.Listbox(main_frame, height=6)
        self.exclusion_listbox.grid(row=4, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Default exclusions
        default_exclusions = [
            r"\.git/.*", 
            "node_modules/.*", 
            "__pycache__/.*"
        ]
        for pattern in default_exclusions:
            self.exclude_patterns.append(pattern)
            self.exclusion_listbox.insert(tk.END, pattern)
        
        # Listbox buttons
        listbox_buttons = ttk.Frame(main_frame)
        listbox_buttons.grid(row=5, column=1, sticky=tk.E, pady=5)
        ttk.Button(listbox_buttons, text="Remove Selected", command=self._remove_exclusion).pack(side=tk.RIGHT, padx=5)
        ttk.Button(listbox_buttons, text="Clear All", command=self._clear_exclusions).pack(side=tk.RIGHT, padx=5)
        
        # Progress
        ttk.Label(main_frame, text="Progress:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
        self.progress.grid(row=6, column=1, sticky=tk.W+tk.E, pady=5)
        
        # Status
        ttk.Label(main_frame, text="Status:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.status_text = tk.Text(main_frame, height=8, width=50, wrap=tk.WORD)
        self.status_text.grid(row=7, column=1, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        self.status_text.config(state=tk.DISABLED)
        
        # Add scrollbar to status text
        status_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        status_scroll.grid(row=7, column=2, sticky=tk.N+tk.S)
        self.status_text.config(yscrollcommand=status_scroll.set)
        
        # Execute button
        ttk.Button(main_frame, text="Merge Codebase", command=self._execute_merge).grid(row=8, column=1, sticky=tk.E, pady=10)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def _check_message_queue(self):
        """Check for messages from the worker thread and process them in the main thread"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                if message[0] == "status":
                    self._update_status(message[1])
                elif message[0] == "messagebox":
                    messagebox_type, title, text = message[1:4]
                    if messagebox_type == "error":
                        messagebox.showerror(title, text)
                    elif messagebox_type == "info":
                        messagebox.showinfo(title, text)
                    elif messagebox_type == "warning":
                        messagebox.showwarning(title, text)
                elif message[0] == "finish":
                    success = message[1]
                    self._finish_process_ui(success)
                self.message_queue.task_done()
        except queue.Empty:
            pass
        
        # Schedule the next check
        self.root.after(100, self._check_message_queue)
    
    def _browse_output(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
            initialdir=os.path.dirname(self.output_file.get()),
            initialfile=os.path.basename(self.output_file.get())
        )
        if filename:
            self.output_file.set(filename)
    
    def _add_exclusion(self):
        pattern = self.exclusion_entry.get().strip()
        if pattern:
            self.exclude_patterns.append(pattern)
            self.exclusion_listbox.insert(tk.END, pattern)
            self.exclusion_entry.delete(0, tk.END)
    
    def _remove_exclusion(self):
        selected = self.exclusion_listbox.curselection()
        if selected:
            index = selected[0]
            self.exclusion_listbox.delete(index)
            self.exclude_patterns.pop(index)
    
    def _clear_exclusions(self):
        self.exclusion_listbox.delete(0, tk.END)
        self.exclude_patterns.clear()

    def _update_status(self, message):
        """Update the status text from the main thread"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def _thread_safe_status(self, message):
        """Update status in a thread-safe way"""
        self.message_queue.put(("status", message))
    
    def _is_binary_file(self, file_path):
        """Check if a file is binary based on content and mimetype"""
        try:
            # Check mimetype first
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type and not mime_type.startswith(('text/', 'application/json', 'application/xml', 'application/javascript')):
                return True
            
            # Try to open and read the first few bytes
            with open(file_path, 'rb') as f:
                content = f.read(1024)
                # If there's a null byte, it's likely binary
                if b'\x00' in content:
                    return True
                
                # Try decoding as text
                try:
                    content.decode('utf-8')
                    return False
                except UnicodeDecodeError:
                    return True
        except Exception:
            # If any error occurs, consider it binary to be safe
            return True
        
        return False
    
    def _should_include_file(self, file_path):
        """Determine if a file should be included in the merged file"""
        return should_include_file(file_path, self.MAX_FILE_SIZE)
    
    def _clone_repo(self, repo_url, temp_dir):
        """Clone a GitHub repository to the specified directory"""
        self._thread_safe_status(f"Cloning repository: {repo_url}")
        result = clone_repo(repo_url, temp_dir)
        if not result:
            self._thread_safe_status(f"Error cloning repository")
        return result
    
    def _process_repository(self, repo_dir, output_file, exclude_patterns=None):
        """Process repository files and merge them into a single file"""
        self._thread_safe_status(f"Processing repository in {repo_dir}")
        
        # Update the status callback to use our thread-safe method
        status_callback = self._thread_safe_status
        
        # Use the core function from codebase_merger.py
        file_count = process_repository(
            repo_dir, 
            output_file, 
            max_file_size=self.MAX_FILE_SIZE,
            exclude_patterns=exclude_patterns,
            status_callback=status_callback
        )
        
        self._thread_safe_status(f"Completed! Processed {file_count} files.")
        return file_count
        
    def _execute_merge(self):
        # Validate inputs
        if not self.repo_url.get().strip():
            messagebox.showerror("Error", "Please enter a GitHub repository URL.")
            return
        
        if not self.output_file.get().strip():
            messagebox.showerror("Error", "Please specify an output file.")
            return
        
        # Start progress bar
        self.progress.start()
        
        # Clear status
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)
        
        # Update status
        self._update_status(f"Starting merge process...")
        self._update_status(f"Repository: {self.repo_url.get()}")
        self._update_status(f"Output file: {self.output_file.get()}")
        self._update_status(f"Exclusions: {', '.join(self.exclude_patterns)}")
        
        # Start merge in a separate thread
        self.process_thread = threading.Thread(target=self._run_merge)
        self.process_thread.daemon = True
        self.process_thread.start()
    
    def _run_merge(self):
        try:
            # Create a temporary directory
            self.temp_dir = tempfile.TemporaryDirectory()
            temp_dir_path = self.temp_dir.name
            
            # Clone repository
            self._thread_safe_status(f"Cloning repository to temporary directory...")
            if not self._clone_repo(self.repo_url.get(), temp_dir_path):
                self._thread_safe_status(f"Error: Failed to clone repository.")
                self.message_queue.put(("messagebox", "error", "Error", "Failed to clone repository. Please check the URL and your internet connection."))
                self._finish_process(False)
                return
            
            # Update max file size
            self.MAX_FILE_SIZE = self.max_file_size.get() * 1024 * 1024
            
            # Process repository
            self._thread_safe_status(f"Processing repository files...")
            file_count = self._process_repository(
                temp_dir_path, 
                self.output_file.get(),
                self.exclude_patterns
            )
            
            # Complete
            if file_count > 0:
                self._thread_safe_status(f"Success! Processed {file_count} files.")
                self._thread_safe_status(f"Output saved to: {self.output_file.get()}")
                self.message_queue.put(("messagebox", "info", "Success", f"Successfully merged {file_count} files into {self.output_file.get()}"))
            else:
                self._thread_safe_status(f"No files were processed. Check your exclusion patterns.")
                self.message_queue.put(("messagebox", "warning", "Warning", "No files were processed. Check your exclusion patterns."))
            
            self._finish_process(True)
            
        except Exception as e:
            self._thread_safe_status(f"Error: {str(e)}")
            self.message_queue.put(("messagebox", "error", "Error", f"An error occurred: {str(e)}"))
            self._finish_process(False)
    
    def _finish_process(self, success):
        """Clean up resources in the worker thread and signal the UI to update"""
        # Clean up
        if self.temp_dir:
            try:
                self.temp_dir.cleanup()
            except:
                pass
        
        # Signal UI thread to update
        self.message_queue.put(("finish", success))
    
    def _finish_process_ui(self, success):
        """Update UI elements after processing is complete (called from main thread)"""
        # Stop progress bar
        self.progress.stop()
        
        # Final status update
        if success:
            self._update_status("Process completed successfully.")
        else:
            self._update_status("Process failed.")

if __name__ == "__main__":
    root = tk.Tk()
    app = CodebaseMergerGUI(root)
    root.mainloop()

def main():
    """Entry point for the console script"""
    root = tk.Tk()
    app = CodebaseMergerGUI(root)
    root.mainloop()
    return 0