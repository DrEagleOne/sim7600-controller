# SIM7600 4G Dongle Controller

## 呢個程式可以做到：

✅ 打出電話  
✅ 接收電話  
✅ 對話記錄存入文字檔  

---

## 安裝步驟

### 1. Install Python Library
```bash
pip3 install pyserial
```

### 2. 插入 SIM7600 Dongle
- 將 4G Dongle 插入 Mac USB
- 確認有 drivers (Mac usually has built-in drivers)

### 3. 搵到 Serial Port
```bash
ls /dev/tty.*
```
搵 `/dev/tty.usbxxx` 或 `/dev/cu.usbxxx` 開頭既device

---

## 使用方法

### 檢查訊號
```bash
python3 sim7600_controller.py --port /dev/tty.usbxxx --signal
```

### 打出電話
```bash
python3 sim7600_controller.py --port /dev/tty.usbxxx --make-call +85312345678
```

### 接聽電話
```bash
python3 sim7600_controller.py --port /dev/tty.usbxxx --answer
```

### 顯示通話記錄
```bash
python3 sim7600_controller.py --port /dev/tty.usbxxx --logs
```

### 結束通話
```bash
python3 sim7600_controller.py --port /dev/tty.usbxxx --hangup
```

---

## 記錄檔位置

所有通話記錄會存入 `call_logs/` folder：
- `outgoing_號碼_時間.txt` - 打出既電話
- `incoming_號碼_時間.txt` - 接收既電話

---

## 溫馨提示

- 需要一張有通話功能既 SIM 卡 (唔係純上網卡)
- SIM 卡要啟用 VoLTE 先可以打語音電話
- 如果打唔到，可能需要 APN 設定
