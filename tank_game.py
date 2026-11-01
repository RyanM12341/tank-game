import pygame as pg
from pygame._sdl2 import touch
import random as rand

import tank_game_classes as c

"""
Ideas:
	better title menu
	pause menu
	abilities
	shooting animations
	better tank designs and movement
	different weapons
	different type of enemies
	fix spawning locations
	despawning mechanic
	stop enemies from being on top of each other
	explosions when bullets hit
	sound effects
"""

#--------‐----------------Initialisation--------------------------#

pg.init()
pg.display.set_caption('Game')

game_active = False

#--screen variables and division
screen = pg.display.set_mode((1000, 2000))
screen.set_colorkey('Black')
#the numbers given to set_mode are arbritrary
screen_info = pg.display.Info()
screen_w = screen_info.current_w
screen_h = screen_info.current_h
screen_split = 0.60
controls_h = screen_h * (1-screen_split)
bound = screen_h * screen_split

#--touch controls
control_mag = 2
added_grass = []

num_dev = pg._sdl2.touch.get_num_devices()
device_id = pg._sdl2.touch.get_device(num_dev - 1)

#--score and difficulty (linked)
high_score = 0
score = 0
difficulty_increase = 0.2

#--timers
clock = pg.time.Clock()
enemy_timer = pg.USEREVENT + 1
debug_timer = pg.USEREVENT + 2
pg.time.set_timer(debug_timer, 5000)
pg.time.set_timer(enemy_timer, 500)
#--------‐----------------Groups--------------------------#

#--player
player = c.Player('Blue', 'Red', 'Black', 0.2, (screen_w / 2, bound / 2), 5, 5, 100) #Buttons also have fixed magnitudes
player_group = c.Tank_Group(player)

player_bullets = pg.sprite.Group()
enemy_bullets = pg.sprite.Group()

#--area where game takes place
play_area = c.Grass_Group()

#--controls
controls_group = pg.sprite.RenderUpdates()
movement_joystick = c.Joystick('movement', screen_w, bound, controls_h)
point_joystick = c.Joystick('looking', screen_w, bound, controls_h)
controls = [movement_joystick, point_joystick]
controls_group.add(*controls)

#--enemies
enemies = c.Tank_Group()

#--player healthbar
healthbar = pg.sprite.Group(c.Healthbar(screen_w, 75, 15, 'topleft', (0, bound)))

#--items on menu title screen
menu_items = pg.sprite.Group()

title = c.Text(200, 'Tank Game', True, 'White', 'center', (screen_w / 2, screen_h / 2))
finishing_score = c.Text(50, f'Your score: 0', True, 'White', 'midtop', title.rect.midbottom, new_txt=lambda: f'Your score: {score}')
high_score_display = c.Text(50, f'High score: {high_score}', True, 'White', 'midtop', finishing_score.rect.midbottom, new_txt=lambda: f'High score: {high_score}')

menu_items.add(title, finishing_score, high_score_display)

#--items present always
ui_items = pg.sprite.Group() 

fps_counter = c.Text(20, f'Fps: {clock.get_fps()}', True, 'Black', 'topleft', (0, 0), new_txt = lambda : f'Fps: {clock.get_fps()}')
ui_items.add(fps_counter)

#--backgrounds to everything when the game is active except game area
backgrounds = pg.sprite.Group() 

controls_background = c.Background((0, bound), screen_w, screen_h - bound, 'black')
backgrounds.add(controls_background)

#--items present only during the game
game_items = pg.sprite.Group() 

score_counter = c.Text(30, '0', True, 'black', 'midtop', (screen_w / 2, 0), new_txt= lambda: f'{score}')

game_items.add(healthbar, *controls, score_counter)

""" previously used to debug the problems witht the background

missing_rects_counter = c.Text(20, '' , True, 'Black', 'topleft', (0, 20), new_txt= lambda: f'missing rects: {missing_rects}'  )
poss_rects_counter = c.Text(20, '' , True, 'Black', 'topleft', (0, 40), new_txt= lambda: f'poss_rects: {poss_rects}')
points_counter = c.Text(20, '' , True, 'Black', 'topleft', (0, 60), new_txt= lambda: f'points: {points}')
added_grass_counter = c.Text(20, '' , True, 'Black', 'topleft', (0, 80), new_txt= lambda: f'points: {added_points}')"""

""" previous control system that used buttons

up = Button((screen_w * 0.5, bound + controls_h *0.25), 'y', -control_mag)
controls.add(up)

down = Button((screen_w * 0.5, bound + controls_h *0.75), 'y', control_mag)
controls.add(down)

left = Button((screen_w * 0.25, bound + controls_h * 0.5), 'x', -control_mag)
controls.add(left)

right = left = Button((screen_w * 0.75, bound + controls_h * 0.5), 'x', control_mag)
controls.add(right)
"""

