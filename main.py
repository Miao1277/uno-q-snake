import time
import random
import socket
from arduino.app_utils import App, Bridge

WIDTH = 13
HEIGHT = 8

def safe_bridge_call(func_name, *args):
    try:
        Bridge.call(func_name, *args)
    except Exception:
        pass

def sync_led_matrix(snake, food):
    bits = []
    snake_set = set(snake)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if (x, y) in snake_set or (x, y) == food:
                bits.append("1")
            else:
                bits.append("0")
    safe_bridge_call("updateMatrix", "".join(bits))

def spawn_food(snake):
    while True:
        pos = (random.randint(0, WIDTH - 1), random.randint(0, HEIGHT - 1))
        if pos not in snake:
            return pos

def render_board(snake, food, score, high_score, interval):
    lines = [
        "\033[H",
        "=== UNO Q DUAL-CORE SNAKE ===\r\n",
        f"Score: {score} | High: {high_score} | {round(1/interval, 1)} steps/s   \r\n",
        "+" + "--" * WIDTH + "+\r\n"
    ]
    snake_set = set(snake[1:])
    head = snake[0]
    for y in range(HEIGHT):
        row = ["|"]
        for x in range(WIDTH):
            if (x, y) == head:
                row.append("@@")
            elif (x, y) == food:
                row.append("<>")
            elif (x, y) in snake_set:
                row.append("[]")
            else:
                row.append("  ")
        row.append("|\r\n")
        lines.append("".join(row))
    lines.append("+" + "--" * WIDTH + "+\r\n")
    lines.append("Controls: [W][A][S][D] Move | [Q] Quit\r\n")
    return "".join(lines).encode()

def handle_client(conn):
    conn.setblocking(False)
    high_score = 0
    try:
        while True:
            # 1. 開始畫面
            start_msg = (
                "\033[2J\033[H\033[?25l"
                "=========================================\r\n"
                "   UNO Q LED-MATRIX + TERMINAL SNAKE     \r\n"
                "=========================================\r\n"
                "  Dual-Core: Linux MPU + STM32 MCU       \r\n"
                "  Display  : 13x8 LED Matrix & Terminal  \r\n"
                "-----------------------------------------\r\n"
                "  Press [SPACE] to Start or [Q] to Quit  \r\n"
                "=========================================\r\n"
            )
            conn.sendall(start_msg.encode())

            while True:
                try:
                    data = conn.recv(16)
                    if not data:
                        return
                    if b' ' in data:
                        break
                    if b'q' in data or b'Q' in data:
                        return
                except BlockingIOError:
                    pass
                time.sleep(0.05)

            # 2. 初始化新局
            snake = [(WIDTH // 2 - i, HEIGHT // 2) for i in range(3)]
            direction = (1, 0)
            next_dir = (1, 0)
            food = spawn_food(snake)
            score = 0
            interval = 0.28
            safe_bridge_call("onGameStart")
            sync_led_matrix(snake, food)
            conn.sendall(b"\033[2J")
            last_move = time.time()

            # 3. 遊戲主迴圈
            while True:
                try:
                    data = conn.recv(16)
                    if not data:
                        return
                    for b in data:
                        c = chr(b).lower()
                        if c == 'w' and direction != (0, 1):
                            next_dir = (0, -1)
                        elif c == 's' and direction != (0, -1):
                            next_dir = (0, 1)
                        elif c == 'a' and direction != (1, 0):
                            next_dir = (-1, 0)
                        elif c == 'd' and direction != (-1, 0):
                            next_dir = (1, 0)
                        elif c == 'q':
                            return
                except BlockingIOError:
                    pass

                if time.time() - last_move >= interval:
                    last_move = time.time()
                    direction = next_dir
                    new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

                    if (new_head[0] < 0 or new_head[0] >= WIDTH or
                        new_head[1] < 0 or new_head[1] >= HEIGHT or
                        new_head in snake):
                        safe_bridge_call("onGameOver")
                        break

                    snake.insert(0, new_head)
                    if new_head == food:
                        score += 10
                        if score > high_score:
                            high_score = score
                        interval = max(0.10, interval - 0.01)
                        safe_bridge_call("onEatFood")
                        food = spawn_food(snake)
                    else:
                        snake.pop()

                    conn.sendall(render_board(snake, food, score, high_score, interval))
                    sync_led_matrix(snake, food)
                time.sleep(0.01)

            # 4. Game Over 畫面
            over_msg = (
                "\033[2J\033[H\r\n\r\n"
                "  #####################################  \r\n"
                "  #             GAME OVER             #  \r\n"
                "  #####################################  \r\n"
                f"    Final Score : {score}                     \r\n"
                f"    High Score  : {high_score}                     \r\n"
                "  -------------------------------------  \r\n"
                "   Press [SPACE] to Replay or [Q] Quit   \r\n"
                "  #####################################  \r\n"
            )
            conn.sendall(over_msg.encode())

            while True:
                try:
                    data = conn.recv(16)
                    if not data:
                        return
                    if b' ' in data:
                        break
                    if b'q' in data or b'Q' in data:
                        return
                except BlockingIOError:
                    pass
                time.sleep(0.05)
    except Exception:
        pass
    finally:
        try:
            conn.sendall(b"\033[?25h\r\n")
            conn.close()
        except Exception:
            pass

def run_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 8899))
    srv.listen(1)
    print("Snake server ready on port 8899!")
    while True:
        conn, _ = srv.accept()
        handle_client(conn)

def loop():
    run_server()

App.run(user_loop=loop)
