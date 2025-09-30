#!/bin/sh

set -xe

date

ymdh=${1:-2025081200}
account=${2:-hurricane}

HOMEdir=/scratch3/HFIP/hwrfv3/save/${USER}/mlglobal_202509
cd ${HOMEdir}/oper/ursa

EXPT=$(basename ${HOMEdir})
export SUBEXPT=${SUBEXPT:-${EXPT}_ensemble}
WORKdir=/scratch3/NCEPDEV/stmp/${USER}/${SUBEXPT}
OUTPUTdir=${WORKdir}/output
mkdir -p ${OUTPUTdir}
ln -sf ${OUTPUTdir} ./

#./submit_mlgefs_job_ursa.py -h # To list more commandline options
# Examples
#./submit_mlgefs_job_ursa.py -e EAGLE_ensemble -d 2025081200 -l 64 -a hurricane -r gpu -s hpss -k NO
./submit_mlgefs_job_ursa.py -e ${SUBEXPT} -d ${ymdh} -a ${account}

date

echo "done"
