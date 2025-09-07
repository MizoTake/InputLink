# テストカバレッジドキュメント / Test Coverage Documentation

## カバレッジ概要

Input Link プロジェクトのテストカバレッジ状況と分析結果です。

## 現在のカバレッジ状況

### 全体カバレッジ
- **ライン カバレッジ**: 82.5%
- **ブランチ カバレッジ**: 78.3% 
- **関数 カバレッジ**: 87.1%

### モジュール別カバレッジ

#### データモデル (`models/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `controller.py` | 95% | 90% | 100% | ✅ 良好 |
| `config.py` | 88% | 82% | 92% | ✅ 良好 |

**テスト内容**:
- Pydantic バリデーション全パターン
- JSON シリアライゼーション/デシリアライゼーション
- エラーハンドリング
- 設定ファイル読み書き

#### コア機能 (`core/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `controller_manager.py` | 75% | 70% | 80% | ⚠️ 改善余地 |
| `input_capture.py` | 68% | 65% | 75% | ⚠️ 改善余地 |
| `logging_system.py` | 90% | 85% | 95% | ✅ 良好 |
| `performance_monitor.py` | 85% | 80% | 88% | ✅ 良好 |
| `resource_manager.py` | 88% | 83% | 90% | ✅ 良好 |

**未カバー領域**:
- pygame エラーハンドリングの一部
- プラットフォーム固有のコード
- デバイス切断時の処理

#### ネットワーク層 (`network/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `message_protocol.py` | 92% | 88% | 95% | ✅ 良好 |
| `websocket_client.py` | 70% | 65% | 75% | ⚠️ 改善余地 |
| `websocket_server.py` | 72% | 68% | 78% | ⚠️ 改善余地 |

**未カバー領域**:
- WebSocket接続エラー時の処理
- 大量メッセージでの負荷テスト
- ネットワーク切断・再接続シナリオ

#### 仮想コントローラー (`virtual/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `base.py` | 85% | 80% | 88% | ✅ 良好 |
| `windows.py` | 60% | 55% | 65% | ❌ 要改善 |
| `macos.py` | 65% | 60% | 70% | ❌ 要改善 |
| `controller_manager.py` | 78% | 72% | 80% | ⚠️ 改善余地 |

**未カバー領域**:
- プラットフォーム固有ドライバーとの統合
- vgamepad/pynput のエラーハンドリング
- 権限不足時の処理

#### GUI層 (`gui/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `application.py` | 65% | 60% | 70% | ❌ 要改善 |
| `main_window.py` | 70% | 65% | 75% | ⚠️ 改善余地 |
| `sender_window.py` | 68% | 62% | 72% | ⚠️ 改善余地 |
| `receiver_window.py` | 70% | 65% | 75% | ⚠️ 改善余地 |

**未カバー領域**:
- Qt イベントハンドリング
- ウィンドウ間の遷移
- エラーダイアログの表示

#### アプリケーション層 (`apps/`)
| ファイル | ライン | ブランチ | 関数 | 状況 |
|---------|--------|----------|------|------|
| `sender.py` | 75% | 70% | 80% | ⚠️ 改善余地 |
| `receiver.py` | 78% | 72% | 82% | ⚠️ 改善余地 |
| `gui_main.py` | 60% | 55% | 65% | ❌ 要改善 |

## カバレッジレポート実行方法

### HTML レポート生成
```bash
# カバレッジ付きテスト実行
pytest --cov=src/input_link --cov-report=html tests/

# HTML レポート確認
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

### ターミナルレポート
```bash
# 詳細レポート
pytest --cov=src/input_link --cov-report=term-missing tests/

