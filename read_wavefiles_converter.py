# -*- coding: utf-8 -*-
# NOTE: The WAV file must be 16bit-PCM format.
# It must be encoded at 22050Hz. 
# Only mono audio files supported at this time.
# Steps to create the file in Audacity:
# 1) Open the WAV file in Audacity.
# 2) If it is stereo, split the Stereo track to mono
# 3) Delete one of the channels
# 4) Set the Project Rate to 22050Hz
# 5) Set the Sample Format to 16-bit PCM
# 6) Export the file, leave all the file meta data fields blank
# 
# Run the script below, update the file path to the file you just exported.
# A text file is generated containing the adjusted byte content for the 
# DAC on the Photon Particle

import wave

class SoundFile:
    
    def __init__(self, filename):
        self.filename = filename
        self.file = wave.open(filename, 'rb')
        self.frameCount = self.file.getnframes()
 
    def describe(self):
        return self.file.getparams()

    def close(self):
        return self.file.close()
       
    # Returns an array of 16 bit words
    # Joins bytes of the frame array
    def byteArray(self):
        curFrame = 0
        frameArray = []
        while curFrame < self.frameCount:
            frame = self.file.readframes(1)
            # Assumes 16 bit frame
            b1 = frame[0] #right bit
            b2 = frame[1] #left bit
            b = (b2 << 8) + b1
            #print('{0:08b} {1:08b} -> {2:016b}'.format(b2, b1, b))
            frameArray.append(b)
            curFrame += 1
        return frameArray
       
    def byteFormatedString(self, bArray):
        bStrings = []
        for idx, val in enumerate(bArray):
            hexStr = ''
            if ((idx % 30 == 0) and (idx > 0)):
                hexStr += '\n'
            hexStr += ('0x{:04x}'.format(val))
            bStrings.append(hexStr)
        return  ",".join(bStrings)
        
    # Converts wave two's compliment to positive 
    # integers and shifts existing positive integers up 
    def twosToOnes(self, bArray):
        onesArray = []
        for b in bArray:
            if b > 0x8000:
                b2 = 0x8000 - (0xffff & (~b + 1))
                #print('{0:016b} NN {1:016b}'.format(b,b2))
                
            else:
                b2 = b + 0x8000
                #print('{0:016b} PP {1:016b}'.format(b,b2))
            #print('{0} -> {1}'.format(b,b2))
            onesArray.append(b2)

        return(onesArray)
        
    def toDAC12(self, bArray):
        dacArray = []
        for b in bArray:
            dacVal = b >> 4
            #print('0x{:04x}'.format(dacVal))
            #print(dacVal)            
            if dacVal > 4095:
                print('ALERT - Out of band')
            dacArray.append(b>>4)
            
        return dacArray
        
       
    def writeFile(self):
        txtName = self.filename.replace('.wav', '.h')
        txt = open(txtName, 'w')
        txt.truncate()
        txt.write('\n\n// Auto generated\nint frame_count = {};\n'.format(self.frameCount))
        txt.write('const uint16_t wave_data[{}] =\n'.format(self.frameCount))
        txt.write('{')
        bArray = self.byteArray()
        bArray = self.twosToOnes(bArray)
        bArray = self.toDAC12(bArray)
        txt.write(self.byteFormatedString(bArray))
        txt.write('};\n')
        txt.close()
       
       
def main():
    fpath = 'BB8_shake.wav'
    wav = SoundFile(fpath)
    wavProps = wav.describe()
    print(wavProps)
    print('writing file')
    wav.writeFile()
    print('done')
    
    
main()