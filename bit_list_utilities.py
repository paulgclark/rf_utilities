# The following functions simplify manipulating lists of bits,
# in which each list item is an integer 0 or 1. This is the 
# primary way in which binary data is stored and manipulated
# within the wave* family of tools.
#
# note: these functions have not been optimized for performance,
# but are instead implemented for maximal clarity and readability

import sys
from collections import deque
LOGIC_X = "X"

# inverts a single bit, in which the bit is stored as an int
# equal to 0 or 1
def invertBit(inputBit):
    if inputBit == 1:
        outputBit = 0
    elif inputBit == 0:
        outputBit = 1
    else:
        outputBit = LOGIC_X
    return outputBit


# logically inverts each bit in the list
def invertBitList(bitList):
    bitListInv = []
    for bit in bitList:
        # bitListInv.append(invertBit(bit))
        if bit == 0:
            bitListInv.append(1)
        else:
            bitListInv.append(0)
    return bitListInv


# rotates the bitlist, with optional inversion
# positive rotate value denotes right-ward direction
def rotateBitList(bitList, rotate, invert = True):
    # rotate
    ind = deque(bitList)
    ind.rotate(rotate)
    # convert to list and invert contents into output string
    bitList = list(ind)
    outList = []
    if invert:
        #outList = invertBitList(bitList)
        for bit in bitList:
            if bit == 0:
                outList.append(1)
            else:
                outList.append(0)
            
    return outList


# swaps the bytes of a bit list and returns the new list
# should add the ability to handle lengths other than 16
def byteReverse(bitList):
    if len(bitList) != 16:
        print("WARNING: input bit list not evenly divisible by 8")
        return 16*[LOGIC_X]
    else:
        return bitList[8:16] + bitList[0:8]


# This function returns a list of bits located at the indices contained in 
# the index list. It will return the LOGIC_X character if the bit is outside 
# the bounds of the rawData list
def extractDisjointedBits(targetList, indexList):
    extractedBits = []
    for index in indexList:
        if index < len(targetList):
            extractedBits.append(targetList[index])    
        else:
            extractedBits.append(LOGIC_X)
    return extractedBits


# writes the data value into an existing list at the indices 
# specified; the targetList is passed by reference, and its
# contents are modified
# 
# Note: newData and indexList must be the same length
def writeDisjointBits(targetList, newData, indexList):
    if len(newData) != len(indexList):
        print("ERROR: attempting to write bits to list with", end=' ')
        print("improper indexList length. Exiting...")
        exit(1)

    l = len(targetList)
    if max(indexList) >= l:
        print("ERROR: index in list out of range, write will", end=' ')
        print("not be attempted.")
        return 0

    for index, bit in zip(indexList, newData):
        targetList[index] = bit


# returns the decimal value of the binary value represented by
# the bit list; by default, the function assumes MSB, in which 
# the item at index 0 is the most significant bit. You can choose
# an LSB conversion by setting reverse to True. You can also
# invert the bits before the conversion
def bitsToDec(bitList, invert = False, reverse = False):
    # invert bits if necessary
    bitList2 = []
    if invert:
        for bit in bitList:
            if bit == 0:
                bitList2.append(1)
            else:
                bitList2.append(0)
    else:
        bitList2 = bitList[:]
                
    # reverse bits if necessary
    if reverse:
        bitList3 = reversed(bitList2)
    else:
        bitList3 = bitList2[:]
        
    value = 0
    for bit in bitList3:
        if isinstance(bit, int):
            value = (value << 1) | bit
        else:
            # if we don't have an integer, then we ended up with a
            # logic error at some point
            value = -1
            break
    return int(value)


# returns a bit list of the specified length, corresponding to
# the integer value passed; the input integer must be greater than
# or equal to zero and less than 2**(len)
def decToPaddedBits(intVal, numBits):
    # make sure the input value is an int
    val = int(intVal)
    #if int(intVal) > (2**(numBits)-1):
    if val.bit_length() > numBits:
        print("WARNING: decToBits() passed too few bits ({}) to render integer: {}".format(numBits, val), end=' ')
        return numBits*[LOGIC_X]
    # build minimum bit count equivalent
    bits = [int(digit) for digit in bin(val)[2:]]
    # now pad the front end with zeros as needed
    padCount = numBits - len(bits)
    bits = padCount*[0] + bits
    return bits


