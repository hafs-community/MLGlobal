#!/bin/sh

set -xe

date

SUBEXPT=${SUBEXPT:-EAGLE_ensemble}
COMROOT=/scratch3/NCEPDEV/stmp/${USER}/${SUBEXPT}
HPSSROOT=/NCEPDEV/emc-hwrf/5year/${USER}/${SUBEXPT}

export KEEPDATA=${KEEPDATA:-NO}
export num_pressure_levels=${num_pressure_levels:-13}

echo "Current state: $curr_datetime"

start_time=$(date +%s)
echo "Uploading member $gefs_member for: $curr_datetime"

## Extract the date and hour parts
ymd=${curr_datetime:0:8}
hour=${curr_datetime:8:2}

COMdir=$COMROOT/pmlgefs."$ymd"/"$hour"
HPSSdir=$HPSSROOT/${ymd}
# archive to HPSS
cd $COMdir/
hsi mkdir -p ${HPSSdir}
htar -cvf ${HPSSdir}/pmlgefs.${curr_datetime}.${gefs_member}.tar forecasts_${num_pressure_levels}_levels_${gefs_member}_model_${model_id}

if [ $? -ne 0 ]; then
  echo "FATAL ERROR: htar failed"
  exit 1
else
  echo "htar FINISHED. Clean up the local dir if KEEPDATA == NO."
  if [[ ${KEEPDATA} == NO ]]; then
    rm -r forecasts_${num_pressure_levels}_levels_${gefs_member}_model_${model_id}
  fi
fi

end_time=$(date +%s)  # Record the end time in seconds since the epoch
# Calculate and print the execution time
execution_time=$((end_time - start_time))
echo "Execution time for uploading: $execution_time seconds"

date
