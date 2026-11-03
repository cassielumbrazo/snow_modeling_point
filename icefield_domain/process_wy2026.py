"""WY2026 extension of 1_process_hrrrak_grib_files.ipynb.

The decoder and historical reprojection convention are preserved for consistency
with WY2020–WY2025. At most eight daily batches run at once. Missing source days
are reported, never filled. Historical outputs are opened read-only.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import os
import warnings
import numpy as np
import pandas as pd
import xarray as xr
import pygrib
import rioxarray

desired_vars = [
    't',        # Temperature (surface level)
    'sp',       # Surface pressure
    '2t',       # 2 metre temperature
    '2r',       # 2 metre relative humidity
    'tp',       # Total Precipitation
    'prate',    # Precipitation rate
    '10u',      # 10 metre U wind component
    '10v',      # 10 metre V wind component
    'sdswrf',   # Surface downward short-wave radiation flux
    'sdlwrf',   # Surface downward long-wave radiation flux
    # Extras
    'gust',     # Wind speed (gust)
    'tcc',      # Total Cloud Cover
    'lcc',      # Low cloud cover
    'mcc',      # Medium cloud cover
    'hcc',      # High cloud cover
    'lai',      # Leaf Area Index
    '2d',       # 2 metre dewpoint temperature
    '2sh',      # 2 metre specific humidity
    'suswrf',   # Surface upward short-wave radiation flux
    'sulwrf',   # Surface upward long-wave radiation flux
    'orog',     # Orography
    'sdwe',     # Water equivalent of accumulated snow depth
    'sde',      # Snow depth
    'veg',      # Vegetation
    'vgtyp',    # Vegetation Type
    'gflux',    # Ground heat flux
]

def process_grib_file(grib_path):
    """ Process a single .grib2 file and return an xarray dataset """
    try:
        # Extract init time and forecast step from filename
        # Example: 'hrrr.t00z.wrfsfcf05.ak.grib2' -> init_hour=0, forecast_step=5
        filename = os.path.basename(grib_path)
        init_hour = int(filename.split('.')[1][1:3])  # 't00z' -> 0
        forecast_step = int(filename.split('.')[2][-2:])  # 'wrfsfcf05' -> '05' -> 5

        # Get date from folder name
        date_str = grib_path.split('/')[-2].split('.')[1]  # e.g., '20241001'
        init_datetime = pd.to_datetime(f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {init_hour:02d}:00")
        valid_time = init_datetime + pd.Timedelta(hours=forecast_step)

        # Collect desired vars using pygrib
        grbs = pygrib.open(grib_path)
        var_info = {}
        grid_latlon = None
        for grb in grbs:
            short_name = grb.shortName.lower()
            if short_name in desired_vars:
                # Special filter: for 't', only keep surface level
                if short_name == 't' and not (grb.typeOfLevel == 'surface'):
                    continue
                if grid_latlon is None:
                    grid_latlon = grb.latlons()
                key = f"{short_name}_{grb.level}_{grb.typeOfLevel}"
                var_info[key] = {
                    'short_name': short_name,
                    'level': grb.level,
                    'typeOfLevel': grb.typeOfLevel,
                    'data': grb.values,
                    'lat': grid_latlon[0],
                    'lon': grid_latlon[1],
                    'attrs': {  # Preserve GRIB metadata
                        'long_name': getattr(grb, 'name', short_name),
                        'units': getattr(grb, 'units', ''),
                        'GRIB_shortName': getattr(grb, 'shortName', short_name),
                        'GRIB_name': getattr(grb, 'name', ''),
                        'GRIB_cfName': getattr(grb, 'cfName', ''),
                        'GRIB_cfVarName': getattr(grb, 'cfVarName', ''),
                        'level': grb.level,
                        'typeOfLevel': grb.typeOfLevel
                    }
                }
        grbs.close()

        if not var_info:
            print(f"⚠️ Skipping {grib_path}: No desired variables found")
            return None

        # Create merged dataset
        datasets = []
        first_key = list(var_info.keys())[0]
        lat = var_info[first_key]['lat']
        lon = var_info[first_key]['lon']

        grouped_vars = {}
        for key, info in var_info.items():
            group_key = f"{info['short_name']}_{info['typeOfLevel']}"
            if group_key not in grouped_vars:
                grouped_vars[group_key] = []
            grouped_vars[group_key].append(info)

        for group_key, infos in grouped_vars.items():
            short_name = infos[0]['short_name']
            type_level = infos[0]['typeOfLevel']
            attrs = infos[0]['attrs']  # Use attrs from first (assuming consistent)

            if len(infos) == 1:
                info = infos[0]
                data = info['data']
                level = info['level']

                if type_level == 'surface' or (type_level == 'heightAboveGround' and level == 0):
                    da = xr.DataArray(
                        data,
                        dims=['y', 'x'],
                        coords={
                            'y': range(data.shape[0]),
                            'x': range(data.shape[1]),
                            'latitude': (['y', 'x'], lat),
                            'longitude': (['y', 'x'], lon)
                        },
                        attrs=attrs,
                        name=short_name
                    )
                elif type_level == 'heightAboveGround' and level in [2, 10]:
                    da = xr.DataArray(
                        data,
                        dims=['y', 'x'],
                        coords={
                            'y': range(data.shape[0]),
                            'x': range(data.shape[1]),
                            'latitude': (['y', 'x'], lat),
                            'longitude': (['y', 'x'], lon)
                        },
                        attrs={**attrs, 'heightAboveGround': level},  # Add height as attr
                        name=short_name
                    )
                else:
                    da = xr.DataArray(
                        data,
                        dims=['y', 'x'],
                        coords={
                            'y': range(data.shape[0]),
                            'x': range(data.shape[1]),
                            'latitude': (['y', 'x'], lat),
                            'longitude': (['y', 'x'], lon)
                        },
                        attrs=attrs,
                        name=short_name
                    )
                datasets.append(da)
            else:
                # Multi-level (rare now)
                levels = [info['level'] for info in infos]
                data_stack = np.stack([info['data'] for info in infos], axis=0)
                da = xr.DataArray(
                    data_stack,
                    dims=['level', 'y', 'x'],
                    coords={
                        'level': levels,
                        'y': range(data_stack.shape[1]),
                        'x': range(data_stack.shape[2]),
                        'latitude': (['y', 'x'], lat),
                        'longitude': (['y', 'x'], lon)
                    },
                    attrs=attrs,
                    name=short_name
                )
                datasets.append(da)

        ds_merged = xr.merge(datasets, compat='override')

        # Calculate wind speed and direction (from 10u and 10v), with attrs
        if '10u' in ds_merged and '10v' in ds_merged:
            ds_merged['wind'] = np.sqrt(ds_merged['10u']**2 + ds_merged['10v']**2)
            ds_merged['wind'].attrs.update({
                'long_name': '10 metre wind speed calculated from u and v wind components',
                'units': 'm s**-1',
                'GRIB_shortName': '10m wind',
                'standard_name': 'wind speed',
                'GRIB_name': '10 metre wind speed',
                'GRIB_cfName': 'wind_speed',
                'GRIB_cfVarName': 'wind10'
            })

            # Wind direction: atan2(v, u) gives direction in degrees from east (positive x), convert to 0-360
            wind_dir_rad = np.arctan2(ds_merged['10v'], ds_merged['10u'])
            ds_merged['wind_dir'] = (wind_dir_rad * 180 / np.pi + 360) % 360
            ds_merged['wind_dir'].attrs.update({
                'long_name': '10 metre wind direction (from which wind blows)',
                'units': 'degrees',
                'GRIB_shortName': '10m wind dir',
                'standard_name': 'wind_from_direction',
                'GRIB_name': '10 metre wind direction',
                'GRIB_cfName': 'wind_from_direction',
                'GRIB_cfVarName': 'winddir10'
            })

        # Rename variables (as in old code) - attrs should be preserved
        ds_merged = ds_merged.rename({
            't': 'temp_surface',
            'sp': 'pressure',
            '2t': 'temp',
            '2r': 'rh',
            'sdwe': 'swe',
            'sde': 'snowdepth',
            'sdswrf': 'swrad',
            'sdlwrf': 'lwrad',
            'tp': 'precip_total',
            'prate': 'precip_rate'
        })

        # Drop unnecessary variables if any
        drop_vars = [var for var in ['unknown'] if var in ds_merged]
        ds_merged = ds_merged.drop_vars(drop_vars, errors='ignore')

        # Assign time coordinates (mimic old code: time as valid_time, add step)
        step = pd.Timedelta(hours=forecast_step)
        ds_merged = ds_merged.assign_coords({
            'time': valid_time,
            'step': step,
            'valid_time': valid_time
        })

        return ds_merged

    except Exception as e:
        print(f"⚠️ Error processing {grib_path}: {e}")
        return None

BASE = Path('/hdd/snow_hydrology/hrrrak/icefield_domain')


def _process_day(folder):
    datasets = []
    for path in sorted(Path(folder).glob('*.grib2')):
        ds = process_grib_file(str(path))
        if ds is None:
            raise RuntimeError(f'GRIB decoding failed: {path}')
        datasets.append(ds)
    if not datasets:
        raise ValueError(f'No GRIB files in {folder}')
    return xr.concat(datasets, dim='time').sortby('time')


def process_water_year_2026(base=BASE, workers=8):
    """Create new annual files from available WY2026 initialization folders."""
    base = Path(base)
    folder = base / 'f567/WY2026'
    output = base / 'netcdf'
    raw_path = output / 'hrrrak_merged_grib_f567_WY2026_raw.nc'
    utm_path = output / 'hrrrak_merged_grib_f567_WY2026_utm.nc'
    for path in (raw_path, utm_path):
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite {path}')
    days = sorted(p for p in folder.glob('hrrr.*') if p.is_dir())
    expected = pd.date_range('2025-10-01', '2026-09-30', freq='D')
    expected_names = {f'hrrr.{d:%Y%m%d}' for d in expected}
    if not days or any(d.name not in expected_names for d in days):
        raise ValueError('Missing source directory or unexpected WY2026 date folders')
    missing_days = sorted(expected_names - {p.name for p in days})
    print(f'WY2026: {len(days)} initialization days; missing: {missing_days}', flush=True)
    if missing_days:
        warnings.warn(f'Incomplete WY2026 source coverage: {missing_days}')
    batches = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        for i, ds in enumerate(executor.map(_process_day, days), 1):
            batches.append(ds)
            if i % 30 == 0 or i == len(days):
                print(f'Processed {i}/{len(days)} days', flush=True)
    raw = xr.concat(batches, dim='time').sortby('time')
    del batches
    times = raw.indexes['time']
    if not times.is_unique or not times.is_monotonic_increasing:
        raise ValueError('Duplicate or unsorted valid times')
    # Historical annual files use initialization dates, with valid time +5 hours.
    expected_times = pd.date_range('2025-10-01 05:00', '2026-10-01 04:00', freq='h')
    missing_times = expected_times.difference(times)
    if len(times.difference(expected_times)):
        raise ValueError('Valid times outside the historical annual convention')
    print(f'{len(times)} hours; {len(missing_times)} missing; '
          f'{times[0]} through {times[-1]} UTC', flush=True)
    raw.attrs.update(source_water_year=2026,
                     missing_initialization_days=', '.join(missing_days),
                     missing_valid_hours=len(missing_times))
    # Compare the actual GRIB grid before applying the historical approximation.
    with xr.open_dataset(output / 'hrrrak_merged_grib_f567_WY2025_raw.nc') as reference:
        for name in ('latitude', 'longitude'):
            np.testing.assert_allclose(raw[name], reference[name], rtol=0, atol=1e-8)
        if set(raw.data_vars) != set(reference.data_vars):
            raise ValueError('WY2026 variables differ from the WY2025 schema')
    # Preserve the same 1D lon/lat approximation used by previous annual files.
    spatial = raw.copy(deep=False)
    spatial.rio.write_crs('EPSG:4326', inplace=True)
    spatial = spatial.drop_vars(['x', 'y']).rename({'longitude': 'x', 'latitude': 'y'})
    x = spatial['x'].isel(y=0).values
    y = spatial['y'].isel(x=0).values
    spatial = spatial.drop_vars(['x', 'y']).assign_coords(x=x, y=y)
    spatial = spatial.rio.set_spatial_dims(x_dim='x', y_dim='y')
    utm = spatial.rio.reproject('EPSG:32608')
    with xr.open_dataset(output / 'hrrrak_merged_grib_f567_WY2025_utm.nc') as reference:
        np.testing.assert_array_equal(utm.x, reference.x)
        np.testing.assert_array_equal(utm.y, reference.y)
    # Save the raw data without CRS, as in the previous annual files.
    raw = raw.drop_vars('spatial_ref', errors='ignore')
    for ds, path in ((raw, raw_path), (utm, utm_path)):
        partial = path.with_suffix('.partial.nc')
        if partial.exists():
            raise FileExistsError(partial)
        ds.to_netcdf(partial, engine='scipy', format='NETCDF3_64BIT')
        partial.rename(path)
        print(f'Saved {path}', flush=True)
    return utm


if __name__ == '__main__':
    process_water_year_2026()
