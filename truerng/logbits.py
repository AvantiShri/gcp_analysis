#!/usr/bin/env python

import serial
import time
import os
from serial.tools import list_ports
import argparse

def read_bytes(ser, num_bytes):
	the_bytes=ser.read(num_bytes)
	string_bytes = [bin(x)[2:] for x in the_bytes]
	return string_bytes

def prep_device(comport):
	ser = serial.Serial(port=comport,timeout=10)
	if(ser.isOpen() == False):
		ser.open()
	# Set Data Terminal Ready to start flow
	ser.setDTR(True)
	# This clears the receive buffer so we aren't using buffered data
	ser.flushInput()

	return ser

def run(output_file, bytes_per_interval, time_interval, comport, flushtime=1):
	
	output_fh = open(output_file, 'w')
	output_fh.write("# Bytes per interval: "+str(bytes_per_interval)+"\n")
	output_fh.write("# Time interval: "+str(time_interval)+"\n")
	
	ser = prep_device(comport)

	timenow = time.time()
	next_time = (timenow - timenow%time_interval) + time_interval
	next_flush_time = (timenow - timenow%flushtime) + flushtime
	while True:
		timenow = time.time()
		if (timenow > next_time):
			the_bytes = read_bytes(ser, num_bytes=bytes_per_interval)
			output_fh.write(str(timenow)+"\t"+(",".join(the_bytes))+"\n")

			sum_last_bits = sum([int(x[-1]) for x in the_bytes])
			timechunk = (timenow - timenow%time_interval)
			if timechunk >= (next_time + time_interval):
				print("Missed "+str((timechunk-next_time)/time_interval)+" chunks!")
			print(timechunk, sum_last_bits)
			next_time = timechunk + time_interval

		if (timenow > next_flush_time):
			output_fh.flush()
			print("Flushed!")
			next_flush_time = (timenow - timenow%flushtime) + flushtime


if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--output_file", required=True)
	parser.add_argument("--bytes_per_interval", type=int, default=200)
	parser.add_argument("--time_interval", type=float, default=0.1)
	parser.add_argument("--comport", default='COM3')
	args = parser.parse_args()
	run(output_file=args.output_file, bytes_per_interval=args.bytes_per_interval,
		time_interval=args.time_interval, comport=args.comport)
