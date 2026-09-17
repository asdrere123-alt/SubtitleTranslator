#!/bin/sh
# Download a complete update before replacing the installed Enigma2 plugin.
set -eu

PLUGIN_DIR="/usr/lib/enigma2/python/Plugins/Extensions/SubtitleTranslator"
KEYS_FILE="/etc/subtitle_keys.conf"
GITHUB_RAW="https://raw.githubusercontent.com/asdrere123-alt/SubtitleTranslator/main"

if [ "$(id -u)" != "0" ]; then
    echo "Error: run this installer as root." >&2
    exit 1
fi
command -v wget >/dev/null 2>&1 || { echo "Error: wget is required." >&2; exit 1; }

PARENT_DIR=$(dirname "$PLUGIN_DIR")
mkdir -p "$PARENT_DIR"
STAGING_DIR=$(mktemp -d "$PARENT_DIR/.subtitle-install.XXXXXX")
BACKUP_DIR="$STAGING_DIR/previous"
cleanup() {
    if [ -d "$BACKUP_DIR" ] && [ ! -e "$PLUGIN_DIR" ]; then
        if ! mv "$BACKUP_DIR" "$PLUGIN_DIR"; then
            echo "Error: restore the previous installation from $BACKUP_DIR" >&2
            return
        fi
    fi
    rm -rf "$STAGING_DIR"
}
trap cleanup 0
trap 'exit 1' 1 2 15
mkdir "$STAGING_DIR/new"

echo "Downloading Subtitle Translator..."
for file in plugin.pyc plugin.png __init__.py; do
    if ! wget -q -O "$STAGING_DIR/new/$file" "$GITHUB_RAW/$file"; then
        echo "Error: failed to download $file. Existing installation preserved." >&2
        exit 1
    fi
done
# __init__.py is intentionally empty in this repository.
if [ ! -s "$STAGING_DIR/new/plugin.pyc" ] || [ ! -s "$STAGING_DIR/new/plugin.png" ]; then
    echo "Error: incomplete download. Existing installation preserved." >&2
    exit 1
fi
chmod 755 "$STAGING_DIR/new"
chmod 644 "$STAGING_DIR/new/"*

# Never truncate or replace an existing keys file.
if [ ! -e "$KEYS_FILE" ] && [ ! -L "$KEYS_FILE" ]; then
    (
        umask 077
        set -C
        cat > "$KEYS_FILE" <<'KEYS'
# Subtitle Translator API Keys Configuration
# Multiple Groq/Gemini keys may be entered, one per line.
# Respect each provider's terms and quotas.
GROQ_KEY=
GEMINI_KEY=
OCRSPACE_KEY=
APININJAS_KEY=
GOOGLE_KEY=
KEYS
    )
else
    echo "Existing API-key configuration preserved."
fi

if [ -e "$PLUGIN_DIR" ]; then
    mv "$PLUGIN_DIR" "$BACKUP_DIR"
fi
# The exit trap restores the backup if this move fails.
mv "$STAGING_DIR/new" "$PLUGIN_DIR"
rm -f /tmp/subtitle_translator.log /tmp/subtitle_translator.log.old /tmp/subtitle_cache.json

echo "Installation complete. Restarting the Enigma2 GUI..."
sync
if ! killall -9 enigma2; then
    echo "Please restart the Enigma2 GUI manually."
fi
