# Engine.py imports - pygame, sys, random, noise, time
from Engine import *

# Imports and Clock
clock = pygame.time.Clock()
from pygame.locals import *

# Prepare mixer for sounds
pygame.mixer.pre_init(44100, 16, 2, 512)

# Initialize pygame
pygame.init()

# Variabels
window_size = (600, 400)
surface_size = (300, 200)
tile_size = 16
last_time = time.time()
framerate = 60
true_scroll = [0, 0]
game_map_id = 'Maps/map'

# Caption, display and surface
pygame.display.set_caption('Blob\'s Adventure')
screen = pygame.display.set_mode(window_size, 0, 32)
display = pygame.Surface(surface_size)

# Images
background_image = pygame.image.load('background.png').convert()

# Player instance
player = Player('Player_animations/idle/idle_0', [10 * tile_size, 9 * tile_size - 35], animation_file_id = "Player_animations/Animation_file.txt")
player.action = 'idle'

# Level instance
level = Level(player, game_map_id, tile_size)
level.load_map()

# Game instance
game = Game([level], 'Tiles/tile_ids_file.txt', music_file = 'Music/Music_file.txt')
game.get_tile_indexs()
level.tile_indexs = game.tile_indexs.copy()

# Game loop
while True:
    # Fill screen for reset effect
    display.blit(background_image, (0, 0))

    # Adjust scroll, to make "camera" follow the player with a slight lag
    true_scroll[0] += (player.rect.x - true_scroll[0] - 160)/10
    true_scroll[1] += (player.rect.y - true_scroll[1] - 110)/10
    scroll = true_scroll.copy() # Integer copy of true_scroll, to make
    scroll[0] = int(scroll[0])  # ground movenment avoid bugs.
    scroll[1] = int(scroll[1])

    # Move player and get collision types dict
    tile_rects = level.render_map(display, ['{}'.format(i) for i in range(1,15)], scroll)
    player.move(tile_rects)

    # Render player
    player.render(display, scroll)

    # Event loop
    for event in pygame.event.get():
        if event.type == QUIT: # Exit event
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_RIGHT:
                player.moving_right = True
            if event.key == K_LEFT:
                player.moving_left = True
            if event.key == K_UP and player.air_timer < 6:
                player.y_momentum = -5
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                player.moving_right = False
            if event.key == K_LEFT:
                player.moving_left = False

    # Scale display size to match window size
    screen.blit(pygame.transform.scale(display, window_size), (0, 0))

    # Update display at 60 frames per second
    pygame.display.update()
    clock.tick(framerate)