from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/train', methods=['POST'])
def train():
    """
    接收前端網格資訊並執行 Q Learning，
    最後回傳:
      - policy: dict, 格子 -> 最優動作
      - qValues: dict, 格子 -> Q-value
      - path: list, 依照最優策略由起點到終點的路徑(以index表現)
      - reachable: bool, 是否成功抵達終點
    """
    data = request.get_json()
    gridSize = data['gridSize']
    startPos = data['startPos']
    goalPos = data['goalPos']
    obstacles = data['obstacles']

    # 將障礙物轉為 (row, col) 集合
    obstacle_set = set((o['row'], o['col']) for o in obstacles)

    actions = ['U', 'D', 'L', 'R']
    Q = {}
    for r in range(gridSize):
        for c in range(gridSize):
            if (r, c) not in obstacle_set:
                Q[(r, c)] = {a: 0.0 for a in actions}

    alpha = 0.1
    gamma = 0.9
    epsilon = 0.2
    episodes = 1000

    startState = (startPos['row'], startPos['col'])
    goalState = (goalPos['row'], goalPos['col'])
    def is_valid(r, c):
        return 0 <= r < gridSize and 0 <= c < gridSize and (r, c) not in obstacle_set

    def step(state, action):
        if state == goalState:
            return state, 0.0, True

        (r, c) = state
        if action == 'U': r -= 1
        elif action == 'D': r += 1
        elif action == 'L': c -= 1
        elif action == 'R': c += 1

        # 撞牆或障礙物：留在原地，獎勵 -1
        if not is_valid(r, c):
            return (state), -1.0, False
        # 抵達終點：+1
        if (r, c) == goalState:
            return (r, c), 1.0, True
        # 一般移動：0
        return (r, c), 0.0, False
    # Q-Learning
    max_steps = 100  # 可以根據實際需求調整
    for _ in range(episodes):
        state = startState
        done = False
        steps = 0
        while not done and steps < max_steps:
            # epsilon-greedy
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
            steps += 1  # 增加步數計數
        if steps >= max_steps:
            print("Episode terminated due to max_steps reached.")
    # 轉換為 policy、qValues
    policy = {}
    qValues = {}
    idx_map = {}
    idx_counter = 1
    for r in range(gridSize):
        for c in range(gridSize):
            idx_map[(r, c)] = idx_counter
            idx_counter += 1
    for (r, c), action_dict in Q.items():
        idx = idx_map[(r, c)]
        # goal 狀態不需要動作
        if (r, c) == goalState:
            qValues[idx] = 0.0
            continue
        best_a = max(action_dict, key=action_dict.get)  # 取Q值最高的動作
        policy[idx] = best_a
        qValues[idx] = action_dict[best_a]
    # 找出從起點到終點的路徑
    path = []
    visited = set()
    current = startState
    reachable = False

    while True:
        path.append(idx_map[current])
        if current == goalState:
            reachable = True
            break
        if current in visited:
            break
        visited.add(current)

        idx = idx_map[current]
        if idx not in policy:
            break

        action = policy[idx]
        (r, c) = current
        if action == 'U': r -= 1
        elif action == 'D': r += 1
        elif action == 'L': c -= 1
        elif action == 'R': c += 1

        if not is_valid(r, c):
            break
        current = (r, c)

    print(f"迴圈結束，最終 reachable = {reachable}")
    resp = {
        "policy": policy,
        "qValues": qValues,
        "path": path,
        "reachable": reachable
    }
    return jsonify(resp)

if __name__ == '__main__':
    app.run(debug=True)
