from celery import Celery
from celery.utils.log import get_task_logger
from celery.task.control import revoke

import constants
from functions import *
import geopandas as gpd
import pandas as pd
from geomet import wkt
import pyproj
from shapely.geometry import Polygon,mapping
from sentinelsat import SentinelAPI
import landsatxplore.api
import datetime
import time

import dateutil.relativedelta
import os
import numpy as np
from landsatxplore.earthexplorer import EarthExplorer
import numpy.ma as ma
from skimage.transform import resize

from functions import *
from read_xml import read_xml_sentinel
from lai_cab import calcola_lai,calcola_cab
import traceback
import rasterio as rio
import os.path

from zipfile import ZipFile
import fiona

path=os.getcwd()
#nome del file shp di appoggio in cui viene caricato il poligono con la proiezione di riferimento
shp_proj=path+"/reference.shp"

#sentinel
sentineluser='glicciardi'
sentinelpwd='mokamoka'

#landsat
landsatuser='glicciardi'
landsatpwd='MokaMoka1802'

max_cloud=30
W0=2.17
ki=1.13
ci=0.89
kd=1.41
cd=0.61
ai=43.4
bi=0.95
ad=62
bd=0.52
a=0.5
b=0.5

celery = Celery('smartagri_api',backend='rpc://',broker='pyamqp://guest@localhost//')
logger = get_task_logger(__name__)


@celery.task(bind=True)
def download_task(self,gis,ts):
    lock(None,self,"\n"+gis+"\n"+ts)
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
    result,products_df_sorted,scenes_df_sorted,n_products,n_scenes=check(gis,start_date,stop_date)
    path = os.getcwd()+"/"+constants.data_dir

    if result==True:
        release(None)
        return res_ok("already downloaded",False,True)


    num_record_sentinel, campi=products_df_sorted.shape
    api = SentinelAPI(sentineluser, sentinelpwd, 'https://scihub.copernicus.eu/dhus')
    for i in range (0,num_record_sentinel):
        index=products_df_sorted['uuid'][i]
        api.download(index, path, checksum=True)

    num_record_landsat, campi=scenes_df_sorted.shape

    for i in range (0,num_record_landsat):
        index=scenes_df_sorted['entityId'][i]
        ee = EarthExplorer(landsatuser, landsatpwd)
        ee.download(scene_id=index, output_dir=path)
        ee.logout()
    release(None)
    return res_ok("ok",False,True)


