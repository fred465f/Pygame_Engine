# Imports
from cmath import rect
from dis import dis
from msilib.schema import Class
from re import A
from tkinter.messagebox import NO
import pygame, sys, random, noise, time, math

# ---------------------------------------------------------------------
# Base parent classes
# ---------------------------------------------------------------------

# Actor parent class for all moveable and interactable objects
class Actor():
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, colorkey = (255, 255, 255)):
        self.image_id = image_id
        self.image = pygame.image.load(self.image_id + '.png').convert()
        self.image.set_colorkey(colorkey)
        self.location = location
        self.animation_file_id = animation_file_id
        self.animation_frames = {}
        self.animation_database = {}
        self.action = None
        self.frame = 0
        self.flip = False

        # Load animations for actor
        if self.animation_file_id != None:
            self.load_animation()

    # Function for rendering actor
    def render(self, display, scroll):
        if self.action != None:
            self.frame += 1
            if self.frame >= len(self.animation_database[self.action][1]):
                self.frame = 0
            image_id = self.animation_database[self.action][1][self.frame]
            self.image = self.animation_frames[image_id]
        display.blit(pygame.transform.flip(self.image, self.flip, False), (self.location[0] - scroll[0], self.location[1] - scroll[1]))

    # Function for loading animatiion for actor (changing pygame.image as dictated by a .txt file)
    def load_animation(self):
        data = None
        with open(self.animation_file_id, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            anim_id, anim_frames, anim_type = row.split(' ')
            anim_action = anim_id.split('/')[-1]
            animation_frame_data = []
            for i, frames in enumerate(anim_frames.split('/')):    
                anim_image = pygame.image.load(anim_id + '/' + anim_action + '_{}'.format(i) + '.png').convert()
                anim_image.set_colorkey((255, 255, 255))
                self.animation_frames[anim_action + '_{}'.format(i)] = anim_image.copy()
                for frame in range(int(frames)):
                    animation_frame_data.append(anim_action + '_{}'.format(i))
            self.animation_database[anim_action] = [anim_type, animation_frame_data]

    # Change action
    def change_action(self, action):
        if self.action != action:
            self.action = action
            self.frame = 0

# Parent class for all collectable; coins, stars, ...
class Collectable(Actor):
    # Constructor
    def __init__(self, image_id, location, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, colorkey)

        # Extra constructor for Collectable
        self.rect = pygame.Rect(*self.location, self.image.get_width(), self.image.get_height())

# Parent class for all objects affected by wind; grass, particles, ...
class Wind():
    pass

# Parent class for the game
class Game():
    # Constructor
    def __init__(self, levels, tile_file, ui_elements = None):
        self.levels = levels
        self.tile_file = tile_file
        self.tile_indexs = {}
        self.ui_elements = ui_elements
        self.level_count = 0
        self.stars_collected = 0

    # Funtion to get dictionary of type {'1': pygame.image, '2': pygame.image, ...}
    # for all tiles used ingame
    def get_tile_indexs(self):
        data = None
        with open(self.tile_file, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            id, image_id = row.split(' ') 
            self.tile_indexs[id] = pygame.image.load(image_id + '.png').convert()

    # Function to get the next level of the game
    def next_level(self):
        if self.level_count <= len(self.levels):
            self.level_count += 1
        return self.levels[self.level_count]

    # Function to get the previous level of the game
    def previous_level(self):
        if self.level_count != 0:
            self.level_count -= 1
        return self.levels[self.level_count]

    # Function to render the UI
    def render_ui(self):
        if self.ui_elements != None:
            pass

# Parent class for all levels
class Level():
    # Constructor
    def __init__(self, player, game_map_id, tile_size, tile_indexs = None, enemies = None, collectables = None, player_spawn_position = None):
        self.player = player
        self.player_spawn_position = player_spawn_position
        self.game_map_id = game_map_id + '.txt'
        self.game_map = []
        self.tile_indexs = tile_indexs
        self.tile_size = tile_size
        self.enemies = enemies
        self.collectables = collectables

    # Function for loading map
    def load_map(self):
        if self.game_map == []:
            data = None
            with open(self.game_map_id, 'r', encoding = 'UTF8') as file:
                data = file.read().split('\n')
            for row in data:
                self.game_map.append(row.split('\t'))            
        else:
            print("Map already loaded")
            print('\n\n\n' + str(self.game_map) + '\n\n\n')
            self.game_map = None

    # Function for rendering map
    def render_map(self, display, col_with, scroll):
        if self.game_map != None:
            tile_rects = []
            for row_nr, row in enumerate(self.game_map):
                for tile_nr, tile in enumerate(row):
                    if tile != '0':
                        x_pos = tile_nr * self.tile_size
                        y_pos = row_nr * self.tile_size
                        display.blit(self.tile_indexs[tile], (x_pos - scroll[0], y_pos - scroll[1]))
                    if tile in col_with:
                        tile_rects.append(pygame.Rect(x_pos, y_pos, self.tile_size, self.tile_size))
            return tile_rects
        else:
            print("Map not yet loaded")

    # Function for rendering actors
    def render_actors(self, display):
        pass

    # Function for rendering collectables
    def render_collectables(self, display):
        pass


# ---------------------------------------------------------------------
# Child classes of Actor
# ---------------------------------------------------------------------

# Character class
class Character(Actor):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, colorkey)

        # Extra constructor for Character
        self.rect = pygame.Rect(*self.location, self.image.get_width(), self.image.get_height())

    # Function for testing for collisions
    def collision_test(self, tiles):
        hit_list = []
        for tile in tiles:
            if self.rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list

    # Function for adjusting actor movement
    def adjust_movement(self):
        # Reset movement
        self.movement = [0, 0]

        # Adjust player movement in x-direction
        if self.moving_right:
            self.movement[0] += 2
        if self.moving_left:
            self.movement[0] -= 2

        # Adjust player movement in x-direction
        self.movement[1] += self.y_momentum
        self.y_momentum += 0.2

        # Cap y-momentum
        if self.y_momentum > 3:
            self.y_momentum = 3

    # Function for moving actor
    def move(self, tiles):
        # Adjust player movement
        self.adjust_movement()

        # Keep track of collision types
        collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

        # Find collisions in x-direction
        self.rect.x += self.movement[0]
        hit_list = self.collision_test(tiles)
        for tile in hit_list:
            if self.movement[0] > 0:
                self.rect.right = tile.left
                collision_types['right'] = True
            elif self.movement[0] < 0:
                self.rect.left = tile.right
                collision_types['left'] = True

        # Find collisions in y-direction
        self.rect.y += self.movement[1]
        hit_list = self.collision_test(tiles)
        for tile in hit_list:
            if self.movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types['bottom'] = True
            elif self.movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types['top'] = True

        # Make player fall down if they hit a ceiling
        if collision_types['top']:
            self.y_momentum = - 1/2 * self.y_momentum
        
        # Cheking if player touched ground, and are able to jump again
        if collision_types['bottom']:
            self.y_momentum = 0
            self.air_timer = 0
        else:
            self.air_timer += 1

# Player class is actually a child class of Character class
# that inherits functionality from the Actor class
class Player(Character):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, colorkey)

        # Extra constructor for Player
        self.movement = [0, 0]
        self.y_momentum = 0
        self.moving_left = False
        self.moving_right = False
        self.air_timer = 0
        self.spawn_found = False

    # Function for moving player
    def move(self, tiles):
        # Default function for moving characters
        super().move(tiles)

        # Extra functionality for moving player
        if self.movement[0] > 0:
            self.change_action('run')
            self.flip = False
        elif self.movement[0] == 0:
            self.change_action('idle')
        elif self.movement[0] < 0:
            self.change_action('run')
            self.flip = True

        # Update position for animation
        self.location = [self.rect.x, self.rect.y]

