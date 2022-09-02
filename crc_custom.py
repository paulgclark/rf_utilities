
import bit_list_utilities as blu
import itertools 

# CRC input bit order
CRC_NORM = 0 # data bits are processed from MSB to LSB
CRC_REVERSE = 1 # data bits are processed from LSB to MSB
CRC_REFLECT = 2 # data processed from MSByte to LSByte, but each byte reversed
CRC_BIT_ORDER_OPTIONS = [CRC_NORM, CRC_REVERSE, CRC_REFLECT]

# initial value options
CRC_INIT_ZERO = 0
CRC_INIT_ONE = 1
CRC_INIT_OPTIONS = [CRC_INIT_ZERO, CRC_INIT_ONE]

# output reversal options
CRC_REVERSE_FALSE = 0
CRC_REVERSE_TRUE = 1
CRC_REVERSE_BYTES = 2
CRC_REVERSE_FINAL_OPTIONS = [CRC_REVERSE_FALSE, CRC_REVERSE_TRUE, CRC_REVERSE_BYTES]

# different options to pad the packet
CRC_NOPAD = 0
CRC_PAD_TO_EVEN = 1 # pad packet to an even multiple of the pad count
CRC_PAD_ABS = 2 # pad packet with pad count worth of bits
CRC_PAD_OPTIONS = [CRC_NOPAD, CRC_PAD_TO_EVEN, CRC_PAD_ABS]

MASTER_CRC_OPTIONS = list(itertools.product(CRC_BIT_ORDER_OPTIONS, 
                                            CRC_INIT_OPTIONS,
                                            CRC_REVERSE_FINAL_OPTIONS))

# initialize master poly list, which contains a list of common
# polynomials indexed by length
MASTER_POLY_LIST = [list([]) for _ in xrange(65)]
 
# Common CRC Polynomials
POLY_3_GSM = [1,0,1,1]
MASTER_POLY_LIST[3] = [POLY_3_GSM]

POLY_4_ITU = [1, 0,0,1,1]
MASTER_POLY_LIST[4] = [POLY_4_ITU]

POLY_5_EPC = [1,0, 1,0,0,1]
POLY_5_ITU = [1,1, 0,1,0,1]
POLY_5_USB = [1,0, 0,1,0,1]
MASTER_POLY_LIST[5] = [POLY_5_EPC, POLY_5_ITU, POLY_5_USB]

POLY_6_CDMA2000_A = [1,1,0, 0,1,1,1]
POLY_6_CDMA2000_B = [1,0,0, 0,1,1,1]
POLY_6_DARC       = [1,0,1, 1,0,0,1]
POLY_6_GSM        = [1,1,0, 1,1,1,1]
POLY_6_ITU        = [1,0,0, 0,0,1,1]
MASTER_POLY_LIST[6] = [POLY_6_CDMA2000_A, POLY_6_CDMA2000_B, POLY_6_DARC,
                       POLY_6_GSM, POLY_6_ITU]

POLY_7_MMC_SD = [1,0,0,0, 1,0,0,1]
POLY_7_MVB    = [1,1,1,0, 0,1,0,1]
MASTER_POLY_LIST[7] = [POLY_7_MMC_SD, POLY_7_MVB]

POLY_8_DVB       = [1, 1,1,0,1, 0,1,0,1]
POLY_8_AUTOSAR   = [1, 0,0,1,0, 1,1,1,1]
POLY_8_BLUETOOTH = [1, 1,0,1,0, 0,1,1,1]
POLY_8_CCITT     = [1, 0,0,0,0, 0,1,1,1]
POLY_8_MAXIM     = [1, 0,0,1,1, 0,0,0,1] # used for 1-wire
POLY_8_DARC      = [1, 0,0,1,1, 1,0,0,1]
POLY_8_GSM_B     = [1, 0,1,0,0, 1,0,0,1]
POLY_8_SAE_J1850 = [1, 0,0,0,1, 1,1,0,1]
POLY_8_WCDMA     = [1, 1,0,0,1, 1,0,1,1]
MASTER_POLY_LIST[8] = [POLY_8_DVB, POLY_8_AUTOSAR, POLY_8_BLUETOOTH,
                       POLY_8_CCITT, POLY_8_MAXIM, POLY_8_DARC,
                       POLY_8_GSM_B, POLY_8_SAE_J1850, POLY_8_WCDMA]

