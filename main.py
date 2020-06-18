# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:	 23:20:21, 17-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 15:09:01, 18-Jun-2020

import discord
import asyncio
import re
import json
import os
import random

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
if not os.path.isfile('data.json'):
	with open('data.json', 'w') as f:
		f.write(json.dumps({'queuelen':5, 'chain':{}}))

with open('data.json', 'r') as f:
	dat = json.load(f)
	ql = dat['queuelen']
	markov = dat['chain']

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

def getchar(channelid):
	out = '\n'
	for i in range(ql,0,-1):
		if len(queue[channelid]) < i or queue[channelid][-i:] not in markov: continue;
		curr = markov[queue[channelid][-i:]]
		ret = random.choices(list(curr.keys()), weights=list(curr.values()), k=1)[0];
		if random.random() < 0.4:
			return ret
		else:
			out = ret
	return ret

def getchars(channelid):
	out = ""
	while(len(out) < 2000):
		c = getchar()
		if len(out) > 0 or c != '\n':
			queue[channelid]+=c;
		out+=c;
		if out[-1] == '\n': break;
	return out[:-1];

def getname(bot, msg, id):
	mem = msg.guild.get_member(id) or bot.get_user(id);
	return "" if not mem else mem.display_name;

def parseMessage(bot, msg): #replaces mentions with respective names
	return re.sub(r'<@?(.?)(:.+?:)?(\d+)>',
		lambda x:x.group(2) if x.group(2) else getname(bot, msg, int(x.group(3))) if x.group(1) in ['', '!'] else (lambda y:y.name if y else "deleted-channel")(bot.get_channel(int(x.group(3)))) if x.group(1) == '#' else (lambda y:y.name if y else "deleted-role")(msg.guild.get_role(int(x.group(3)))) if x.group(1) == '&' else x.group(0),
		msg.content
	)

async def save():
	while 1:
		await asyncio.sleep(60);
		print(f'{bcolors.OKGREEN}saving...{bcolors.ENDC}')
		with open('data.json', 'w') as f:
			out = json.dumps({'queuelen':ql, 'chain':markov})
			f.write(out)
		print(f'{bcolors.OKGREEN}saved {len(out)} characters{bcolors.ENDC}\n')

async def sendMessage(channel):
	try:
		await channel.send(getchars());
		if random.random() < 1/5:
			await sendMessage(channel);
	except Exception:
		pass;

class Client(discord.Client):
	async def on_ready(self):
		print("ready")
		await asyncio.gather(save())
	async def on_message(self, msg):
		parsed = parseMessage(bot, msg)
		print(f'Recieved\n{parsed}\nfrom {msg.author.display_name}\n')
		if re.match(f'<@!?{self.user.id}>', msg.content):
			await sendMessage(msg.channel);
		else:
			updatemarkov(msg.channel.id, parsed+'\n')
			if random.random() < 1/20 or self.user in msg.mentions:
				await sendMessage(msg.channel);
		
bot = Client()

with open('token.txt', 'r') as f:
	bot.run(f.read().strip())