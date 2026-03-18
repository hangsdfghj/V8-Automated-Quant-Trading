import pandas as pd
import requests
import os
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. 系統路徑與日期初始化
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

TODAY_STR = datetime.now().strftime('%Y%m%d') 
CUSTOMER_LIST_FILE = "顧客名單.xlsx"
SNIPER_LIST_FILE = f"今日狙擊清單_{TODAY_STR}.xlsx"

# Discord 字元限制為 2000，我們保險設定在 1800 以內進行切分
MAX_DISCORD_LENGTH = 1800

def format_price(price):
    """
    優化價格顯示：
    1. 先四捨五入到小數點後 2 位 (台股最小 Tick 是 0.01，所以 2 位絕對夠)
    2. 轉為字串後，去掉末尾多餘的 0
    3. 如果最後剩個點，也去掉
    """
    # 先做一次 round 修正浮點數誤差，再格式化成字串
    formatted = "{:.2f}".format(round(price, 2))
    
    # 去除末尾的 0 (例如 47.40 -> 47.4) 與多餘的點 (例如 3135.00 -> 3135)
    return formatted.rstrip('0').rstrip('.')
    try:
        if price == int(price): return str(int(price))
        return f"{price:g}"
    except:
        return str(price)

def send_bulk_sniper_report():
    print(f"🕒 --- Discord 發送任務啟動: {datetime.now().strftime('%H:%M:%S')} ---")
    
    if not os.path.exists(SNIPER_LIST_FILE):
        print(f"❌ 找不到今日檔案 {SNIPER_LIST_FILE}")
        return

    try:
        customers_df = pd.read_excel(CUSTOMER_LIST_FILE)
        sniper_df = pd.read_excel(SNIPER_LIST_FILE)
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        return

    if sniper_df.empty:
        print("💡 今日無標的符合門檻。")
        return

    # 2. 預先打包所有股票項目
    display_date = datetime.now().strftime('%Y/%m/%d')
    header = f"━━━━━━━━━━━━━━━━━━━━\n🎯 **V8.0 量化戰報** ({display_date})\n━━━━━━━━━━━━━━━━━━━━\n\n"
    footer = (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **交易紀律**：進場價已依 ATR 與 Tick 規則優化，超標不追。\n"
        f"🔔 *以上僅供研究參考，建議明日收盤平倉。*\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

    all_stock_items = []
    for _, row in sniper_df.iterrows():
        p_display = format_price(row['建議進場點'])
        item = (
            f"📈 **股票代碼：{row['股票代碼']}**\n"
            f"💰 建議進場點：**{p_display}** (最高容忍價)\n"
            f"🎯 信心度比例：**{row['信心度比例']}**\n"
            f"📝 量化指標：{row['進場原因']}\n"
            f"----------------------------\n"
        )
        all_stock_items.append(item)

    # 3. 訊息切分邏輯 (防止超過 2000 字)
    final_messages = []
    current_message = header
    
    for item in all_stock_items:
        # 如果當前訊息 + 新項目 + 結尾字數 > 限制，就先存檔並開啟新訊息
        if len(current_message) + len(item) + len(footer) > MAX_DISCORD_LENGTH:
            final_messages.append(current_message + footer)
            current_message = header + " (續)\n\n" + item
        else:
            current_message += item
    
    # 加入最後一則訊息
    final_messages.append(current_message + footer)

    # 4. 發送給 Local 環境顧客
    current_rows = customers_df[customers_df['執行環境'] == 'Local']
    sent_count = 0

    for _, customer in current_rows.iterrows():
        webhook_url = str(customer['Webhook_URL']).strip()
        name = customer['顧客名稱']
        
        print(f"📡 正在發送戰報至 [{name}] (共分 {len(final_messages)} 則訊息)...")
        
        try:
            for i, msg in enumerate(final_messages):
                payload = {"content": f"👋 {name}，這是今日戰報 ({i+1}/{len(final_messages)})：\n\n{msg}"}
                response = requests.post(webhook_url, json=payload, timeout=15)
                
                if response.status_code in [200, 204]:
                    print(f"  ✅ 第 {i+1} 部分發送成功")
                    if i == len(final_messages) - 1: sent_count += 1
                else:
                    print(f"  ❌ 第 {i+1} 部分發送失敗！(Status: {response.status_code}) - {response.text}")
        except Exception as e:
            print(f"🚨 發送過程異常: {e}")

    print(f"\n🏁 --- 任務結束，成功傳遞給 {sent_count} 位訂閱者 ---")

if __name__ == "__main__":
    send_bulk_sniper_report()