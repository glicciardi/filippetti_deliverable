#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 10 17:03:10 2019

@author: glicciardi
"""
from geomet import wkt
import pyproj
import datetime
import time
import dateutil.relativedelta
from landsatxplore.earthexplorer import EarthExplorer
import numpy.ma as ma
from skimage.transform import resize
import rasterio
import rasterio as rio
from flask import jsonify
from rasterio.plot import plotting_extent
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from datetime import timedelta
import geopandas as gpd
from osgeo import ogr, osr
import os
from sentinelsat import SentinelAPI
import earthpy.spatial as es
import zipfile
import fiona
import math
import json
import tarfile
import scipy
import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
from sentinelsat import SentinelAPI
import landsatxplore.api
from shapely.geometry import Polygon
import gdal
import tasks
from constants import *
import constants
from functions_lai_cab_nn import neuron1_lai, neuron2_lai,neuron3_lai,neuron4_lai,neuron5_lai,neuron1_cab, neuron2_cab,neuron3_cab,neuron4_cab,neuron5_cab,layer2_lai,layer2_cab
from sklearn.preprocessing import minmax_scale
from utilities_lai_cab import normalize, denormalize

#########################################################################################
########utilities########################################################################
#########################################################################################

def get_coordinates(polygon):
    x_list, y_list = polygon.exterior.coords.xy
    #bbox_poly = Polygon([[min(x_list),min(y_list)],[max(x_list),min(y_list)],[max(x_list),max(y_list)],[min(x_list),max(y_list)],[min(x_list),min(y_list)]])
    return x_list, y_list


def calculate_start_date(stop_date):
    start_date = stop_date - dateutil.relativedelta.relativedelta(days=7)
    #start_date = stop_date - dateutil.relativedelta.relativedelta(months=4)
    return start_date

# Check if images exists in local dir
def check(polygon,start_date,stop_date,only_sentinel = False):
    x_list, y_list = get_coordinates(polygon)
    products_df_sorted,scenes_df_sorted=query_images(x_list,y_list,start_date,stop_date,only_sentinel)
    if(only_sentinel):
        n_products=products_df_sorted.shape
        if (n_products[0]==0):
            return False,0,0
        if n_products[0]>0:
            flag_s2=check_images_sentinel(products_df_sorted)
        result= flag_s2
        return result,products_df_sorted,n_products[0]
    n_products=products_df_sorted.shape
    n_scenes=scenes_df_sorted.shape
    if (n_products[0]==0 and n_scenes[0]==0):
        return False,0,0,0,0
    flag_s2=False
    flag_ls=False
    if n_products[0]>0:
        flag_s2=check_images_sentinel(products_df_sorted)
    if n_scenes[0]>0:
        flag_ls=check_images_landsat(scenes_df_sorted)
    result= flag_s2 or flag_ls
    return result,products_df_sorted,scenes_df_sorted,n_products[0],n_scenes[0]

def get_directory(sub_path):
    currentDirectory = os.getcwd()
    return currentDirectory+'/'+sub_path+'/'

def write_json_to_file(json_data,dir):
    print(json_data)
    with open(dir+"/out.json", 'w') as f:
        json.dump(json_data, f)


def calcola_week(date):
    day_of_year = date.timetuple().tm_yday
    return math.floor(day_of_year/7)+1

# DA QUA SI PUO MODIFICARE IL PATH DEL RISULTATO
def calcola_result_path(ts,tenant,code,operazione):
    tenant=tenant.replace(" ","")
    code=code.replace(" ","")
    path=os.getcwd()
    results_dir='results'
    stop_date = datetime.datetime.strptime(ts.split('T')[0], '%d/%m/%Y')
    dir_out = path+"/"+results_dir+"/"+operazione+"/"+str(stop_date.year)+"/"+str(calcola_week(stop_date))+"/"+tenant+"/"+code
    if not os.path.exists(dir_out):
        os.makedirs(dir_out,exist_ok=True)
    return dir_out

# PREPARE JSON FOR ERROR RESPONSE
def res_error(code,message,save_dir = False,in_task = False):
    out_json = {
        "status":"ERR",
        "error_code":code,
        "message":message
    }

    if save_dir:
        write_json_to_file(out_json,save_dir)
    if not in_task:
        out = jsonify(
                out_json
            )
        return out
    else:
        return out_json


# PREPARE JSON FOR OK RESPONSE
def res_cached_json(dir):
    path = dir+"/out.json"
    if os.path.isfile(path):
        f= open(path,'r')

        json_string=f.readline()
        parsed_json = (json.loads(json_string))
        out = jsonify(
                parsed_json
            )
        f.close()
        return out
    else: return res_error(-10,"no cached results")

def res_ok(message,save_dir = False,in_task = False):
    if message==None:
        out_json = {
            "status":"OK"
        }
    else:
        out_json = {
            "status":"OK",
            "message":message
        }
    if save_dir:
        write_json_to_file(out_json,save_dir)
    if not in_task:
        out = jsonify(
                out_json
            )
        return out
    else:
        return out_json

###### lock single task per process / download
def lock(dir,task,message):
    if dir is not None:
        f = open(dir+"/"+constants.task_lockfile, "w")
    else:
        f = open(constants.task_lockfile, "w")
    if task is not None:
        f.write(task.request.id)
    if message  is not None:
        f.write(message)
    f.close()

def release(dir):
    if dir is not None:
        path = dir+"/"+constants.task_lockfile
    else:
        path = constants.task_lockfile
    if os.path.isfile(path):
        os.remove(path)
        return True
    else: return False

def is_locked(dir):
    if dir is not None:
        path = dir+"/"+constants.task_lockfile
    else:
        path = constants.task_lockfile
    if os.path.isfile(path):
        return True
    else:
        return False

def force_unlock_task(dir):
    if dir is not None:
        path = dir+"/"+constants.task_lockfile
    else:
        path = constants.task_lockfile
    if os.path.isfile(path):
        f= open(path,'r')
        task_id=f.readline()
        task_id=task_id.strip('\n')
        print("stopping: "+task_id)
        tasks.celery.control.revoke(task_id, terminate=True)
        f.close()
        release(dir)
        return True
    else:
        return False
#####

#########################################################################################
########query sul server S2 e Landsat per ricerca immagini###############################
#########################################################################################

def query_images(x_list,y_list,start_date,stop_date,only_sentinel = False):
    bbox_poly = Polygon([[min(x_list),min(y_list)],[max(x_list),min(y_list)],[max(x_list),max(y_list)],[min(x_list),max(y_list)],[min(x_list),min(y_list)]])
    api = SentinelAPI(sentineluser, sentinelpwd, 'https://scihub.copernicus.eu/dhus')
    print(bbox_poly)
    print(start_date.strftime("%Y%m%d"))
    print(stop_date.strftime("%Y%m%d"))
    print(max_cloud)
    products = api.query(bbox_poly,date=(start_date.strftime("%Y%m%d"),stop_date.strftime("%Y%m%d")) , platformname='Sentinel-2',processinglevel= 'Level-2A', cloudcoverpercentage=(0, max_cloud))
    products_df = api.to_dataframe(products)
    numero_products=products_df.shape
    if numero_products[0]>0:
        products_df=products_df.sort_values(by='beginposition')
        num_record_s2, campi=products_df.shape
        first_available_s2_imm=products_df['beginposition'][0]
    if(only_sentinel):
        return products_df, 0
    api = landsatxplore.api.API(landsatuser, landsatpwd)
    scenes = api.search(dataset='LANDSAT_8_C1',start_date=start_date.isoformat(), end_date=first_available_s2_imm.isoformat(),bbox=(min(y_list),min(x_list),max(y_list),max(x_list)),max_results=1000,max_cloud_cover=max_cloud)
    scenes_df=pd.DataFrame(scenes)
    numero_scene=scenes_df.shape
    if numero_scene[0]>0:
        scenes_df=scenes_df.sort_values(by='acquisitionDate')
        num_record_landsat, campi=scenes_df.shape
    return products_df, scenes_df


#########################################################################################
########check presenza immagini su server locale          ###############################
#########################################################################################

def check_images_landsat(scenes_df_sorted):
    save_dir = get_directory(data_dir)
    num_record_landsat, campi=scenes_df_sorted.shape
    for i in range (0,num_record_landsat):
        nome_file=scenes_df_sorted['displayId'][i]
        estensione='.tar.gz'
        nome_file=save_dir+nome_file+estensione
        if os.path.exists(nome_file) is False:
            return False
    return True

def check_images_sentinel(products_df_sorted):
    save_dir = get_directory(data_dir)
    num_record_sentinel, campi=products_df_sorted.shape
    for i in range (0,num_record_sentinel):
        nome_file=products_df_sorted['title'][i]
        estensione='.zip'
        nome_file=save_dir+nome_file+estensione
        if os.path.exists(nome_file) is False:
            return False
    return True

# Download single sentinel image
def download_sentinel_image(index,data_path):
    api = SentinelAPI(sentineluser, sentinelpwd, 'https://scihub.copernicus.eu/dhus')
    api.download(index, data_path, checksum=True)

#########################################################################################
########funzione che cambia l'EPSG di un file SHP########################################
#########################################################################################

def cambia_epsg(in_epsg ,out_epsg ,in_shp):#in_epsg ="4326",out_epsg ="32632",in_shp):
    wkspFldr = os.path.dirname(in_shp)
    base=os.path.basename(in_shp)
    ext=os.path.splitext(base)[1]
    name_file=os.path.splitext(base)[0]
    out_shp=wkspFldr+'/'+name_file+'_rep'+ext
    #print(out_shp)
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(in_epsg)
    # output SpatialReference
    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(out_epsg)
    # create the CoordinateTransformation
    coordTrans = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
    # get the input layer
    inDataSet = driver.Open(in_shp)
    inLayer = inDataSet.GetLayer()
    # create the output layer
    if os.path.exists(out_shp):
        driver.DeleteDataSource(out_shp)
    outDataSet = driver.CreateDataSource(out_shp)
    outLayer = outDataSet.CreateLayer("reproject", geom_type=ogr.wkbMultiPolygon)
    # add fields
    inLayerDefn = inLayer.GetLayerDefn()
    for i in range(0, inLayerDefn.GetFieldCount()):
        fieldDefn = inLayerDefn.GetFieldDefn(i)
        outLayer.CreateField(fieldDefn)
    # get the output layer's feature definition
    outLayerDefn = outLayer.GetLayerDefn()
    # loop through the input features
    inFeature = inLayer.GetNextFeature()
    while inFeature:
        # get the input geometry
        geom = inFeature.GetGeometryRef()
        # reproject the geometry
        geom.Transform(coordTrans)
        # create a new feature
        outFeature = ogr.Feature(outLayerDefn)
        # set the geometry and attribute
        outFeature.SetGeometry(geom)
        for i in range(0, outLayerDefn.GetFieldCount()):
            outFeature.SetField(outLayerDefn.GetFieldDefn(i).GetNameRef(), inFeature.GetField(i))
        # add the feature to the shapefile
        outLayer.CreateFeature(outFeature)
        # dereference the features and get the next input feature
        outFeature = None
        inFeature = inLayer.GetNextFeature()
    # Save and close the shapefiles
    inDataSet = None
    outDataSet = None
    return out_shp


#########################################################################################
########funzione che cambia l'EPSG di un file tif########################################
#########################################################################################
#platform = 0 for Geotiff, 1 for JP2
def reproject_et(inpath, outpath, new_crs, platform):
    dst_crs = new_crs
    if platform==1:
        driv='JP2OpenJPEG'
    if platform==0:
        driv='Gtiff'
    print(driv)
    with rio.open(inpath, driver=driv) as src:
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'driver':'Gtiff',
            'crs': dst_crs,
            'transform': transform,
            'width': width,
            'height': height
        })
        with rio.open(outpath, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rio.band(src, i),
                    destination=rio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest)


#########################################################################################
########funzione che scarica le bande 4 e 8 dell'immagine sentinel di riferimento########
#########################################################################################

def dl_image_4_8(nome_file):
    currentDirectory = os.getcwd()
    nome_b4=''
    nome_b8=''
    lista_immagini=list()
    lista_immagini.append(nome_file)
    zfile = zipfile.ZipFile(nome_file)#lista_immagini[0])
    appo=(zfile.namelist())
    dimensione=len(appo)
    result=list()
    for j in range(0,dimensione):
        stringa=appo[j]
        if stringa.endswith('jp2'):
            result.append(appo[j])
        #estraggo solo le bande 8 e 4 per derivare gli indici
    n_imm=len(result)
    for k in range(0,n_imm):
       # print(result)
        if result[k].find('B04_10m')>=0:
            nome_b4=result[k]
        if result[k].find('B08_10m')>=0:
            nome_b8=result[k]
    zfile.extract(nome_b4,'temp')
    zfile.extract(nome_b8,'temp')
    nome_b4=currentDirectory+'/temp/'+nome_b4
    nome_b8=currentDirectory+'/temp/'+nome_b8
    dataset_b4=rasterio.open(nome_b4,'r')
    #dataset_b8=rasterio.open(nome_b8,'r')
    metadatas=dataset_b4.meta
    metadatas['dtype']='float32'
    metadatas['driver']='GTiff'
    #b4=dataset_b4.read(1)
    #b8=dataset_b8.read(1)
    present=1
    return present,nome_b4,nome_b8,metadatas
        #return b4,b8,metadatas


#########################################################################################
########funzione che scarica le bande 4 e 5 dell'immagine Landsat di riferimento  #######
#########################################################################################

def dl_image_4_5(nome_file):
    currentDirectory = os.getcwd()
    nome_b4=''
    nome_b5=''
    nome_mtl=''
    lista_immagini=list()
    lista_immagini.append(nome_file)
    tar = tarfile.open(nome_file)
    appo=tar.getmembers()
    dimensione=len(appo)
    result=list()
    for j in range(0,dimensione):
        stringa=str(appo[j])
        result.append(stringa)
        #estraggo solo le bande 8 e 4 per derivare gli indici
    n_imm=len(result)
    path_n=currentDirectory+'/temp/'
    for k in range(0,n_imm):
       # print(result)
        if result[k].find('B4.TIF')>=0:
            tar.extract(appo[k],path_n)
            nome_b4=result[k]
        if result[k].find('B5.TIF')>=0:
            tar.extract(appo[k],path_n)
            nome_b5=result[k]
        if result[k].find('MTL.txt')>=0:
            tar.extract(appo[k],path_n)
            nome_mtl=result[k]
    pos1=nome_b4.find(" '")
    pos2=nome_b4.find("' at")
    nome_b4=nome_b4[pos1+2:pos2]
    pos1=nome_b5.find(" '")
    pos2=nome_b5.find("' at")
    nome_b5=nome_b5[pos1+2:pos2]
    pos1=nome_mtl.find(" '")
    pos2=nome_mtl.find("' at")
    nome_mtl=nome_mtl[pos1+2:pos2]
    nome_b4=currentDirectory+'/temp/'+nome_b4
    nome_b5=currentDirectory+'/temp/'+nome_b5
    nome_mtl=currentDirectory+'/temp/'+nome_mtl
    dataset_b4=rasterio.open(nome_b4,'r')
    #dataset_b8=rasterio.open(nome_b8,'r')
    metadatas=dataset_b4.meta
    metadatas['dtype']='float32'
    metadatas['driver']='GTiff'
    #b4=dataset_b4.read(1)
    #b8=dataset_b8.read(1)
    present=1
    return present,nome_b4,nome_b5,nome_mtl,metadatas
        #return b4,b8,metadatas


#########################################################################################
########funzione che scarica le bande utili a Lai e Cab########
#########################################################################################

def dl_image_lai_cab(nome_file):
    currentDirectory = os.getcwd()
    nome_b3=''
    nome_b4=''
    nome_b5=''
    nome_b6=''
    nome_b7=''
    nome_b8a=''
    nome_b11=''
    nome_b12=''
#    lista_immagini=list()
#
#
#    lista_immagini.append(nome_file)
    zfile = zipfile.ZipFile(nome_file)
    appo=(zfile.namelist())
    dimensione=len(appo)
    result=list()
    result_xml=list()
    for j in range(0,dimensione):
        stringa=appo[j]
        if stringa.endswith('jp2'):
            result.append(appo[j])
        if stringa.endswith('xml'):
            result_xml.append(appo[j])
        #estraggo solo le bande 8 e 4 per derivare gli indici
    n_imm=len(result)
    for k in range(0,n_imm):
       # print(result)
        if result[k].find('B03_20m')>=0:
            nome_b3=result[k]
        if result[k].find('B04_20m')>=0:
            nome_b4=result[k]
        if result[k].find('B05_20m')>=0:
            nome_b5=result[k]
        if result[k].find('B06_20m')>=0:
            nome_b6=result[k]
        if result[k].find('B07_20m')>=0:
            nome_b7=result[k]
        if result[k].find('B8A_20m')>=0:
            nome_b8a=result[k]
        if result[k].find('B11_20m')>=0:
            nome_b11=result[k]
        if result[k].find('B12_20m')>=0:
            nome_b12=result[k]
    n_xml=len(result_xml)
    for k in range(0,n_xml):
        if result_xml[k].find('MTD_TL')>=0:
            nome_xml=result_xml[k]
    zfile.extract(nome_b3,'temp')
    zfile.extract(nome_b4,'temp')
    zfile.extract(nome_b5,'temp')
    zfile.extract(nome_b6,'temp')
    zfile.extract(nome_b7,'temp')
    zfile.extract(nome_b8a,'temp')
    zfile.extract(nome_b11,'temp')
    zfile.extract(nome_b12,'temp')
    zfile.extract(nome_xml,'temp')
    nome_b3=currentDirectory+'/temp/'+nome_b3
    nome_b4=currentDirectory+'/temp/'+nome_b4
    nome_b5=currentDirectory+'/temp/'+nome_b5
    nome_b6=currentDirectory+'/temp/'+nome_b6
    nome_b7=currentDirectory+'/temp/'+nome_b7
    nome_b8a=currentDirectory+'/temp/'+nome_b8a
    nome_b11=currentDirectory+'/temp/'+nome_b11
    nome_b12=currentDirectory+'/temp/'+nome_b12
    nome_xml=currentDirectory+'/temp/'+nome_xml
    dataset_b3=rasterio.open(nome_b3,'r')
    metadatas=dataset_b3.meta
    metadatas['dtype']='float32'
    metadatas['driver']='GTiff'
    return nome_b3,nome_b4,nome_b5,nome_b6,nome_b7,nome_b8a,nome_b11,nome_b12,nome_xml,metadatas


#########################################################################################
########funzione che calcola l'NDVI dell'immagine sentinel di riferimento################
#########################################################################################

def calcola_ndvi(nir,red,metadatas):
    bands,rows,cols=red.shape
    ndvi = es.normalized_diff(b1=nir[0,:,:], b2=red[0,:,:])
   # ndvi2=np.zeros((rows,cols),dtype="float64")
#
    for i in range(0,rows):
        for j in range (0,cols):
             appo=ndvi[i,j]
             if math.isnan(appo):
               ndvi[i,j] =0
               #print(ndvi[i,j])
            #sopra=int(b4[0,i,j]-b8[0,i,j])
            #sotto=int(b4[0,i,j]+b8[0,i,j])
           # if sotto > 0 :
           #     diff=sopra/sotto
           #     ndvi2[i,j]=diff
         #  if math.isnan(diff) is True:
          #     diff=0
            #else:
            #    ndvi2[i,j]=0
    metadatas['dtype']="float64"
    metadatas['driver']="GTiff"
    metadatas['count'] = 1
    metadatas['nodata'] = 0
    print(metadatas)
#    with rasterio.open('/Users/glicciardi/Desktop/ndvi.tif','w',**metadatas) as dst:
#        dst.write(ndvi,1)
#
#    dst.close()
#
##    with rasterio.open('/Users/glicciardi/Desktop/ndvi2.tif','w',**metadatas) as dst:
##        dst.write(ndvi2,1)
#
#    dst.close()
    return ndvi,metadatas


#########################################################################################
########funzione che fa il crop delle immagini raster su input di un shp ################
#########################################################################################

def crop_image_by_shp(imm,shp):
    currentDirectory = os.getcwd()
    crop_extent = gpd.read_file(shp)
    imm_or=rasterio.open(imm,'r')
    metadatas_imm_or=imm_or.meta
    imm_crop, imm_crop_meta = es.crop_image(imm_or,crop_extent,all_touched=True)
    with fiona.open(shp, "r") as shapefile:
        geoms = [feature["geometry"] for feature in shapefile]
    out_image, out_transform = mask(imm_or, geoms,all_touched=True,crop=True)
    imm_crop_affine = imm_crop_meta["transform"]
    # Create spatial plotting extent for the cropped layer
    #imm_extent = plotting_extent(imm_crop[0], imm_crop_affine)
    metadatas_imm_or.update({'transform': imm_crop_affine,
                       'height': imm_crop.shape[1],
                       'width': imm_crop.shape[2],
                       'nodata': 0})
    #imm_crop=imm_crop[0,:,:]
   # out_image, out_transform = mask(imm_crop, geoms,invert=True)
   # wkspFldr = os.path.dirname(imm)
    base=os.path.basename(imm)
    ext=os.path.splitext(base)[1]
    name_file=os.path.splitext(base)[0]
    metadatas_imm_or['driver']="GTiff"
    path_out=currentDirectory+'/'+name_file+'_rep'+'.tif'
    #path_out = imm#"data/colorado-flood/spatial/outputs/lidar_chm_cropped.tif"
#    with rio.open(path_out, 'w', **metadatas_imm_or) as ff:
#        ff.write(out_image[0], 1)
    return out_image,metadatas_imm_or


#########################################################################################
########funzione che estrae rescaling parameters per TOA                 ################
#########################################################################################

def rescale_reflectance(namefile, band_number):
    mult=0
    adder=0
    stringa1=''
    with open(namefile) as f:
        lineList = f.readlines()
    n_righe=len(lineList)
    stringa1='REFLECTANCE_MULT_BAND_'+str(band_number)
    stringa2='REFLECTANCE_ADD_BAND_'+str(band_number)
    for i in range (0,n_righe):
        a=str(lineList[i])
        res=a.find(stringa1)
        if res>0:
            lunghezza=len(a)
            inizio=a.find('=')
            mult=float(a[inizio+2:lunghezza])
        res2=a.find(stringa2)
        if res2>0:
            lunghezza=len(a)
            inizio=a.find('=')
            adder=float(a[inizio+2:lunghezza])
            return(mult, adder)


#########################################################################################
########funzione che poligonizza il raster                               ################
#########################################################################################

def poligonizza_raster(nomefile,nomeoutput):
    sourceRaster = gdal.Open(nomefile) #/Users/glicciardi/Desktop/ndvi3.tif'
    band = sourceRaster.GetRasterBand(1)
    #bandArray = band.ReadAsArray()
    #outShapefile = "polygonized"
    srs = osr.SpatialReference()
    srs.ImportFromWkt( sourceRaster.GetProjectionRef() )
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if os.path.exists(nomeoutput):#outShapefile+".shp"):
        driver.DeleteDataSource(nomeoutput)#outShapefile+".shp")
    outDatasource = driver.CreateDataSource(nomeoutput)#outShapefile+ ".shp")
    outLayer = outDatasource.CreateLayer("polygonized", srs=None)
    fd = ogr.FieldDefn("DN", ogr.OFTInteger)
    outLayer.CreateField(fd)
    dst_field = outLayer.GetLayerDefn().GetFieldIndex("DN")
    gdal.Polygonize(band, None, outLayer, dst_field, [], callback=None)
    #gdal.Polygonize( band, None, outLayer, -1, [], callback=None )
    outDatasource.Destroy()
    sourceRaster = None


#########################################################################################
########funzione che individua le immagini NDVI con 70% di pixel >0.6 o < 0.3############
#########################################################################################
########ritorna un vettore i cui valori indicano se è veg (2), bs(1) o altro(0)##########
#########################################################################################

def trova_vegetazione(imm_ndvi):
    rows,cols=imm_ndvi.shape
    print(rows,cols)
    total_pixel=rows*cols
    tot_valid_pixels=0
    conta_veg=0
    conta_bs=0
    result_im=0
    #result_im=np.zeros([rows,cols])
   # ndvi2=np.zeros((rows,cols),dtype="float64")
    #for k in range (1,bands):
    for i in range(1,rows):
        for j in range (1,cols):
            appo=imm_ndvi[i,j]
            if appo != 0:
                tot_valid_pixels=tot_valid_pixels+1
    for i in range(1,rows):
        for j in range (1,cols):
            appo=imm_ndvi[i,j]
            if appo != 0:
                if appo>0.6:
                    conta_veg=conta_veg+1
                if appo<0.3:
                    conta_bs=conta_bs+1
    ratio_veg=conta_veg/tot_valid_pixels
    print(conta_veg)
    print(tot_valid_pixels)
    if ratio_veg> 0.7:
        result_im=2
#    ratio_bs=conta_bs/tot_valid_pixels
#    if ratio_bs<0.3:
#        result_im=1
    return result_im


#########################################################################################
########funzione che normalizza l'NDVI tra 0 e 1 dopo z-score                ############
#########################################################################################

def normalize_ndvi(ndvi):
    appo=scipy.stats.zscore(ndvi, axis=None)
    b = (appo - np.min(appo))/np.ptp(appo)
    return b


#########################################################################################
########funzione che trova imm variando la copertura nuvolosa############################
#########################################################################################

def calcola_kmean(imm_input,num_cluster):
    kmeans = KMeans(n_clusters=num_cluster)
    #rows,cols=imm_input.shape
    bands, rows,cols=imm_input.shape
    #reordered=np.reshape(imm_input,(1,rows*cols))
    reordered=np.reshape(imm_input,(bands,rows*cols))
    reordered=reordered.T
    kmeans.fit(reordered)
    clustered_array = kmeans.predict(reordered)
    #clustered_imm=np.reshape(clustered_array,(1, rows,cols))
    clustered_imm=np.reshape(clustered_array,(rows,cols))
    return clustered_imm
