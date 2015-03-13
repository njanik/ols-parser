#!/usr/bin/env python

import argparse, os, xlsxwriter
import json
from glob import glob





##################################################################################

def xlsxWriteHeader(wordksheet, metadataKeys):

    line = 0
    col = 0




    worksheet.set_column(len(metadataKeys),200, 1)


    #DISPLAY LEGEND OF EACH METADATA COLS
    for legend in metadataKeys:

        worksheet.write(line, col, legend, cellHeaderFormat)
        col = col + 1

    for i in range(1,200):
        worksheet.write(line, col, i, cellHeaderFormat)
        col = col + 1




##################################################################################

def xlsxWriteFrame(worksheet, line, frameInfo):


    col = 0


    for field in frameInfo['metadata']:

        if not type(frameInfo['metadata'][field]) is list:
            value = frameInfo['metadata'][field]

        else:
            #if value is a list, just display the first element with the total number of element
            value = frameInfo['metadata'][field][0]
            nb = len(frameInfo['metadata'][field])
            if nb>1:
                value += ' ('+ str(nb) +')'

                #and put all the real value in a comment
                comment = "\n".join(frameInfo['metadata'][field])


                worksheet.write_comment(line, col, comment)


        worksheet.write(line, col, value , cellMetadataFormat)
        col = col + 1


    #col = col + 1


    for state in list(frameInfo['frame']):
        if state == '1':
            cellFormat = formatOne
        else:
            cellFormat = formatZero

        worksheet.write(line, col, state , cellFormat)
        col = col + 1

    line +=1
###############################################################################








parser = argparse.ArgumentParser(description='olsparser parameters descriptions:')
parser.add_argument('-i','--inputfile', help='One OLS file or a ', required=True)
args = vars(parser.parse_args())



inputfiles = glob(args['inputfile'])


#load configuration
options = {}
execfile("config.conf", options)


parsedFiles = {}

if 'groupAllFiles' in options and options['groupAllFiles'] == True:

    parsedFiles['_GLOBAL_'] = {}
    parsedFiles['_GLOBAL_']['channels'] = {}

    for channel in options['channelsToExport']:
        parsedFiles['_GLOBAL_']['channels'][channel] = {'raw':{}, 'binary':{} }




for inputfile in inputfiles:


    with open(inputfile, "r") as file:

        parsedFiles[inputfile] = {}

        parsedFiles[inputfile]['rawdata'] = {}

        headers = {}


        for line in file:

            line = line.strip()
            firstChar = line[:1]



            if firstChar == ";":

                ################ PARSE HEADER ##################

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




            else:

                ################ PARSE DATA ##################

                values = line.split('@')

                channelsState = int(values[0], 16);
                time = int(values[1]);

                values = []

                mask = 1
                for i in range(0, headers['channels']):
                    channelState = channelsState & mask
                    mask = mask << 1

                    values.append( int(channelState > 0)  )

                parsedFiles[inputfile]['rawdata'][time] = values


        parsedFiles[inputfile]['headers'] = headers


        ################ CLEAN AND SIMPLIFY DATA ##################

        parsedFiles[inputfile]['channels'] = {}


        fileIndex = inputfile

        if 'groupAllFiles' in options and options['groupAllFiles'] == True:
            fileIndex = '_GLOBAL_'



        #init previous state
        previousState = {}
        previousTime = {}
        for channel in options['channelsToExport']:
            previousState[channel] = -1
            previousTime[channel] = 0


        for time in sorted(parsedFiles[inputfile]['rawdata']):
            values = parsedFiles[inputfile]['rawdata'][time]


            for channel in options['channelsToExport']:

                if not channel in parsedFiles[inputfile]['channels']:
                    parsedFiles[inputfile]['channels'][channel] = { 'raw':{}, 'binary':{}  }

                state = values[channel]



                #if the previous state was the same (in the current channel), we don't need to keep this value
                if previousState[channel] != state:


                    parsedFiles[inputfile]['channels'][channel]['raw'][previousTime[channel]] = {
                        'time':previousTime[channel],
                        'state':int(not state),  # 'not' because we save the previous state
                        'duration':time - previousTime[channel]
                    }

                    previousState[channel] = state
                    previousTime[channel] = time

        ################ CONVERT TO BINARY according to options parameters ##################




        for channel in options['channelsToExport']:

            lastKey = parsedFiles[inputfile]['channels'][channel]['raw'].keys()[-1]

            for time in sorted(parsedFiles[inputfile]['channels'][channel]['raw']):
                #print 'time ' + str(time)


                stateInfo = parsedFiles[inputfile]['channels'][channel]['raw'][time]

                state = stateInfo['state']
                duration = stateInfo['duration']


                #start of a new trame
                if time == 0 or state == options['logicalOneState'] and duration == options['startTrameDuration']:
                    packet = []
                    startTime = time


                elif state == options['logicalOneState'] and duration == options['logicalOneDuration']:
                    packet.append(1)

                elif state == options['logicalZeroState'] and duration == options['logicalZeroDuration']:
                    packet.append(0)


                elif len(packet) > 0 and (duration > options['minDurationBetweenTrame'] or time == lastKey):


                    #The frame is complete. This frame will now be decoded in binary

                    #check the size of frames. If not the correct size, exclude it
                    keepFrame = True
                    if 'errorControlSize' in options:
                        keepFrame = False
                        for size in options['errorControlSize']:
                            if len(packet) == size:
                                keepFrame = True
                                break





                    ########## METADATA #######################################

                    #calculate the hex value
                    binaryStr = ''
                    for value in packet:
                        binaryStr += str(value)

                    hexValue = hex(int(binaryStr, 2))


                    #Name the frame from their signatures
                    frameType = 'unknown'
                    if 'signatures' in options:
                        for signature in options['signatures']:
                            if binaryStr.startswith(signature) == True:
                                frameType = options['signatures'][signature]
                                break


                    if 'frameTypeToKeep' in options and not frameType in options['frameTypeToKeep']:
                        keepFrame = False


                    if keepFrame:

                        #save the binary data

                        startTimeStr = str((startTime/float(parsedFiles[inputfile]['headers']['rate']))*1000) + 'ms'
                        startTimeStr = os.path.basename(inputfile) + '>' + startTimeStr


                        #check if the same exact frame not already exist

                        if not hexValue in parsedFiles[fileIndex]['channels'][channel]['binary']:


                            parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue] = {}
                            parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['metadata'] = {
                                'frameType': frameType,
                                'startTimes': [startTimeStr],
                                'length': len(binaryStr),
                                'occurrence':1,
                                'files':[os.path.basename(inputfile)]
                            }

                            parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['frame'] = binaryStr



                        else:


                            #already exist.

                            #add the occurence of this frame
                            parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['metadata']['occurrence'] += 1

                            #add the the startTime (for the current file) is not already exist
                            #if not startTimeStr in parsedFiles[fileIndex]['channels']['binary'][hexValue]['metadata']['startTimes']:

                            parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['metadata']['startTimes'].append(startTimeStr)



                            #add the the filename is not already exist
                            if not os.path.basename(inputfile) in parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['metadata']['files']:
                                parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['metadata']['files'].append(os.path.basename(inputfile))





