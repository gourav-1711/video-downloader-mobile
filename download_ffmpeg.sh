#!/bin/bash
# Download pre-compiled FFmpeg binaries for Android
# These binaries are from ffmpeg-kit-full-gpl releases

set -e

echo "Downloading FFmpeg binaries for Android..."

# Create directories
mkdir -p ffmpeg_bin/arm64-v8a
mkdir -p ffmpeg_bin/armeabi-v7a

# FFmpeg Kit version (GPL version includes all codecs)
VERSION="6.0-2"
BASE_URL="https://github.com/arthenica/ffmpeg-kit/releases/download/v${VERSION}"

# Download arm64-v8a
echo "Downloading arm64-v8a binaries..."
curl -L "${BASE_URL}/ffmpeg-kit-full-gpl-${VERSION}-android-arm64-v8a.aar" -o /tmp/ffmpeg-arm64.aar
unzip -o /tmp/ffmpeg-arm64.aar "jni/arm64-v8a/*" -d /tmp/ffmpeg-arm64
# Extract the ffmpeg binary (it's named libffmpegkit.so in AAR)
# For standalone binaries, we'll use a different approach

# Alternative: Use pre-built static binaries
echo ""
echo "NOTE: FFmpeg Kit AARs contain libraries, not standalone binaries."
echo "For standalone ffmpeg/ffprobe binaries, download from:"
echo "  https://github.com/ArkGamer/ffmpeg-android/releases"
echo ""
echo "Or build using ffmpeg-android-maker:"
echo "  https://github.com/ArkGamer/ffmpeg-android-maker"
echo ""

# Clean up
rm -f /tmp/ffmpeg-arm64.aar

echo "Please manually download ffmpeg and ffprobe binaries for:"
echo "  - arm64-v8a (64-bit ARM)"
echo "  - armeabi-v7a (32-bit ARM)"
echo ""
echo "Place them in:"
echo "  ffmpeg_bin/arm64-v8a/ffmpeg"
echo "  ffmpeg_bin/arm64-v8a/ffprobe"
echo "  ffmpeg_bin/armeabi-v7a/ffmpeg"
echo "  ffmpeg_bin/armeabi-v7a/ffprobe"