#########################################################################################
# CLUSTERING OMOGENEE
@celery.task(bind=True)
def process_task(self,ts,tenant,code,gis,gis_epsg,satellite,images,dir_out):
    lock(dir_out,self,"\n"+gis+"\n"+ts)
    try:
        coordinates = wkt.loads(gis)
        coordinates=coordinates['coordinates'][0]
        #proj_in = pyproj.Proj("+init=epsg:3857")
        #proj_out = pyproj.Proj("+init=epsg:4326")
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
        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }
        with fiona.open(shp_proj, 'w', 'ESRI Shapefile', schema) as c:
            c.write({
                'geometry': mapping(gis),
                'properties': {'id': 1},
            })
        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }
        with fiona.open(shp_proj, 'w', 'ESRI Shapefile', schema) as c:
            c.write({
                'geometry': mapping(gis),
                'properties': {'id': 1},
            })
        stop_date = datetime.datetime.strptime(ts.split('T')[0], '%d/%m/%Y')
        start_date = calculate_start_date(stop_date)
        result,products_df_sorted,scenes_df_sorted,n_products,n_scenes=check(gis,start_date,stop_date)
        if(n_products==0 and n_scenes==0):
            release(dir_out)
            return res_error(-2,'no images found',dir_out,True)
        if(( n_products>0 or n_scenes>0 ) and result==False):
            release(dir_out)
            return res_error(-1,'missing image files',dir_out,True)
        #controlla se le immagini sono presenti sul server
        now = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(now)
        #inserire processing
        data_path = os.getcwd()+"/"+constants.data_dir
        temp_path=os.getcwd()+"/"+constants.temp_dir



        flag=0
        meta_exist=0
        num_record_sentinel, campi=products_df_sorted.shape
        #if
        if num_record_sentinel>0:
            for i in range (0,num_record_sentinel):
                nome_file=products_df_sorted['title'][i]
                estensione='.zip'
                ###Seleziona solo be immagini con estensione 'JP2'###
                nome_file=data_path+"/"+nome_file+estensione
                present,b4,b8,metadatas=dl_image_4_8(nome_file)
                reproject_et(inpath=b4, outpath=dir_out+'/appo.tif', new_crs='EPSG:4326',platform=1)
                red,meta_red=crop_image_by_shp(dir_out+'/appo.tif',shp_proj)
                reproject_et(inpath=b8, outpath=dir_out+'/appo.tif', new_crs='EPSG:4326',platform=1)
                nir,meta_nir=crop_image_by_shp(dir_out+'/appo.tif',shp_proj)
                ndvi,meta=calcola_ndvi(nir,red,meta_red)
                ndvi=ma.masked_where(ndvi== 0, ndvi)
                ndvi_norm=normalize_ndvi(ndvi)
                ndvi=ndvi_norm
                rows,cols=ndvi.shape
                if flag==0:
                    flag=1
                    result=np.zeros((num_record_sentinel,rows,cols))
                    result[0,:,:]=ndvi
                else:
                    result[i,:,:]=ndvi
            metadata_stack=meta_red
            meta_exist=1
        flag=0
        num_record_landsat, campi=scenes_df_sorted.shape
        if num_record_landsat>0:
            for i in range (0,num_record_landsat):
                nome_file=scenes_df_sorted['displayId'][i]
                estensione='.tar.gz'
                ###Seleziona solo be immagini con estensione 'JP2'###
                nome_file=data_path+"/"+nome_file+estensione
                present,b4,b5,nome_mtl,metadatas=dl_image_4_5(nome_file)
                reproject_et(inpath=b4, outpath=dir_out+'/appo.tif', new_crs='EPSG:4326',platform=0)
                red,meta_red=crop_image_by_shp(dir_out+'/appo.tif',shp_proj)
                reproject_et(inpath=b5, outpath=dir_out+'/appo.tif', new_crs='EPSG:4326',platform=0)
                nir,meta_nir=crop_image_by_shp(dir_out+'/appo.tif',shp_proj)
                m_4,a_4=rescale_reflectance(nome_mtl,4)
                m_5,a_5=rescale_reflectance(nome_mtl,5)
                red=red*m_4+a_4
                nir=nir*m_5+a_5
                ndvi,meta=calcola_ndvi(nir,red,metadatas)
                image_resized = resize(ndvi, (rows,cols),anti_aliasing=False, mode='constant',order=0)
                ndvi=image_resized
                #rows,cols=ndvi.shape
                if flag==0:
                    flag=1
                    result_ls=np.zeros((num_record_landsat,rows,cols))
                    result_ls[0,:,:]=ndvi
                else:
                    result_ls[i,:,:]=ndvi
                if meta_exist==0:
                    metadata_stack=meta_red
                    stack=result_ls
                else:
                    stack=np.zeros((num_record_landsat+num_record_sentinel,rows,cols))
                    stack[0:num_record_sentinel,:,:]=result
                    stack[num_record_sentinel:num_record_landsat+num_record_sentinel,:,:]=result_ls
        else:
            stack=result
        bands,rows,cols=stack.shape
        metadata_stack.update(count=bands)
        metadata_stack.update(width=cols)
        metadata_stack.update(height=rows)
        metadata_stack.update(dtype='float64')


        path_out=dir_out+"/result.tif"
        with rio.open(path_out, 'w', **metadata_stack) as dst:
            for ch in range(stack.shape[0]):
                # iterate over channels and write bands
                img_channel = stack[ch,:, :]
                dst.write(img_channel, ch + 1)
        cluster=calcola_kmean(stack,5)
        meta_cluster=metadata_stack
        meta_cluster.update(count=1)
        meta_cluster.update(dtype='int32')
        path_out=dir_out+"/cluster.tif"
        with rio.open(path_out, 'w', **metadata_stack) as dst:
            dst.write(cluster, 1)
        path_shp=dir_out+"/cluster.shp"
        path_dbf=dir_out+"/cluster.dbf"
        path_shx=dir_out+"/cluster.shx"
        path_zip=dir_out+"/out.zip"
        poligonizza_raster(path_out,path_shp)
        with ZipFile(path_zip, 'w') as zipobj:
            zipobj.write(path_shp, 'out.shp')
            zipobj.write(path_dbf, 'out.dbf')
            zipobj.write(path_shx, 'out.shx')
            zipobj.close()
        driver = ogr.GetDriverByName('ESRI Shapefile')
        data_source = driver.Open(path_shp, 0)
        fc = {
            'type': 'FeatureCollection',
            'features': []
            }
        lyr = data_source.GetLayer(0)
        for feature in lyr:
            fc['features'].append(feature.ExportToJson(as_object=True))
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%YT%H:%M:%S')
        out = {
            'ts': str(st),
            'gis': fc
        }
        out['ts']=st
        out['areas']=fc

        #with open('cluster.json', 'w') as f:
        #    json.dump(fc, f)
        zip_file=open(path_zip,'rb') #???
        out_data = zip_file.read() #???
        release(dir_out)
        return res_ok(str(out),dir_out,True)
    except BaseException as e:
        traceback.print_exc()
        release(dir_out)
        return (res_error(-6,str(type(e))+": "+str(e)),dir_out,True)




