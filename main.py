import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import yt_dlp
import threading
import os
import re
import zipfile
import urllib.request
import shutil
from pathlib import Path

class YouTubeBulkDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Bulk Downloader")
        self.root.geometry("800x600")
        
        self.download_path = str(Path.home() / "Downloads")
        self.is_downloading = False
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.ffmpeg_path = os.path.join(self.app_dir, "ffmpeg")
        
        # Check and download FFmpeg if needed
        self.check_ffmpeg()
        
        self.setup_gui()
    
    def check_ffmpeg(self):
        """Check if FFmpeg exists, if not download it"""
        ffmpeg_exe = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(self.ffmpeg_path, "ffprobe.exe")
        
        if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
            return True
        
        # Ask user if they want to download FFmpeg
        result = messagebox.askyesno(
            "FFmpeg Required",
            "FFmpeg is required for MP3 conversion and video merging.\n\n"
            "Do you want to download FFmpeg automatically?\n"
            "(This is a one-time download of ~140MB)"
        )
        
        if result:
            self.download_ffmpeg()
        else:
            messagebox.showwarning(
                "Limited Functionality",
                "Without FFmpeg:\n"
                "• MP3 conversion will not work\n"
                "• Some video qualities may not work\n\n"
                "You can manually install FFmpeg later."
            )
        
        return os.path.exists(ffmpeg_exe)
    
    def download_ffmpeg(self):
        """Download FFmpeg from GitHub releases"""
        # Create progress window
        self.ffmpeg_progress_win = tk.Toplevel(self.root)
        self.ffmpeg_progress_win.title("Downloading FFmpeg")
        self.ffmpeg_progress_win.geometry("450x180")
        self.ffmpeg_progress_win.transient(self.root)
        self.ffmpeg_progress_win.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
        
        ttk.Label(self.ffmpeg_progress_win, text="Downloading FFmpeg...", font=("Arial", 12)).pack(pady=15)
        self.ffmpeg_status_label = ttk.Label(self.ffmpeg_progress_win, text="Connecting...")
        self.ffmpeg_status_label.pack(pady=5)
        self.ffmpeg_progress_bar = ttk.Progressbar(self.ffmpeg_progress_win, mode='determinate', length=350, maximum=100)
        self.ffmpeg_progress_bar.pack(pady=10)
        self.ffmpeg_percent_label = ttk.Label(self.ffmpeg_progress_win, text="0%")
        self.ffmpeg_percent_label.pack(pady=5)
        
        # Start download in separate thread
        download_thread = threading.Thread(target=self._download_ffmpeg_thread, daemon=True)
        download_thread.start()
    
    def _download_ffmpeg_thread(self):
        """Thread function to download FFmpeg"""
        try:
            # Smaller FFmpeg essentials build (~25MB)
            ffmpeg_url = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
            
            # Create ffmpeg directory
            os.makedirs(self.ffmpeg_path, exist_ok=True)
            zip_path = os.path.join(self.ffmpeg_path, "ffmpeg.zip")
            
            # Download with progress
            self._update_ffmpeg_status("Downloading... Please wait")
            
            # Use urlopen for progress tracking
            response = urllib.request.urlopen(ffmpeg_url, timeout=60)
            total_size = int(response.headers.get('content-length', 0))
            
            downloaded = 0
            block_size = 8192
            
            with open(zip_path, 'wb') as f:
                while True:
                    buffer = response.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    if total_size > 0:
                        percent = int((downloaded / total_size) * 100)
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        self._update_ffmpeg_progress(percent, f"Downloaded: {downloaded_mb:.1f} / {total_mb:.1f} MB")
            
            self._update_ffmpeg_status("Extracting FFmpeg...")
            self._update_ffmpeg_progress(100, "Extracting...")
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.ffmpeg_path)
            
            # Find and move the exe files to ffmpeg folder
            for root_dir, dirs, files in os.walk(self.ffmpeg_path):
                for file in files:
                    if file in ['ffmpeg.exe', 'ffprobe.exe']:
                        src = os.path.join(root_dir, file)
                        dst = os.path.join(self.ffmpeg_path, file)
                        if src != dst:
                            shutil.copy2(src, dst)
            
            # Clean up zip file
            os.remove(zip_path)
            
            # Remove extracted folders (keep only exe files)
            for item in os.listdir(self.ffmpeg_path):
                item_path = os.path.join(self.ffmpeg_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            # Success
            self.root.after(0, self._ffmpeg_download_success)
            
        except Exception as e:
            self.root.after(0, lambda: self._ffmpeg_download_failed(str(e)))
    
    def _update_ffmpeg_status(self, text):
        """Update status label from thread"""
        self.root.after(0, lambda: self.ffmpeg_status_label.config(text=text))
    
    def _update_ffmpeg_progress(self, percent, text):
        """Update progress bar from thread"""
        def update():
            self.ffmpeg_progress_bar['value'] = percent
            self.ffmpeg_percent_label.config(text=f"{percent}%")
            self.ffmpeg_status_label.config(text=text)
        self.root.after(0, update)
    
    def _ffmpeg_download_success(self):
        """Called when FFmpeg download succeeds"""
        self.ffmpeg_progress_win.destroy()
        messagebox.showinfo("Success", "FFmpeg downloaded successfully!\n\nYou can now download MP3 and MP4 files.")
    
    def _ffmpeg_download_failed(self, error):
        """Called when FFmpeg download fails"""
        self.ffmpeg_progress_win.destroy()
        messagebox.showerror(
            "Download Failed",
            f"Failed to download FFmpeg:\n{error}\n\n"
            "Please download FFmpeg manually from:\n"
            "https://www.gyan.dev/ffmpeg/builds/\n\n"
            "Download 'ffmpeg-release-essentials.zip', extract it,\n"
            "and copy ffmpeg.exe & ffprobe.exe to:\n"
            f"{self.ffmpeg_path}"
        )
    
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
        self.quality_combo.current(0)  # Select "best" by default
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
        
        self.download_btn = ttk.Button(button_frame, text="Start Download", command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_btn = ttk.Button(button_frame, text="Clear URLs", command=self.clear_urls)
        self.clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_download, state=tk.DISABLED)
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
        
    def validate_urls(self, urls):
        valid_urls = []
        youtube_pattern = re.compile(r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)')
        
        for url in urls:
            url = url.strip()
            if url and youtube_pattern.search(url):
                valid_urls.append(url)
            elif url:
                self.log_message(f"Invalid URL skipped: {url}")
                
        return valid_urls
        
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_download(self):
        urls_input = self.urls_text.get(1.0, tk.END).strip()
        if not urls_input:
            messagebox.showwarning("No URLs", "Please enter at least one YouTube URL.")
            return
            
        urls = urls_input.split('\n')
        valid_urls = self.validate_urls(urls)
        
        if not valid_urls:
            messagebox.showwarning("No Valid URLs", "No valid YouTube URLs found.")
            return
            
        if not os.path.exists(self.download_path):
            try:
                os.makedirs(self.download_path)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create download directory: {str(e)}")
                return
                
        self.is_downloading = True
        self.download_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.progress_bar['value'] = 0
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_videos, args=(valid_urls,))
        self.download_thread.start()
        
    def stop_download(self):
        self.is_downloading = False
        self.progress_var.set("Stopping download...")
        
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
        
    def download_videos(self, urls):
        total_urls = len(urls)
        format_type = self.format_var.get()
        quality = self.quality_var.get()
        
        self.log_message(f"Selected format: {format_type}, Quality: {quality}")
        
        # Check for FFmpeg path
        ffmpeg_location = None
        ffmpeg_exe = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            ffmpeg_location = self.ffmpeg_path
            self.log_message(f"✓ FFmpeg found at: {ffmpeg_location}")
        else:
            self.log_message("⚠ FFmpeg not found - video quality may be limited!")
        
        # Common yt-dlp options - use default client (most reliable now)
        common_opts = {
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'quiet': False,
            'no_warnings': False,
        }
        
        # Add FFmpeg location if available
        if ffmpeg_location:
            common_opts['ffmpeg_location'] = ffmpeg_location
        
        # yt-dlp options based on format
        if format_type == "mp3":
            if not ffmpeg_location:
                self.log_message("⚠ WARNING: FFmpeg not found. MP3 conversion may fail.")
                self.log_message("  Restart the app to download FFmpeg automatically.")
            
            ydl_opts = {
                **common_opts,
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
            }
        else:
            # Format selectors for video - simplified and reliable
            if ffmpeg_location:
                # With FFmpeg - download best streams and merge
                if quality == "best":
                    format_selector = 'bv*+ba/b'
                    self.log_message("Downloading: BEST quality available")
                elif quality == "1080p":
                    format_selector = 'bv*[height<=1080]+ba/b[height<=1080]/b'
                    self.log_message("Downloading: Up to 1080p (Full HD)")
                elif quality == "720p":
                    format_selector = 'bv*[height<=720]+ba/b[height<=720]/b'
                    self.log_message("Downloading: Up to 720p (HD)")
                elif quality == "480p":
                    format_selector = 'bv*[height<=480]+ba/b[height<=480]/b'
                    self.log_message("Downloading: Up to 480p (SD)")
                elif quality == "360p":
                    format_selector = 'bv*[height<=360]+ba/b[height<=360]/b'
                    self.log_message("Downloading: Up to 360p")
                elif quality == "smallest":
                    format_selector = 'wv*+wa/w'
                    self.log_message("Downloading: Smallest file size")
                else:
                    format_selector = 'bv*+ba/b'
                    self.log_message("Downloading: Default best quality")
            else:
                # Without FFmpeg - pre-merged formats only (limited quality)
                self.log_message("⚠ No FFmpeg - downloading pre-merged format (may be limited)")
                format_selector = 'b'  # best single file format
                
            ydl_opts = {
                **common_opts,
                'format': format_selector,
                'merge_output_format': 'mp4',
            }
        
        successful_downloads = 0
        
        for i, url in enumerate(urls):
            if not self.is_downloading:
                break
                
            try:
                self.progress_var.set(f"Downloading {i+1}/{total_urls}: Processing...")
                self.log_message(f"\n--- Starting download {i+1}/{total_urls} ---")
                self.log_message(f"URL: {url}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Download directly (info extraction included)
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown') if info else 'Unknown'
                    
                    if info:
                        height = info.get('height', 'N/A')
                        width = info.get('width', 'N/A')
                        self.log_message(f"Title: {title}")
                        self.log_message(f"Resolution: {width}x{height}")
                    
                successful_downloads += 1
                self.log_message(f"✓ Successfully downloaded: {title}")
                
            except Exception as e:
                error_msg = str(e)
                self.log_message(f"✗ Error downloading {url}: {error_msg}")
                
            # Update progress bar
            progress = ((i + 1) / total_urls) * 100
            self.progress_bar['value'] = progress
            self.root.update_idletasks()
        
        # Reset UI state
        self.is_downloading = False
        self.download_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        if successful_downloads < total_urls:
            self.progress_var.set(f"Download completed. {successful_downloads}/{total_urls} successful.")
        else:
            self.progress_var.set(f"Download completed! {successful_downloads}/{total_urls} successful.")
            
        self.log_message(f"\n--- Download Summary ---")
        self.log_message(f"Total URLs: {total_urls}")
        self.log_message(f"Successful: {successful_downloads}")
        self.log_message(f"Failed: {total_urls - successful_downloads}")

def main():
    root = tk.Tk()
    app = YouTubeBulkDownloader(root)
    root.mainloop()

if __name__ == "__main__":
    main()
