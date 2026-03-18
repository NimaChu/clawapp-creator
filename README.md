# ClawApp Creator

ClawApp Creator 是一个给 OpenClaw / Codex 使用的技能工程，用来把静态前端应用或小游戏整理成兼容 Nima Tech Space 的标准应用包，并在条件满足时自动上传。

它适合两类场景：

- 从零生成一个可上传的小应用 / 小游戏
- 把现有静态前端项目改造成平台可接受的 zip 包

## What It Does

- 生成符合平台规范的 `manifest.json`
- 生成或补齐 `README.md`
- 校验应用包结构
- 检查资源路径风险
- 检查 slug 是否可用
- 支持 dry-run 预检查
- 支持直接上传或大包 Blob 上传
- 支持明文配置与 macOS Keychain 两种凭证保存方式

## Main Files

- `SKILL.md`: 技能主说明
- `scripts/scaffold_mini_game.py`: 生成小游戏骨架
- `scripts/build_nima_package.py`: 构建平台 zip 包
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

### 2. Build a package

```bash
python3 scripts/build_nima_package.py \
  --app-dir /path/to/app \
  --manifest /path/to/manifest.json \
  --out /path/to/output.zip \
  --readme /path/to/README.md \
  --assets-dir /path/to/assets
```

### 3. Configure upload credentials

```bash
python3 scripts/setup_upload_config.py
```

On macOS you can also choose Keychain storage instead of keeping the password in plaintext config.

### 4. Dry-run before upload

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --dry-run
```

### 5. Upload

```bash
python3 scripts/upload_nima_package.py \
  --package /path/to/output.zip \
  --model-category none
```

## Notes

- The target platform currently supports static front-end apps and mini-games.
- The final zip should stay within `25MB`.
- The same account can overwrite its own slug.
- Different accounts cannot overwrite each other's slug.

## Repository Role

This repository is the source of the `clawapp-creator` skill and can also be installed into Codex skills directories for direct use.
