# ClawApp Creator

ClawApp Creator is a skill project for OpenClaw / Codex. It helps turn static front-end apps and mini-games into CLAWSPACE-compatible app packages, then uploads them to the production site when the user wants to publish.

It is designed for two common cases:

- Start a small app or mini-game from scratch
- Adapt an existing static front-end project into a platform-ready zip package

Production platform:

- Website: [https://www.nima-tech.space](https://www.nima-tech.space)
- Skill on ClawHub: [https://clawhub.ai/NimaChu/clawapp-creator](https://clawhub.ai/NimaChu/clawapp-creator)

## First-Time Flow

For a first-time user, this is the smoothest path:

1. Let ClawApp Creator register a CLAWSPACE account for you
2. Save reusable upload credentials
3. Package the app
4. Run a dry-run check
5. Upload and receive the detail, launch, and download links

If you prefer to register manually, you can do that first on the website:

- [https://www.nima-tech.space/register](https://www.nima-tech.space/register)

## What It Does

- Generates a compliant `manifest.json`
- Generates or fills in a `README.md`
- Validates the package structure
- Checks risky asset paths
- Checks whether a slug is available
- Searches public apps on CLAWSPACE
- Downloads public CLAWSPACE app zip packages
- Supports dry-run validation before upload
- Supports direct uploads and large-package Blob uploads
- Supports both plaintext config storage and macOS Keychain storage
- Helps choose between `none / text / multimodal / code` model categories
- Includes OCR / image-analysis starter support
- Returns detail, launch, download, and share-ready links after upload

## Main Files

- `SKILL.md`: Main skill instructions
- `scripts/scaffold_mini_game.py`: Generate a mini-game scaffold
- `scripts/build_nima_package.py`: Build a platform zip package
- `scripts/register_clawspace_account.py`: Register a new account and save upload config
- `scripts/setup_upload_config.py`: Configure credentials for an existing account
- `scripts/upload_nima_package.py`: Validate and upload a package
- `references/platform-contract.md`: Packaging rules
- `references/model-api.md`: Platform model API guide

## Quick Start

### 1. Scaffold a new mini-game

```bash
python3 scripts/scaffold_mini_game.py \
  --out /path/to/new-project \
  --name "Orbit Tap" \
  --description "A lightweight game about tapping planets on an orbit."
```

### 1b. Scaffold an OCR / multimodal app

```bash
python3 scripts/scaffold_mini_game.py \
  --template ocr-tool \
  --out /path/to/ocr-tool \
  --name "Online OCR Tool" \
  --description "Upload an image and extract text, tables, or visual content."
```

### 2. Build a package

```bash
python3 scripts/build_nima_package.py \
  --app-dir /path/to/app \
  --manifest /path/to/manifest.json \
  --out /path/to/output.zip \
  --readme /path/to/README.md \
  --assets-dir /path/to/assets
```

### 3. Register a new CLAWSPACE account

```bash
python3 scripts/register_clawspace_account.py
```

This creates the account and saves reusable upload credentials in one step.

Recommended first-time options:

- Let ClawApp Creator register the account and save the upload config for you
- Or register manually first at [https://www.nima-tech.space/register](https://www.nima-tech.space/register)

Non-interactive example:

```bash
python3 scripts/register_clawspace_account.py \
  --site-url https://www.nima-tech.space \
  --display-name "Your Name" \
  --email you@example.com \
  --password 'your-password' \
  --password-store keychain \
  --non-interactive
```

### 4. Configure upload credentials for an existing account

```bash
python3 scripts/setup_upload_config.py
```

On macOS you can choose Keychain storage instead of storing the password in plaintext config.

Default production site:

```text
https://www.nima-tech.space
```

### 5. Dry-run before upload

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --dry-run
```

### 6. Upload

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --model-category none
```

### 7. Search public apps on CLAWSPACE

```bash
python3 scripts/search_clawspace_apps.py "ocr"
```

### 8. Download a public app package

```bash
python3 scripts/download_clawspace_app.py orbit-heist --out-dir /path/to/downloads
```

## Publish Mode Prompts

These direct prompts work well in OpenClaw:

- `Help me make a mini-game that can be uploaded to CLAWSPACE`
- `Turn this project into a publishable CLAWSPACE app`
- `Help me publish this app directly`

In publish mode, the skill should diagnose, package, verify slug ownership, upload, and return the final links.

## Supported Templates

- `starter-mini-game`
- `starter-ocr`
- `starter-memory-flip`
- `starter-focus-timer`
- `starter-ai-rewriter`

## Notes

- The target platform currently supports static front-end apps and mini-games.
- The final zip should stay within `25MB`.
- The same account can overwrite its own slug.
- Different accounts cannot overwrite each other's slug.
- New users can register directly through `scripts/register_clawspace_account.py`.
- Existing users should use `scripts/setup_upload_config.py` instead of registering again.
- Public search and download use the production site at `https://www.nima-tech.space`.
- If ClawHub is rate limited, users can still install the skill from GitHub.

## Repository Role

This repository is the source of the `clawapp-creator` skill and can also be installed directly into Codex skills directories.
