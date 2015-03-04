import sys

class OlsFileParser:

    inputFile = ''
    capturedData = None

    def __init__(self, inputFile):

        self.inputFile = inputFile

        headers = self.parseHeader()



        trames = self.parseData(headers)





    def parseHeader(self):

        headers = {}

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
                        headers['rate'] = int(value)

                    elif fieldname == 'Channels':
                        headers['channels'] = int(value)

                    elif fieldname == 'EnabledChannels':
                        headers['enabledChannels'] = int(value)

        return headers




    def parseData(self, headers):

        trames = TramesData(headers['rate'], headers['channels'])

        with open(self.inputFile, "r") as file:
            for line in file:
                line = line.strip()
                firstChar = line[:1]
                if firstChar != ";":



                    values = line.split('@')

                    channelsState = int(values[0], 16);
                    time = int(values[1]);

                    values = []

                    mask = 1
                    for i in range(0, headers['channels']):
                        channelState = channelsState & mask
                        mask = mask << 1

                        values.append( channelState > 0  )

                        trames.addData(time, values)


        print trames.displayData()






class TramesData:


    rate = 0
    channelsNumber = 0


    data = {}





    def __init__(self, rate, numberOfChannel):

        self.numberOfChannel = numberOfChannel
        self.rate = rate

        self.data = {}




    def addData(self, time, values):

        self.data[time] = values


    def displayData(self):

        for time in sorted(self.data):
            print time
            timeInSec = time / float(self.rate)
            print str(timeInSec)
            print self.data[time]
            print '--------'








parser = OlsFileParser('ols/fake.ols')
