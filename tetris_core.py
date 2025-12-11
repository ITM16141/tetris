import pygame
import random

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.board = Board()
        self.renderer = Renderer(self.screen)
        self.current_piece = Piece(random.choice(list(Config.SHAPES.keys())))
        self.next_piece = Piece(random.choice(list(Config.SHAPES.keys())))
        self.hold_piece = None
        self.can_hold = True
        self.score = 0
        self.game_over = False

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = Piece(random.choice(list(Config.SHAPES.keys())))
        self.can_hold = True
        if not self.board.valid_space(self.current_piece):
            self.game_over = True

    def hold(self):
        if not self.can_hold: return
        if self.hold_piece is None:
            self.hold_piece = Piece(self.current_piece.shape)
            self.spawn_piece()
        else:
            self.current_piece, self.hold_piece = Piece(self.hold_piece.shape), Piece(self.current_piece.shape)
            self.current_piece.x = Config.COLS//2 - 2
            self.current_piece.y = 0
        self.can_hold = False

    def get_ghost_cells(self):
        ghost_y = self.current_piece.y
        while self.board.valid_space(self.current_piece, dy=(ghost_y - self.current_piece.y + 1)):
            ghost_y += 1
        return [(x, y + (ghost_y - self.current_piece.y)) for x,y in self.current_piece.cells()]

    def handle_input(self, event):
        if event.key == pygame.K_LEFT and self.board.valid_space(self.current_piece, dx=-1):
            self.current_piece.x -= 1
        elif event.key == pygame.K_RIGHT and self.board.valid_space(self.current_piece, dx=1):
            self.current_piece.x += 1
        elif event.key == pygame.K_DOWN and self.board.valid_space(self.current_piece, dy=1):
            while self.board.valid_space(self.current_piece, dy=1):
                self.current_piece.y += 1
                self.score += 2
        elif event.key == pygame.K_UP:
            new_rot = (self.current_piece.rotation+1)%4
            if self.board.valid_space(self.current_piece, rotation=new_rot):
                self.current_piece.rotation = new_rot
        elif event.key == pygame.K_c:
            self.hold()

    def update(self):
        if self.board.valid_space(self.current_piece, dy=1):
            self.current_piece.y += 1
        else:
            self.board.lock_piece(self.current_piece)
            lines = self.board.clear_lines()
            self.score += lines * 100
            self.spawn_piece()

    def draw(self):
        self.screen.fill((0,0,0))
        grid = self.board.create_grid()
        self.renderer.draw_grid(grid)
        if not self.game_over:
            ghost_cells = self.get_ghost_cells()
            self.renderer.draw_ghost_piece(self.current_piece, ghost_cells)
            self.renderer.draw_piece(self.current_piece)
            self.renderer.draw_next_piece(self.next_piece)
            self.renderer.draw_hold_piece(self.hold_piece)
        pygame.display.flip()

