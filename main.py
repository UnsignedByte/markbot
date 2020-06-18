# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:	 23:20:21, 17-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 03:20:20, 18-Jun-2020

import discord
import asyncio
import re
import json
import os
import random

queue = ""

#default file
if not os.path.isfile('data.json'):
	with open('data.json', 'w') as f:
		f.write(json.dumps({'queuelen':5, 'chain':{}}))

with open('data.json', 'r') as f:
	dat = json.load(f)
	ql = dat['queuelen']
	markov = dat['chain']

def updatemarkov(content):
	global queue
	queue+=content
	while len(queue) > ql:
		if queue[:ql] not in markov:
			markov[queue[:ql]] = {};
		if queue[ql] not in markov[queue[:ql]]:
			markov[queue[:ql]][queue[ql]] = 1;
		else:
			markov[queue[:ql]][queue[ql]] += 1;
		queue = queue[1:]

def getchar():
	if (len(queue) < ql or queue[-ql:] not in markov): return '\n'
	curr = markov[queue[-ql:]]
	return random.choices(list(curr.keys()), weights=list(curr.values()), k=1)[0]

def getchars():
	global queue
	out = ""
	while(len(out) < 2000):
		c = getchar()
		if len(out) > 0 or c != '\n':
			queue+=c;
		out+=c;
		if out[-1] == '\n': break;
	return out[:-1];

def getname(bot, msg, id):
	mem = msg.guild.get_member(id) or bot.get_user(id);
	return "" if not mem else mem.display_name;

def parseMessage(bot, msg): #replaces mentions with respective names
	return re.sub(r'<@?(.?)(\d+)>',
		lambda x:getname(bot, msg, int(x.group(2))) if x.group(1) in ['', '!'] else (lambda y:y.name if y else "deleted-channel")(bot.get_channel(int(x.group(2)))) if x.group(1) == '#' else (lambda y:y.name if y else "deleted-role")(msg.guild.get_role(int(x.group(2)))) if x.group(1) == '&' else x.group(0),
		msg.content
	)

async def save():
	while 1:
		await asyncio.sleep(60);
		print('saving...')
		with open('data.json', 'w') as f:
			f.write(json.dumps({'queuelen':ql, 'chain':markov}))
		print('saved')

class Client(discord.Client):
	async def on_ready(self):
		print("ready")
		await asyncio.gather(save())
	async def on_message(self, msg):
		parsed = parseMessage(bot, msg)
		if parsed == (await msg.guild.fetch_member(self.user.id)).display_name:
			try:
				await msg.channel.send(getchars());
			except Exception:
				pass;
		else:
			updatemarkov(parsed+'\n')
			if random.random() < 1/20 or self.user in msg.mentions:
				try:
					await msg.channel.send(getchars());
				except Exception:
					pass;
		
bot = Client()

with open('token.txt', 'r') as f:
	bot.run(f.read().strip())