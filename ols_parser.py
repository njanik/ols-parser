import sys, xlsxwriter, itertools

class OlsFileParser:

    inputFile = ''


    def __init__(self, inputFile):

        self.inputFile = inputFile

        headers = self.parseHeader()



        self.trames = self.parseData(headers)

        self.trames.inputfile = self.inputFile

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

    cleanedData = {}



    def __init__(self, rate, numberOfChannel):

        self.numberOfChannel = numberOfChannel
        self.rate = rate






    def addData(self, time, values):

        self.data[time] = values


    #this method return a dictionnary of the channels values but remove all unncessary entry
    #example: 0>True  10>true   12> false will be changed with:
    #           0>True  12>false  (the 10>true is not necessary)


    def getCleanData(self, channel):

        cleannedData = {}
        oldState = False
        #print self.data

        oldTime = 0
        for time in sorted(self.data):
            #print self.data[time][channel]
            if self.data[time][channel] != oldState:


                cleannedData[time] = {'state':oldState, 'duration':time - oldTime}

                oldState = self.data[time][channel]
                oldTime = time

        return cleannedData




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

            data = self.trames.getCleanData(channel)

            convertedTrames = {}
            packet = []
            startTime = 0

            for time in sorted(data):

                timeInSec = time / float(self.trames.rate)

                #print str(time)
                #print data[time]

                state = data[time]['state']
                duration = data[time]['duration']

                #start of a new trame
                if state == self.options['logicalOneState'] and duration == self.options['startTrameTime']:
                    packet = []
                    startTime = time


                elif state == self.options['logicalOneState'] and duration == self.options['logicalOneTime']:
                    packet.append(True)

                elif state == self.options['logicalZeroState'] and duration == self.options['logicalZeroTime']:
                    packet.append(False)


                elif duration > self.options['spaceBetweenTrameTime'] and len(packet) > 0:


                    toAdd = False


                    if 'errorControlSize' in self.options:
                        goodsize = False

                        for size in self.options['errorControlSize']:
                            if len(packet) == size:
                                toAdd = True
                                break

                    else:
                        toAdd = True

                    if toAdd:

                        #check if the same trame was not already added
                        binaryStr = ''
                        for value in packet:
                            binaryStr = binaryStr + str(int(value))

                        hexValue = hex(int(binaryStr, 2)),

                        frameType = 'unknown'

                        for signature in self.options['signatures']:
                            if binaryStr.startswith(signature) == True:
                                frameType = self.options['signatures'][signature]
                                break



                        keep = True

                        if 'keepOnlyFrameName' in self.options:
                            if not frameType in self.options['keepOnlyFrameName']:
                                keep = False


                        if keep and not hexValue in convertedTrames:



                            packetInfo = {
                                'metadata':
                                {
                                        'type':frameType,
                                        'file':self.trames.inputfile,
                                        'occurrence':1,
                                        'hexValue': str(hexValue),
                                        'startTime': str((startTime/float(self.trames.rate))*1000) + 'ms'
                                },

                                'packet':packet
                            }

                            keep
                            convertedTrames[hexValue] = packetInfo

                        elif keep:

                            convertedTrames[hexValue]['metadata']['occurrence'] += 1


                else:
                    pass
                    #print '*******'



            #print convertedTrames



            # Create an new Excel file and add a worksheet.
            workbook = xlsxwriter.Workbook('trames.xlsx')
            worksheet = workbook.add_worksheet()

            # Widen the first column to make the text clearer.
            #worksheet.set_column('A:A', 20)

            # Add a bold format to use to highlight cells.
            #bold = workbook.add_format({'bold': True})



            # Text with formatting.
            #worksheet.write('A2', 'World', bold)

            # Write some numbers, with row/column notation.
            #worksheet.write(2, 0, 123)
            #worksheet.write(3, 0, 123.456)


            worksheet.set_column(0,len(packetInfo['metadata']) -1, 10)
            worksheet.set_column(len(packetInfo['metadata']),100, 1)




            cellMetadataFormat = workbook.add_format()
            cellMetadataFormat.set_font_color('red')

            formatZero = workbook.add_format()
            formatZero.set_font_color('#c1c1c1')

            formatOne = workbook.add_format()
            formatOne.set_font_color('black')

            line = 0
            for key in convertedTrames:
                packetInfo = convertedTrames[key]

                col = 0
                for field in packetInfo['metadata']:
                    worksheet.write(line, col, packetInfo['metadata'][field], cellMetadataFormat)
                    col = col + 1

                col = col + 1
                for value in packetInfo['packet']:

                    if value == True:
                        value = '1'
                        cellFormat = formatOne
                    else:
                        value = '0'
                        cellFormat = formatZero

                    worksheet.write(line, col, value, cellFormat)
                    col = col + 1

                line = line + 1


            # Insert an image.
            #worksheet.insert_image('B5', 'logo.png')

            workbook.close()


parser = OlsFileParser('ols/1.ols')
trames = parser.getTrames()

exportService = TramesExporter(trames)
exportService.setOptions(
    {
        'channelsToExport':[0],
        'logicalOneState':True,
        'logicalZeroState':True,
        'logicalOneTime':1,
        'logicalZeroTime':3,
        'startTrameTime':5,
        'spaceBetweenTrameTime':10,
        'errorControlSize':[96], #72
        'signatures':{
            '00100001':'A',
            '10001011':'B',
            '10100001':'C',
            #'11000001':'D',
            '10000001':'E',
            '01001011':'F',
            '01000001':'G'
        },
        'keepOnlyFrameName':{
            'A','B'
        }
    }
)

exportService.generateXlsx()
