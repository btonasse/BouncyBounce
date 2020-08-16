version = '1.2'
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
		for x in range(self.rows):
			for y in range(self.cols):
				if x == 0 or x == self.rows-1 or y == 0 or y == self.cols-1:
					self.coords[(x,y)] = '#'
				else:
					self.coords[(x,y)] = ' '

	def printGrid(self, rows_full):
		print("\033[F"*rows_full, end='')
		grid = ''
		for x in range(self.rows):
			line = '\n'
			for y in range(self.cols):
				if isinstance(self.coords[(x,y)], BouncyEntity):
					line += self.coords[(x,y)].symbol
				else:
					line += self.coords[(x,y)]
			grid += line
		print(grid, end='')
		return grid

	def addEntities(self, symbol, fore='rand', back='default', pos='rand', speed=None, howmany=1):
		if pos != 'rand':
			howmany = 1
		for _ in range(howmany):
			newpos = ''
			if pos == 'rand':
				while not newpos or self.coords[newpos] != ' ': 
					newpos = (randint(1,self.rows-1),randint(1,self.cols-1))
			elif self.coords[pos] != ' ':
				raise Exception(f"Cannot add entity to {pos}")
			else:
				newpos = pos
			self.entities.append(BouncyEntity(symbol, fgcolor=fore, bgcolor=back, speed=speed))
			self.coords[(newpos)] = self.entities[-1]
			self.entities[-1].pos = newpos

	def findSolids(self, coord, deltas):
		bouncex, bouncey = False, False
		target = self.coords[(coord[0]+deltas[0],coord[1]+deltas[1])]
		if target == ' ' or (isinstance(target, BouncyEntity) and coord == target.pos):
			return bouncex, bouncey, None
		else:
			if self.coords[(coord[0],coord[1]+deltas[1])] == ' ' or self.coords[(coord[0]+deltas[0],coord[1])] != ' ':
				bouncex = True
			if self.coords[(coord[0]+deltas[0],coord[1])] == ' ' or self.coords[(coord[0],coord[1]+deltas[1])] != ' ':
				bouncey = True
			if isinstance(target, BouncyEntity):
				solidtype = target.symbol
			else:
				solidtype = '#'
			return bouncex, bouncey, solidtype

	def checkDirectBounce(self, entity):
		wallx, wally, solidtype = self.findSolids(entity.pos, entity.deltas)
		if solidtype == '#':
			if wallx:
				entity.deltas[0] *= -1
				entity.speed[0] *= -1
			if wally:
				entity.deltas[1] *= -1
				entity.speed[1] *= -1
			return True
		elif solidtype:
			impacted = self.coords[(entity.pos[0]+entity.deltas[0],entity.pos[1]+entity.deltas[1])]
			if wallx:
				entity.deltas[0] *= -1
				entity.speed[0], impacted.speed[0] = impacted.speed[0], entity.speed[0]
			if wally:
				entity.deltas[1] *= -1
				entity.speed[1], impacted.speed[1] = impacted.speed[1], entity.speed[1]
			return True

	def bounceLoop(self, clockspeed=0.02, row_offset=0): 
		print(sc.hide_cursor)
		rows_full=self.rows+row_offset
		for _ in range(1000): #Turn this into a while true loop with a break condition
			sleep(clockspeed)
			self.printGrid(rows_full)
			#input('')
			for entity in self.entities:
				entity.xenergy += entity.speed[0]
				if entity.xenergy >= 100:
					entity.deltas[0] = 1
					entity.xenergy -= 100
				elif entity.xenergy <= -100:
					entity.deltas[0] = -1
					entity.xenergy += 100
				else:
					entity.deltas[0] = 0
				entity.yenergy += entity.speed[1]
				if entity.yenergy >= 100:
					entity.deltas[1] = 1
					entity.yenergy -= 100
				elif entity.yenergy <= -100:
					entity.deltas[1] = -1
					entity.yenergy += 100
				else:
					entity.deltas[1] = 0
				
				for _ in range(2): #this only works for one tile in the middle. energy is not transferred when there are two or more
					directbounce = self.checkDirectBounce(entity)
				entity.newpos = (entity.pos[0]+entity.deltas[0], entity.pos[1]+entity.deltas[1]) #new position before entity collision


			newpositions = [entity.newpos for entity in self.entities]
			while any([newpositions.count(newposition) > 1 for newposition in set(newpositions)]): #check why speed and direction is sometimes bugged #this checks if two or more entities want to move in the same direction and makes them bounce
				for newposition in set(newpositions):
					if newpositions.count(newposition) > 1:
						indexes_to_exchange = [i for i, value in enumerate(newpositions) if value == newposition]
						involved_entities = [self.entities[ind] for ind in indexes_to_exchange]
						newspeeds = []
						for entity in involved_entities: 
							newdelta = [0,0]
							newspeed = [0,0]
							xtick, ytick = False, False
							for ind in indexes_to_exchange:
								if entity.deltas[0] != self.entities[ind].deltas[0]:
									newspeed[0] += self.entities[ind].speed[0]
									xtick = True
								if entity.deltas[1] != self.entities[ind].deltas[1]:
									newspeed[1] += self.entities[ind].speed[1]
									ytick = True
							if not xtick:
								newspeed[0] = entity.speed[0]
							if not ytick:
								newspeed[1] = entity.speed[1]
							if newspeed[0] > 0:
								newdelta[0] = 1
							elif newspeed[0] < 0:
								newdelta[0] = -1
							else:
								newdelta[0] = 0
							if newspeed[1] > 0:
								newdelta[1] = 1
							elif newspeed[1] < 0:
								newdelta[1] = -1
							else:
								newdelta[1] = 0
							newspeeds.append((newdelta,newspeed))
						for i, entity in enumerate(involved_entities):
							entity.deltas = newspeeds[i][0]
							entity.speed = newspeeds[i][1]
							for _ in range(2):
								directbounce = self.checkDirectBounce(entity)
							entity.newpos = (entity.pos[0]+entity.deltas[0], entity.pos[1]+entity.deltas[1])
				newpositions = [entity.newpos for entity in self.entities]
			for entity in self.entities:
				if self.coords[entity.newpos] == ' ': 
					self.coords[entity.pos] = ' '
					self.coords[entity.newpos] = entity
					entity.pos = entity.newpos

