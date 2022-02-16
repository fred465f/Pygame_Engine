# Engine.py imports - pygame, sys, random, noise, time
from ast import Str
from re import L
from tkinter.messagebox import NO
import py
from sympy import N, python
from Engine import *

# Imports and Clock
clock = pygame.time.Clock()
from pygame.locals import *

# Prepare mixer for sounds
pygame.mixer.pre_init(44100, 16, 2, 512)

# Initialize pygame
pygame.init()

# Variabels
window_size = (900, 600)
surface_size = (300, 200)
tile_size = 16
last_time = time.time()
framerate = 60
true_scroll = [0, 0]
game_map_id = 'Maps/map.txt'
font = pygame.font.SysFont("monospace", 8, True)
ui_images = {'coin': pygame.image.load('Collectables/coin_red.png')}
ui_outline_col = (71, 71, 71)
song_timer = 0
play = False
current_song = None
fadout = 1000
particle_color = (175, 75, 75)
shake_timer = 0
particle_amount = 10

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
songs = [Song('Collectables/1_song.png', [11 * tile_size, -2 * tile_size], name = '1_song'),
Song('Collectables/2_song.png', [10 * tile_size - 31, 9 * tile_size - 85], name = '2_song'),
Song('Collectables/3_song.png', [10 * tile_size + 1, 9 * tile_size - 85], name = '3_song')]

# Collectables
collectables = coins

# Level instance
level = Level(player, tile_size, game_map_id = game_map_id, background_id = 'Background/Background_file.txt', collectables = collectables)

# Game instance
game = Game([level], 'Tiles/tile_ids_file.txt', music_file = 'Music/Music_file.txt', ui_file = 'UI/UI_file.txt', songs_collected = {'1_song': False, '2_song': False, '3_song': False})
game.get_tile_indexs()
level.tile_indexs = game.tile_indexs.copy()

# Events
current_event = 0
event_locs = [[11 * tile_size, 4 * tile_size], 
[14 * tile_size, 2 * tile_size], 
[11 * tile_size, -1 * tile_size]]
event_tile_paths = ['Tiles/SingleGrass.png', 'Tiles/SingleGrass.png', 'Tiles/SingleGrass.png']
event_song = songs[0]
event_coins = [Coin('Collectables/coin_red.png', [loc[0], loc[1] - tile_size]) for loc in event_locs]
event_1 = Event(event_locs, event_tile_paths, event_song, event_coins)
events = [event_1]

# Functions
rendering_particles = False
particles = []
def render_particles(display, scroll, loc, color = (175, 75, 75), amount = 10): # Spawn particles
    if rendering_particles and len(particles) == 0:
        for i in range(amount):
            particles.append([[loc[0] + 7, loc[1] + 7], [random.randint(0, 20) / 10 - 1, random.randint(0, 20) / 10 - 1], random.randint(2, 4)])

    for particle in particles:
        particle[0][0] += particle[1][0]
        particle[0][1] += particle[1][1]
        particle[1][1] += 0.05
        particle[2] -= 0.1
        true_loc = [particle[0][0] - scroll[0], particle[0][1] - scroll[1]]
        pygame.draw.circle(display, color, true_loc, particle[2])

    for particle in particles:
        if particle[2] <= 0:
            particles.remove(particle)
        
    if len(particles) == 0:
        return False

    return True

# Game loop
while True:
    # Adjust scroll, to make "camera" follow the player with a slight lag
    if true_scroll[0] < 0:
        true_scroll[0] = 0
    elif true_scroll[0] + surface_size[0] > len(level.game_map[0]) * tile_size:
        true_scroll[0] = len(level.game_map[0]) * tile_size - surface_size[0]
    elif (0 <= true_scroll[0]) and (true_scroll[0] + surface_size[0] <= len(level.game_map[0]) * tile_size):
        if true_scroll[0] == 0 and (player.rect.x - true_scroll[0] - 160)/10 < 0:
            true_scroll[1] += (player.rect.y - true_scroll[1] - 110)/10
        elif true_scroll[0] + surface_size[0] == len(level.game_map[0]) * tile_size and (player.rect.x - true_scroll[0] - 160)/10 > 0:
            true_scroll[1] += (player.rect.y - true_scroll[1] - 110)/10
        else:
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
    coins_collected, song_collected, loc_collectable = level.render_collectables(display, scroll, player.rect)
    game.coins_collected += coins_collected

    # Get collision types dict and render map
    tile_rects = level.render_map(display, ['{}'.format(i) for i in range(1,17)], scroll)

    # Render event
    event = events[current_event]
    tile_rect, loc_event, particle_color_temp, coin_collected, song_collected, song_name = event.render(display, scroll, player.rect, shake_timer)
    if coin_collected:
        game.coins_collected += 1
        particle_amount = 10
    if song_collected:
        game.songs_collected[song_name] = True
        particle_amount = 10
    if event.state == (event.states + 1):
        if shake_timer == 0:
            game.screen_shake_counter = 20
            particle_amount = 20
        shake_timer += 1
        if shake_timer > 20:
            event.state += 1
            shake_timer = 0
    if particle_color_temp != None:
        particle_color = particle_color_temp
    if len(tile_rect) != 0:
        for tile in tile_rect:
            tile_rects.append(tile)
        
    # Move player
    player.move(tile_rects)

    # Move pet
    y_dist = player.rect.y - pet.rect.y
    x_dist = player.rect.x - pet.rect.x
    if abs(y_dist) < 32:
        if (x_dist) > 16:
            pet.moving_right = True
        elif (-x_dist) > 16:
            pet.moving_left = True
        elif abs(x_dist) < 32:
            pet.moving_left = False
            pet.moving_right = False
    pet.move(tile_rects)

    # Render player
    player.render(display, scroll)

    # Render pet
    pet.render(display, scroll)

    # Render UI
    game.render_ui(display, font, ui_outline_col)

    # Fadout music
    if song_timer <= 10000:
        song_timer += 1
    if song_timer == 600:
        game.fadeout_music(ms = fadout)

    # Render particles
    for loc in [loc_event, loc_collectable]:
        if loc != 0:
            rendering_particles = True
        if rendering_particles:
            rendering_particles = render_particles(display, scroll, loc, color = particle_color, amount = particle_amount)
        if song_collected:
            game.songs_collected[song_collected] = True
            game.songs_count += 1

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
                ui_outline_col = (25, 25, 25)
                current_song = '{}_song'.format(game.song_ui_selected + 1)
                game.play_music(current_song)
                game.volume_music(1)
                song_timer = 0
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                player.moving_right = False
            if event.key == K_LEFT:
                player.moving_left = False
            if event.key == K_SPACE:
                ui_outline_col = (71, 71, 71)

    # Scale display size to match window size
    screen.blit(pygame.transform.scale(display, window_size), (0, 0))

    # Update display at 60 frames per second
    pygame.display.update()
    clock.tick(framerate)