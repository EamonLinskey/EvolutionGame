# import modules
import pygame
import random
import time
import math
import statistics
import copy

# initialize constants Some may be removed later
BASE_CREATURE_HEIGHT = 10
BASE_CREATURE_WIDTH = 10
BASE_SPEED = 5
BASE_VISION = 50
BASE_MINFOOD = 2
BASE_NUMCHILD = 2
roundsCount = 0
startingNumber = 2

displayWidth = 800
displayHeight = 600
displaySize = (displayWidth, displayHeight)
leftBound = 0
upperBound = 0
rightBound = displayWidth
lowerBound = displayHeight
gameName = "Evolution Model"
fps = 60

# Define rgb colors for pygame drawing
black = (0,0,0)
white = (255,255,255)
red = (255,0,0)
green = (0,255,0)
blue = (0,0, 255)
grey = (220,220,220)
yellow = (255,255,0)
orange = (255,135,0)


# initialize pygame
pygame.init()
gameDisplay = pygame.display.set_mode(displaySize)
pygame.display.set_caption(gameName)

# Define Classes

# Target is a class used for points on the screen such as food
class Target:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Class used for individual gene allels. Includes genes relative dominance and 
# it has an 'effect' which is a function that changes the value of creature 
# object attributes
class Gene:
    def __init__(self, name, geneType, dominance, effect):
        self.name = name
        self.geneType = geneType
        # should be a value from 0 to 1 to detemine dominance
        self.dominance = dominance
        # should be  a dict of functions that modify traits 
        self.effect = effect

# Class mad up of many genes. Each gene currently is added by hand by appending 
# to the class
class DNA: 
    # Each gene should have 2 allels. So they should be list of length 2
    def __init__(self, speedGene, sightGene, motabolismGene, dietGene, 
                    riskGene):
        self.speedGene = speedGene
        self.sightGene = sightGene
        self.motabolismGene = motabolismGene
        self.dietGene = dietGene
        self.riskGene = riskGene

# Defines Creature object. Properties set to constants can be changed once more
# genes are defined
class Creature:
    counter = 0
    def __init__(self, width, height, color, species, DNA):
        self.x = random.randint(0, displayWidth - width)
        self.y = random.randint(0, displayHeight - height)
        self.width = width
        self.height = height
        self.color = color
        self.species = species
        self.nextMove = math.radians(random.randint(0,360))
        self.prevTarget = Target(random.randint(0, displayWidth - width),
                                 random.randint(0, displayHeight - height))
        self.id = Creature.counter
        self.numEaten = 0
        self.DNA = DNA
        self.vision = BASE_VISION
        self.minFood = BASE_MINFOOD
        self.numChild = BASE_NUMCHILD
        self.movement = BASE_SPEED
        self.diet = 0.5
        self.risk = 0.5
        self.feelsFull = BASE_MINFOOD + 1
        self.reproCapacity = 2
        Creature.counter += 1

    # function for iterating id's called only when a copy of a creature is 
    # created for breeding
    def iterateId(self):
        Creature.counter += 1
        self.id = Creature.counter

    # Randomized movement and position. Useful for positioning after breeding
    def randomizeMoveElements(self):
        self.nextMove = math.radians(random.randint(0,360))
        self.x = random.randint(0, displayWidth - self.width)
        self.y = random.randint(0, displayHeight - self.height)
        self.prevTarget = Target(random.randint(0, displayWidth - self.width), 
                                random.randint(0, displayHeight - self.height))

# Class for food that creatures eat. Each food need a unique id
class Food:
    counter = 0
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.id = Food.counter
        Food.counter += 1

# Curried function that allows any attribute to be changed when a creature param 
# is used. Attributes key must be manually edited each time a new gene is added 
# to make sure the correct creature attribute is updated
def modifyAttribute(amount, attribute):
    def f(crt):
        attributes = {"speed": "movement", "vision": "vision", 
                        "metabolism": "minFood", "diet": "diet", 
                        "fullness": "feelsFull", "risk": "risk"}
        setattr(crt, attributes[attribute], 
                (getattr(crt, attributes[attribute]) + amount)) 
        return crt
    return f


# Draws a circle around creture to represent tit field of view. It assumes 
# circular FOV
def drawVision(c):
    pygame.draw.circle(gameDisplay, black, [int(c.x +c.width/2),
                                            int(c.y +c.height/2)], c.vision+1)
    pygame.draw.circle(gameDisplay, grey, [int(c.x +c.width/2),
                                            int(c.y +c.height/2)], c.vision)

