#!/usr/bin/python
# -*- coding: latin-1 -*-
# # FSK-decode
# For Python 3
# By Zoe Blade
# https://github.com/ZoeB/wave-tools/blob/master/fsk-decode.py
# (Hopefully) converts a .wav file into a demodulated .bin file

import struct # For converting the (two's complement?) binary data to integers
import sys # For command line arguments
import wave # For .wav input and output

# Set sensible defaults
amplitudeThreshold = 1024 # This has to be a number between 1 and 32767
frequencyThreshold = 1600 # This should be a number between 1 and the waveform's sample rate
baudRate = 300 # This should be the desired data rate of the (A)FSK signal
endianness = "big" # This should be either "big" or "little"
inputFilenames = ['file_1.wav']

# Override the defaults
for argument in sys.argv:
        # Override the filename
        if (argument[-4:].lower() == '.wav'):
                inputFilenames.append(argument)
                continue

if (len(inputFilenames) == 0):
        print("""\
Usage:
python3 fsk-decode.py [option...] input.wav

Options: (may appear before or after arguments)
        --amplitude-threshold=foo
                set the cutoff point between signal and noise (default is 1024, any number between 1 and 32767 is valid)
        --frequency-threshold=foo
                set the cutoff point between low and high frequency, in Hertz (default is 1600, any number between 1 and the sample rate is valid)
        --baud-rate=foo
                set the baud rate, in Hertz (default is 300, any number between 1 and the sample rate is valid)
        --endianness=foo
                set the endianness (default is "big", "little" is also valid)
        """)
        exit()

# Cycle through files
for inputFilename in inputFilenames:
        outputFilenamePrefix = inputFilename[:-4]
        outputFilenameNumber = 0

        try:
                inputFile = wave.open(inputFilename, 'r')
        except:
                print(inputFilename, "doesn't look like a valid .wav file.  Skipping.")
                continue

        print("Converting", inputFilename, "to pulse waveform")

        framerate = inputFile.getframerate()
        numberOfChannels = inputFile.getnchannels()
        sampleWidth = inputFile.getsampwidth()

    
        pulseWaveform = {}

        for iteration in range(0, inputFile.getnframes()):
                allChannelsAsBinary = inputFile.readframes(1)
                allChannelsCurrentlyBeneathThreshold = True

                for channelNumber in range (numberOfChannels):
                        channelNumber = channelNumber + 1
                        channelStart = (channelNumber - 1) * sampleWidth
                        channelEnd = channelNumber * sampleWidth
                        channelAsInteger = struct.unpack('<h', allChannelsAsBinary[channelStart:channelEnd])
                        channelAsInteger = channelAsInteger[0]

                        if (channelAsInteger >= amplitudeThreshold):
                                pulseWaveform[iteration] = True
                        else:
                                pulseWaveform[iteration] = False

                        break # Only pay attention to the first (mono or left) channel

        print("Demodulating", inputFilename)

        frequencies = {}
        highFrequency = False
        falses = 0
        lastSampleValue = 0

        for sampleAddress, sampleValue in pulseWaveform.items():
                if (lastSampleValue == False and sampleValue == True):
                        # Rising tip of waveform.  Time to measure it.
                        if (framerate / falses > frequencyThreshold):
                                # It's the highest of the two expected frequencies
                                highFrequency = True
                        else:
                                # It's the lowest of the two expected frequencies
                                highFrequency = False

                        falses = 0
                else:
                        falses = falses + 1

                lastSampleValue = sampleValue
                frequencies[sampleAddress] = highFrequency

        print("Grouping blocks of", inputFilename, "at baud rate intervals")

        data = []

        # 1 (second) / baud rate * sample rate = samples per block
        # Therefore sample rate / baud rate = samples per block
        blockSize = int(framerate / baudRate)

        lowFrequencyTally = 0
        highFrequencyTally = 0

        for sampleAddress, highFrequency in frequencies.items():
                if highFrequency == True:
                        highFrequencyTally = highFrequencyTally + 1
                else:
                        lowFrequencyTally = lowFrequencyTally + 1

                if sampleAddress % blockSize == 0:
                        # Block division!
                        if (highFrequencyTally >= lowFrequencyTally):
                                data.append(1)
                        else:
                                data.append(0)

                        lowFrequencyTally = 0
                        highFrequencyTally = 0

        print("Truncating", inputFilename)

        truncatedData = []
        copying = False

        my_string = ','.join(str(bit) for bit in data)
 
        outputFilename = inputFilename[:-4] + '.txt'
        print("Writing ", outputFilename)

        try:
                outputFile = open(outputFilename, 'w')
        except:
                print("Could not write to", outputFilename, "- skipping")
                continue

        outputFile.write(my_string)
        outputFile.close()

        print(inputFilename, "finished converting")
