# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   17:33:28, 19-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 20:33:59, 19-Jun-2020

import json
import msgpack

with open('data_pretty.json', 'r') as f:
	dat = json.load(f)

with open('data.msgpack', 'wb') as f:
	msgpack.dump(dat, f)