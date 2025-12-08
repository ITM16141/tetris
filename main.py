from tetris_core import Game
import pygame, sys

def main():
    game = Game()
    fall_time = 0
    fall_speed = 0.8
    while True:
        dt = game.clock.tick(60)/1000
        fall_time += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                game.handle_input(event)
        if fall_time >= fall_speed and not game.game_over:
            fall_time = 0
            game.update()
        game.draw()

if __name__ == "__main__":
    main()