# Draws Creature
def drawCreature(c): 
    pygame.draw.rect(gameDisplay, c.color, [c.x,c.y,c.width,c.height])
    
# Draws Food
def drawFood(f):
    pygame.draw.rect(gameDisplay, black, [f.x,f.y,f.width,f.height])

# returns distance between two points
def distance(p0, p1):
    return math.sqrt((p0.x - p1.x)**2 + (p0.y - p1.y)**2)

# Returnd the angle the p0 must move at relative to the x-axis to get to point y 
# in a straight line in radians
def angle(p0, p1):
    try:
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

# Returns the information on the target the creature should appraoch next 
def selectTarget(crt, foods, creatures):
    # Intitalize empy lists
    targets = []
    avoids = []

    # generates list of targets that the creature can "see"
    # diet is a value from 0.0 to 1.0
    # less than 0.5 means herbavore only, greter than 0.5 means 
    # predator only. 0.5 can eat both
    # creature only chases food if it is not full
    if crt.numEaten < crt.feelsFull:
        if crt.diet <= 0.5:
            for food in foods:
                if (food.x in range(crt.x-crt.vision, crt.x+crt.vision) and 
                food.y in range(crt.y-crt.vision, crt.y+crt.vision)):
                    targets.append((Target(food.x, food.y), distance(food, crt), 
                                    angle(food, crt)))
    
    # Both generaters a lsit of prey for predators and a list of predators to 
    # avoid of the prey
    for tarCrt in creatures:
        # prevents canabalism
        if tarCrt.species != crt.species:
            # Checks if visible
            if (tarCrt.x in range(crt.x-crt.vision, crt.x+crt.vision) and 
            tarCrt.y in range(crt.y-crt.vision, crt.y+crt.vision)):
                # Checks if hungry and able to eat veggies
                if crt.diet >= 0.5 and crt.numEaten < crt.feelsFull:
                    targets.append((Target(tarCrt.x, tarCrt.y), 
                                distance(tarCrt, crt), angle(tarCrt, crt)))
                # Checks if predator nearby and if creature is risk averse
                if crt.risk <= 0.5 and tarCrt.diet >= 0.5:

                    # Selects a point at in the opposite direction of the threat
                    # using the creature's max movement
                    x = round(crt.x - 
                                (math.sin(angle(tarCrt, crt)))*crt.movement)
                    y = round(crt.y - 
                                (math.cos(angle(tarCrt, crt)))*crt.movement)
                    avoidTar = Target(x, y)

                    avoids.append((avoidTar, distance(tarCrt, crt), 
                                angle(tarCrt, crt) + math.pi))

    # filters targets to return closest
    closestTar = None
    closestAvoids = None

    # gets closest desireale target
    if len(targets) > 0:
        closestTar = min(targets, key = lambda t: t[1])
        crt.prevTarget = closestTar[0]

    # gets closests threat
    if len(avoids) > 0:
        closestAvoids =  min(avoids, key = lambda t: t[1])
    
    # checks if predator should be avoided with high priority
    if crt.risk < 0.5 and closestAvoids != None:
        closestTar =  closestAvoids
        crt.prevTarget = closestTar[0]

    # gives partially risk adverse creatures the chance to avoid predators but 
    # they will still be tempeted by food if it is closer then the predator
    elif crt.risk == 0.5 and closestAvoids != None: 
        closestTar = min([closestAvoids, closestTar], key = lambda t: t[1])
        crt.prevTarget = closestTar[0]
        
    

    if len(targets) == 0 and len(avoids) == 0:
        # gets location of creature and save it as a set
        x = set(range(getBounds(crt)["xleft"]-crt.width, 
                        getBounds(crt)["xright"]+crt.width))
        y = set(range(getBounds(crt)["yleft"]-crt.height, 
                        getBounds(crt)["yright"]+crt.height))
        # checks if the creature is already on target 
        if crt.prevTarget.x in x and crt.prevTarget.y in y:
             # set a random target within the bounds
            crt.prevTarget = Target(random.randint(0,displayWidth - crt.width), 
                                random.randint(0, displayHeight - crt.height))
            
        
        closestTar = [crt.prevTarget, distance(crt.prevTarget, crt), 
                            angle(crt.prevTarget, crt)]
                            
    return closestTar

