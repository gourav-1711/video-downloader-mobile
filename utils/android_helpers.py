"""Android-specific helper functions for the Video Downloader app."""

import os
from kivy.utils import platform


def get_download_path():
    """Get a writable path that works on Android 10+ without special permissions"""
    if platform == "android":
        from jnius import autoclass, cast
        from android import mActivity

        # Use App-Specific External Storage
        # Path: /sdcard/Android/data/org.pyapp.videodownloader/files/Download
        context = cast("android.content.Context", mActivity.getApplicationContext())

        # getExternalFilesDir(None) gives us the private app folder on SD card
        file_p = context.getExternalFilesDir(None)
        download_path = os.path.join(file_p.getAbsolutePath(), "Download")
    else:
        # Desktop fallback
        download_path = os.path.expanduser("~/Downloads")

    if not os.path.exists(download_path):
        os.makedirs(download_path)
    return download_path


def get_ffmpeg_location():
    """Locate the pre-installed 'fake library' FFmpeg"""
    if platform == "android":
        try:
            from jnius import autoclass, cast
            from android import mActivity

            # 1. Find the read-only executable in the system library path
            Context = autoclass("android.content.Context")
            context = cast(Context, mActivity.getApplicationContext())
            app_info = context.getApplicationInfo()
            native_lib_dir = app_info.nativeLibraryDir

            # The system installed it here because we named it .so
            source_ffmpeg = os.path.join(native_lib_dir, "libffmpeg.so")

            # 2. Verify it exists
            if not os.path.exists(source_ffmpeg):
                print(f"Error: libffmpeg.so not found at {source_ffmpeg}")
                return None

            # 3. Create a symlink named "ffmpeg" in our writable folder
            # yt-dlp needs the file to be named "ffmpeg", not "libffmpeg.so"
            files_dir = context.getFilesDir().getAbsolutePath()
            bin_dir = os.path.join(files_dir, "bin")
            os.makedirs(bin_dir, exist_ok=True)

            target_ffmpeg = os.path.join(bin_dir, "ffmpeg")

            # Re-create the link if needed
            if os.path.exists(target_ffmpeg):
                if os.path.realpath(target_ffmpeg) != source_ffmpeg:
                    os.remove(target_ffmpeg)
                    os.symlink(source_ffmpeg, target_ffmpeg)
            else:
                os.symlink(source_ffmpeg, target_ffmpeg)

            # Return the DIRECTORY containing the 'ffmpeg' link
            return bin_dir

        except Exception as e:
            print(f"FFmpeg setup error: {e}")
            return None

    return None  # Use system default on desktop


def scan_media_file(filepath):
    """Make downloaded file visible in Android gallery/file manager"""
    if platform == "android":
        try:
            from android import mActivity
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            File = autoclass("java.io.File")

            # Broadcast to media scanner
            intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
            intent.setData(Uri.fromFile(File(filepath)))
            mActivity.sendBroadcast(intent)
        except Exception:
            pass  # Silently fail on non-Android


def toast(message):
    """Show a short toast message on Android - simplified version"""
    if platform == "android":
        try:
            from android.runnable import run_on_ui_thread

            @run_on_ui_thread
            def show_toast(msg):
                from jnius import autoclass
                from android import mActivity

                Toast = autoclass("android.widget.Toast")
                context = mActivity.getApplicationContext()
                Toast.makeText(context, msg, Toast.LENGTH_LONG).show()

            show_toast(str(message))
        except Exception as e:
            print(f"Toast failed: {e}")
    else:
        print(f"TOAST: {message}")


def copy_to_public_downloads(private_file_path, filename):
    """
    Copies a file from the app-private folder to the public Download folder
    using the Android MediaStore API (Works on Android 10+).
    """
    if platform == "android":
        try:
            from jnius import autoclass, cast
            from android import mActivity

            # Check if source file exists
            if not os.path.exists(private_file_path):
                print(f"Source not found: {private_file_path}")
                return False

            # Java classes
            Context = autoclass("android.content.Context")
            MediaStore = autoclass("android.provider.MediaStore")
            ContentValues = autoclass("android.content.ContentValues")
            FileInputStream = autoclass("java.io.FileInputStream")
            Integer = autoclass("java.lang.Integer")

            # Get the Content Resolver
            context = cast(Context, mActivity.getApplicationContext())
            resolver = context.getContentResolver()

            # Set up the new file details
            content_values = ContentValues()
            content_values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename)

            # Detect MIME type from extension
            ext = filename.lower()
            if ext.endswith(".mp3"):
                mime_type = "audio/mpeg"
            elif ext.endswith(".m4a"):
                mime_type = "audio/mp4"
            elif ext.endswith(".mkv"):
                mime_type = "video/x-matroska"
            elif ext.endswith(".webm"):
                mime_type = "video/webm"
            elif ext.endswith(".opus"):
                mime_type = "audio/opus"
            else:
                mime_type = "video/mp4"

            content_values.put(MediaStore.MediaColumns.MIME_TYPE, mime_type)
            content_values.put(
                MediaStore.MediaColumns.RELATIVE_PATH, "Download/Video-Downloader"
            )

            # Set IS_PENDING = 1 so other apps don't see the file while we copy
            content_values.put(MediaStore.MediaColumns.IS_PENDING, Integer(1))

            # Insert the empty file into MediaStore
            uri = resolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI, content_values
            )

            if uri is None:
                print("MediaStore insert failed - no URI returned")
                return False

            # Open streams to copy data
            out_stream = resolver.openOutputStream(uri)
            if out_stream is None:
                print("Failed to open output stream")
                return False

            in_stream = FileInputStream(private_file_path)

            # Simple byte-by-byte copy using Java streams
            byte_array = bytearray(8192)
            while True:
                bytes_read = in_stream.read(byte_array)
                if bytes_read == -1:
                    break
                # Convert to Java byte array for writing
                out_stream.write(byte_array[:bytes_read])

            in_stream.close()
            out_stream.close()

            # Now that copy is done, set IS_PENDING = 0 to reveal the file
            update_values = ContentValues()
            update_values.put(MediaStore.MediaColumns.IS_PENDING, Integer(0))
            resolver.update(uri, update_values, None, None)

            print(f"Successfully copied to public downloads: {filename}")
            return True

        except Exception as e:
            print(f"Error copying to public downloads: {e}")
            import traceback

            traceback.print_exc()
            return False

    return False
