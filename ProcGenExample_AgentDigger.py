# -*- coding: utf-8 -*-
"""
Created on Fri Oct 30 19:01:31 2015

@author: Ryan McCormick

PROVIDED AS IS WITHOUT WARRANTY OR GUARANTEE THAT IT WILL WORK.
"""

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import random
from random import randint

'''
Classes to procedurally generate a map using a blind digger agent.
A blind digger object can dig its way through
a digging map object.

This implementation closely follows the approch outlined
here:
http://pcgbook.com/
http://pcgbook.com/wp-content/uploads/chapter03.pdf

The algorithm closely follows that on page 39 of the .pdf:
-------
1: initialize chance of changing direction Pc=5
2: initialize chance of adding room Pr=5
3: place the digger at a dungeon tile and randomize its direction
4: dig along that direction
5: roll a random number Nc between 0 and 100
6: if Nc below Pc:
7: randomize the agent’s direction
8: set Pc=0
9: else:
10: set Pc=Pc+5
11:roll a random number Nr between 0 and 100
12:if Nr below Pr:
13: randomize room width and room height between 3 and 7
14: place room around current agent position
14: set Pr=0
15:else:
16: set Pr=Pr+5
17:if the dungeon is not large enough:
18: go to step 4
-------
'''

'''
Some global variables to store parameters
'''
UNDUGTILE = "X"
CORRIDORTILE = "C"
ROOMTILE = "R"

DIRECTIONLIST = ["up", "down", "left", "right"]

DEFAULTCHANGEDIRECTIONCHANCE = 1
DEFAULTROOMBUILDINGCHANCE = 1

INCREMENTOFDIRECTIONCHANGE = 0.05
INCREMENTOFROOMBUILDING = 0.025

'''
The DiggingMap class contains an x by y matrix of the map. Elements
of the matrix correspond to tiles, and are either undug, corridors, or room tiles.
'''

class DiggingMap(object):
    def __init__(self, width, height):
        self.area = width * height
        self.width = width
        self.height= height
        self.tilesDug = 0
        self.percentAreaDug = (float(self.tilesDug) / float(self.area)) * 100.0
        tileMap = []
        for yVal in range(0, height):
            xList = []
            for xVal in range(0, width):
                xList.append(UNDUGTILE)
            tileMap.append(xList)
        self.tileMap = tileMap
        
    def digRoomTile(self, x, y):
        print("Attempting to dig room at coordinates " + str(x), str(y))
        if ((x >= self.width - 1) or (y >= self.height - 1)):
            print("Coordinate out of range")
        elif ((x < 0) or (y < 0)):
            print("Coordinates out of range.")
        else:
            self.tileMap[x][y] = ROOMTILE
            self.tilesDug += 1
            self.percentAreaDug = (float(self.tilesDug) / float(self.area)) * 100.0
            
    def digCorridorTile(self, x, y):
        print("Attempting to dig corridor at coordinates " + str(x), str(y))
        if ((x >= self.width - 1) or (y >= self.height - 1)):
            print("Coordinate out of range.")
        elif ((x < 0) or (y < 0)):
            print("Coordinates out of range.")
        elif (self.tileMap[x][y] == ROOMTILE):
            print("Tile is already a room, no need to dig.")
        else:
            self.tileMap[x][y] = CORRIDORTILE
            self.tilesDug += 1
            self.percentAreaDug = (float(self.tilesDug) / float(self.area)) * 100.0
    
    def getTileAtLocation(self, x, y):
        return self.tileMap[x][y]
    
    def plotDiggingMap(self):
        tileList = []
        for xVal in range(len(self.tileMap)):
            for yVal in range(len(self.tileMap[xVal])):                  
                if self.tileMap[xVal][yVal] == CORRIDORTILE:
                    newRectangle = Rectangle((xVal, yVal), 1, 1, facecolor = "grey")
                    tileList.append(newRectangle)
                if self.tileMap[xVal][yVal] == ROOMTILE:
                    newRectangle = Rectangle((xVal, yVal), 1, 1, facecolor = "orange")
                    tileList.append(newRectangle)
       
        fig = plt.figure()
        ax = fig.gca()  #GCA = get current axes
        backgroundTile = Rectangle((0, 0), self.width, self.height, facecolor = "blue")
        ax.add_patch(backgroundTile)
        for tile in tileList:
            ax.add_patch(tile)

        ax.set_ylim(0,  self.height - 1)
        ax.set_xlim(0,  self.width - 1)
        
    def getWidth(self):
        return self.width
        
    def getHeight(self):
        return self.height

'''
The BlindDigger class can dig in DiggingMap. Most of the work is done
in the performDigIteration function.
'''

