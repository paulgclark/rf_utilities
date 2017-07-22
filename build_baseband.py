import json
from collections import OrderedDict
from pprint import pprint

def toggleLevel(level):
    if level == 0:
        level = 1
    else:
        level = 0
    return level

def nibbleToBits(inputNib):
    if inputNib == '0': bits = [0, 0, 0, 0]
    if inputNib == '1': bits = [0, 0, 0, 1]
    if inputNib == '2': bits = [0, 0, 1, 0]
    if inputNib == '3': bits = [0, 0, 1, 1]
    if inputNib == '4': bits = [0, 1, 0, 0]
    if inputNib == '5': bits = [0, 1, 0, 1]
    if inputNib == '6': bits = [0, 1, 1, 0]
    if inputNib == '7': bits = [0, 1, 1, 1]
    if inputNib == '8': bits = [1, 0, 0, 0]
    if inputNib == '9': bits = [1, 0, 0, 1]
    if inputNib == 'A': bits = [1, 0, 1, 0]
    if inputNib == 'B': bits = [1, 0, 1, 1]
    if inputNib == 'C': bits = [1, 1, 0, 0]
    if inputNib == 'D': bits = [1, 1, 0, 1]
    if inputNib == 'E': bits = [1, 1, 1, 0]
    if inputNib == 'F': bits = [1, 1, 1, 1]
    return bits

def populateLevel(outFile, level, sampleCount):
    for _ in xrange(sampleCount):
        if level == 1:
            outFile.write(b'\x01')
        else:
            outFile.write(b'\x00')



class basebandDefinition:
    initialVal = 0
    elementList = []
    widthList = []
    waveList = []

    def __init__(self):
        print "Creating new baseband definition object"
        
    def readFromFile(self, inFileName):
        # read each line of the file into a list item
        with open(inFileName) as inFile:
            lines = inFile.read().splitlines()

        # split each line into list items
        for line in lines:
            # chop off anything at a '#' char and after
            decommentLine = line.split('#')[0]
            # ignore any empty lines
            if len(decommentLine) > 0:
                # create list for this line
                lineList = decommentLine.split() 

                if lineList[0] == "INIT":
                    initialVal = int(lineList[1])
                elif lineList[0] == "REG":
                    self.elementList.append(lineList)
                elif lineList[0] == "NRZ":
                    self.elementList.append(lineList)
                elif lineList[0] == "ARB":
                    self.elementList.append(lineList)
                # add manchester and PWM

    def buildWidthList(self):
        level = self.initialVal
        self.widthList = []
        for element in self.elementList:
            if element[0] == "ARB":
                level = int(element[1])
                for width in element[2:]:
                    self.widthList.append([level, int(width)])
                    level = toggleLevel(level)
            if element[0] == "NRZ":
                lowWidth = int(element[1])
                highWidth = int(element[2])
                if element[3] == "HEX":
                    bitList = []
                    for byte in element[4:]:
                        bitList += nibbleToBits(byte[0]) + nibbleToBits(byte[1])
                    for bit in bitList:
                        if bit == 0:
                            self.widthList.append([0, lowWidth])
                        else:
                            self.widthList.append([1, highWidth])
                elif element[3] == "ASCII":
                    bitList = []
                    for char in element[5]:
                        asciiVal = ord(char) # number from 0 to 255
                        bitList = [int(n) for n in bin(asciiVal)[2:].zfill(8)]
                        print str(asciiVal) + " = ",
                        print bitList 
                        if element[4] == "LSB": # need to reverse for LSB
                            bitList = bitList[::-1]
                        for bit in bitList:
                            if bit == 0:
                                self.widthList.append([0, lowWidth])
                            else:
                                self.widthList.append([1, highWidth])
 
            if element[0] == "REG":
                level = int(element[1])
                lowWidth = int(element[2])
                highWidth = int(element[3])
                pulseCount = int(element[4])
                for i in xrange(2*pulseCount):
                    if level == 0:
                        self.widthList.append([0, lowWidth])
                    else:
                        self.widthList.append([1, highWidth])
                    level = toggleLevel(level)
            
        return []

    def buildWave(self, sampleRate):
        self.waveList = []
        for pair in self.widthList:
            for _ in xrange( int((1.0*sampleRate/1000000) * pair[1]) ):
                self.waveList.append(pair[0])
        
    def writeWaveToFile(self, outFileName, repeatVal):
        with open(outFileName, 'wb') as outFile:
            for _ in xrange(repeatVal):
                for bit in self.waveList:
                    if bit == 1:
                        outFile.write(b'\x01')
                    else:
                        outFile.write(b'\x00')


    def printDefinition(self):
        print self.elementList

    def printWidths(self):
        for pair in self.widthList:
            print pair

    def printWave(self):
        for bit in self.waveList:
            print bit,


def microsecondsToSamples(time, sampleRate):
    return int(1.0*time*sampleRate)

def addSamples(basebandList, signalLevel, arbWidth, sampleRate):
    newBasebandList = basebandList
    valsToAdd = microsecondsToSamples(arbWidth, sampleRate)
    for _ in xrange(valsToAdd):
        newBasebandList.append(signalLevel)
    if signalLevel == 1:
        newSignalLevel = 0
    else:
        newSignalLevel = 1
    return (newBasebandList, newSignalLevel)

def buildBaseband(jsonFileName, basebandSampleRate, initialValue):
    signalLevel = initialValue

    # read from file (move to top level)
    print "reading json data from file: " + jsonFileName
    with open(jsonFileName) as jsonFile:
    #with open("../input_files/test.json") as jsonFile:
        jsonObj = json.load(jsonFile, object_pairs_hook=OrderedDict)
    print(odString(jsonObj))
    pprint(jsonObj)

    print "building baseband"
    basebandList = []
    # start with preamble
    preambleJson = jsonObj["preamble"]
    pprint(preambleJson)
    for element in preambleJson:
        if element[0] == "arbitrary":
            print "adding arbitrary timing"
            for arbWidth in element[1]:
                (basebandList, signalLevel) = addSamples(basebandList, signalLevel, arbWidth)

    

    return basebandList
