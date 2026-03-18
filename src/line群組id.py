import schedule
import time
from linebot import LineBotApi
from linebot.models import TextSendMessage

# --- 設定區 ---
CHANNEL_ACCESS_TOKEN = '你的Token'
GROUP_ID = '你剛剛抓到的C開頭ID'

def job():
    try:
        line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
        # 設定你想傳送的訊息內容
        msg = "早安！這是今天的自動提醒訊息。"
        
        line_bot_api.push_message(GROUP_ID, TextSendMessage(text=msg))
        print(f"[{time.strftime('%H:%M:%S')}] 訊息發送成功！")
    except Exception as e:
        print(f"發送失敗: {e}")

# 設定每天下午 3:45 執行 (請根據需求修改時間)
schedule.every().day.at("15:45").do(job)

print("自動發送服務運行中... (按 Ctrl+C 結束)")

while True:
    schedule.run_pending()
    time.sleep(1)