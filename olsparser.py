#!/usr/bin/env python

import argparse, os, xlsxwriter
import json
from glob import glob

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


                    if not keepFrame:
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





                        parsedFiles[fileIndex]['channels'][channel]['binary'][hexValue]['frame'] = packet

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




############# EXPORT BINARY IN XLSX FORMAT ########################


#
#
# workbook = xlsxwriter.Workbook('trames.xlsx')
# worksheet = workbook.add_worksheet()
#
# #
# #worksheet.set_column(0,len(packetInfo['metadata']) -1, 10)
# #worksheet.set_column(len(packetInfo['metadata']),100, 1)
#
# # create styles
# cellMetadataFormat = workbook.add_format()
# cellMetadataFormat.set_font_color('red')
#
# formatZero = workbook.add_format()
# formatZero.set_font_color('#c1c1c1')
#
# formatOne = workbook.add_format()
# formatOne.set_font_color('black')
#
#
# line = 0
# for key in parsedFiles:
#     packetInfo = convertedTrames[key]
#
#     col = 0
#     for field in packetInfo['metadata']:
#         worksheet.write(line, col, packetInfo['metadata'][field], cellMetadataFormat)
#         col = col + 1
#
#     col = col + 1
#     for value in packetInfo['packet']:
#
#         if value == True:
#             value = '1'
#             cellFormat = formatOne
#         else:
#             value = '0'
#             cellFormat = formatZero
#
#         worksheet.write(line, col, value, cellFormat)
#         col = col + 1
#
#     line = line + 1
#
#
# workbook.close()






#remove rawdata
for file in parsedFiles:
    for channel in options['channelsToExport']:
        print file
        if 'rawdata' in parsedFiles[file]:
            del parsedFiles[file]['rawdata']
        del parsedFiles[file]['channels'][channel]['raw']





print json.dumps(parsedFiles, sort_keys=True, indent=4)
#



#
#
#print parsedFiles
