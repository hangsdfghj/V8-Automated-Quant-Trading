@echo off
chcp 65001
title V8 股市預測自動化系統

:: 1. 切換到專題路徑
cd /d "C:\Users\hangs\OneDrive\Desktop\專題"

echo ========================================
echo [1/5] 正在爬取現貨資料...
python 爬現貨.py

echo [2/5] 正在爬取期貨資料...
python 爬期貨.py

echo [3/5] 正在進行數據合併與特徵工程...
python 期貨+現貨合併.py

echo [4/5] 正在執行 V8 Stacking 模型預測...
python 預測產出.py

echo [5/5] 正在將狙擊戰報發送到 Discord...
python 0206管理員傳送.py

echo ========================================
echo ✅ 所有任務已完成！
pause