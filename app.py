from flask import Flask, request, jsonify, g
from public_functions import *
from functions import *
from multiprocessing import Value
import os

import traceback
import os.path
flask = Flask(__name__)

    #revoke(task_id, terminate=True)
    #with counter.get_lock():
    #    counter.value += 1
    #return "result: "+str(counter.value)
@flask.route('/op1/process', methods = ['POST'])
def clusteringOmogenee():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = process(content["ts"],content["tenant"],content["code"],content["gis"],content.get("gis_epsg","epsg:3857"),content.get("satellite",None),content.get("images",None))
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op1/get', methods = ['POST'])
def getClusteringOmogenee():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = get_process(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op1/stop', methods = ['POST'])
def stopClusteringOmogenee():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = stop_process(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op2/process', methods = ['POST'])
def zonizzazioneStagione():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    if('force_download' in content):
        force_download = content["force_download"]
        if(isinstance(force_download, str) and force_download.lower().strip()=='false'):
            force_download = False
    else:
        force_download = False
    try:
        response = process_lai_cab(content["ts"],content["tenant"],content["code"],content["gis"],content.get("gis_epsg","epsg:3857"),content.get("satellite",None),content.get("images",None),content.get("cult",None),content.get("parameters",None),force_download)
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op2/get', methods = ['POST'])
def getZonizzazioneStagione():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = get_process_lai_cab(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op2/stop', methods = ['POST'])
def stopZonizzazioneStagione():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = stop_process_lai_cab(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op3/process', methods = ['POST'])
def bilancioAzoto():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = process_bilancio_azoto(content["ts"],content["tenant"],content["code"],content["gis"],content.get("gis_epsg","epsg:3857"),content.get("satellite",None),content.get("images",None),content.get("cult",None),content.get("previous_cult",None),content["indexes"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op3/get', methods = ['POST'])
def getBilancioAzoto():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = get_process_bilancio_azoto(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/op3/stop', methods = ['POST'])
def stopBilancioAzoto():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    try:
        response = stop_process_bilancio_azoto(content["ts"],content["tenant"],content["code"])
        print(response)
        return response
    except BaseException as e:
        traceback.print_exc()
        return (res_error(-7,str(type(e))+": "+str(e)))

@flask.route('/download', methods = ['POST'])
def startDownload():
    if request.method == 'POST':
        print (request.is_json)
    content = request.get_json()
    print (content)
    response = download(content["gis"],content["ts"])
    print(response)
    return response

@flask.route('/download/stop', methods = ['POST'])
def stopDownload():
    if request.method == 'POST':
        print (request.is_json)
    response = stop_download()
    print(response)
    return response
#    return jsonify(
#        test="jsontest",
#        test2="datadatas",
#        id="g.user.id"
#    )

# code : nome terreno ovvero nome to_file
# gis : poligono
# gis_epsg : proiezione DA NON METTERE
# ts : stop_date  da cui start_date meno due mesi
