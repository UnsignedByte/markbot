# -*- coding: utf-8 -*-
# @Author: UnsignedByte
# @Date:   01:06:07, 19-Jun-2020
# @Last Modified by:   UnsignedByte
# @Last Modified time: 01:18:05, 19-Jun-2020

import json

with open('data.json', 'r') as f:
	dat = json.load(f)

with open('data_pretty.json', 'w') as f:
	json.dump(dat, f, indent=2, sort_keys=True)