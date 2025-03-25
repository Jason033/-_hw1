# hw1
# Q-Learning GridWorld Flask 應用互動報告

本報告整理了從最初需求到最終調試的整個互動過程，並記錄了各階段修改的內容與除錯過程。該文件可在 GitHub 上正常顯示，且適用於 Markdown 編譯器。

---

## 1. 需求概述

### 1.1 初始需求
- **網格生成與設定**  
  - 使用者在網頁上輸入網格大小（介於 3 至 10，預設為 5）。
  - 按下「生成網格」後，網格會以依序編號（從左到右、從上到下）生成。
  - 使用者依序點擊設定：
    - 第一次點擊：設定**起點**（綠色）。
    - 第二次點擊：設定**終點**（紅色）。
    - 後續點擊：設定最多 `(gridSize - 2)` 個**障礙物**（灰色）。

- **Q-Learning 訓練與顯示**  
  - 按下「開始 Q Learning」後，後端進行 1000 次 Q-Learning 迭代，計算出最佳策略和每個網格的 Q-value。
  - 前端以動畫方式在主網格中高亮顯示最佳路徑。
  - 原始版本將箭頭（代表最佳動作）與 Q-value 直接疊加在網格中。

### 1.2 後續修改需求
1. **顯示區塊分離**  
   - 將箭頭 (Policy) 與 Q-value 分別在兩個不同的表格中顯示，原網格僅保留起點、終點、障礙物與最佳路徑動畫。

2. **新增 Reset 功能**  
   - 加入 Reset 按鈕，可清除所有內容（網格、點擊狀態、結果表格），使得每次開始 Q-Learning 都是全新狀態。

3. **錯誤提示機制**  
   - 當 Q-Learning 無法找到從起點到終點的路徑時，在網頁上顯示「無法到達終點」的錯誤訊息。
   - 後端通過一個 `reachable` 變數來判斷是否可達，並在前端依據其值顯示提示。

4. **除錯過程**  
   - Q-Learning 部分可能因為某些 episode 永遠無法終止而卡住，導致後續 `print()` 語句無法輸出。
   - 為防止無限迴圈，建議在每個 episode 中加入最大步數限制。

---

## 2. 互動過程與修改詳情

### 2.1 初始版本實作
- 實作了基本的 Flask 程式，包含：
  - 前端使用 HTML/JavaScript 生成網格及設定起點、終點和障礙物。
  - 後端使用 Q-Learning 算法進行訓練，返回最佳策略、Q-value 與最佳路徑，並以動畫形式展示。

### 2.2 分離顯示區塊 (Policy 與 Q-value)
- **修改重點**：
  - 在前端添加兩個獨立的表格，分別顯示每個網格的方向箭頭（最佳策略）和 Q-value。
  - 移除了原本在網格上直接標示箭頭和 Q-value 的代碼，使得主網格僅保留路徑動畫。

### 2.3 新增 Reset 按鈕與重新顯示邏輯
- **修改重點**：
  - 新增 Reset 按鈕，點擊後執行 `resetAll()`，清空網格、結果區並重置全局變數。
  - 在「開始 Q-Learning」前也會清除前一次操作殘留的動畫與結果，確保每次顯示全新結果。

### 2.4 新增錯誤提示機制 (無法到達終點)
- **修改重點**：
  - 後端在進行路徑搜尋時，使用一個 `reachable` 變數。只有當 `current == goalState` 時，設置 `reachable = True`；否則保持為 `False`。
  - 回傳 JSON 時包含 `reachable` 欄位。
  - 前端在接收到結果後檢查 `reachable`，若為 `False` 則在結果區顯示「無法到達終點」訊息，並不執行路徑高亮動畫。

### 2.5 除錯與 Q-Learning 迴圈無限迴圈問題
- **問題描述**：
  - 若某些 episode 無法到達終點，while 迴圈可能無限執行，導致後續的 `print()` 無法輸出。
  
- **修改方案**：
  1. **加入最大步數限制**：  
     在每個 episode 中加入步數計數器，若步數達到設定上限（如 `max_steps = 100`）則強制中斷該 episode，避免無限迴圈。
     
     ```python
     max_steps = 100  # 每個 episode 的最大步數限制
     for _ in range(episodes):
         state = startState
         done = False
         steps = 0
         while not done and steps < max_steps:
             # epsilon-greedy 策略
             if random.random() < epsilon:
                 action = random.choice(actions)
             else:
                 qvals = Q[state]
                 maxQ = max(qvals.values())
                 best_actions = [a for a, v in qvals.items() if v == maxQ]
                 action = random.choice(best_actions)
     
             next_state, reward, done = step(state, action)
     
             old_value = Q[state][action]
             max_next = max(Q[next_state].values()) if next_state in Q else 0.0
             Q[state][action] = old_value + alpha * (reward + gamma * max_next - old_value)
     
             state = next_state
             steps += 1
             print(f"[DEBUG] steps: {steps}, current: {state}", flush=True)
         if steps >= max_steps:
             print("[DEBUG] Episode terminated due to reaching max_steps", flush=True)
     print("4train() was called!", flush=True)
     ```
  
  2. **在各個可能 `break` 前加入 debug 輸出**：  
     這有助於確定程式在哪個分支提前中斷：
     
     ```python
     while True:
         path.append(idx_map[current])
         print(f"[DEBUG] current={current}, reachable={reachable}", flush=True)
         if current == goalState:
             reachable = True
             print(f"[DEBUG] 到達終點，reachable={reachable}", flush=True)
             break
         if current in visited:
             print("[DEBUG] 發現迴圈 (current in visited)，跳出", flush=True)
             break
         visited.add(current)
     
         idx = idx_map[current]
         if idx not in policy:
             print("[DEBUG] idx not in policy，跳出", flush=True)
             break
     
         action = policy[idx]
         (r, c) = current
         if action == 'U': r -= 1
         elif action == 'D': r += 1
         elif action == 'L': c -= 1
         elif action == 'R': c += 1
     
         if not is_valid(r, c):
             print("[DEBUG] next step invalid，跳出", flush=True)
             break
         current = (r, c)
     
     print(f"[DEBUG] 迴圈結束, final reachable={reachable}", flush=True)
     ```
  
- **最終觀察**：  
  若 Q-Learning 迴圈中的 episode 無法正確結束，則後續的 print 無法被呼叫。加入步數上限後可以避免無限迴圈，確保每次 episode 都能在合理步數內結束。

---

## 3. 總結與建議

- **需求滿足情況**：  
  - 網格生成、起點/終點與障礙物設定功能正常。
  - 箭頭與 Q-value 分別顯示在兩個獨立表格中。
  - Reset 按鈕能正確清除所有內容並重置狀態。
  - 當路徑完全封死時，後端會返回 `reachable=False`，前端依據此狀態顯示「無法到達終點」的錯誤提示。

- **除錯重點**：  
  - 確認後端 `train()` 是否真的被呼叫，並檢查是否有無限迴圈的問題。
  - 加入最大步數限制以避免單一 episode 永遠無法結束。
  - 利用 debug print 輸出在各個 break 前的狀態，有助於分析流程中斷的原因。
  - 檢查前端 CSS（例如 z-index）確保錯誤訊息不會被其他圖層遮擋。

- **部署建議**：  
  - 在開發模式下使用 `app.run(debug=True)`，以便觀察終端日誌。
  - 測試時確保瀏覽器沒有使用快取，必要時使用無痕模式。

---
## 4.成果展示



https://github.com/user-attachments/assets/d9e1abc9-dff9-48fd-b03c-8993f39234d5

