# Imports
from socket import gaierror
from inflection import titleize
import pygame, sys, random, noise, time, math

from sympy import re

# ---------------------------------------------------------------------
# Base parent classes
# ---------------------------------------------------------------------

# Actor parent class for all moveable and interactable objects
class Actor():
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        self.tile_size = tile_size
        self.image_id = image_id
        self.image = pygame.image.load(self.image_id).convert()
        self.image.set_colorkey(colorkey)
        self.location = location
        self.animation_file_id = animation_file_id
        self.animation_frames = {}
        self.animation_database = {}
        self.action = None
        self.frame = 0
        self.flip = False
        self.sound_file = sound_file
        self.sound_database = {}

        # Load animations for actor
        if self.animation_file_id != None:
            self.load_animation()

        # Load sounds for actor
        if self.sound_file != None:
            self.load_sounds()

    # Funtion to load dictionary of type {'background_music': 'file1.wav', 'start_scene': 'file2.wav', ...}
    # for all music files used ingame
    def load_sounds(self):
        data = None
        with open(self.sound_file, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            sound_id, sound_path = row.split(' ') 
            self.sound_database[sound_id] = pygame.mixer.Sound(sound_path)

    # Function to play sound from sound_database dictionary
    def play_sound(self, sound_id):
        if sound_id in self.sound_database.keys():
            self.sound_database[sound_id].play()

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
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

        # Extra constructor for Collectable
        rect_location = [self.location[0] + int(self.tile_size/4), self.location[1] + int(self.tile_size/4)]
        self.rect = pygame.Rect(*rect_location, int(self.tile_size/4), int(self.tile_size/4))

# Parent class for all objects affected by wind; grass, particles, ...
class Wind():
    pass

# Parent class for the game
class Game():
    # Constructor
    def __init__(self, levels, tile_file, music_file = None, ui_file = None, colorkey = (255, 255, 255), songs_collected = None):
        self.colorkey = colorkey
        self.levels = levels
        self.tile_file = tile_file
        self.music_file = music_file
        self.music_database = {}
        self.music_loaded = False
        self.tile_indexs = {}
        self.ui_file = ui_file
        self.ui_images = {}
        self.ui_rects = {}
        self.level_count = 0
        self.coins_collected = 0
        self.songs_collected = songs_collected
        self.songs_lst = ['1_song', '2_song', '3_song']
        self.song_ui_momentum = 5
        self.song_ui_height = 200
        self.song_ui_key_pressed = False
        self.song_ui_selected = 0
        self.songs_count = 0
        self.screen_shake_counter = 0
        self.surf_size = [300, 200]

        # Load music for game
        if self.music_file != None:
            self.load_music()

        # Load ui images for game
        if self.ui_file != None:
            self.load_ui_images()

    # Funtion to load dictionary of type {'background_music': 'file1.wav', 'start_scene': 'file2.wav', ...}
    # for all music files used ingame
    def load_music(self):
        data = None
        with open(self.music_file, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            music_id, music_path = row.split(' ') 
            self.music_database[music_id] = music_path

    # Function to play music from music_database dictionary
    def play_music(self, music_id, repeat = -1):
        if not self.music_loaded:
            pygame.mixer.music.load(self.music_database[music_id])
            self.music_loaded = True
        else:
            pygame.mixer.music.unload()
            pygame.mixer.music.load(self.music_database[music_id])
        pygame.mixer.music.play(repeat)

    # Function to pause music
    def pause_music(self, condition = True):
        if self.music_loaded:
            if condition:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    # Function to set volume music
    def volume_music(self, volume):
        if self.music_loaded:
            pygame.mixer.music.set_volume(volume)

    # Function to fadeout music
    def fadeout_music(self, ms = 1000):
        if self.music_loaded:
            pygame.mixer.music.fadeout(ms)
    
    # Funtion to get dictionary of type {'1': pygame.image, '2': pygame.image, ...}
    # for all tiles used ingame
    def get_tile_indexs(self, colorkey = (255, 255, 255)):
        data = None
        with open(self.tile_file, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            id, image_id, type = row.split(' ') 
            tile_img = pygame.image.load(image_id + '.png').convert()
            tile_img.set_colorkey(colorkey)
            self.tile_indexs[id] = [tile_img, type]

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

    # Funtion to load dictionary of type {'ui_image': pygame.image, ...}
    def load_ui_images(self):
        data = None
        with open(self.ui_file, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            id, path = row.split(' ')
            img = pygame.image.load(path).convert()
            img.set_colorkey(self.colorkey)
            self.ui_images[id] = img

    # Function to render the UI
    def render_ui(self, display, font):
        # Render different ui elements
        if self.ui_images != None:
            # Render coins collected
            scoretext = font.render(str(self.coins_collected), 1, (0,0,0))
            display.blit(scoretext, (15, 3))
            display.blit(self.ui_images['coin'], (0, 0))

            # Render songs collected
            songs = [self.ui_images[song + '_ui'] for song in self.songs_lst if self.songs_collected[song]]
            if len(songs) != 0:
                for i, song in enumerate(songs):
                    offset = 0
                    if i == self.song_ui_selected:
                        offset = 5
                    loc = [int(self.surf_size[0]/(len(songs) + 1) * (i + 1)) - int(song.get_width()/2), self.song_ui_height - offset]
                    display.blit(song, loc)

                if (self.song_ui_height >= (self.surf_size[1] - int(songs[0].get_height()) + 5)) and self.song_ui_key_pressed:
                    self.song_ui_height -= self.song_ui_momentum
                elif (self.song_ui_height <= 200) and (not self.song_ui_key_pressed):
                    self.song_ui_height += self.song_ui_momentum

    # Function to produce screen shake
    def screen_shake(self):
        if self.screen_shake_counter:
            self.screen_shake_counter -= 1
            return [random.randint(0, 8) - 4, random.randint(0, 8) - 4]

# Parent class for all levels
class Level():
    # Constructor
    def __init__(self, player, tile_size, game_map_id = None, tile_indexs = None, background_id = None, enemies = None, collectables = None, player_spawn_position = None):
        self.player = player
        self.player_spawn_position = player_spawn_position
        self.game_map_id = game_map_id
        self.game_map = []
        self.tile_indexs = tile_indexs
        self.tile_size = tile_size
        self.enemies = enemies
        self.collectables = collectables
        self.background_id = background_id
        self.background_elements = []

        # Load game map if given
        if self.game_map_id != None:
            self.load_map()
        
        # Load background elements
        if self.background_id != None:
            self.load_background()

    # Function for loading map
    def load_map(self):
        data = None
        with open(self.game_map_id, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            self.game_map.append(row.split('\t'))            

    # Function for rendering map
    def render_map(self, display, col_with, scroll):
        if self.game_map != None:
            tile_rects = []
            for row_nr, row in enumerate(self.game_map):
                for tile_nr, tile in enumerate(row):
                    if tile != '0':
                        x_pos = tile_nr * self.tile_size
                        y_pos = row_nr * self.tile_size
                        display.blit(self.tile_indexs[tile][0], (x_pos - scroll[0], y_pos - scroll[1]))
                    if tile in col_with:
                        tile_rects.append([pygame.Rect(x_pos, y_pos, self.tile_size, self.tile_size), self.tile_indexs[tile][1]])
            return tile_rects
        else:
            print("Map not yet loaded")

    # Function for loading background elements
    def load_background(self, colorkey = (255, 255, 255)):
        data = None
        with open(self.background_id, 'r', encoding = 'UTF8') as file:
            data = file.read().split('\n')
        for row in data:
            id, loc, parallax = row.split(' ')
            bg_img = pygame.image.load(id + '.png').convert()
            bg_img.set_colorkey(colorkey)
            self.background_elements.append([bg_img, [int(i) for i in loc.split(',')], float(parallax)])

    # Function for rendering background elements
    def render_background(self, display, scroll):
        if self.background_elements != []:
            for bg_element in self.background_elements:
                bg_img = bg_element[0]
                bg_loc = bg_element[1]
                bg_parallax = bg_element[2]
                display.blit(bg_img, (bg_loc[0] - scroll[0] * bg_parallax, bg_loc[1] - scroll[1] * bg_parallax))

    # Function for rendering actors
    def render_actors(self, display, scroll):
        pass

    # Function for rendering collectables
    def render_collectables(self, display, scroll, rect):
        # Check for collision with rect, if true, remove collectable
        collected = 0
        song = None
        for c in self.collectables:
            if c.rect.colliderect(rect):
                if isinstance(c, Coin):
                    self.collectables.remove(c)
                    collected += 1
                elif isinstance(c, Song):
                    song = c.name
                    self.collectables.remove(c)

        # Render collectables
        for c in self.collectables:
            c.render(display, scroll)

        # Return collected collectables
        return collected, song


# ---------------------------------------------------------------------
# Child classes of Actor
# ---------------------------------------------------------------------

# Character class
class Character(Actor):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

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

        # Normal tiles
        normal_tiles = [tile[0] for tile in tiles if tile[1] == '0']

        # Ramp tiles
        ramps_rect = [ramp[0] for ramp in tiles if ramp[1] != '0']
        ramps_type = [ramp[1] for ramp in tiles if ramp[1] != '0']

        # Collision with normal tiles
        # ------------------------------------------------
        # Find collisions in x-direction
        self.rect.x += self.movement[0]
        hit_list = self.collision_test(normal_tiles)
        for tile in hit_list:
            if self.movement[0] > 0:
                self.rect.right = tile.left
                collision_types['right'] = True
            elif self.movement[0] < 0:
                self.rect.left = tile.right
                collision_types['left'] = True

        # Find collisions in y-direction
        self.rect.y += self.movement[1]
        hit_list = self.collision_test(normal_tiles)
        for tile in hit_list:
            if self.movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types['bottom'] = True
            elif self.movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types['top'] = True

        # Collision with normal tiles
        # ------------------------------------------------
        for ramp, type in zip(ramps_rect, ramps_type):
            if self.rect.colliderect(ramp):
                # Relative x-position between player and ramp
                rel_x = self.rect.x - ramp.x

                # Get height at player's position based on the type of ramp
                if type == '1':
                    pos_height = rel_x + self.rect.width
                elif type == '2':
                    pos_height = self.tile_size - rel_x

                # Constraints
                pos_height = min(pos_height, self.tile_size)
                pos_height = max(pos_height, 0)

                # Set target y-position
                target_y = ramp.y + self.tile_size - pos_height

                # Check if player collided with ramp
                if self.rect.bottom > target_y:
                    # Adjust player height
                    self.rect.bottom = target_y
                    self.location[1] = self.rect.y
                    collision_types['bottom'] = True

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
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

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

# Pet class is actually a child class of Character class
# that inherits functionality from the Actor class
class Pet(Character):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

        # Extra constructor for Pet
        self.movement = [0, 0]
        self.y_momentum = 0
        self.moving_left = False
        self.moving_right = False
        self.air_timer = 0
        self.spawn_found = False

    # Function for moving pet
    def move(self, tiles):
        # Default function for moving characters
        super().move(tiles)

        # Extra functionality for moving pet
        """
        if self.movement[0] > 0:
            self.change_action('run')
            self.flip = False
        elif self.movement[0] == 0:
            self.change_action('idle')
        elif self.movement[0] < 0:
            self.change_action('run')
            self.flip = True
        """

        # Update position for animation
        self.location = [self.rect.x, self.rect.y]

# Enemy class is actually a child class of Character class
# that inherits functionality from the Actor class
class Enemy(Character):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

        # Extra constructor for Enemy
        self.movement = [0, 0]
        self.moving_left = False
        self.moving_right = False


# ---------------------------------------------------------------------
# Child classes of Collectables
# ---------------------------------------------------------------------

# Coin class
class Coin(Collectable):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255)):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

# Song class
class Song(Collectable):
    # Constructor
    def __init__(self, image_id, location, animation_file_id = None, sound_file = None, tile_size = 16, colorkey = (255, 255, 255), name = None):
        # Default actor constructor
        super().__init__(image_id, location, animation_file_id, sound_file, tile_size, colorkey)

        # Extra song constructor
        self.name = name


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