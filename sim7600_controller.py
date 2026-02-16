#!/usr/bin/env python3
"""
SIM7600 4G Dongle Controller
=========================
呢個程式可以控制 SIM7600 4G Dongle 打出同接收電話

功能：
- 打出電話
- 接收電話
- 對話記錄存入文字檔

使用前需要：
1. 插入 SIM7600 4G Dongle
2. install pyserial: pip3 install pyserial
3. 搵到正確既 serial port (通常係 /dev/tty.usbxxx)

"""


import serial
import time
import os
from datetime import datetime
from pathlib import Path


class SIM7600Controller:
    """SIM7600 4G Dongle 控制"""
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.call_log_dir = Path("call_logs")
        self.call_log_dir.mkdir(exist_ok=True)
        
    def connect(self):
        """連接 SIM7600"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"✅ 已連接到 {self.port}")
            return True
        except serial.SerialException as e:
            print(f"❌ 連接失敗: {e}")
            return False
    
    def send_at(self, command, wait=1):
        """發送 AT Command"""
        if not self.ser:
            print("❌ 未連接")
            return None
        
        self.ser.write(f"{command}\r\n".encode())
        time.sleep(wait)
        
        response = ""
        while self.ser.in_waiting:
            response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
        return response.strip()
    
    def get_signal(self): 
        """檢查訊號強度"""
        result = self.send_at("AT+CSQ")
        if result and "+CSQ:" in result:
            # Parse signal quality
            # +CSQ: <rssi>,<ber>
            # rssi: 0-31 (99 = not detectable)
            # ber: 0-7 (99 = not detectable)
            import re
            match = re.search(r'\+CSQ:\s*(\d+),(\d+)', result)
            if match:
                rssi = int(match.group(1))
                if rssi == 99:
                    return "無訊號"
                elif rssi >= 20:
                    return f"訊號強 ({rssi}/31)"
                else:
                    return f"訊號一般 ({rssi}/31)"
        return "無法獲取訊號"
    
    def make_call(self, phone_number):
        """打出電話"""
        print(f"📞 緊打去 {phone_number}...")
        
        # Dial
        result = self.send_at(f'ATD{phone_number};', wait=2)
        
        if "OK" in result or "CALL" in result:
            print(f"✅ 正在通話中... (按 Ctrl+C 結束)")
            self._call_active = True
            
            # 開始記錄
            log_file = self._create_log_file("outgoing", phone_number)
            
            # 等對方接聽
            time.sleep(2)
            
            # 監聽通話狀態
            self._monitor_call(log_file, phone_number, "outgoing")
            return True
        else:
            print(f"❌ 打出失敗: {result}")
            return False
    
    def answer_call(self):
        """接聽電話"""
        print("📞 正在接聽...")
        result = self.send_at("ATA")
        
        if "OK" in result:
            print("✅ 已接聽！開始對話...")
            self._call_active = True
            
            # 創建記錄檔
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = self.call_log_dir / f"incoming_{timestamp}.txt"
            
            self._monitor_call(log_file, "incoming", "incoming")
            return True
        return False
    
    def hangup(self): 
        """結束通話"""
        print("📴 正在結束通話...")
        result = self.send_at("ATH")
        self._call_active = False
        return "OK" in result
    
    def _create_log_file(self, call_type, number):
        """創建記錄檔"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{call_type}_{number}_{timestamp}.txt"
        filepath = self.call_log_dir / filename
        
        # 寫入標題
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"=== 通話記錄 ===\n")
            f.write(f"類型: {'打出' if call_type == 'outgoing' else '接收'}\n")
            f.write(f"號碼: {number}\n")
            f.write(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"==================\n\n")
        
        return filepath
    
    def _monitor_call(self, log_file, number, call_type):
        """監聽通話"""
        print(f"📝 正在記錄通話到: {log_file}")
        print("💬 對話內容 (Ctrl+C 結束通話):")
        
        try:
            while self._call_active:
                if self.ser and self.ser.in_waiting:
                    data = self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                    if data:
                        print(f"  > {data.strip()}")
                        
                        # 寫入記錄
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {data.strip()}\n")
                
                # 檢查是否仲係通話中
                result = self.send_at("AT+CPAS", wait=0.5)
                if result and "0" not in result:  # 0 = ready, 3 = incoming, 4 = call in progress
                    print("📴 對方已掛線")
                    self._call_active = False
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷")
        finally:
            self.hangup()
            print(f"✅ 通話記錄已保存: {log_file}")
    
    def list_call_logs(self):
        """列出所有通話記錄"""
        print("\n=== 通話記錄 ===")
        logs = sorted(self.call_log_dir.glob("*.txt"), key=os.path.getmtime, reverse=True)
        
        if not logs:
            print("暫無記錄")
            return
        
        for log in logs[:10]:  # 最近10條
            with open(log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"\n📄 {log.name}")
                if lines:
                    print(f"   {lines[0].strip()}")  # 類型
                    print(f"   {lines[1].strip()}")  # 號碼
    
    def close(self):
        """關閉連接"""
        if self.ser:
            self.ser.close()
            print("✅ 已斷開連接")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='SIM7600 4G Dongle Controller')
    parser.add_argument('--port', default='/dev/ttyUSB0', help='Serial port (default: /dev/ttyUSB0)')
    parser.add_argument('--make-call', '-m', help='打出電話號碼')
    parser.add_argument('--answer', '-a', action='store_true', help='接聽電話')
    parser.add_argument('--hangup', '-h', action='store_true', help='結束通話')
    parser.add_argument('--logs', '-l', action='store_true', help='顯示通話記錄')
    parser.add_argument('--signal', '-s', action='store_true', help='檢查訊號')
    
    args = parser.parse_args()
    
    sim = SIM7600Controller(port=args.port)
    
    if not sim.connect():
        print("\n💡 提示：")
        print("1. 確認 SIM7600 已插入")
        print("2. 確認 drivers 已安裝")
        print("3. 搵到正確既 port: ls /dev/tty.*")
        return
    
    # 檢查訊號
    if args.signal or args.make_call or args.answer:
        print(f"📶 訊號: {sim.get_signal()}")
    
    if args.make_call:
        sim.make_call(args.make_call)
    
    elif args.answer:
        sim.answer_call()
    
    elif args.hangup:
        sim.hangup()
    
    elif args.logs:
        sim.list_call_logs()
    
    else:
        # Interactive mode
        print("""
=== SIM7600 4G Dongle 控制 ===

指令:
  --make-call <號碼>  打出電話
  --answer            接聽電話  
  --hangup            結束通話
  --logs              顯示通話記錄
  --signal            檢查訊號

例子:
  python sim7600.py --make-call +85312345678
  python sim7600.py --answer
  python sim7600.py --logs
        """)
    
    sim.close()


if __name__ == "__main__":
    main()
