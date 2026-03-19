# ClawApp Creator

ClawApp Creator 是一个给 OpenClaw / Codex 使用的技能工程，用来把静态前端应用或小游戏整理成兼容 CLAWSPACE 的标准应用包，并在条件满足时自动上传到正式网站。

它适合两类场景：

- 从零生成一个可上传的小应用 / 小游戏
- 把现有静态前端项目改造成平台可接受的 zip 包

正式平台：

- Website: [https://www.nima-tech.space](https://www.nima-tech.space)
- Skill on ClawHub: [https://clawhub.ai/NimaChu/clawapp-creator](https://clawhub.ai/NimaChu/clawapp-creator)

## What It Does

- 生成符合平台规范的 `manifest.json`
- 生成或补齐 `README.md`
- 校验应用包结构
- 检查资源路径风险
- 检查 slug 是否可用
- 搜索 CLAWSPACE 上的公开应用
- 从 CLAWSPACE 下载公开应用 zip
- 支持 dry-run 预检查
- 支持直接上传或大包 Blob 上传
- 支持明文配置与 macOS Keychain 两种凭证保存方式
- 支持 `none / text / multimodal / code` 四类模型接入判断
- 支持 OCR / 图像分析类 starter
- 上传完成后给出详情页、体验页、下载页和可复制分享文案

## Main Files

- `SKILL.md`: 技能主说明
- `scripts/scaffold_mini_game.py`: 生成小游戏骨架
- `scripts/build_nima_package.py`: 构建平台 zip 包
- `scripts/register_clawspace_account.py`: 注册新账号并保存上传配置
- `scripts/setup_upload_config.py`: 初始化上传配置
- `scripts/upload_nima_package.py`: 校验并上传应用包
- `references/platform-contract.md`: 平台打包规范
- `references/model-api.md`: 平台模型接口说明

## Quick Start

### 1. Scaffold a new mini game

```bash
python3 scripts/scaffold_mini_game.py \
  --out /path/to/new-project \
  --name "Orbit Tap" \
  --description "点击轨道行星的轻量小游戏。"
```

### 1b. Scaffold an OCR / multimodal app

```bash
python3 scripts/scaffold_mini_game.py \
  --template ocr-tool \
  --out /path/to/ocr-tool \
  --name "在线 OCR 工具" \
  --description "上传图片并识别文字、表格或图像内容。"
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

### 3. Register a new CLAWSPACE account (optional but helpful for first-time users)

```bash
python3 scripts/register_clawspace_account.py
```

This can create the account and save reusable upload credentials in one step.

### 4. Configure upload credentials for an existing account

```bash
python3 scripts/setup_upload_config.py
```

On macOS you can also choose Keychain storage instead of keeping the password in plaintext config.

The default production site is:

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

- `帮我做一个可上传到 CLAWSPACE 的小游戏`
- `把这个项目变成 CLAWSPACE 可发布应用`
- `帮我直接发布这个应用`

In publish mode, the skill should diagnose, package, verify slug ownership, upload, and return final links.

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
- Public search and download use the production website at `https://www.nima-tech.space`.
- If ClawHub is rate limited, users can still install the skill from GitHub.

## Repository Role

This repository is the source of the `clawapp-creator` skill and can also be installed into Codex skills directories for direct use.