# Enemy class is actually a child class of Character class
# that inherits functionality from the Actor class
class Enemy(Character):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, colorkey)

        # Extra constructor for Enemy
        self.movement = [0, 0]
        self.moving_left = False
        self.moving_right = False


# ---------------------------------------------------------------------
# Child classes of Collectables
# ---------------------------------------------------------------------

# Coin class
class Coin(Collectable):
    pass

# Star class
class Star(Collectable):
    pass


# ---------------------------------------------------------------------
# Child classes of Wind
# ---------------------------------------------------------------------

# Grass class
class Grass(Wind):
    # Constructor
    def __init__(self, image, loc):
        self.image = image
        self.image.set_colorkey((255, 255, 255))
        self.loc = loc
        self.angle = 0

    # Rotate grass baes on distance from player to grass
    def rotate(self, rect):
        dist = self.distance(rect)
        if dist < 10 and self.angle == 0:
            self.angle = 30
            self.image = pygame.transform.rotate(self.image, self.angle)
        else:
            self.angle = 0
            self.image = pygame.transform.rotate(self.image, self.angle)
            
    # Distance from player to grass
    def distance(self, rect):
        rect_pos = [rect.center[0], rect.bottom]
        return math.sqrt((rect_pos[0] - self.loc[0])**2 + (rect_pos[1] - self.loc[1])**2)

    # Function for rendering all grass
    def render(self, display, scroll, rect):
        self.rotate(rect)
        grass_rect = pygame.Rect(*self.loc, self.image.get_width(), self.image.get_height())
        display.blit(self.image, (grass_rect.x - scroll[0], grass_rect.y - scroll[1]))