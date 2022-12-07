import sys
import fileinput

programStart = 8000
pc = 8000
currentLine = 0
labelDictionary = dict()
opCodeDictionary = dict()
instructionSet = []
byteXOR = 0
byteCount = 0
errorCount = 0



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                           # 
#                                            Main                                           # 
#                                                                                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 



def main():

    global errorCount

    n = len(sys.argv)
    if n != 2:
        print("Usage: T34.py INFILE.s") 
    inputFile = sys.argv[1]
    outputFile = inputFile.replace(".s", ".o")
    global out
    out = open(outputFile, "w")

    # pass 1 ---
    for line in fileinput.input(files = inputFile):
        match addToDictionary(line):
            case -1: # bad opcode
                errorCount += 1
                outputFinalMessage()
                return -1
            case -3: # duplicate symbol
                input("WARNING: Duplicate symbol found. Press enter to continue.")
                errorCount += 1
            case -5: # memory full
                errorCount += 1
                outputFinalMessage()
                return -5    
            case -6: # bad operand
                errorCount += 1
                outputFinalMessage()
                return -6

    resetProgramCounter()
    resetCurrentLine() 

    # pass 2 ---
    for line in fileinput.input(files = inputFile):
        match readInstructionLine(line):
            case -2:
                input("WARNING: Bad addressing mode found. Press enter to continue.")
                errorCount += 1
            case -4:
                input("WARNING: Bad branch found. Press enter to continue.")
                errorCount += 1
            case -6:
                errorCount += 1
                outputFinalMessage()
                return -6 # bad operand    

    outputFinalMessage()            




# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                           # 
#                                    Primary Methods                                        # 
#                                                                                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 



def addToDictionary(line):
    global pc
    global programStart
    global currentLine
    
    currentLine += 1
    if(line[0] == '*'):
        return

    label = line[0:9].replace(" ", "").upper()
    instruction = line[9:13].replace(" ", "").replace("\n", "").upper()
    operand = line[13:25].replace(" ", "").replace("\n", "").upper()

    if instruction not in instructionSet:
        out.write("Bad opcode in line: " + str(currentLine) + "\n")
        return -1 # bad opcode

    if "*" in operand or "/" in operand or "=" in operand or "+" in operand or "-" in operand \
         or "." in operand or "&" in operand or "!" in operand or "%" in operand:
        try:
            operand = parse(operand)
        except:
            var = 0 # we'll deal with all bad opcodes later during execution 

    if (instruction == "EQU"):
        if label in labelDictionary:
            out.write("Duplicate symbol in line: " + str(currentLine) + "\n")
            return -3 # duplicate symbol
        labelDictionary[label] = operand
        if len(labelDictionary) > 255:
            out.write("Memory Full")
            return -5        

    if(label != "" and instruction != "EQU"):
        if label in labelDictionary:
            out.write("Duplicate symbol in line: " + str(currentLine) + "\n")
            return -3 # duplicate symbol
        labelDictionary[label] = "$" + str(pc).zfill(4)
        if len(labelDictionary) > 255:
            out.write("Memory Full")
            return -5

    if(instruction == "ORG"):
        programStart = operand.replace("$", "")
        pc = programStart
        return

    # all branching instructions should increment pc by 2. return in case of referencing forward label in calculation
    if(instruction == "BCC" or instruction == "BCS" or instruction == "BEQ" or instruction == "BMI"\
         or instruction == "BNE" or instruction == "BPL" or instruction == "BVC" or instruction == "BVS"):
        pc = incrementHex(pc, 2)
        return

    if(instruction == "JSR" or instruction == "JMP"):
        pc = incrementHex(pc, 3)
        return

    if(instruction != "EQU"):
        if(instruction != ""):
            pc = incrementHex(pc)    
        if(operand != ""):
            match determineAddressingType(operand):
                case "immediate" | "zero page" | "zero page,x" | "(indirect,x)" | "(indirect),y":
                    pc = incrementHex(pc)                    
                case "absolute" | "absolute,x" | "absolute,y":
                    pc = incrementHex(pc, 2)  

    # check for full memory
    if int(str(pc).replace("$", ""), 16) > 65535:
        out.write("Memory Full")
        return -5                   



