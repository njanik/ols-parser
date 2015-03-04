import sys

class OlsFileParser:

    inputFile = ''
    capturedData = None

    def __init__(self, inputFile):

        self.inputFile = inputFile

        headers = self.parseHeader()



        self.trames = self.parseData(headers)

        #self.trames.displayData()





    def getTrames(self):

        return self.trames


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


        return trames






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




class TramesExporter:

    trames = None

    options = {'channelsToExport':[0], 'logicalOneState':True, 'logicalZeroState':True, 'logicalOneTime':1, 'logicalZeroTime':3, 'startTrameTime':5, 'spaceBetweenTrameTime':10}


    def __init__(self, trames):

        self.trames = trames

    def setOptions(self, options):

        self.options.update(options)


    def generateXlsx(self):

        for channel in self.options['channelsToExport']:

            oldState = False
            stateTime = 0

            convertedTrames = []
            packet = []


            for time in sorted(self.trames.data):
                print time
                timeInSec = time / float(self.trames.rate)

                state = self.trames.data[time][channel]
                print str(timeInSec)
                print self.trames.data[time][channel]
                print '--------'


                if state == oldState:
                    stateTime = stateTime + 1

                else:
                    #change state


                    #start of a new trame
                    if state == self.options['logicalOneState'] and stateTime == self.options['startTrameTime']:
                        packet = []
                        stateTime = 0

                    #ONE
                    elif state == self.options['logicalOneState'] and stateTime == self.options['logicalOneTime']:
                        packet.append(True)
                        stateTime = 0


                    #ZERO
                    elif state == self.options['logicalZeroState'] and stateTime == self.options['logicalZeroTime']:
                        packet.append(False)
                        stateTime = 0

                    elif stateTime > self.options['spaceBetweenTrameTime']:
                        convertedTrames.append(packet)
                        stateTime = 0




                oldState = state

            print convertedTrames


parser = OlsFileParser('ols/fake.ols')
trames = parser.getTrames()

exportService = TramesExporter(trames)
exportService.setOptions({'channelsToExport':[0], 'logicalOneState':True, 'logicalZeroState':True, 'logicalOneTime':1, 'logicalZeroTime':3, 'startTrameTime':5, 'spaceBetweenTrameTime':10})
exportService.generateXlsx()