POLY_10_ATM      = [1,1,0, 0,0,1,1, 0,0,1,1]
POLY_10_CDMA2000 = [1,1,1, 1,1,0,1, 1,0,0,1]
POLY_10_GSM      = [1,0,1, 0,1,1,1, 0,1,0,1]
MASTER_POLY_LIST[10] = [POLY_10_ATM, POLY_10_CDMA2000, POLY_10_GSM]

POLY_11_FLEXRAY = [1,0,1,1, 1,0,0,0, 0,1,0,1]
MASTER_POLY_LIST[11] = [POLY_11_FLEXRAY]

POLY_12          = [1, 1,0,0,0, 0,0,0,0, 1,1,1,1]
POLY_12_CDMA2000 = [1, 1,1,1,1, 0,0,0,1, 0,0,1,1]
POLY_12_GSM      = [1, 1,1,0,1, 0,0,1,1, 0,0,0,1]
MASTER_POLY_LIST[12] = [POLY_12, POLY_12_CDMA2000, POLY_12_GSM]

POLY_13_BBC = [1,1, 1,1,0,0, 1,1,1,1, 0,1,0,1]
MASTER_POLY_LIST[13] = [POLY_13_BBC]

POLY_14_DARC = [1,0,0, 1,0,0,0, 0,0,0,0, 0,1,0,1]
POLY_14_GSM  = [1,1,0, 0,0,0,0, 0,0,1,0, 1,1,0,1]
MASTER_POLY_LIST[14] = [POLY_14_DARC, POLY_14_GSM]

POLY_15_CAN      = [1,1,0,0, 0,1,0,1, 1,0,0,1, 1,0,0,1]
POLY_15_MPT1327  = [1,1,1,0, 1,0,0,0, 0,0,0,1, 0,1,0,1]
MASTER_POLY_LIST[15] = [POLY_15_CAN, POLY_15_MPT1327]

POLY_16_CHAKRAVARTY   = [1, 0,0,1,0, 1,1,1,1, 0,0,0,1, 0,1,0,1]
POLY_16_ARINC         = [1, 1,0,1,0, 0,0,0,0, 0,0,1,0, 1,0,1,1]  
POLY_16_CCITT         = [1, 0,0,0,1, 0,0,0,0, 0,0,1,0, 0,0,0,1]
POLY_16_CDMA2000      = [1, 1,1,0,0, 1,0,0,0, 0,1,1,0, 0,1,1,1]
POLY_16_DECT          = [1, 0,0,0,0, 0,1,0,1, 1,0,0,0, 1,0,0,1]
POLY_16_T10_DIF       = [1, 1,0,0,0, 1,0,1,1, 1,0,1,1, 0,1,1,1]
POLY_16_DNP           = [1, 0,0,1,1, 1,1,0,1, 0,1,1,0, 0,1,0,1]
POLY_16_IBM           = [1, 1,0,0,0, 0,0,0,0, 0,0,0,0, 0,1,0,1]
POLY_16_OPEN_SAFETY_A = [1, 0,1,0,1, 1,0,0,1, 0,0,1,1, 0,1,0,1]
POLY_16_OPEN_SAFETY_B = [1, 0,1,1,1, 0,1,0,1, 0,1,0,1, 1,0,1,1]
POLY_16_PROFIBUS      = [1, 0,0,0,1, 1,1,0,1, 1,1,0,0, 1,1,1,1]
MASTER_POLY_LIST[16] = [POLY_16_CHAKRAVARTY, POLY_16_ARINC, POLY_16_CCITT,
                        POLY_16_CDMA2000, POLY_16_DECT, POLY_16_T10_DIF,
                        POLY_16_DNP, POLY_16_IBM, POLY_16_OPEN_SAFETY_A,
                        POLY_16_OPEN_SAFETY_B, POLY_16_PROFIBUS]

