import sys
import fileinput


def readInstructionLine(line):
    if(line[0] == '*'):
        return
    else:
        print(line)


def main():

    n = len(sys.argv)
    if n != 3:
        print("Usage: T34.py FILE.s FILE.o") 
     
    inputFile = sys.argv[1]
    outputFile = sys.argv[2]

    for line in fileinput.input(files = inputFile):
        readInstructionLine(line)


main()