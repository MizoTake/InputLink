# テストシナリオ / Test Scenarios

## テストシナリオ概要

Input Link の機能別テストシナリオを定義し、実装の品質と信頼性を確保します。

## 機能別テストシナリオ

### 1. データモデルテスト (`models/`)

#### 1.1 ControllerInputData 検証シナリオ

**シナリオ**: コントローラー入力データの作成と検証
```python
def test_controller_input_data_validation():
    # 正常ケース
    data = ControllerInputData(
        controller_number=1,
        controller_id="xbox_360_controller"
    )
    assert data.controller_number == 1
    
    # 異常ケース: 無効なコントローラー番号
    with pytest.raises(ValueError):
        ControllerInputData(controller_number=0, controller_id="test")
    
    # 異常ケース: 空のコントローラーID
    with pytest.raises(ValueError):
        ControllerInputData(controller_number=1, controller_id="")
```

**期待結果**:
- 有効データは正常に作成される
- 無効データはValidationErrorを発生させる
- Timestampが自動設定される

#### 1.2 設定ファイル操作シナリオ

**シナリオ**: JSON設定ファイルの読み書き
```python
def test_config_file_operations():
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "test_config.json"
        
        # デフォルト設定作成
        original = ConfigModel.create_default()
        original.debug_logging = True
        original.save_to_file(config_path)
        
        # 設定ファイル読み込み
        loaded = ConfigModel.load_from_file(config_path)
        assert loaded.debug_logging == True
```

### 2. コントローラー管理テスト (`core/`)

#### 2.1 コントローラー検出シナリオ

**シナリオ**: pygame経由でのコントローラー検出
```python
@patch("pygame.joystick.get_count", return_value=2)
@patch("pygame.joystick.Joystick") 
def test_controller_detection():
    # Mock設定
    mock_joystick.get_name.return_value = "Xbox 360 Controller"
    mock_joystick.get_guid.return_value = "abc123"
    
    manager = ControllerManager()
    controllers = manager.scan_controllers()
    
    assert len(controllers) == 2
    assert controllers[0].is_xbox_controller()
```

**期待結果**:
- 接続されたコントローラーを正しく検出
- Xbox/PlayStation コントローラーを適切に識別
- 推奨入力メソッドを正しく設定

#### 2.2 コントローラー番号割り当てシナリオ

**シナリオ**: コントローラー番号の手動/自動割り当て
```python
def test_controller_number_assignment():
    manager = ControllerManager()
    controller = create_mock_controller("test_controller")
    manager._controllers[0] = controller
    
    # 手動割り当て
    success = manager.assign_controller_number("test_controller_1", 3)
    assert success
    assert controller.assigned_number == 3
    
    # 重複割り当て (既存を上書き)
    success = manager.assign_controller_number("test_controller_2", 3)
    assert success
```

### 3. ネットワーク通信テスト (`network/`)

#### 3.1 WebSocket基本通信シナリオ

**シナリオ**: クライアント-サーバー間の基本通信
```python
@pytest.mark.asyncio
async def test_websocket_basic_communication():
    server = WebSocketServer("127.0.0.1", 0)
    await server.start()
    
    client = WebSocketClient("127.0.0.1", server.port)
    await client.start()
    
    # メッセージ送信
    test_data = ControllerInputData(
        controller_number=1,
        controller_id="test_controller"
    )
    await client.send_controller_input(test_data)
    
    # メッセージ受信確認
    await asyncio.sleep(0.1)
    # アサーション処理
```

#### 3.2 接続エラー処理シナリオ

**シナリオ**: ネットワーク接続エラーの処理
```python
@pytest.mark.asyncio
async def test_connection_error_handling():
    client = WebSocketClient("127.0.0.1", 9999)  # 存在しないポート
    
    connection_attempts = []
    async def mock_connect(*args):
        connection_attempts.append(args)
        raise ConnectionRefusedError("Connection refused")
    
    with patch('websockets.connect', side_effect=mock_connect):
        await client.start()
        await asyncio.sleep(0.1)
        await client.stop()
    
    assert len(connection_attempts) >= 1
```

#### 3.3 メッセージ整合性シナリオ

