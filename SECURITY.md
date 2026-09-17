# Security policy

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability or expose API
keys, tokens, receiver addresses, or private subtitle content.

If the repository's **Security** tab offers **Report a vulnerability**, use
that private reporting option. Otherwise, open a minimal issue asking the
maintainer to arrange a private reporting channel, without vulnerability
details or credentials. Share reproduction steps and impact only through the
private channel once it is available. Redact credentials and personal data.

## API keys and subtitle data

API keys are stored locally in `/etc/subtitle_keys.conf`. Never commit this
file or paste its contents into an issue. Depending on the configured provider,
subtitle text or captured subtitle images may be sent to a third-party service
for processing. Review that provider's terms and privacy policy before use.
