import tkinter as tk
from tkinter import messagebox
import yt_dlp
import threading
import os
import re
import zipfile
import urllib.request
import shutil

from gui import DownloaderGUI


class YouTubeBulkDownloader:
    def __init__(self, root):
        self.root = root
        self.is_downloading = False
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.ffmpeg_path = os.path.join(self.app_dir, "ffmpeg")
        
        # Setup GUI with callbacks
        callbacks = {
            'start_download': self.start_download,
            'stop_download': self.stop_download,
        }
        self.gui = DownloaderGUI(root, callbacks)
        
        # Check and download FFmpeg if needed
        self.check_ffmpeg()
    
    def check_ffmpeg(self):
        """Check if FFmpeg exists, if not download it"""
        ffmpeg_exe = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(self.ffmpeg_path, "ffprobe.exe")
        
        if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
            return True
        
        if self.gui.show_ffmpeg_download_dialog():
            self.download_ffmpeg()
        else:
            self.gui.show_ffmpeg_warning()
        
        return os.path.exists(ffmpeg_exe)
    
    def download_ffmpeg(self):
        """Download FFmpeg from GitHub releases"""
        self.gui.create_ffmpeg_progress_window()
        download_thread = threading.Thread(target=self._download_ffmpeg_thread, daemon=True)
        download_thread.start()
    
    def _download_ffmpeg_thread(self):
        """Thread function to download FFmpeg"""
        try:
            ffmpeg_url = "https://github.com/GyanD/codexffmpeg/releases/download/7.1/ffmpeg-7.1-essentials_build.zip"
            os.makedirs(self.ffmpeg_path, exist_ok=True)
            zip_path = os.path.join(self.ffmpeg_path, "ffmpeg.zip")
            
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
                        self.root.after(0, lambda p=percent, t=f"Downloaded: {downloaded_mb:.1f} / {total_mb:.1f} MB": 
                                       self.gui.update_ffmpeg_progress(p, t))
            
            self.root.after(0, lambda: self.gui.update_ffmpeg_progress(100, "Extracting..."))
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.ffmpeg_path)
            
            for root_dir, dirs, files in os.walk(self.ffmpeg_path):
                for file in files:
                    if file in ['ffmpeg.exe', 'ffprobe.exe']:
                        src = os.path.join(root_dir, file)
                        dst = os.path.join(self.ffmpeg_path, file)
                        if src != dst:
                            shutil.copy2(src, dst)
            
            os.remove(zip_path)
            
            for item in os.listdir(self.ffmpeg_path):
                item_path = os.path.join(self.ffmpeg_path, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            
            self.root.after(0, self._ffmpeg_download_success)
            
        except Exception as e:
            self.root.after(0, lambda: self._ffmpeg_download_failed(str(e)))
    
    def _ffmpeg_download_success(self):
        self.gui.close_ffmpeg_progress_window()
        self.gui.show_ffmpeg_success()
    
    def _ffmpeg_download_failed(self, error):
        self.gui.close_ffmpeg_progress_window()
        self.gui.show_ffmpeg_error(error, self.ffmpeg_path)
    
    def validate_urls(self, urls):
        valid_urls = []
        youtube_pattern = re.compile(r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)')
        
        for url in urls:
            url = url.strip()
            if url and youtube_pattern.search(url):
                valid_urls.append(url)
            elif url:
                self.gui.log_message(f"Invalid URL skipped: {url}")
                
        return valid_urls
    
    def start_download(self, urls_input, format_type, quality, download_path):
        urls = urls_input.split('\n')
        valid_urls = self.validate_urls(urls)
        
        if not valid_urls:
            messagebox.showwarning("No Valid URLs", "No valid YouTube URLs found.")
            return
        
        if not os.path.exists(download_path):
            try:
                os.makedirs(download_path)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot create download directory: {str(e)}")
                return
        
        self.is_downloading = True
        self.gui.set_downloading_state(True)
        
        self.download_thread = threading.Thread(
            target=self.download_videos, 
            args=(valid_urls, format_type, quality, download_path)
        )
        self.download_thread.start()
    
    def stop_download(self):
        self.is_downloading = False
        self.gui.set_progress_text("Stopping download...")
    
    def download_videos(self, urls, format_type, quality, download_path):
        total_urls = len(urls)
        
        self.gui.log_message(f"Selected format: {format_type}, Quality: {quality}")
        
        ffmpeg_location = None
        ffmpeg_exe = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            ffmpeg_location = self.ffmpeg_path
            self.gui.log_message(f"✓ FFmpeg found at: {ffmpeg_location}")
        else:
            self.gui.log_message("⚠ FFmpeg not found - video quality may be limited!")
        
        common_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'quiet': False,
            'no_warnings': False,
        }
        
        if ffmpeg_location:
            common_opts['ffmpeg_location'] = ffmpeg_location
        
        if format_type == "mp3":
            if not ffmpeg_location:
                self.gui.log_message("⚠ WARNING: FFmpeg not found. MP3 conversion may fail.")
                self.gui.log_message("  Restart the app to download FFmpeg automatically.")
            
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
            if ffmpeg_location:
                if quality == "best":
                    format_selector = 'bv*+ba/b'
                    self.gui.log_message("Downloading: BEST quality available")
                elif quality == "1080p":
                    format_selector = 'bv*[height<=1080]+ba/b[height<=1080]/b'
                    self.gui.log_message("Downloading: Up to 1080p (Full HD)")
                elif quality == "720p":
                    format_selector = 'bv*[height<=720]+ba/b[height<=720]/b'
                    self.gui.log_message("Downloading: Up to 720p (HD)")
                elif quality == "480p":
                    format_selector = 'bv*[height<=480]+ba/b[height<=480]/b'
                    self.gui.log_message("Downloading: Up to 480p (SD)")
                elif quality == "360p":
                    format_selector = 'bv*[height<=360]+ba/b[height<=360]/b'
                    self.gui.log_message("Downloading: Up to 360p")
                elif quality == "smallest":
                    format_selector = 'wv*+wa/w'
                    self.gui.log_message("Downloading: Smallest file size")
                else:
                    format_selector = 'bv*+ba/b'
                    self.gui.log_message("Downloading: Default best quality")
            else:
                self.gui.log_message("⚠ No FFmpeg - downloading pre-merged format (may be limited)")
                format_selector = 'b'
                
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
                self.gui.set_progress_text(f"Downloading {i+1}/{total_urls}: Processing...")
                self.gui.log_message(f"\n--- Starting download {i+1}/{total_urls} ---")
                self.gui.log_message(f"URL: {url}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get('title', 'Unknown') if info else 'Unknown'
                    
                    if info:
                        height = info.get('height', 'N/A')
                        width = info.get('width', 'N/A')
                        self.gui.log_message(f"Title: {title}")
                        self.gui.log_message(f"Resolution: {width}x{height}")
                    
                successful_downloads += 1
                self.gui.log_message(f"✓ Successfully downloaded: {title}")
                
            except Exception as e:
                error_msg = str(e)
                self.gui.log_message(f"✗ Error downloading {url}: {error_msg}")
            
            progress = ((i + 1) / total_urls) * 100
            self.gui.set_progress(progress)
        
        self.is_downloading = False
        self.gui.set_downloading_state(False)
        
        if successful_downloads < total_urls:
            self.gui.set_progress_text(f"Download completed. {successful_downloads}/{total_urls} successful.")
        else:
            self.gui.set_progress_text(f"Download completed! {successful_downloads}/{total_urls} successful.")
            
        self.gui.log_message(f"\n--- Download Summary ---")
        self.gui.log_message(f"Total URLs: {total_urls}")
        self.gui.log_message(f"Successful: {successful_downloads}")
        self.gui.log_message(f"Failed: {total_urls - successful_downloads}")


def main():
    root = tk.Tk()
    app = YouTubeBulkDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
