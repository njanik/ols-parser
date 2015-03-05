import sys, xlsxwriter

class OlsFileParser:

    inputFile = ''


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

            convertedTrames = []
            packet = []

            for time in sorted(data):

                timeInSec = time / float(self.trames.rate)

                print str(time)
                print data[time]

                state = data[time]['state']
                duration = data[time]['duration']

                #start of a new trame
                if state == self.options['logicalOneState'] and duration == self.options['startTrameTime']:
                    packet = []


                elif state == self.options['logicalOneState'] and duration == self.options['logicalOneTime']:
                    packet.append(True)

                elif state == self.options['logicalZeroState'] and duration == self.options['logicalZeroTime']:
                    packet.append(False)


                elif duration > self.options['spaceBetweenTrameTime'] and len(packet) > 0:
                    convertedTrames.append(packet)


                else:
                    print '*******'



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


            worksheet.set_column('A:FF', 1)

            formatZero = workbook.add_format()
            formatZero.set_font_color('gray')

            formatOne = workbook.add_format()
            formatOne.set_font_color('black')

            line = 0
            for packet in convertedTrames:

                col = 0
                for value in packet:

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
exportService.setOptions({'channelsToExport':[0], 'logicalOneState':True, 'logicalZeroState':True, 'logicalOneTime':1, 'logicalZeroTime':3, 'startTrameTime':5, 'spaceBetweenTrameTime':10})
exportService.generateXlsx()
