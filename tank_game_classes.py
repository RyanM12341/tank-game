import pygame as pg
from pygame._sdl2 import touch
import random as rand

#--------‐----------------classes--------------------------#
class Tank_Group(pg.sprite.Group):
	def draw(self, screen):
		sprites = self.sprites()
		for spr in sprites:
			screen.blit(spr.image, spr.rect)
			screen.blit(spr.new_turret_image, spr.turret_rect)
			screen.blit(spr.new_cannon_image, spr.cannon_rect)
			
			if hasattr(spr, 'healthbar'):
				screen.blit(spr.healthbar.image, spr.healthbar.rect)
				
				

class Grass_Group(pg.sprite.Group):
	#needs to go after movement (in player move)
	def update(self, screen_w, bound, player, added_grass):
		sprites = self.sprites()
		points = set()
		for spr in sprites:
			if spr.rect.left > screen_w or spr.rect.right < 0 or spr.rect.top > bound or spr.rect.bottom < -100: #to have consistency with the grass adding condition
				self.remove(spr)
				continue
			elif spr.rect.collidepoint(player.rect.center):
				c = spr
			points.add((int(spr.rect.topleft[0]), int(spr.rect.topleft[1])))
		
		grass_h = c.grass_h	
		poss_rects = set()
		
		for j in range(-1, 2):
			for i in range(-1, 2): 
				r = (int(c.rect.topleft[0] + (i * screen_w)), int(c.rect.topleft[1] + (j * grass_h)))
				poss_rects.add(r)
		
		missing_rects = poss_rects - points # set of topleft points for rects that might be needed but are not present
		
		for r in missing_rects:
			rect = pg.rect.Rect(*r, screen_w, bound)
			if not (rect.left > screen_w or rect.right < 0 or rect.top > bound or rect.bottom < -100): # for some reason rect.bottom < 0 means rect.bottom <40 or something like that
				new_grass = Grass(screen_w, bound, 'topleft', r)
				self.add(new_grass)
				added_grass.append(new_grass)
			
		added_points = []	
		for g in added_grass:
			added_points.append(g.rect.topleft)
			
		
		return missing_rects, poss_rects, points, added_grass, added_points
			
			

class Tank(pg.sprite.Sprite):
	def __init__(self, body_colour, turret_colour, cannon_colour, firerate, spawn_coords, speed, inaccuracy, health):
		super().__init__()
		
		self.body_length = 60
		self.turret_length = 35
		self.cannon_length = 35
		self.cannon_width = 15
	
		self.spawn_coords = spawn_coords
		
		#body
		body = pg.Surface((self.body_length, self.body_length))
		self.image = body.convert()
		self.rect = self.image.fill(body_colour)
		self.rect.center = (spawn_coords)
		
		#other components
		self.turret_image = pg.Surface((self.turret_length, self.turret_length)).convert_alpha() # used to be convert_alpha
		self.new_turret_image = self.turret_image
		self.turret_rect = self.turret_image.fill(turret_colour)
		self.turret_rect.center = self.rect.center
		
		self.cannon_image = pg.Surface((self.cannon_width, self.cannon_length)).convert_alpha()  # used to be convert_alpha
		self.new_cannon_image = self.cannon_image
		self.cannon_rect = self.cannon_image.fill(cannon_colour)
		self.cannon_rect.midbottom = self.turret_rect.midtop
		self.cannon_dir = (0, -((self.turret_length / 2) + self.cannon_length / 2))
		
		self.base_speed = speed
		self.max_speed = speed
		
		
		self.shoot_timer = 0
		
		self.base_firerate = firerate
		self.firerate = firerate # time between shots
		self.inaccuracy = inaccuracy #the max angle to the normal of the cannon that a bullet can be shot at
		
		self.base_health = health
		self.max_health = health
		self.health = health
		
		#vectors
		self.north = pg.math.Vector2(0, -1)
		
		self.x_v = 0
		self.y_v = 0
		
		#CONVERT ALL SURFACES####№#########################
	def calc_vector_to(self, pos):
		dx = pos[0] - self.rect.center[0]
		dy = pos[1] - self.rect.center[1]
		dir = pg.math.Vector2(dx, dy)
		return dir
	
	def point(self, pos, screen_w, bullets): #movement joystick passes pos = (x, y)
	#look joystick passes a vector to pos
		if type(pos) != tuple:
			dir = pos
		else:
			dir = self.calc_vector_to(pos)
		
		if dir.magnitude() > 0:
			angle =self.north.angle_to(dir)
			#if not (dx < 0 and angle < 90): 
			angle = 360 - angle
			
			self.new_turret_image = pg.transform.rotozoom(self.turret_image, angle, 1)
			self.turret_rect = self.new_turret_image.get_rect(center = self.rect.center)
			self.new_cannon_image = pg.transform.rotozoom(self.cannon_image, angle, 1)
			
			#put the cannon in the correct place
			self.cannon_dir = dir.normalize() * ((self.turret_length / 2)  +  (self.cannon_length / 2))
			coords = self.rect.center + self.cannon_dir
			
			self.cannon_rect = self.new_cannon_image.get_rect(center = coords)
			
		if self.shoot_timer > self.firerate:
			self.shoot(screen_w, bullets)
			self.shoot_timer = 0
		
	def shoot(self, screen_w, bullets):
		inaccuracy = rand.randint(-self.inaccuracy, self.inaccuracy)
		bullet_trajectory = self.cannon_dir.rotate(inaccuracy)
		return bullet_trajectory
		
	def change_direction(self, dir=None, mag=0): 
		#first if statements are for the buttons
		if dir == 'x' and self.x_v != mag:
			self.x_v += mag
		elif dir == 'y' and self.y_v != mag:
			self.y_v += mag
		else:
			self.x_v = mag[0]
			self.y_v = mag[1]
								
	def move(self, other = None): # other is a tuple		
		#move base
		if other is not None:
			self.rect.x += other[0] 
			self.rect.y += other[1]
		else:
			self.rect.x += self.x_v
			self.rect.y += self.y_v
		
	def move_the_rest(self):
		#move turret	
		self.turret_rect.center = self.rect.center	
		

		#move cannon
		cannon_x = self.rect.center[0] + self.cannon_dir[0]
		cannon_y = self.rect.center[1] + self.cannon_dir[1]
		self.cannon_rect.center = (cannon_x, cannon_y)
		
	def reset_v(self):
		self.x_v = 0
		self.y_v = 0
		
	def timer_update(self):
		self.shoot_timer += 1/60

		
						