class Renderer:
    def __init__(self, screen):
        self.screen = screen

    def draw_grid(self, grid):
        for y in range(Config.ROWS):
            for x in range(Config.COLS):
                pygame.draw.rect(
                    self.screen,
                    grid[y][x],
                    ((Config.WIDTH - Config.PLAY_W) // 2 + x * Config.BLOCK_SIZE,
                     (Config.HEIGHT - Config.PLAY_H) // 2 + y * Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    [i / 1.25 for i in grid[y][x]],
                    ((Config.WIDTH - Config.PLAY_W) // 2 + x * Config.BLOCK_SIZE,
                     (Config.HEIGHT - Config.PLAY_H) // 2 + y * Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE),
                    1
                )

        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            ((Config.WIDTH - Config.PLAY_W) // 2 - 3,
             (Config.HEIGHT - Config.PLAY_H) // 2 - 3,
             Config.PLAY_W + 6,
             Config.PLAY_H + 6),
            3
        )

    def draw_piece(self, piece):
        for (x, y) in piece.cells():
            if y >= 0:
                pygame.draw.rect(
                    self.screen,
                    piece.color,
                    (
                        (Config.WIDTH - Config.PLAY_W) // 2 + x * Config.BLOCK_SIZE,
                        (Config.HEIGHT - Config.PLAY_H) // 2 + y * Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE
                    )
                )
                pygame.draw.rect(
                    self.screen,
                    [i / 1.25 for i in piece.color],
                    ((Config.WIDTH - Config.PLAY_W) // 2 + x * Config.BLOCK_SIZE,
                     (Config.HEIGHT - Config.PLAY_H) // 2 + y * Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE,
                     Config.BLOCK_SIZE),
                    1
                )

    def draw_ghost_piece(self, piece, ghost_cells):
        for (x, y) in ghost_cells:
            rect = pygame.Rect(
                (Config.WIDTH - Config.PLAY_W)//2 + x * Config.BLOCK_SIZE,
                (Config.HEIGHT - Config.PLAY_H)//2 + y * Config.BLOCK_SIZE,
                Config.BLOCK_SIZE,
                Config.BLOCK_SIZE
            )
            pygame.draw.rect(self.screen, piece.color, rect, 1)

    def draw_next_piece(self, next_piece):
        font = pygame.font.SysFont("consolas", 20)
        label = font.render("Next:", True, (255, 255, 255))
        self.screen.blit(label, (Config.WIDTH - 150, 50))
        if next_piece:
            for (x, y) in next_piece.cells():
                pygame.draw.rect(
                    self.screen,
                    next_piece.color,
                    (
                        Config.WIDTH - 150 + x * Config.BLOCK_SIZE,
                        80 + y * Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE
                    ),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    [i / 1.25 for i in next_piece.color],
                    (
                        Config.WIDTH - 150 + x * Config.BLOCK_SIZE,
                        80 + y * Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE
                    ),
                    1
                )

    def draw_hold_piece(self, hold_piece):
        font = pygame.font.SysFont("consolas", 20)
        label = font.render("Hold:", True, (255, 255, 255))
        self.screen.blit(label, (50, 50))
        if hold_piece:
            for (x, y) in hold_piece.cells():
                pygame.draw.rect(
                    self.screen,
                    hold_piece.color,
                    (
                        50 + x * Config.BLOCK_SIZE,
                        80 + y * Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE
                    ),
                    0
                )
                pygame.draw.rect(
                    self.screen,
                    [i / 1.25 for i in hold_piece.color],
                    (
                        50 + x * Config.BLOCK_SIZE,
                        80 + y * Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE,
                        Config.BLOCK_SIZE
                    ),
                    1
                )

    def draw_opponent_grid(self, grid, x, y, scale=0.3):
        block = int(Config.BLOCK_SIZE * scale)
        for row in range(Config.ROWS):
            for col in range(Config.COLS):
                pygame.draw.rect(
                    self.screen,
                    grid[row][col],
                    (x + col * block, y + row * block, block, block),
                    0
                )
        pygame.draw.rect(
            self.screen,
            (200, 200, 200),
            (x, y, Config.COLS * block, Config.ROWS * block),
            2
        )

    def draw_opponent_info(self, name, score, x, y):
        font = pygame.font.SysFont("consolas", 18)
        text = font.render(f"{name} ({score})", True, (255, 255, 255))
        self.screen.blit(text, (x, y - 22))

class Board:
    def __init__(self, locked=None):
        if locked is None:
            locked = {}
        self.locked = locked

    def create_grid(self):
        grid = [[(0, 0, 0) for _ in range(Config.COLS)] for _ in range(Config.ROWS)]
        for y in range(Config.ROWS):
            for x in range(Config.COLS):
                if (x, y) in self.locked:
                    grid[y][x] = self.locked[(x, y)]
        return grid

    def valid_space(self, piece, rotation=None, dx=0, dy=0):
        for x,y in piece.cells(rotation, dx, dy):
            if x < 0 or x >= Config.COLS or y >= Config.ROWS:
                return False
            if y >= 0 and self.locked.get((x,y)):
                return False
        return True

    def lock_piece(self, piece):
        for x,y in piece.cells():
            if y >= 0:
                self.locked[(x,y)] = piece.color

    def clear_lines(self):
        lines = 0
        for y in range(Config.ROWS):
            if all((x,y) in self.locked for x in range(Config.COLS)):
                for x in range(Config.COLS):
                    del self.locked[(x,y)]
                for (x2,y2) in sorted(list(self.locked.keys()), key=lambda p:p[1], reverse=True):
                    if y2 < y:
                        self.locked[(x2,y2+1)] = self.locked.pop((x2,y2))
                lines += 1
        return lines

    def add_garbage_lines(self, count):
        for _ in range(count):
            for (x, y) in sorted(list(self.locked.keys()), key=lambda p: p[1]):
                if y > 0:
                    self.locked[(x, y - 1)] = self.locked.pop((x, y))
            hole = random.randint(0, Config.COLS - 1)
            for x in range(Config.COLS):
                if x != hole:
                    self.locked[(x, Config.ROWS - 1)] = (100, 100, 100)

class Piece:
    def __init__(self, shape):
        self.shape = shape
        self.rotation = 0
        self.color = Config.COLORS[shape]
        self.x = Config.COLS // 2 - 2
        self.y = 0

    def cells(self, rotation = None, dx = 0, dy = 0):
        rot = self.rotation if rotation is None else rotation
        return [(self.x + cx + dx, self.y + cy + dy)
                for cx, cy in Config.SHAPES[self.shape][rot]]

class Config:
    BLOCK_SIZE = 20

    COLS, ROWS = 10, 20
    PLAY_W, PLAY_H = COLS * BLOCK_SIZE, ROWS * BLOCK_SIZE

    TOP_LEFT_Y = 80

    WIDTH, HEIGHT = 800, 600

    @classmethod
    def update_window_size(cls, width, height):
        cls.WIDTH, cls.HEIGHT = width, height

    @classmethod
    def update_block_size(cls, block_size):
        cls.BLOCK_SIZE = block_size
        cls.PLAY_W = cls.COLS * cls.BLOCK_SIZE
        cls.PLAY_H = cls.ROWS * cls.BLOCK_SIZE

    COLORS = {
        'I': (0, 240, 240),
        'O': (240, 240, 0),
        'T': (160, 0, 240),
        'S': (0, 240, 0),
        'Z': (240, 0, 0),
        'J': (0, 0, 240),
        'L': (240, 160, 0)
    }

    SHAPES = {
        'I': [[(0, 1), (1, 1), (2, 1), (3, 1)], [(2, 0), (2, 1), (2, 2), (2, 3)],
              [(0, 2), (1, 2), (2, 2), (3, 2)], [(1, 0), (1, 1), (1, 2), (1, 3)]],
        'O': [[(1, 0), (2, 0), (1, 1), (2, 1)]] * 4,
        'T': [[(1, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (2, 1), (1, 2)],
              [(0, 1), (1, 1), (2, 1), (1, 2)], [(1, 0), (0, 1), (1, 1), (1, 2)]],
        'S': [[(1, 0), (2, 0), (0, 1), (1, 1)], [(1, 0), (1, 1), (2, 1), (2, 2)],
              [(1, 1), (2, 1), (0, 2), (1, 2)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
        'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)], [(2, 0), (1, 1), (2, 1), (1, 2)],
              [(0, 1), (1, 1), (1, 2), (2, 2)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
        'J': [[(0, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (2, 0), (1, 1), (1, 2)],
              [(0, 1), (1, 1), (2, 1), (2, 2)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
        'L': [[(2, 0), (0, 1), (1, 1), (2, 1)], [(1, 0), (1, 1), (1, 2), (2, 2)],
              [(0, 1), (1, 1), (2, 1), (0, 2)], [(0, 0), (1, 0), (1, 1), (1, 2)]]
    }