def determineAddressingType(operand):

    operand = str(operand).replace(" ", "")

    if (operand == ""):
        return "implied"
    if(operand[0].isalpha() and (len(operand) != 1 or operand[0] != "A")):
        operand = labelDictionary[operand]
    if (len(operand) == 1 and operand[0] == "A"):
        return "accumulator"
    elif (operand[0] == "#"):
        return "immediate"
    elif (operand[0] == "$" and operand[len(operand) - 1].lower() == "x"):
        if hexIsGreaterThanFF(operand.replace(",", "").replace("x", "").replace("X", "")):
            return "absolute,x"
        else:
            return "zero page,x"  
    elif (operand[0] == "$" and operand[len(operand) - 1].lower() == "y"):
        if hexIsGreaterThanFF(operand.replace(",", "").replace("y", "").replace("Y", "")):
            return "absolute,y"
        else:
            return "zero page,y"     
    elif (operand[0] == "$"):
        if(hexIsGreaterThanFF(operand)):
            return "absolute"
        else:
            return "zero page"  
    elif (operand[0] == "(" and operand[len(operand) - 1] == ")" and operand[len(operand) - 2].lower() == "x"):
        return "(indirect,x)"
    elif (operand[0] == "(" and operand[len(operand) - 1] == ")" and operand[len(operand) - 2].lower() == "y"):
        return "(indirect,y)"
    elif (operand[0] == "(" and operand[len(operand) - 1].lower() == "x"):
        return "(indirect),x"          
    elif (operand[0] == "(" and operand[len(operand) - 1].lower() == "y"):
        return "(indirect),y"
    elif (operand[0] == "(" and operand[len(operand)- 1] == ")"):
        return "indirect"    



def readInstructionLine(line):
    global pc
    global currentLine
    global byteXOR

    currentLine += 1
    if len(line) > 64:
        out.write("Bad operand on line: " + str(currentLine))
        return -6
    if(line[0] == '*'):
        return
    label = line[0:9].replace(" ", "").replace("\n", "").upper()
    instruction = line[9:13].replace(" ", "").replace("\n", "").upper()
    operand = line[13:25].replace(" ", "").replace("\n", "").upper()


    for key in labelDictionary:
        if key in operand:
            operand = operand.replace(key, labelDictionary[key])

    if instruction == "END" or instruction == "EQU":
        return

    if instruction == "ORG":
        programStart = operand.replace("$", "")
        pc = programStart     
        return   

    if instruction == "CHK":
        write(str(hex(byteXOR).replace("0x", "")).upper())
        pc = incrementHex(pc)
        return


    if "*" in operand or "/" in operand or "=" in operand or "+" in operand or "-" in operand \
         or "." in operand or "&" in operand or "!" in operand or "%" in operand:
        try:
            operand = parse(operand)
        except:
            out.write("Bad operand on line: " + str(currentLine))
            return -6

    if instruction == "BCC" or instruction == "BCS" or instruction == "BEQ" or instruction == "BMI" or instruction == "BNE"\
    or instruction == "BPL" or instruction == "BVC" or instruction == "BVS":
        try:
            operand = subHex(operand, addHex(pc, 2)).replace("0x", "")  
            if hexIsGreaterThanFF(operand):
                out.write("Bad branch in line: " + str(currentLine) + "\n")
                return -4 # bad branch
            operand = str(hex(int(operand, 16) & 255)).replace("0x", "").upper()    
            opcode = opCodeDictionary[instruction + " relative"]
            write(opcode, operand.replace("$", ""))  
            pc = incrementHex(pc, 2)
        except:
            out.write("Bad address mode in line: " + str(currentLine) + "\n")
            return -2
        return

    addressingType = determineAddressingType(operand)

    try:
        if addressingType == "implied":
            opcode = opCodeDictionary[instruction]
        else:
            opcode = opCodeDictionary[instruction + " " + addressingType]   
    except:
        out.write("Bad address mode in line: " + str(currentLine) + "\n")        
        return -2
    match addressingType:
        case "implied":
            write(opcode)
            pc = incrementHex(pc)
        case "immediate":
            write(opcode, operand.replace("#$", ""))
            pc = incrementHex(pc, 2)
        case "zero page":
            write(opcode, operand.replace("$", ""))
            pc = incrementHex(pc, 2)                    
        case "zero page,x":
            write(opcode, operand.replace("$", "").replace(",X", ""))
            pc = incrementHex(pc, 2)                      
        case "absolute":
            write(opcode, operand[3] + operand[4], operand[1] + operand[2])
            pc = incrementHex(pc, 3)                      
        case "absolute,x":
            write(opcode, operand[3] + operand[4], operand[1] + operand[2])
            pc = incrementHex(pc, 3)                      
        case "absolute,y":
            write(opcode, operand[3] + operand[4], operand[1] + operand[2])
            pc = incrementHex(pc, 3)                      
        case "(indirect,x)":
            write(opcode, operand[2] + operand[3])
            pc = incrementHex(pc, 2)                      
        case "(indirect),y":
            write(opcode, operand[2] + operand[3])
            pc = incrementHex(pc, 2)       



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                           # 
#                                     Utility Functions                                     # 
#                                                                                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