POLY_17_CAN = [1,1, 0,1,1,0, 1,0,0,0, 0,1,0,1, 1,0,1,1]
MASTER_POLY_LIST[17] = [POLY_17_CAN]

POLY_21_CAN = [1,1, 0,0,0,0, 0,0,1,0, 1,0,0,0, 1,0,0,1, 1,0,0,1]
MASTER_POLY_LIST[21] = [POLY_21_CAN]

POLY_24_FLEXRAY = [1, 0,1,0,1, 1,1,0,1, 0,1,1,0, 1,1,0,1, 1,1,0,0, 1,0,1,1]
POLY_24_RADIX64 = [1, 1,0,0,0, 0,1,1,0, 0,1,0,0, 1,1,0,0, 1,1,1,1, 1,0,1,1]
MASTER_POLY_LIST[24] = [POLY_24_FLEXRAY, POLY_24_RADIX64]

POLY_30_CDMA = [1,1,0, 0,0,0,0, 0,0,1,1, 0,0,0,0, 1,0,1,1, 1,0,0,1, 1,1,0,0, 0,1,1,1]
MASTER_POLY_LIST[30] = [POLY_30_CDMA]

POLY_32      = [1, 0,0,0,0, 0,1,0,0, 1,1,0,0, 0,0,0,1, 0,0,0,1, 1,1,0,1, 1,0,1,1, 0,1,1,1]
POLY_32_C    = [1, 0,0,0,1, 1,1,1,0, 1,1,0,1, 1,1,0,0, 0,1,1,0, 1,1,1,1, 0,1,0,0, 0,0,0,1]
POLY_32_K    = [1, 0,1,1,1, 0,1,0,0, 0,0,0,1, 1,0,1,1, 1,0,0,0, 1,1,0,0, 1,1,0,1, 0,1,1,1]
POLY_32_K2   = [1, 0,0,1,1, 0,0,1,0, 0,1,0,1, 1,0,0,0, 0,0,1,1, 0,1,0,0, 1,0,0,1, 1,0,0,1]
POLY_32_Q    = [1, 1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1, 1,0,1,0, 1,0,1,1]
MASTER_POLY_LIST[32] = [POLY_32, POLY_32_C, POLY_32_K, POLY_32_K2, 
                        POLY_32_Q]

POLY_40_GSM = [1] + list(blu.decToPaddedBits(intVal=0x0004820009, numBits=40))
MASTER_POLY_LIST[40] = [POLY_40_GSM]

POLY_64_ECMA = [1] + blu.decToPaddedBits(intVal=0x42F0E1EBA9EA3693, numBits=64)
POLY_64_ISO  = [1] + blu.decToPaddedBits(intVal=0x000000000000001B, numBits=64)
MASTER_POLY_LIST[64] = [POLY_64_ECMA, POLY_64_ISO]