# updates creatures move
def updateIntention(crt, foods, creatures):
    target = selectTarget(crt, foods, creatures)
    crt.nextMove = target[2]
        

def move(creature):
    # Uses trig to clculate the vector segements needed to move the correct 
    # direction
    xMovement = round((math.cos(creature.nextMove) * creature.movement), 2)
    yMovement = round((math.sin(creature.nextMove) * creature.movement), 2)

    # updates creatures postion. stat.medien prevents the creature from moving
    # past the bounds of the screen
    creature.x = int(statistics.median([leftBound, rightBound - creature.width, 
                                    creature.x + xMovement]))
    creature.y = int(statistics.median([upperBound, 
                                    lowerBound - creature.height, 
                                    creature.y + yMovement]))

# used to get the bounds of object
def getBounds(obj):
    return {"xleft":int(obj.x +obj.width/2), 
            "xright":int(obj.x +(3*obj.width)/2),
            "yleft":int(obj.y +obj.height/2), 
            "yright":int(obj.y +(3*obj.height)/2)}

# Removes any food that is touched by a creature
def checkCollisions(crt, foods):
    # Iterate through copy of list so that we can alter the inital list without 
    # a new loop
    for food in foods[:]:
        if food != crt and (crt.numEaten < crt.feelsFull):
            # Checks for overlaps bewtween objects
            x = set(range(getBounds(food)["xleft"], getBounds(food)["xright"]))
            y = set(range(getBounds(food)["yleft"], getBounds(food)["yright"]))

            if ((isinstance(food, Food) and crt.diet <= 0.5) or 
            ((isinstance(food, Creature) and (crt.diet >= 0.5 and 
            food.species != crt.species)))):
                
                if (x.intersection(range(getBounds(crt)["xleft"], 
                getBounds(crt)["xright"])) and 
                y.intersection((range(getBounds(crt)["yleft"], 
                getBounds(crt)["yright"])))):
                    # If an object is collided with by a creature it dissapers 
                    # (Think eaten, drunk, consumed etc.)
                    foods.remove(food)
                    crt.numEaten += 1
    return foods

# Generates food objects
def populateFood(number):
    foods = []
    for i in range(number):
        x = random.randint(0, displayWidth - BASE_CREATURE_WIDTH)
        y = random.randint(0, displayHeight - BASE_CREATURE_HEIGHT)
        foods.append(Food(x, y, 10,10))
    return foods

# Takes on allel at random from each parent for each gene
def mixParentsDNA(parentA, parentB):
    # Copy parentA's DNA (not biologically accurate but programatically 
    # convenient)
    childDNA = copy.deepcopy(parentA.DNA)
    
    for attr in DNAAtributes:
        # Get both Allels from parent A
        childGene = getattr(childDNA, attr)

        # set a random allel to a random allel from parent B
        parentBGene = copy.deepcopy(getattr(parentB.DNA, attr))
        childGene[random.randint(0,1)] = parentBGene[random.randint(0,1)]
       
    return childDNA

