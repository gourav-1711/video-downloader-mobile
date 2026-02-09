"""Android-specific helper functions for the Video Downloader app."""

import os
import shutil
from kivy.utils import platform


def get_download_path():
    """Get a writable path that works on Android 10+ without special permissions"""
    if platform == "android":
        from jnius import autoclass, cast
        from android import mActivity

        # Use App-Specific External Storage
        context = cast("android.content.Context", mActivity.getApplicationContext())
        file_p = context.getExternalFilesDir(None)
        download_path = os.path.join(file_p.getAbsolutePath(), "Download")
    else:
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

            Context = autoclass("android.content.Context")
            context = cast(Context, mActivity.getApplicationContext())
            app_info = context.getApplicationInfo()
            native_lib_dir = app_info.nativeLibraryDir

            source_ffmpeg = os.path.join(native_lib_dir, "libffmpeg.so")

            if not os.path.exists(source_ffmpeg):
                print(f"Error: libffmpeg.so not found at {source_ffmpeg}")
                return None

            files_dir = context.getFilesDir().getAbsolutePath()
            bin_dir = os.path.join(files_dir, "bin")
            os.makedirs(bin_dir, exist_ok=True)

            target_ffmpeg = os.path.join(bin_dir, "ffmpeg")

            if os.path.exists(target_ffmpeg):
                if os.path.realpath(target_ffmpeg) != source_ffmpeg:
                    os.remove(target_ffmpeg)
                    os.symlink(source_ffmpeg, target_ffmpeg)
            else:
                os.symlink(source_ffmpeg, target_ffmpeg)

            return bin_dir

        except Exception as e:
            print(f"FFmpeg setup error: {e}")
            return None

    return None


def scan_media_file(filepath):
    """Make downloaded file visible in Android gallery/file manager"""
    if platform == "android":
        try:
            from android import mActivity
            from jnius import autoclass

            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            File = autoclass("java.io.File")

            intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
            intent.setData(Uri.fromFile(File(filepath)))
            mActivity.sendBroadcast(intent)
        except Exception:
            pass


def request_storage_permission():
    """
    Request MANAGE_EXTERNAL_STORAGE permission (Android 11+).
    Opens settings if not already granted.
    Returns True if permission is granted.
    """
    if platform == "android":
        try:
            from android.permissions import request_permissions, Permission
            from jnius import autoclass
            from android import mActivity

            # Request standard permissions first
            request_permissions(
                [
                    Permission.INTERNET,
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ]
            )

            # Check for "All Files Access" (Android 11+)
            Environment = autoclass("android.os.Environment")
            if not Environment.isExternalStorageManager():
                # Send user to Settings to enable it
                Intent = autoclass("android.content.Intent")
                Settings = autoclass("android.provider.Settings")
                Uri = autoclass("android.net.Uri")

                intent = Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION)
                uri = Uri.parse("package:" + mActivity.getPackageName())
                intent.setData(uri)
                mActivity.startActivity(intent)
                return False
            return True
        except Exception as e:
            print(f"Permission request error: {e}")
            return False
    return True


def copy_to_public_downloads(private_file_path, filename):
    """
    Copies a file from the app-private folder to the public Download folder.
    Uses simple shutil.move with MANAGE_EXTERNAL_STORAGE permission.
    """
    if platform == "android":
        try:
            if not os.path.exists(private_file_path):
                print(f"Source not found: {private_file_path}")
                return False

            # Direct path to public Downloads
            public_dir = "/storage/emulated/0/Download/Video-Downloader"
            os.makedirs(public_dir, exist_ok=True)

            dest_path = os.path.join(public_dir, filename)

            # Move the file
            shutil.move(private_file_path, dest_path)
            print(f"Moved to: {dest_path}")

            # Scan so it shows up immediately
            scan_media_file(dest_path)
            return True

        except Exception as e:
            print(f"Error copying to public downloads: {e}")
            import traceback

            traceback.print_exc()
            return False

    return False
