#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from .base_class import BaseDownloadClass

# import pandas as pd
import polars as pl
import obspy
import glob
from urllib.parse import urljoin

import random
import requests
import os
import shutil
import json
from copy import deepcopy
from datetime import datetime, timedelta


from onc.onc import ONC


try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    # assume everything is loaded using export $(cat .env | xargs)
    pass

token = os.getenv('ONC_TOKEN')

def check_token_is_set():
    """
    """
    error_message = """You do not have an Ocean Networks Canada token registered in the repository. To add your token, run
    hydrophone-downloader-set-token ONC_token=<your_token_here>

    This only needs to be done once. If you do not have an ONC token, you can get one by registering at https://data.oceannetworks.ca/Profile and then going to the 'Web Services' tab and clicking "Generate Token".
    """
    assert token is not None, error_message
    assert token != "" , error_message


def str_gen():
    STR_KEY_GEN = 'abcdefghijklmnopqrstuvwxyz1234567890'
    return ''.join(random.choice(STR_KEY_GEN) for _ in range(16))



class ONCDownloadClass(BaseDownloadClass):
    def __init__(self):
        super().__init__()
        check_token_is_set()
        self.onc = ONC(token=token, )
        self.token = token
        self.license = 'CC-BY 4.0'
        self.__post_init__()

    def get_deployments(self,):
        """
        a list of deployments, each deployment is a day of data, containing a dict of the following:
        {
            'date': 'YYYY-MM-DD',
            'latitude': float,
            'longitude': float,
            'depth': float,
            'license': str,
            'source': str,
            # any other information that is useful to save
        }
        """

        deployments_out = []

        # get all of the locations
        url = 'https://data.oceannetworks.ca/api/locations'
        parameters = {'method':'get',
                    'token':self.token, # replace YOUR_TOKEN_HERE with your personal token obtained from the 'Web Services API' tab at https://data.oceannetworks.can/Profile when logged in.
                    'deviceCategoryCode':'HYDROPHONE'}
        
        response = requests.get(url,params=parameters)
        
        if (response.ok):
            locations = json.loads(str(response.content,'utf-8')) # convert the json response to an object

        else:
            if(response.status_code == 400):
                error = json.loads(str(response.content,'utf-8'))
                print(error) # json response contains a list of errors, with an errorMessage and parameter
            else:
                print ('Error {} - {}'.format(response.status_code,response.reason))



        seen = set()  # Add this before the for location in locations: loop

        for location in locations:
            # get the locatio{'dpo_audioFormatConversion':1,'dpo_hydrophoneDataDiversionMode':'OD'}n code.
            locationCode = location['locationCode']

    
            url = 'https://data.oceannetworks.ca/api/deployments'
            parameters = {'method':'get',
                        'token':token, # replace YOUR_TOKEN_HERE with your personal token obtained from the 'Web Services API' tab at https://data.oceannetworks.ca/Profile when logged in.
                        'locationCode':locationCode,
                        'deviceCategoryCode':'HYDROPHONE'}
            
            response = requests.get(url,params=parameters)
            
            if (response.ok):
                deployments = json.loads(str(response.content,'utf-8')) # convert the json response to an object
            else:
                if(response.status_code == 400):
                    error = json.loads(str(response.content,'utf-8'))
                    print(error) # json response contains a list of errors, with an errorMessage and parameter
                else:
                    print ('Error {} - {}'.format(response.status_code,response.reason))

            # for each deployment, get the deployment code
            # print(deployments)
            # input()
            for deployment in deployments:              

                # begin = pd.to_datetime(deployment['begin'], format='%Y-%m-%dT%H:%M:%S.000Z')
                begin = datetime.strptime(deployment['begin'], '%Y-%m-%dT%H:%M:%S.000Z')
                if deployment['end'] is None:
                    # end = pd.Timestamp.now()
                    end = datetime.now()
                else:
                    # end = pd.to_datetime(deployment['end'], format='%Y-%m-%dT%H:%M:%S.000Z')
                    end = datetime.strptime(deployment['end'], '%Y-%m-%dT%H:%M:%S.000Z')

                

                # for date in pd.date_range(start=begin.date(), end=end.date()+pd.Timedelta('1D'))[::-1]:
                for date in pl.date_range(start=begin, end=end, interval='1d', eager=True).alias('date').to_frame().to_dict()['date'][::-1]:
                    key = (locationCode, date)
                    if key in seen:
                        continue
                    seen.add(key)

                    # print('latitude', deployment['lat'])
                    # print('longitude', deployment['lon'])
                    # print('locationCode', locationCode)
                    # print(date)
                    # print(date.date())
                    # print(deployment['deviceCode'])


                    if deployment['citation'] is None:
                        citation = None
                    else:
                        citation = deployment['citation']['citation']


                    fname = (date).strftime('%Y_%m_%d')+'-'+locationCode+f"lat{deployment['lat']:.3f}lon{deployment['lon']:.3f}"

                    


                    # todo download wav if pre April 9, 2021, then convert to flac using ffmpeg

                    extension='flac'
                    # if date <= pd.Timestamp('2021-04-09'):
                    if date <= datetime.strptime('2021-04-09', '%Y-%m-%d').date():
                        extension='wav'

                    
                    filters = {
                        'deviceCode':deployment['deviceCode'],    # AML CTD Metrec X 50348 in Burrard Inlet
                        'dateFrom': date.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                        # 'dateTo': (date+pd.Timedelta('1D')).strftime('%Y-%m-%d')+'T00:00:00.000Z',
                        'dateTo': (date+timedelta(days=1)).strftime('%Y-%m-%d')+'T00:00:00.000Z',
                        'extension':extension,
                    }

                    deployments_out.append({
                        'date': date,
                        'latitude': deployment['lat'],
                        'longitude': deployment['lon'],
                        'depth': deployment['depth'],
                        'license': self.license,
                        'locationCode': locationCode,
                        'source': 'ONC',
                        'fname': fname,
                        'citation': citation,
                        'filters': filters
                    })

        print('There are', len(deployments_out), 'deployments available from ONC')
        return deployments_out

    

    def download_data(self, min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time, save_dir):
        """
        Download data from ONC, saving to a temp folder and then moving to the final destination.
        """

        from datetime import datetime

        # First, get deployments (must be before using deployments)
        deployments = self.filter_deployments(
            min_lat, max_lat, min_lon, max_lon, min_depth, max_depth, license, start_time, end_time
        )

        for deployment in deployments:
            filters = deployment['filters']
            locationCode = deployment['locationCode']
            date = deployment['date']
            fname = os.path.join(save_dir, deployment['fname'])
            os.makedirs(fname, exist_ok=True)

            # Create a unique temp folder for each deployment
            device_code = filters['deviceCode']
            date_str = date.strftime("%Y%m%d")
            timestamp = datetime.now().strftime("%H%M%S")
            outPath = os.path.join(save_dir, f"tmp_{device_code}_{locationCode}_{date_str}_{timestamp}")
            self.onc = ONC(token=self.token, outPath=outPath)

            citation = deployment['citation']
            if citation is not None:
                author, year, title, journal, doi = citation.split('. ')
                citation = "@misc{"+fname.split('/')[-1]+", author={"+author+"}, year={"+year+"}, title={"+title+"}, journal={"+journal+"}, doi={"+doi+"},}"
                with open(os.path.join(fname, 'reference.bib'), 'w') as f:
                    f.write(citation)

            filters_archived = filters.copy()
            filters_archived['rowLimit'] = 80000
            results = self.onc.getListByDevice(filters_archived)
            if len(results['files'])>0:
                # download the files
                try:
                    result = self.onc.getDirectFiles(filters_archived)
                    # save the filters to json in fname
                    with open(os.path.join(fname, 'filters.json'), 'w') as f:
                        json.dump(filters_archived, f)

                    print("*"*40)
                except:
                    print("FAIL"*40)
                    # we will still want to clean up and transfer the files
                    pass
            else:
                # optional parameters to loop through and try:
                filters_orig = {'locationCode': locationCode,'deviceCategoryCode':'HYDROPHONE','dataProductCode':'AD','extension':'flac','dateFrom':date.strftime('%Y-%m-%d'),'dateTo':(date+timedelta(days=1)).strftime('%Y-%m-%d'),'dpo_audioDownsample':-1} #, 'dpo_audioFormatConversion':0}
                is_done = False

                for d in [{'dpo_hydrophoneDataDiversionMode':'OD'}, {'dpo_hydrophoneDataDiversionMode':'OD', 'dpo_hydrophoneChannel':'All'},{'dpo_hydrophoneChannel':'All'},{'dpo_audioFormatConversion':0,'dpo_hydrophoneDataDiversionMode':'OD','dpo_hydrophoneChannel':'All'},{'dpo_audioFormatConversion':0,'dpo_hydrophoneDataDiversionMode':'OD'},{'dpo_audioFormatConversion':1,'dpo_hydrophoneDataDiversionMode':'OD','dpo_hydrophoneChannel':'All'}]:
                    filters = deepcopy(filters_orig)
                    filters.update(d)
                    try:
                        print(filters)
                        result  = self.onc.orderDataProduct(filters, includeMetadataFile=False)
                        # save the filters to json in fname
                        with open(os.path.join(fname, 'filters.json'), 'w') as f:
                            json.dump(filters, f)
                        is_done=True
                        break
                    except:
                        continue

            if filters['extension'] == 'wav':
                print("WAV files downloaded, no conversion to FLAC performed. Keeping WAV and deleting no files here.")
                # WAV files are kept as is.
            # os.system(f'rsync -aavt --remove-source_files tmp/* {fname}')
            for s in glob.glob(outPath+'/*', recursive=True):
                if not os.path.exists(fname):
                    shutil.move(s, fname)

            # Clean up temp folder after moving files
            shutil.rmtree(outPath, ignore_errors=True)


