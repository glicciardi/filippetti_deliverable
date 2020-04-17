#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 19 11:10:34 2019

@author: glicciardi
"""
import xml.etree.ElementTree as ET
import re
import numpy as np

import matplotlib.pyplot as plt
from skimage.transform import resize

def read_xml_sentinel(nomefile,rows_in,cols_in):
    
    
    tree = ET.parse(nomefile)
    root = tree.getroot()
    general_info=root[0]
    geometric_info=root[1]
    QI_info=root[2]
    
    
    tile_angles=geometric_info[1]
    
    sun_angles_grid=tile_angles[0]
    sun_angles_grid_zenith=sun_angles_grid[0]
    sun_angles_grid_azimuth=sun_angles_grid[1]
    
    col_step_sza=int(sun_angles_grid_zenith[0].text)
    row_step_sza=int(sun_angles_grid_zenith[1].text)
    
#####################################################################################
#############funzione per l'estrazione dei valori di sun zenith angle################
#####################################################################################    
    value_list=sun_angles_grid_zenith[2]
    
    n_righe=len(value_list)
    
    array_sza=np.zeros((23,23))
    
    for j in range (0,n_righe):
        riga=value_list[j].text
        
        appo=[]
        values=[]
        appo.append(0)
        
        for m in re.finditer(' ', riga):
             appo.append(m.end())
         
        appo.append(len(riga)+1)
        
        n_values=len(appo)-1
        for i in range(0,n_values):
            numero=float(riga[appo[i]:appo[i+1]-1])
            values.append(numero)
        
            
            
        myarray = np.asarray(values)
        array_sza[j,:]=myarray
         
#####################################################################################
#############funzione per l'estrazione dei valori di sun azimuth angle###############
#####################################################################################  
    sun_angles_grid_azimuth=sun_angles_grid[1]
    
    col_step_saa=int(sun_angles_grid_azimuth[0].text)
    row_step_saa=int(sun_angles_grid_azimuth[1].text)
    
    
    value_list=sun_angles_grid_azimuth[2]
    
    n_righe=len(value_list)
    
    array_saa=np.zeros((23,23))
    
    for j in range (0,n_righe):
        riga=value_list[j].text
        
        appo=[]
        values=[]
        appo.append(0)
        
        for m in re.finditer(' ', riga):
             appo.append(m.end())
         
        appo.append(len(riga)+1)
        
        n_values=len(appo)-1
        for i in range(0,n_values):
            numero=float(riga[appo[i]:appo[i+1]-1])
            values.append(numero)
        
            
            
        myarray = np.asarray(values)
        array_saa[j,:]=myarray    
    
#####################################################################################
#############funzione per l'estrazione dei valori di view zenith angle###############
#####################################################################################              
        

    array_vza=np.zeros((5,23,23))    
    array_vza_tot=np.zeros((13,23,23))
            
    for mmm in range (0,13):    
       add_start=mmm*5
       add_stop=(mmm+1)*5
       
     
        
       for k in range (add_start,add_stop):
           
        
            viewing_Incidence_Angles_Grids=tile_angles[k+2]
            
            vza=viewing_Incidence_Angles_Grids[0]
            values_8_8=vza[2]
            
            
            
            for j in range (0,n_righe):
                riga=values_8_8[j].text
                
                appo=[]
                values=[]
                appo.append(0)
                
                for m in re.finditer(' ', riga):
                     appo.append(m.end())
                 
                appo.append(len(riga)+1)
                
                n_values=len(appo)-1
                for i in range(0,n_values):
                    numero=float(riga[appo[i]:appo[i+1]-1])
                    
                    values.append(numero)
                    
                    
                    
                myarray = np.asarray(values)
                
                
                
                array_vza[k-add_start,j,:]=myarray
                
                
       #print(array_vza.shape)
       bands,rows,cols=array_vza.shape
            
       for k in range (0,bands):
            for i in range (0,rows):
                for j in range(0,cols):
                    where_are_NaNs = np.isnan(array_vza)
                    array_vza[where_are_NaNs] = 0
                
    
    
    
       array_vza_tot[mmm,:,:]=np.max(array_vza,axis=0)            
                    
#####################################################################################
#############funzione per l'estrazione dei valori di view azimuth angle###############
#####################################################################################              
        

    array_vaa=np.zeros((5,23,23))    
    array_vaa_tot=np.zeros((13,23,23))
            
    for mmm in range (0,13):    
       add_start=mmm*5
       add_stop=(mmm+1)*5
       
     
        
       for k in range (add_start,add_stop):
           
        
            viewing_Incidence_Angles_Grids=tile_angles[k+2]
            
            vaa=viewing_Incidence_Angles_Grids[1]
            values_8_8=vaa[2]
            
            
            
            for j in range (0,n_righe):
                riga=values_8_8[j].text
                
                appo=[]
                values=[]
                appo.append(0)
                
                for m in re.finditer(' ', riga):
                     appo.append(m.end())
                 
                appo.append(len(riga)+1)
                
                n_values=len(appo)-1
                for i in range(0,n_values):
                    numero=float(riga[appo[i]:appo[i+1]-1])
                    values.append(numero)
                
                    
                    
                myarray = np.asarray(values)
                
                
                
                array_vaa[k-add_start,j,:]=myarray
                
                
       #print(array_vza.shape)
       bands,rows,cols=array_vaa.shape
            
       for k in range (0,bands):
            for i in range (0,rows):
                for j in range(0,cols):
                    where_are_NaNs = np.isnan(array_vaa)
                    array_vaa[where_are_NaNs] = 0
                
    
    
    
       array_vaa_tot[mmm,:,:]=np.max(array_vaa,axis=0) 
#####################################################################################
#############funzione per il calcolo della media degli angoli di vista###############
#####################################################################################  

          
    viewing_zenith_angle_mean=np.max(array_vza_tot,axis=0)
    viewing_azimuth_angle_mean=np.max(array_vaa_tot,axis=0)              
    
#####################################################################################
#############funzione per il resize delle varie immagini degli angoli ###############
#####################################################################################      
    
    viewing_zenith_angle_mean_resized = resize(viewing_zenith_angle_mean, (rows_in,cols_in),anti_aliasing=False, mode='constant',order=0)
    viewing_azimuth_angle_mean_resized = resize(viewing_azimuth_angle_mean, (rows_in,cols_in),anti_aliasing=False, mode='constant',order=0)
    array_sza_resized= resize(array_sza, (rows_in,cols_in),anti_aliasing=False, mode='constant',order=1)
    array_saa_resized= resize(array_saa, (rows_in,cols_in),anti_aliasing=False, mode='constant',order=1)
    
    
    return array_sza_resized,array_saa_resized, viewing_zenith_angle_mean_resized,viewing_azimuth_angle_mean_resized