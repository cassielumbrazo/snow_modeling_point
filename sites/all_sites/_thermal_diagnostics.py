from pathlib import Path
import numpy as np
import pandas as pd
from datetime import datetime
import json

# Installed SNOWPACK 3.7.0 Constants.h (SI).
RHO_I, RHO_W, RHO_A = 917., 1000., 1.1
CP_I, CP_W, CP_A = 2100., 4190., 1004.67
LF = 334000.
SOIL_DEPTHS = (0.1,0.5,1.,5.)
PROFILE_EDGES=np.linspace(0,1,41)


def iter_profiles(path, codes):
    """Stream hourly PRO records; retain missing values and original timestamps."""
    record={};time=None
    with Path(path).open() as stream:
        for line in stream:
            if line.strip()=='[DATA]':break
        else:raise ValueError(f'No data: {path}')
        for line in stream:
            key=line[:4]
            if key=='0500':
                if time is not None:yield time,record
                time=datetime.strptime(line[5:].strip(),'%d.%m.%Y %H:%M:%S');record={}
            elif time is not None and key in codes:
                parts=line.strip().split(',');a=np.asarray(parts[2:],float)
                if len(a)!=int(parts[1]):raise ValueError(f'Invalid array: {path}, {time}, {key}')
                a[a<=-999]=np.nan;record[key]=a
        if time is not None:yield time,record


def soil_storage(record, cosine, mineral_rho=2600., mineral_cp=1000.):
    """Integrate rounded native soil layer states over actual partial thicknesses."""
    z=record['0501']*.01*cosine
    n=int(np.count_nonzero(z < -1e-6));T=record['0503'][:n]
    assert len(z)==len(record['0503'])+1 and abs(z[n])<1e-5
    bottom=-z[:n];top=-z[1:n+1];dz=bottom-top
    theta={key:record[key][:n]/100 for key in ['0506','0515','0516','0519']}
    cv=theta['0506']*RHO_W*CP_W+theta['0515']*RHO_I*CP_I+theta['0516']*RHO_A*CP_A+theta['0519']*mineral_rho*mineral_cp
    result={}
    for depth in SOIL_DEPTHS:
        tag=str(int(depth*100));w=np.maximum(0,np.minimum(bottom,depth)-np.minimum(top,depth))
        C=np.sum(cv*w);E=np.sum(cv*T*w)
        result[f'C_{tag}_Jm2K']=C;result[f'E_{tag}_MJm2']=E/1e6
        result[f'Tmean_{tag}_C']=np.sum(T*w)/np.sum(w)
        result[f'Tcapacity_{tag}_C']=E/C
        result[f'ice_{tag}_kgm2']=np.sum(theta['0515']*RHO_I*w)
    result['soil_solid_mean']=np.sum(theta['0519']*dz)/dz.sum()
    return result


def snow_profiles(path, cosine, soil_layers, cache_dir):
    """Reconstruct compact snow metrics and conservative normalized-height bins."""
    path=Path(path);cache_dir=Path(cache_dir);cache_dir.mkdir(parents=True,exist_ok=True)
    marker=dict(schema=2,path=str(path),size=path.stat().st_size,mtime=path.stat().st_mtime_ns,cosine=cosine,soil_layers=soil_layers)
    meta=cache_dir/(path.stem+'.json');cache=cache_dir/(path.stem+'.npz')
    if meta.exists() and cache.exists() and json.loads(meta.read_text())==marker:
        with np.load(cache) as c: return pd.DataFrame(c['data'],index=pd.DatetimeIndex(c['time']),columns=c['columns'])
    times=[];rows=[]
    cols=['snow_height_normal_m','bulk_mass_T_C','T_above_5cm_C','T_above_10cm_C','T_above_20cm_C','T_above_50cm_C','T_below_surface_10cm_C','cold_deficit_MJm2','snow_mass_kgm2_slope']+[f'fraction_{i:02}' for i in range(40)]
    for time,r in iter_profiles(path,{'0501','0502','0503','0506','0515','0516'}):
        times.append(time);row=np.full(len(cols),np.nan)
        if '0503' not in r or len(r['0503'])<=soil_layers:
            row[0]=0.;rows.append(row);continue
        T=r['0503'][soil_layers:];rho=r['0502'][soil_layers:]
        z=r['0501']*.01*cosine
        if soil_layers:z=z[soil_layers:]
        else:z=np.r_[0.,z]
        assert len(z)==len(T)+1 and abs(z[0])<1e-5 and np.all(np.diff(z)>0)
        dz=np.diff(z);mid=(z[1:]+z[:-1])/2;H=z[-1];mass=rho*dz
        row[0]=H;row[1]=np.sum(mass*T)/np.sum(mass)
        row[2:6]=np.interp([.05,.10,.20,.50],mid,T,left=np.nan,right=np.nan)
        row[6]=np.interp(H-.10,mid,T,left=np.nan,right=np.nan)
        cv=(r['0506'][soil_layers:]*RHO_W*CP_W+r['0515'][soil_layers:]*RHO_I*CP_I+r['0516'][soil_layers:]*RHO_A*CP_A)/100
        row[7]=-np.sum(cv*np.minimum(T,0)*dz)/1e6;row[8]=mass.sum()
        # Integrate each native element exactly within fixed fractions of snow height.
        integrated=np.r_[0.,np.cumsum(T*dz)]
        row[9:]=np.diff(np.interp(PROFILE_EDGES*H,z,integrated))/(np.diff(PROFILE_EDGES)*H)
        rows.append(row)
    frame=pd.DataFrame(rows,index=pd.DatetimeIndex(times,name='time'),columns=cols)
    assert frame.index.is_unique and frame.index.is_monotonic_increasing
    np.savez_compressed(cache,time=frame.index.values,data=frame.values,columns=np.array(cols))
    meta.write_text(json.dumps(marker,indent=2)+'\n')
    return frame
