import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path


class DownloaderGUI:
    def __init__(self, root, callbacks):
        self.root = root
        self.root.title("YouTube Bulk Downloader")
        self.root.geometry("800x600")
        
        self.callbacks = callbacks
        self.download_path = str(Path.home() / "Downloads")
        
        self.setup_gui()
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="YouTube Bulk Downloader", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # URLs input section
        ttk.Label(main_frame, text="YouTube URLs (one per line):").grid(row=1, column=0, columnspan=3, sticky=tk.W)
        
        self.urls_text = scrolledtext.ScrolledText(main_frame, height=8, width=70)
        self.urls_text.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 10))
        
        # Format selection
        format_frame = ttk.Frame(main_frame)
        format_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.format_var = tk.StringVar(value="mp4")
        ttk.Radiobutton(format_frame, text="MP4 (Video)", variable=self.format_var, value="mp4").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="MP3 (Audio)", variable=self.format_var, value="mp3").pack(side=tk.LEFT)
        
        # Quality selection
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(quality_frame, text="Quality:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, width=25, state="readonly")
        self.quality_combo['values'] = ("best", "1080p", "720p", "480p", "360p", "smallest")
        self.quality_combo.current(0)
        self.quality_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Quality description label
        self.quality_desc = ttk.Label(quality_frame, text="(4K/1080p - Best Available)", foreground="gray")
        self.quality_desc.pack(side=tk.LEFT)
        
        # Bind quality change event
        self.quality_combo.bind("<<ComboboxSelected>>", self.on_quality_change)
        
        # Download path
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="Download Path:").grid(row=0, column=0, padx=(0, 10))
        
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        ttk.Button(path_frame, text="Browse", command=self.browse_path).grid(row=0, column=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        self.download_btn = ttk.Button(button_frame, text="Start Download", command=self.on_start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="Clear URLs", command=self.clear_urls)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.on_stop_download, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Progress section
        ttk.Label(main_frame, text="Download Progress:").grid(row=7, column=0, columnspan=3, sticky=tk.W, pady=(20, 5))
        
        self.progress_var = tk.StringVar(value="Ready to download")
        progress_label = ttk.Label(main_frame, textvariable=self.progress_var)
        progress_label.grid(row=8, column=0, columnspan=3, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Log output
        ttk.Label(main_frame, text="Download Log:").grid(row=10, column=0, columnspan=3, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=8, width=70)
        self.log_text.grid(row=11, column=0, columnspan=3, sticky=(tk.W, tk.E))
    
    def browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.path_var.set(folder)
            self.download_path = folder
    
    def clear_urls(self):
        self.urls_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
    
    def on_quality_change(self, event=None):
        """Update quality description when selection changes"""
        quality = self.quality_var.get()
        descriptions = {
            "best": "(4K/1080p - Best Available)",
            "1080p": "(Full HD)",
            "720p": "(HD)",
            "480p": "(SD)",
            "360p": "(Low Quality)",
            "smallest": "(Smallest File Size)"
        }
        self.quality_desc.config(text=descriptions.get(quality, ""))
    
    def on_start_download(self):
        urls_input = self.urls_text.get(1.0, tk.END).strip()
        if not urls_input:
            messagebox.showwarning("No URLs", "Please enter at least one YouTube URL.")
            return
        
        if self.callbacks.get('start_download'):
            self.callbacks['start_download'](
                urls_input,
                self.format_var.get(),
                self.quality_var.get(),
                self.path_var.get()
            )
    
    def on_stop_download(self):
        if self.callbacks.get('stop_download'):
            self.callbacks['stop_download']()
    
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_progress(self, value):
        self.progress_bar['value'] = value
        self.root.update_idletasks()
    
    def set_progress_text(self, text):
        self.progress_var.set(text)
    
    def set_downloading_state(self, is_downloading):
        if is_downloading:
            self.download_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.progress_bar['value'] = 0
        else:
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
    
    def show_ffmpeg_download_dialog(self):
        """Show FFmpeg download confirmation dialog"""
        return messagebox.askyesno(
            "FFmpeg Required",
            "FFmpeg is required for MP3 conversion and video merging.\n\n"
            "Do you want to download FFmpeg automatically?\n"
            "(This is a one-time download of ~140MB)"
        )
    
    def show_ffmpeg_warning(self):
        """Show FFmpeg missing warning"""
        messagebox.showwarning(
            "Limited Functionality",
            "Without FFmpeg:\n"
            "• MP3 conversion will not work\n"
            "• Some video qualities may not work\n\n"
            "You can manually install FFmpeg later."
        )
    
    def create_ffmpeg_progress_window(self):
        """Create FFmpeg download progress window"""
        self.ffmpeg_progress_win = tk.Toplevel(self.root)
        self.ffmpeg_progress_win.title("Downloading FFmpeg")
        self.ffmpeg_progress_win.geometry("450x180")
        self.ffmpeg_progress_win.transient(self.root)
        self.ffmpeg_progress_win.protocol("WM_DELETE_WINDOW", lambda: None)
        
        ttk.Label(self.ffmpeg_progress_win, text="Downloading FFmpeg...", font=("Arial", 12)).pack(pady=15)
        self.ffmpeg_status_label = ttk.Label(self.ffmpeg_progress_win, text="Connecting...")
        self.ffmpeg_status_label.pack(pady=5)
        self.ffmpeg_progress_bar = ttk.Progressbar(self.ffmpeg_progress_win, mode='determinate', length=350, maximum=100)
        self.ffmpeg_progress_bar.pack(pady=10)
        self.ffmpeg_percent_label = ttk.Label(self.ffmpeg_progress_win, text="0%")
        self.ffmpeg_percent_label.pack(pady=5)
        
        return self.ffmpeg_progress_win
    
    def update_ffmpeg_progress(self, percent, text):
        """Update FFmpeg progress bar"""
        self.ffmpeg_progress_bar['value'] = percent
        self.ffmpeg_percent_label.config(text=f"{percent}%")
        self.ffmpeg_status_label.config(text=text)
    
    def close_ffmpeg_progress_window(self):
        """Close FFmpeg progress window"""
        if hasattr(self, 'ffmpeg_progress_win'):
            self.ffmpeg_progress_win.destroy()
    
    def show_ffmpeg_success(self):
        """Show FFmpeg download success message"""
        messagebox.showinfo("Success", "FFmpeg downloaded successfully!\n\nYou can now download MP3 and MP4 files.")
    
    def show_ffmpeg_error(self, error, ffmpeg_path):
        """Show FFmpeg download error message"""
        messagebox.showerror(
            "Download Failed",
            f"Failed to download FFmpeg:\n{error}\n\n"
            "Please download FFmpeg manually from:\n"
            "https://www.gyan.dev/ffmpeg/builds/\n\n"
            "Download 'ffmpeg-release-essentials.zip', extract it,\n"
            "and copy ffmpeg.exe & ffprobe.exe to:\n"
            f"{ffmpeg_path}"
        )
