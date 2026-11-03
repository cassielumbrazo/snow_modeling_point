"""Create the extended series from annual files, preserving older products."""
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

BASE = Path('/hdd/snow_hydrology/hrrrak/icefield_domain/netcdf')


def merge_water_years(base=BASE):
    base = Path(base)
    destination = base / 'hrrrak_f567_WY2020-WY2026_utm.nc'
    partial = destination.with_suffix('.partial.nc')
    for path in (destination, partial):
        if path.exists():
            raise FileExistsError(f'Refusing to overwrite {path}')
    paths = [base / f'hrrrak_merged_grib_f567_WY{year}_utm.nc'
             for year in range(2020, 2027)]
    sources = []
    try:
        for path in paths:
            ds = xr.open_dataset(path, chunks={'time': 168})
            sources.append(ds)
            reference = sources[0]
            for coord in ('x', 'y'):
                np.testing.assert_array_equal(ds[coord], reference[coord])
            if ds.spatial_ref.attrs['crs_wkt'] != reference.spatial_ref.attrs['crs_wkt']:
                raise ValueError(f'CRS mismatch: {path}')
            for name in set(ds.data_vars) & set(reference.data_vars):
                if ds[name].dims != reference[name].dims:
                    raise ValueError(f'Dimension mismatch: {path}: {name}')
                if ds[name].attrs.get('units') != reference[name].attrs.get('units'):
                    raise ValueError(f'Units mismatch: {path}: {name}')
            times = ds.indexes['time']
            if not times.is_unique or not times.is_monotonic_increasing:
                raise ValueError(f'Duplicate or unsorted times: {path}')
            print(f'{path.name}: {len(times)} hours, {times[0]} to {times[-1]}', flush=True)
        merged = xr.concat(sources, dim='time', data_vars='minimal',
                           coords='minimal', compat='override', join='exact')
        times = merged.indexes['time']
        if not times.is_unique or not times.is_monotonic_increasing:
            raise ValueError('Annual files overlap or are out of order')
        expected = pd.date_range('2019-10-01 05:00', '2026-10-01 04:00', freq='h')
        missing = expected.difference(times)
        if len(times.difference(expected)):
            raise ValueError('Unexpected time coverage')
        print(f'Merged: {len(times)} hours; {len(missing)} missing hours', flush=True)
        merged.attrs.update(water_years='WY2020-WY2026',
                            missing_valid_hours=len(missing),
                            wy2026_missing_initialization_days=sources[-1].attrs.get(
                                'missing_initialization_days', ''))
        # SciPy buffers this ~24 GB file in memory, as in the original notebook.
        # This avoids costly classic-NetCDF metadata redefinitions in netCDF4.
        merged.to_netcdf(partial, engine='scipy', format='NETCDF3_64BIT')
        with xr.open_dataset(partial) as check:
            np.testing.assert_array_equal(check.time, merged.time)
            if set(check.data_vars) != set(merged.data_vars):
                raise ValueError('Output variables do not match')
        partial.rename(destination)
        print(f'Saved {destination}', flush=True)
        return destination
    finally:
        for ds in sources:
            ds.close()


if __name__ == '__main__':
    merge_water_years()
