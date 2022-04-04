#!/usr/bin/python3.7

# skripta za AWOS
# testna stanica

# parameters TSoilNNN/HSoilNNN-soil temperature/humidity on NNN cm deep

import json
import datetime
import time
import random
import os
import board
# modul za vlaznost/temperaturu, senzor DHT22
import Adafruit_DHT

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

import threading

def statistical_calculation(input_list):
    output_list=['///' for i in range(5)]
    current=[]
    for i,j in input_list[-5:]:
        try:
            current.append(float(j))
        except:
            pass
    if len(current)>0:
        output_list[0]='{:0.1f}'.format(sum(current)/len(current))
    pmin, pmax= 10000, -10000
    for i,j in input_list:
        try:
            if float(j)<pmin:
                pmin=float(j)
                output_list[1],output_list[2]=j,i[:5]
            if float(j)>pmax:
                pmax=float(j)
                output_list[3],output_list[4]=j,i[:5]
        except:
            pass
    #output [current, min, time_min, max, time_max]
    return output_list

class Mjerenje:
    def __init__(self, data_pin, senzor):
        self.data_pin=data_pin
        self.senzor=senzor
        self.izmjereno=[]
        for i in range(len(self.data_pin)):
            self.izmjereno.append('///')
    def dht22(self):
        try:
            dht_device = Adafruit_DHT.AM2302
            humidity,temperature=Adafruit_DHT.read_retry(dht_device,self.data_pin[0])
            self.izmjereno=['{:0.1f}'.format(temperature), '{:0.1f}'.format(humidity)]
        except:
            pass
        return self.izmjereno
    def mjerenje(self):
        if self.senzor=='dht22':#vraca [temperatura,vlaznost]
            thread=threading.Thread(target=self.dht22)
        else:
            pass
        thread.start()
        thread.join(timeout=3)
        return self.izmjereno

if __name__=='__main__':
    #edit/set absolute script path in next line
    script_path='/absolute/script/path'
    main_dict={'metadata':{}}
    all_measurements_dict={}
    tmp_dict={}
    if os.path.exists(script_path+'/sensors.json') and os.path.exists(script_path+'/station.json'):
        with open(script_path+'/sensors.json') as json_file:
            json_sensors=json.load(json_file)
        with open(script_path+'/station.json') as json_file:
            json_station=json.load(json_file)
    else:
        exit()
    measurement_minute=json_station["setup"]["measurement_minute"]
    report_minute=json_station["setup"]["report_minute"]
    all_parameters,meteo_parameters=[],[]
    for sensor in json_sensors:
        if sensor['senzor']!='rpi':
            meteo_parameters.extend(sensor["parametri"])
            for parametri in sensor['parametri']:
                all_parameters.extend([parametri+y for y in ['','Min','Max','MinTime','MaxTime','NumberOfSamples']])
    meta_parameters=[]
    for meta in json_station["metadata"]:
        main_dict['metadata'][meta]=json_station['metadata'][meta]

    #iskljucivanje svih gpio pinova: setovanje pinova na logicki LOW tj 0
    all_connected_data_pins=[]
    for senzor in json_sensors:
        all_connected_data_pins.extend(senzor['gpio_data_pin'])
    for pin in set(all_connected_data_pins):
        if pin>0:
            GPIO.setup(pin, GPIO.IN)

    while True:
        try:
            current_time_1=datetime.datetime.utcnow()+datetime.timedelta(hours=1)
            for grupa in json_sensors:
                izmjereno=Mjerenje(senzor=grupa['senzor'], data_pin=grupa['gpio_data_pin']).mjerenje()
                for i in range(len(izmjereno)):
                    tmp_dict.setdefault(grupa['parametri'][i],[])
                    tmp_dict[grupa['parametri'][i]].append([(current_time_1+datetime.timedelta(minutes=1)).strftime('%H:%M:%S'), izmjereno[i]])
            time.sleep(20) #WMO standard for sampling temperature (3sec for wind, 20sec for others)
            current_time_2=datetime.datetime.utcnow()+datetime.timedelta(hours=1)
            if int(current_time_1.strftime('%S'))>int(current_time_2.strftime('%S')):
                if current_time_2.strftime('%M') in measurement_minute:
                    m_time=current_time_2.strftime('%Y-%m-%dT%H:%M:%S+01:00')
                    all_measurements_dict[m_time]={}
                    for meteo_parameter in meteo_parameters:
                        statistics=statistical_calculation(tmp_dict[meteo_parameter])
                        all_measurements_dict[m_time][meteo_parameter]=statistics[0]
                        if meteo_parameter+'Min' in all_parameters:
                            all_measurements_dict[m_time][meteo_parameter+'Min']=statistics[1]
                            all_measurements_dict[m_time][meteo_parameter+'MinTime']=statistics[2]
                        if meteo_parameter+'Max' in all_parameters:
                            all_measurements_dict[m_time][meteo_parameter+'Max']=statistics[3]
                            all_measurements_dict[m_time][meteo_parameter+'MaxTime']=statistics[4]
                if current_time_2.strftime('%M') in report_minute:
                    main_dict['metadata']['report_time']=(datetime.datetime.utcnow()+datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S+01:00')
                    i=0
                    for vrijeme,podaci in all_measurements_dict.items():
                        main_dict['dataset'+str(i)]={'Time':vrijeme}
                        main_dict['dataset'+str(i)].update(podaci)
                        i+=1
                    all_measurements_dict={}
                    with open(script_path+'/DATA/'+'SXQB'+json_station['metadata']['measurement_id']+'_'+json_station['metadata']['locator']+'_'+current_time_2.strftime('%Y%m%d%H%M%S'), 'w') as outfile:
                        json.dump(main_dict, outfile, indent=4)
        except KeyboardInterrupt:
            exit()
exit()
