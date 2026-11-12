"""Extract snow-only bulk metrics from soil-enabled SNOWPACK PRO files."""
from pathlib import Path
import numpy as np
import pandas as pd


def nearest_profiles(path, target_times, tolerance='24h'):
    """Stream a large PRO file once, retaining only the nearest target profiles.

    Keep the original Table 2 rule: nearest profile within tolerance; when
    two profiles are equally close, choose the later timestamp.
    """
    targets=pd.DatetimeIndex(pd.to_datetime(list(target_times)))
    tolerance=pd.Timedelta(tolerance)
    best={};current_time=None;current=None;in_data=False

    def save():
        if current is None:return
        for target in targets:
            offset=abs(current_time-target)
            if offset>tolerance:continue
            previous=best.get(target)
            if previous is None or offset<=previous[0]:
                best[target]=(offset,current_time,current)

    with Path(path).open(errors='replace') as stream:
        for line in stream:
            line=line.strip()
            if line=='[DATA]':in_data=True;continue
            if not in_data:continue
            if line.startswith('0500,'):
                save()
                current_time=pd.to_datetime(line.split(',')[1],format='%d.%m.%Y %H:%M:%S')
                current={} if any(abs(current_time-t)<=tolerance for t in targets) else None
            elif current is not None and line[:4] in {'0501','0502','0503'}:
                parts=line.split(',');values=np.array([float(v) for v in parts[2:] if v!=''])
                if len(values)!=int(parts[1]):raise ValueError(f'Invalid {parts[0]} count at {current_time}')
                current[parts[0]]=values
    save()
    missing=targets.difference(pd.DatetimeIndex(best))
    if len(missing):raise ValueError(f'No profiles within {tolerance}: {missing.tolist()}')
    return dict(sorted((v[1],v[2]) for v in best.values()))


def snow_bulk_metrics(profile):
    """Compute HS, SWE, and thickness-weighted density/temperature above ground.

    Soil runs store N+1 boundary heights (0501) and N element density and
    temperature values (0502/0503). Legacy snow-only top-height arrays of
    length N are also supported. Heights are cm relative to the ground.
    """
    heights=np.asarray(profile['0501'],dtype=float)
    density=np.asarray(profile['0502'],dtype=float)
    temperature=np.asarray(profile['0503'],dtype=float)
    if len(density)!=len(temperature):raise ValueError('Density/temperature element counts differ')
    if len(heights)==len(density)+1:
        bottom,top=heights[:-1],heights[1:]
    elif len(heights)==len(density):
        bottom,top=np.r_[0.,heights[:-1]],heights
    else:raise ValueError('Profile height boundaries do not match element counts')
    dz=top-bottom
    snow=(bottom>=0)&(top>0)&(dz>0)
    if not snow.any():
        return dict(HS_cm=0.,bulk_density_kg_m3=np.nan,mean_temperature_C=np.nan,SWE_mm=0.)
    if not (np.isfinite(dz[snow]).all() and np.isfinite(density[snow]).all()
            and np.isfinite(temperature[snow]).all()):
        raise ValueError('Nonfinite snow-layer properties')
    dz=dz[snow];density=density[snow];temperature=temperature[snow]
    hs=dz.sum();swe=np.sum(density*dz/100.)
    return dict(HS_cm=hs,bulk_density_kg_m3=swe/(hs/100.),
                mean_temperature_C=np.average(temperature,weights=dz),SWE_mm=swe)
