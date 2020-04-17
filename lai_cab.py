#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 19:15:58 2019

@author: glicciardi
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 10:08:47 2019

@author: glicciardi
"""
import math
from functions_lai_cab_nn import neuron1_lai, neuron2_lai,neuron3_lai,neuron4_lai,neuron5_lai,neuron1_cab, neuron2_cab,neuron3_cab,neuron4_cab,neuron5_cab,layer2_lai,layer2_cab
from sklearn.preprocessing import minmax_scale
from utilities_lai_cab import normalize, denormalize
#sample=0
#
#min_b3=0
#max_b3=0.253061520471542
#min_b4=0
#max_b4=0.290393577911328
#min_b5=0
#max_b5=0.305398915248555
#min_b6=0.006637972542253
#max_b6=0.608900395797889
#min_b7=0.013972727018939
#max_b7=0.753827384322927
#min_b8a=0.026690138082061
#max_b8a=0.782011770669178
#min_b11=0.016388074192258
#max_b11=0.493761397883092
#min_b12=0
#max_b12=0.493025984460231
#
#viewZenithMean_min=0.918595400582046
#viewZenithMean_max=1
#sunZenithAngles_min=0.342022871159208
#sunZenithAngles_max= 0.936206429175402

degToRad = math.pi / 180

def calcola_lai(B03,B04,B05,B06,B07,B8A,B11,B12,sunZenithAngles,sunAzimuthAngles,viewZenithMean,viewAzimuthMean):
    b03_norm = normalize(B03, 0, 0.253061520471542)
    b04_norm = normalize(B04, 0, 0.290393577911328)
    b05_norm = normalize(B05, 0, 0.305398915248555)
    b06_norm = normalize(B06, 0.006637972542253, 0.608900395797889)
    b07_norm = normalize(B07, 0.013972727018939, 0.753827384322927)
    b8a_norm = normalize(B8A, 0.026690138082061, 0.782011770669178)
    b11_norm = normalize(B11, 0.016388074192258, 0.493761397883092)
    b12_norm = normalize(B12, 0, 0.493025984460231)
    viewZen_norm = normalize(math.cos(viewZenithMean * degToRad), 0.918595400582046, 1)
    sunZen_norm  = normalize(math.cos(sunZenithAngles * degToRad), 0.342022871159208, 0.936206429175402)
    relAzim_norm = math.cos((sunAzimuthAngles - viewAzimuthMean) * degToRad)


    n1 = neuron1_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n2 = neuron2_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n3 = neuron3_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n4 = neuron4_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n5 = neuron5_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)

    l2 = layer2_lai(n1, n2, n3, n4, n5)
    #lai=minmax_scale(l2, feature_range=(0.000319182538301, 14.4675094548151), axis=0, copy=True)
    lai = denormalize(l2, 0.000319182538301, 14.4675094548151)
    return lai / 3


def calcola_cab(B03,B04,B05,B06,B07,B8A,B11,B12,sunZenithAngles,sunAzimuthAngles,viewZenithMean,viewAzimuthMean):

    b03_norm = normalize(B03, 0, 0.253061520471542)
    b04_norm = normalize(B04, 0, 0.290393577911328)
    b05_norm = normalize(B05, 0, 0.305398915248555)
    b06_norm = normalize(B06, 0.006637972542253, 0.608900395797889)
    b07_norm = normalize(B07, 0.013972727018939, 0.753827384322927)
    b8a_norm = normalize(B8A, 0.026690138082061, 0.782011770669178)
    b11_norm = normalize(B11, 0.016388074192258, 0.493761397883092)
    b12_norm = normalize(B12, 0, 0.493025984460231)
    viewZen_norm = normalize(math.cos(viewZenithMean * degToRad), 0.918595400582046, 1)
    sunZen_norm  = normalize(math.cos(sunZenithAngles * degToRad), 0.342022871159208, 0.936206429175402)
    relAzim_norm = math.cos((sunAzimuthAngles - viewAzimuthMean) * degToRad)


    n1 = neuron1_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n2 = neuron2_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n3 = neuron3_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n4 = neuron4_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)
    n5 = neuron5_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm)

    l2 = layer2_cab(n1, n2, n3, n4, n5)

    cab = denormalize(l2, 0.007426692959872, 873.908222110306)
    #cab=minmax_scale(l2, feature_range=(0.007426692959872, 873.908222110306), axis=0, copy=True)
    return cab/300