def outputFinalMessage():
    out.write("\n--End assembly, " + str(byteCount) + " bytes, Errors: " + str(errorCount))

def incrementHex(hexNum, incAmount = 1):
    hexNum = str(hexNum).replace("$", "")
    return hex(int(hexNum, 16) + incAmount).replace("0x", "").upper()

def addHex(hexNum1, hexNum2):
    hexNum1 = str(hexNum1).replace("$", "")
    hexNum2 = str(hexNum2).replace("$", "")
    return hex(int(hexNum1, 16) + int(hexNum2, 16)).replace("0x", "").upper()

def subHex(hexNum1, hexNum2):
    hexNum1 = str(hexNum1).replace("$", "")
    hexNum2 = str(hexNum2).replace("$", "")
    return hex(int(hexNum1, 16) - int(hexNum2, 16)).replace("0x", "").upper()

def hexIsGreaterThanFF(hexNum):
    return int(hexNum.replace("$", ""), 16) > 255

def resetProgramCounter():
    global pc
    global programStart
    pc = programStart

def resetCurrentLine():
    global currentLine
    currentLine = 0

def write(opcode, byte1= "", byte2 = ""):
    global byteXOR
    global byteCount
    global pc
    
    if byte1 != "":
        byte1 = byte1.zfill(2)
        byteXOR ^= int(byte1, 16)
        byteCount += 1
    if byte2 != "":
        byte2 = byte2.zfill(2)
        byteXOR ^= int(byte2, 16)
        byteCount += 1
    byteXOR ^= int(opcode, 16)
    byteCount += 1

    out.write(str(pc) + ": " + opcode + " " + byte1 + " " + byte2 + "\n")    