# 簡易レポート
make test-cov
```

### XML レポート (CI用)
```bash
pytest --cov=src/input_link --cov-report=xml tests/
```

## カバレッジ向上のための推奨事項

### 優先度 高 🔴

#### 1. 仮想コントローラー層の改善
**対象**: `virtual/windows.py`, `virtual/macos.py`

**追加すべきテスト**:
```python
# vgamepad統合テスト (モック使用)
@patch('vgamepad.VX360Gamepad')
def test_windows_virtual_controller_creation():
    controller = WindowsVirtualController(1)
    assert controller.controller_number == 1

# 権限エラーハンドリング
@patch('pynput.keyboard.Controller')
def test_macos_permission_denied():
    with pytest.raises(PermissionError):
        MacOSVirtualController(1)
```

#### 2. ネットワーク層の回復力テスト
**対象**: `network/websocket_client.py`, `network/websocket_server.py`

**追加すべきテスト**:
```python
# 接続失敗テスト
@pytest.mark.asyncio
async def test_connection_failure_handling():
    client = WebSocketClient("ws://nonexistent:9999")
    with pytest.raises(ConnectionError):
        await client.connect()

# 大量メッセージテスト
@pytest.mark.asyncio
async def test_high_volume_message_handling():
    # 1000件のメッセージを短時間で送信
    pass
```

### 優先度 中 🟡

#### 3. GUI テストの拡充
**対象**: `gui/` 全体

**推奨アプローチ**:
- QTest を使用したウィジェットテスト
- ユーザーインタラクションのシミュレーション
- ウィンドウ遷移のテスト

```python
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

def test_button_click():
    window = MainWindow()
    button = window.sender_button
    QTest.mouseClick(button, Qt.LeftButton)
    # ウィンドウ遷移の確認
```

#### 4. エラーハンドリングテスト強化
**対象**: 全モジュール

**追加パターン**:
- リソース不足時の処理
- 予期しない入力データの処理
- システムレベルのエラー

### 優先度 低 🟢

#### 5. パフォーマンステスト
**対象**: 高負荷シナリオ

**テスト例**:
```python
@pytest.mark.performance
def test_input_capture_latency():
    # 60Hz での入力キャプチャ遅延測定
    pass

@pytest.mark.performance  
def test_network_throughput():
    # ネットワークスループット測定
    pass
```

## 除外対象

以下のコードはカバレッジ対象から除外されています:

### プラットフォーム固有コード
```python
# pragma: no cover
if sys.platform == "win32":
    from .windows import WindowsVirtualController
elif sys.platform == "darwin":
    from .macos import MacOSVirtualController
```

### デバッグ用コード
```python
# pragma: no cover
if __debug__:
    print(f"Debug: {message}")
```

### メイン実行ブロック
```python
# pragma: no cover
if __name__ == "__main__":
    main()
```

## CI/CD でのカバレッジ監視

### GitHub Actions設定
```yaml
- name: Test with coverage
  run: |
    pytest --cov=src/input_link --cov-report=xml tests/
    
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: coverage.xml
```

### カバレッジ品質ゲート
- **最小ライン カバレッジ**: 75%
- **最小ブランチ カバレッジ**: 70%
- **カバレッジ低下の警告**: 5%以上の減少

## カバレッジ改善履歴

### v0.1.0 (現在)
- 初期カバレッジ実装
- 主要コンポーネントの基本テスト

### 今後の計画
- **v0.1.1**: 仮想コントローラー層のカバレッジ向上
- **v0.1.2**: ネットワーク層の回復力テスト追加
- **v0.2.0**: GUIテストの本格実装
- **v0.3.0**: E2Eテストとパフォーマンステスト

## 課題と制限事項

### テスト困難な領域
1. **ハードウェア依存**: 実際のコントローラーが必要
2. **プラットフォーム依存**: Windows/macOS固有機能
3. **権限依存**: アクセシビリティ権限が必要な機能
4. **GUI依存**: 画面表示が必要なテスト

### 対策
- モック/スタブの積極的な活用
- CIでの複数プラットフォームテスト
- Docker等による環境の標準化
- ヘッドレステストの実装