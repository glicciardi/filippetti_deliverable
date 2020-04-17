#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 19:16:26 2019

@author: glicciardi
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 10:47:31 2019

@author: glicciardi
"""

import math

def normalize(input_data,minimo,massimo):
    return 2 * (input_data - minimo) / (massimo - minimo) - 1

def denormalize(input_data,minimo,massimo):
    return 0.5 * (input_data + 1) * (massimo - minimo) + minimo

def tansig(input):
  return 2 / (1 + math.exp(-2 * input)) - 1