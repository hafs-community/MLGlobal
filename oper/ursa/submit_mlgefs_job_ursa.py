#!/usr/bin/env python3

import os
import socket
import datetime
#from datetime import datetime, timedelta
import argparse
import pathlib
from time import time
import subprocess
import json

#import numpy as np

def get_closest_cycle(now=None):

    cycles = [0, 6, 12, 18]

    if now is None:
        now = datetime.datetime.now(datetime.UTC)
        #now = datetime.utcnow()

    current_hour = now.hour

    recent_cycle = max([c for c in cycles if c <= current_hour], default=18)
    if current_hour < min(cycles):
        # If current time is before 00z, subtract a day
        cycle_time = datetime.datetime(now.year, now.month, now.day, recent_cycle) - datetime.timedelta(days=1)
    else:
        cycle_time = datetime.datetime(now.year, now.month, now.day, recent_cycle)

    #return cycle_time - datetime.timedelta(hours=6)
    return cycle_time


def get_job_id(command):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print("Job submission failed:", result.stderr)
        exit(1)

    job_id = result.stdout.strip().split()[-1]

    return job_id


def submit_slurm_run(member, param, model_id, curr_datetime, prev_datetime):

    #Step 1 - generate input file
    command1 = [
        'sbatch', '--nodes=1', '--ntasks=1', '--mem=10g', f'--account={account}', '--partition=u1-service', \
        '--time=30:00', f'--job-name=getdata_{curr_datetime}_{member}', f'--output=output/getdata_{curr_datetime}_{member}_%j.log', f'--error=output/getdata_{curr_datetime}_{member}_%j.log', \
        f'--export=SUBEXPT={experiment},gefs_member={member},config_path={param},model_id={model_id},curr_datetime={curr_datetime},prev_datetime={prev_datetime}', \
        'mlgefs_prepdata_ursa.sh'
    ]
    job_id1 = get_job_id(command1)

    #Step 2 - run graphcast
    if forecast_run_type == 'gpu':
        command2 = ['sbatch', f'--dependency=afterok:{job_id1}', '--nodes=1', f'--account={account}', '--partition=u1-h100', \
            '--qos=gpuwf', '--gres=gpu:h100:1', '--exclusive', '--time=30:00', f'--job-name=run_{curr_datetime}_{member}', f'--output=output/fcst_{curr_datetime}_{member}_%j.log', \
            f'--error=output/fcst_{curr_datetime}_{member}_%j.log', f'--export=SUBEXPT={experiment},forecast_length={forecast_length},gefs_member={member},config_path={param},model_id={model_id},curr_datetime={curr_datetime}', \
            'mlgefs_runfcst_ursa.sh']
    elif forecast_run_type == 'cpu':
        command2 = ['sbatch', f'--dependency=afterok:{job_id1}', '--nodes=1', '--cpus-per-task=180', f'--account={account}', '--partition=u1-compute', \
                '--qos=batch', '--exclusive', '--time=01:30:00', f'--job-name=run_{curr_datetime}_{member}', f'--output=output/fcst_{curr_datetime}_{member}_%j.log', \
            f'--error=output/fcst_{curr_datetime}_{member}_%j.log', f'--export=SUBEXPT={experiment},forecast_length={forecast_length},gefs_member={member},config_path={param},model_id={model_id},curr_datetime={curr_datetime}', \
            'mlgefs_runfcst_ursa.sh']
    else:
        raise NotImplementedError(f'forecast_run_type of {forecast_run_type} is not supported!')

    job_id2 = get_job_id(command2)

    #Step 3 - run TC_tracker
    command3 = ['sbatch', f'--dependency=afterok:{job_id2}', '--nodes=1', '--ntasks=1', f'--account={account}', \
        '--partition=u1-compute', '--time=30:00', '--mem=90g', f'--job-name=tctracker_{curr_datetime}_{member}', f'--output=output/tctracker_{curr_datetime}_{member}_%j.log', \
        f'--error=output/tctracker_{curr_datetime}_{member}_%j.log', f'--export=SUBEXPT={experiment},KEEPDATA={keep_data},forecast_length={forecast_length},gefs_member={member},PDY={curr_datetime[:8]},cyc={curr_datetime[8:]}', \
        'jAIGFS_cyclone_track_00.ecf_ursa']
    job_id3 = get_job_id(command3)

    ##Step 4 - upload data to s3 bucket or hpss
    if archive_type == 's3':
        command4 = ['sbatch', f'--dependency=afterok:{job_id3}', '--nodes=1', '--ntasks=1', f'--account={account}', \
            '--partition=u1-service', '--time=30:00', f'--job-name=datadissm_{curr_datetime}_{member}', f'--output=output/datadissm_{curr_datetime}_{member}_%j.log', \
            f'--error=output/datadissm_{curr_datetime}_{member}_%j.log', f'--export=SUBEXPT={experiment},KEEPDATA={keep_data},gefs_member={member},model_id={model_id},curr_datetime={curr_datetime}', \
            'mlgefs_datadissm_ursa.sh']
        job_id4 = get_job_id(command4)
    elif archive_type == 'hpss':
        command4 = ['sbatch', f'--dependency=afterok:{job_id3}', '--nodes=1', '--ntasks=1', f'--account={account}', \
            '--partition=u1-service', '--time=01:30:00', f'--job-name=archhpss_{curr_datetime}_{member}', f'--output=output/archhpss_{curr_datetime}_{member}_%j.log', \
            f'--error=output/archhpss_{curr_datetime}_{member}_%j.log', f'--export=SUBEXPT={experiment},KEEPDATA={keep_data},gefs_member={member},model_id={model_id},curr_datetime={curr_datetime}', \
            'mlgefs_archhpss_ursa.sh']
        job_id4 = get_job_id(command4)
    else:
        raise NotImplementedError(f'archive_type of {archive_type} is not supported!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download and process GEFS data")
    parser.add_argument("-d", "--start_datetime", help="Start datetime in the format 'YYYYMMDDHH'", default=None)
    parser.add_argument("-e", "--experiment", help="Experiment name", default='EAGLE_ensemble')
    parser.add_argument("-a", "--account", help="Compute project account: e.g., nems", default='hurricane')
    parser.add_argument("-r", "--forecast_run_type", help="Forecast run type: gpu or cpu", default='cpu')
    parser.add_argument("-s", "--archive_type", help="Achive type: s3 or hpss", default='hpss')
    parser.add_argument("-l", "--forecast_length", help="Forecast steps in nubmer of 6-hours", default=64)
    parser.add_argument("-k", "--keep_data", help="Keep run dirs after job completed or being archived", default='YES')
    args = parser.parse_args()

    account=args.account
    forecast_run_type=args.forecast_run_type
    archive_type=args.archive_type
    experiment=args.experiment
    forecast_length=args.forecast_length
    keep_data=args.keep_data.upper()
    print(f'account: {account}')
    print(f'forecast_run_type: {forecast_run_type}')
    print(f'archive_type: {archive_type}')
    print(f'experiment: {experiment}')
    print(f'forecast_length: {forecast_length}')
    print(f'keep_data: {keep_data}')

    if args.start_datetime is not None:
        now = datetime.datetime.strptime(args.start_datetime, "%Y%m%d%H")
    else:
        now = None

    hostname = socket.gethostname()
    if hostname.startswith('ufe'):
        param_path = '/scratch3/NCEPDEV/nems/Linlin.Cui/Tests/MLGEFSv1.0/oper/graphcast_gefs_params'
    elif hostname.startswith('linlincui'):
        param_path = '/lustre2/Linlin.Cui/MLGEFSv1.0/weights'
    else:
        raise NotImplementedError(f'{hostname} is not supported yet!')

    with open('model_weights_ursa.json', 'r') as file:
        models = json.load(file)

    #Get current forecast cycle
    curr_datetime = get_closest_cycle(now=now)
    prev_datetime = curr_datetime - datetime.timedelta(hours=6)
    print(f'curr_datetime: {curr_datetime}')
    print(f'prev_datetime: {prev_datetime}')

    for key, values in models.items():
        if key == '0':
            member = f'c{int(key):02d}'
        else:
            member = f'p{int(key):02d}'

        param = f'{param_path}/{values.get("params")}'
        submit_slurm_run(member, param, key, curr_datetime.strftime("%Y%m%d%H"), prev_datetime.strftime("%Y%m%d%H"))