# Takes all creatures and a list of species
def breedCreatures(creatures, survivingSpecies):
    # Initialize new creatures
    newCreatures = []

    for species in survivingSpecies:
        # get all members of single species
        filtCrts = [crt for crt in creatures if crt.species == species]
        
        # If there are 2 or more potential mates:
        while len(filtCrts) > 1:
            # Select 2 parents at random. (Assumes no sexual selection)
            samples = random.sample(range(len(filtCrts)), 2)
            (parentA, parentB) = (filtCrts[samples[0]], filtCrts[samples[1]])

            # Get the average number of children per breeding session 
            # of the 2 parents
            numChild = round((parentA.numChild + parentB.numChild)/2)

            # Create children
            for i in range(numChild):
                # copy the template DNA of the species
                baseCreature = copy.deepcopy(TemplateDNADict[parentA.species])
                # iterate the ID so that child has new id
                baseCreature.iterateId()

                # Randomize starting position and itital movements
                baseCreature.randomizeMoveElements()

                # update creatures DNA to be a mix of the parennts
                baseCreature.DNA = mixParentsDNA(parentA, parentB)

                # loop through each gene
                for gene in DNAAtributes:
                    # find the dominant gene of each pair and apply the effect 
                    # to the creature

                    allels = getattr(baseCreature.DNA, gene)

                    # This check allows for co-dominance of different genes only
                    if (allels[0].dominance == allels[1].dominance and 
                    allels[0].name != allels[1].name):
                        for func in allels[0].effect:
                            baseCreature = func(baseCreature)

                        for func in allels[1].effect:
                            baseCreature = func(baseCreature)
                    elif allels[0].dominance > allels[1].dominance:
                        for func in allels[0].effect:
                            baseCreature = func(baseCreature)
                    else:
                        for func in allels[1].effect:
                            baseCreature = func(baseCreature)

                # Add finalized creature to list of cretures
                newCreatures.append(baseCreature)

            # initializes list of parents that has completed breeding for the 
            # round
            finishedParentsIndex = []

            # iterate parents reproductive Capacity
            for sample in samples:
                filtCrts[sample].reproCapacity -= 1
                if filtCrts[sample].reproCapacity == 0:
                    finishedParentsIndex.append(sample)

            # Delete parents that have complete breeding from list. 
            # The list is reversed to prevent messing up the index if multiple 
            # parents are deleted
            finishedParentsIndex.sort(reverse=True)
            for index in finishedParentsIndex:  
                del filtCrts[index]

            # TODO if I inted to support inter round survivals of parents i need
            # to reset their reproductive capacity or decrement a copy instead 
            # of the original
    return newCreatures

# Used to initalize  starting populations. Diffrent simulations should change 
# this function to get varied outcomes
def populateCreatures(popList):
    # initalize list
    creatures = []

    # poplist is a pretty complicated input. It is effectively a list of species 
    # dicts and baseline traits and their number
    for species in popList:
        for i in range(species["num"]):
            baseCreature = Creature(BASE_CREATURE_WIDTH,BASE_CREATURE_HEIGHT, 
                                    species["color"], species["species"], 
                                    species["base"])
            # Apply effects of the dominant genes
            for gene in DNAAtributes:
                allels = getattr(baseCreature.DNA, gene)
                dominant = max(allels, key = lambda t: t.dominance)
                for func in dominant.effect:
                    baseCreature = func(baseCreature)
                
            creatures.append(baseCreature)
    return creatures

# Checks to see if all creatures are full
def allFull(crts):
    for crt in crts:
        if crt.numEaten < crt.feelsFull:
            return False
    return True


def gameLoop(creatures, startingSpecies, foodNum):
    # Tracks population counts
    for species in startingSpecies:
        speciesCount = len([x for x in creatures if x.species == species])
        print(f'{species}: {speciesCount}')

    # Initalizes Round constants
    numLoops = 0
    gameExit = False
    paused = False
    lastHovered = None

    # initalizes clock
    clock = pygame.time.Clock()

    # Adds food to map
    foods = populateFood(foodNum)

    # declare globals
    global roundsCount
    
    # Main round loop
    while not gameExit:
        # Check for events from user
        for event in pygame.event.get():
            # Quits game and program
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            # Allows pausing with the spacebar
            if event.type == pygame.KEYDOWN and event.key == 32:
                paused = not paused
                lastHovered = None
        # Creates a hover tool that works when the game is paused
        if paused:
            # Adds rectangle on each creature that can be used to check for 
            # mouse collisions
            for crt in creatures:
                rect = pygame.Rect(crt.x, crt.y, crt.width, crt.height)
                if (rect.collidepoint(pygame.mouse.get_pos()) and 
                lastHovered != crt):
                    # saves last hover tp prevent multiple trigger on 
                    # similar events (i.e. mouse twitches)
                    lastHovered = crt

                    # Print creature information
                    print(f"{crt.species} {crt.id} has eaten", 
                        f"{crt.numEaten} foods. It is at",
                        f"{crt.x, crt.y} It is currenlty headed for" 
                        f"{crt.prevTarget.x, crt.prevTarget.y}.")
                    print(f"feelsFull: {crt.numEaten >= crt.feelsFull}")
                    print(f"Its creature next move is: {crt.nextMove}")
                    print(f"Its Risk is {crt.risk}")
                    print(f"Its Risk is {crt.risk}")
                    
                    for gene in DNAAtributes:
                        print(f'Its {gene} is ' 
                            f'{getattr(crt.DNA, gene)[0].name}', 
                            f'{getattr(crt.DNA, gene)[1].name}')
            if event.type == pygame.KEYDOWN and event.key == 13:
                numLoops = 1000
        # When all cretures are dead, or all food is gone or enough loops have 
        # happened end the current round    
        if (len(foods) == 0 or len(creatures) == 0 or numLoops > (1000) or 
        allFull(creatures)):
           
            
            # reset loop number
            numLoops = 0

            # kill any creatures that did not get enough food
            for creature in creatures[:]:
                if creature.numEaten < creature.minFood:
                    print(f'{creature.species} number {creature.id}', 
                        'died from hunger')
                    creatures.remove(creature)

                # reset creatures eaten count for later rounds
                creature.numEaten = 0

           
            
            # iterate rounds
            roundsCount += 1
            print(f'ROUND COMPLETE: {roundsCount}')
           
            if roundsCount < 100:
                # Create new cratures by breeding parents stimulating 
                # sexual reproduction
                creatures = breedCreatures(creatures, startingSpecies)

                # Run another round with new creatures
                gameLoop(creatures, startingSpecies, foodNum)
                gameExit = True
            else:
                gameExit = True

        if not paused:
            # iterate loops
            numLoops += 1
            
            # paint background
            gameDisplay.fill(white)

            # Movment logic for creatures.
            for creature in creatures[:]:
                foods = checkCollisions(creature, foods)
                if creature.diet >= 0.5:
                    creatures = checkCollisions(creature, creatures)
                
                # move creature
                updateIntention(creature, foods, creatures) 
                move(creature)
                
            
            # add vision to display
            for creature in creatures:
                drawVision(creature)

            # these loops are seperate to allow the creatures to always be above 
            # the FOV graphics
            for creature in creatures:
                drawCreature(creature)
            
            # Draw foods
            for food in foods:               
                drawFood(food)

            # update display
            pygame.display.update()
        
            #advance clock
            clock.tick(fps)

