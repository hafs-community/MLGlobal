#!/bin/sh

module use /contrib/spack-stack/spack-stack-1.9.1/envs/ue-oneapi-2024.2.1/install/modulefiles/Core
module load stack-oneapi/2024.2.1
module load python/3.11.7
module load py-numpy

#./submit_mlgefs_job_ursa.py -d 2025080100 -a hurricane -r gpu -s hpss
./submit_mlgefs_job_ursa.py -d $1