##################################   remove rawdata
for file in parsedFiles:
    for channel in options['channelsToExport']:

        if 'rawdata' in parsedFiles[file]:
            del parsedFiles[file]['rawdata']
        del parsedFiles[file]['channels'][channel]['raw']


if 'groupAllFiles' in options:
    for file in parsedFiles.keys():
        if file != '_GLOBAL_':
            del parsedFiles[file]


############# EXPORT BINARY IN XLSX FORMAT ########################


workbook = xlsxwriter.Workbook('trames.xlsx')
worksheet = workbook.add_worksheet()


firstChannel = options['channelsToExport'][0]
firstFile = parsedFiles.keys()[0]
firstHexIndex = parsedFiles[firstFile]['channels'][firstChannel]['binary'].keys()[0]

metadata = parsedFiles[firstFile]['channels'][firstChannel]['binary'][firstHexIndex]['metadata']

#worksheet.set_column(0,len(packetInfo['metadata']) -1, 10)


# create styles

cellHeaderFormat = workbook.add_format()
cellHeaderFormat.set_font_color('blue')
cellHeaderFormat.set_font_size('7')

cellMetadataFormat = workbook.add_format()
cellMetadataFormat.set_font_color('red')
cellMetadataFormat.set_font_size('9')

formatZero = workbook.add_format()
formatZero.set_font_color('#c1c1c1')


formatOne = workbook.add_format()
formatOne.set_font_color('black')
formatOne.set_bg_color('f0ffb2')



### write all frame in the first sheet

line = 1

xlsxWriteHeader(worksheet, metadata.keys())

for file in parsedFiles:

    for channel in parsedFiles[file]['channels']:

        for hexIndex in parsedFiles[file]['channels'][channel]['binary']:

            frameInfo = parsedFiles[file]['channels'][channel]['binary'][hexIndex]

            xlsxWriteFrame(worksheet, line, frameInfo)
            line += 1





# sort each frameType in each sheets ###########################

if 'signatures' in options:
    for signature in options['signatures']:

        frameType = options['signatures'][signature]

        worksheet = workbook.add_worksheet(frameType)
        line = 1

        xlsxWriteHeader(worksheet, metadata.keys())

        for file in parsedFiles:
            for channel in parsedFiles[file]['channels']:

                for hexIndex in parsedFiles[file]['channels'][channel]['binary']:

                    frameInfo = parsedFiles[file]['channels'][channel]['binary'][hexIndex]

                    if frameInfo['metadata']['frameType'] == frameType:
                        xlsxWriteFrame(worksheet, line, frameInfo)
                        line += 1


workbook.close()




#print json.dumps(parsedFiles, sort_keys=True, indent=4)
#



#
#
#print parsedFiles