# This class defines all of the parameters of a CRC, and is easier to pass
# into and out of functions than a set of variables. It is also possible to 
# assign lists to each of the variables and use as an input to the 
# brute force crc discovery functions  
class CrcDefinition:
    crcLen = 2
    crcPoly = [1, 0, 1]
    crcStart = 0
    crcStop = 0
    dataStart = 0
    dataStop = 0
    inputBitOrder = CRC_NORM
    initVal = 0
    reverseFinal = False
    finalXOR = [0, 0]
    padType = CRC_NOPAD
    padCount = 0
    padVal = 0
    
    def __init__(self, crcLen, crcPoly, dataStart, dataStop,
                 inputBitOrder, initVal, reverseFinal,
                 finalXOR, padType, padCount, padVal,
                 crcStart = 0, crcStop = 0):
            self.crcLen = crcLen
            self.crcPoly = crcPoly
            self.dataStart = dataStart
            self.dataStop = dataStop
            self.inputBitOrder = inputBitOrder
            self.initVal = initVal
            self.reverseFinal = reverseFinal
            self.finalXOR = finalXOR
            self.padType = padType
            self.padCount = padCount
            self.padVal = padVal
            self.crcStart = crcStart
            self.crcStop = crcStop

    
    # computes CRC of the specified dataStart...dataStop range using
    # the CRC definition; use this when you want to generate a CRC
    def computeCRC(self, inputData):
        return crcCompute(payload=inputData[self.dataStart:self.dataStop+1],
                          crcPoly=self.crcPoly,
                          inputBitOrder=self.inputBitOrder,
                          initVal=self.initVal,
                          reverseFinal=self.reverseFinal,
                          finalXOR=self.finalXOR,
                          padType=self.padType,
                          padCount=self.padCount,
                          padVal=self.padVal)


    # if your data already contains a CRC and you want to check it,
    # make sure the crcStart...crcStop indices are defined and 
    # run this function
    def checkCRC(self, inputData):
        crcObserved = inputData[self.crcStart:self.crcStop+1]
        crcComputed = crcCompute(payload=inputData[self.dataStart:self.dataStop+1],
                                 crcPoly=self.crcPoly,
                                 inputBitOrder=self.inputBitOrder,
                                 initVal=self.initVal,
                                 reverseFinal=self.reverseFinal,
                                 finalXOR=self.finalXOR,
                                 padType=self.padType,
                                 padCount=self.padCount,
                                 padVal=self.padVal)
        return crcObserved == crcComputed 
    
    # generates a string containing the CRC properties stored in the object
    def crcPropertiesString(self):
        str  = "CRC Properties:\n"
        str += "  Length = {}\n".format(self.crcLen)
        str += "  Poly = {}\n".format(self.crcPoly)
        str += "  Input Bit Order = {}\n".format(self.inputBitOrder)
        str += "  Initial Value = {}\n".format(self.initVal)
        str += "  Reverse Final = {}\n".format(self.reverseFinal)
        str += "  Final XOR = {}\n".format(self.finalXOR)
        str += "  Pad Type = {}\n".format(self.padType)
        str += "  Pad Count = {}\n".format(self.padCount)
        str += "  Pad Value = {}\n".format(self.padVal)
        str += "  Indices:\n"
        str += "    CRC Start  = {:3}\n".format(self.crcStart)
        str += "    CRC Stop   = {:3}\n".format(self.crcStop)        
        str += "    Data Start = {:3}\n".format(self.dataStart)
        str += "    Data Stop  = {:3}\n".format(self.dataStop)
        return str
    
        
    # if you have set the variables in this object to lists of possible values,
    # this function then iterates over all of these CRC properies and tries them
    # out on the list of input data values; after iterating through all of the
    # possibilities, it returns the most successful options 
    def crcIterate(self, inputDataList, verbose):
        solutionSpace = list(itertools.product(MASTER_POLY_LIST[self.crcLen],
                                          self.inputBitOrder,
                                          self.initVal,
                                          self.reverseFinal,
                                          self.finalXOR,
                                          self.PadType,
                                          self.PadCount,
                                          self.PadVal,
                                          self.crcStart,
                                          self.crcStop,
                                          self.dataStart,
                                          self.dataStop))
        
        masterSuccessList = []
        for crcPoly, inputBitOrder, initVal, reverseFinal,\
            finalXOR, padType, PadCount, PadVal,\
            crcStart, crcStop, dataStart, dataStop in solutionSpace:
            
            successList = []
            for inputData in inputDataList:
                crcObserved = inputData[crcStart:crcStop+1]
                crcComputed = crcCompute(payload=inputData[dataStart:dataStop+1],
                                         crcPoly=crcPoly,
                                         inputBitOrder=inputBitOrder,
                                         initVal=initVal,
                                         reverseFinal=reverseFinal,
                                         finalXOR=finalXOR,
                                         padType=padType,
                                         padCount=padCount,
                                         padVal=padVal)
                successList.append(crcObserved == crcComputed)
                
            masterSuccessList.append(successList)

        # go through results and determine the most successful attempt
        successCount = []
        for successList in masterSuccessList:
            successCount.append(sum(int(successList)))
        
        # this returns the index of the best attempt
        indexOfBest = successCount.index(max(successCount))

        # display the results of the most successful attempts
        if verbose:
            print("Successes: {} at index = {}".format(max(successCount), indexOfBest))
            print(masterSuccessList)
            
        # return a CRC object containing the parameters of the most successful
        # need to acess the solution space with the index and get the values
        print(solutionSpace[indexOfBest])
        return 0


