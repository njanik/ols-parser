

class OlsFileParser:

    inputFile = ''
    olsData = None

    def __init__(self, inputFile):


        self.olsData = OlsData()
        self.inputFile = inputFile

        self.parseHeader()




    def parseHeader(self):

        with open(self.inputFile, "r") as file:
            for line in file:
                line = line.strip()
                firstChar = line[:1]
                if firstChar != ";":
                    break
                else:
                    print line





class OlsData:


    rate = 0
    channels = 0
    enabledChannels = 0


    #def __init__(self):



    def parseHeader(self):
        return 'hello world'



parser = OlsFileParser('1.ols')
