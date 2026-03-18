import pandas as pd
import numpy as np
import os
import warnings

warnings.filterwarnings("ignore")

def calculate_rsi(series, period=14):
    """計算 RSI 指標 (14D)"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def generate_v8_master_table():
    print("⏳ 正在執行期貨與現貨數據合併...")
    
    # 1. 讀取爬蟲產出的原始 Excel 檔
    try:
        # 爬現貨.py 產出的檔名
        spot_df = pd.read_excel('所有標的整合表[現貨].xlsx')
        # 爬期貨.py 產出的檔名
        future_df = pd.read_excel('所有標的整合表[期貨].xlsx')
    except Exception as e:
        print(f"❌ 讀取 Excel 失敗，請確認前兩步爬蟲是否成功: {e}")
        return

    # 2. 標的名稱清洗與對齊
    # 現貨: "欣興 (3037)" -> "欣興"
    spot_df['標的簡稱'] = spot_df['標的名稱'].str.extract(r'^([^\s\(（]+)')
    # 期貨: "欣興期貨" -> "欣興"
    future_df['標的簡稱'] = future_df['標的'].str.replace('期貨', '', regex=False).str.strip()
    
    # 3. 日期格式統一
    spot_df['日期'] = pd.to_datetime(spot_df['日期'].astype(str).str.strip())
    future_df['日期'] = pd.to_datetime(future_df['日期'].astype(str).str.strip())

    # 4. 合併資料 (Inner Join)
    merged_df = pd.merge(spot_df, future_df, on=['日期', '標的簡稱'], how='inner')
    
    # 5. 逐標的分組計算 7 大核心特徵
    final_list = []
    for name, group in merged_df.groupby('標的簡稱'):
        g = group.copy().sort_values('日期')
        
        # --- 核心修正區：對齊爬蟲產出的欄位名稱 ---
        # A. 基差率 = (期貨收盤價 - 現貨收盤價) / 現貨收盤價
        g['基差率'] = (g['期貨收盤價'] - g['現貨收盤價']) / g['現貨收盤價']
        
        # B. 基差率變動
        g['基差率變動'] = g['基差率'].diff()
        
        # C. 成交量比率 = 期貨成交量 / 現貨成交量(張)
        g['成交量比率'] = g['期貨成交量'] / g['現貨成交量(張)']
        
        # D. 乖離率 (使用 MA5)
        ma5 = g['現貨收盤價'].rolling(window=5).mean()
        g['乖離率'] = (g['現貨收盤價'] - ma5) / ma5
        
        # E. 乖離變動 (模型需要的第 5 個特徵)
        g['乖離變動'] = g['乖離率'].diff()
        
        # F. 現貨RSI (更名為 RSI 以符合模型)
        g['RSI'] = calculate_rsi(g['現貨收盤價'], period=14)
        
        # G. ATR_Pct (14D)
        tr_proxy = g['現貨收盤價'].diff().abs()
        g['ATR_Pct'] = tr_proxy.rolling(window=14).mean() / g['現貨收盤價']
        
        final_list.append(g)

    # 6. 合併與清理
    result_df = pd.concat(final_list, ignore_index=True)
    result_df = result_df.dropna() # 刪除計算產生的空值

    # 7. 排序：先日期再標的
    result_df = result_df.sort_values(by=['日期', '標的名稱'], ascending=[True, True])

    # 8. 格式化輸出
    output_filename = 'V8_特徵整合總表_含原始數據.csv'
    # 使用 utf-8-sig 確保 Excel 開啟不亂碼，且預測腳本能正確讀取
    result_df.to_csv(output_filename, index=False, encoding='utf-8-sig')
    
    print(f"✅ 合併完成！已產出：{output_filename}")
    print(f"📊 總筆數：{len(result_df)} 筆")

if __name__ == "__main__":
    generate_v8_master_table()