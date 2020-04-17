#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 20 19:15:22 2019

@author: glicciardi
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 10:16:44 2019

@author: glicciardi
"""
from utilities_lai_cab import tansig,normalize, denormalize
import math




def neuron1_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma= 4.96238030555279- 0.023406878966470 * b03_norm+ 0.921655164636366 * b04_norm+ 0.135576544080099 * b05_norm- 1.938331472397950 * b06_norm- 3.342495816122680 * b07_norm+ 0.902277648009576 * b8a_norm+ 0.205363538258614 * b11_norm- 0.040607844721716 * b12_norm- 0.083196409727092 * viewZen_norm+ 0.260029270773809 * sunZen_norm+ 0.284761567218845 * relAzim_norm
    return tansig(somma)
    
def neuron2_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma= 1.416008443981500- 0.132555480856684 * b03_norm- 0.139574837333540 * b04_norm- 1.014606016898920 * b05_norm- 1.330890038649270 * b06_norm+ 0.031730624503341 * b07_norm- 1.433583541317050 * b8a_norm- 0.959637898574699 * b11_norm+ 1.133115706551000 * b12_norm+ 0.216603876541632 * viewZen_norm+ 0.410652303762839 * sunZen_norm+ 0.064760155543506 * relAzim_norm
    return tansig(somma)
    

def neuron3_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=1.075897047213310+ 0.086015977724868 * b03_norm+ 0.616648776881434 * b04_norm+ 0.678003876446556 * b05_norm+ 0.141102398644968 * b06_norm- 0.096682206883546 * b07_norm- 1.128832638862200 * b8a_norm+ 0.302189102741375 * b11_norm+ 0.434494937299725 * b12_norm- 0.021903699490589 * viewZen_norm- 0.228492476802263 * sunZen_norm- 0.039460537589826 * relAzim_norm
    return tansig(somma)

def neuron4_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=1.533988264655420- 0.109366593670404 * b03_norm- 0.071046262972729 * b04_norm+ 0.064582411478320 * b05_norm+ 2.906325236823160 * b06_norm- 0.673873108979163 * b07_norm- 3.838051868280840 * b8a_norm+ 1.695979344531530 * b11_norm+ 0.046950296081713 * b12_norm- 0.049709652688365 * viewZen_norm+ 0.021829545430994 * sunZen_norm+ 0.057483827104091 * relAzim_norm
    return tansig(somma)

def neuron5_lai(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=3.024115930757230- 0.089939416159969 * b03_norm+ 0.175395483106147 * b04_norm- 0.081847329172620 * b05_norm+ 2.219895367487790 * b06_norm+ 1.713873975136850 * b07_norm+ 0.713069186099534 * b8a_norm+ 0.138970813499201 * b11_norm- 0.060771761518025 * b12_norm+ 0.124263341255473 * viewZen_norm+ 0.210086140404351 * sunZen_norm- 0.183878138700341 * relAzim_norm   
    return tansig(somma)


def layer2_lai(neuron1, neuron2, neuron3, neuron4, neuron5):
    somma =1.096963107077220- 1.500135489728730 * neuron1- 0.096283269121503 * neuron2- 0.194935930577094 * neuron3- 0.352305895755591 * neuron4+ 0.075107415847473 * neuron5
    return somma





def neuron1_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma= 4.242299670155190+ 0.400396555256580 * b03_norm+ 0.607936279259404 * b04_norm+ 0.137468650780226 * b05_norm- 2.955866573461640 * b06_norm- 3.186746687729570 * b07_norm+ 2.206800751246430 * b8a_norm- 0.313784336139636 * b11_norm+ 0.256063547510639 * b12_norm- 0.071613219805105 * viewZen_norm+ 0.510113504210111 * sunZen_norm+ 0.142813982138661 * relAzim_norm
    
    return tansig(somma)
    
def neuron2_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma= - 0.259569088225796- 0.250781102414872 * b03_norm+ 0.439086302920381 * b04_norm- 1.160590937522300 * b05_norm- 1.861935250269610 * b06_norm+ 0.981359868451638 * b07_norm+ 1.634230834254840 * b8a_norm- 0.872527934645577 * b11_norm+ 0.448240475035072 * b12_norm+ 0.037078083501217 * viewZen_norm+ 0.030044189670404 * sunZen_norm+ 0.005956686619403 * relAzim_norm 
    return tansig(somma)
    

def neuron3_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=3.130392627338360+ 0.552080132568747 * b03_norm- 0.502919673166901 * b04_norm+ 6.105041924966230 * b05_norm- 1.294386119140800 * b06_norm- 1.059956388352800 * b07_norm- 1.394092902418820 * b8a_norm+ 0.324752732710706 * b11_norm- 1.758871822827680 * b12_norm- 0.036663679860328 * viewZen_norm- 0.183105291400739 * sunZen_norm- 0.038145312117381 * relAzim_norm   
    return tansig(somma)

def neuron4_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=0.774423577181620+ 0.211591184882422 * b03_norm- 0.248788896074327 * b04_norm+ 0.887151598039092 * b05_norm+ 1.143675895571410 * b06_norm- 0.753968830338323 * b07_norm- 1.185456953076760 * b8a_norm+ 0.541897860471577 * b11_norm- 0.252685834607768 * b12_norm- 0.023414901078143 * viewZen_norm- 0.046022503549557 * sunZen_norm- 0.006570284080657 * relAzim_norm
    return tansig(somma)

def neuron5_cab(b03_norm,b04_norm,b05_norm,b06_norm,b07_norm,b8a_norm,b11_norm,b12_norm, viewZen_norm,sunZen_norm,relAzim_norm):
    somma=2.584276648534610+ 0.254790234231378 * b03_norm- 0.724968611431065 * b04_norm+ 0.731872806026834 * b05_norm+ 2.303453821021270 * b06_norm- 0.849907966921912 * b07_norm- 6.425315500537270 * b8a_norm+ 2.238844558459030 * b11_norm- 0.199937574297990 * b12_norm+ 0.097303331714567 * viewZen_norm+ 0.334528254938326 * sunZen_norm+ 0.113075306591838 * relAzim_norm
    return tansig(somma)


def layer2_cab(neuron1, neuron2, neuron3, neuron4, neuron5):
    somma =0.463426463933822	- 0.352760040599190 * neuron1- 0.603407399151276 * neuron2+ 0.135099379384275 * neuron3- 1.735673123851930 * neuron4- 0.147546813318256 * neuron5
    return somma