class AcsDefinition():
    dataStart = 0,
    dataStop = 0, 
    acsStart = 0,
    acsStop = 0,
    dataInvert = False, 
    dataReverse = CRC_REVERSE_FALSE, 
    numOutputBits = 8, 
    initSum = 0
    
    def __init__(self, dataStart, dataStop, dataInvert, dataReverse, numOutputBits, initSum, acsStart, acsStop):
        self.dataStart = dataStart
        self.dataStop = dataStop
        self.dataInvert = dataInvert 
        self.dataReverse = dataReverse 
        self.numOutputBits = numOutputBits 
        self.initSum = initSum
        self.acsStart = acsStart
        self.acsStop = acsStop
        
        
    def computeACS(self, inputData):
        return checksumCompute(dataList=inputData, 
                               dataStart=self.dataStart, 
                               dataStop=self.dataStop, 
                               dataInvert=self.dataInvert, 
                               dataReverse=self.dataReverse, 
                               numOutputBits=self.numOutputBits, 
                               initSum=self.initSum)
        
        
    def checkACS(self, inputData):
        acsObserved = inputData[self.acsStart:self.acsStop+1]
        acsComputed = checksumCompute(dataList=inputData, 
                                      dataStart=self.dataStart, 
                                      dataStop=self.dataStop, 
                                      dataInvert=self.dataInvert, 
                                      dataReverse=self.dataReverse, 
                                      numOutputBits=self.numOutputBits, 
                                      initSum=self.initSum)
        return blu.bitsToDec(acsObserved) == acsComputed 
        
        
    # generates a string containing the ACS properties stored in the object
    def acsPropertiesString(self):
        str  = "ACS Properties:\n"
        str += "  Invert Data = {}\n".format(self.dataInvert)
        str += "  Reverse Data = {}\n".format(self.dataReverse)
        str += "  Number of Output Bits = {}\n".format(self.numOutputBits)
        str += "  Initial Sum = {}\n".format(self.initSum)
        str += "  Indices:\n"
        str += "    ACS Start  = {:3}\n".format(self.acsStart)
        str += "    ACS Stop   = {:3}\n".format(self.acsStop)        
        str += "    Data Start = {:3}\n".format(self.dataStart)
        str += "    Data Stop  = {:3}\n".format(self.dataStop)
        return str

        
    def iterateACS(self, inputDataList, verbose):
        return 0
        