class Player(Tank):
	def shoot(self, screen_w, player_bullets):
		bullet_trajectory = super().shoot(screen_w, player_bullets)
		player_bullets.add(Bullet(self.cannon_rect.center, bullet_trajectory))
		
	def move(self, screen_w, bound, player_bullets, enemy_bullets, enemies, play_area):
			#repurposing a part of original tank for a larger map
		super().move()
		
		def scroll(dist, groups): #this is supposed to be inside the function move
			for group in groups:
				for spr in group.sprites():
					spr.move(other=dist)
		
		items = [player_bullets, enemy_bullets, enemies, play_area]
		half_length = 150
		left = screen_w / 2 - half_length
		right = screen_w / 2 + half_length
		top = bound / 2 - half_length
		bottom = bound / 2 + half_length
		if self.rect.left < left:
			dist = left - self.rect.left
			self.rect.left = left
			scroll((dist, 0), items)
		if self.rect.right > right:
			dist = right - self.rect.right
			self.rect.right = right
			scroll((dist, 0), items)
		if self.rect.top < top:
			dist = top - self.rect.top
			self.rect.top = top
			scroll((0, dist), items)
		if self.rect.bottom > bottom:
			dist = bottom - self.rect.bottom
			self.rect.bottom = bottom
			scroll((0, dist), items)
			
		super().move_the_rest()
		
	def reset(self, screen_w, bullets):
		self.rect.center = self.spawn_coords
		self.shoot_timer = 0
		self.point(self.north, screen_w, bullets)
		self.health = self.max_health
		
	def update(self, screen_w, bound, player_bullets, enemy_bullets, enemies, play_area):
		self.move(screen_w, bound, player_bullets, enemy_bullets, enemies, play_area)
		self.move_the_rest()
		self.timer_update()
	
	
	
