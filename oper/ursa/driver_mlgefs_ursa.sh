#!/bin/sh

set -xe

#module use /contrib/spack-stack/spack-stack-1.9.1/envs/ue-oneapi-2024.2.1/install/modulefiles/Core
#module load stack-oneapi/2024.2.1
#module load python/3.11.7
#module load py-numpy

date
HOMEdir=/scratch3/HFIP/hwrfv3/save/${USER}/mlglobal
cd ${HOMEdir}/oper/ursa

ymdh=${1:-2025090100}
SUBEXPT=EAGLE_ensemble
mkdir -p /scratch3/NCEPDEV/stmp/${USER}/${SUBEXPT}/output
ln -sf /scratch3/NCEPDEV/stmp/${USER}/${SUBEXPT}/output ./
#./submit_mlgefs_job_ursa.py -e EAGLE_ensemble -d 2025080100 -l 64 -a hurricane -r gpu -s hpss
#./submit_mlgefs_job_ursa.py -d ${ymdh}
./submit_mlgefs_job_ursa.py -e ${SUBEXPT} -d ${ymdh}

date

echo "done"