#####################################
# Note: payload and crcPoly are lists of integers, each valued either 1 or 0
def crcCompute(payload, crcPoly, inputBitOrder, initVal, reverseFinal,
               finalXOR, padType, padCount, padVal):

    # print out inputs before proceeding
    if False:
        print("payload length: {}".format(len(payload)))
        print("crcPoly: {}".format(crcPoly))
        print("inputBitOrder: " + str(inputBitOrder))
        print("initVal: " + str(initVal))
        print("reverseFinal: " + str(reverseFinal))
        print("finalXOR: {}".format(finalXOR))
        print("padType: " + str(padType))
        print("padCount: " + str(padCount))
        print("padVal: " + str(padVal))
        
    # pad the packet as instructed
    payloadPad = payload[:];
    if padType == CRC_PAD_ABS: # add fixed number of bits
        for i in range(padCount):
            payloadPad.append(padVal)
    elif padType == CRC_PAD_TO_EVEN:
        if padCount != 0:
            numBits = len(payload) % padCount # figure how many short of even
        else:
            numBits = len(payload)
        for i in range(numBits):
            payloadPad.append(padVal)

    # reflecting means reversing the bits within each byte
    # note, this will only work if the payload is a multiple of 8 long
    if inputBitOrder == CRC_REFLECT:
        payloadIn = payloadPad[:]
        i = 0
        while i <= len(payloadIn)-8:
            payloadByte = payloadIn[i:i+8]
            payloadIn[i:i+8] = payloadByte[::-1] # assign to reversed byte
            i += 8
    # reverse the payload if instructed
    elif inputBitOrder == CRC_REVERSE:
        payloadIn = payloadPad[::-1]
    # else process normally 
    else:
        payloadIn = payloadPad[:]

    # the working value of the computation is the payload input padded
    # by a number of bits equal to one less than the poly length
    # these bit positions allow for a remainder of the division
    for i in range(len(crcPoly) - 1):
        payloadIn.append(initVal) # CRCs can have different initial values

    #print("range i and j and len(payloadIn):")
    #print(range(len(payload)))
    #print(range(len(crcPoly)))
    #print(len(payloadIn) #print payload)
    #print(payloadIn)

    for i in range(len(payload)):
        if (payloadIn[i] == 1):
            for j in range(len(crcPoly)):
                payloadIn[i+j] = (payloadIn[i+j]+crcPoly[j]) % 2
        #print(payloadIn)

    # crc value is the remainder which is stored in the final bits 
    # of the computation
    crcRemainder = payloadIn[-(len(crcPoly)-1):]

    # final reversal of CRC bits
    if reverseFinal == CRC_REVERSE_TRUE:
        crcOut = crcRemainder[::-1]
    elif reverseFinal == CRC_REVERSE_FALSE:
        crcOut = crcRemainder[:]
    elif reverseFinal == CRC_REVERSE_BYTES:
        crcOut = blu.byteReverse(crcRemainder)

    # final XOR mask
    crcXOR = []
    for i in range(len(crcOut)):
        if ((crcOut[i]==1) ^ (finalXOR[i]==1)):
            crcXOR.append(1)
        else:
            crcXOR.append(0)

    return(crcXOR)


# This function iterates over a series of payloads and associated CRC
# values. Each iteration uses a different set of CRC configurations, as
# supplied in the arguments. Each argument is a list of the values that
# you want to iterate over. If you want to fix a particular configuration
# value, then simply pass a single-element list.
#
# Note: passing an empty list for the crcPoly will cause the function to
# iterate over all common polynomials for that length.
#
# The function returns the set of parameters that has the most success
# matching the observed CRC.
def crcIterate(dataListofLists,
               dataStartList, 
               dataStopList,
               crcPolyLen,
               crcPolyList, 
               inputBitOrderList, 
               initValList, 
               reverseFinalList,
               finalXORList, 
               padTypeList, 
               padCountList, 
               padValList):
    return 0

# This function iterates over a series of payloads and associated arithmetic
# checksum options. Each iteration uses a different set of CRC configurations, 
# as supplied in the arguments. Each argument is a list of the values that
# you want to iterate over. If you want to fix a particular configuration
# value, then simply pass a single-element list.
# The function returns the set of parameters that has the most success
# matching the observed checksum.
def checkSumIterate(dataListofLists,
                    observedChecksumList,
                    dataStartList, 
                    dataStopList, 
                    dataInvertList, 
                    dataReverseList, 
                    singleByteList, 
                    initSumList):
    return 0

# this function computes a simple arithmetic checksum and returns the 
# value in a decimal integer
def checksumCompute(dataList, 
                    dataStart, dataStop, 
                    dataInvert = False, 
                    dataReverse = CRC_REVERSE_FALSE, 
                    numOutputBits = 8, 
                    initSum = 0):

    if (dataStop - dataStart + 1) % 8 != 0:
        print("WARNING: Input data contains incomplete byte.")
        print("         Length of list should be evenly divisible by 8.")
    sum = initSum
    for i in xrange(dataStart, dataStop, 8):
        bitsInByte = dataList[i:i+8]
        if dataReverse == CRC_REVERSE_TRUE:
            sum += blu.bitsToDec(bitList=bitsInByte, 
                                 invert=dataInvert,
                                 reverse=True)
        else:
            sum += blu.bitsToDec(bitList=bitsInByte, 
                                 invert=dataInvert,
                                 reverse=False)
            
    modVal = 2**numOutputBits
    sum = sum % modVal
    if dataReverse == CRC_REVERSE_BYTES:
        print("Warning: arithmetic checksum byte swap feature not yet implemented")
    return sum

