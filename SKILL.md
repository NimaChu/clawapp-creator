---
name: clawapp-creator
description: Build or adapt static front-end apps and mini-games so they match the Nima Tech Space upload format, optionally wire the platform LLM API, package a compliant zip, and upload it to the site. Use when Codex needs to help OpenClaw users create, retrofit, package, validate, or publish an app/game for the platform.
---

# ClawApp Creator

Build the smallest working app package that can be uploaded to Nima Tech Space, then upload it if the user wants.

This skill can also search public apps on CLAWSPACE and download app packages from the site.

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

For a first-time uploader with no saved credentials, start by offering two clear paths:

- "我可以直接帮你注册 CLAWSPACE 账号并保存上传配置"
- "如果你想自己操作，也可以先去 https://www.nima-tech.space/register 注册"

Prefer asking this before you attempt upload-related commands.

## Workflow

1. On a brand-new machine or first-time setup, run `scripts/check_environment.py` first when the user is unsure whether the skill is ready to use.
2. Before upload, if the user is unsure which CLAWSPACE account is currently active, run `scripts/check_clawspace_account.py`.
3. Confirm the app can be shipped as a static front-end.
4. Build or fix the app until it outputs a static bundle.
5. Decide whether the app needs a model.
6. Generate a compliant `manifest.json`, optional `README.md`, and `assets/`.
7. If there is no project yet, scaffold one with `scripts/scaffold_mini_game.py`.
8. Preview locally with `scripts/preview_clawspace_app.py` when the user wants a browser check before package or upload.
9. Package everything into a zip with `scripts/build_nima_package.py`.
10. Diagnose with `scripts/diagnose_nima_package.py` before upload when helpful.
11. Upload with `scripts/upload_nima_package.py` when the user wants publishing.
12. Verify the detail page and launch page after upload.

For discovery and reuse:

13. Search public apps with `scripts/search_clawspace_apps.py`
14. Download public app zips with `scripts/download_clawspace_app.py`

## Game-Specific Guidance

Only apply this section when the user is building a game, mini-game, or playful interactive experience.
Do not force these rules onto utilities, visual experiments, AI tools, or other non-game apps.

When the project is clearly a game:

1. Infer the likely game shape before suggesting polish:
   - arcade / score chase
   - puzzle
   - story / dialogue
   - sim / management
   - action / adventure
2. Suggest only the lightweight completion features that fit that game type.
3. Treat these as recommendations, not hard requirements.

Useful game-specific suggestions:

- Arcade / score chase:
  - current score
  - best score
  - clear game-over summary
  - fast restart loop
- Puzzle:
  - moves
  - best score or best completion
  - clear solved state
  - reset / reshuffle
- Story / dialogue:
  - chapter or scene progress
  - clear ending state
  - replay entry point
- Sim / management:
  - visible resource change
  - round / stage goal
  - lightweight local progress if useful

When a game needs local persistence, prefer `app/lib/clawspace-game-storage.js` instead of ad-hoc localStorage keys.

For game polish, prefer checking for:

- a readable start state
- clear controls
- visible current-state feedback
- a clear end-state or result screen
- at least one satisfying feedback moment such as combo, streak, burst, or win feedback

Again, use these as genre-aware completion prompts. Do not flatten every game into the same structure.

## Package Rules

Read [references/platform-contract.md](./references/platform-contract.md) before packaging.

Always enforce these minimum rules:

- Ship only static front-end apps or mini-games.
- Put built files under `app/`.
- Keep the entry file inside `app/`, usually `app/index.html`.
- Keep package root flat: `manifest.json`, optional `README.md`, optional `assets/`, required `app/`.
- Strongly recommend adding a cover image and at least one screenshot, even though CLAWSPACE can render default covers when they are missing.
- The scaffold now generates default cover assets automatically, so creators start with a usable listing without having to prepare custom art first.
- The scaffold keeps starter packages lighter by generating `thumbnail.png` and `icon.png` without automatically duplicating them into `screenshots`.
- Game starters now also include `app/lib/clawspace-game-storage.js` for reusable local best-score / best-run persistence via browser storage.
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

For OCR, screenshot analysis, chart reading, or any app that sends images, use `modelCategory = multimodal` and send OpenAI-compatible `content` arrays with `text` and `image_url` parts.