# ZONIZZAZIONE STAGIONE
@celery.task(bind=True)
def process_lai_cab_task(self,ts,tenant,code,gis,gis_epsg,satellite,images,cult,_parameters,force_download,dir_out):
    lock(dir_out,self,"\n"+gis+"\n"+ts)
    try:
        # leggo i parametri dinamicamente, per utilizzare basta richiamarli dal dizionario pars (guardare JSON d'esempio)
        pars = {}
        for par in _parameters:
            pars[par["code"]] = par["value"]
        # es. per richiamare W0 -> pars["W0"]

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
        now = datetime.datetime.now()
        timestamp = datetime.datetime.timestamp(now)

        #inserire processing
        data_path = os.getcwd()+"/"+constants.data_dir

        schema = {
            'geometry': 'Polygon',
            'properties': {'id': 'int'},
        }
        with fiona.open(shp_proj, 'w', 'ESRI Shapefile', schema) as c:
            c.write({
                'geometry': mapping(gis),
                'properties': {'id': 1},
            })
        reference_polygon = gpd.read_file(shp_proj)
        geometria_poly=reference_polygon['geometry'][0]
        x_list, y_list = geometria_poly.exterior.coords.xy
        bbox_poly = Polygon([[min(x_list),min(y_list)],[max(x_list),min(y_list)],[max(x_list),max(y_list)],[min(x_list),max(y_list)],[min(x_list),min(y_list)]])
        stop_date = datetime.datetime.strptime(ts.split('T')[0], '%d/%m/%Y')
        start_date = calculate_start_date(stop_date)
        result,products_df_sorted,n_products=check(gis,start_date,stop_date,True)

        if(n_products==0):
            release(dir_out)
            return res_error(-2,'no images found',dir_out,True)
        index=products_df_sorted['uuid'][0]
        nome_file=products_df_sorted['title'][0]
        if(n_products>0 and result==False):
            if(force_download):
                download_sentinel_image(index, data_path)
            else:
                release(dir_out)
                return res_error(-1,'missing image files',dir_out,True)


    #    api = SentinelAPI(sentineluser, sentinelpwd, 'https://scihub.copernicus.eu/dhus')
    #    products = api.query(bbox_poly,date=(start_date,stop_date) , platformname='Sentinel-2',processinglevel= 'Level-2A', cloudcoverpercentage=(0, max_cloud))
    #    if len(products) == 0:
    #        return res_error(-1,'no images found',dir_out)
    #    products_df = api.to_dataframe(products)
    #    products_df_sorted=products_df.sort_values(by='beginposition',ascending=False)

        #api.download(index, data_path, checksum=True)
        estensione='.zip'
        ###Seleziona solo be immagini con estensione 'JP2'###
        nome_file=data_path+'/'+nome_file+estensione
        nome_b3,nome_b4,nome_b5,nome_b6,nome_b7,nome_b8a,nome_b11,nome_b12,nome_xml,metadatas=dl_image_lai_cab(nome_file)
        imm_or=rio.open(nome_b3,'r')
        rows_imm,cols_imm=imm_or.shape
        meta_appo=imm_or.meta
        meta_appo.update({'driver': 'Gtiff','dtype': 'float64'})
        dst_crs='EPSG:4326'
        sun_zenith_angle,sun_azimuth_angle, view_zenith_angle_mean,view_azimuth_angle_mean=read_xml_sentinel(nome_xml,rows_imm,cols_imm)
        sza_file=dir_out+'/sza.tif'
        saa_file=dir_out+'/saa.tif'
        vzam_file=dir_out+'/vzam.tif'
        vaam_file=dir_out+'/vaam.tif'
        with rio.open(sza_file, 'w', **meta_appo) as dst:
            dst.write(sun_zenith_angle, 1)
        with rio.open(saa_file, 'w', **meta_appo) as dst:
            dst.write(sun_azimuth_angle, 1)
        with rio.open(vzam_file, 'w', **meta_appo) as dst:
            dst.write(view_zenith_angle_mean, 1)
        with rio.open(vaam_file, 'w', **meta_appo) as dst:
            dst.write(view_azimuth_angle_mean, 1)
        reproject_et(inpath=nome_b3, outpath=dir_out+'/b3.tif', new_crs='EPSG:4326',platform=1)
        b3,meta_b3=crop_image_by_shp(dir_out+'/b3.tif',shp_proj)
        reproject_et(inpath=nome_b4, outpath=dir_out+'/b4.tif', new_crs='EPSG:4326',platform=1)
        b4,meta_b4=crop_image_by_shp(dir_out+'/b4.tif',shp_proj)
        reproject_et(inpath=nome_b5, outpath=dir_out+'/b5.tif', new_crs='EPSG:4326',platform=1)
        b5,meta_b5=crop_image_by_shp(dir_out+'/b5.tif',shp_proj)
        reproject_et(inpath=nome_b6, outpath=dir_out+'/b6.tif', new_crs='EPSG:4326',platform=1)
        b6,meta_b6=crop_image_by_shp(dir_out+'/b6.tif',shp_proj)
        reproject_et(inpath=nome_b7, outpath=dir_out+'/b7.tif', new_crs='EPSG:4326',platform=1)
        b7,meta_b7=crop_image_by_shp(dir_out+'/b7.tif',shp_proj)
        reproject_et(inpath=nome_b8a, outpath=dir_out+'/b8a.tif', new_crs='EPSG:4326',platform=1)
        b8a,meta_b8a=crop_image_by_shp(dir_out+'/b8a.tif',shp_proj)
        reproject_et(inpath=nome_b11, outpath=dir_out+'/b11.tif', new_crs='EPSG:4326',platform=1)
        b11,meta_b11=crop_image_by_shp(dir_out+'/b11.tif',shp_proj)
        reproject_et(inpath=nome_b12, outpath=dir_out+'/b12.tif', new_crs='EPSG:4326',platform=1)
        b12,meta_b12=crop_image_by_shp(dir_out+'/b12.tif',shp_proj)
        reproject_et(inpath=sza_file, outpath=dir_out+'/sun_zenith_angles.tif', new_crs='EPSG:4326',platform=0)
        sun_zenith_angle_prj,meta_sza=crop_image_by_shp(dir_out+'/sun_zenith_angles.tif',shp_proj)
        reproject_et(inpath=saa_file, outpath=dir_out+'/sun_azimuth_angles.tif', new_crs='EPSG:4326',platform=0)
        sun_azimuth_angle_prj,meta_saa=crop_image_by_shp(dir_out+'/sun_azimuth_angles.tif',shp_proj)
        reproject_et(inpath=vzam_file, outpath=dir_out+'/view_zenith_angles.tif', new_crs='EPSG:4326',platform=0)
        view_zenith_angle_mean_prj,meta_vzam=crop_image_by_shp(dir_out+'/view_zenith_angles.tif',shp_proj)
        reproject_et(inpath=vaam_file, outpath=dir_out+'/view_azimuth_angles.tif', new_crs='EPSG:4326',platform=0)
        view_azimuth_angle_mean_prj,meta_vaam=crop_image_by_shp(dir_out+'/view_azimuth_angles.tif',shp_proj)
        b3=b3/10000
        b4=b4/10000
        b5=b5/10000
        b6=b6/10000
        b7=b7/10000
        b8a=b8a/10000
        b11=b11/10000
        b12=b12/10000
        cols=meta_b3['width']
        rows=meta_b3['height']
        lai=np.zeros((rows,cols))
        cab=np.zeros((rows,cols))
        for i in range (0,rows):
            for j in range(0,cols):
                lai[i,j]=calcola_lai(
                        b3[0,i,j],
                        b4[0,i,j],
                        b5[0,i,j],
                        b6[0,i,j],
                        b7[0,i,j],
                        b8a[0,i,j],
                        b11[0,i,j],
                        b12[0,i,j],
                        sun_zenith_angle_prj[0,i,j],
                        sun_azimuth_angle_prj[0,i,j],
                        view_zenith_angle_mean_prj[0,i,j],
                        view_azimuth_angle_mean_prj[0,i,j])
                cab[i,j]=calcola_cab(
                        b3[0,i,j],
                        b4[0,i,j],
                        b5[0,i,j],
                        b6[0,i,j],
                        b7[0,i,j],
                        b8a[0,i,j],
                        b11[0,i,j],
                        b12[0,i,j],
                        sun_zenith_angle_prj[0,i,j],
                        sun_azimuth_angle_prj[0,i,j],
                        view_zenith_angle_mean_prj[0,i,j],
                        view_azimuth_angle_mean_prj[0,i,j])
        W=np.zeros((rows,cols))
        N_critico=np.zeros((rows,cols))
        N_coltura=np.zeros((rows,cols))
        Mappa_deficit_N=np.zeros((rows,cols))
        lai_ki=lai/ki
        lai_kd=lai/kd
        exp1=1/ci
        exp2=1/cd
        for i in range (0,rows):
            for j in range(0,cols):
                if lai[i,j]<W0:
                    W[i,j]=lai_ki[i,j]**exp1
                else:
                    W[i,j]=lai_kd[i,j]**exp2
                if W[i,j]<W0:
                    N_critico[i,j]=ai*(W[i,j]**bi)
                else:
                    N_critico[i,j]=ad*(W[i,j]**bd)
        N_coltura=a+b*cab
        Mappa_deficit_N=N_critico-N_coltura
        meta_mappa=meta_b3
        meta_mappa.update(dtype='float64')
        with rio.open(dir_out+'/Mappa_deficit_N.tif', 'w', **meta_mappa) as ff:
            ff.write(Mappa_deficit_N,1)
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%d/%m/%YT%H:%M:%S')
        out = {
            'ts': str(st),
            'mappa_deficit_n': str(Mappa_deficit_N),
            'lai': str(lai),
            'cab': str(cab),
            'n_critico': str(N_critico),
            'n_coltura': str(N_coltura)
        }
        write_json_to_file(out,dir_out)
        release(dir_out)
        return res_ok(out,dir_out,True)
    except BaseException as e:
        traceback.print_exc()
        release(dir_out)
        return (res_error(-6,str(type(e))+": "+str(e),dir_out,True))
    #return b3,b4,b5,b6,b7,b8a,b11,b12,sun_zenith_angle_prj,sun_azimuth_angle_prj,view_zenith_angle_mean_prj,view_azimuth_angle_mean_prj


