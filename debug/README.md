# Debug Scripts

このフォルダには、開発・デバッグ用のスクリプトが含まれています。

## ファイル一覧

### コントローラースキャン関連
- `debug_controller_scan.py` - コントローラー検出の基本テスト
- `debug_controller_scan_flow.py` - 完全なスキャン信号フローのデバッグ
- `debug_rescan_behavior.py` - 再スキャン時の動作テスト
- `test_controller_persistence_fix.py` - コントローラー状態永続化のテスト
- `test_real_controller_scan.py` - 実際のコントローラーでのスキャンテスト

### GUI関連
- `debug_gui_flow.py` - GUI全体の処理フローデバッグ
- `debug_card_visibility.py` - コントローラーカードの表示問題デバッグ
- `debug_window_visibility.py` - ウィンドウ階層の表示問題デバッグ
- `debug_simple_scan.py` - シンプルなGUIスキャンテスト
- `test_gui_scanning.py` - GUIスキャン機能のテスト
- `test_gui_rescan_fix.py` - GUI再スキャン修正のテスト

### 永続化テスト
- `test_simple_persistence.py` - シンプルな永続化テスト

## 使用方法

各スクリプトは独立して実行できます：

```bash
# ルートディレクトリから
python debug/debug_controller_scan.py
python debug/test_gui_scanning.py
```

## 注意

これらのスクリプトは開発・デバッグ専用です。本番環境では使用しないでください。