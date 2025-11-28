import tkinter as tk
from tkinter import messagebox
import yt_dlp
import threading
import os
import re
import zipfile
import urllib.request
import shutil
import time

from gui import DownloaderGUI


class YouTubeBulkDownloader:
    def __init__(self, root):
        self.root = root
        self.is_downloading = False
        self.current_file_index = 0
        self.total_files = 0
        self.current_title = ""
        self.download_start_time = None
        self.file_start_time = None
        self.total_downloaded_bytes = 0
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
        self.download_start_time = time.time()
        self.total_downloaded_bytes = 0
        self.gui.set_downloading_state(True)
        
        self.download_thread = threading.Thread(
            target=self.download_videos, 
            args=(valid_urls, format_type, quality, download_path)
        )
        self.download_thread.start()
    
    def stop_download(self):
        self.is_downloading = False
        self.root.after(0, lambda: self.gui.set_progress_text("⏹ Stopping download..."))
        self.root.after(0, lambda: self.gui.set_status("Cancelling..."))
    
    def format_bytes(self, bytes_value):
        """Format bytes to human readable string"""
        if bytes_value is None:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024
        return f"{bytes_value:.2f} TB"
    
    def format_time(self, seconds):
        """Format seconds to human readable string"""
        if seconds is None or seconds < 0:
            return "N/A"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            mins, secs = divmod(int(seconds), 60)
            return f"{mins}m {secs}s"
        else:
            hours, remainder = divmod(int(seconds), 3600)
            mins, secs = divmod(remainder, 60)
            return f"{hours}h {mins}m {secs}s"
    
    def progress_hook(self, d):
        """Handle download progress updates from yt-dlp"""
        if d['status'] == 'downloading':
            # Get raw values
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta')
            
            # Calculate file percentage
            if total > 0:
                file_percent = (downloaded / total) * 100
            else:
                file_percent = 0
            
            # Calculate overall progress
            if self.total_files > 0:
                overall_percent = ((self.current_file_index + (file_percent / 100)) / self.total_files) * 100
            else:
                overall_percent = file_percent
            
            # Format values
            downloaded_str = self.format_bytes(downloaded)
            total_str = self.format_bytes(total) if total > 0 else "Unknown"
            speed_str = f"{self.format_bytes(speed)}/s" if speed else "Calculating..."
            eta_str = self.format_time(eta) if eta else "Calculating..."
            
            # Truncate title for display
            display_title = self.current_title[:40] + "..." if len(self.current_title) > 40 else self.current_title
            
            # Update GUI
            self.root.after(0, lambda: self.gui.update_progress(
                overall_percent=overall_percent,
                file_percent=file_percent,
                file_num=self.current_file_index + 1,
                total_files=self.total_files,
                downloaded=downloaded_str,
                total_size=total_str,
                speed=speed_str,
                eta=eta_str,
                title=display_title,
                phase="downloading"
            ))
            
        elif d['status'] == 'finished':
            filename = d.get('filename', '')
            filesize = d.get('total_bytes') or d.get('downloaded_bytes', 0)
            self.total_downloaded_bytes += filesize
            
            self.root.after(0, lambda: self.gui.update_progress(
                overall_percent=((self.current_file_index + 1) / self.total_files) * 100 if self.total_files > 0 else 100,
                file_percent=100,
                file_num=self.current_file_index + 1,
                total_files=self.total_files,
                downloaded=self.format_bytes(filesize),
                total_size=self.format_bytes(filesize),
                speed="--",
                eta="--",
                title=self.current_title[:40] + "..." if len(self.current_title) > 40 else self.current_title,
                phase="processing"
            ))
        
        elif d['status'] == 'error':
            self.root.after(0, lambda: self.gui.set_status("❌ Error occurred"))
    
    def download_videos(self, urls, format_type, quality, download_path):
        total_urls = len(urls)
        self.total_files = total_urls
        
        self.gui.log_message(f"{'='*50}")
        self.gui.log_message(f"📥 Starting bulk download")
        self.gui.log_message(f"   Format: {format_type.upper()}, Quality: {quality}")
        self.gui.log_message(f"   Total files: {total_urls}")
        self.gui.log_message(f"{'='*50}")
        
        ffmpeg_location = None
        ffmpeg_exe = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe):
            ffmpeg_location = self.ffmpeg_path
            self.gui.log_message(f"✓ FFmpeg ready")
        else:
            self.gui.log_message("⚠ FFmpeg not found - some features limited")
        
        common_opts = {
            'outtmpl': os.path.join(download_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.progress_hook],
        }
        
        if ffmpeg_location:
            common_opts['ffmpeg_location'] = ffmpeg_location
        
        if format_type == "mp3":
            if not ffmpeg_location:
                self.gui.log_message("⚠ WARNING: FFmpeg not found. MP3 conversion may fail.")
            
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
                quality_map = {
                    "best": ('bv*+ba/b', "BEST quality"),
                    "1080p": ('bv*[height<=1080]+ba/b[height<=1080]/b', "1080p (Full HD)"),
                    "720p": ('bv*[height<=720]+ba/b[height<=720]/b', "720p (HD)"),
                    "480p": ('bv*[height<=480]+ba/b[height<=480]/b', "480p (SD)"),
                    "360p": ('bv*[height<=360]+ba/b[height<=360]/b', "360p"),
                    "smallest": ('wv*+wa/w', "Smallest size"),
                }
                format_selector, quality_desc = quality_map.get(quality, ('bv*+ba/b', "Default"))
                self.gui.log_message(f"📹 Quality: {quality_desc}")
            else:
                format_selector = 'b'
                
            ydl_opts = {
                **common_opts,
                'format': format_selector,
                'merge_output_format': 'mp4',
            }
        
        successful_downloads = 0
        failed_downloads = []
        
        for i, url in enumerate(urls):
            if not self.is_downloading:
                self.gui.log_message(f"\n⏹ Download cancelled by user")
                break
            
            self.current_file_index = i
            self.file_start_time = time.time()
            
            try:
                # Fetch video info first
                self.root.after(0, lambda idx=i: self.gui.update_progress(
                    overall_percent=(idx / total_urls) * 100,
                    file_percent=0,
                    file_num=idx + 1,
                    total_files=total_urls,
                    downloaded="--",
                    total_size="--",
                    speed="--",
                    eta="--",
                    title="Fetching video info...",
                    phase="fetching"
                ))
                
                self.gui.log_message(f"\n{'─'*40}")
                self.gui.log_message(f"📄 [{i+1}/{total_urls}] Processing...")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Get info first
                    info = ydl.extract_info(url, download=False)
                    self.current_title = info.get('title', 'Unknown') if info else 'Unknown'
                    duration = info.get('duration', 0) if info else 0
                    
                    self.gui.log_message(f"   Title: {self.current_title}")
                    if duration:
                        self.gui.log_message(f"   Duration: {self.format_time(duration)}")
                    
                    # Now download
                    ydl.download([url])
                    
                    if info:
                        height = info.get('height', 'N/A')
                        width = info.get('width', 'N/A')
                        if height != 'N/A' and width != 'N/A':
                            self.gui.log_message(f"   Resolution: {width}x{height}")
                
                file_time = time.time() - self.file_start_time
                successful_downloads += 1
                self.gui.log_message(f"   ✓ Completed in {self.format_time(file_time)}")
                
            except Exception as e:
                error_msg = str(e)[:100]
                failed_downloads.append((url, error_msg))
                self.gui.log_message(f"   ✗ Failed: {error_msg}")
        
        # Final summary
        total_time = time.time() - self.download_start_time
        
        self.is_downloading = False
        self.root.after(0, lambda: self.gui.set_downloading_state(False))
        
        # Final progress update
        final_percent = 100 if successful_downloads == total_urls else (successful_downloads / total_urls) * 100
        status_emoji = "✅" if successful_downloads == total_urls else "⚠️"
        
        self.root.after(0, lambda: self.gui.update_progress(
            overall_percent=final_percent,
            file_percent=100,
            file_num=total_urls,
            total_files=total_urls,
            downloaded=self.format_bytes(self.total_downloaded_bytes),
            total_size=self.format_bytes(self.total_downloaded_bytes),
            speed="--",
            eta="--",
            title=f"{status_emoji} Download Complete!",
            phase="complete"
        ))
        
        # Summary log
        self.gui.log_message(f"\n{'='*50}")
        self.gui.log_message(f"📊 DOWNLOAD SUMMARY")
        self.gui.log_message(f"{'='*50}")
        self.gui.log_message(f"   Total files: {total_urls}")
        self.gui.log_message(f"   ✓ Successful: {successful_downloads}")
        self.gui.log_message(f"   ✗ Failed: {len(failed_downloads)}")
        self.gui.log_message(f"   📦 Total size: {self.format_bytes(self.total_downloaded_bytes)}")
        self.gui.log_message(f"   ⏱ Total time: {self.format_time(total_time)}")
        
        if failed_downloads:
            self.gui.log_message(f"\n❌ Failed URLs:")
            for url, error in failed_downloads:
                self.gui.log_message(f"   • {url[:50]}...")
        
        self.gui.log_message(f"{'='*50}")


def main():
    root = tk.Tk()
    app = YouTubeBulkDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
