# Engine.py imports - pygame, sys, random, noise, time
from Engine import *

# Imports and Clock
clock = pygame.time.Clock()
from pygame.locals import *

# Initialize pygame
pygame.init()

# Variabels
window_size = (600, 400)
surface_size = (300, 200)
tile_size = 16
air_timer = 0
chunk_size = 8
last_time = time.time()
framerate = 60
true_scroll = [0, 0]
game_map = {}

# Function
def generate_chunk(x, y): # Generate chunk at position x, y from top left (0-indexed)
    chunk_data = []
    for y_pos in range(chunk_size):
        for x_pos in range(chunk_size):
            target_x = x * chunk_size + x_pos
            target_y = y * chunk_size + y_pos
            tile_type = 0 # Air (Nothing)
            height = int(noise.pnoise1(target_x * 0.1, repeat = 99999999) * 6)
            if target_y > 8 - height:
                tile_type = 1 # Dirt middle
            elif target_y == 8 - height:
                tile_type = 4 # Grass top
            if (target_y == 8 - height - 2):
                loc = [target_x - 1, target_y - 1]
                chunk_data.append([[0, 0], Grass(grass_index[1], loc)])
            elif tile_type != 0:
                chunk_data.append([[target_x, target_y], tile_type])
            else:
                chunk_data.append([[0, 0], 0])

    for i in range(len(chunk_data) - 1):
        if chunk_data[i][1] == 4 and i % 7 != 0:
            if (chunk_data[i + 1][1] == 0) and (chunk_data[i - 1][1] == 0):
                chunk_data[i][1] = 7 # Grass top single
            elif chunk_data[i + 1][1] == 0:
                chunk_data[i][1] = 6 # Grass top right
            elif chunk_data[i - 1][1] == 0:
                chunk_data[i][1] = 5 # Grass top left
    return chunk_data


# Caption, display and surface
pygame.display.set_caption('Blob\'s Adventure')
screen = pygame.display.set_mode(window_size, 0, 32)
display = pygame.Surface(surface_size)

# Images and tile indexes
background_image = pygame.image.load('background.png').convert()
dirt_middle_image = pygame.image.load('Tiles/DirtMiddle.png').convert()
dirt_left_image = pygame.image.load('Tiles/DirtLeft.png').convert()
dirt_right_image = pygame.image.load('Tiles/DirtRight.png').convert()
grass_top_image = pygame.image.load('Tiles/GrassTop.png').convert()
grass_top_right_image = pygame.image.load('Tiles/GrassTopRight.png').convert()
grass_top_left_image = pygame.image.load('Tiles/GrassTopLeft.png').convert()
grass_top_single_image = pygame.image.load('Tiles/SingleGrassTop.png').convert()
tile_index = {1:dirt_middle_image,
              2:dirt_left_image,
              3:dirt_right_image,
              4:grass_top_image,
              5:grass_top_left_image,
              6:grass_top_right_image,
              7:grass_top_single_image
              }

# Grass
grass1 = pygame.image.load('Tiles/Grass1.png').convert()
grass2 = pygame.image.load('Tiles/Grass2.png').convert()
grass3 = pygame.image.load('Tiles/Grass3.png').convert()
grass_index = {1:grass1,
              2:grass2,
              3:grass3,
              }

# Background objects
bg_objs = [[0.25, [120, 10, 70, 400]], [0.50, [120, 10, 70, 600]]]

# Player attributes
player = Player('blob_self_made', [50, 50])

# Game loop
while True:

    # Calculate time between frames for framerate independence
    dt = time.time() - last_time
    dt *= framerate
    last_time = time.time()

    # Fill screen for reset effect
    display.blit(background_image, (0, 0))

    # Adjust scroll, to make "camera" follow the player with a slight lag
    true_scroll[0] += (player.rect.x - true_scroll[0] - 160)/10 * dt
    true_scroll[1] += (player.rect.y - true_scroll[1] - 110)/10 * dt
    scroll = true_scroll.copy() # Integer copy of true_scroll, to make
    scroll[0] = int(scroll[0])  # ground movenment avoid bugs.
    scroll[1] = int(scroll[1])

    # Render background objects
    for obj in bg_objs:
        obj_rect = pygame.Rect(obj[1][0] - scroll[0] * obj[0], obj[1][1] - scroll[1] * obj[0], obj[1][2], obj[1][3])
        if obj[0] == 0.5:
            pygame.draw.rect(display, (14, 222, 150), obj_rect)
        elif obj[0] == 0.25:
            pygame.draw.rect(display, (9, 91, 85), obj_rect)

    # Create tile rects
    tile_rects = []
    for y in range(4): # 4 is number of chunks in y-direction
        for x in range(4): # 4 is number of chunks in x-direction
            target_x = x - 1 + int(round(scroll[0]/(chunk_size*tile_size)))
            target_y = y - 1 + int(round(scroll[1]/(chunk_size*tile_size)))
            target_chunk = str(target_x) + ';' + str(target_y)
            if target_chunk not in game_map:
                game_map[target_chunk] = generate_chunk(target_x, target_y)
            for tile in game_map[target_chunk]:
                if isinstance(tile[1], Grass):
                    tile[1].render(display, scroll, player.rect)
                    continue
                elif tile[1] == 0:
                    continue
                display.blit(tile_index[tile[1]],(tile[0][0]*tile_size-scroll[0],tile[0][1]*tile_size-scroll[1]))
                if tile[1] in [4, 5, 6, 7]: # Tiles to check for collision with
                    tile_rects.append(pygame.Rect(tile[0][0]*tile_size,tile[0][1]*tile_size, tile_size, tile_size))

    # Finds spawn location (spawns on grass)
    if not player.spawn_found:
        player.location = [tile_rects[1][0]*tile_size,tile_rects[1][1]*tile_size] # Second colidable selected as spawn position
        player.spawn_found = True

    # Move player and get collision types dict
    player.move(tile_rects, dt)

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
            if event.key == K_e: # Framerate testing REMOVE BEFORE COMPILING!!!!
                framerate = 10
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