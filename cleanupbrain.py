# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   01:06:07, 19-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 01:14:26, 19-Jun-2020

import json

with open('data.json', 'r') as f:
	dat = json.load(f)
	
for i in dat['chain'].keys():
	dat['chain'][i] = dict((k, v) for k, v in dat['chain'][i].items() if v)

dat['chain'] = dict((k, v) for k, v in dat['chain'].items() if v)

print(dat['chain'])

with open('data.json', 'w') as f:
	json.dump(dat, f)