# Defines a list of genes that have specific traits. These must be added by hand
# TODO allow loading from cvd file maybe? 
longLegs = Gene("longLegs", "speedGene", 0, [modifyAttribute(5, "speed")])
shortLegs = Gene("shortLegs", "speedGene", 1, [modifyAttribute(-2, "speed")])
medLegs = Gene("shortLegs", "speedGene", .5, [])

hawkEyes = Gene("hawkEyes", "sightGene", 0, [modifyAttribute(75, "vision")])
wormEyes = Gene("wormEyes", "sightGene", 1, [modifyAttribute(-25, "vision")])
normalEyes = Gene("normalEyes", "sightGene", 0.5, [])

FastMeta = Gene("FastMeta", "motabolismGene", 0, 
                [modifyAttribute(1, "metabolism"), 
                modifyAttribute(1, "fullness")])
slowMeta = Gene("slowMeta", "motabolismGene", 1, 
                [modifyAttribute(-1, "metabolism"), 
                modifyAttribute(-1, "fullness")])
medMeta = Gene("medMeta", "motabolismGene", 0.5, [])

predator = Gene("meatEater", "sightGene", 1, [modifyAttribute(0.25, "diet")])
herbavore = Gene("leafEater", "sightGene", 1, [modifyAttribute(-0.25, "diet")])

skiddish = Gene("scared", "riskGene", 1, [modifyAttribute(-0.25, "risk")])
oblivious = Gene("oblivious", "riskGene", 1, [modifyAttribute(0.25, "risk")])

