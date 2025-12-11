import socket, threading, pygame, os, sys, json, uuid

from tetris_core import Game, Config, Board


def load_config():
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_file_path = os.path.join(base_path, "config.json")
    with open(config_file_path, "r", encoding="utf-8") as f:
        return json.load(f)

class NetworkGame(Game):
    def __init__(self, sock, player_id, player_name, screen):
        super().__init__()
        self.sock = sock
        self.player_id = player_id
        self.player_name = player_name
        self.screen = screen
        self.opponents = {}
        threading.Thread(target=self.receive, daemon=True).start()

    def send_state(self, garbage=0):
        state = {
            "id": self.player_id,
            "name": self.player_name,
            "locked": list(self.board.locked.items()),
            "score": self.score,
            "piece": self.current_piece.shape,
            "garbage": garbage
        }
        self.sock.sendall(json.dumps(state).encode())

    def receive(self):
        while True:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break

                state = json.loads(data.decode())
                sender_id = state.get("id")

                if sender_id != self.player_id and state.get("garbage", 0) > 0:
                    self.board.add_garbage_lines(state["garbage"])

                locked_list = state.get("locked", [])
                locked_dict = {
                    (pos[0], pos[1]): tuple(color)
                    for pos, color in locked_list
                }

                self.opponents[sender_id] = {
                    "name": state.get("name", ""),
                    "score": state.get("score", 0),
                    "locked": locked_dict,
                    "piece": state.get("piece"),
                    "garbage": state.get("garbage", 0)
                }

            except Exception as e:
                print("Receive error:", e)
                break

    def update(self):
        if self.board.valid_space(self.current_piece, dy=1):
            self.current_piece.y += 1
        else:
            self.board.lock_piece(self.current_piece)
            lines = self.board.clear_lines()
            self.score += lines * 100
            garbage = max(0, lines - 1)
            self.spawn_piece()
            self.send_state(garbage)

    def draw(self):
        self.screen.fill((0, 0, 0))

        grid = self.board.create_grid()
        self.renderer.draw_grid(grid)

        self.renderer.draw_player_info(self.player_name, self.score)

        if not self.game_over:
            ghost_cells = self.get_ghost_cells()
            self.renderer.draw_ghost_piece(self.current_piece, ghost_cells)
            self.renderer.draw_piece(self.current_piece)
            self.renderer.draw_next_piece(self.next_piece)
            self.renderer.draw_hold_piece(self.hold_piece)

        screen_width, screen_height = self.screen.get_size()
        Config.update_window_size(screen_width, screen_height)

        if len(self.opponents) > 0:
            opponents_list = list(self.opponents.items())
            half = len(opponents_list) // 2
            left_players = opponents_list[:half]
            right_players = opponents_list[half:]

            scale = 0.3
            block = int(Config.BLOCK_SIZE * scale)
            slot_w = block * Config.COLS
            slot_h = block * Config.ROWS
            margin = 10

            center_x = (Config.WIDTH - Config.PLAY_W) // 2
            center_y = (Config.HEIGHT - Config.PLAY_H) // 2

            for i, (pid, opp) in enumerate(left_players):
                slot_x = center_x - slot_w - 50
                slot_y = center_y + i * (slot_h + margin)
                opp_grid = Board(opp["locked"]).create_grid()
                self.renderer.draw_opponent_grid(opp_grid, slot_x, slot_y, scale)
                self.renderer.draw_opponent_info(
                    opp["name"], opp["score"], slot_x, slot_y
                )

            for i, (pid, opp) in enumerate(right_players):
                slot_x = center_x + Config.PLAY_W + 50
                slot_y = center_y + i * (slot_h + margin)
                opp_grid = Board(opp["locked"]).create_grid()
                self.renderer.draw_opponent_grid(opp_grid, slot_x, slot_y, scale)
                self.renderer.draw_opponent_info(
                    opp["name"], opp["score"], slot_x, slot_y
                )

        pygame.display.flip()

def get_player_name(screen):
    font = pygame.font.SysFont("consolas", 30)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ""
    clock = pygame.time.Clock()

    while True:
        screen_width, screen_height = screen.get_size()
        input_box = pygame.Rect(screen_width//2 - 100, screen_height//2 - 20, 200, 40)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                Config.update_window_size(event.w, event.h)
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_box.collidepoint(event.pos)
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_RETURN:
                    return text if text.strip() else "Player"
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        screen.fill((0,0,0))
        txt_surface = font.render(text, True, color)
        input_box.w = max(200, txt_surface.get_width()+10)
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(screen, color, input_box, 2)
        prompt = font.render("Enter your name:", True, (255,255,255))
        screen.blit(prompt, (screen_width//2 - 120, screen_height//2 - 70))
        pygame.display.flip()
        clock.tick(30)

def main():
    pygame.init()
    config = load_config()
    host = config["HOST"]
    port = config["PORT"]
    room = config["ROOM"]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(room.encode())

    info = pygame.display.Info()
    screen_width, screen_height = info.current_w, info.current_h
    screen = pygame.display.set_mode((screen_width / 1.5, screen_height / 1.5), pygame.RESIZABLE)
    Config.update_window_size(screen_width / 1.5, screen_height / 1.5)

    player_id = str(uuid.uuid4())
    player_name = get_player_name(screen)

    game = NetworkGame(sock, player_id, player_name, screen)
    fall_time = 0
    fall_speed = 0.8

    while True:
        dt = game.clock.tick(60)/1000
        fall_time += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.VIDEORESIZE:
                Config.update_window_size(event.w, event.h)
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                game.screen = screen
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                game.handle_input(event)

        if fall_time >= fall_speed and not game.game_over:
            fall_time = 0
            game.update()
        game.draw()

if __name__ == "__main__":
    main()