# Scripts

このフォルダには、開発支援やユーティリティ用のスクリプトが含まれています。

## ファイル一覧

### ユーティリティ
- `trigger_gui_scan.py` - 実行中のGUIアプリケーションに対してスキャンを実行するトリガー
- `_scratch_ws_check.py` - WebSocket接続のテスト用スクリプト

## 使用方法

各スクリプトは独立して実行できます：

```bash
# ルートディレクトリから
python scripts/trigger_gui_scan.py
python scripts/_scratch_ws_check.py
```

## 用途

これらのスクリプトは主に：
- 開発時の動作テスト
- 自動化されたテスト実行
- デバッグ補助

などの目的で使用されます。