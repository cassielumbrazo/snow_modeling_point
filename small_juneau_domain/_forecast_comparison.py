"""Compare processed native-grid HRRR-AK forecast mosaics at a selected point."""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import xarray as xr

DATA_ROOT = Path('/hdd/snow_hydrology/hrrrak/small_juneau_domain/netcdf')
OBS_CSV = Path('/hdd/snow_hydrology/met_station/ppsa2/PPSA2.2026-03-20.csv')
OPTIONS = ('f123', 'f567', 'f6to11', 'f6to29')
EXPECTED_LEADS = {'f123':{1,2,3}, 'f567':{5,6,7}, 'f678':{6,7,8},
                  'f6to11':set(range(6,12)), 'f6to29':set(range(6,30))}
LABELS = {'TA':'Air temperature (°C)', 'RH':'Relative humidity (%)',
          'PSUM':'PRATE × 3600 (mm per hour)', 'VW':'Wind speed (m/s)',
          'DW':'Wind direction (grid-relative °)', 'ISWR':'Incoming shortwave (W/m²)',
          'ILWR':'Incoming longwave (W/m²)', 'PS':'Surface pressure (hPa)'}


def discover(root=DATA_ROOT):
    """Select native grids, preferring later full versions over test1 subsets."""
    groups={}
    for p in sorted(Path(root).glob('hrrrak_merged_grib_*.nc')):
        m=re.fullmatch(r'hrrrak_merged_grib_(f123|f567|f678|f6to11|f6to29)_(WY\d{4})(_test1)?\.nc',p.name)
        if m: groups.setdefault((m[1],m[2]),[]).append(p)
    selected={};excluded=[]
    for key,paths in groups.items():
        chosen=next((p for p in paths if '_test1' not in p.stem),paths[0])
        selected[key]=chosen
        excluded.extend({'option':key[0],'period':key[1],'selected':str(chosen),
                         'excluded_older_version':str(p)} for p in paths if p!=chosen)
    return selected,pd.DataFrame(excluded)


def distance_km(lat,lon,target_lat,target_lon):
    lat,lon=np.deg2rad(lat),np.deg2rad(lon)
    tlat,tlon=np.deg2rad(target_lat),np.deg2rad(target_lon)
    a=np.sin((lat-tlat)/2)**2+np.cos(lat)*np.cos(tlat)*np.sin((lon-tlon)/2)**2
    return 6371*2*np.arcsin(np.sqrt(np.clip(a,0,1)))


def read_point(path,latitude=58.262,longitude=-134.517,site_elevation=670,lapse_rate=.006):
    with xr.open_dataset(path) as ds:
        lon=(ds.longitude.values+180)%360-180
        distances=distance_km(ds.latitude.values,lon,latitude,longitude)
        y,x=np.unravel_index(np.nanargmin(distances),distances.shape)
        names=['temp','rh','precip_rate','u10','v10','swrad','lwrad','orog',
               'pressure' if 'pressure' in ds else 'sp']
        point=ds[names].isel(y=int(y),x=int(x)).load()
        def check(v,unit):
            if point[v].attrs.get('units')!=unit:raise ValueError(f'Review {v} units in {path}')
        for v,u in [('temp','K'),('rh','%'),('precip_rate','kg m**-2 s**-1'),
                    ('u10','m s**-1'),('v10','m s**-1'),('swrad','W m**-2'),
                    ('lwrad','W m**-2'),(names[-1],'Pa')]:check(v,u)
        times=pd.DatetimeIndex(ds.valid_time.values)
        if not times.equals(pd.DatetimeIndex(ds.time.values)):
            raise ValueError(f'Time must be valid time: {path}')
        if times.has_duplicates or not times.is_monotonic_increasing:
            raise ValueError(f'Review duplicate/unsorted valid times: {path}')
        lead=np.asarray(ds.step.values/np.timedelta64(1,'h'),dtype=float)
        init=times-pd.to_timedelta(lead,unit='h')
        elevation=float(point.orog.isel(time=0))
        frame=pd.DataFrame({
            'TA':point.temp.values-273.15,'RH':point.rh.values,
            'PSUM':point.precip_rate.values*3600,
            'VW':np.hypot(point.u10.values,point.v10.values),
            # No grid-to-earth rotation is applied to the native components.
            'DW':(270-np.degrees(np.arctan2(point.v10.values,point.u10.values)))%360,
            'ISWR':point.swrad.values,'ILWR':point.lwrad.values,
            'PS':point[names[-1]].values/100,'lead_h':lead},index=times)
        frame['TA_lapse']=frame.TA-lapse_rate*(site_elevation-elevation)
        frame=frame.replace([np.inf,-np.inf],np.nan)
        # Retain raw valid values; mask impossible RH and negative precipitation.
        frame['RH']=frame.RH.where(frame.RH.between(0,100))
        frame['PSUM']=frame.PSUM.where(frame.PSUM.ge(0))
        frame['DW']=frame.DW.where(frame.VW.gt(.1))
        index=pd.date_range(times.min(),times.max(),freq='h')
        audit=dict(path=str(path),rows=len(times),start_UTC=times.min(),end_UTC=times.max(),
                   missing_hours=len(index.difference(times)),grid_y=int(y),grid_x=int(x),
                   grid_latitude=float(ds.latitude[y,x]),grid_longitude=float(lon[y,x]),
                   distance_km=float(distances[y,x]),grid_elevation_m=elevation,
                   site_elevation_m=site_elevation,TA_correction_C=-lapse_rate*(site_elevation-elevation),
                   actual_leads_h=','.join(str(int(v)) for v in sorted(set(lead))),
                   initialization_hours_UTC=','.join(str(v) for v in sorted(set(init.hour))))
    return frame.reindex(index),audit


