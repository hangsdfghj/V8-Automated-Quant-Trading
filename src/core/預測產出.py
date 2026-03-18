import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import os
import warnings

warnings.filterwarnings("ignore")

# ==========================================
# 1. 系統設定與路徑初始化
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

DATA_FILE = 'V8_特徵整合總表_含原始數據.csv'
THRESHOLD = 0.71 
TODAY_STR = datetime.now().strftime('%Y%m%d')
OUTPUT_NAME = f"今日狙擊清單_{TODAY_STR}.xlsx"

FEATURES_IN_MODEL = ['基差率', '基差率變動', '成交量比率', '乖離率', '乖離變動', 'RSI', 'ATR_Pct']

def get_tw_tick_size(price):
    """台股最小升降單位規則"""
    if price < 10: return 0.01
    elif price < 50: return 0.05
    elif price < 100: return 0.10
    elif price < 500: return 0.50
    elif price < 1000: return 1.00
    else: return 5.00

def apply_tw_tick_floor(price):
    """對齊台股跳動單位並執行無條件捨去"""
    tick = get_tw_tick_size(price)
    # 透過精度修正後執行 floor
    return np.floor(np.round(price / tick, 8)) * tick

def generate_sniper_report():
    print(f"⏳ 正在啟動 V8.0 ATR 波動導向預測引擎...")

    try:
        df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    except:
        print(f"❌ 找不到特徵檔 [{DATA_FILE}]")
        return

    df['日期'] = pd.to_datetime(df['日期'])
    df = df.sort_values(['標的名稱', '日期'])
    # 確保特徵完整
    df['乖離變動'] = df.groupby('標的名稱')['乖離率'].diff()
    df = df.rename(columns={'現貨RSI': 'RSI'})

    try:
        rf = joblib.load('rf_v8_model.pkl')
        gb = joblib.load('gb_v8_model.pkl')
        meta = joblib.load('meta_v8_model.pkl')
        scaler = joblib.load('scaler_v8.pkl')
    except Exception as e:
        print(f"❌ 模型載入失敗：{e}")
        return

    # 提取最後一筆數據進行預測
    latest_data = df.dropna(subset=FEATURES_IN_MODEL).groupby('標的名稱').tail(1).copy()
    
    if latest_data.empty:
        print("❌ 數據不足，無法執行。")
        return

    X_scaled = scaler.transform(latest_data[FEATURES_IN_MODEL])
    p_rf = rf.predict_proba(X_scaled)[:, 1]
    p_gb = gb.predict_proba(X_scaled)[:, 1]
    confidence = meta.predict_proba(np.column_stack([p_rf, p_gb]))[:, 1]
    
    latest_data['信心度'] = confidence

    # ==========================================
    # 2. 轉換格式 (進場價：收盤價 + 0.1 * ATR)
    # ==========================================
    sniper_list = latest_data[latest_data['信心度'] > THRESHOLD].copy()

    if sniper_list.empty:
        print("💡 今日無標的符合門檻。")
        return

    sniper_list['股票代碼'] = sniper_list['標的名稱'].str.extract(r'\((\d+)\)')
    
    # 【核心修正】改用 ATR 計算建議進場點
    # 我們取收盤價加上 0.1 倍的 ATR 波動金額，作為追價上限
    # 公式：收盤價 * (1 + 0.1 * ATR_Pct)
    raw_suggested = sniper_list['現貨收盤價'] * (1 + 0.1 * sniper_list['ATR_Pct'])
    sniper_list['建議進場點'] = raw_suggested.apply(apply_tw_tick_floor)
    
    sniper_list['信心度比例'] = sniper_list['信心度'].apply(lambda x: f"{x:.2%}")
    
    def get_reason(row):
        reasons = []
        # 直接揭露特徵數值，展現量化嚴謹度
        reasons.append(f"基差率 {row['基差率']:.2%}")
        reasons.append(f"乖離變動 {row['乖離變動']:.2%}")
        reasons.append(f"ATR 波動率 {row['ATR_Pct']:.1%}")
        reasons.append(f"RSI 指標 {row['RSI']:.0f}")
        return "；".join(reasons)
        
    sniper_list['進場原因'] = sniper_list.apply(get_reason, axis=1)

    final_output = sniper_list[['股票代碼', '建議進場點', '信心度比例', '進場原因']]
    final_output.to_excel(OUTPUT_NAME, index=False)
    print(f"✅ 專業版狙擊清單(ATR-Tick版)已產出：{OUTPUT_NAME}")

if __name__ == "__main__":
    generate_sniper_report()