# Subtitle Translator for Enigma2

![Subtitle Translator](plugin.png)

AI-powered subtitle translation and OCR for Enigma2 receivers, with an optional
Tesseract OCR server that runs on another computer on your local network.

## Highlights

- Supports Groq and Gemini for text translation.
- Offers cloud OCR options, including OCR.space, and local Tesseract OCR.
- Accepts multiple Groq and Gemini keys in the configuration file.
- Offers a local OCR server to move heavy OCR work off the receiver.
- Keeps temporary subtitle data in memory where possible to reduce disk writes.

## Requirements

- An Enigma2 receiver with a Python version compatible with the distributed
  `plugin.pyc`. Python bytecode is version-specific; Python 3 alone does not
  guarantee compatibility.
- Internet access for cloud translation or OCR providers.
- Your own API key for each selected cloud provider that requires one.

Enigma2 distributions differ significantly. If the plugin does not work on
your image, open a bug report and include the image name, image version,
receiver model, Python version, and the relevant log output.

## Installation

Download and inspect the installer over SSH on the receiver, then run it as
root. Finish any active recording first because installation restarts the GUI.

```sh
wget -O /tmp/subtitle-translator-install.sh \
  https://raw.githubusercontent.com/asdrere123-alt/SubtitleTranslator/main/install.sh
cat /tmp/subtitle-translator-install.sh
# Run only after the download succeeds and you have reviewed the script:
sh /tmp/subtitle-translator-install.sh
```

The installer downloads the plugin to:

```text
/usr/lib/enigma2/python/Plugins/Extensions/SubtitleTranslator
```

It then restarts the Enigma2 GUI. Existing API-key configuration is preserved
during updates.

If HTTPS certificate verification fails, check the receiver's date/time and
update its CA certificates before retrying.

## Configuration

API keys can be entered in the plugin settings or stored in:

```text
/etc/subtitle_keys.conf
```

Example:

```conf
# Add one key per line. Multiple Groq and Gemini keys are allowed.
GROQ_KEY=gsk_example
GEMINI_KEY=AIza_example
OCRSPACE_KEY=example
APININJAS_KEY=example
GOOGLE_KEY=example
```

Use multiple keys only within the provider's terms and quotas. Never commit
real API keys to GitHub or post them in an issue. Provider names,
limits, models, and pricing can change; consult each provider before use.

## Local OCR

Local OCR runs Tesseract on another computer on the same network, reducing the
receiver's processing load.

1. Install Tesseract OCR:
   - Windows: use a trusted Tesseract distribution.
   - macOS: `brew install tesseract`
   - Debian/Ubuntu: `sudo apt install tesseract-ocr`
   Ensure the English language data (`eng`) is installed: the server currently
   uses English OCR.
2. Clone this repository on the computer that will run OCR. Use Python 3.9 or
   newer for the listed server dependencies.
3. Install the Python dependencies:

   ```sh
   python -m pip install -r requirements-local-ocr.txt
   ```

4. Start the server:

   ```sh
   python local_ocr.py
   ```

5. In the plugin settings, set the local server URL to:

   ```text
   http://<COMPUTER_IP>:8000/ocr
   ```

The local OCR server listens on all network interfaces and has no authentication
or HTTPS. Restrict port `8000` to your receiver using your computer's firewall;
do not forward it to the internet. It prints recognized text to the terminal.
Local OCR keeps image processing on your computer, but cloud translation can
still send the recognized text to the selected translation provider.

## Privacy and security

When a cloud provider is selected, subtitle text or captured subtitle images
may be sent to that provider for processing. Review the selected provider's
privacy terms before use. API keys are stored locally on the receiver; keep
the receiver, configuration file, and logs private.

See [SECURITY.md](SECURITY.md) for handling sensitive reports and credentials.

## Logs and troubleshooting

The plugin writes diagnostic information to:

```text
/tmp/subtitle_translator.log
```

Before sharing a log, remove API keys, tokens, local IP addresses, and any
subtitle text you consider private.

Common checks:

- Confirm that the receiver has internet access and its date/time is correct.
- Confirm that the selected API key is valid and has remaining quota.
- Verify that the channel is currently broadcasting subtitles.
- For local OCR, confirm that port `8000` is reachable from the receiver.

## Contributing

Bug reports, compatibility results, documentation improvements, and focused
pull requests are welcome. Please use the provided issue templates and avoid
including credentials or private subtitle content.

## Source availability and licensing

The receiver plugin is currently distributed as compiled `plugin.pyc`; its
`plugin.py` source is not included. The local OCR server and installer source
are available in this repository. No project license has been selected here.
Public repository access alone should not be interpreted as an open-source
license or permission to redistribute the software.

## Maintainer

Developed and maintained by [Ahmed Ibrahim](https://github.com/asdrere123-alt).
