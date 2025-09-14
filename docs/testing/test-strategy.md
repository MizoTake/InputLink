# テスト戦略 / Test Strategy

## テスト概要

Input Link のテスト戦略は、システム品質保証と継続的な信頼性向上を目的としています。

## テストカテゴリ

### 1. 単体テスト (Unit Tests) 📝

**対象**: 個別のコンポーネントとクラス
**場所**: `tests/unit/`
**実行**: `pytest -m unit`

#### テスト対象コンポーネント

##### データモデル (`test_models.py`)
- **ButtonState**: ボタン状態の検証
- **ControllerState**: 軸データの範囲検証とクランプ処理
- **ControllerInputData**: 入力データの検証とシリアライゼーション
- **ConfigModel**: 設定ファイルの読み書きと検証
- **SenderConfig/ReceiverConfig**: 設定の妥当性チェック

```python
# テスト例: 軸データの範囲検証
def test_stick_value_validation(self):
    # 有効値テスト
    state = ControllerState(left_stick_x=0.5, left_stick_y=-0.8)
    assert state.left_stick_x == 0.5
    
    # 無効値テスト (範囲外)
    with pytest.raises(ValueError):
        ControllerState(left_stick_x=2.0)
```

##### コントローラー管理 (`test_controller_manager.py`)
- **DetectedController**: コントローラー識別とタイプ検出
- **ControllerManager**: pygame統合とデバイス管理
- **番号割り当て**: コントローラー番号の自動/手動割り当て
- **接続状態管理**: 接続/切断の追跡

```python
# テスト例: Xbox/PlayStation コントローラー検出
def test_xbox_controller_detection(self):
    xbox_names = ["Xbox 360 Controller", "Xbox One Controller"]
    for name in xbox_names:
        controller = DetectedController(name=name, ...)
        assert controller.is_xbox_controller()
        assert controller.get_recommended_input_method() == InputMethod.XINPUT
```

##### ネットワーク通信 (`test_network.py`)
- **NetworkMessage**: メッセージプロトコルと JSON シリアライゼーション
- **WebSocketClient**: クライアント接続と再接続ロジック
- **WebSocketServer**: サーバー機能とクライアント管理
- **Message Factory**: 各種メッセージタイプの作成

##### 仮想コントローラー (`test_virtual.py`)
- **VirtualController**: プラットフォーム固有実装
- **VirtualControllerFactory**: ファクトリーパターン
- **VirtualControllerManager**: ライフサイクル管理

##### システムコンポーネント
- **ResourceManager** (`test_resource_manager.py`): リソース管理
- **PerformanceMonitor** (`test_performance_monitor.py`): パフォーマンス監視

### 2. 結合テスト (Integration Tests) 🔗

**対象**: コンポーネント間の連携
**場所**: `tests/integration/`
**実行**: `pytest -m integration`

#### GUI統合テスト
- **test_gui.py**: GUI基本動作
- **test_gui_interactions.py**: ユーザーインタラクション
- **test_gui_functions.py**: GUI機能
- **test_sender_window.py**: 送信ウィンドウ
- **test_receiver_window.py**: 受信ウィンドウ
- **test_back_to_main.py**: ウィンドウ遷移
- **test_dynamic_controllers.py**: 動的コントローラー管理

#### UI詳細テスト
- **test_ui_button_processing.py**: ボタン処理
- **test_ui_layout_analysis.py**: レイアウト解析
- **test_receiver_scroll_functionality.py**: スクロール機能

#### システム統合テスト
- **test_app_lifecycle.py**: アプリケーションライフサイクル
- **test_network_resilience.py**: ネットワーク回復力

### 3. エンドツーエンドテスト (E2E Tests) 🌐

**対象**: 完全なワークフロー
**場所**: `tests/e2e/` (今後追加予定)
**実行**: `pytest -m e2e`

#### 予定されるE2Eテスト
- 送信側→受信側の完全なデータフロー
- 複数コントローラーの同時動作
- ネットワーク切断・再接続シナリオ
- プラットフォーム固有機能のテスト

