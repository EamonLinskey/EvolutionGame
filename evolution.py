import pygame
import random
import time
import math
import statistics

BASE_CREATURE_HEIGHT = 10
BASE_SPEED = 5
BASE_VISION = 50
BASE_MINFOOD = 2
scores = {"blue":0, "green":0, "red":0}
dead = {"blue":0, "green":0, "red":0}
roundsCount = 0
startingNumber = 10

displayWidth = 800
displayHeight = 600
displaySize = (displayWidth, displayHeight)
gameName = "Eamon's game"
fps = 60

black = (0,0,0)
white = (255,255,255)
red = (255,0,0)
green = (0,255,0)
blue = (0,0, 255)
grey = (220,220,220)



pygame.init()

gameDisplay = pygame.display.set_mode(displaySize)
pygame.display.set_caption(gameName)

class Target:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Gene:
    def __init__(self, name, geneType, dominance, effect):
        self.name = name
        self.geneType = geneType
        # should be a value from 0 to 1 to detemine dominance
        self.dominance = dominance
        # should be  a dict of functions that modify traits 
        self.effect = effect

def modifyAttribute(amount, attribute):
    def f(crt):
        attributes = {"speed": "movement", "vision": "vision", "metabolism": "minFood"}
        # if attribute == "vision":
        #     print(crt.vision)
        #     print(attributes[attribute])
        setattr(crt, attributes[attribute], (getattr(crt, attributes[attribute]) + amount)) 
        # if attribute == "vision":
        #     print(crt.vision)
        #print(crt.movement)
        return crt
    return f

class DNA: 
    # Each gene should have 2 allels. So they should be list of length 2
    def __init__(self, speedGene, sightGene, motabolismGene):
        self.speedGene = speedGene
        self.sightGene = sightGene
        self.motabolismGene = motabolismGene


longLegs = Gene("longLegs", "speedGene", 1, modifyAttribute(5, "speed"))
shortLegs = Gene("shortLegs", "speedGene", 0, modifyAttribute(-2, "speed"))
medLegs = Gene("shortLegs", "speedGene", .5, modifyAttribute(0, "speed"))

hawkEyes = Gene("hawkEyes", "sightGene", 1, modifyAttribute(75, "vision"))
wormEyes = Gene("wormEyes", "sightGene", 0, modifyAttribute(-25, "vision"))
normalEyes = Gene("normalEyes", "sightGene", 0.5, modifyAttribute(0, "vision"))

FastMeta = Gene("FastMeta", "motabolismGene", 1, modifyAttribute(1, "metabolism"))
slowMeta = Gene("slowMeta", "motabolismGene", 0, modifyAttribute(-1, "metabolism"))
medMeta = Gene("medMeta", "motabolismGene", 0.5, modifyAttribute(0, "metabolism"))

BaseGreenDNA = DNA([longLegs, longLegs], [wormEyes, wormEyes], [medMeta, medMeta])
BaseBlueDNA = DNA([medLegs, medLegs], [normalEyes, normalEyes], [medMeta, medMeta])
BaseRedDNA = DNA([shortLegs, shortLegs], [hawkEyes, hawkEyes], [medMeta, medMeta])





class Creature:
    counter = 0
    def __init__(self, x, y, width, height, color, species, DNA):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.movement = BASE_SPEED
        self.nextMove = math.radians(random.randint(0,360))
        self.numEaten = 0
        self.id = Creature.counter
        self.vision = BASE_VISION
        self.species = species
        self.surface = pygame.Surface((width, height))
        self.prevTarget = Target(0, 0)
        self.minFood = BASE_MINFOOD
        self.DNA = DNA
        Creature.counter += 1

        #print(f"{self.color}'s angle is {self.nextMove}")
    #def listAttributes():
        #return (self.x, self.y, self.width, self.height, self.color, self.movement)

class Food:
    counter = 0
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.id = Food.counter
        Food.counter += 1

def drawVision(c):
    pygame.draw.circle(gameDisplay, black, [int(c.x +c.width/2),int(c.y +c.height/2)], c.vision+1)
    pygame.draw.circle(gameDisplay, grey, [int(c.x +c.width/2),int(c.y +c.height/2)], c.vision)

