"""Android-specific helper functions for the YouTube Downloader app."""

import os
from kivy.utils import platform


def get_download_path():
    """Get a writable path that works on Android 10+ without special permissions"""
    if platform == "android":
        from jnius import autoclass, cast
        from android import mActivity

        # Use App-Specific External Storage
        # Path: /sdcard/Android/data/org.pyapp.ytdownloader/files/Download
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
    """Show a short toast message on Android (Thread-safe)"""
    if platform == "android":
        from jnius import autoclass, cast, PythonJavaClass, java_method
        from android import mActivity

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        currentActivity = cast("android.app.Activity", PythonActivity.mActivity)
        JString = autoclass("java.lang.String")
        Toast = autoclass("android.widget.Toast")

        class ToastRunnable(PythonJavaClass):
            __javainterfaces__ = ["java/lang/Runnable"]
            __javacontext__ = "app"

            def __init__(self, message):
                self.message = message
                super().__init__()

            @java_method("()V")
            def run(self):
                try:
                    t = Toast.makeText(
                        currentActivity.getApplicationContext(),
                        JString(self.message),
                        Toast.LENGTH_LONG,
                    )
                    t.show()
                except Exception as e:
                    print(f"Toast error: {e}")

        currentActivity.runOnUiThread(ToastRunnable(message))
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

            # Java classes
            Context = autoclass("android.content.Context")
            MediaStore = autoclass("android.provider.MediaStore")
            ContentValues = autoclass("android.content.ContentValues")
            FileInputStream = autoclass("java.io.FileInputStream")
            Integer = autoclass("java.lang.Integer")

            # Get the Content Resolver (the system service that handles files)
            context = cast(Context, mActivity.getApplicationContext())
            resolver = context.getContentResolver()

            # Set up the new file details
            content_values = ContentValues()
            content_values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename)

            # Detect MIME type from extension
            if filename.endswith(".mp3"):
                mime_type = "audio/mpeg"
            elif filename.endswith(".m4a"):
                mime_type = "audio/mp4"
            elif filename.endswith(".mkv"):
                mime_type = "video/x-matroska"
            elif filename.endswith(".webm"):
                mime_type = "video/webm"
            else:
                mime_type = "video/mp4"

            content_values.put(MediaStore.MediaColumns.MIME_TYPE, mime_type)
            content_values.put(
                MediaStore.MediaColumns.RELATIVE_PATH, "Download/YouTube-Downloader"
            )

            # Set IS_PENDING = 1 so other apps don't see the file while we copy
            content_values.put("is_pending", Integer(1))

            # Insert the empty file into MediaStore
            uri = resolver.insert(
                MediaStore.Downloads.EXTERNAL_CONTENT_URI, content_values
            )

            if uri:
                # Open streams to copy data
                out_stream = resolver.openOutputStream(uri)
                in_stream = FileInputStream(private_file_path)

                # Copy in chunks (4KB buffer)
                buffer = bytearray(4096)
                while True:
                    bytes_read = in_stream.read(buffer)
                    if bytes_read == -1:
                        break
                    out_stream.write(buffer, 0, bytes_read)

                in_stream.close()
                out_stream.close()

                # Now that copy is done, set IS_PENDING = 0 to reveal the file
                content_values.clear()
                content_values.put("is_pending", Integer(0))
                resolver.update(uri, content_values, None, None)

                return True  # Success!

        except Exception as e:
            print(f"Error copying to public downloads: {e}")
            toast(f"Copy failed: {str(e)[:50]}")  # Show user why it failed
            return False

    return False
