# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:	 23:20:21, 17-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 21:24:48, 19-Jun-2020

import discord
import asyncio
import re
import msgpack
import os
import random
import math
import time
import datetime
import traceback

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
weights = {}

#default file
if not os.path.isfile('data.msgpack'):
	with open('data.msgpack', 'wb') as f:
		msgpack.dump({'queuelen':10, 'chain':{}, 'rates':{}}, f)

with open('data.msgpack', 'rb') as f:
	try:
		dat = msgpack.load(f)
		ql = dat['queuelen']
		markov = dat['chain']
		rates = dat['rates']
	except EOFError as e:
		ql = 10
		markov = {}
		rates = {}

def updatemarkov(channelid, content):
	if channelid not in queue: queue[channelid] = ""
	queue[channelid]+=content
	while len(queue[channelid]) > ql:
		for i in range(1,ql+1):
			if queue[channelid][:i] not in markov:
				markov[queue[channelid][:i]] = {};
			if queue[channelid][i] not in markov[queue[channelid][:i]]:
				markov[queue[channelid][:i]][queue[channelid][i]] = 1/weights[channelid];
			else:
				markov[queue[channelid][:i]][queue[channelid][i]] += 1/weights[channelid];
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
	return out

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
	countlost = 0;
	if len(markov) == 0: return 0;
	chosenseq = random.choices(list(markov.keys()), k=times)
	for s in chosenseq:
		if not s in markov: continue;
		total = sum(markov[s].values())
		chosenlet = random.choices(list(markov[s].keys()), k=random.randrange(len(markov[s])+1))
		for k in chosenlet:
			if not k in markov[s]: continue;
			# decay
			# \left(\cos\frac{\pi x}{2}\right)^{\frac{1}{4}} \cdot\left(\frac{\sqrt{n}+1}{2}\right)
			countlost+=markov[s][k]
			dratio = (math.sin(markov[s][k]/total*math.pi/2)**0.25)*(random.random()**0.5+1)/2;
			markov[s][k] = round(dratio*markov[s][k])
			countlost-=markov[s][k]
			if markov[s][k] == 0:
				del markov[s][k]
		if len(markov[s]) == 0:
			del markov[s]
	return countlost


savemins = 1
async def save():
	while 1:
		fsize = os.path.getsize("data.msgpack");
		a = datetime.datetime.now()
		print(f'Brain was {bcolors.WARNING}{fsize}{bcolors.ENDC} bytes with {bcolors.WARNING}{len(markov)}{bcolors.ENDC} sequences.')
		print(f'{bcolors.BOLD}{bcolors.HEADER}Decaying...{bcolors.ENDC}')
		decayed = 0
		times = 0
		for i in range(savemins):
			# \frac{2}{1+\left(1+\frac{1}{5\cdot10^{7}}\right)^{-x}}-1 
			n = int(random.random()*(2/(1+(1+10**-6/3)**-len(markov))-1)*len(markov))
			decayed += decay(n)
			times+=n
		print(f'Decayed {bcolors.WARNING}{times}{bcolors.ENDC} times, losing {bcolors.WARNING}{decayed}{bcolors.ENDC} remembrances.')
		b = datetime.datetime.now()
		print(f'Process took {bcolors.WARNING}{int((b-a).total_seconds()*1000)} ms{bcolors.ENDC}.\n')
		print(f'{bcolors.BOLD}{bcolors.HEADER}saving...{bcolors.ENDC}')
		with open('data.msgpack', 'wb') as f:
			msgpack.dump({'queuelen':ql, 'rates':rates, 'chain':markov}, f)
		print(f'Brain is now {bcolors.WARNING}{os.path.getsize("data.msgpack")}{bcolors.ENDC} bytes with {bcolors.WARNING}{len(markov)}{bcolors.ENDC} sequences.')
		print(f'Process took {bcolors.WARNING}{int((datetime.datetime.now()-b).total_seconds()*1000)} ms{bcolors.ENDC}.\n')
		await asyncio.sleep(savemins*60);

#optimal seconds between messages
msecs = 5;
async def decSecond():
	while 1:
		for k in weights.keys():
			weights[k] = max(weights[k]-1/msecs, 0);
		await asyncio.sleep(1);

async def sendMessage(channel):
	try:
		out = getchars(str(channel.id));
		async with channel.typing():
			
			await asyncio.sleep(random.random()/5*len(out))
			await channel.send(out);
	except Exception as e:
		print(f'{bcolors.FAIL}{traceback.format_exc()}{bcolors.ENDC}\n')

scaryprefix = "hi this is a wendy's and also, to marc: "
class Client(discord.Client):
	async def on_ready(self):
		print("ready")
		await asyncio.gather(save(), decSecond())
	async def on_message(self, msg):
		channelid = str(msg.channel.id)
		if not msg.author.bot and msg.content.startswith(scaryprefix):
			cont = msg.content[len(scaryprefix):];
			f = re.match(r'^sucky set rate to (\d+)/(\d+)$', cont);
			if f:
				rates[channelid] = int(f.group(1))/int(f.group(2));
				print(f"{bcolors.HEADER}Set rate for channel {msg.channel.name} to {rates[channelid]}.{bcolors.ENDC}\n")
			return;
		parsed = parseMessage(bot, msg)
		print(f'Recieved\n{parsed}\nfrom {bcolors.OKGREEN}{msg.author.display_name}{bcolors.ENDC}\n')
		if re.match(f'<@!?{self.user.id}>', msg.content):
			await sendMessage(msg.channel);
		else:
			if not channelid in weights: weights[channelid] = 0
			weights[channelid] += 1;
			updatemarkov(channelid, parsed+'\n')
			if msg.author.id != self.user.id and \
					(random.random() < (rates[channelid] if channelid in rates else 1/30) or \
					self.user in msg.mentions):
				await sendMessage(msg.channel);
		
bot = Client()

with open('token.txt', 'r') as f:
	bot.run(f.read().strip())