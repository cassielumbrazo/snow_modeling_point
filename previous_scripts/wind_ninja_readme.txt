Wind Ninja ReadMe Notes

Pre-Run Notes
* The wind field extent needs to be larger (or exactly) the extend of the DEM (not the other way around)

Run Notes
To run on this linux machine, we run the following command to open a docker container with holds Wind Ninja 
> docker run -v /hdd:/hdd -it windninja:latest /bin/bash 

Then we call "WindNinja_cli" to run Wind Ninja inside that docker container, pointing to a config file 
> WindNinja_cli /hdd/snow_hydrology/wind_ninja/example_files/CONFIG_FILE_NAME.cfg 