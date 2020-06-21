# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   01:06:07, 19-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 01:54:31, 21-Jun-2020

import msgpack

EPSILON = 1e-9;

with open('data.msgpack', 'rb') as f:
	dat = msgpack.load(f)
	
for i in dat['chain'].keys():
	dat['chain'][i] = dict((k, v) for k, v in dat['chain'][i].items() if v > EPSILON)

dat['chain'] = dict((k, v) for k, v in dat['chain'].items() if v)

with open('data.msgpack', 'wb') as f:
	msgpack.dump(dat, f)