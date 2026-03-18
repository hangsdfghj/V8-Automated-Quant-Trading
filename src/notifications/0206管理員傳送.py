import pandas as pd
import requests
import os
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

TODAY_STR = datetime.now().strftime('%Y%m%d') 
CUSTOMER_LIST_FILE = "顧客名單.xlsx"
SNIPER_LIST_FILE = f"今日狙擊清單_{TODAY_STR}.xlsx"
IS_GITHUB = os.getenv("GITHUB_ACTIONS") == "true"

def format_price(price):
    """格式化價格，整數不顯示小數點"""
    if price == int(price): return str(int(price))
    return f"{price:g}"

def send_bulk_sniper_report():
    print(f"🕒 Discord 發送啟動: {datetime.now().strftime('%H:%M:%S')}")

    if not os.path.exists(SNIPER_LIST_FILE):
        print(f"❌ 找不到今日檔案: {SNIPER_LIST_FILE}")
        return

    try:
        customers_df = pd.read_excel(CUSTOMER_LIST_FILE)
        sniper_df = pd.read_excel(SNIPER_LIST_FILE)
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        return

    display_date = datetime.now().strftime('%Y/%m/%d')
    header = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **V8.0 量化戰略：今日狙擊清單** ({display_date})\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    body_items = []
    for _, row in sniper_df.iterrows():
        p_display = format_price(row['建議進場點'])
        item = (
            f"📈 **股票代碼：{row['股票代碼']}**\n"
            f"💰 建議進場點：**{p_display}** (最高容忍價)\n"
            f"🎯 信心度比例：**{row['信心度比例']}**\n"
            f"📝 量化特徵：{row['進場原因']}\n"
            f"----------------------------"
        )
        body_items.append(item)
    
    footer = (
        f"\n━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **交易紀律**：基於 ATR 波動計算建議價，超標請勿追高。\n"
        f"🔔 *建議明日收盤結算，僅限當日有效。*\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    full_message = header + "\n".join(body_items) + footer

    # 篩選 Local 環境顧客
    current_rows = customers_df[customers_df['執行環境'] == 'Local']

    for _, customer in current_rows.iterrows():
        webhook_url = customer['Webhook_URL']
        payload = {"content": f"👋 {customer['顧客名稱']}，今日戰報：\n\n{full_message}"}
        requests.post(webhook_url, json=payload)

    print(f"✅ 成功發送給 {len(current_rows)} 位訂閱者。")

if __name__ == "__main__":
    send_bulk_sniper_report()