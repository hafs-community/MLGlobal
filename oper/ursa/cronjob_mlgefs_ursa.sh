#!/bin/sh

set -xe

date
account=hurricane
ymdh_beg=2025081200
ymdh_end=2025081206
ymdh_int=6

HOMEdir=/scratch3/HFIP/hwrfv3/save/${USER}/mlglobal_202509
cd ${HOMEdir}/oper/ursa

EXPT=$(basename ${HOMEdir})
export SUBEXPT=${SUBEXPT:-${EXPT}_ensemble}
WORKdir=/scratch3/NCEPDEV/stmp/${USER}/${SUBEXPT}
OUTPUTdir=${WORKdir}/output
mkdir -p ${OUTPUTdir}
ln -sf ${OUTPUTdir} ./

ymdh=${ymdh_beg}
# Loop for forecast cycles
while [ ${ymdh} -le ${ymdh_end} ]; do
  ntrk=$(/bin/ls -1 ${WORKdir}/ens_tracker/com/aigfs.${ymdh:0:8}/${ymdh:8:2}/products/atmos/cyclone/tracks/m???p.t${ymdh:8:2}z.cyclone.trackatcfunix | wc -l)
  nmem=$(grep params ./model_weights_ursa.json | wc -l)
  if [[ $ntrk == $nmem ]]; then
    echo "Forecast cycle ${ymdh} completed"
    # Increment ymdh by ymdh_int hours
    ymdh=$(date -u -d "${ymdh:0:8} ${ymdh:8:2} +${ymdh_int} hours" +"%Y%m%d%H")
    continue
  else
    echo "Running forecast cycle: ${ymdh}"
    narchjobs=$(squeue -u ${USER} -h -t pending,running -r  | grep archhpss_${ymdh} | wc -l)
    njoblogs=$(/bin/ls -1 ${OUTPUTdir}/*${ymdh}*.log | wc -l)
    if [[ $narchjobs > 0 ]] || [[ $njoblogs > 0 ]]; then
      echo "Still ${narchjobs} archhpss jobs ongoing or there were previously $njoblogs job logs for ${ymdh}. Exit now, check and revisit later on."
    else
      echo "Check and run ./submit_mlgefs_job_ursa.py"
      # Check active jobs under account
      n_jobs=$(squeue -u ${USER} -h -t pending,running -r -A ${account} | wc -l)
      # MaxJobs = 400, job number limit per account on Ursa
      if [[ $(($n_jobs + 4 * $nmem)) < 400 ]]; then
        ./submit_mlgefs_job_ursa.py -e ${SUBEXPT} -d ${ymdh} -a ${account}
      else
        echo "INFO: Number of active jobs under $account: $(($n_jobs + 4 * $nmem)) will exceed the MaxJobs (400) limit."
        echo "INFO: Skip submitting jobs for ${ymdh} for now."
        echo "INFO: You can wait and revisit later on."
      fi
    fi
    exit
  fi
done
