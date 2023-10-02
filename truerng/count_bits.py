#!/usr/bin/python

# TrueRNG Read - Simple Example
# Chris K Cockrum
# 7/9/2021
#
# Requires Python 2.7 or 3.7+, pyserial
# On Linux - may need to be root or set /dev/tty port permissions to 666
#
# Python available here: https://www.python.org/
# Install Pyserial package with:   python -m pip install pyserial

import serial
import time
import os
from serial.tools import list_ports
import numpy as np
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('--output_file', default='experiments.json')
parser.add_argument('--summary_output_file', default='summary_experiments.json')
parser.add_argument('--exp_name', default='unnamed')
parser.add_argument('--blocksize', default=1024, type=int)
parser.add_argument('--numloops', default=1024, type=int)
args = parser.parse_args()


# Number of Bytes to Capture per Block
blocksize=args.blocksize

# Number of Blocks to Capture
numloops=args.numloops

if (os.path.isfile(args.output_file)):
    #Open existing outputfile, count number of recorded trials
    previous_exps_json = json.load(open(args.output_file))
else:
    previous_exps_json = []

print(str(len(previous_exps_json))+" previous experiments found in output file "+str(args.output_file))
this_exp_json = {"experiment_name": args.exp_name,
                 "blocksize": args.blocksize,
                 "numloops": args.numloops}


# Print our header
print('TrueRNG Counting Ones vs Zeros Example')
print('http://ubld.it')
print('==================================================')

import serial.tools.list_ports

# ubld.it TrueRNG
TrueRNGpid="04D8"
TrueRNGhid="F5FE"

# ubld.it TrueRNGpro
TrueRNGpropid="16D0"
TrueRNGprohid="0AA0"

# ubld.it TrueRNGproV2
TrueRNGproV2pid="04D8"
TrueRNGproV2hid="EBB5"

# Set default of None for com port
rng_com_port = None

ports = list(serial.tools.list_ports.comports())

for p in ports:
    if(rng_com_port == None):
        if TrueRNGproV2pid and TrueRNGproV2hid in p.hwid:
           rng_com_port = p.device
           print('TrueRNGproV2 Found')
           break
        if TrueRNGpropid and TrueRNGprohid in p.hwid:
           rng_com_port = p.device
           print('TrueRNGpro Found')
           break
        if TrueRNGpid and TrueRNGhid in p.hwid:
           rng_com_port = p.device
           print('TrueRNG Found')
           break

if rng_com_port == None:
    print('TrueRNG Not Found')
    exit()

# Print which port we're using
print('Using com port:  ' + str(rng_com_port))

# Print block size and number of loops
print('Block Size:      ' + str(blocksize) + ' Bytes')
print('Number of loops: ' + str(numloops))
print('Total size:      ' + str(blocksize * numloops) + ' Bytes')
print('Writing to:      random.bin')
print('==================================================')

# Open/create the file random.bin in the current directory with 'write binary'
fp=open('random.bin','wb')

# Print an error if we can't open the file
if fp==None:
    print('Error Opening File!')

# Try to setup and open the comport
try:
    ser = serial.Serial(port=rng_com_port,timeout=10)  # timeout set at 10 seconds in case the read fails
except:
    print('Port Not Usable!')
    print('Do you have permissions set to read ' + rng_com_port + ' ?')

# Open the serial port if it isn't open
if(ser.isOpen() == False):
    ser.open()

# Set Data Terminal Ready to start flow
ser.setDTR(True)

# This clears the receive buffer so we aren't using buffered data
ser.flushInput()

# Keep track of total bytes read
totalbytes=0
totalloops=0
totalzeros=0

# Generate look-up table for number of 1's in a byte
ones_in_byte = [0] * 256
for n in range(256):
    ones_in_byte[n] = bin(n).count("1")

totalones=0
totalzeros=0

block_z_scores = []
cum_zsq_minus_1 = 0

starttime=time.time()
# Loop
for _ in range(numloops):

    # Try to read the port and record the time before and after
    try:
        x=ser.read(blocksize)   # read bytes from serial port
    except:
        print('Read Failed!!!')
        break

    # Update total bytes read
    totalbytes +=len(x)
    totalloops += 1

    #compute Z^2 - 1 for the block
    bits_in_block = len(x)*8
    ones_in_block = sum([ones_in_byte[x[n]] for n in range(len(x))])
    block_z_score = (ones_in_block - (0.5*bits_in_block))/np.sqrt(bits_in_block*0.25)
    block_z_scores.append(round(block_z_score,3))
    cum_zsq_minus_1 += (np.square(block_z_score) - 1)


    totalones += ones_in_block
    totalzeros += bits_in_block - ones_in_block

    # If we were able to open the file, write to disk
    if fp !=0:
        fp.write(x)

    # Calculate the rate
    timenow=time.time()
    if(timenow!=starttime):
        rate=float(totalbytes) / ((timenow-starttime)*1000.0)

    #print(str(totalbytes) + ' Bytes Read at ' + '{:6.2f}'.format(rate) + ' Kbytes/s',end='\r')
    print('{:0<10}'.format(round(cum_zsq_minus_1/np.sqrt(totalloops),3))
          + ' z score after '+'{:0>6}'.format(totalloops)+' loops',end='\r')

zscore_for_cumzsqm1 = cum_zsq_minus_1/np.sqrt(totalloops)

print('\n\nResults')
print(    '=======')
print('Total Ones : ' + str(totalones))
print('Total Zeros: ' + str(totalzeros) + '\n')
print('Total Bits : ' + str(totalbytes*8))
print('cum_zsq_minus_1: ' + str(cum_zsq_minus_1))
print('Z score for cum_zsq_minus_1: ' + str(zscore_for_cumzsqm1))

if (totalones==totalzeros):
    print('\nEqual Number of Ones and Zeros in Capture!')
if (totalones>totalzeros):
    print('\nThere are ' + str(totalones-totalzeros) + ' more ones in the Capture!')
else:
    print('\nThere are ' + str(totalzeros-totalones) + ' more zeros in the Capture!')

print(    '=======')

# Close the serial port
ser.close()

# If the file is open then close it
if fp != 0:
    fp.close()

#overwrite the experiments text file with updated json that has
# new experiment added
this_exp_json['block_z_scores'] = block_z_scores
this_exp_json['cum_zsq_minus_1'] = cum_zsq_minus_1
this_exp_json['zscore_for_cumzsqm1'] = zscore_for_cumzsqm1

previous_exps_json.append(this_exp_json)
with open(args.output_file,'w') as f:
    f.write(json.dumps(previous_exps_json))
with open(args.summary_output_file,'w') as f:
    summary_experiments = []
    for x in previous_exps_json:
        del x['block_z_scores']
        summary_experiments.append(x)
    f.write(json.dumps(summary_experiments, indent=4))

# If we're on Linux set min on com port back to 1
# Pyserial screws this up
if os.name == 'posix':
    os.system('stty -F '+rng_com_port+' min 1')
