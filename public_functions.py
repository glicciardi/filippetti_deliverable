#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 10:34:31 2019

@author: glicciardi
"""
import os
from functions import *
from read_xml import read_xml_sentinel
from lai_cab import calcola_lai,calcola_cab
import traceback
import rasterio as rio
import os.path
import geopandas as gpd
import pandas as pd
from geomet import wkt
import pyproj
from shapely.geometry import Polygon,mapping
from sentinelsat import SentinelAPI
import landsatxplore.api
import datetime
import time
from zipfile import ZipFile
import dateutil.relativedelta
import os
import numpy as np
from landsatxplore.earthexplorer import EarthExplorer
import numpy.ma as ma
import tasks
from skimage.transform import resize
import fiona
import constants
import inspect



#########################################################################################
# CLUSTERING OMOGENEE
def process(ts,tenant,code,gis,gis_epsg,satellite,images):
    dir_out=calcola_result_path(ts,tenant,code,"CLUSTERIZZAZIONE")
    if is_locked(dir_out):
        return res_error(-1,'is already processing')
    else:
        task = tasks.process_task.delay(ts,tenant,code,gis,gis_epsg,satellite,images,dir_out)
        return res_ok('ok')

def get_process(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"CLUSTERIZZAZIONE")
    if is_locked(dir_out):
        return res_error(-1,'is processing')
    else:
        return res_cached_json(dir_out)

def stop_process(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"CLUSTERIZZAZIONE")
    return_value = force_unlock_task(dir_out)
    if return_value:
        return res_ok('ok')
    else:
        return res_error(-1,'is not processing')





# ZONIZZAZIONE STAGIONE
def process_lai_cab(ts,tenant,code,gis,gis_epsg,satellite,images,cult,_parameters,force_download):
    dir_out=calcola_result_path(ts,tenant,code,"ZONIZZAZIONE")
    if is_locked(dir_out):
        return res_error(-1,'is already processing')
    else:
        task = tasks.process_lai_cab_task.delay(ts,tenant,code,gis,gis_epsg,satellite,images,cult,_parameters,force_download,dir_out)
        return res_ok('ok')

def get_process_lai_cab(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"ZONIZZAZIONE")
    if is_locked(dir_out):
        return res_error(-1,'is processing')
    else:
        return res_cached_json(dir_out)

def stop_process_lai_cab(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"ZONIZZAZIONE")
    return_value = force_unlock_task(dir_out)
    if return_value:
        return res_ok('ok')
    else:
        return res_error(-1,'is not processing')


# BILANCIO AZOTO
def process_bilancio_azoto(ts,tenant,code,gis,gis_epsg,satellite,images,cult,previous_cult,_indexes):
    dir_out=calcola_result_path(ts,tenant,code,"BILANCIOAZOTO")
    if is_locked(dir_out):
        return res_error(-1,'is already processing')
    else:
        task = tasks.process_bilancio_azoto_task.delay(ts,tenant,code,gis,gis_epsg,satellite,images,cult,previous_cult,_indexes,dir_out)
        return res_ok('ok')

def get_process_bilancio_azoto(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"BILANCIOAZOTO")
    if is_locked(dir_out):
        return res_error(-1,'is processing')
    else:
        return res_cached_json(dir_out)

def stop_process_bilancio_azoto(ts,tenant,code):
    dir_out=calcola_result_path(ts,tenant,code,"BILANCIOAZOTO")
    return_value = force_unlock_task(dir_out)
    if return_value:
        return res_ok('ok')
    else:
        return res_error(-1,'is not processing')

#########################################################################################

def download(gis,ts):
    if is_locked(None):
        return res_error(-1,'is downloading')
    else:
        task = tasks.download_task.delay(gis,ts)
        return res_ok('ok')

def stop_download():
    return_value = force_unlock_task(None)
    if return_value:
        return res_ok('ok')
    else:
        return res_error(-1,'no downloads in progress')


def check_public(gis,start_date,stop_date):
    coordinates = wkt.loads(gis)
    coordinates=coordinates['coordinates'][0]
    proj_in = pyproj.Proj("epsg:3857")
    proj_out = pyproj.Proj("epsg:4326")
    tuples=[]

    for coord in coordinates:
        #POTREBBE ESSERE NECESSARIO CONVERTIRE IN METRI LE COORDINATE PRIMA DI FARE TRANSFORM, DA ANALIZZARE PIU' ACCURATAMENTE
        lon, lat = pyproj.transform(proj_in,proj_out,coord[0],coord[1])
        tuples.append((lon,lat))
    coordinates=tuples
    print(coordinates)
    gis = Polygon(coordinates)
    stop_date = datetime.datetime.strptime(ts.split('T')[0], '%d/%m/%Y')
    start_date = calculate_start_date(stop_date)
    result,products_df_sorted,scenes_df_sorted=check(gis,start_date,stop_date)
    if result==True:
        return res_ok('True')
    else:
        return res_ok('False')

#########################################################################################
