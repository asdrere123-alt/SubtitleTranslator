#!/bin/sh
# =============================================
# 🚀 AI Subtitle Translator - Auto Installer
# By Ahmed Ibrahim (@asdrere123-alt)
# =============================================


PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/SubtitleTranslator"
GITHUB_RAW="https://raw.githubusercontent.com/asdrere123-alt/SubtitleTranslator/main"

echo ""
echo "======================================"
echo "🤖 AI Subtitle Translator Installer"
echo "By Ahmed Ibrahim"
echo "======================================"
echo ""

# Create plugin folder
mkdir -p "$PLUGIN_DIR"

# Download main plugin file
echo "📥 Downloading plugin..."
wget -q "$GITHUB_RAW/plugin.pyc" -O "$PLUGIN_DIR/plugin.pyc"

if [ $? -eq 0 ]; then
    echo "✅ Plugin downloaded successfully!"
else
    echo "❌ Download failed! Check your internet connection."
    exit 1
fi

# Restart Enigma2
echo ""
echo "🔄 Restarting Enigma2..."
sleep 2
killall -9 enigma2
