# YouTube Bulk Downloader

A Python-based GUI application for downloading multiple YouTube videos as MP3 or MP4 files using yt-dlp.

## Features

- **Bulk Download**: Paste multiple YouTube URLs and download them all at once
- **Format Options**: Choose between MP4 (video) or MP3 (audio only)
- **Quality Selection**: Select video quality (best, 720p, 480p, 360p, worst)
- **Custom Download Path**: Choose where to save your downloads
- **Progress Tracking**: Real-time progress bar and detailed logging
- **Error Handling**: Robust error handling with detailed error messages
- **User-Friendly GUI**: Clean and intuitive tkinter interface

## Installation

1. Make sure you have Python 3.7+ installed
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Usage

1. **Add URLs**: Paste YouTube URLs in the text area (one URL per line)
2. **Select Format**: Choose MP4 for video or MP3 for audio only
3. **Choose Quality**: Select desired video quality (MP3 uses best audio quality)
4. **Set Download Path**: Choose where to save files (default: Downloads folder)
5. **Start Download**: Click "Start Download" to begin the process
6. **Monitor Progress**: Watch the progress bar and log for real-time updates

## Supported URL Formats

- https://www.youtube.com/watch?v=VIDEO_ID
- https://youtu.be/VIDEO_ID
- youtube.com/watch?v=VIDEO_ID
- youtu.be/VIDEO_ID

## Requirements

- Python 3.7+
- yt-dlp
- tkinter (usually included with Python)
- FFmpeg (automatically handled by yt-dlp)

## Notes

- The application automatically validates YouTube URLs
- Invalid URLs are skipped with a warning message
- Downloads are saved with the video title as filename
- For MP3 conversion, audio is extracted at 192kbps quality
- The application supports stopping downloads mid-process

## Troubleshooting

If you encounter issues:

1. **FFmpeg errors**: yt-dlp will automatically download FFmpeg if needed
2. **Permission errors**: Make sure you have write access to the download directory
3. **Network errors**: Check your internet connection and try again
4. **URL errors**: Ensure URLs are valid YouTube links

## License

This project is for educational purposes. Respect YouTube's terms of service and copyright laws.
