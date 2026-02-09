"""YouTube Downloader - A Kivy app for downloading videos and audio."""

import threading
import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
import yt_dlp

# Import from local modules
from utils import (
    get_download_path,
    get_ffmpeg_location,
    scan_media_file,
    copy_to_public_downloads,
    request_storage_permission,
)
from ui import StyledBoxLayout, StyledProgressBar, GradientButton


# Set window background color
Window.clearcolor = (0.08, 0.08, 0.12, 1)  # Dark background


class DownloaderApp(App):
    def build(self):
        self.title = "Video Downloader"

        # Request storage permissions on Android
        request_storage_permission()

        # Main container
        main_layout = BoxLayout(orientation="vertical", padding=20, spacing=15)

        # Header
        header = Label(
            text="[b]Video Downloader[/b]",
            markup=True,
            font_size="28sp",
            size_hint=(1, 0.1),
            color=(1, 1, 1, 1),
        )
        main_layout.add_widget(header)

        # URL Input Card
        url_card = StyledBoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10,
            size_hint=(1, 0.15),
            bg_color=(0.12, 0.12, 0.18, 1),
        )

        url_label = Label(
            text="Video URL",
            size_hint=(1, 0.3),
            halign="left",
            color=(0.7, 0.7, 0.8, 1),
            font_size="14sp",
        )
        url_label.bind(size=url_label.setter("text_size"))
        url_card.add_widget(url_label)

        self.url_input = TextInput(
            hint_text="Paste YouTube URL here...",
            size_hint=(1, 0.7),
            multiline=False,
            background_color=(0.18, 0.18, 0.25, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.5, 0.5, 0.6, 1),
            cursor_color=(0.4, 0.6, 1, 1),
            padding=[15, 12],
        )
        url_card.add_widget(self.url_input)
        main_layout.add_widget(url_card)

        # Options Card
        options_card = StyledBoxLayout(
            orientation="vertical",
            padding=15,
            spacing=10,
            size_hint=(1, 0.25),
            bg_color=(0.12, 0.12, 0.18, 1),
        )

        options_label = Label(
            text="Download Options",
            size_hint=(1, 0.2),
            halign="left",
            color=(0.7, 0.7, 0.8, 1),
            font_size="14sp",
        )
        options_label.bind(size=options_label.setter("text_size"))
        options_card.add_widget(options_label)

        # Format and Quality row
        options_row = BoxLayout(
            orientation="horizontal", spacing=15, size_hint=(1, 0.8)
        )

        # Format Selection
        format_box = BoxLayout(orientation="vertical", spacing=5)
        format_label = Label(
            text="Format",
            size_hint=(1, 0.3),
            halign="left",
            color=(0.6, 0.6, 0.7, 1),
            font_size="12sp",
        )
        format_label.bind(size=format_label.setter("text_size"))
        format_box.add_widget(format_label)

        # Added "Playlist (Audio)" option
        self.format_spinner = Spinner(
            text="Both",
            values=("Audio", "Video", "Both", "Playlist (Audio)"),
            size_hint=(1, 0.7),
            background_color=(0.25, 0.25, 0.35, 1),
            color=(1, 1, 1, 1),
        )
        format_box.add_widget(self.format_spinner)
        options_row.add_widget(format_box)

        # Quality Selection
        quality_box = BoxLayout(orientation="vertical", spacing=5)
        quality_label = Label(
            text="Quality",
            size_hint=(1, 0.3),
            halign="left",
            color=(0.6, 0.6, 0.7, 1),
            font_size="12sp",
        )
        quality_label.bind(size=quality_label.setter("text_size"))
        quality_box.add_widget(quality_label)

        self.quality_spinner = Spinner(
            text="Best",
            values=("Best", "1080p", "720p", "480p", "360p"),
            size_hint=(1, 0.7),
            background_color=(0.25, 0.25, 0.35, 1),
            color=(1, 1, 1, 1),
        )
        quality_box.add_widget(self.quality_spinner)
        options_row.add_widget(quality_box)

        options_card.add_widget(options_row)
        main_layout.add_widget(options_card)

        # Download Button
        self.download_btn = GradientButton(
            text="Download",
            size_hint=(1, 0.12),
            font_size="18sp",
            bold=True,
            color=(1, 1, 1, 1),
            gradient_colors=[(0.4, 0.2, 0.8, 1)],
        )
        self.download_btn.bind(on_press=self.start_download)
        main_layout.add_widget(self.download_btn)

        # Progress Card
        progress_card = StyledBoxLayout(
            orientation="vertical",
            padding=20,
            spacing=10,
            size_hint=(1, 0.35),
            bg_color=(0.12, 0.12, 0.18, 1),
        )

        # Progress header with percentage
        progress_header = BoxLayout(orientation="horizontal", size_hint=(1, 0.25))

        self.status_label = Label(
            text="Ready to download",
            size_hint=(0.7, 1),
            halign="left",
            color=(0.7, 0.7, 0.8, 1),
            font_size="14sp",
        )
        self.status_label.bind(size=self.status_label.setter("text_size"))
        progress_header.add_widget(self.status_label)

        self.percent_label = Label(
            text="0%",
            size_hint=(0.3, 1),
            halign="right",
            color=(0.4, 0.8, 1, 1),
            font_size="18sp",
            bold=True,
        )
        self.percent_label.bind(size=self.percent_label.setter("text_size"))
        progress_header.add_widget(self.percent_label)
        progress_card.add_widget(progress_header)

        # Progress bar
        self.progress_bar = StyledProgressBar(size_hint=(1, 0.3))
        progress_card.add_widget(self.progress_bar)

        # Speed and ETA row
        stats_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.25))

        self.speed_label = Label(
            text="Speed: --",
            size_hint=(0.5, 1),
            halign="left",
            color=(0.5, 0.5, 0.6, 1),
            font_size="12sp",
        )
        self.speed_label.bind(size=self.speed_label.setter("text_size"))
        stats_row.add_widget(self.speed_label)

        self.eta_label = Label(
            text="ETA: --",
            size_hint=(0.5, 1),
            halign="right",
            color=(0.5, 0.5, 0.6, 1),
            font_size="12sp",
        )
        self.eta_label.bind(size=self.eta_label.setter("text_size"))
        stats_row.add_widget(self.eta_label)
        progress_card.add_widget(stats_row)

        # Size info
        self.size_label = Label(
            text="",
            size_hint=(1, 0.2),
            halign="center",
            color=(0.45, 0.45, 0.55, 1),
            font_size="11sp",
        )
        self.size_label.bind(size=self.size_label.setter("text_size"))
        progress_card.add_widget(self.size_label)

        main_layout.add_widget(progress_card)

        return main_layout

    def start_download(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_label.text = "Please enter a URL first!"
            self.status_label.color = (1, 0.4, 0.4, 1)
            return

        self.reset_progress()
        self.download_btn.disabled = True

        # Start download in background thread
        threading.Thread(
            target=self.run_download,
            args=(url, self.format_spinner.text, self.quality_spinner.text),
            daemon=True,
        ).start()

    def get_format_string(self, format_type, quality):
        """Generate yt-dlp format string based on user selection"""
        quality_map = {
            "Best": "",
            "1080p": "[height<=1080]",
            "720p": "[height<=720]",
            "480p": "[height<=480]",
            "360p": "[height<=360]",
        }
        q = quality_map.get(quality, "")

        if format_type == "Audio" or format_type == "Playlist (Audio)":
            return "bestaudio/best"
        elif format_type == "Video":
            return f"bestvideo{q}/best{q}"
        else:  # Both (Video + Audio)
            # Prefer pre-muxed formats to avoid FFmpeg merge issues
            if q:
                return f"best{q}/bestvideo{q}+bestaudio/best"
            return "best/bestvideo+bestaudio"

    def run_download(self, url, format_type, quality):
        """Main download function with fallback handling"""
        try:
            format_string = self.get_format_string(format_type, quality)
            download_path = get_download_path()

            # Custom logger for Android compatibility
            class QuietLogger:
                def debug(self, msg):
                    pass

                def warning(self, msg):
                    pass

                def error(self, msg):
                    pass

            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Base yt-dlp options
            ydl_opts = {
                "format": format_string,
                "outtmpl": {
                    "default": os.path.join(
                        download_path, f"download_{timestamp}.%(ext)s"
                    )
                },
                "progress_hooks": [self.progress_hook],
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "logger": QuietLogger(),
                "concurrent_fragment_downloads": 8,
                "buffersize": 1024 * 64,
                "http_chunk_size": 10485760,
                "format_sort": ["res", "ext:mp4:m4a:webm", "proto:https"],
            }

            # Playlist handling
            if format_type == "Playlist (Audio)":
                ydl_opts["noplaylist"] = False  # Enable playlist downloads
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            else:
                ydl_opts["noplaylist"] = True  # Single video only

            # Set FFmpeg location
            ffmpeg_loc = get_ffmpeg_location()
            if ffmpeg_loc:
                ydl_opts["ffmpeg_location"] = ffmpeg_loc

            # Audio format handling
            if format_type == "Audio":
                ydl_opts["postprocessors"] = [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ]
            elif format_type == "Both":
                ydl_opts["merge_output_format"] = "mkv"
                ydl_opts["postprocessor_args"] = {
                    "ffmpeg": ["-c", "copy", "-strict", "-2"]
                }

            # Try download with fallback for "Both" format
            try:
                self._do_download(ydl_opts, url)
            except Exception as merge_error:
                # If merge fails for "Both", fallback to pre-muxed video
                if format_type == "Both" and "post" in str(merge_error).lower():
                    Clock.schedule_once(
                        lambda dt: self.update_progress(
                            "Merge failed, trying fallback...", 50, "--", "--", ""
                        )
                    )
                    # Retry with simple "best" format (already has audio)
                    ydl_opts["format"] = "best"
                    ydl_opts.pop("merge_output_format", None)
                    ydl_opts.pop("postprocessor_args", None)
                    self._do_download(ydl_opts, url)
                else:
                    raise  # Re-raise if not a merge error

            Clock.schedule_once(lambda dt: self.download_complete())

        except Exception as e:
            error_msg = str(e)[:100]
            Clock.schedule_once(lambda dt: self.download_error(error_msg))

    def _do_download(self, ydl_opts, url):
        """Execute the actual download and copy to public folder"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info:
                # Handle playlist (multiple entries) or single video
                entries = info.get("entries", [info])
                for entry in entries:
                    if entry:
                        # Get the expected filename
                        expected_path = ydl.prepare_filename(entry)
                        base_path = os.path.splitext(expected_path)[0]

                        # Try to find the actual file (extension may differ after post-processing)
                        possible_extensions = [
                            ".mp3",
                            ".m4a",
                            ".mkv",
                            ".mp4",
                            ".webm",
                            ".opus",
                            ".ogg",
                        ]
                        actual_path = None

                        # First check if expected file exists
                        if os.path.exists(expected_path):
                            actual_path = expected_path
                        else:
                            # Search for file with different extension
                            for ext in possible_extensions:
                                test_path = base_path + ext
                                if os.path.exists(test_path):
                                    actual_path = test_path
                                    break

                        if actual_path and os.path.exists(actual_path):
                            filename_only = os.path.basename(actual_path)

                            # Copy to public Downloads
                            success = copy_to_public_downloads(
                                actual_path, filename_only
                            )
                            if success:
                                print(f"Saved to public: {filename_only}")
                                try:
                                    os.remove(actual_path)
                                except Exception:
                                    pass
                            else:
                                # Fallback: at least scan the private file
                                print(f"Copy failed, file at: {actual_path}")
                                scan_media_file(actual_path)
                        else:
                            print(f"File not found: {expected_path}")

    def progress_hook(self, d):
        if d["status"] == "downloading":
            percent = d.get("downloaded_bytes", 0) or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0) or 0

            # Format speed
            speed_raw = d.get("speed")
            if speed_raw is not None:
                try:
                    if speed_raw >= 1024 * 1024:
                        speed = f"{speed_raw / (1024 * 1024):.1f} MB/s"
                    elif speed_raw >= 1024:
                        speed = f"{speed_raw / 1024:.1f} KB/s"
                    else:
                        speed = f"{speed_raw:.0f} B/s"
                except (TypeError, ValueError):
                    speed = "--"
            else:
                speed = "--"

            # Format ETA
            eta_raw = d.get("eta")
            if eta_raw is not None:
                try:
                    eta_seconds = int(eta_raw)
                    if eta_seconds >= 3600:
                        eta = f"{eta_seconds // 3600}:{(eta_seconds % 3600) // 60:02d}:{eta_seconds % 60:02d}"
                    else:
                        eta = f"{eta_seconds // 60}:{eta_seconds % 60:02d}"
                except (TypeError, ValueError):
                    eta = "--"
            else:
                eta = "--"

            if total > 0:
                progress_pct = (percent / total) * 100
                downloaded_mb = percent / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                size_text = f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
            else:
                progress_pct = 0
                size_text = ""

            Clock.schedule_once(
                lambda dt, p=progress_pct, s=speed, e=eta, sz=size_text: self.update_progress(
                    "Downloading...", p, s, e, sz
                )
            )
        elif d["status"] == "finished":
            Clock.schedule_once(
                lambda dt: self.update_progress("Processing...", 100, "--", "--", "")
            )

    def update_progress(self, status, percent, speed, eta, size_text):
        self.status_label.text = status
        self.status_label.color = (0.4, 0.7, 1, 1)
        self.percent_label.text = f"{percent:.1f}%"
        self.progress_bar.progress = percent
        self.speed_label.text = f"Speed: {speed}"
        self.eta_label.text = f"ETA: {eta}"
        self.size_label.text = size_text

    def download_complete(self):
        self.status_label.text = "Download Complete!"
        self.status_label.color = (0.4, 0.9, 0.5, 1)
        self.percent_label.text = "100%"
        self.progress_bar.progress = 100
        self.speed_label.text = "Speed: --"
        self.eta_label.text = "ETA: Done!"
        self.size_label.text = ""
        self.download_btn.disabled = False

    def download_error(self, error):
        self.status_label.text = f"Error: {error}"
        self.status_label.color = (1, 0.4, 0.4, 1)
        self.percent_label.text = "--"
        self.progress_bar.progress = 0
        self.speed_label.text = ""
        self.eta_label.text = ""
        self.size_label.text = ""
        self.download_btn.disabled = False

    def reset_progress(self):
        self.status_label.text = "Starting download..."
        self.status_label.color = (1, 0.8, 0.2, 1)
        self.percent_label.text = "0%"
        self.progress_bar.progress = 0
        self.speed_label.text = "Speed: --"
        self.eta_label.text = "ETA: --"
        self.size_label.text = ""


if __name__ == "__main__":
    DownloaderApp().run()