#--------‐----------------Functions--------------------------#

def get_event_pos(event):
	x = event.x * screen_w
	y = event.y * screen_h
	event_pos = (x, y) #dic tionary once
	return event_pos


#--------‐----------------Event loop--------------------------#

while True:
	#--get all finger info
	fingers = []
	f = 0
	i = 0
	#search for fingers until there are none left
	while f is not None:
		f = pg._sdl2.touch.get_finger(device_id, i)
		if f is not None:
			fingers.append(f)
		i += 1
		
	for event in pg.event.get():
		if event.type == pg.FINGERDOWN:
			event_pos = get_event_pos(event)
	
			if game_active:	
				#--update controls accordingly
				controls_group.update(fingers, screen_w, screen_h, player, player_bullets, event_pos, 'down', event.finger_id)
			else:
				#--start the game
				game_active = True
				score = 0
				score_counter.update()
				player.reset(screen_w, player_bullets)
				finishing_score.update()
				high_score_display.update()
				healthbar.update(player)
				#ui_items.add(missing_rects_counter, poss_rects_counter, points_counter, added_grass_counter) used to debug the background issues
				for spr in controls_group.sprites():
					spr.reset_finger_info(player)
				pg.time.set_timer(enemy_timer, 3000)
				play_area.add(c.Grass(screen_w, bound, 'center', player.rect.center))
					
		if event.type == pg.FINGERUP:
			event_pos = get_event_pos(event)
			if game_active:
				#--update controls accordingly
				controls_group.update(fingers, screen_w, screen_h, player, player_bullets, event_pos, 'up', event.finger_id)
				
		if  event.type == enemy_timer and game_active:
			#--create a position for enemt tank in quadrant furthest from player centre and spswn it in
			if player.rect.center[0] < screen_w / 2:
				pos_x = rand.randint(player.rect.center[0] + 500, screen_w)
			else:
				pos_x = rand.randint(0, player.rect.center[0] - 500)
				
			if player.rect.center[1] < bound / 2:
				pos_y = rand.randint(player.rect.center[1] + 500, int(bound))
			else:
				pos_y = rand.randint(0, player.rect.center[1] - 500)
				
			difficulty_multiplier = 1 + (score * difficulty_increase)
			enemies.add(c.Enemy('green3', 'green4', 'Black', 1.5 / difficulty_multiplier, (pos_x, pos_y), 2 * difficulty_multiplier, 10, 30 * difficulty_multiplier))
					
		if event.type == debug_timer:
			pass
	
#------------------Event Checking Ends--------------#
	
	if game_active:
		#a lot of the assignment is for compatabiliy with debugging tools that are normally commented out		
		added_rects = player_group.update(screen_w, bound, player_bullets, enemy_bullets, enemies, play_area)
		missing_rects, poss_rects, points, added_grass, added_points = play_area.update(screen_w, bound, player, added_grass)
		enemies.update(screen_w, bound, player, enemy_bullets)
		controls_group.update(fingers, screen_w, screen_h, player, player_bullets) #lack of parameters messes up buttons
		
		#--check if any enemies have been hit by player fire and act accordingly
		enemy_collisions = pg.sprite.groupcollide(enemies, player_bullets, False, True)
		for enemy in enemy_collisions:
			collision_num = len(enemy_collisions.get(enemy))
			enemy.health -= 10 * collision_num
			if enemy.health <= 0:
				enemy.kill()
				score += 1
				score_counter.update()
				player.health += enemy.max_health * 0.25
				if player.health > player.max_health:
					player.health = player.max_health
				healthbar.update(player)
			
		#--check if player has been hit by enemy fire and act accordingly
		if pg.sprite.groupcollide(player_group, enemy_bullets, False, True):
			player.health -= 10
			if player.health <= 0:
				game_active = False
				enemies.empty()
				enemy_bullets.empty()
				player_bullets.empty()
				play_area.empty()
				if score > high_score:
					high_score = score
				#ui_items.remove(missing_rects_counter, poss_rects_counter, points_counter, added_grass_counter) previously used when debugging the background
			healthbar.update(player)
		
		#--draw everything in	
		screen.fill('Black')
		play_area.draw(screen)
		#bullets are blitted in their update function
		player_bullets.update(screen_w, bound, screen)
		enemy_bullets.update(screen_w, bound, screen)
		
		enemies.draw(screen)
		player_group.draw(screen)	
		
		controls_background.draw(screen)
		game_items.draw(screen)
		
	else:
		#when game is not active, display menu items
		screen.fill('Blue')
		menu_items.update()
		menu_items.draw(screen)

	#display the ui items no matter what
	ui_items.update()
	ui_items.draw(screen)
	pg.display.update()
	
	clock.tick(60)