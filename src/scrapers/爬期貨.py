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

def scrape_yahoo_all_in_one(target_list):
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # 建立一個空清單，用來存放所有標的的 DataFrame
    all_dfs = []
    
    for symbol in target_list:
        data_list = []
        url = f"https://tw.stock.yahoo.com/quote/{symbol}/technical-analysis"
        
        try:
            print(f"\n🔎 正在採集標的: [{symbol}]")
            driver.get(url)
            wait = WebDriverWait(driver, 15)

            # 1. 擷取標的名稱
            try:
                tag_xpath = "//div[contains(@class, 'tag-group-wrapper')]//a"
                target_label = wait.until(EC.presence_of_element_located((By.XPATH, tag_xpath))).get_attribute('textContent').strip()
            except:
                target_label = symbol
            
            print(f"🎯 目標名稱確定：{target_label}")

            # 2. 關閉廣告
            try:
                ad_close_xpath = "//*[local-name()='path' and contains(@d, 'M13.4406')]/ancestor::button"
                ad_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, ad_close_xpath)))
                driver.execute_script("arguments[0].click();", ad_btn)
                print("✅ 廣告已關閉")
            except:
                pass

            # 3. 定位並採集 K 棒
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "highcharts-root")))
            time.sleep(3) 
            candles = driver.find_elements(By.CSS_SELECTOR, "g.highcharts-series-0 path.highcharts-point")
            
            if not candles:
                print(f"⚠️ {symbol} 找不到圖表數據，跳過")
                continue

            actions = ActionChains(driver)
            last_date = ""
            target_range = candles[-30:] # 抓最後 20 筆

            for candle in target_range:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", candle)
                    driver.execute_script("window.scrollBy(0, -150);")
                    time.sleep(0.1)
                    actions.move_to_element(candle).perform()
                    
                    for retry in range(10):
                        date_val = driver.find_element(By.XPATH, "//div[contains(@class, 'Whs(nw)') and contains(@class, 'D(b)--mobileLandscape')]").get_attribute('textContent').strip()
                        
                        if date_val and date_val != last_date:
                            close_val = driver.find_element(By.XPATH, "//span[text()='收']/following-sibling::span").get_attribute('textContent').strip().replace(',', '')
                            vol_raw = driver.find_element(By.XPATH, "//span[text()='量']/following-sibling::span").get_attribute('textContent').strip().replace(',', '')
                            
                            data_list.append({
                                "標的": target_label,
                                "日期": date_val,
                                "期貨收盤價": float(close_val),
                                "期貨成交量": int(float(vol_raw) * 1000)
                            })
                            last_date = date_val
                            break
                        time.sleep(0.1)
                except:
                    continue

            # 4. 將當前標的轉換為 DataFrame
            if data_list:
                all_dfs.append(pd.DataFrame(data_list))
                print(f"📊 {target_label} 數據擷取完成 (共 {len(data_list)} 筆)")

        except Exception as e:
            print(f"🚨 標的 {symbol} 發生異常: {e}")
            continue

    # 5. 合併與輸出
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        # 輸出為 Excel 檔 (記得先安裝 pip install openpyxl)
        output_name = "所有標的整合表[期貨].xlsx"
        final_df.to_excel(output_name, index=False)
        print("\n" + "═"*40)
        print(f"🏁 全部任務完成！")
        print(f"📁 總表已存為：{output_name}")
        print(f"📈 總筆數：{len(final_df)} 筆")
        print("═"*40)
    else:
        print("\n❌ 失敗：沒有抓到任何資料。")

    driver.quit()

if __name__ == "__main__":
    # 你可以在這裡列出所有想要抓的標的代碼
    stock_targets = ["WIRF&", "WCDF&"] 
    scrape_yahoo_all_in_one(stock_targets)