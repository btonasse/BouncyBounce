version = '1.3'
from time import sleep
from random import randint, choice
from console.utils import cls
from console.screen import sc
from console import fg, bg, fx

class BouncyGrid():
	def __init__(self, rows=50, cols=120, gravity=0, friction=0):
		self.rows = rows
		self.cols = cols
		self.gravity = gravity
		self.friction = friction
		self.coords = dict()
		self.entities = []
		self.walls = []
		for x in range(self.rows):
			for y in range(self.cols):
				if x == 0 or x == self.rows-1 or y == 0 or y == self.cols-1:
					self.walls.append(Wall())
					self.coords[(x,y)] = self.walls[-1]
				else:
					self.coords[(x,y)] = ' '

	def printGrid(self, rows_full):
		print("\033[F"*rows_full, end='')
		grid = ''
		for x in range(self.rows):
			line = '\n'
			for y in range(self.cols):
				if self.coords[(x,y)] == ' ':
					line += self.coords[(x,y)]
				else:
					line += self.coords[(x,y)].symbol
			grid += line
		print(grid, end='')
		return grid

	def addWalls(self, positions, elasticity=100, fgcolor='white', bgcolor='default'):
		pass

	def addEntity(self, symbol, solidtype='bouncy', elasticity=100, fore='rand', back='default', pos='rand', speed=None):
		newpos = ''
		if pos == 'rand':
			while not newpos or self.coords[newpos] != ' ': 
				newpos = (randint(1,self.rows-1),randint(1,self.cols-1))
		elif self.coords[pos] != ' ':
			raise Exception(f"Cannot add entity to {pos}")
		else:
			newpos = pos
		self.entities.append(BouncyEntity(symbol, solidtype, elasticity, fgcolor=fore, bgcolor=back, speed=speed))
		self.coords[(newpos)] = self.entities[-1]
		self.entities[-1].pos = newpos

	def evalImpact(self): 
		entity_queue = sorted([entity for entity in self.entities], key=lambda x: (x.energy[0]+x.energy[1])/2)
		while len(entity_queue) > 0:
			target = entity_queue[0].targetpos
			
			if isinstance(self.coords[target], Wall):
				if entity_queue[0].deltas[0] and (self.coords[(entity_queue[0].pos[0],entity_queue[0].pos[1]+entity_queue[0].deltas[1])] == ' ' or self.coords[(entity_queue[0].pos[0]+entity_queue[0].deltas[0],entity_queue[0].pos[1])] != ' '):
					entity_queue[0].speed[0] *= -1
				if entity_queue[0].deltas[1] and (self.coords[(entity_queue[0].pos[0]+entity_queue[0].deltas[0],entity_queue[0].pos[1])] == ' ' or self.coords[(entity_queue[0].pos[0],entity_queue[0].pos[1]+entity_queue[0].deltas[1])] != ' '):
					entity_queue[0].speed[1] *= -1
				self.updateDeltas(entity_queue[0])
				self.updateTargetPos(entity_queue[0])
				if isinstance(self.coords[entity_queue[0].targetpos], Wall): #prevent bouncing between walls forever
					entity_queue.pop(0)
				continue

			all_targetpos = {entity.targetpos:[] for entity in self.entities}
			for entity in self.entities:
				all_targetpos[entity.targetpos].append(entity)
			if len(all_targetpos[target]) > 1:
				newspeeds = []
				for entity in all_targetpos[target]:
					newspeed = [0,0]
					xtick, ytick = False, False
					for targetentity in all_targetpos[target]:
						if entity.deltas != targetentity.deltas:
							entity_queue.append(targetentity)
							if entity.deltas[0] != targetentity.deltas[0]:
								newspeed[0] += targetentity.speed[0]
								xtick = True
							if entity.deltas[1] != targetentity.deltas[1]:
								newspeed[1] += targetentity.speed[1]
								ytick = True
					if not xtick:
						newspeed[0] = entity.speed[0]
					if not ytick:
						newspeed[1] = entity.speed[1]
					newspeeds.append(newspeed)
				for i, entity in enumerate(all_targetpos[target]):
					entity.speed = newspeeds[i]
					self.updateDeltas(entity)
					self.updateTargetPos(entity)
				entity_queue.pop(0)

			elif isinstance(self.coords[target], BouncyEntity) and (entity_queue[0].pos != target) and (self.coords[target].deltas == [0,0] or self.coords[target].targetpos == entity_queue[0].pos):
				entity_queue[0].speed, self.coords[target].speed = self.coords[target].speed, entity_queue[0].speed
				self.updateDeltas(entity_queue[0])
				self.updateDeltas(self.coords[target])
				self.updateTargetPos(entity_queue[0])
				self.updateTargetPos(self.coords[target])
				entity_queue.append(self.coords[target])
				entity_queue.pop(0)
				entity_queue = sorted(entity_queue, key=lambda x: (x.energy[0]+x.energy[1])/2)
				continue
			
			
			else:
				entity_queue.pop(0)
				continue
	
		
	
	def updateDeltas(self, entity):
		entity.deltas = [entity.speed[0]//(abs(entity.speed[0]) or 1), entity.speed[1]//(abs(entity.speed[1]) or 1)]
	def updateTargetPos(self, entity):
		entity.targetpos = (entity.pos[0]+entity.deltas[0],entity.pos[1]+entity.deltas[1])


	def updateEntities(self):
		for entity in self.entities:
			entity.energy[0] += abs(entity.speed[0])
			entity.energy[1] += abs(entity.speed[1])
			if entity.energy[0] >= 100:
				entity.deltas[0] = entity.speed[0]//(abs(entity.speed[0]) or 1)
				entity.energy[0] -= 100
			else:
				entity.deltas[0] = 0
			if entity.energy[1] >= 100:
				entity.deltas[1] = entity.speed[1]//(abs(entity.speed[1]) or 1)
				entity.energy[1] -= 100
			else:
				entity.deltas[1] = 0
			entity.targetpos = (entity.pos[0]+entity.deltas[0],entity.pos[1]+entity.deltas[1])
		
		self.evalImpact()

		for _ in range(2): #need to do it twice to draw entities that go where another entity was
			for entity in self.entities:
				if self.coords[entity.targetpos] == ' ':
					self.coords[entity.pos] = ' '
					self.coords[entity.targetpos] = entity
					entity.pos = entity.targetpos 



	def bounceLoop(self, clockspeed=0.02, row_offset=0): 
		print(sc.hide_cursor)
		rows_full=self.rows+row_offset#+1
		for _ in range(1000): #Turn this into a while true loop with a break condition
			sleep(clockspeed)
			self.printGrid(rows_full)
			self.updateEntities()
			#input(f'{self.entities[0].speed} {self.entities[0].deltas} {self.entities[0].energy} - {self.entities[1].speed} {self.entities[1].deltas} {self.entities[1].energy}')
			

class BouncyEntity():
	def __init__(self, symbol, solidtype='bouncy', elasticity=100, fgcolor='white', bgcolor='default', speed=None):
		self.symbol=wrapColor(symbol, fgcolor, bgcolor)
		self.solidtype=solidtype
		self.elasticity=elasticity
		self.speed = speed or [randint(-100,100),randint(-100,100)]
		self.energy=[0,0]
		self.deltas=[0,0]
		self.pos=None
		self.targetpos=None

class Wall():
	def __init__(self, symbol='#', solidtype='immobile', elasticity=100, fgcolor='white', bgcolor='default'):
		self.symbol=wrapColor(symbol, fgcolor, bgcolor)
		self.solidtype=solidtype
		self.elasticity=elasticity
		

def wrapColor(string, fore='white', back='default'):
	if fore == back and not any([clr == 'rand' for clr in [fore,back]]):
		raise Exception("Fore and Back color cannot be equal.")
	fgcolors={'yellow':fg.yellow,'red':fg.red,'blue':fg.blue,'green':fg.green,'cyan':fg.cyan,'white':'','black':fg.lightblack,'magenta':fg.magenta}
	bgcolors={'yellow':bg.yellow,'red':bg.red,'blue':bg.blue,'green':bg.green,'cyan':bg.cyan,'white':bg.white,'black':bg.lightblack,'magenta':bg.magenta,'default':''}
	f_color, bg_color = fore, back
	while f_color in ['rand', bg_color]:
		f_color = choice(list(fgcolors.keys()))
	while bg_color in ['rand', f_color]:
		bg_color = choice(list(bgcolors.keys()))
	wrapped_string = fgcolors[f_color]+bgcolors[bg_color]+string+fx.default
	return wrapped_string



if __name__ == '__main__':
	cls()
	import ctypes, os
	os.system(f'title BouncyBounce v{version}')
	user32 = ctypes.WinDLL('user32')
	SW_MAXIMISE = 3
	hWnd = user32.GetForegroundWindow()
	user32.ShowWindow(hWnd, SW_MAXIMISE)
	###############################################

	
	'''
	#Two horizontal collides and two diagonal collides. Diagonal and horizontal meets at corner. 
	a = BouncyGrid(50,50)
	a.addEntity('@', pos=(1,2), speed=[0,100])
	a.addEntity('@', pos=(1,10), speed=[0,-50])
	a.addEntity('@', pos=(1,1), speed=[100,100])
	a.addEntity('@', pos=(48,48), speed=[-100,-100])
	'''
	
	'''
	#Two horizontal collides with stationary at same time, opposite directions.
	a = BouncyGrid(50,51)
	a.addEntity('@', pos=(1,1), speed=[0,100])
	a.addEntity('@', pos=(1,25), speed=[0,0])
	a.addEntity('@', pos=(1,49), speed=[0,-100])
	'''

	'''
	#Two horizontal collides with two stationaries at same time, opposite directions.
	a = BouncyGrid(50,50)
	a.addEntity('@', pos=(1,1), speed=[0,100])
	a.addEntity('@', pos=(1,24), speed=[0,0])
	a.addEntity('@', pos=(1,25), speed=[0,0])
	a.addEntity('@', pos=(1,48), speed=[0,-100])
	'''
	
	'''
	#2 entities try to go to same space
	a = BouncyGrid(50,51)
	a.addEntity('@', pos=(17,1), speed=[0,100])
	a.addEntity('@', pos=(1,49), speed=[-50,-50])
	'''
	
	'''
	#3 entities try to go to same space
	a = BouncyGrid(60,51)
	a.addEntity('@', pos=(17,1), speed=[0,100])
	a.addEntity('@', pos=(1,49), speed=[-50,-50])
	a.addEntity('@', pos=(49,33), speed=[-100,0])
	'''

	'''
	#entity moves into space of an entity that is moving out of that space.
	a = BouncyGrid(50,50)
	a.addEntity('@', pos=(5,5), speed=[0,100])
	a.addEntity('@', pos=(5,6), speed=[100,100])
	'''
	
	'''
	#two entities move in line at same pace and the first collides with another
	a = BouncyGrid(50,50)
	a.addEntity('@', pos=(5,5), speed=[0,100])
	a.addEntity('@', pos=(5,10), speed=[0,-50])
	a.addEntity('@', pos=(5,11), speed=[0,-50])
	'''

	'''
	#two collide with stationary but not from totally opposite directions. 
	a = BouncyGrid(50,51)
	a.addEntity('@', pos=(10,5), speed=[0,100])
	a.addEntity('@', pos=(15,15), speed=[-100,-100])
	a.addEntity('@', pos=(10,10), speed=[0,0])
	'''
	
	
	#random multiple entities
	a = BouncyGrid()
	for _ in range(50):
		a.addEntity('@')
	
	
	
	#try to think of a way to make animation more smooth
	

	a.bounceLoop()
	input('')
