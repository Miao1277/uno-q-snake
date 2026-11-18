# Arduino UNO Q 雙核心 LED 點矩陣與終端機貪吃蛇遊戲

本專題在 **Arduino UNO Q** 開發板上實作無需外接感測器與螢幕的貪吃蛇遊戲，充分發揮其**異質雙核心架構（Qualcomm Linux MPU + STM32 MCU）**，實現電腦終端機與板載 **13×8 LED 點矩陣** 1:1 雙螢幕同步顯示。

## 系統架構說明
- **Linux 端 (`main.py`)**：負責貪吃蛇遊戲核心運算、碰撞偵測、動態加速機制、ANSI Escape Code 無閃爍終端機畫面渲染，並建立 TCP Socket 伺服器（Port `8899`）接收低延遲鍵盤操作。
- **STM32 MCU 端 (`sketch.ino`)**：透過 `Arduino_RouterBridge` RPC 接收 Linux 端指令，即時控制板載硬體：
  - **13×8 板載 LED 點矩陣 (`updateMatrix`)**：1:1 即時同步顯示蛇身移動軌跡與食物位置。
  - **板載狀態指示燈 (`LED_BUILTIN`)**：吃到食物（`+10 分`）閃爍一次（150ms）、遊戲結束（Game Over）恆亮、重新開始時熄滅。

## 操作按鍵說明
- `SPACE`（空白鍵）：開始遊戲 / 結束後重新遊玩
- `W` / `A` / `S` / `D`：控制方向（上 / 左 / 下 / 右）
- `Q`：離開連線

## 執行步驟
1. 使用 **Arduino App Lab** 開啟本專案並點擊 **Run**，自動燒錄 STM32 韌體並啟動 Python Bridge 伺服器。
2. 開啟 UNO Q 板載終端機，連線至容器內網的 Port `8899`，按下空白鍵即可開始遊玩。
