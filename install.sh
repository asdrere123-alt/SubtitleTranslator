#!/bin/sh
# ============================================================
# 🚀 Subtitle Translator public-installer
# Enhanced Clean-Install Script
# ============================================================

PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/SubtitleTranslator"
GITHUB_RAW="https://raw.githubusercontent.com/asdrere123-alt/SubtitleTranslator/main"

echo "================================================="
echo "🎯 Subtitle Translator - Professional Installer"
echo "================================================="

# 1. Force Remove Old Version
if [ -d "$PLUGIN_DIR" ]; then
    echo "🗑️  Removing old version found at $PLUGIN_DIR..."
    rm -rf "$PLUGIN_DIR"
fi

# 2. Recreate Directory
echo "📁 Preparing fresh installation folder..."
mkdir -p "$PLUGIN_DIR"

# 3. Download Latest Files
echo "🌐 Downloading latest release from GitHub..."
WGET_OPTS="--no-check-certificate"
wget -q $WGET_OPTS "$GITHUB_RAW/plugin.pyc?t=$(date +%s)" -O "$PLUGIN_DIR/plugin.pyc"
wget -q $WGET_OPTS "$GITHUB_RAW/plugin.png?t=$(date +%s)" -O "$PLUGIN_DIR/plugin.png"
wget -q $WGET_OPTS "$GITHUB_RAW/__init__.py?t=$(date +%s)" -O "$PLUGIN_DIR/__init__.py"

if [ $? -ne 0 ]; then
    echo "❌ Error: Download failed! Please check your internet connection."
    exit 1
fi

chmod 755 "$PLUGIN_DIR/plugin.pyc"

# 4. Handle Keys Configuration (Persistent)
KEYS_FILE="/etc/subtitle_keys.conf"
if [ ! -f "$KEYS_FILE" ]; then
    echo "🔑 No existing keys.conf found. Creating new template at $KEYS_FILE"
    echo "# Subtitle Translator API Keys Configuration" > "$KEYS_FILE"
    echo "# You can add multiple keys for Groq/Gemini to avoid limits" >> "$KEYS_FILE"
    echo "GROQ_KEY=" >> "$KEYS_FILE"
    echo "GROQ_KEY=" >> "$KEYS_FILE"
    echo "GEMINI_KEY=" >> "$KEYS_FILE"
    echo "GEMINI_KEY=" >> "$KEYS_FILE"
    echo "OCRSPACE_KEY=" >> "$KEYS_FILE"
    echo "APININJAS_KEY=" >> "$KEYS_FILE"
else
    echo "✅ Existing configuration preserved at $KEYS_FILE"
fi

echo "================================================="
echo "✅ Installation Complete!"
echo "🔄 Enigma2 is restarting to apply changes..."
echo "================================================="

# 5. Restart Enigma2
sync
killall -9 enigma2
exit 0
