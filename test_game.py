# Engine.py imports - pygame, sys, random, noise, time
from ast import Str
import py
from sympy import python
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
game_map_id = 'Maps/map.txt'
font = pygame.font.SysFont("monospace", 8, True)
ui_images = {'coin': pygame.image.load('Collectables/coin_red.png')}

# Caption, display and surface
pygame.display.set_caption('Blob\'s Adventure')
screen = pygame.display.set_mode(window_size, 0, 32)
display = pygame.Surface(surface_size)

# Images
background_image = pygame.image.load('background.png').convert()

# Player instance
player = Player('Player_animations/idle/idle_0.png', [10 * tile_size, 9 * tile_size - 32], animation_file_id = "Player_animations/Animation_file.txt")
player.action = 'idle'

# Pet instance
pet = Pet('blob.png', [10 * tile_size, 9 * tile_size - 16])

# Create coins
coins = [Coin('Collectables/coin_red.png', [10 * tile_size - 15, 9 * tile_size - 35])]

# Create songs
songs = [Song('Collectables/1_song.png', [10 * tile_size - 15, 9 * tile_size - 85], name = '1_song'),
Song('Collectables/2_song.png', [10 * tile_size - 31, 9 * tile_size - 85], name = '2_song'),
Song('Collectables/3_song.png', [10 * tile_size + 1, 9 * tile_size - 85], name = '3_song')]

# Collectables
collectables = coins + songs

# Level instance
level = Level(player, tile_size, game_map_id = game_map_id, background_id = 'Background/Background_file.txt', collectables = collectables)

# Game instance
game = Game([level], 'Tiles/tile_ids_file.txt', music_file = 'Music/Music_file.txt', ui_file = 'UI/UI_file.txt', songs_collected = {'1_song': False, '2_song': False, '3_song': False})
game.get_tile_indexs()
level.tile_indexs = game.tile_indexs.copy()

# Game loop
while True:
    # Adjust scroll, to make "camera" follow the player with a slight lag
    true_scroll[0] += (player.rect.x - true_scroll[0] - 160)/10
    true_scroll[1] += (player.rect.y - true_scroll[1] - 110)/10
    scroll = true_scroll.copy() # Integer copy of true_scroll, to make
    scroll[0] = int(scroll[0])  # ground movenment avoid bugs.
    scroll[1] = int(scroll[1])

    # Update scroll based on screen shake
    if game.screen_shake_counter:
        shake = game.screen_shake()
        scroll[0] += shake[0]
        scroll[1] += shake[1]

    # Render background and collectables (plus, check for collision with player)
    level.render_background(display, scroll)
    coins_collected, song_collected = level.render_collectables(display, scroll, player.rect)
    game.coins_collected += coins_collected
    if song_collected:
        game.songs_collected[song_collected] = True
        game.songs_count += 1

    # Move player and get collision types dict
    tile_rects = level.render_map(display, ['{}'.format(i) for i in range(1,17)], scroll)
    player.move(tile_rects)

    # Move pet
    if abs(player.rect.y - pet.rect.y) < 32:
        if (player.rect.x - pet.rect.x) > 16:
            pet.moving_right = True
        elif (pet.rect.x - player.rect.x) > 16:
            pet.moving_left = True
        elif abs(player.rect.x - pet.rect.x) < 32:
            pet.moving_left = False
            pet.moving_right = False
    pet.move(tile_rects)

    # Render player
    player.render(display, scroll)

    # Render pet
    pet.render(display, scroll)

    # Render UI
    game.render_ui(display, font)

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
            if event.key == K_e:
                game.screen_shake_counter = 15
            if event.key == K_q:
                if game.song_ui_key_pressed:
                    game.song_ui_key_pressed = False
                else:
                    game.song_ui_key_pressed = True
            if event.key == K_1:
                game.song_ui_selected = 0
            if event.key == K_2:
                game.song_ui_selected = 1
            if event.key == K_3:
                game.song_ui_selected = 2
            if event.key == K_SPACE:
                game.song_ui_key_pressed = False
                game.song_ui_height = 200
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