class Enemy(Tank):
	def __init__(self, body_colour, turret_colour, cannon_colour, firerate, spawn_coords, speed, inaccuracy, health):
		"""#cant use calc_vector_to here because it has no rect at this point
		dx = player.rect.center[0] + spawn_coords[0]
		dy = player.rect.center[1] + spawn_coords[1]
		dir_vector = pg.math.Vector2(dx, dy)
		if dir_vector.magnitude() < 500:
			dir_vector.scale_to_length(rand.randint(500, 2000))
			pos_x = math.abs(player.rect.center[0] + dir_vector[0])
			pos_y = math.abs(player.rect.center[1] + dir_vector[1])
			spawn_coords = (pos_x, pos_y)
			
			old way of spawning tanks that takes spawn_pos as random coordinates in the play area
			"""	
		
		super().__init__(body_colour, turret_colour, cannon_colour, firerate, spawn_coords, speed, inaccuracy, health)
		
		#much of the following is repeated in functions that would normally be in the update function
		healthbar_pos_x = self.rect.center[0]
		healthbar_pos_y = self.rect.center[1] - (self.body_length / 2) - self.cannon_length - 20
		healthbar_pos = (healthbar_pos_x, healthbar_pos_y)
		
		self.healthbar = Healthbar(60, 15, 3, 'center', healthbar_pos)
		
	def move_the_rest(self):
		super().move_the_rest()
		healthbar_pos_x = self.rect.center[0]
		healthbar_pos_y = self.rect.center[1] - (self.body_length / 2) - self.cannon_length - 5
		healthbar_pos = (healthbar_pos_x, healthbar_pos_y)
		self.healthbar.rect.center = healthbar_pos
		
		
	def lock_player(self, player, screen_w, bullets):
		#point cannon
		self.point(player.rect.center, screen_w, bullets)
		
		#move towards player
		dir_vector = self.calc_vector_to(player.rect.center)
		mag = dir_vector.magnitude()
		if mag > 500:
			dir_vector.scale_to_length(self.max_speed)
			self.change_direction(mag = dir_vector)
		else:
			self.reset_v()
			
	def shoot(self, screen_w, enemy_bullets):
		bullet_trajectory = super().shoot(screen_w, enemy_bullets)
		enemy_bullets.add(Bullet(self.cannon_rect.center, bullet_trajectory))	
	
	def update(self, screen_w, bound, player, enemy_bullets): #most of these variables are only here for compatability with player tank
		self.lock_player(player, screen_w, enemy_bullets)
		self.healthbar.update(self)
		self.move()
		self.move_the_rest()
		self.timer_update()

		
						
class Bullet(pg.sprite.Sprite):
	def __init__(self, pos, dir):
		super().__init__()
		self.image = pg.Surface((21, 21), pg.SRCALPHA).convert_alpha()
		pg.draw.circle(self.image, 'Yellow', (11, 11), 10)
		self.rect = self.image.get_rect(center = pos)
		
		self.v = dir.normalize() * 20
		
	def move(self, other=None): #other is a tuple
		if other is not None:
			self.rect.x += other[0] 
			self.rect.y += other[1] 
		else:
			self.rect.center += self.v
		
	def update(self, screen_w, bound, screen):
		self.move()
		if self.rect.right < 0 or self.rect.left > screen_w or self.rect.bottom < 0 or self.rect.top > bound:
			self.kill()
			return
		screen.blit(self.image, self.rect)
		
#===========Environment=============#
		
class Background(pg.sprite.Sprite):
	def __init__(self, start_pos, width, height, colour):
		super().__init__()
		self.image = pg.Surface((width, height)).convert()
		self.rect = self.image.fill(colour)
		self.rect.topleft = start_pos
		
	def draw(self, screen):
		screen.blit(self.image, self.rect)
		
	def in_area(self, pos):
		return self.rect.collidepoint(pos)
		
class Grass(pg.sprite.Sprite):
	def __init__(self, screen_w, bound, point, pos):
		super().__init__()
		columns = 8
		tile_w = screen_w / columns
		# we want square tiles so tile_h = tile_w
		rows = bound / tile_w
		if str(type(rows))  == "<class 'float'>":
			rows = int(rows) + 1
		self.grass_h = rows * tile_w
		sur = pg.Surface((columns * tile_w, rows * tile_w))
		for y in range(0, rows):
			for x in range(0, columns):
				grass_index = rand.randint(0, 2)
				pg.draw.rect(sur, f'chartreuse{grass_index + 2}', (x * tile_w, y * tile_w, tile_w, tile_w))
			
		#pg.draw.rect(sur, 'Red', (0, 0, screen_w, self.grass_h), 10)	
		self.image = sur
		self.rect = self.image.get_rect(**{point:pos})
		
	def move(self, other): #terrible aregument labelling for compatabilty with other sprites with the scrolling of the screen
		self.rect.x += other[0] 
		self.rect.y += other[1]
				
		
class Healthbar(pg.sprite.Sprite):
	def __init__(self, length, width, border_thickness, point, pos):
		super().__init__()
		self.length = length
		self.width = width
		self.border_thickness = border_thickness
		
		self.image = pg.Surface((length, width))
		self.image.fill('Red')
		self.rect = self.image.get_rect(**{point:pos})
		pg.draw.rect(self.image, 'Black', (0, 0, length, width), border_thickness)
		
	def update(self, entity): #entity is the one whose health the healthbar shows
		length = self.length * (entity.health/entity.max_health)
		self.image.fill('Gray')
		pg.draw.rect(self.image, 'Red', (0,0,length,self.width))
		pg.draw.rect(self.image, 'Black', (0, 0, self.length, self.width), self.border_thickness)	

