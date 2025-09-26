#!/bin/bash

# load modules
module use /contrib/spack-stack/spack-stack-1.9.1/envs/ue-oneapi-2024.2.1/install/modulefiles/Core/
module load stack-oneapi
module load awscli-v2/2.15.53
module list

echo "Current state: $curr_datetime"

start_time=$(date +%s)
echo "Uploading member $gefs_member for: $curr_datetime"

## Extract the date and hour parts
ymd=${curr_datetime:0:8}
hour=${curr_datetime:8:2}

# upload forecast outputs
aws s3 --profile gcgfs sync $curr_datetime/forecasts_13_levels_${gefs_member}_model_${model_id}/ s3://noaa-nws-graphcastgfs-pds/${SUBEXPT:-EAGLE_ensemble}/pmlgefs."$ymd"/"$hour"/forecasts_13_levels_${gefs_member}_model_${model_id}/
rm -r $curr_datetime/forecasts_13_levels_${gefs_member}_model_${model_id}

end_time=$(date +%s)  # Record the end time in seconds since the epoch
# Calculate and print the execution time
execution_time=$((end_time - start_time))
echo "Execution time for uploading: $execution_time seconds"