class BlindDigger(object):
    def __init__(self, directionPercentChance = 5, roomPercentChance = 5, 
                 location = (0, 0), direction = "up", 
                 roomWidthRange = (3, 7), roomHeightRange = (3, 7)):
        self.percentChanceOfChangingDirection = directionPercentChance
        self.percentChanceOfBuildingRoom = roomPercentChance
        self.location = location
        self.direction = direction
        self.roomWidthRange = roomWidthRange
        self.roomHeightRange = roomHeightRange
        
    def setDirection(self, inputDirection):
        self.direction = inputDirection
    
    def setLocation(self, inputLocation):
        self.location = inputLocation
    
    def initializeDig(self, diggingMap):
        print("Initializing dig")
        initialXLocation = randint(0, diggingMap.getWidth() - 1)
        initialYLocation = randint(0, diggingMap.getHeight() - 1)
        self.location = (initialXLocation, initialYLocation)
        
        diggingMap.digCorridorTile(self.location[0], self.location[1])
        
        self.direction = random.choice(DIRECTIONLIST)
        
    def performDigIteration(self, diggingMap):
        print("Performing iteration of digging")
        currentTile = diggingMap.getTileAtLocation(self.location[0], self.location[1])
        
        
        # Chance to switch direction
        directionRoll = randint(0, 99)
        if (directionRoll < self.percentChanceOfChangingDirection and currentTile != ROOMTILE):
            self.direction = random.choice(DIRECTIONLIST)
            self.percentChangeOfChangingDirection = DEFAULTCHANGEDIRECTIONCHANCE
        elif (currentTile == ROOMTILE):
            self.percentChangeOfChangingDirection = DEFAULTCHANGEDIRECTIONCHANCE
        else:
            self.percentChanceOfChangingDirection = self.percentChanceOfChangingDirection + INCREMENTOFDIRECTIONCHANGE

        roomRoll = randint(0, 99)
        if (roomRoll < self.percentChanceOfBuildingRoom and currentTile != ROOMTILE):
            print("Building room. Percent chance of room is ", self.percentChanceOfBuildingRoom, " and roll was ", roomRoll)
            # Choose room width
            roomWidth = randint(self.roomWidthRange[0], self.roomWidthRange[1])
            roomWidthDiv2 = int(round((roomWidth / 2.0)))
            roomWidthRemainder = roomWidth - roomWidthDiv2
            # Choose room height
            roomHeight = randint(self.roomHeightRange[0], self.roomHeightRange[1])
            roomHeightDiv2 = int(round((roomHeight / 2.0)))
            roomHeightRemainder = roomHeight - roomHeightDiv2
            
            
            print(roomWidthDiv2, roomWidthRemainder, roomHeightDiv2, roomHeightRemainder)
            # Cover the 4 quarters.
            # Positive X, Positive Y            
            for xIncrement in range(0, roomWidthDiv2 + 1):
                for yIncrement in range(0, roomHeightDiv2 + 1):
                    print("Building room coord ", xIncrement, yIncrement, " from ", self.location)
                    diggingMap.digRoomTile(self.location[0] + xIncrement, self.location[1] + yIncrement)
            # Positive X, Negative Y
            for xIncrement in range(0, roomWidthDiv2 + 1):
                for yIncrement in range(0, roomHeightRemainder + 1):
                    print(xIncrement, yIncrement)
                    diggingMap.digRoomTile(self.location[0] + xIncrement, self.location[1] - yIncrement)
                
            # Negative X, Negative Y
            for xIncrement in range(0, roomWidthRemainder + 1):
                for yIncrement in range(0, roomHeightRemainder + 1):
                    print(xIncrement, yIncrement)
                    diggingMap.digRoomTile(self.location[0] - xIncrement, self.location[1] - yIncrement)
                
            # Negative X, Positive Y
            for xIncrement in range(0, roomWidthRemainder + 1):
                for yIncrement in range(0, roomHeightDiv2 + 1):
                    print(xIncrement, yIncrement)
                    diggingMap.digRoomTile(self.location[0] - xIncrement, self.location[1] + yIncrement)
                
            
            self.percentChanceOfBuildingRoom = DEFAULTROOMBUILDINGCHANCE
        elif (currentTile == ROOMTILE):
            self.percentChanceOfBuildingRoom = DEFAULTROOMBUILDINGCHANCE
        else:
            self.percentChanceOfBuildingRoom = self.percentChanceOfBuildingRoom + INCREMENTOFROOMBUILDING
        
        
        # Switch to opposite directions if at the edge.
        if (self.location[0] == 0):
            self.direction = "right"
        if (self.location[0] == diggingMap.getWidth() - 1):
            self.direction = "left"
        if (self.location[1] == 0):
            self.direction = "up"
        if (self.location[1] == diggingMap.getHeight() - 1):
            self.direction = "down"
        
        if (self.direction == "up"):
            self.location = (self.location[0], self.location[1] + 1)
        if (self.direction == "down"):
            self.location = (self.location[0], self.location[1] - 1)
        if (self.direction == "right"):
            self.location = (self.location[0] + 1, self.location[1])
        if (self.direction == "left"):
            self.location = (self.location[0] - 1, self.location[1])
            
        
        diggingMap.digCorridorTile(self.location[0], self.location[1])
    
        
    
'''
Main logic function
'''
        
def generateAgentDiggerMap():
    mapHeight = 50
    mapWidth = 50
    digger = BlindDigger()
    
    diggingMap = DiggingMap(mapWidth, mapHeight)
    digger.initializeDig(diggingMap)
    
    while (diggingMap.percentAreaDug < 40):
        digger.performDigIteration(diggingMap)
    
    diggingMap.plotDiggingMap()
    
if __name__ == "__main__":
    generateAgentDiggerMap()
       

