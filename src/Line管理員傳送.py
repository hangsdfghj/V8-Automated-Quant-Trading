import pandas as pd
import requests
import os
from datetime import datetime
import warnings
from dotenv import load_dotenv

# 忽略警告
warnings.filterwarnings("ignore")

# ==========================================
# 1. 初始化與環境變數
# ==========================================
# 確保程式執行路徑與檔案所在位置相同 (雙重保險)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# 載入 .env 變數
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_TARGET_ID = os.getenv("LINE_TARGET_ID")

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
}

TODAY_DT = datetime.now()
TODAY_STR = TODAY_DT.strftime('%Y%m%d')
DISPLAY_DATE = TODAY_DT.strftime('%Y/%m/%d')
SNIPER_FILE_PATTERN = f"今日狙擊清單_{TODAY_STR}.xlsx"

# ==========================================
# 2. 戰報格式化與切分
# ==========================================
def format_price(price):
    try:
        if price == int(price): return str(int(price))
        return f"{price:g}"
    except:
        return str(price)

def get_formatted_chunks():
    chunks = []
    
    if not os.path.exists(SNIPER_FILE_PATTERN):
        print(f"⚠️ 找不到檔案: {SNIPER_FILE_PATTERN}")
        return [f"⚠️ 尚未產出 {TODAY_STR} 的 Excel 戰報檔案。"]

    try:
        df_sniper = pd.read_excel(SNIPER_FILE_PATTERN)
        if df_sniper.empty:
            return [f"💡 今日 ({TODAY_STR}) 戰報無符合條件的資料。"]
        
        # 標題與結尾
        header_text = f"🎯 V8.0 量化戰報 ({DISPLAY_DATE})\n\n"
        footer_text = (
            "\n"
            "💡 交易紀律：進場價已依 ATR 與 Tick 規則優化，超標不追。\n"
            "🔔 以上僅供研究參考，建議明日收盤平倉。"
        )
        
        # 組合每一檔股票
        all_items = []
        for _, row in df_sniper.iterrows():
            p_display = format_price(row.get('建議進場點', 'N/A'))
            item = (
                f"📈 股票代碼：{row.get('股票代碼', 'N/A')}\n"
                f"💰 建議進場點：{p_display} (最高容忍價)\n"
                f"🎯 信心度比例：{row.get('信心度比例', 'N/A')}\n"
                f"📝 量化指標：{row.get('進場原因', 'N/A')}\n"
                "----------------------------\n"
            )
            all_items.append(item)
            
        # 智慧分頁 (避免 LINE 單則訊息過長)
        current_chunk = header_text
        MAX_CHARS = 1500
        
        for item in all_items:
            if len(current_chunk) + len(item) + len(footer_text) > MAX_CHARS:
                chunks.append(current_chunk + footer_text)
                current_chunk = header_text + item
            else:
                current_chunk += item
                
        if current_chunk:
            chunks.append(current_chunk + footer_text)
            
    except Exception as e:
        print(f"⚠️ 讀取戰報失敗: {e}")
        chunks.append(f"⚠️ 無法讀取戰報詳情 ({e})")
        
    return chunks

# ==========================================
# 3. 發送邏輯
# ==========================================
def main():
    print(f"🚀 啟動 LINE 群組戰報發送程式 ({TODAY_STR})...")

    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_TARGET_ID:
        print("❌ 錯誤：請確保 .env 檔案中已設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_TARGET_ID。")
        return

    raw_chunks = get_formatted_chunks()
    
    # 準備發送的 payload
    url = "https://api.line.me/v2/bot/message/push"
    payload_messages = [{"type": "text", "text": chunk} for chunk in raw_chunks]

    try:
        # LINE 每次 Push 最多包含 5 個 message object
        for i in range(0, len(payload_messages), 5):
            batch = payload_messages[i:i+5]
            payload = {
                "to": LINE_TARGET_ID.strip(),
                "messages": batch
            }
            response = requests.post(url, headers=HEADERS, json=payload, timeout=15)
            
            if response.status_code == 200:
                print(f"  ✅ [LINE] 第 {i//5 + 1} 批次發送成功！")
            else:
                print(f"  ❌ [LINE] 發送失敗: {response.text}")
    except Exception as e:
        print(f"🚨 發生不可預期的錯誤: {e}")

    print("🏁 執行結束。")

if __name__ == "__main__":
    main()