class BouncyEntity():
	def __init__(self, symbol, fgcolor='white', bgcolor='default', speed=None):
		self.symbol=wrapColor(symbol, fgcolor, bgcolor)
		self.speed = speed or [randint(-100,100),randint(-100,100)]
		self.xenergy=0
		self.yenergy=0
		self.pos=None
		self.newpos=None
		self.deltas=[0,0]

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
	a = BouncyGrid(50,50)
	a.addEntities('@', pos=(1,2), speed=[0,100])
	a.addEntities('@', pos=(1,10), speed=[0,-50])
	a.addEntities('@', pos=(1,1), speed=[100,100])
	a.addEntities('@', pos=(48,48), speed=[-100,-100])
	'''
	
	'''
	a = BouncyGrid(50,51)
	a.addEntities('@', pos=(1,1), speed=[0,100])
	a.addEntities('@', pos=(1,25), speed=[0,0])
	a.addEntities('@', pos=(1,49), speed=[0,-100])
	'''

	'''
	a = BouncyGrid(50,50)
	a.addEntities('@', pos=(1,1), speed=[0,100])
	a.addEntities('@', pos=(1,24), speed=[0,0])
	a.addEntities('@', pos=(1,25), speed=[0,0])
	a.addEntities('@', pos=(1,48), speed=[0,-100])
	'''


	
	a = BouncyGrid()
	a.addEntities('@', howmany=50)
	



	a.bounceLoop()
	input('')
