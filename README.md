\# 🚀 V8 智慧量化狙擊系統：基於 Stacking 集成學習之台股交易框架



!\[Python](https://img.shields.io/badge/Python-3.8+-blue.svg)

!\[Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Latest-orange.svg)

!\[License](https://img.shields.io/badge/License-MIT-green.svg)



\## 📖 專案概述：AI 狙擊手故事

在台股市場中，期貨與現貨之間的「基差（Basis）」往往隱含了法人大戶的情緒轉折。本專案開發了一個自動化「AI 狙擊手」，透過監控期現貨價差、動量指標及波動率，精準捕捉權值股次日漲幅超過 \*\*1.5%\*\* 的噴發瞬間。



本系統實現了從 \*\*數據自動採集 (Scraping)\*\*、\*\*特徵工程 (Feature Engineering)\*\*、\*\*模型推論 (Stacking Model)\*\* 到 \*\*多平台自動化戰報推送 (Deployment)\*\* 的全流程閉環。







\---



\## 📈 實戰績效 (2023 - 2025)

經三年回測驗證，系統於 15 檔核心白名單標的（如：鴻海、長榮、緯穎、廣達等）表現優異：

\- \*\*累積報酬率：55.58%\*\*

\- \*\*總交易次數：64 次\*\* (均為高信心度狙擊訊號)

\- \*\*核心價值\*\*：具備高勝率過濾機制，成功排除 80% 以上的市場無效雜訊。



\---



\## 🛠️ 技術架構與核心算法



\### 1. Stacking 集成學習模型 (Ensemble Learning)

系統採用雙層疊加架構，兼顧穩定性與靈敏度：

\- \*\*第一層 (Base Models)\*\*：

&#x20; - \*\*Random Forest (隨機森林)\*\*：穩健的投票者，負責抗噪與捕捉非線性關係。

&#x20; - \*\*Gradient Boosting (梯度提升樹)\*\*：精準的糾錯者，擅長捕捉微小的動能轉折。

\- \*\*第二層 (Meta Model)\*\*：

&#x20; - \*\*Logistic Regression (邏輯回歸)\*\*：理性執行長，整合兩大模型預測機率，產出最終 \*\*信心指數 (Confidence Index)\*\*。



\### 2. 核心量化因子 (Feature Engineering)

\- \*\*跨市場因子\*\*：基差率、基差率變動 (監控期現背離)。

\- \*\*動量與空間\*\*：RSI、乖離率、乖離變動 (捕捉加速度)。

\- \*\*風險控管\*\*：ATR 波動率 (動態決定進場位與追價距離)。



\### 3. 實戰部署優化

\- \*\*Tick Size 對齊\*\*：自動計算符合台股規範之最小跳動單位（如 10-50 元跳 0.05）。

\- \*\*多平台推送\*\*：整合 Discord Webhook 與 LINE Messaging API，具備智慧訊息切分邏輯。



\---



\## 📂 目錄結構

```text

├── models/                  # 訓練完成之模型持久化檔案 (.pkl)

├── src/

│   ├── scrapers/            # 數據採集：Selenium 自動化爬蟲 (現貨/期貨)

│   ├── core/                # 核心邏輯：數據合併、特徵工程與模型預測

│   └── notifications/       # 自動化通知：Discord \& LINE 訊息發送模組

├── requirements.txt         # 專案套件依賴清單

└── .env.example             # 環境變數設定範例 (不含私密 Token)