## テスト実行方法

### 基本的なテスト実行

```bash
# 全テスト実行
make test

# カテゴリ別実行
pytest -m unit          # 単体テスト
pytest -m integration   # 結合テスト
pytest -m e2e           # E2Eテスト

# 詳細出力
pytest -v

# 特定ファイルのテスト
pytest tests/unit/test_models.py

# 特定テストメソッド
pytest tests/unit/test_models.py::TestButtonState::test_default_all_false
```

### カバレッジ測定

```bash
# カバレッジ付きテスト
make test-cov

# HTMLレポート生成
pytest --cov=src/input_link --cov-report=html

# ターミナルレポート
pytest --cov=src/input_link --cov-report=term
```

### 継続的インテグレーション

```bash
# CI用コマンド (lint + test)
make check

# 全品質チェック (format + lint + test + build)
make all
```

## テストツールとライブラリ

### テストフレームワーク
- **pytest**: メインテストフレームワーク
- **pytest-asyncio**: 非同期テスト支援
- **pytest-mock**: モックとパッチ
- **pytest-cov**: カバレッジ測定

### モッキング
```python
from unittest.mock import Mock, patch

@patch("pygame.joystick.get_count", return_value=2)
def test_controller_scanning(self, mock_get_count):
    # pygame をモックしてテスト
    pass
```

### 非同期テスト
```python
@pytest.mark.asyncio
async def test_websocket_connection():
    async with websockets.connect("ws://localhost:8765") as websocket:
        # 非同期WebSocket通信のテスト
        pass
```

## テストデータ管理

### フィクスチャファイル
- `tests/fixtures/`: テスト用データファイル
- 設定ファイル、コントローラープロファイルなど

### テンポラリファイル
```python
import tempfile
from pathlib import Path

def test_config_file_operations():
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test_config.json"
        # テンポラリファイルでのテスト
```

## 品質メトリクス

### 目標カバレッジ
- **コードカバレッジ**: 85% 以上
- **ブランチカバレッジ**: 80% 以上
- **関数カバレッジ**: 90% 以上

### 品質ゲート
- すべての単体テストが通過
- 結合テストが通過
- Lint チェック (ruff) が通過
- 型チェック (mypy) が通過

## テスト環境

### 開発環境
- Python 3.8+ 対応
- Windows / macOS クロスプラットフォーム
- 仮想環境での隔離実行

### CI/CD環境
- GitHub Actions でのマトリックステスト
- 複数Python版での実行
- プラットフォーム別テスト

## テスト作成ガイドライン

### 命名規則
- テストファイル: `test_*.py`
- テストクラス: `TestClassName`
- テストメソッド: `test_specific_behavior`

### テスト構造
```python
class TestComponentName:
    """Test component description."""
    
    def setup_method(self):
        """Set up test fixtures."""
        pass
    
    def teardown_method(self):
        """Clean up after test."""
        pass
    
    def test_specific_behavior(self):
        """Should do something specific."""
        # Arrange
        # Act  
        # Assert
        pass
```

### アサーション
- 明確で読みやすいアサーション
- エラーメッセージの適切な設定
- エッジケースの網羅

### モック使用
- 外部依存性のモック (pygame, websockets)
- 適切な境界でのモック
- リアルな動作の模倣

## トラブルシューティング

### よくあるテスト問題

**pygame 関連テスト**
```bash
# X11/Display エラー (Linux)
export SDL_VIDEODRIVER=dummy
pytest tests/unit/test_controller_manager.py
```

**非同期テスト**
```python
# 非同期テストのタイムアウト
@pytest.mark.asyncio
@pytest.mark.timeout(5)  # 5秒タイムアウト
async def test_async_operation():
    pass
```

**リソースリーク**
- teardown_method での適切なクリーンアップ
- ファイルハンドルの確実なクローズ
- pygame のquit処理

### デバッグ
```bash
# テスト失敗時の詳細出力
pytest -vv --tb=long

# 特定テストのデバッグ
pytest --pdb tests/unit/test_models.py::TestButtonState::test_default_all_false
```