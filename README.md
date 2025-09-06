# Input Link

ローカルネットワーク上で、送信側PCのゲームコントローラー入力を受信側PCへWebSocket経由で転送するシステムです。

## 特長

- クロスプラットフォーム対応（Windows / macOS）
- 低遅延なリアルタイム入力転送
- DInput / XInput コントローラーに対応
- 受信側での仮想コントローラー（Windows: ViGEm / vgamepad）
- 自動再接続を含む堅牢なWebSocket通信
- 最大8台までの複数コントローラーに対応
- JSON設定とCLIオプションで柔軟に構成

## クイックスタート

### 事前ビルド済み実行ファイルの利用

**Windows:**
1. [Releases](../../releases) から `InputLink-Windows-Installer.exe` をダウンロード
2. インストーラーを実行（ViGEmドライバーのセットアップを含みます）
3. スタートメニューから「Input Link Sender」「Input Link Receiver」を起動

**macOS:**
1. [Releases](../../releases) から `InputLink-macOS.dmg` をダウンロード
2. DMGをマウントし、アプリをApplicationsへドラッグ
3. Applications / Launchpad から起動

### コマンドラインでの利用

【送信側（コントローラー入力の取得）】
```bash
# 既定の接続先に接続
input-link-sender

# 接続先を指定
input-link-sender --host 192.168.1.100 --port 8765

# 詳細ログ
input-link-sender --verbose
```

【受信側（コントローラー入力の仮想化）】
```bash
# 既定ポートで起動
input-link-receiver

# ポートや最大コントローラー数を変更
input-link-receiver --port 9000 --max-controllers 8

# 詳細ログ
input-link-receiver --verbose
```

このリポジトリ内のローカルCLIから直接起動することもできます（インストール不要）。

```bash
# リポジトリルートから
python main.py sender --host 127.0.0.1 --port 8765
python main.py receiver --port 8765 --max-controllers 4

# Makeターゲットの利用
make run-sender
make run-receiver
make run-gui
```

## ソースからビルド

### 前提条件

- Python 3.8+
- Git

### 開発セットアップ

```bash
# リポジトリ取得
git clone https://github.com/inputlink/inputlink.git
cd inputlink

# 開発用依存関係をインストール
make install-dev

# テストを実行
make test

# フォーマットとLint
make format lint
```

### 実行ファイルのビルド

```bash
# 現在のプラットフォーム向けにビルド
make build

# 生成物のクリーン
make clean
```

プラットフォーム別ビルド:
- Windows: `build\build.bat` または `make build-windows`
- macOS: `./build/build.sh` または `make build-macos`

詳細は [BUILD.md](BUILD.md) を参照してください。

## アーキテクチャ

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Sender PC     │ ◄──────────────► │   Receiver PC   │
│                 │                  │                 │
│ ┌─────────────┐ │                  │ ┌─────────────┐ │
│ │ Controller  │ │                  │ │ Virtual     │ │
│ │ Manager     │ │                  │ │ Controller  │ │
│ └─────────────┘ │                  │ │ Manager     │ │
│ ┌─────────────┐ │                  │ └─────────────┘ │
│ │ Input       │ │                  │ ┌─────────────┐ │
│ │ Capture     │ │                  │ │ Input       │ │
│ └─────────────┘ │                  │ │ Simulation  │ │
│ ┌─────────────┐ │                  │ └─────────────┘ │
│ │ WebSocket   │ │                  │ ┌─────────────┐ │
│ │ Client      │ │                  │ │ WebSocket   │ │
│ └─────────────┘ │                  │ │ Server      │ │
└─────────────────┘                  │ └─────────────┘ │
                                     └─────────────────┘
```

主なコンポーネント:
- Sender: pygameで入力取得しWebSocketで送信
- Receiver: 入力を受信し仮想コントローラーへ反映
- Models: Pydanticで検証されたデータモデル
- Network: 非同期WebSocket通信と再接続処理

## 対応プラットフォーム

### Windows
- 仮想コントローラー: ViGEm Bus Driver（Xbox 360エミュレーション）
- 入力方式: DirectInput / XInput
- 要件: Windows 10/11、ViGEmドライバー（インストーラーで導入）

### macOS
- 仮想コントローラー: キーボードシミュレーション（WASD等）
- 入力方式: pygame経由の汎用HID
- 要件: macOS 10.12+、アクセシビリティ権限

## 設定

設定ファイルは `~/.input-link/config.json` に保存されます。

```json
{
  "sender_config": {
    "receiver_host": "127.0.0.1",
    "receiver_port": 8765,
    "polling_rate": 60,
    "retry_interval": 1.0,
    "max_retry_attempts": 10
  },
  "receiver_config": {
    "listen_port": 8765,
    "max_controllers": 4,
    "auto_create_virtual": true,
    "connection_timeout": 30.0
  }
}
```

## テスト

```bash
# すべてのテスト
make test

# カバレッジ付き
make test-cov

# 種別ごとの実行
pytest -m unit        # 単体テスト
pytest -m integration # 結合テスト
pytest -m e2e         # E2Eテスト
```

### 手動動作確認（Gamepad）

受信側PC（Windows / XInput / ViGEm）で仮想コントローラーの反映を簡単に確認するには、以下のサイトをブラウザで開いてください。

- https://hardwaretester.com/gamepad

手順（Windows）:
- 受信側を起動（vgamepad/ViGEmで仮想コントローラーが作成されます）
- 送信側を起動して受信側へ接続
- 上記リンクを受信側PCの Chromium / Edge / Firefox で開く
- 仮想の「Xbox 360 Controller」が検出され、ボタンやスティック操作が反映されます

補足:
- macOS実装はキーボードマッピングによるシミュレーションのため、ブラウザのゲームパッドテスターでは検出されません。ログや想定キーイベントで確認してください。

## コントリビュート

1. コードスタイル: `black` / `isort` / `ruff`
2. テスト: 新規機能にはpytestでテストを追加
3. 型ヒント: 可能な限り型注釈を追加
4. ドキュメント: 変更点に合わせて更新
5. コミット: Conventional Commits を推奨

### 開発用コマンド

```bash
make help              # 利用可能なコマンド一覧
make install-dev       # 開発依存のインストール
make test              # テスト実行
make lint              # Lint実行
make format            # フォーマット適用
make build             # 実行ファイルのビルド
make clean             # 生成物のクリーン
```
