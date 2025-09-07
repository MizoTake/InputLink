# システム概要 / System Overview

## アーキテクチャ概要

Input Link は、送信側PCのゲームコントローラー入力を受信側PCに転送し、仮想コントローラーとして再現するシステムです。

```
┌─────────────────────────────────┐     WebSocket      ┌─────────────────────────────────┐
│          Sender PC              │ ◄──────────────────► │          Receiver PC            │
│                                 │                     │                                 │
│  ┌─────────────────────────┐   │                     │  ┌─────────────────────────┐   │
│  │    Controller           │   │                     │  │    Virtual Controller   │   │
│  │    Detection            │   │                     │  │    Management          │   │
│  │   (pygame)              │   │                     │  │  (vgamepad/keyboard)    │   │
│  └─────────────────────────┘   │                     │  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │                     │  ┌─────────────────────────┐   │
│  │    Input Capture        │   │                     │  │    Input Simulation     │   │
│  │   (60Hz polling)        │   │                     │  │   (Real-time)           │   │
│  └─────────────────────────┘   │                     │  └─────────────────────────┘   │
│  ┌─────────────────────────┐   │                     │  ┌─────────────────────────┐   │
│  │    WebSocket Client     │   │                     │  │    WebSocket Server     │   │
│  │  (Auto-reconnection)    │   │                     │  │  (Multi-client)         │   │
│  └─────────────────────────┘   │                     │  └─────────────────────────┘   │
└─────────────────────────────────┘                     └─────────────────────────────────┘
```

## 主要コンポーネント

### 1. データモデル層 (`models/`)

#### ControllerInputData
- Pydantic v2による厳密な入力データ検証
- タイムスタンプ付きコントローラー状態
- JSON シリアライゼーション対応

```python
class ControllerInputData(BaseModel):
    controller_number: int = Field(..., ge=1)
    controller_id: str = Field(..., min_length=1)
    input_method: InputMethod = Field(default=InputMethod.XINPUT)
    buttons: ButtonState = Field(default_factory=ButtonState)
    axes: ControllerState = Field(default_factory=ControllerState)
    timestamp: Optional[float] = None
```

#### ConfigModel
- クロスプラットフォーム設定管理
- JSON設定ファイルの検証と読み込み
- CLI パラメータとの統合

### 2. コントローラー管理層 (`core/`)

#### ControllerManager
- pygame を使用したクロスプラットフォームコントローラー検出
- Xbox/PlayStation コントローラーの自動識別
- デバイス接続状態の追跡

#### InputCaptureEngine
- 60Hz リアルタイム入力ポーリング
- デッドゾーン処理と軸正規化
- 非同期入力キャプチャ

### 3. ネットワーク層 (`network/`)

#### WebSocketClient (送信側)
- 自動再接続機能付きWebSocketクライアント
- 指数バックオフによる接続リトライ
- メッセージキューイング

#### WebSocketServer (受信側)
- マルチクライアント対応WebSocketサーバー
- 非同期メッセージ処理
- クライアント状態管理

#### NetworkMessage
- タイプ化されたメッセージプロトコル
- JSON シリアライゼーション
- メッセージID による追跡

### 4. 仮想コントローラー層 (`virtual/`)

#### プラットフォーム固有実装

**Windows (`windows.py`)**
- ViGEm Bus Driver 統合
- vgamepad による Xbox 360 エミュレーション
- DirectInput/XInput サポート

**macOS (`macos.py`)**
- キーボードシミュレーション（pynput）
- WASD + スペースキーマッピング
- アクセシビリティ権限が必要

#### VirtualControllerManager
- 複数仮想コントローラーのライフサイクル管理
- プラットフォーム固有ファクトリーパターン
- 動的コントローラー作成・削除

### 5. アプリケーション層 (`apps/` & `gui/`)

#### CLI アプリケーション
- `SenderApp`: 非同期コントローラー入力送信
- `ReceiverApp`: 非同期入力受信と仮想化
- Click フレームワークによるコマンドライン統合

#### GUI アプリケーション
- PySide6 (Qt) ベース
- Apple Human Interface Guidelines 準拠
- マルチウィンドウ対応

## データフロー

### 送信側フロー
```
Physical Controller → pygame → InputCaptureEngine → ControllerInputData → 
NetworkMessage → WebSocketClient → Network
```

### 受信側フロー
```
Network → WebSocketServer → NetworkMessage → ControllerInputData → 
VirtualControllerManager → Platform-specific Virtual Controller
```

## 技術スタック

### コア技術
- **Python 3.8+**: クロスプラットフォーム互換性
- **asyncio**: 全体を通じた非同期アーキテクチャ
- **Pydantic v2**: データ検証とシリアライゼーション
- **pygame**: コントローラー入力キャプチャ
- **websockets**: WebSocket通信

### プラットフォーム統合
- **vgamepad** (Windows): ViGEm仮想コントローラー
- **pynput** (macOS): キーボードシミュレーション
- **PySide6**: クロスプラットフォームGUI

### 開発ツール
- **pytest**: 非同期テストサポート付きテストフレームワーク
- **black/isort/ruff**: コード品質管理
- **mypy**: 静的型チェック
- **PyInstaller**: 実行ファイル作成

## 設計原則

### 非同期設計
すべてのI/O操作は asyncio を使用してノンブロッキング実行

### 依存性注入
コンポーネントはテスタビリティのためコールバック/依存関係を受け入れ

### ファクトリーパターン
プラットフォーム固有の仮想コントローラー作成

### オブザーバーパターン
コールバックとQt シグナルによるステータス更新

### モデル・ビュー分離
コアロジックをGUIプレゼンテーション層から分離