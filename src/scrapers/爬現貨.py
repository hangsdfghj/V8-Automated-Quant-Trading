import time
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_yahoo_spot_data(target_list):
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    all_data_frames = [] # 用來存儲所有標的的 DataFrame
    
    for symbol in target_list:
        data_list = []
        url = f"https://tw.stock.yahoo.com/quote/{symbol}/technical-analysis"
        
        try:
            print(f"\n🔎 正在採集現貨標的: [{symbol}]")
            driver.get(url)
            wait = WebDriverWait(driver, 15)

            # 1. 關閉干擾廣告 (使用你提供的 SVG Path)
            try:
                ad_close_xpath = "//*[local-name()='path' and contains(@d, 'M13.4406')]/ancestor::button"
                ad_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, ad_close_xpath)))
                driver.execute_script("arguments[0].click();", ad_btn)
                print("✅ 廣告已排除")
            except:
                pass

            # 2. 擷取「標的名稱」(從 h2 抓取，例如：欣興 (3037))
            try:
                name_xpath = "//div[@id='qsp-technicalAnalysis-chart']//h2"
                raw_name = wait.until(EC.presence_of_element_located((By.XPATH, name_xpath))).text
                # 格式化名稱，移除多餘空白
                target_label = raw_name.strip()
                print(f"🎯 目標名稱確定：{target_label}")
            except:
                target_label = symbol
                print(f"⚠️ 無法識別 h2 名稱，使用代碼: {symbol}")

            # 3. 定位 K 棒並等待渲染
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))
            time.sleep(3) 
            candles = driver.find_elements(By.CSS_SELECTOR, "g.highcharts-series-0 path.highcharts-point")
            
            if not candles:
                print(f"⚠️ {symbol} 找不到圖表數據，跳過")
                continue

            print(f"📈 辨識到 {len(candles)} 根 K 棒，採集最後 20 筆數據...")
            actions = ActionChains(driver)
            last_date = ""

            # 4. 模擬懸停採集 (針對現貨標籤優化)
            target_range = candles[-30:] 
            for candle in target_range:
                try:
                    # 置中捲動並微調，確保頂部資料區不被擋住
                    driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", candle)
                    driver.execute_script("window.scrollBy(0, -160);")
                    time.sleep(0.1)
                    actions.move_to_element(candle).perform()
                    
                    for retry in range(10):
                        # 日期擷取
                        date_val = driver.find_element(By.XPATH, "//div[contains(@class, 'Whs(nw)') and contains(@class, 'D(b)--mobileLandscape')]").get_attribute('textContent').strip()
                        
                        if date_val and date_val != last_date:
                            # 收盤價擷取
                            close_val = driver.find_element(By.XPATH, "//span[text()='收']/following-sibling::span").get_attribute('textContent').strip().replace(',', '')
                            
                            # 成交量擷取 (現貨標籤為「量(張)」，不乘 1000)
                            try:
                                vol_el = driver.find_element(By.XPATH, "//span[contains(text(), '量')]/following-sibling::span")
                                vol_val = vol_el.get_attribute('textContent').strip().replace(',', '')
                            except:
                                vol_val = "0"
                            
                            data_list.append({
                                "標的名稱": target_label,
                                "日期": date_val,
                                "現貨收盤價": float(close_val),
                                "現貨成交量(張)": int(vol_val)
                            })
                            last_date = date_val
                            break
                        time.sleep(0.1)
                except:
                    continue

            # 轉成 DataFrame 存入清單
            if data_list:
                all_data_frames.append(pd.DataFrame(data_list))
                print(f"✅ {target_label} 擷取完成")

        except Exception as e:
            print(f"🚨 處理 {symbol} 時發生錯誤: {e}")
            continue

    # 5. 合併所有數據並儲存成單一 Excel
    if all_data_frames:
        final_df = pd.concat(all_data_frames, ignore_index=True)
        # 自動依照標的與日期命名
        output_file = "所有標的整合表[現貨].xlsx"
        final_df.to_excel(output_file, index=False)
        print("\n" + "═"*40)
        print(f"🏁 任務完成！")
        print(f"📁 總表路徑：{output_file}")
        print(f"📊 總筆數：{len(final_df)} 筆")
        print("═"*40)
    else:
        print("\n❌ 失敗：未抓取到任何數據")

    driver.quit()

# --- 執行區 ---
if __name__ == "__main__":
    # 你可以把所有現貨代碼放在這裡，它會一檔一檔爬完並合併
    spot_targets = [
        "3037.TW",  # 欣興
        "2330.TW",  # 台積電
    ]
    
    scrape_yahoo_spot_data(spot_targets)