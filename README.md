# 物聯網個人小專題 - 雷射槍標靶及線上排行榜 (IoT Laser Gun Target & Leaderboard)

## 📖 研究動機
因為平時喜歡玩射擊遊戲，且許多遊戲內都有專屬的標靶射擊練習區，因此決定親自動手製作一個具備實體互動與線上排行機制的雷射射擊系統。

## 🛠️ 使用硬體與材料
**雷射槍材料**
*   Arduino mini pro (做為接地與結構輔助)
*   LilyPad CR2032 電池座與 CR2032 電池
*   5V 雷射模組
*   紙箱與鋁箔紙
*   杜邦線

**雷射標靶材料**
*   NodeMCU-32S 開發板
*   Micro USB 線 (連接電腦供電)
*   光敏感測器 (安裝於標靶中心)
*   伺服馬達 (控制標靶倒下與彈回)
*   無源蜂鳴器 (音效提示)
*   SSD1306 OLED 螢幕 (顯示目前得分)
*   TM1637 七段顯示器 (顯示遊戲倒數時間)
*   實體按鈕 (啟動/重置遊戲)
*   麵包板、杜邦線、紙箱與木筷

## ⚙️ 系統運作原理
*   **雷射槍觸發機制**：透過壓下紙箱製的板機時，讓插在 Arduino mini pro GND 孔的杜邦線，觸碰到電池座負極上的鋁箔紙使電路導通，進而觸發 5V 雷射模組發射雷射光。
*   **標靶互動與計分**：NodeMCU-32S 透過 `machine` 模組控制硬體。遊戲啟動後限時 15 秒 (TM1637 顯示倒數)。當雷射光擊中光敏感測器，蜂鳴器會發出提示音，伺服馬達會帶動標靶向後倒 90 度再彈回，同時總分加 1 分並即時顯示於 OLED 螢幕上。
*   **分數上傳與資料庫儲存**：遊戲結束後，系統會透過 `urequests` 模組將帶有分數的 JSON 資料使用 HTTP POST 傳送至 Node-RED。Node-RED 接收後回傳 HTTP 200 狀態，並將資料進行時差處理 (+8 小時) 後存入 MySQL 資料庫 (`scorelist` 資料庫中的 `leaderboard` 資料表)。
*   **線上排行榜**：Node-RED 設定每 1 秒定期 (Inject) 向資料庫查詢前十名最高分紀錄 (ORDER BY score DESC LIMIT 10)，將撈取出的資料格式化後，傳送至 Dashboard 2.0 的 UI Template 節點呈現即時排名。

## 💻 程式碼引用模組 (MicroPython)
*   `machine`：控制硬體 GPIO、PWM (伺服馬達/蜂鳴器) 和 ADC (光敏感測器) 等功能。
*   `time`、`ntptime`：暫停執行、處理時間相關操作與 NTP 網路校時。
*   `network`：連接 Wi-Fi 處理網路通信。
*   `urequests`：發送 HTTP 請求與伺服器 (Node-RED) 交互資料。
*   `tm1637`：操作七段數碼顯示器顯示倒數計時。
*   `ssd1306`：控制 OLED 顯示器顯示圖形與大字體分數。

## 🗄️ 資料庫結構
*   **資料庫名稱**：`scorelist`
*   **資料表名稱**：`leaderboard`
*   **包含欄位**：
    *   `id` (主鍵，自動遞增)
    *   `score` (獲得分數)
    *   `play_time` (遊玩與記錄時間)

## 📚 參考文獻
*   [Node-RED Dashboard 2 UI Template Widget](https://dashboard.flowfuse.com/nodes/widgets/ui-template.html)
*   [Node-RED Dashboard 2.0: Layout, Navigation & Styling](https://flowfuse.com/blog/2024/05/node-red-dashboard-2-layout-navigation-styling/)