# Create the base DNA for each species type as well as an overall DNA template
BaseAllDNA = DNA([medLegs, medLegs], [normalEyes, normalEyes], 
                    [medMeta, medMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BaseGreenDNA = DNA([longLegs, longLegs], [wormEyes, wormEyes], 
                    [medMeta, medMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BaseBlueDNA = DNA([medLegs, medLegs], [normalEyes, normalEyes], 
                    [medMeta, medMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BaseRedDNA = DNA([shortLegs, shortLegs], [hawkEyes, hawkEyes], 
                    [medMeta, medMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BaseYellowDNA = DNA([shortLegs, longLegs], [wormEyes, hawkEyes], 
                    [slowMeta, FastMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BaseYellowDNA2 = DNA([shortLegs, longLegs], [wormEyes, wormEyes], 
                    [medMeta, slowMeta], [herbavore, herbavore], 
                    [skiddish, skiddish])
BasePredatorDNA = DNA([longLegs, longLegs], [wormEyes, wormEyes], 
                    [slowMeta, slowMeta], [predator, predator], 
                    [skiddish, skiddish])

# Intialize list of DNA attributes for lookups later
DNAAtributes = [a for a in dir(BaseAllDNA) if (not a.startswith('__') and 
                                        not callable(getattr(BaseAllDNA,a)))]


# Initializes template creatures. When creatures are breed they use these 
# templates before their genes are changed with a parental gene mix. This 
# is not biologically acurate but allows for genes to be stored as an effect on 
# a baseline value
BlueTemplate = Creature(BASE_CREATURE_WIDTH, BASE_CREATURE_HEIGHT, blue, "blue",
                        BaseBlueDNA)
GreenTemplate = Creature(BASE_CREATURE_WIDTH, BASE_CREATURE_HEIGHT, green, 
                        "green", BaseGreenDNA)
RedTemplate = Creature(BASE_CREATURE_WIDTH, BASE_CREATURE_HEIGHT, red, "red",
                        BaseRedDNA)
YellowTemplate = Creature(BASE_CREATURE_WIDTH, BASE_CREATURE_HEIGHT, yellow, 
                        "yellow", BaseYellowDNA)
PredatorTemplate = Creature(BASE_CREATURE_WIDTH, BASE_CREATURE_HEIGHT, orange, 
                        "orange", BasePredatorDNA)


# stores the templates for easy access
TemplateDNADict = {"blue": BlueTemplate, "red": RedTemplate, 
                    "green": GreenTemplate, "yellow": YellowTemplate, 
                    "orange": PredatorTemplate}


# Define Species
blueSpecies = {"num": startingNumber, "base": BaseBlueDNA,
                     "speciesBaseDNA": BaseBlueDNA, "color": blue, 
                     "species": "blue"}
redSpecies = {"num": startingNumber, "base": BaseRedDNA, 
                    "speciesBaseDNA": BaseRedDNA, "color": red, 
                    "species": "red"}
greenSpecies = {"num": startingNumber, "base": BaseGreenDNA, 
                    "speciesBaseDNA": BaseGreenDNA, "color": green, 
                    "species": "green"}
yellowSpecies = {"num": startingNumber, "base": BaseYellowDNA, 
                    "speciesBaseDNA": BaseYellowDNA, "color": yellow, 
                    "species": "yellow"}
yellowSpecies2 = {"num": startingNumber, "base": BaseYellowDNA, 
                    "speciesBaseDNA": BaseYellowDNA2, "color": yellow, 
                    "species": "yellow"}
predatorSpecies = {"num": startingNumber, "base": BasePredatorDNA, 
                    "speciesBaseDNA": BasePredatorDNA, "color": orange, 
                    "species": "orange"}

def StartPopsFromBreeding(foodNum, speciesList):
    # produce list od starting species
    startingSpecies = set()
    for s in speciesList:
        startingSpecies.add(s["species"])
    startingSpecies = list(startingSpecies)

    # populate initial creatures
    creatures = populateCreatures(speciesList)

    # breed inital creatures
    creatures = breedCreatures(creatures, startingSpecies)

    gameLoop(creatures, startingSpecies, foodNum)


ThreeHomoSpeciesInComp = [blueSpecies, redSpecies, greenSpecies]
ThreeHomoOneHeteroSpeciesInComp = [blueSpecies, redSpecies, greenSpecies, 
                                    yellowSpecies]
OneHeteroSpeciesInComp = [yellowSpecies]
HeteroPreyVsHomoPredator = [yellowSpecies, predatorSpecies]
OnePredator = [predatorSpecies]
ThreeHomoOneHeteroSpeciesInCompOnePred = [blueSpecies, redSpecies, greenSpecies, 
                                            yellowSpecies, predatorSpecies]
PredatorsAndPrey = [predatorSpecies, redSpecies]
#StartPopsFromBreeding(10, OneHeteroSpeciesInComp)
#StartPopsFromBreeding(60, ThreeHomoOneHeteroSpeciesInComp)
#StartPopsFromBreeding(60, ThreeHomoSpeciesInComp)
#StartPopsFromBreeding(10, HeteroPreyVsHomoPredator)
#StartPopsFromBreeding(10, OnePredator)
StartPopsFromBreeding(50,ThreeHomoOneHeteroSpeciesInCompOnePred)
#StartPopsFromBreeding(50,PredatorsAndPrey)

pygame.quit()
quit()
    