**シナリオ**: 送信データの整合性確認
```python
@pytest.mark.asyncio
async def test_message_integrity():
    # 詳細なコントローラーデータ作成
    original_data = ControllerInputData(
        controller_number=3,
        controller_id="xbox_controller_001",
        buttons=ButtonState(a=True, x=True, dpad_up=True),
        axes=ControllerState(left_stick_x=0.75, left_trigger=0.9)
    )
    
    # JSON変換と復元
    message = MessageProtocol.create_controller_input_message(original_data)
    json_data = message.to_json()
    parsed_message = MessageProtocol.parse_message(json_data)
    
    # データ整合性確認
    reconstructed = parsed_message.get_controller_data()
    assert reconstructed.controller_number == original_data.controller_number
    assert abs(reconstructed.axes.left_stick_x - 0.75) < 0.001
```

### 4. 仮想コントローラーテスト (`virtual/`)

#### 4.1 Windows仮想コントローラーシナリオ

**シナリオ**: vgamepad統合テスト
```python
@patch('vgamepad.VX360Gamepad')
def test_windows_virtual_controller(mock_gamepad):
    controller = WindowsVirtualController(1)
    
    # 入力データ適用
    input_data = ControllerInputData(
        controller_number=1,
        controller_id="test",
        buttons=ButtonState(a=True),
        axes=ControllerState(left_stick_x=0.5)
    )
    
    controller.apply_input(input_data)
    
    # vgamepad への適切な呼び出し確認
    mock_gamepad.return_value.press_button.assert_called()
    mock_gamepad.return_value.left_joystick_float.assert_called_with(x_value_float=0.5, y_value_float=0.0)
```

#### 4.2 macOS仮想コントローラーシナリオ

**シナリオ**: キーボードシミュレーション
```python
@patch('pynput.keyboard.Controller')
def test_macos_virtual_controller(mock_keyboard):
    controller = MacOSVirtualController(1)
    
    # ボタン入力
    input_data = ControllerInputData(
        controller_number=1,
        controller_id="test",
        buttons=ButtonState(a=True)  # スペースキーにマップ
    )
    
    controller.apply_input(input_data)
    
    # キーボード入力確認
    mock_keyboard.return_value.press.assert_called()
```

### 5. GUI機能テスト (`gui/`)

#### 5.1 基本ウィンドウ表示シナリオ

**シナリオ**: メインウィンドウの表示と基本操作
```python
def test_main_window_display(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
    window.show()
    assert window.isVisible()
    
    # ボタンクリックテスト
    sender_button = window.find_child(QPushButton, "sender_button")
    qtbot.mouseClick(sender_button, Qt.LeftButton)
    
    # ウィンドウ遷移確認
    assert isinstance(window.current_window, SenderWindow)
```

#### 5.2 コントローラーカード表示シナリオ

**シナリオ**: 検出されたコントローラーの表示
```python
def test_controller_card_display(qtbot):
    sender_window = SenderWindow()
    qtbot.addWidget(sender_window)
    
    # モックコントローラーデータ
    controllers = [
        DetectedController(
            pygame_id=0,
            device_id=1, 
            name="Xbox 360 Controller",
            guid="abc123",
            num_axes=6,
            num_buttons=14,
            num_hats=1
        )
    ]
    
    sender_window.update_controller_list(controllers)
    
    # コントローラーカードの存在確認
    controller_cards = sender_window.find_children(ControllerCard)
    assert len(controller_cards) == 1
    assert "Xbox 360" in controller_cards[0].controller_name_label.text()
```

### 6. アプリケーション統合テスト (`apps/`)

#### 6.1 送信アプリケーションシナリオ

**シナリオ**: CLI送信アプリの動作
```python
@pytest.mark.asyncio
async def test_sender_app_lifecycle():
    app = SenderApp(
        host="127.0.0.1",
        port=8765,
        config_file=None
    )
    
    # アプリケーション開始
    start_task = asyncio.create_task(app.start())
    await asyncio.sleep(0.1)  # 初期化待機
    
    # 実行状態確認
    assert app.running
    
    # アプリケーション停止
    await app.stop()
    assert not app.running
    
    await start_task
```

#### 6.2 受信アプリケーションシナリオ