#===========controls=============#		
						
class Button(pg.sprite.Sprite):
	def __init__(self, pos, dimension, magnitude):
		super().__init__()
		self.image = pg.Surface((300, 300)).convert()
		self.rect = self.image.fill('Gray')
		self.rect.center = pos
		self.dimension = dimension
		self.magnitude = magnitude
		self.touches = []
			
	def update(self, mouse_pos, state, id):
		
		mag = 0	
		if state == 'up' and id in self.touches:
			if len(self.touches) == 1:
				mag = -self.magnitude
			self.touches.remove(id)	
		elif state == 'down' and self.rect.collidepoint(mouse_pos):
			if not self.touches:
				mag = self.magnitude
			self.touches.append(id)
			
		player.change_direction(self.dimension, mag)
	
		
				
class Joystick(pg.sprite.Sprite):
	def __init__(self, type, screen_w, bound, controls_h):
		super().__init__()
		self.joy_type = type
		if self.joy_type == 'movement':
			x = screen_w * 0.25	
		elif self.joy_type == 'looking':
			x = screen_w * 0.75
		
		self.image = pg.Surface((301, 301)).convert()
		pg.draw.circle(self.image, 'Gray', (151, 151), 151)
		self.rect = self.image.get_rect(center = (x, bound + controls_h / 2))
		
		self.true_center = self.rect.center
		self.touch_info = {'id':None, 'start_point':()}
		
	def reset_finger_info(self, player):
		self.touch_info['id'] = None
		self.rect.center = self.true_center
		if self.joy_type == 'movement':
			player.reset_v()
		
	def update(self, fingers, screen_w, screen_h,player, bullets, pos=None, type=None, id=None): #clapped way of doing it
		if id is not None: #presence of an id shows that this update is to add or remove a  touch
			if type == 'down' and self.rect.collidepoint(pos) and self.touch_info['id'] is None:
				self.touch_info['id'] = id
				self.touch_info['start_point'] = pos
			elif type == 'up' and self.touch_info['id'] == id:
			#could be better to ignore finger ups and instead look for if the finger is gone
				self.reset_finger_info(player)
				
				
		elif self.touch_info['id'] is not None: #no id means we just need to update the records of where the touch is
			 #delay from this being an elif?
			finger = None
			#find the finger in the fingers list that corresponds to this joystick
			for f in fingers:
				if f['id'] == self.touch_info['id']:
					finger = f
					break
					
				
			if finger is not None: 
				#finger for this joystick has been found
				x = finger['x'] * screen_w
				y = finger['y'] * screen_h
				event_pos = (x, y)
				diff_x = event_pos[0] - self.touch_info['start_point'][0]
				diff_y = event_pos[1] - self.touch_info['start_point'][1]
				diff = (diff_x, diff_y)
				diff_vector = pg.math.Vector2(diff)
				dist = diff_vector.magnitude()
				
				deadzone = 50
				if dist > deadzone:
					effective_dist = dist - deadzone
					if effective_dist > 100:
						effective_dist = 100
					#effective dist isi proportion of max speed(100 is max, 0 is 0) (also how much joystick moves)
					diff_vector.scale_to_length(effective_dist)
					x = diff_vector[0]
					y = diff_vector[1]
					
					
					#position joystick visually
					new_center_x = self.true_center[0]  + x 
					new_center_y = self.true_center[1] + y
					self.rect.center = (new_center_x, new_center_y)
					if self.joy_type == 'movement':
						player.change_direction(mag = (x/100 * player.max_speed, y / 100 * player.max_speed))
					else:
						player.point(diff_vector, screen_w, bullets)
			
				else:
					#movement below deadzone so no player movement
					if self.joy_type == 'movement':
						player.reset_v()
					self.rect.center = self.true_center
			else: 
				#no finger corresponding to this joystick
				self.reset_finger_info(player)
"""
need base?
"""

class Text(pg.sprite.Sprite):
	def __init__(self, size, txt, AA, colour, point, pos, font=None, new_txt=None):
		super().__init__()
		
		self.AA = AA
		self.colour = colour
		
		self.font = pg.font.Font(font, size)
		self.image = self.font.render(txt, AA, colour)
		self.rect = self.image.get_rect(**{point:pos})
		self.new_txt = new_txt
		
	def update(self):
		if self.new_txt is not None:
			txt = self.new_txt()
			self.image = self.font.render(txt, self.AA, self.colour)
		