#!/usr/bin/env python

import argparse
import time

def run(output_file):
	output_fh = open(output_file, 'w')
	event_count = 0
	over_count = 0
	ball_count = 0
	awaiting_event_start = True
	special_event_tag = None
	while True:
		if (awaiting_event_start):
			prompt = "Awaiting Start (OC: "+str(over_count)+"."+str(ball_count)+")\n"
		else:
			if (special_event_tag):
				prompt = "Awaiting End ("+special_event_tag+") end\n"
			else:
				prompt = "Awaiting End (OC: "+str(over_count)+"."+str(ball_count)+") end\n"
		user_input = input(prompt)
		timestamp = time.time()
		if (len(user_input)==0 or user_input.startswith("!")):
			if (awaiting_event_start):
				event_count += 1
				towrite = (str(timestamp)+"\t"+"STARTEVENT:"+str(event_count))
				if (user_input.startswith("!")): #! is for special events
					towrite += " "+user_input
					special_event_tag = user_input
				else: #Otherwise, assume standard event of ball bowled
					towrite += " OC:"+str(over_count)+"."+str(ball_count)
				print(towrite)
				output_fh.write(towrite+"\n")
				output_fh.flush()
				awaiting_event_start = False				
			else:
				towrite = str(timestamp)+"\t"+"STOPEVENT:"+str(event_count)
				print(towrite)
				output_fh.write(towrite+"\n")
				output_fh.flush()
				if (special_event_tag is None):
					ball_count += 1
				awaiting_event_start = True
				special_event_tag = None
		else:
			if (user_input=="io"): #increment over
				ball_count = 0
				over_count += 1
				towrite = (str(timestamp)+"\t"+"INCREMENTOVER:"+str(over_count))
				print(towrite)
				output_fh.write(towrite+"\n")
				output_fh.flush()
			elif (user_input=="c" and awaiting_event_start==False): #cancel event start
				awaiting_event_start = True
				towrite = str(timestamp)+"\t"+"CANCELEVENT:"+str(event_count) 
				print(towrite)
				output_fh.write(towrite+"\n")
				output_fh.flush()
				event_count -= 1
			elif (user_input=="so"): #set over
				over_count = int(input("Enter the over number: "))
				ball_count = int(input("Enter the ball count: "))
			else: #interpret as a general comment
				towrite = str(timestamp)+"\t"+"COMMENT "+user_input
				print(towrite)
				output_fh.write(towrite+"\n")
				output_fh.flush()

if __name__=="__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument("--output_file", required=True)
	args = parser.parse_args()
	run(args.output_file)
