# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:	 23:20:21, 17-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 08:50:58, 25-Aug-2020

import json
import discord
import asyncio
import re
import os
import psutil
import random
import math
import time
import datetime
import traceback
import Levenshtein
# import nest_asyncio
# nest_asyncio.apply()

class bcolors:
  HEADER = '\033[95m'
  OKBLUE = '\033[94m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  FAIL = '\033[91m'
  ENDC = '\033[0m'
  BOLD = '\033[1m'
  UNDERLINE = '\033[4m'


process = psutil.Process(os.getpid()) # python process

#strings in queue (by channel)???
queue = {}

#user message rate sort of
weights = {}

#last messsages in each channel
lastmsgs = {}

# queued messages existing?
queued = {}

# when to snap the thing
EPSILON = 100;

#default file
if not os.path.isdir('data/config.json'):
	with open('data/config.json', 'w') as f:
		json.dump({'queuelen':15, 'rates':{}}, f, indent=2)

with open('data/config.json', 'r') as f:
	try:
		dat = json.load(f)
		ql = dat['queuelen']
		rates = dat['rates']
	except EOFError as e:
		ql = 15
		rates = {}

def toweight(msg):
	# 1-\frac{1}{1+\frac{\sqrt{\frac{x}{2000}}}{1-\frac{x}{2000}}^{-3}}
	return  int(1000*((0.5 if msg.author.bot else 1) # we don't like bots that much
				* (lambda x: 1 if x == 0 else 1-(1/(1+(x/(1-x))**-3)))(len(msg.content)/2001) # long messages also bad
				/ weights[msg.author.id] # spammers >:(
				* (1-max([Levenshtein.ratio(msg.content, m)**2 for m in lastmsgs[msg.channel.id][msg.author.id]] + [0])))) # same messages bad

def ssplit(s):
	return ['f\\' if x is '/' else x for x in list(s)];

def toPath(s):
	return os.path.join('data', *ssplit(s), 'data.json');

def exists(s):
	return os.path.isfile(toPath(s));

def read(s):
	try:
		return json.load(open(toPath(s), 'r'));
	except ValueError:
		return {};

def write(s, v):
	os.makedirs(os.path.join('data', *ssplit(s)), exist_ok=True)
	return json.dump(v, open(toPath(s), 'w'));

def updatemarkov(channelid, content, weight):
	queue[channelid]+=content

	# small weight, skip other stuff
	if (weight < EPSILON):
		if len(queue[channelid]) > ql:
			queue[channelid] = queue[channelid][-ql:];
		return;
	while len(queue[channelid]) > ql:
		for i in range(1,ql+1):
			v = {};
			if exists(queue[channelid][:i]):
				v = read(queue[channelid][:i]);
			if queue[channelid][i] not in v:
				v[queue[channelid][i]] = weight;
			else:
				v[queue[channelid][i]] += weight;
			write(queue[channelid][:i], v);
		queue[channelid] = queue[channelid][1:]

def getchar(channelid, tq):
	out = '\n'
	last = queue[channelid]+tq;
	for i in range(ql,0,-1):
		l = toPath(last[-i:]);
		if len(last) < i or not exists(last[-i:]): continue;
		curr = read(last[-i:]);
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
		if out[-1] == '\r':
			if len(out) > 1: break;
			out = "";
	return out[:-1];

def getname(bot, msg, id):
	if not msg.guild: return bot.get_user(id).display_name;
	mem = msg.guild.get_member(id) or bot.get_user(id);
	return "" if not mem else mem.display_name;

def parseMessage(bot, msg): #replaces mentions with respective names
	# return re.sub(r'<@?(.?)(:.+?:)?(\d+)>',
	# 	lambda x:x.group(2) if x.group(2) else f"@{getname(bot, msg, int(x.group(3)))}" if x.group(1) in ['', '!'] else (lambda y:f'#{y.name if y else "deleted-channel"}')(bot.get_channel(int(x.group(3)))) if x.group(1) == '#' else (lambda y:f'@{y.name if y else "deleted-role"}')(msg.guild.get_role(int(x.group(3)))) if x.group(1) == '&' else x.group(0),
	# 	msg.content
	# )
	return (re.sub(r'<@?(.?)(:.+?:)?(\d+)>',
		lambda x:x.group(0) if x.group(2) else f"@{getname(bot, msg, int(x.group(3)))}" if x.group(1) in ['', '!'] else x.group(0),
		msg.content
	)+''.join('\n'+x.url for x in msg.attachments)).strip()

#decay brain data randomly
# def decay(times):
# 	countlost = 0;
# 	if len(markov) == 0: return 0;
# 	chosenseq = random.choices(list(markov.keys()), k=times)
# 	for s in chosenseq:
# 		if not s in markov: continue;
# 		total = sum(markov[s].values())
# 		chosenlet = random.choices(list(markov[s].keys()), k=len(markov[s])//2+1)
# 		for k in chosenlet:
# 			if not k in markov[s]: continue;
# 			# decay
# 			# \left(\cos\frac{\pi x}{2}\right)^{\frac{1}{4}} \cdot\left(\frac{\sqrt{n}+1}{2}\right)
# 			countlost+=markov[s][k]
# 			markov[s][k] = int(max(0.1, math.sin(markov[s][k]/total*math.pi/2)**0.25)*(random.random()**0.5+1)/2*markov[s][k])
# 			countlost-=markov[s][k]
# 			if markov[s][k] < EPSILON:
# 				del markov[s][k]
# 		if len(markov[s]) == 0:
# 			del markov[s]
# 	return countlost


savemins = 1
async def save():
	finished = datetime.datetime.now();
	while 1:
		fsize = os.path.getsize("data/");

		print(f'{bcolors.WARNING}{(datetime.datetime.now()-finished).total_seconds()} seconds{bcolors.ENDC} have elapsed.')

		a = datetime.datetime.now()
		print(f'Brain is {bcolors.WARNING}{fsize}{bcolors.ENDC} bytes.')
		

		print(f'{bcolors.BOLD}{bcolors.HEADER}saving...{bcolors.ENDC}')
		with open('data/config.json', 'w') as f:
			json.dump({'queuelen':ql, 'rates':rates}, f, indent=2)
		finished = datetime.datetime.now();
		print(f'Process took {bcolors.WARNING}{int((finished-a).total_seconds()*1000)} ms{bcolors.ENDC}.\n')

		await asyncio.sleep(savemins*60)

#optimal seconds between messages
msecs = 2;
async def decSecond():
	while 1:
		for k in weights.keys():
			weights[k] = max(weights[k]-1/msecs, 0);
		await asyncio.sleep(1);

async def sendMessage(channel):
	if channel.id in queued and queued[channel.id]: return;
	queued[channel.id] = True;
	try:
		out = getchars(str(channel.id));
		async with channel.typing():
			await asyncio.sleep(random.random()/10*len(out))
			await channel.send(out);
	except Exception as e:
		print(f'{bcolors.FAIL}{traceback.format_exc()}{bcolors.ENDC}\n')
	finally:
		queued[channel.id] = False;

started = False
savedmsgnum = 10;
scaryprefix = "hi this is a wendy's and also, to marc: "
class Client(discord.Client):
	async def on_ready(self):
		global started
		print("ready")
		if started:
			return
		started = True
		asyncio.gather(save(), decSecond())
	async def on_message(self, msg):
		channelid = str(msg.channel.id)
		if channelid not in queue: queue[channelid] = ""
		if not msg.author.bot and msg.content.startswith(scaryprefix) and msg.author.id == 418827664304898048:
			cont = msg.content[len(scaryprefix):];
			f = re.match(r'^sucky set rate to (\d+)/(\d+)$', cont);
			if f:
				rates[channelid] = int(f.group(1))/int(f.group(2));
				print(f"{bcolors.HEADER}Set rate for channel {msg.channel.name} to {rates[channelid]}.{bcolors.ENDC}\n")
			return;
		parsed = parseMessage(bot, msg)
		if re.match(f'^<@!?{self.user.id}>$', msg.content):
			await sendMessage(msg.channel);
		else:
			if not msg.author.id in weights: weights[msg.author.id] = 0
			if not msg.channel.id in lastmsgs: lastmsgs[msg.channel.id] = {};
			if not msg.author.id in lastmsgs[msg.channel.id]: lastmsgs[msg.channel.id][msg.author.id] = [];
			weights[msg.author.id] += 1;
			weight = toweight(msg);
			lastmsgs[msg.channel.id][msg.author.id] = lastmsgs[msg.channel.id][msg.author.id][-savedmsgnum:] + [msg.content];
			print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: Recieved\n{parsed}\nfrom {bcolors.OKGREEN}{msg.author.display_name}{bcolors.ENDC} with weight {bcolors.OKGREEN}{weight/1000}{bcolors.ENDC} ({bcolors.OKGREEN}{weights[msg.author.id]}{bcolors.ENDC} message(s) queued).\n')
			updatemarkov(channelid, parsed+'\r', weight)

			if random.random() < 1/50:
				await msg.add_reaction('⭐');
			if msg.author.id != self.user.id and \
					(random.random() < (rates[channelid] if channelid in rates else 1/50) or \
					self.user in msg.mentions):
				await sendMessage(msg.channel);

bot = Client()

with open('token.txt', 'r') as f:
	bot.run(f.read().strip(), bot=True)
