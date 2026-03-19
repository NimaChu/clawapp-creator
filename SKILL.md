---
name: clawapp-creator
description: Build or adapt static front-end apps and mini-games so they match the Nima Tech Space upload format, optionally wire the platform LLM API, package a compliant zip, and upload it to the site. Use when Codex needs to help OpenClaw users create, retrofit, package, validate, or publish an app/game for the platform.
---

# ClawApp Creator

Build the smallest working app package that can be uploaded to Nima Tech Space, then upload it if the user wants.

## Publish Mode

Treat the following requests as a direct publish workflow:

- "帮我做一个可上传到 CLAWSPACE 的小游戏"
- "把这个项目变成 CLAWSPACE 可发布应用"
- "帮我直接发布这个应用"

In publish mode:

1. diagnose the project
2. fix or scaffold the app
3. package it
4. verify slug ownership
5. upload it
6. return the final links and a ready-to-share summary

## Workflow

1. Confirm the app can be shipped as a static front-end.
2. Build or fix the app until it outputs a static bundle.
3. Decide whether the app needs a model.
4. Generate a compliant `manifest.json`, optional `README.md`, and `assets/`.
5. If there is no project yet, scaffold one with `scripts/scaffold_mini_game.py`.
6. Package everything into a zip with `scripts/build_nima_package.py`.
7. Diagnose with `scripts/diagnose_nima_package.py` before upload when helpful.
8. Upload with `scripts/upload_nima_package.py` when the user wants publishing.
9. Verify the detail page and launch page after upload.

## Package Rules

Read [references/platform-contract.md](./references/platform-contract.md) before packaging.

Always enforce these minimum rules:

- Ship only static front-end apps or mini-games.
- Put built files under `app/`.
- Keep the entry file inside `app/`, usually `app/index.html`.
- Keep package root flat: `manifest.json`, optional `README.md`, optional `assets/`, required `app/`.
- Default `modelCategory` to `none` unless the app truly needs AI.
- Keep the zip at or under `25MB`.
- Remember slug ownership: the same account can overwrite its own slug, but another user's slug must not be reused.

## Model Rules

If the app does not need AI, keep `modelCategory` as `none`.

If the app needs AI, prefer the platform API instead of any user-supplied API key:

- Endpoint: `POST /api/llm/chat`
- Required field: `appId`
- Allowed categories: `text`, `multimodal`, `code`

Read [references/model-api.md](./references/model-api.md) when wiring AI.

Tell the user the platform can provide a free shared model path when they choose a model category during upload.

Do not embed third-party model keys in client code.

## Packaging

Use `assets/manifest.example.json` as the starting template.

Use `assets/README.template.md` as the starting template when the app needs a basic product readme.

If the user wants to start from zero instead of retrofitting an existing app, copy one of these starter assets first:

- `assets/starter-mini-game/` for a no-model static game
- `assets/platform-llm-client.js` for a minimal platform model client

Or scaffold directly:

```bash
python3 scripts/scaffold_mini_game.py \
  --out /path/to/new-project \
  --name "Orbit Tap" \
  --slug orbit-tap \
  --description "点击轨道行星的轻量小游戏。"
```

Use:

```bash
python3 scripts/build_nima_package.py \
  --app-dir /path/to/dist \
  --manifest /path/to/manifest.json \
  --out /path/to/output.zip \
  --readme /path/to/README.md \
  --assets-dir /path/to/assets
```

The script validates the structure, checks the required fields, checks the size limit, and builds the final zip.
It also warns about high-risk asset references like root-absolute `/assets/...` paths or remote `http/https` URLs inside the packaged front-end.

For project diagnosis, use:

```bash
python3 scripts/diagnose_nima_package.py \
  --app-dir /path/to/app-or-dist \
  --manifest /path/to/manifest.json
```

This checks:

- resource paths
- slug quality
- manifest presence
- likely external model key usage
- whether `modelCategory` looks more suitable as `none`, `text`, `multimodal`, or `code`

## Uploading

Production site:

- Website: `https://www.nima-tech.space`
- Base API URL: `https://www.nima-tech.space`

Use `upload-config.json` in the skill folder as the default reusable credential file. Ask the user once, then store:

- `siteUrl`
- `email`
- `password`

Leave the file empty by default. Reuse it on later uploads unless the user wants to override it.

When saving credentials, prefer file permission `600`.
On macOS, prefer saving the password to Keychain and keeping `upload-config.json` as site metadata plus fallback config.
Keep the original plaintext-password config flow available as a backup option for users who prefer simple portability.

For the first-time setup, prefer:

```bash
python3 scripts/setup_upload_config.py
```

Or in non-interactive mode:

```bash
python3 scripts/setup_upload_config.py \
  --site-url https://www.nima-tech.space \
  --email user@example.com \
  --password 'password' \
  --password-store keychain \
  --non-interactive
```

This setup script verifies the credentials by calling the real login endpoint before saving them.
It now validates:

- site URL format, with a real example
- email format
- login credentials before saving

Supported password stores are:

- `config`: store the password in `upload-config.json`
- `keychain`: store the password in macOS Keychain and keep config file password empty
- `both`: store in both places

Use:

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --model-category none \
  --site-url https://www.nima-tech.space \
  --email user@example.com \
  --password 'password' \
  --save-config
```

If you want to validate everything except the final upload, use:

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --dry-run
```

Use `none` unless the app truly needs the platform model.

The upload script reads missing values from `upload-config.json`, logs in, sends the package to `/api/import-app`, and prints the resulting detail and launch URLs.
After upload, it also prints plain-text app links so the user can open the detail page immediately.
If `useKeychain` is enabled in the config and no explicit password was passed, the upload script will try macOS Keychain before failing.

During upload, report progress in stages:

- current stage
- what is already done
- what comes next

Before uploading, check whether the slug is available:

- If it is new, upload normally.
- If it belongs to the same account, explain that this upload will overwrite the older version.
- If it belongs to another account, stop and tell the user to change the slug before packaging again.

If the package is too large for a direct Vercel function upload, use the site's Blob client-upload flow instead of failing early.

Only auto-upload after the user has provided valid site credentials or already has them stored in `upload-config.json`. If credentials are unavailable, stop after packaging and tell the user they need to register, log in once, and save or provide their credentials.

If login fails, tell the user to rerun:

```bash
python3 scripts/setup_upload_config.py
```

and refresh the stored credentials.

## Verification

After packaging or uploading:

- Open the generated zip and confirm it contains the expected root structure.
- If uploaded, open the detail page.
- If uploaded, open the launch page.
- If the app uses the platform model, test one real request through the site.
- After upload, provide the final share summary with app name, detail page, launch page, and download link.
- Also print a ready-to-copy share text block after upload.

## Common Fixes

- If assets do not load after upload, switch the app build to relative asset paths.
- If the packer warns about `http/https` resources, bundle those assets locally when possible instead of depending on third-party URLs.
- If the packer warns about `/assets/...` paths, rewrite them to relative paths such as `./assets/...`.
- If the upload is rejected, check `entry`, root structure, and zip size first.
- If the upload fails because the slug is already owned by someone else, change the slug in `manifest.json` and rebuild the zip.
- If the app uses AI and fails after upload, confirm the uploaded `modelCategory` matches the app’s actual use case.
- If the app only needs deterministic gameplay or local logic, remove model usage and keep `modelCategory` as `none`.
- If the user has no project yet, scaffold from `assets/starter-mini-game/` instead of inventing files from scratch.
