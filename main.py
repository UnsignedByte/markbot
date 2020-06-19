# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:	 23:20:21, 17-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 21:48:04, 18-Jun-2020

import discord
import asyncio
import re
import pickle
import os
import random
import math
import sys

class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'

queue = {}

#default file
if not os.path.isfile('data.txt'):
	with open('data.txt', 'wb') as f:
		pickle.dump({'queuelen':10, 'chain':{}}, f)

with open('data.txt', 'rb') as f:
	try:
		dat = pickle.load(f)
		ql = dat['queuelen']
		markov = dat['chain']
	except EOFError as e:
		ql = 10
		markov = {}

def updatemarkov(channelid, content):
	if channelid not in queue: queue[channelid] = ""
	queue[channelid]+=content
	while len(queue[channelid]) > ql:
		for i in range(1,ql+1):
			if queue[channelid][:i] not in markov:
				markov[queue[channelid][:i]] = {};
			if queue[channelid][i] not in markov[queue[channelid][:i]]:
				markov[queue[channelid][:i]][queue[channelid][i]] = 1;
			else:
				markov[queue[channelid][:i]][queue[channelid][i]] += 1;
		queue[channelid] = queue[channelid][1:]

def getchar(channelid, tq):
	out = '\n'
	last = queue[channelid]+tq;
	for i in range(ql,0,-1):
		if len(last) < i or last[-i:] not in markov: continue;
		curr = markov[last[-i:]]
		ret = random.choices(list(curr.keys()), weights=list(curr.values()), k=1)[0];
		if random.random() < 0.5:
			return ret
		else:
			out = ret
	return ret

def getchars(channelid):
	out = ""
	while(len(out) < 2000):
		c = getchar(channelid, out)
		out+=c;
		if out[-1] == '\n' and random.random() < 4/5: break;
	return out[:-1];

def getname(bot, msg, id):
	mem = msg.guild.get_member(id) or bot.get_user(id);
	return "" if not mem else mem.display_name;

def parseMessage(bot, msg): #replaces mentions with respective names
	return re.sub(r'<@?(.?)(:.+?:)?(\d+)>',
		lambda x:x.group(2) if x.group(2) else getname(bot, msg, int(x.group(3))) if x.group(1) in ['', '!'] else (lambda y:f'#{y.name if y else "deleted-channel"}')(bot.get_channel(int(x.group(3)))) if x.group(1) == '#' else (lambda y:f'@{y.name if y else "deleted-role"}')(msg.guild.get_role(int(x.group(3)))) if x.group(1) == '&' else x.group(0),
		msg.content
	)

#decay brain data randomly
def decay(times):
	chosenseq = random.choices(list(markov.keys()), k=times)
	for s in chosenseq:
		chosenlet = random.choice(list(markov[s].keys()))
		# decay
		# \left(\sin\frac{\pi x}{2}\right)^{\frac{1}{10}}
		markov[s][chosenlet] = int((math.sin(random.random()*math.pi/2)**0.1)*markov[s][chosenlet])

async def save():
	while 1:
		await asyncio.sleep(60);
		bsize = sys.getsizeof(markov)
		print(f'Brain is {bcolors.WARNING}{bsize}{bcolors.ENDC} bytes in size.\n Decaying...')
		times = random.randrange(int(sys.getsizeof(markov)**0.5))
		decay(times)
		nsize = sys.getsizeof(markov)
		print(f'Decayed {bcolors.WARNING}{times}{bcolors.ENDC} times.\nBrain is now {bcolors.WARNING}{nsize}{bcolors.ENDC} bytes in size.')

		print(f'{bcolors.BOLD}{bcolors.HEADER}saving...{bcolors.ENDC}')
		with open('data.txt', 'wb') as f:
			pickle.dump({'queuelen':ql, 'chain':markov}, f)
		print(f'{bcolors.OKGREEN}saved {bcolors.WARNING}{os.path.getsize("data.txt")}{bcolors.ENDC} bytes{bcolors.ENDC}\n')

async def sendMessage(channel):
	try:
		out = getchars(channel.id);
		await channel.send(getchars(channel.id));
	except Exception as e:
		print(f'{bolors.FAIL}{e}{bcolors.ENDC}')

class Client(discord.Client):
	async def on_ready(self):
		print("ready")
		await asyncio.gather(save())
	async def on_message(self, msg):
		# if msg.author.id == self.user.id: return
		parsed = parseMessage(bot, msg)
		# sys.getsizeof(markov)
		print(f'Recieved\n{parsed}\nfrom {bcolors.OKGREEN}{msg.author.display_name}{bcolors.ENDC}\n')
		if re.match(f'<@!?{self.user.id}>', msg.content):
			await sendMessage(msg.channel);
		else:
			updatemarkov(msg.channel.id, parsed+'\n')
			if random.random() < 1/30 or self.user in msg.mentions:
				await sendMessage(msg.channel);
		
bot = Client()

with open('token.txt', 'r') as f:
	bot.run(f.read().strip())