**シナリオ**: CLI受信アプリの動作
```python
@pytest.mark.asyncio
async def test_receiver_app_with_virtual_controllers():
    app = ReceiverApp(
        host="127.0.0.1",
        port=8765,
        max_controllers=4
    )
    
    virtual_controllers_created = []
    
    def on_virtual_controller_create(controller_number):
        virtual_controllers_created.append(controller_number)
    
    app.virtual_controller_callback = on_virtual_controller_create
    
    # 受信アプリ開始
    await app.start()
    
    # 仮想コントローラー作成の確認
    assert len(virtual_controllers_created) <= 4
    
    await app.stop()
```

## エラーケーステストシナリオ

### 7.1 リソース不足シナリオ

**シナリオ**: メモリ不足やファイルハンドル不足時の動作
```python
def test_resource_exhaustion_handling():
    # ファイルハンドル制限テスト
    with patch('builtins.open', side_effect=OSError("Too many open files")):
        config = ConfigModel.load_from_file("config.json")
        # デフォルト設定で継続することを確認
        assert config.sender_config.receiver_host == "127.0.0.1"
```

### 7.2 権限不足シナリオ

**シナリオ**: アクセシビリティ権限不足時の処理
```python
@patch('pynput.keyboard.Controller')
def test_macos_permission_denied(mock_keyboard):
    mock_keyboard.side_effect = PermissionError("Accessibility permission required")
    
    with pytest.raises(PermissionError):
        controller = MacOSVirtualController(1)
    
    # ログにエラーメッセージが記録されることを確認
```

### 7.3 ネットワーク障害シナリオ

**シナリオ**: 様々なネットワーク障害への対応
```python
@pytest.mark.asyncio
async def test_network_failure_scenarios():
    # 接続拒否
    client = WebSocketClient("127.0.0.1", 9999)
    await client.start()  # 内部で再試行処理が実行される
    
    # タイムアウト
    with patch('websockets.connect', side_effect=asyncio.TimeoutError):
        await client._attempt_connection()
    
    # 接続切断
    # サーバー側での切断処理テスト
```

## パフォーマンステストシナリオ

### 8.1 高負荷シナリオ

**シナリオ**: 大量データ処理時のパフォーマンス
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_high_volume_message_processing():
    server = WebSocketServer("127.0.0.1", 0)
    await server.start()
    
    client = WebSocketClient("127.0.0.1", server.port)
    await client.start()
    
    start_time = time.time()
    
    # 1000メッセージを高速送信
    for i in range(1000):
        data = ControllerInputData(
            controller_number=1,
            controller_id="perf_test"
        )
        await client.send_controller_input(data)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # パフォーマンス基準: 1000メッセージを5秒以内で処理
    assert processing_time < 5.0
    
    await client.stop()
    await server.stop()
```

### 8.2 遅延測定シナリオ

**シナリオ**: エンドツーエンド遅延の測定
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_end_to_end_latency():
    received_timestamps = []
    
    def input_callback(input_data):
        received_timestamps.append(time.time())
    
    server = WebSocketServer("127.0.0.1", 0)
    server.input_callback = input_callback
    await server.start()
    
    client = WebSocketClient("127.0.0.1", server.port)
    await client.start()
    
    sent_timestamp = time.time()
    data = ControllerInputData(
        controller_number=1,
        controller_id="latency_test"
    )
    await client.send_controller_input(data)
    
    await asyncio.sleep(0.1)  # 受信待機
    
    if received_timestamps:
        latency = received_timestamps[0] - sent_timestamp
        # 遅延基準: 100ms以内
        assert latency < 0.1
```

## テスト実行順序

1. **単体テスト**: 個別コンポーネントの動作確認
2. **統合テスト**: コンポーネント間連携の確認  
3. **GUI テスト**: ユーザーインターフェースの動作確認
4. **エラーケーステスト**: 異常系の処理確認
5. **パフォーマンステスト**: 性能要件の確認

## テスト環境要件

### 最小環境
- Python 3.8+
- pytest 7.0+
- Mock/patch による外部依存の分離

### 完全テスト環境
- 物理コントローラー (Xbox/PlayStation)
- Windows: ViGEmドライバー
- macOS: アクセシビリティ権限
- ネットワーク接続

### CI環境
- ヘッドレス実行対応
- pygame の仮想ディスプレイ設定
- Mock による依存関係の分離