def parse(operand):
    x = str(operand)
    operators = set('+-*/&.!')
    opList = []
    numList = []
    buffer = []
    for c in x:
        if c == "*":
            if len(numList) >= len(opList) + len(buffer):
                buffer.append(str(int(str(pc), 16)))
                continue
        if c in operators:  
            numList.append(''.join(buffer))
            buffer = []
            opList.append(c)
        else:
            buffer.append(c) 
    numList.append(''.join(buffer))

    # convert all the elements of numList to decimal
    for index in range(len(numList)):
        if numList[index][0] == "%":
            numList[index] = int(numList[index].replace("%", ""), 2)
        elif numList[index][0] == "$" or numList[index][0] == "#":
            numList[index] = int(numList[index].replace("$", "").replace("#", ""), 16)       
        elif numList[index][0] == "O":
            numList[index] = int(numList[index].replace("O", ""), 8)
        elif numList[index][0].isalpha():
            numList[index] = int(str(labelDictionary[numList[index]]).replace("$", ""), 16)    
        else:
            numList[index] = int(numList[index].replace("#", ""))    

    while len(opList) != 0:
        if opList[0] == "+":
            numList[0] = int(numList[0] + numList[1])
            numList.pop(1)
        elif opList[0] == "-":
            numList[0] = int(numList[0] - numList[1])
            numList.pop(1)
        elif opList[0] == "/":
            numList[0] = int(numList[0] // numList[1])
            numList.pop(1)
        elif opList[0] == "*":
            numList[0] = int(numList[0] * numList[1])
            numList.pop(1)
        elif opList[0] == "!":
            numList[0] = int(numList[0] ^ numList[1])
        elif opList[0] == ".":
            numList[0] = int(numList[0] | numList[1])
        elif opList[0] == "&":        
            numList[0] = int(numList[0] & numList[1])
        opList.pop(0)
    returnValue = hex(int(str(numList[0]).replace(".0", ""))).replace("0x", "").upper()
    if len(returnValue) == 1:
        returnValue = returnValue.zfill(2)
    elif len(returnValue) == 3:
        returnValue = returnValue.zfill(4)
    return "$" + returnValue



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#                                                                                           # 
#                                   Dictionary Creation                                     # 
#                                                                                           #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 



opCodeDictionary["ADC immediate"] = "69"
opCodeDictionary["ADC zero page"] = "65"
opCodeDictionary["ADC zero page,x"] = "75"
opCodeDictionary["ADC absolute"] = "6D"
opCodeDictionary["ADC absolute,x"] = "7D"
opCodeDictionary["ADC absolute,y"] = "79"
opCodeDictionary["ADC (indirect,x)"] = "61"
opCodeDictionary["ADC (indirect),y"] = "71"

opCodeDictionary["AND immediate"] = "29"
opCodeDictionary["AND zero page"] = "25"
opCodeDictionary["AND zero page,x"] = "35"
opCodeDictionary["AND absolute"] = "2D"
opCodeDictionary["AND absolute,x"] = "3D"
opCodeDictionary["AND absolute,y"] = "39"
opCodeDictionary["AND (indirect,x)"] = "21"
opCodeDictionary["AND (indirect),y"] = "31"

opCodeDictionary["ASL"] = "0A"
opCodeDictionary["ASL accumulator"] = "0A"
opCodeDictionary["ASL zero page"] = "06"
opCodeDictionary["ASL zero page,x"] = "16"
opCodeDictionary["ASL absolute"] = "0E"
opCodeDictionary["ASL absolute,x"] = "1E"

opCodeDictionary["BCC relative"] = "90"

opCodeDictionary["BCS relative"] = "B0"

opCodeDictionary["BEQ relative"] = "F0"

opCodeDictionary["BIT zero page"] = "24"
opCodeDictionary["BIT absolute"] = "2C"

opCodeDictionary["BMI relative"] = "30"

opCodeDictionary["BNE relative"] = "D0"

opCodeDictionary["BPL relative"] = "10"

opCodeDictionary["BRK"] = "00"

opCodeDictionary["BVC relative"] = "50"

opCodeDictionary["BVS relative"] = "70"

opCodeDictionary["CLC"] = "18"

opCodeDictionary["CLD"] = "D8"

opCodeDictionary["CLI"] = "58"

opCodeDictionary["CLV"] = "B8"

opCodeDictionary["CMP immediate"] = "C9"
opCodeDictionary["CMP zero page"] = "C5"
opCodeDictionary["CMP zero page,x"] = "D5"
opCodeDictionary["CMP absolute"] = "CD"
opCodeDictionary["CMP absolute,x"] = "DD"
opCodeDictionary["CMP absolute,y"] = "D9"
opCodeDictionary["CMP (indirect,x)"] = "C1"
opCodeDictionary["CMP (indirect),y"] = "D1"

opCodeDictionary["CPX immediate"] = "E0"
opCodeDictionary["CPX zero page"] = "E4"
opCodeDictionary["CPX absolute"] = "EC"

opCodeDictionary["CPY immediate"] = "C0"
opCodeDictionary["CPY zero page"] = "C4"
opCodeDictionary["CPY absolute"] = "CC"

opCodeDictionary["DEC zero page"] = "C6"
opCodeDictionary["DEC zero page,x"] = "D6"
opCodeDictionary["DEC absolute"] = "CE"
opCodeDictionary["DEC absolute,x"] = "DE"

opCodeDictionary["DEX"] = "CA"

opCodeDictionary["DEY"] = "88"

opCodeDictionary["EOR immediate"] = "49"
opCodeDictionary["EOR zero page"] = "45"
opCodeDictionary["EOR zero page,x"] = "55"
opCodeDictionary["EOR absolute"] = "4D"
opCodeDictionary["EOR absolute,x"] = "5D"
opCodeDictionary["EOR absolute,y"] = "59"
opCodeDictionary["EOR (indirect,x)"] = "41"
opCodeDictionary["EOR (indirect),y"] = "51"


opCodeDictionary["INC zero page"] = "E6"
opCodeDictionary["INC zero page,x"] = "F6"
opCodeDictionary["INC absolute"] = "EE"
opCodeDictionary["INC absolute,x"] = "FE"

opCodeDictionary["INX"] = "E8"

opCodeDictionary["INY"] = "C8"

opCodeDictionary["JMP absolute"] = "4C"
opCodeDictionary["JMP indirect"] = "6C"

opCodeDictionary["JSR absolute"] = "20"

opCodeDictionary["LDA immediate"] = "A9"
opCodeDictionary["LDA zero page"] = "A5"
opCodeDictionary["LDA zero page,x"] = "B5"
opCodeDictionary["LDA absolute"] = "AD"
opCodeDictionary["LDA absolute,x"] = "BD"
opCodeDictionary["LDA absolute,y"] = "B9"
opCodeDictionary["LDA (indirect,x)"] = "A1"
opCodeDictionary["LDA (indirect),y"] = "B1"

opCodeDictionary["LDX immediate"] = "A2"
opCodeDictionary["LDX zero page"] = "A6"
opCodeDictionary["LDX zero page,y"] = "B6"
opCodeDictionary["LDX absolute"] = "AE"
opCodeDictionary["LDX absolute,y"] = "BE"

opCodeDictionary["LDY immediate"] = "A0"
opCodeDictionary["LDY zero page"] = "A4"
opCodeDictionary["LDY zero page,x"] = "B4"
opCodeDictionary["LDY absolute"] = "AC"
opCodeDictionary["LDY absolute,x"] = "BC"

opCodeDictionary["LSR"] = "4A"
opCodeDictionary["LSR accumulator"] = "4A"
opCodeDictionary["LSR zero page"] = "46"
opCodeDictionary["LSR absolute"] = "4E"
opCodeDictionary["LSR absolute,x"] = "5E"

opCodeDictionary["NOP"] = "EA"

opCodeDictionary["ORA immediate"] = "09"
opCodeDictionary["ORA zero page"] = "05"
opCodeDictionary["ORA zero page,x"] = "15"
opCodeDictionary["ORA absolute"] = "0D"
opCodeDictionary["ORA absolute,x"] = "1D"
opCodeDictionary["ORA absolute,y"] = "19"
opCodeDictionary["ORA (indirect,x)"] = "01"
opCodeDictionary["ORA (indirect),y"] = "11"

opCodeDictionary["PHA"] = "48"

opCodeDictionary["PHP"] = "08"

opCodeDictionary["PLA"] = "68"

opCodeDictionary["PLP"] = "28"

opCodeDictionary["ROL"] = "2A"
opCodeDictionary["ROL accumulator"] = "2A"
opCodeDictionary["ROL zero page"] = "26"
opCodeDictionary["ROL zero page,x"] = "36"
opCodeDictionary["ROL absolute"] = "2E"
opCodeDictionary["ROL absolute,x"] = "3E"

opCodeDictionary["ROR"] = "6A"
opCodeDictionary["ROR accumulator"] = "6A"
opCodeDictionary["ROR zero page"] = "66"
opCodeDictionary["ROR zero page,x"] = "76"
opCodeDictionary["ROR absolute"] = "6E"
opCodeDictionary["ROR absolute,x"] = "7E"

opCodeDictionary["RTI"] = "40"

opCodeDictionary["RTS"] = "60"

opCodeDictionary["SBC immediate"] = "E9"
opCodeDictionary["SBC zero page"] = "E5"
opCodeDictionary["SBC zero page,x"] = "F5"
opCodeDictionary["SBC absolute"] = "ED"
opCodeDictionary["SBC absolute,x"] = "FD"
opCodeDictionary["SBC absolute,y"] = "F9"
opCodeDictionary["SBC (indirect,x)"] = "E1"
opCodeDictionary["SBC (indirect),y"] = "F1"

opCodeDictionary["SEC"] = "38"

opCodeDictionary["SED"] = "F8"

opCodeDictionary["SEI"] = "78"

opCodeDictionary["STA zero page"] = "85"
opCodeDictionary["STA zero page,x"] = "95"
opCodeDictionary["STA absolute"] = "8D"
opCodeDictionary["STA absolute,x"] = "9D"
opCodeDictionary["STA absolute,y"] = "99"
opCodeDictionary["STA (indirect,x)"] = "81"
opCodeDictionary["STA (indirect),y"] = "91"

opCodeDictionary["STX zero page"] = "86"
opCodeDictionary["STX zero page,y"] = "96"
opCodeDictionary["STX absolute"] = "8E"

opCodeDictionary["STY zero page"] = "84"
opCodeDictionary["STY zero page,x"] = "94"
opCodeDictionary["STY absolute"] = "8C"

opCodeDictionary["TAX"] = "AA"

opCodeDictionary["TAY"] = "A8"

opCodeDictionary["TSX"] = "BA"

opCodeDictionary["TXA"] = "8A"

opCodeDictionary["TXS"] = "9A"

opCodeDictionary["TYA"] = "98"

instructionSet = [
"ADC", "AND", "ASL", "BCC", "BCS", "BEQ", "BIT", "BMI", "BNE", "BPL", "BRK", "BVC",
"BVS", "CHK", "CLC", "CLD", "CLI", "CLV", "CMP", "CPX", "CPY", "DEC", "DEX", "DEY", "END", "EOR",
"EQU", "INC", "INX", "INY", "JMP", "JSR", "LDA", "LDY", "LDX", "LSR", "NOP", "ORA", "ORG", 
"PHA", "PHP", "PLA", "PLP", "ROL", "ROR", "RTI", "RTS", "SBC", "SEC", "SED", "SEI", 
"STA", "STX", "STY", "TAX", "TAY", "TSX", "TXA", "TXS", "TYA"
]

main()