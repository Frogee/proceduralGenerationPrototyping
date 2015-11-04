# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 13:46:42 2015

@author: Ryan McCormick

PROVIDED AS IS WITHOUT WARANTEE OR GUARANTEE THAT IT WILL WORK.
"""

from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import random
from random import randint
from math import sqrt

'''
Classes and functions to procedurally generate a map of rectangular rooms.
The map is generated using the idea of binary space partitioning. It
closely follows the approach of found here:
http://pcgbook.com/
http://pcgbook.com/wp-content/uploads/chapter03.pdf

The algorithm we're sort of following is on page 35 of that pdf and is as follows:
-------
1: start with the entire dungeon area (root node of the BSP tree)
2: divide the area along a horizontal or vertical line
3: select one of the two new partition cells
4: if this cell is bigger than the minimal acceptable size:
5: go to step 2 (using this cell as the area to be divided)
6: select the other partition cell, and go to step 4
7: for every partition cell:
8: create a room within the cell by randomly
choosing two points (top left and bottom right)
within its boundaries
9: starting from the lowest layers, draw corridors to connect
rooms in the nodes of the BSP tree with children of the same
parent
10:repeat 9 until the children of the root node are connected
-------

It uses a binary tree to partition the space. Each leaf represents a
box of space in which a "sub area" (i.e., another box) can be placed.
Once the sub areas are placed, corridors (also boxes) are used to connect them.
'''


'''
BoxHelperClass to do operations on Boxes. This class doesn't do much
other than contain a function that operates on lists of Boxes.
'''

class BoxHelper(object):
    def __init__(self):
        self.name = None
    
    '''
    Given two lists of Boxes, this returns which two Boxes have the closest
    centers. This is used to prevent very distance Boxes from being connected
    if they are chosen from the list at random. As such, this reduces the chance
    of really large corridors that travel over existing rooms.
    '''
    def returnIndicesOfClosestSubAreas(self, boxListFirst, boxListSecond):      
        listToReturn = [0, 0]
        firstListIndex = 0
        secondListIndex = 0
        centroidDistance = 1000000000 # Arbitrarily large magic number        
        for boxFromFirstList in boxListFirst:
            #Find first box centroid
            centerXFirst = boxFromFirstList.origin[0] + (boxFromFirstList.width / 2.0)
            centerYFirst = boxFromFirstList.origin[1] + (boxFromFirstList.height / 2.0)
            secondListIndex = 0            
            for boxFromSecondList in boxListSecond:
                #Find second box centroid
                centerXSecond = boxFromSecondList.origin[0] + (boxFromSecondList.width / 2.0)
                centerYSecond = boxFromSecondList.origin[1] + (boxFromSecondList.height / 2.0)
                distXSquared = (centerXSecond - centerXFirst) * (centerXSecond - centerXFirst)
                distYSquared = (centerYSecond - centerYFirst) * (centerYSecond - centerYFirst) 
                distance = sqrt(distXSquared + distYSquared)
                if (distance < centroidDistance):
                    centroidDistance = distance
                    listToReturn = [firstListIndex, secondListIndex]
                secondListIndex += 1
            firstListIndex += 1
        return listToReturn


'''
Box class to contain information to track location of rectangles.
These are stored in a similar manner to the matplotlib Rectangle class
that is used for plotting.

This class also contains some member functions to divide a box into two
equal boxes, and to randomly generate a "sub area" from the given box area.
'''

class Box(object):
    def __init__(self, origin = (0,0), width = 0, height = 0):
        self.origin = origin
        self.height = height
        self.width = width
        self.area = width * height
    
    def __repr__(self):
        printString = "Box:\nOrigin:(" + str(self.origin[0]) + "," + str(self.origin[1]) + ")\n"
        printString += "Width: " + str(self.width) + "\tHeight: " + str(self.height) + "\n"
        printString += "Area: " + str(self.area)
        return printString
    
    def getHeight(self):
        return self.height
        
    def setHeight(self, height):
        self.height = height
        self.area = self.height * self.width
    
    def getOrigin(self):
        return self.origin
        
    def setOrigin(self, origin):
        self.origin = origin
    
    def getWidth(self):
        return self.width
        
    def setWidth(self, width):
        self.width = width
        self.area = self.height * self.width
    
    def getArea(self):
        return self.area

    '''    
    Returns a list of boxes that are a random division of itself in half.
    '''
    def partitionBox(self):
        boxesToReturn = []
        divideParallelWithWidth = random.choice([True, False])
        
        # A few extra conditions to try to avoid getting to unbalanced:
        # If very wide, divide parallel with height
        if (self.width > 3.0 * self.height):   # 3 is a magic number size factor.
            divideParallelWithWidth = False
        # If vary tall, divide parallel with width
        if (self.height > 3.0 * self.width):   # 3 is a magic number size factor.
            divideParallelWithWidth = True

        if (divideParallelWithWidth == True):
            print("Dividing along width")
            # If first box were (0,0), 20, 50
            # Then partition should be:
            # (0, 0), 20, 25
            # (0, 0 + 25), 20, 25
            originalOrigin = self.origin
            halfHeight = self.height / 2.0
            firstBox = Box((originalOrigin[0], originalOrigin[1]), self.width, halfHeight)
            secondBox = Box((originalOrigin[0], originalOrigin[1] + halfHeight), self.width, halfHeight)
            boxesToReturn.append(firstBox)
            boxesToReturn.append(secondBox)
        else:
            print("Dividing along height")
            # If first box were (0,0), 20, 50
            # Then partition should be:
            # (0, 0), 10, 50
            # (0 + 10, 0), 10, 50
            originalOrigin = self.origin
            halfWidth = self.width / 2.0
            firstBox = Box((originalOrigin[0], originalOrigin[1]), halfWidth, self.height)
            secondBox = Box((originalOrigin[0] + halfWidth, originalOrigin[1]), halfWidth, self.height)
            boxesToReturn.append(firstBox)
            boxesToReturn.append(secondBox)
        return boxesToReturn

    '''
    Create a sub area within a box. This sub area represents a room, and is a Box itself.
    '''
    
    def constructSubArea(self):
        #8: create a room within the cell by randomly
        #   choosing two points (top left and bottom right)
        #   within its boundaries
        
        # We're going to randomly chose a point, and a width and a height
        # constrained by the size of the current box.
        randomWidth = 0
        randomHeight = 0
        boxToReturn = Box()
        MAGICPADDINGNUMBER = 3  # I guess this should be a global parameter or something?
        MAGICWIDTHTHRESHOLD = 6  # More magic numbers
        MAGICHEIGHTTHRESHOLD = 6  # Even more magic numbers
        while (boxToReturn.area < (0.20 * self.area)):  # Another magic number for minimum size of the sub area
            originalOrigin = self.origin
            xLowerBound = int(originalOrigin[0])
            xUpperBound = int(originalOrigin[0] + self.width)
            yLowerBound = int(originalOrigin[1])
            yUpperBound = int(originalOrigin[1] + self.height)
            
            randomOriginX = randint(xLowerBound, xUpperBound)
            randomOriginY = randint(yLowerBound, yUpperBound)
            
            widthUpperBound = int((self.width + self.origin[0]) - randomOriginX)
            heightUpperBound = int((self.height + self.origin[1]) - randomOriginY)

            randomWidth = randint(0, widthUpperBound)
            randomHeight = randint(0, heightUpperBound)
    
            
            boxToReturn.setHeight(randomHeight)
            boxToReturn.setWidth(randomWidth)
            boxToReturn.setOrigin((randomOriginX, randomOriginY))
            
            # Just to make sure the boxes are away from the wall a bit.
            distanceFromRightWall = (self.origin[0] + self.width) - (boxToReturn.origin[0] + boxToReturn.width) 
            distanceFromLeftWall = (boxToReturn.origin[0] - self.origin[0])
            distanceFromTopWall = (self.origin[1] + self.height) - (boxToReturn.origin[1] + boxToReturn.height) 
            distanceFromBottomWall = (boxToReturn.origin[1] - self.origin[1])
            
            print(distanceFromRightWall, distanceFromLeftWall, distanceFromTopWall, distanceFromBottomWall)
        
            # Perform another round if things aren't quite how we want them.            
            if (distanceFromRightWall < MAGICPADDINGNUMBER
                or distanceFromLeftWall < MAGICPADDINGNUMBER
                or distanceFromTopWall < MAGICPADDINGNUMBER
                or distanceFromBottomWall < MAGICPADDINGNUMBER
                or boxToReturn.getHeight() < MAGICHEIGHTTHRESHOLD
                or boxToReturn.getWidth() < MAGICWIDTHTHRESHOLD):                  
                    boxToReturn.setHeight(1)
                    boxToReturn.setWidth(1)
        
        print("The following box:")
        print(self)
        print("Generated the sub area:")
        print(boxToReturn)
        return boxToReturn
        

'''
Generic tree implementation inspired by the following sources:
http://stackoverflow.com/questions/2482602/a-general-tree-implementation-in-python
http://cbio.ufs.ac.za/live_docs/nbn_tut/trees.html

This was my first attempt at implementing a tree data structure and recursion, and it suffers
from a lack of initial design specifications. It morphs from a generic
tree in which a node can have arbitrarily many children, to expecting that
nodes will only have two children for many of the functions to work properly.
Also, the idea for nodes to contain the Box information came relatively late
in the process, so that was haphazardly bolted on near the end (e.g., the class
was renamed to "AreaNode")
'''
        
class AreaNode(object):
    def __init__(self, name, children, box = Box(), parent = "NULL" ):
        self.name = name
        self.children = children  # Dictionary of child nodes, where keys are the name of the child node.
        self.box = box
        self.subArea = box
        self.childrenAreConnected = False
        self.connection = Box()
        
    def __repr__(self, level = 0):
        nodeString = ("\t" * level) + repr(str(self.name)) + "\n"
        for nodeName in self.children:
            nodeString += self.children[nodeName].__repr__(level + 1)
        return nodeString
    
    def searchNode(self, nodeNameToFind, traversalList = [], traversalLevel = 0, nameWasFound = False):
        for nodeName in self.children:    
            if (nameWasFound != True):
                nameWasFound = self.children[nodeName].searchNode(nodeNameToFind, traversalList, traversalLevel + 1, nameWasFound)
            if (nodeName == nodeNameToFind):
                nameWasFound = True
                for level in range(0, traversalLevel + 1):
                    traversalList.append("FILLER")
                traversalList[traversalLevel] = nodeName
                return True
        
            if (nameWasFound == True):
                if (traversalList[traversalLevel] == "FILLER"):
                    traversalList[traversalLevel] = nodeName
                    return True              

    def deleteNode(self, nodeNameToFind, traversalList = [], traversalLevel = 0, nameWasFound = False):
        for nodeName in self.children:
            if (nameWasFound != True):
                nameWasFound = self.children[nodeName].deleteNode(nodeNameToFind, traversalList, traversalLevel + 1, nameWasFound)
            if (nodeName == nodeNameToFind):
                print("Found " + nodeName + ". Deleting.")                
                self.children.pop(nodeName, None)
                return True

    def addNode(self, nodeNameToFind, nodeNameToAdd, box, traversalLevel = 0, nameWasFound = False):
        for nodeName in self.children:
            if (nameWasFound != True):
                nameWasFound = self.children[nodeName].addNode(nodeNameToFind, nodeNameToAdd, box, traversalLevel + 1, nameWasFound)
            if (nodeName == nodeNameToFind):
                print("Found " + nodeName + ". Adding " + nodeNameToAdd)
                newNode = AreaNode(nodeNameToAdd, defaultdict(AreaNode), box)
                self.children[nodeNameToFind].children[nodeNameToAdd] = newNode
                return True
        
    def getRectangles(self, rectangleList, color):
        for nodeName in self.children:
            self.children[nodeName].getRectangles(rectangleList, color)
            nodeBox = Rectangle(self.children[nodeName].box.getOrigin(), 
                                self.children[nodeName].box.getWidth(), 
                                self.children[nodeName].box.getHeight(), facecolor=color)
            rectangleList.append(nodeBox)

    def getSubAreaShapes(self, shapeList):
        for nodeName in self.children:        
            self.children[nodeName].getSubAreaShapes(shapeList)        
        if (len(self.children) == 0):
            nodeBox = self.subArea
            shapeList.append(nodeBox)
        if (self.childrenAreConnected == True):
            shapeList.append(self.connection)
                
    def getSubAreaRectangles(self, rectangleList, boxColor, connectorColor):      
        for nodeName in self.children:
            self.children[nodeName].getSubAreaRectangles(rectangleList, boxColor, connectorColor)
            if (len(self.children[nodeName].children) == 0):
                nodeBox = Rectangle(self.children[nodeName].subArea.getOrigin(), 
                                    self.children[nodeName].subArea.getWidth(), 
                                    self.children[nodeName].subArea.getHeight(), facecolor=boxColor)
                rectangleList.append(nodeBox)
            if (self.childrenAreConnected == True):
                nodeBox = Rectangle(self.connection.getOrigin(),
                                    self.connection.getWidth(),
                                    self.connection.getHeight(), facecolor=connectorColor)
                rectangleList.append(nodeBox)
            
    def partitionNode(self, nodeNameToFind, partitionNames, 
                      box = Box(), traversalLevel = 0,
                      nameWasFound = False):
        for nodeName in self.children:
            if (nameWasFound != True):
                nameWasFound = self.children[nodeName].partitionNode(nodeNameToFind, partitionNames, box, traversalLevel + 1, nameWasFound)
            if (nodeName == nodeNameToFind):
                print("Found " + nodeName + ". Partitioning.")
                #First, need to check how many children it has.
                if (len(self.children[nodeName].children) == 0):
                    #Then we need to determine if and how to divide the current box.
                    #First, find if the box is large enough to partition.
                    MAGICMINIMUMAREA = 10
                    print("Area of " + nodeName + " is " + str(self.children[nodeName].box.getArea()) )
                    if (self.children[nodeName].box.getArea() > MAGICMINIMUMAREA):
                        boxes = self.children[nodeName].box.partitionBox();
                        self.addNode(nodeName, partitionNames[0], boxes[0])
                        self.addNode(nodeName, partitionNames[1], boxes[1])
                        print(self.children[nodeName])
                    else:
                        print("Insufficient area to partition. Not partitioning")
                else:
                    print("Node already has children. Not partitioning.")
                return True
            
    def getNodeArea(self, nodeNameToFind, area, traversalLevel = 0, nameWasFound = False):
         for nodeName in self.children:
            if (nameWasFound != True):
                nameWasFound = self.children[nodeName].getNodeArea(nodeNameToFind, area, traversalLevel + 1, nameWasFound)
            if (nodeName == nodeNameToFind):
                print("Found " + nodeName + ". Returning area of " + str(self.children[nodeName].box.getArea()))                
                area.append(self.children[nodeName].box.getArea())
                return True

    def constructSubArea(self):
        for nodeName in self.children:
            self.children[nodeName].constructSubArea()
            print("Constructing sub area for: " + nodeName)
            subAreaBox = self.children[nodeName].box.constructSubArea()
            self.children[nodeName].subArea = subAreaBox
        
    def resetSubArea(self):
        for nodeName in self.children:
            self.children[nodeName].resetSubArea()
            print("Resetting sub area for: " + nodeName)
            self.children[nodeName].subArea = Box()
            self.children[nodeName].childrenAreConnected = False
            self.children[nodeName].connection = Box()
        
    def getListOfLeafPairs(self, listOfLeafPairs):        
        tempListOfChildren = []
        for nodeName in self.children:
            self.children[nodeName].getListOfLeafPairs(listOfLeafPairs)
            if (len(self.children[nodeName].children) == 0):
                tempListOfChildren.append(nodeName)
        if (len(tempListOfChildren) == 2): 
            print(tempListOfChildren[0] + " and " + tempListOfChildren[1] + " have no children")
            listOfLeafPairs.append((tempListOfChildren[0], tempListOfChildren[1]))

    '''
    One of the major functions, and one of the ugliest.
    
    The purpose is to connect all of the sub areas with boxes, and make sure all rooms are connected somehow.
    We model this by providing all parent nodes with connectors. The trivial case is
    when two leaf nodes are connected (i.e. two sub areas). When the children are nodes
    that themselves have children, we consider all of the sub areas and the connections
    as potential candidates for making new connections between two nodes.
    
    The strange list variable, li_subAreasSuccessfullyConnected, is used because
    I couldn't figure out how to declare a static variable in Python, and I couldn't
    assign an integer or boolean. Evidently, lists are mutable and I could modify it 
    and have it maintained during recursion.
    
    
    '''
    def connectSubArea(self, li_subAreasSuccessfullyConnected):
        tempListOfChildren = []
        for nodeName in self.children:
            self.children[nodeName].connectSubArea(li_subAreasSuccessfullyConnected)
            tempListOfChildren.append(nodeName)
        if (len(tempListOfChildren) == 2 and li_subAreasSuccessfullyConnected != [False]):
            if (self.childrenAreConnected == False):
                print("Adding connection that connects children: " + tempListOfChildren[0] + " and " + tempListOfChildren[1] + " of parent node: " + self.name)

                # Obtain a list of boxes for each child.
                shapeListFirstChild = []
                shapeListSecondChild = []
                
                self.children[tempListOfChildren[0]].getSubAreaShapes(shapeListFirstChild)
                self.children[tempListOfChildren[1]].getSubAreaShapes(shapeListSecondChild)
                
                # Generate a potential connection between the two lists
                print("Attempting to connect:")
                print("Child 1's shapes: ")
                print(shapeListFirstChild)
                print("With Child 2's shapes: ")
                print(shapeListSecondChild)
                
                boxHelper = BoxHelper()
                # Start by choosing the boxes that have the closest centers.
                indexList = boxHelper.returnIndicesOfClosestSubAreas(shapeListFirstChild, shapeListSecondChild)
                choiceFromFirstList = shapeListFirstChild[indexList[0]]
                choiceFromSecondList = shapeListSecondChild[indexList[1]]
                
                terminationIterator = 0                
                while (self.childrenAreConnected == False):
                    
                    if (terminationIterator > 100):
                        # When this happens, we probably can't make the connections
                        # necessary for the given sub areas. If we try to reconstruct
                        # the sub areas, it will invalidate the previous connections made.
                        # At this point, we should probably abort and start again.
                        print("Termination iterator condition met. Setting exit status to false.")
                        if (len(li_subAreasSuccessfullyConnected) == 0):                        
                            li_subAreasSuccessfullyConnected.append(False)
                        else:
                            li_subAreasSuccessfullyConnected[0] = False
                        #raw_input("Press enter to continue")
                        break
                    
                    # Variable to track whether or not the shapes with the closest area will work
                    closestFailed = False
                    
                    # Find overlaps in the X and Y dimensions
                    # X borders (min, max) Y borders (min, max)
                    xMinFirstShape = choiceFromFirstList.origin[0]
                    xMaxFirstShape = choiceFromFirstList.origin[0] + choiceFromFirstList.width
                    
                    yMinFirstShape = choiceFromFirstList.origin[1]
                    yMaxFirstShape = choiceFromFirstList.origin[1] + choiceFromFirstList.height
                    
                    xMinSecondShape = choiceFromSecondList.origin[0]
                    xMaxSecondShape = choiceFromSecondList.origin[0] + choiceFromSecondList.width
                    
                    yMinSecondShape = choiceFromSecondList.origin[1]
                    yMaxSecondShape = choiceFromSecondList.origin[1] + choiceFromSecondList.height  
            
                    #Magic variable to determine the size of corridors.
                    CORRIDORSIZE = 4
                    
                    print("Attempting to connect:")
                    print(choiceFromFirstList)
                    print(choiceFromSecondList)
                    
                    if (xMinFirstShape >= xMinSecondShape and xMinFirstShape <= xMaxSecondShape):
                        print("First shape X starts after second, and starts before end of second")
                        # Need to travel along the Y to connect them. First, find the delimiting X space we can connect.
                        xConnectorLowerLimit = xMinFirstShape
                        xConnectorUpperLimit = min(xMaxFirstShape, xMaxSecondShape)
                        if (xConnectorUpperLimit - xConnectorLowerLimit <= CORRIDORSIZE):
                            closestFailed = True
                            terminationIterator += 1 
                        else:
                            xCenter = randint(xConnectorLowerLimit + (CORRIDORSIZE / 2.0), xConnectorUpperLimit - (CORRIDORSIZE / 2.0))
                            
                            #Find where on the Y axis this needs to be located. Origin needs to be at the minimum maxX, and maximum minX
                            xOrigin = xCenter -2 
                            yOrigin = min(yMaxFirstShape, yMaxSecondShape)
                            
                            yWidth = max(yMinFirstShape, yMinSecondShape) - yOrigin
                            
                            print("The constructed connector will be:")
                            newConnector = Box((xOrigin, yOrigin), CORRIDORSIZE, yWidth)
                            print(newConnector)
                            
                            self.connection = newConnector
                            
                            self.childrenAreConnected = True
                            
                            if (li_subAreasSuccessfullyConnected != [False]):
                                if (len(li_subAreasSuccessfullyConnected) == 0):
                                    li_subAreasSuccessfullyConnected.append(True)
                                    #raw_input("Press enter to continue")
                        
                        
                    elif (yMinFirstShape >= yMinSecondShape and yMinFirstShape <= yMaxSecondShape):
                        print("First shape Y starts after second, and starts before end of second")
                        # Need to travel along the X to connect them. First, find the delimiting Y space we can connect.
                        yConnectorLowerLimit = yMinFirstShape
                        yConnectorUpperLimit = min(yMaxFirstShape, yMaxSecondShape)
                        if (yConnectorUpperLimit - yConnectorLowerLimit <= CORRIDORSIZE):
                            closestFailed = True
                            terminationIterator += 1 
                        else:
                            yCenter = randint(yConnectorLowerLimit + (CORRIDORSIZE / 2.0), yConnectorUpperLimit - (CORRIDORSIZE / 2.0))
                            
                            #Find where on the X axis this needs to be located. Origin needs to be at the minimum maxX, and maximum minX
                            xOrigin = min(xMaxFirstShape, xMaxSecondShape)
                            yOrigin = yCenter - 2
                            
                            xWidth = max(xMinFirstShape, xMinSecondShape) - xOrigin
                            
                            print("The constructed connector will be:")
                            newConnector = Box((xOrigin, yOrigin), xWidth, CORRIDORSIZE)
                            print(newConnector)
                            
                            self.connection = newConnector
                        
                            self.childrenAreConnected = True
                            if (li_subAreasSuccessfullyConnected != [False]):
                                if (len(li_subAreasSuccessfullyConnected) == 0):
                                    li_subAreasSuccessfullyConnected.append(True)
                                    #raw_input("Press enter to continue")
                            
                    
                    elif (xMinSecondShape >= xMinFirstShape and xMinSecondShape <= xMaxFirstShape):
                        print("Second shape X starts after first, and starts before end of first.")
                        # Need to travel along the Y to connect them. First, find the delimiting X space we can connect.
                        xConnectorLowerLimit = xMinSecondShape
                        xConnectorUpperLimit = min(xMaxFirstShape, xMaxSecondShape)
                        if (xConnectorUpperLimit - xConnectorLowerLimit <= CORRIDORSIZE):
                            closestFailed = True
                            terminationIterator += 1 
                        else:
                            xCenter = randint(xConnectorLowerLimit + (CORRIDORSIZE / 2.0), xConnectorUpperLimit - (CORRIDORSIZE / 2.0))
                            
                            #Find where on the Y axis this needs to be located. Origin needs to be at the minimum maxX, and maximum minX
                            xOrigin = xCenter -2 
                            yOrigin = min(yMaxFirstShape, yMaxSecondShape)
                            
                            yWidth = max(yMinFirstShape, yMinSecondShape) - yOrigin
                            
                            print("The constructed connector will be:")
                            newConnector = Box((xOrigin, yOrigin), CORRIDORSIZE, yWidth)
                            print(newConnector)
                            
                            self.connection = newConnector
                            
                            self.childrenAreConnected = True
                            if (li_subAreasSuccessfullyConnected != [False]):
                                if (len(li_subAreasSuccessfullyConnected) == 0):
                                    li_subAreasSuccessfullyConnected.append(True)
                                    #raw_input("Press enter to continue")
                        
                    elif (yMinSecondShape >= yMinFirstShape and yMinSecondShape <= yMaxFirstShape):
                        print("Second shape Y starts after first, and starts before end of first.")
                        # Need to travel along the X to connect them. First, find the delimiting Y space we can connect.
                        yConnectorLowerLimit = yMinSecondShape
                        yConnectorUpperLimit = min(yMaxFirstShape, yMaxSecondShape)
                        if (yConnectorUpperLimit - yConnectorLowerLimit <= CORRIDORSIZE):
                            closestFailed = True
                            terminationIterator += 1                             
                        else:
                            yCenter = randint(yConnectorLowerLimit + (CORRIDORSIZE / 2.0), yConnectorUpperLimit - (CORRIDORSIZE / 2.0))
                            
                            #Find where on the X axis this needs to be located. Origin needs to be at the minimum maxX, and maximum minX
                            xOrigin = min(xMaxFirstShape, xMaxSecondShape)
                            yOrigin = yCenter - 2
                        
                            xWidth = max(xMinFirstShape, xMinSecondShape) - xOrigin
                            
                            print("The constructed connector will be:")
                            newConnector = Box((xOrigin, yOrigin), xWidth, CORRIDORSIZE)
                            print(newConnector)
                            
                            self.connection = newConnector    
                            self.childrenAreConnected = True
                            if (li_subAreasSuccessfullyConnected != [False]):
                                if (len(li_subAreasSuccessfullyConnected) == 0):
                                    li_subAreasSuccessfullyConnected.append(True)
                                    #raw_input("Press enter to continue")
                    
                    else:
                        print("Unable to make connection between:")
                        print(choiceFromFirstList)
                        print(choiceFromSecondList)
                        closestFailed = True
                        terminationIterator += 1
                
                    # If choosing the closest sub areas fails, we start picking at random.
                    # This should probably be picking the second clostest Boxes rather than at random.
                    if (closestFailed == True):
                        indexList[0] = randint(0, len(shapeListFirstChild) - 1)
                        indexList[1] = randint(0, len(shapeListSecondChild) - 1)
                        choiceFromFirstList = shapeListFirstChild[indexList[0]]
                        choiceFromSecondList = shapeListSecondChild[indexList[1]]        
                    else:
                        indexList = boxHelper.returnIndicesOfClosestSubAreas(shapeListFirstChild, shapeListSecondChild)
                        choiceFromFirstList = shapeListFirstChild[indexList[0]]
                        choiceFromSecondList = shapeListSecondChild[indexList[1]]     

                 
             
'''
Tree class to contain the root node. This class doesn't do much
other than maintain the abstraction of the tree; it mostly just calls
Node member functions using the rood node.

The only unique function is that it can draw the tree, but maybe that
should be refactored into a graphics plotting class.
'''
class AreaTree(object):
    def __init__(self, rootNode):
        self.rootNode = rootNode
    
    def __repr__(self):
        return "Tree structure:\n\n" + self.rootNode.__repr__()
        
    def searchNode(self, nodeNameToFind):
        traversalList = []
        print("\nInitiating search for: " + str(nodeNameToFind))
        if (self.rootNode.name == nodeNameToFind):
            print("Root node has value " + nodeNameToFind)
            traversalList.append(0)
        else:
            self.rootNode.searchNode(nodeNameToFind, traversalList, 1, False)
            if (len(traversalList) != 0):
                traversalList[0] = self.rootNode.name
            else:
                traversalList = [None]
        print("Finished searching")
        print("TraversalList:")
        print(traversalList)
        return traversalList
    
    def deleteNode(self, nodeToDelete):
        print("Deleting " + nodeToDelete)
        self.rootNode.deleteNode(nodeToDelete)
        
    def addNode(self, nodeParentName, nodeNameToAdd, box):
        print("Adding " + nodeNameToAdd + " to node " + nodeParentName)
        if (self.rootNode.name == nodeParentName):
            newNode = AreaNode(nodeNameToAdd, defaultdict(AreaNode), box)
            self.rootNode.children[nodeNameToAdd] = newNode
        else:
            self.rootNode.addNode(nodeParentName, nodeNameToAdd, box, 1, False)
        
    def partitionNode(self, nodeNameToPartition, partitionNames):
        print("Partitioning " + nodeNameToPartition)
        if (nodeNameToPartition == self.rootNode.name):
            if (len(self.rootNode.children) == 0):
                MAGICMINIMUMAREA = 10
                print("Area of " + self.rootNode.name + " is " + str(self.rootNode.box.getArea()) )
                if (self.rootNode.box.getArea() > MAGICMINIMUMAREA):
                    boxes = self.rootNode.box.partitionBox();
                    self.addNode(nodeNameToPartition, partitionNames[0], boxes[0])
                    self.addNode(nodeNameToPartition, partitionNames[1], boxes[1])
                    print(self.rootNode.children)
                else:
                    print("Insufficient area to partition. Not partitioning")
            else:
                print("Node already has children. Not partitioning.")
        else:
            self.rootNode.partitionNode(nodeNameToPartition, partitionNames, Box(), 1, False)
    
    def getNodeArea(self, nodeNameToFind):
        area = [] #For whatever reason I have to pass this as a list for it to be modified.
        if (nodeNameToFind == self.rootNode.name):
            area.append(self.rootNode.box.area)
        else:
            self.rootNode.getNodeArea(nodeNameToFind, area)
        return area[0]
                
    def constructSubAreas(self):
        print("Creating sub areas")
        self.rootNode.subArea = self.rootNode.box.constructSubArea()
        self.rootNode.constructSubArea()
    
    def resetSubAreas(self):
        print("Resetting sub areas")
        self.rootNode.subArea = Box()
        self.rootNode.childrenAreConnected = False
        self.rootNode.connection = Box()
        self.rootNode.resetSubArea()
    
    def connectSubAreas(self, li_areasAreConnected):
        print("Connecting sub areas")
        self.rootNode.connectSubArea(li_areasAreConnected)
    
    def getListOfLeafPairs(self, leafPairList):
        print("Getting list of leaf pairs")
        self.rootNode.getListOfLeafPairs(leafPairList)
            
    def showAreaTree(self):
        fig = plt.figure()
        ax = fig.gca()  #GCA = get current axes
        #This gets plotted, but isn't seen since things are drawn over it.
        nodeBox = Rectangle(self.rootNode.box.getOrigin(), self.rootNode.box.getWidth(), self.rootNode.box.getHeight(), facecolor="grey")       
        ax.add_patch(nodeBox)
        ax.set_ylim(self.rootNode.box.getOrigin()[0],  self.rootNode.box.getOrigin()[0] + self.rootNode.box.getHeight())
        ax.set_xlim(self.rootNode.box.getOrigin()[1],  self.rootNode.box.getOrigin()[1] + self.rootNode.box.getWidth())
        
        nodeColor = "blue"
        rectangleList = []
        self.rootNode.getRectangles(rectangleList, nodeColor)
        
        roomColor = "orange"
        corridorColor = "grey"
        subAreaRectangleList = []
        self.rootNode.getSubAreaRectangles(subAreaRectangleList, roomColor, corridorColor)
        
        for rectangle in reversed(rectangleList):   #Need to reverse it so the smaller rectangles get drawn over the larger
            ax.add_patch(rectangle)
            
        for rectangle in reversed(subAreaRectangleList):
            ax.add_patch(rectangle)
            
        fig.show()
        

'''
Prototype implementation of the binary space partitioning method 
of map construction used here.
http://pcgbook.com/wp-content/uploads/chapter03.pdf
1: start with the entire dungeon area (root node of the BSP tree)
2: divide the area along a horizontal or vertical line
3: select one of the two new partition cells
4: if this cell is bigger than the minimal acceptable size:
5: go to step 2 (using this cell as the area to be divided)
6: select the other partition cell, and go to step 4
7: for every partition cell:
8: create a room within the cell by randomly
choosing two points (top left and bottom right)
within its boundaries
9: starting from the lowest layers, draw corridors to connect
rooms in the nodes of the BSP tree with children of the same
parent
10:repeat 9 until the children of the root node are connected
'''

def generateBSPMap():
    # 1: start with the entire area (root node of the BSP tree)
    rootNodeBox = Box((0, 0), 256, 256) #The dimensions should be evenly divisible by 2
    rootNode = AreaNode("root", defaultdict(AreaNode), rootNodeBox)
    tree = AreaTree(rootNode)
    firstPartitionNames = ("A", "B")
    # 2: divide the area along a horizontal or vertical line
    tree.partitionNode("root", firstPartitionNames)
    currentArea = rootNodeBox.getArea()
    currentPartitionNames = firstPartitionNames
    MAGICMINIMUMAREA = (0.03125) * 256 * 256
    #MAGICMINIMUMAREA = (0.10) * 256 * 256
    
    while (currentArea > MAGICMINIMUMAREA):
        # 3: select one of the two new partition cells
        chosenIndex = random.choice([0, 1])
        chosenPartition = currentPartitionNames[chosenIndex]    
        if (chosenIndex == 0):    
            otherPartition = currentPartitionNames[1]
        else:
            otherPartition = currentPartitionNames[0]
        
        #4: if this cell is bigger than the minimal acceptable size:
        print("Chosen partition " + chosenPartition + " has node area " + str(tree.getNodeArea(chosenPartition)))

        if (tree.getNodeArea(chosenPartition) > MAGICMINIMUMAREA):
            #5: go to step 2 (using this cell as the area to be divided)
            newPartitionNames = (chosenPartition + "_0", chosenPartition + "_1")
            tree.partitionNode(chosenPartition, newPartitionNames)
        
        #6: select the other partition cell, and go to step 4
        if (tree.getNodeArea(otherPartition) > MAGICMINIMUMAREA):
            newPartitionNames = (otherPartition + "_0", otherPartition + "_1")
            tree.partitionNode(otherPartition, newPartitionNames)
        
        currentArea = min([tree.getNodeArea(chosenPartition), tree.getNodeArea(otherPartition)])

        partitionNameList = []
        tree.getListOfLeafPairs(partitionNameList)
        currentPartitionNames = random.choice(partitionNameList)
        
    #7: for every partition cell:
    #8: create a room within the cell by randomly
    #   choosing two points (top left and bottom right)
    #   within its boundaries
    li_areasAreConnected = []
    terminationIterator = 0
    while (li_areasAreConnected == [False] or li_areasAreConnected == []):     
        tree.resetSubAreas()        
        tree.constructSubAreas()

        #9: starting from the lowest layers, draw corridors to connect
        #   rooms in the nodes of the BSP tree with children of the same
        #   parent
        #10:repeat 9 until the children of the root node are connected
        li_areasAreConnected = []
        tree.connectSubAreas(li_areasAreConnected)
        terminationIterator += 1
        if (terminationIterator > 50):
            print("Attempted too many iterations. Terminating.")
            print(li_areasAreConnected)
            break

    if (li_areasAreConnected == [True]):
        print(tree)
        tree.showAreaTree()

if __name__ == "__main__":
    generateBSPMap()
       