# returns a list of bits corresponding to an input list of bytes
def byteListToBits(byteList):
    bitList = []
    for byte in byteList:
        bitList += decToPaddedBits(byte, 8)
    return bitList


######################################################################
# The following functions handle string conversion of bit lists for
# cleaner input and output.

# produces a compact string representation of the bit list
def bitsToStr(bitList):
    outStr = ""
    for bit in bitList:
        outStr += str(bit)
    return outStr


# when passed a bit list that is four bits in length, this function
# returns the nibble as a string
def bitsToNibble(bits, reverse = False):
    if reverse:
        bits = list(reversed(bits))
    nibble = LOGIC_X
    if bits == [0, 0, 0, 0]: nibble = '0'
    if bits == [0, 0, 0, 1]: nibble = '1'
    if bits == [0, 0, 1, 0]: nibble = '2'
    if bits == [0, 0, 1, 1]: nibble = '3'
    if bits == [0, 1, 0, 0]: nibble = '4'
    if bits == [0, 1, 0, 1]: nibble = '5'
    if bits == [0, 1, 1, 0]: nibble = '6'
    if bits == [0, 1, 1, 1]: nibble = '7'
    if bits == [1, 0, 0, 0]: nibble = '8'
    if bits == [1, 0, 0, 1]: nibble = '9'
    if bits == [1, 0, 1, 0]: nibble = 'A'
    if bits == [1, 0, 1, 1]: nibble = 'B'
    if bits == [1, 1, 0, 0]: nibble = 'C'
    if bits == [1, 1, 0, 1]: nibble = 'D'
    if bits == [1, 1, 1, 0]: nibble = 'E'
    if bits == [1, 1, 1, 1]: nibble = 'F'
    return nibble


# converts list of input bits to a list of bytes
def bit_list_to_byte_list(bits):
    if len(bits) % 8 != 0:
        print("WARNING: incomplete byte detected in input to bit_list_to_byte_list")
    byte_list = []
    for i in xrange(0, len(bits), 8):
        bits_in_byte = bits[i:i+8]
        byte = bitsToDec(bits_in_byte)
        byte_list.append(byte)
    return byte_list


# when passed a bit list that is eight bits in length, this function
# returns a string representation
def bitsToHexByteString(bits):
    if len(bits) == 8:
        return bitsToNibble(bits[0:4]) + bitsToNibble(bits[4:8])
    else:
        return LOGIC_X + LOGIC_X


# takes an input character and returns a bit list
def nibbleToBits(inputNib):
    bits = [LOGIC_X, LOGIC_X, LOGIC_X, LOGIC_X]
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


# takes an input string of length 2 and returns a bit list
def hexByteToBits(inputHexByteString):
    if inputHexByteString == "0":
        hexBits = nibbleToBits("0") + nibbleToBits("0")
    else:
        hexBits = nibbleToBits(inputHexByteString[0]) \
                + nibbleToBits(inputHexByteString[1])
    return hexBits


# takes an input character and returns the inverted nibble
def nibbleInvert(inputNib):
    nib = LOGIC_X
    if inputNib == '0': nib = 'F'
    if inputNib == '1': nib = 'E'
    if inputNib == '2': nib = 'D'
    if inputNib == '3': nib = 'C'
    if inputNib == '4': nib = 'B'
    if inputNib == '5': nib = 'A'
    if inputNib == '6': nib = '9'
    if inputNib == '7': nib = '8'
    if inputNib == '8': nib = '7'
    if inputNib == '9': nib = '6'
    if inputNib == 'A': nib = '5'
    if inputNib == 'B': nib = '4'
    if inputNib == 'C': nib = '3'
    if inputNib == 'D': nib = '2'
    if inputNib == 'E': nib = '1'
    if inputNib == 'F': nib = '0'
    return nib


# takes an input hex byte string of length two and returns a bit list
def hexStringToDec(inputHexByteString, reverse = False):
    return bitsToDec(hexByteToBits(inputHexByteString), reverse)


# takes an input hex string, two bytes in length, and returns a bit list
def hexShortToDec(byteLowString, byteHighString, reverse = False):
    decimalLow = hexToDec(byteLowString, reverse)
    decimalHigh = hexToDec(byteHighString, reverse)
    decimalWord = 256*256*decimalHigh + decimalLow
    return decimalWord

# prints a list of byte values as ASCII
def print_bytes_as_ascii(byte_list):
    for byte in byte_list:
        sys.stdout.write(chr(byte))
    print("")