def drawCreature(c): 
    pygame.draw.rect(gameDisplay, c.color, [c.x,c.y,c.width,c.height])
    
    
def drawFood(f):
    pygame.draw.rect(gameDisplay, black, [f.x,f.y,f.width,f.height])



regularMove = 5
smallMove = 3
bigMove = 10

regularVis = 50
smallVis = 25
bigVis = 100

leftBound = 0
upperBound = 0
rightBound = displayWidth
lowerBound = displayHeight

def distance(p0, p1):
    return math.sqrt((p0.x - p1.x)**2 + (p0.y - p1.y)**2)

def angle(p0, p1):
    try:
        #print(f'the angle is: {math.degrees(math.atan((p0.y-p1.y)/(p0.x-p1.x)))}')
        if p0.x < p1.x:
            return math.atan((p0.y-p1.y)/(p0.x-p1.x)) - math.pi
        else:
            return math.atan((p0.y-p1.y)/(p0.x-p1.x))
    except:
        # limit as arctan approaches infinity
        if p0.y > p1.y:
            return math.radians(90)
        else:
            return math.radians(-90)

def selectTarget(crt, foods):
    targets = [(Target(food.x, food.y), distance(food, crt), angle(food, crt)) for food in foods if food.x in range(crt.x-crt.vision, 
                        crt.x+crt.vision) and food.y in range(crt.y-crt.vision, 
                        crt.y+crt.vision)]
    if len(targets) > 0:
        closestTarget =  min(targets, key = lambda t: t[1])
        crt.prevTarget = closestTarget[0]
    else:
        x = set(range(getBounds(crt)["xleft"]-crt.width, getBounds(crt)["xright"]+crt.width))
        y = set(range(getBounds(crt)["yleft"]-crt.height, getBounds(crt)["yright"]+crt.height))

        if crt.prevTarget.x in x and crt.prevTarget.y in y:
            crt.prevTarget = Target(random.randint(0,displayWidth - crt.width), random.randint(0, displayHeight - crt.height))

        closestTarget = [crt.prevTarget, distance(crt.prevTarget, crt), angle(crt.prevTarget, crt)]

    return closestTarget

def updateIntention(crt, foods):
    target = selectTarget(crt, foods)
    #print(target)
    #print(len(target))
    crt.nextMove = target[2]
    
    #print(math.degrees(crt.nextMove))
    #crt.nextMove = math.radians(360-45)
    
    
    #print(math.degrees(closestFood[2]))# = math.degrees(closestFood[2])
    #print(closestFood)
        

def move(creature):
    xMovement = round((math.cos(creature.nextMove) * creature.movement), 2)
    yMovement = round((math.sin(creature.nextMove) * creature.movement), 2)
    #print(int(yMovement))
    creature.x = int(statistics.median([leftBound, rightBound - creature.width, 
                                    creature.x + xMovement]))
    creature.y = int(statistics.median([upperBound, 
                                    lowerBound - creature.height, 
                                    creature.y + yMovement]))
    
    return

def getBounds(obj):
    return {"xleft":int(obj.x +obj.width/2), 
            "xright":int(obj.x +(3*obj.width)/2),
            "yleft":int(obj.y +obj.height/2), 
            "yright":int(obj.y +(3*obj.height)/2)}

def checkFoodCollisions(crt, foods):
    # Iterate through copy of list so that we can alter the inital list without 
    # a new loop
    for food in foods[:]:
        if food != crt:
            # Checks for overlaps bewtween objects
    
            
            x = set(range(getBounds(food)["xleft"], getBounds(food)["xright"]))
            y = set(range(getBounds(food)["yleft"], getBounds(food)["yright"]))
            #print(crt.x, crt.y)
            if (x.intersection(range(getBounds(crt)["xleft"], getBounds(crt)["xright"]))
            and y.intersection((range(getBounds(crt)["yleft"], getBounds(crt)["yright"])))):
                #print(f'Collision between {type(food).__name__} {food.id} and {type(crt).__name__} {crt.id}')
                # If an object is collided with by a creature it dissapers 
                # (Think eaten, drunk, consumed etc.)
                foods.remove(food)
                crt.numEaten += 1
    return foods