def load_all(root=DATA_ROOT,**point_settings):
    paths,excluded=discover(root);frames={};rows=[]
    for (option,period),path in paths.items():
        frame,audit=read_point(path,**point_settings)
        actual=set(frame.lead_h.dropna().astype(int))
        audit.update(option=option,period=period,lead_label_matches=actual==EXPECTED_LEADS[option])
        frames[(period,option)]=frame;rows.append(audit)
    # Check older f567 subset at the selected point rather than plotting it twice.
    if not excluded.empty:
        matches=[]
        for row in excluded.to_dict('records'):
            older,_=read_point(row['excluded_older_version'],**point_settings)
            current=frames[(row['period'],row['option'])].reindex(older.index)
            matches.append(bool(np.allclose(current,older,equal_nan=True)))
        excluded['selected_point_values_match']=matches
    return frames,pd.DataFrame(rows),excluded


def load_observations(path=OBS_CSV):
    """Use raw cumulative gauge differences, retaining gaps/resets as missing."""
    columns={'air_temp_set_1':'TA','relative_humidity_set_1':'RH',
             'precip_accum_set_1':'gauge_mm'}
    raw=pd.read_csv(path,skiprows=10,low_memory=False,usecols=['Date_Time',*columns])
    # CSV unit row is explicit: Celsius, %, and Millimeters.
    units=raw.iloc[0]
    if [units[k] for k in columns]!=['Celsius','%','Millimeters']:
        raise ValueError('Review PPSA CSV units')
    raw.index=pd.to_datetime(raw.pop('Date_Time'),utc=True,errors='coerce').dt.tz_convert(None)
    raw=raw.loc[raw.index.notna()].rename(columns=columns)
    raw=raw.apply(pd.to_numeric,errors='coerce').sort_index()
    duplicate_count=int(raw.index.duplicated().sum())
    raw=raw.loc[~raw.index.duplicated(keep='first')]
    hourly=pd.date_range(raw.index.min().ceil('h'),raw.index.max().floor('h'),freq='h')
    raw=raw.reindex(hourly)  # Exact hourly timestamps; no interpolation/forward fill.
    raw['TA']=raw.TA.where(raw.TA.between(-50,100))
    raw['RH']=raw.RH.where(raw.RH.between(0,100))
    gauge=raw.gauge_mm.where(raw.gauge_mm.between(0,40000))
    increments=gauge.diff()  # Reindexing first prevents differences across gaps.
    raw['PSUM']=increments.where(increments.between(0,40))
    return raw[['TA','RH','PSUM']],dict(source=str(path),duplicates_kept_first=duplicate_count,
        precipitation='Difference of consecutive valid hourly cumulative gauge readings; 0–40 mm',
        timestamps='UTC; gauge increment is for the hour ending at timestamp')


def common_table(frames,period,variable,options=OPTIONS,observations=None):
    table=pd.concat({o:frames[(period,o)][variable] for o in options},axis=1)
    if observations is not None:
        obsvar='TA' if variable=='TA_lapse' else variable
        table['PPSA']=observations[obsvar].reindex(table.index)
    return table


def difference(a,b,variable):
    delta=a-b
    return (delta+180)%360-180 if variable=='DW' else delta


def metrics(table,reference,variable):
    """Every option is scored on the identical complete-case timestamps."""
    matched=table.dropna();rows=[]
    for name in table:
        if name==reference:continue
        delta=difference(matched[name],matched[reference],variable)
        rows.append(dict(option=name,n_hours=len(matched),bias=delta.mean(),
                         MAE=delta.abs().mean(),RMSE=np.sqrt((delta**2).mean()),
                         reference_total_mm=matched[reference].sum() if variable=='PSUM' else np.nan,
                         option_total_mm=matched[name].sum() if variable=='PSUM' else np.nan))
    return pd.DataFrame(rows)


def strict_daily(series,operation='mean'):
    """Show a daily value only if all 24 hourly values exist (UTC days)."""
    daily=series.resample('D')
    values=daily.sum(min_count=24) if operation=='sum' else daily.mean().where(daily.count()==24)
    return values
