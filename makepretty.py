# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   01:06:07, 19-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 17:35:37, 19-Jun-2020

import json
import msgpack

with open('data.msgpack', 'rb') as f:
	dat = msgpack.load(f)

with open('data_pretty.json', 'w') as f:
	json.dump(dat, f, indent=2, sort_keys=True)