def populateFood(number):
    foods = []
    for i in range(number):
        x = random.randint(0, displayWidth - BASE_CREATURE_HEIGHT)
        y = random.randint(0, displayHeight - BASE_CREATURE_HEIGHT)

        foods.append(Food(x, y, 10,10))
    return foods

def populateCreatures(popList):
    creatures = []
    DNAAtributes = [a for a in dir(BaseBlueDNA) if not a.startswith('__') and not callable(getattr(BaseBlueDNA,a))]
    
    for pair in popList:
        baseDNA = pair["base"]
        #print(pair["num"])
        for i in range(pair["num"]):
            #print(i)
            baseCreature = Creature(random.randint(0,displayWidth - 10), random.randint(0,displayHeight - 10),10,10, pair["color"], pair["species"], baseDNA)
            for attribute in DNAAtributes:
                genes = getattr(baseCreature.DNA, attribute)
                dominant = max(genes, key = lambda t: t.dominance)
                #print(dominant.effect(baseCreature))
                baseCreature = dominant.effect(baseCreature)
                
            creatures.append(baseCreature)

    
    # creature1 = Creature(400,400,10,10,blue, regularMove, regularVis, "Blue")
    # creature2 = Creature(300,120,10,10,red, smallMove, bigVis, "Red")
    # creature3 = Creature(500,130,10,10,green, bigMove, smallVis, "Green")
    # creatures = [creature1, creature2, creature3]
    
    
    return creatures

def gameLoop(creatures):
    # print("------------------")
    # print(creatures[0].movement)
    # longLegs.effect(creatures[0])
    # print(creatures[0].movement)
    # print("------------------")
    clock = pygame.time.Clock()
    numLoops = 0
    

    
    foods = populateFood(60)

    gameExit = False
    paused = False
    lastHovered = None
    roundStartTime = time.time()

    while not gameExit:

        for event in pygame.event.get():
            #print(event)
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN and event.key == 32:
                paused = not paused
                lastHovered = None
        if paused:
            for creature in creatures:
                rect = pygame.Rect(creature.x, creature.y, creature.width, creature.height)
                if rect.collidepoint(pygame.mouse.get_pos()) and lastHovered != creature:
                    lastHovered = creature
                    print(f"{creature.species} {creature.numEaten} {creature.prevTarget.x, creature.prevTarget.y}")

        if len(foods) == 0 or len(creatures) == 0 or numLoops > (1000):
            global roundsCount
            global scores
            global dead
            numLoops = 0
            for creature in creatures[:]:
                scores[creature.species] += creature.numEaten
                if creature.numEaten < creature.minFood:
                    print(f'{creature.species} number {creature.id} died from hunger')
                    creatures.remove(creature)
                    dead[creature.species] += 1
                creature.numEaten = 0
            roundsCount += 1
            print(f'ROUND COMPLETE: {roundsCount}')
            print(f'Remaining Alive:')
            print(f'Red: {startingNumber - dead["red"]}')
            print(f'Blue: {startingNumber - dead["blue"]}')
            print(f'Green: {startingNumber - dead["green"]}')
            if roundsCount < 100:
                gameLoop(creatures)
                gameExit = True
            else:
                gameExit = True



        if not paused:
            numLoops += 1
            
            gameDisplay.fill(white)


            for creature in creatures:
                foods = checkFoodCollisions(creature, foods)
                updateIntention(creature, foods) 
                move(creature)
                drawVision(creature)
            for creature in creatures:
                drawCreature(creature)
            #dstart = time.time()
            for food in foods:               
                drawFood(food)
            pygame.display.update()
        
            clock.tick(fps)

blueSpecies = {"num": startingNumber, "base": BaseBlueDNA, "color": blue, "species": "blue"}
redSpecies = {"num": startingNumber, "base": BaseRedDNA, "color": red, "species": "red"}
greenSpecies = {"num": startingNumber, "base": BaseGreenDNA, "color": green, "species": "green"}
creatures = populateCreatures([blueSpecies, redSpecies, greenSpecies])
gameLoop(creatures)
pygame.quit()
quit()
    