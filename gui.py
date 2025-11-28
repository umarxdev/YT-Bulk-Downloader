import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path


class DownloaderGUI:
    def __init__(self, root, callbacks):
        self.root = root
        self.root.title("YouTube Bulk Downloader")
        self.root.geometry("850x700")
        self.root.minsize(700, 600)
        
        self.callbacks = callbacks
        self.download_path = str(Path.home() / "Downloads")
        
        self.setup_styles()
        self.setup_gui()
    
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 18, "bold"))
        style.configure("Subtitle.TLabel", font=("Arial", 10), foreground="gray")
        style.configure("Status.TLabel", font=("Arial", 11, "bold"))
        style.configure("Info.TLabel", font=("Arial", 9))
        style.configure("Success.TLabel", foreground="green")
        style.configure("Warning.TLabel", foreground="orange")
        style.configure("Error.TLabel", foreground="red")
    
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)  # Log section expands
        
        # Title Section
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        ttk.Label(title_frame, text="YouTube Bulk Downloader", style="Title.TLabel").pack()
        ttk.Label(title_frame, text="Download multiple videos with ease", style="Subtitle.TLabel").pack()
        
        # URLs input section
        url_frame = ttk.LabelFrame(main_frame, text=" YouTube URLs ", padding="10")
        url_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.urls_text = scrolledtext.ScrolledText(url_frame, height=6, width=70, font=("Consolas", 9))
        self.urls_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text=" Download Options ", padding="10")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # Format selection
        ttk.Label(options_frame, text="Format:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=0, column=1, sticky=tk.W)
        
        self.format_var = tk.StringVar(value="mp4")
        ttk.Radiobutton(format_frame, text="📹 MP4 (Video)", variable=self.format_var, value="mp4").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(format_frame, text="🎵 MP3 (Audio)", variable=self.format_var, value="mp3").pack(side=tk.LEFT)
        
        # Playlist mode checkbox
        ttk.Label(options_frame, text="Playlist:").grid(row=0, column=2, sticky=tk.W, padx=(30, 10))
        self.playlist_var = tk.BooleanVar(value=False)
        self.playlist_check = ttk.Checkbutton(options_frame, text="📋 Download entire playlist", variable=self.playlist_var, command=self.on_playlist_toggle)
        self.playlist_check.grid(row=0, column=3, sticky=tk.W)
        
        # Playlist limit
        self.playlist_limit_frame = ttk.Frame(options_frame)
        self.playlist_limit_frame.grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        ttk.Label(self.playlist_limit_frame, text="Max videos:").pack(side=tk.LEFT, padx=(0, 5))
        self.playlist_limit_var = tk.StringVar(value="10")
        self.playlist_limit_spin = ttk.Spinbox(self.playlist_limit_frame, from_=1, to=9999, width=6, textvariable=self.playlist_limit_var)
        self.playlist_limit_spin.pack(side=tk.LEFT)
        self.playlist_limit_frame.grid_remove()  # Hidden by default
        
        # Quality selection
        ttk.Label(options_frame, text="Quality:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        quality_frame = ttk.Frame(options_frame)
        quality_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        self.quality_var = tk.StringVar(value="best")
        self.quality_combo = ttk.Combobox(quality_frame, textvariable=self.quality_var, width=15, state="readonly")
        self.quality_combo['values'] = ("best", "1080p", "720p", "480p", "360p", "smallest")
        self.quality_combo.current(0)
        self.quality_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        self.quality_desc = ttk.Label(quality_frame, text="(Best Available - 4K/1080p)", style="Info.TLabel")
        self.quality_desc.pack(side=tk.LEFT)
        self.quality_combo.bind("<<ComboboxSelected>>", self.on_quality_change)
        
        # Download path
        ttk.Label(options_frame, text="Save to:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        path_frame = ttk.Frame(options_frame)
        path_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(10, 0))
        path_frame.columnconfigure(0, weight=1)
        
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, font=("Consolas", 9))
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(path_frame, text="📁 Browse", command=self.browse_path, width=12).grid(row=0, column=1)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=15)
        
        self.download_btn = ttk.Button(button_frame, text="⬇️ Start Download", command=self.on_start_download, width=18)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="⏹ Stop", command=self.on_stop_download, state=tk.DISABLED, width=12)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="🗑 Clear", command=self.clear_urls, width=12)
        self.clear_btn.pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text=" Download Progress ", padding="10")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to download")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Current file info
        self.current_file_var = tk.StringVar(value="")
        ttk.Label(progress_frame, textvariable=self.current_file_var, style="Info.TLabel").grid(row=1, column=0, sticky=tk.W)
        
        # File progress bar
        file_progress_frame = ttk.Frame(progress_frame)
        file_progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        file_progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_progress_frame, text="File:", width=8).grid(row=0, column=0, sticky=tk.W)
        self.file_progress_bar = ttk.Progressbar(file_progress_frame, mode='determinate', length=400)
        self.file_progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        self.file_percent_var = tk.StringVar(value="0%")
        ttk.Label(file_progress_frame, textvariable=self.file_percent_var, width=6).grid(row=0, column=2)
        
        # Overall progress bar
        overall_progress_frame = ttk.Frame(progress_frame)
        overall_progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        overall_progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(overall_progress_frame, text="Overall:", width=8).grid(row=0, column=0, sticky=tk.W)
        self.progress_bar = ttk.Progressbar(overall_progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        self.overall_percent_var = tk.StringVar(value="0%")
        ttk.Label(overall_progress_frame, textvariable=self.overall_percent_var, width=6).grid(row=0, column=2)
        
        # Download stats
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.speed_var = tk.StringVar(value="Speed: --")
        self.eta_var = tk.StringVar(value="ETA: --")
        self.size_var = tk.StringVar(value="Size: --")
        
        ttk.Label(stats_frame, textvariable=self.speed_var, style="Info.TLabel", width=20).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_frame, textvariable=self.eta_var, style="Info.TLabel", width=15).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(stats_frame, textvariable=self.size_var, style="Info.TLabel", width=25).pack(side=tk.LEFT)
        
        # Log output
        log_frame = ttk.LabelFrame(main_frame, text=" Download Log ", padding="10")
        log_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=70, font=("Consolas", 9), state=tk.NORMAL)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure log text tags for colors
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("info", foreground="blue")
    
    def browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.path_var.set(folder)
            self.download_path = folder
    
    def clear_urls(self):
        self.urls_text.delete(1.0, tk.END)
        self.log_text.delete(1.0, tk.END)
        self.reset_progress()
    
    def reset_progress(self):
        """Reset all progress indicators"""
        self.progress_bar['value'] = 0
        self.file_progress_bar['value'] = 0
        self.file_percent_var.set("0%")
        self.overall_percent_var.set("0%")
        self.status_var.set("Ready to download")
        self.current_file_var.set("")
        self.speed_var.set("Speed: --")
        self.eta_var.set("ETA: --")
        self.size_var.set("Size: --")
    
    def on_playlist_toggle(self):
        """Show/hide playlist limit when playlist mode is toggled"""
        if self.playlist_var.get():
            self.playlist_limit_frame.grid()
        else:
            self.playlist_limit_frame.grid_remove()
    
    def on_quality_change(self, event=None):
        """Update quality description when selection changes"""
        descriptions = {
            "best": "(Best Available - 4K/1080p)",
            "1080p": "(Full HD)",
            "720p": "(HD Ready)",
            "480p": "(Standard Definition)",
            "360p": "(Low Quality)",
            "smallest": "(Smallest File Size)"
        }
        self.quality_desc.config(text=descriptions.get(self.quality_var.get(), ""))
    
    def on_start_download(self):
        urls_input = self.urls_text.get(1.0, tk.END).strip()
        # Filter out comments
        urls_input = '\n'.join([line for line in urls_input.split('\n') if not line.strip().startswith('#')])
        
        if not urls_input.strip():
            messagebox.showwarning("No URLs", "Please enter at least one YouTube URL.")
            return
        
        self.log_text.delete(1.0, tk.END)
        self.reset_progress()
        
        if self.callbacks.get('start_download'):
            playlist_limit = int(self.playlist_limit_var.get()) if self.playlist_var.get() else 0
            self.callbacks['start_download'](
                urls_input,
                self.format_var.get(),
                self.quality_var.get(),
                self.path_var.get(),
                self.playlist_var.get(),
                playlist_limit
            )
    
    def on_stop_download(self):
        if self.callbacks.get('stop_download'):
            self.callbacks['stop_download']()
    
    def log_message(self, message):
        """Add message to log with optional coloring"""
        self.log_text.insert(tk.END, f"{message}\n")
        
        # Auto-color based on content
        line_start = self.log_text.index("end-2l linestart")
        line_end = self.log_text.index("end-1l lineend")
        
        if "✓" in message or "Success" in message or "Completed" in message:
            self.log_text.tag_add("success", line_start, line_end)
        elif "✗" in message or "Error" in message or "Failed" in message:
            self.log_text.tag_add("error", line_start, line_end)
        elif "⚠" in message or "WARNING" in message:
            self.log_text.tag_add("warning", line_start, line_end)
        
        self.log_text.see(tk.END)
    
    def update_progress(self, overall_percent, file_percent, file_num, total_files, 
                       downloaded, total_size, speed, eta, title, phase):
        """Update all progress indicators"""
        # Update progress bars
        self.progress_bar['value'] = overall_percent
        self.file_progress_bar['value'] = file_percent
        
        # Update percentage labels
        self.overall_percent_var.set(f"{overall_percent:.1f}%")
        self.file_percent_var.set(f"{file_percent:.1f}%")
        
        # Update status based on phase
        phase_icons = {
            "fetching": "🔍",
            "downloading": "⬇️",
            "processing": "⚙️",
            "complete": "✅"
        }
        icon = phase_icons.get(phase, "📥")
        
        if phase == "complete":
            self.status_var.set(f"{icon} {title}")
        else:
            self.status_var.set(f"{icon} {phase.capitalize()} [{file_num}/{total_files}]")
        
        # Update current file info
        self.current_file_var.set(f"📄 {title}")
        
        # Update stats
        self.speed_var.set(f"🚀 Speed: {speed}")
        self.eta_var.set(f"⏱ ETA: {eta}")
        self.size_var.set(f"📦 {downloaded} / {total_size}")
    
    def set_progress(self, value):
        self.progress_bar['value'] = value
        self.overall_percent_var.set(f"{value:.1f}%")
    
    def set_progress_text(self, text):
        self.status_var.set(text)
    
    def set_status(self, text):
        self.status_var.set(text)
    
    def set_downloading_state(self, is_downloading):
        if is_downloading:
            self.download_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.clear_btn.config(state=tk.DISABLED)
        else:
            self.download_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.clear_btn.config(state=tk.NORMAL)
    
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