#BILANCIO AZOTO
@celery.task(bind=True)
def process_bilancio_azoto_task(self,ts,tenant,code,gis,gis_epsg,satellite,images,cult,previous_cult,_indexes,dir_out):
    lock(dir_out,self,"\n"+gis+"\n"+ts)
    try:
        # ordino gli indici per poterli richiamare per chiave. Es. indexes["Fn"] mi restituisce l'oggetto dell'indice Fn
        indexes = {}
        for in_index in _indexes:
            #print(Fn)
            indexes[in_index["code"]] = in_index
            pars = {}
            for parameter in in_index["parameters"]:
                pars[in_index["code"]] = parameter # ordino i parametri per chiave
            in_index["parameters"] = pars

        # esempi
        # accedere al valore di Fn -> indexes["Fn"]["value"],
        #                       unità di misura -> indexes["Fn"]["um"]
        # accedere alla lista dei parametri di Fn -> indexes["Fn"]["parameters"]
        # Anche i parametri sono indicizzati per code, quindi si possono richiamare così:
        # esempio valore del parametro Rc dell'indice Fn -> indexes["Fn"]["parameters"]["Rc"]["value"]
        #
        # Ovviamente si può abbreviare assegnando variabili:
        # parsFn = indexes["Fn"]["parameters"],
        # Così è più facile accedere per esempio al valore di Rc ->
        # parsFn["Rc"]["value"]
        #
        # Per i Raster:
        # rasterRc = parsFn["Rc"]["raster"]
        # e poi rasterRc["content"] per il contenuto in base64

        #inserire qua codice

        out = {
            'ciao': 'ciao'
        }
        release(dir_out)
        return res_ok(out,dir_out,True)
    except BaseException as e:
        traceback.print_exc()
        release(dir_out)
        return (res_error(-6,str(type(e))+": "+str(e),dir_out,True))