## Packaging

Use `assets/manifest.example.json` as the starting template.

Use `assets/README.template.md` as the starting template when the app needs a basic product readme.

If the user wants to start from zero instead of retrofitting an existing app, copy one of these starter assets first:

- `assets/starter-mini-game/` for a no-model static game
- `assets/starter-ocr/` for a multimodal OCR and image-analysis app
- `assets/platform-llm-client.js` for a minimal platform model client

Or scaffold directly:

```bash
python3 scripts/scaffold_mini_game.py \
  --name "Orbit Tap" \
  --slug orbit-tap \
  --description "点击轨道行星的轻量小游戏。"
```

If `--out` is omitted, default to the OpenClaw workspace app directory:

```text
~/.openclaw/workspace/projects/apps/<slug>
```

Prefer this default for first-time users, so OpenClaw-generated apps live in a predictable place under its own workspace.

After scaffolding, encourage the user to add:
- a custom cover image if they want to replace the generated default
- a custom square icon if they want to replace the generated default
- at least one additional screenshot in `assets/`

If they skip custom cover assets, the site can still publish the app with a default generated cover, but custom art makes the listing look much better.
For mobile shells such as WeChat Mini Program, PNG/JPG/WebP cover art is recommended. If creators only provide SVG or skip custom art, the mobile experience can fall back to default PNG covers.

Use:

```bash
python3 scripts/preview_clawspace_app.py /path/to/project --open
```

This starts a lightweight local static server from the project root, reads `manifest.json`, and opens the packaged entry in the browser.

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

Environment check:

```bash
python3 scripts/check_environment.py
```

Use this first on a new machine, or when the user is not sure whether Python, browser preview, network access, or Keychain support are ready.

Production site:

- Website: `https://www.nima-tech.space`
- Base API URL: `https://www.nima-tech.space`

To confirm which saved CLAWSPACE account will be used for upload:

```bash
python3 scripts/check_clawspace_account.py
```

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
python3 scripts/register_clawspace_account.py
```

for a brand-new user who does not have a CLAWSPACE account yet.

Use:

```bash
python3 scripts/setup_upload_config.py
```

for an existing user who already has an account and only needs to save or refresh credentials.

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

The registration script can create a new website account and save the reusable upload config in one step. Prefer this when the user says they do not have a CLAWSPACE account yet.

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

If the package includes oversized PNG/JPG/WebP cover art, the uploader now warns before publish.
If there are obviously broken assets such as zero-byte screenshots, it will stop before upload.
On macOS, when a package has huge `thumbnail.png` or `icon.png` files, prefer:

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --model-category none \
  --optimize-images
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

For first-time users with no upload config, prefer this decision order:

1. offer to register the account directly with `scripts/register_clawspace_account.py`
2. if they do not want that, give them the website registration link: `https://www.nima-tech.space/register`
3. after they finish website registration, run `scripts/setup_upload_config.py`

If login fails, tell the user to rerun:

```bash
python3 scripts/setup_upload_config.py
```

and refresh the stored credentials.

## Searching And Downloading

Use these flows when the user wants to browse CLAWSPACE, find reference apps, or download a package to inspect locally.

Search:

```bash
python3 scripts/search_clawspace_apps.py "ocr"
```

Search with JSON:

```bash
python3 scripts/search_clawspace_apps.py "space game" --json
```

Download by slug:

```bash
python3 scripts/download_clawspace_app.py orbit-heist --out-dir /path/to/downloads
```

Download by detail URL:

```bash
python3 scripts/download_clawspace_app.py https://www.nima-tech.space/apps/orbit-heist
```

Use this for prompts such as:

- "帮我在 CLAWSPACE 找几个 OCR 应用"
- "下载 orbit-heist 到本地"
- "搜索一下 CLAWSPACE 里有哪些小游戏"

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
- If the app is OCR or image understanding and fails after upload, confirm the request uses a multimodal `messages[].content[]` shape instead of plain text only.
- If the app only needs deterministic gameplay or local logic, remove model usage and keep `modelCategory` as `none`.
- If the user has no project yet, scaffold from `assets/starter-mini-game/` instead of inventing files from scratch.
