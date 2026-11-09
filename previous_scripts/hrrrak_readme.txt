HRRR-AK ReadMe Notes 

We have a working .sh script named "download_hrrrak_final_fixed_date_and_forecast.sh" which required some specific changes from the HRRR-CONUS download script.

The AK domain gets run every 3 hours, with hourly forecast time

Can either be given two arguments for year and month:
./download_hrrrak_final.sh YYYY MM (Archive)
or loop over the dates given as one argument separated by comma.
./download_hrrrak_final.sh YYYYMMDD,YYYYMMDD (Archive)

then use the `2_clean_hrrrak_netcdf.ipynb` notebook to clean up the hrrr downloads into a tidy netcdf. 