

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

                    line = line[1:]
                    values = line.split(':')

                    fieldname = values[0].strip()
                    value = values[1].strip()

                    if fieldname == 'Rate':
                        self.olsData.rate = value

                    elif fieldname == 'Channels':
                        self.olsData.channels = value

                    elif fieldname == 'EnabledChannels':
                        self.olsData.enabledChannels = value

        print vars(self.olsData)




class OlsData:


    rate = 0
    channels = 0
    enabledChannels = 0


    #def __init__(self):



    def parseHeader(self):
        return 'hello world'



parser = OlsFileParser('ols/1.ols')
