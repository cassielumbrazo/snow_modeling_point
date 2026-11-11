"""Prepare and compare soil-enabled 1.2°C and 0.7°C precipitation thresholds."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import ast
import configparser
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd
import xarray as xr

MODEL_ROOT = Path(os.environ.get('SNOWPACK_SITES','/home/cassie/python/models/run_snowpack/sites'))
EXPERIMENT = 'soil_thresh07'
FORCINGS = ('hrrrak_lapserate','met_hrrrak_lapserate')
PERIODS = {
    'ppsa': ('WY2020-WY2025','WY2020-WY2025'),
    'tram': ('WY2020-WY2025','WY2023-WY2025'),
    'heen': ('WY2020-WY2025','WY2020-WY2022'),
}
OBSERVATIONS = {
    'ppsa':'/hdd/snow_hydrology/met_station/ppsa2/pppsa_met_station_data_synoptic_2026-03-20',
    'tram':'/hdd/snow_hydrology/met_station/tram/tram_met_station_data_synoptic_2026-03-20',
    'heen':'/hdd/snow_hydrology/met_station/snotel/heenlatinee/heen_met_2016_2026_cleaned_v1.nc',
}


def ini(path):
    result=configparser.ConfigParser(interpolation=None,delimiters=('=',),inline_comment_prefixes=(';','#'))
    result.optionxform=str
    if not result.read(path): raise FileNotFoundError(path)
    return result


def header_and_first(path):
    header={}
    with Path(path).open() as stream:
        for line in stream:
            if line.strip()=='[DATA]': break
            if '=' in line:
                k,v=line.split('=',1);header[k.strip()]=v.strip()
        else: raise ValueError(f'No SMET data section: {path}')
        first=next((line.split() for line in stream if line.strip()),[])
    return header,first


def last_timestamp(path):
    path=Path(path)
    with path.open('rb') as stream:
        stream.seek(-min(path.stat().st_size,16384),2)
        return pd.Timestamp(stream.read().decode().splitlines()[-1].split()[0])


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()


def run_inventory(root=MODEL_ROOT):
    rows=[]
    for site,periods in PERIODS.items():
        for forcing,period in zip(FORCINGS,periods):
            stem=f'{forcing}_{site}_{period}'
            base=Path(root)/site
            control_config=base/'config'/f'{forcing}_soil_{site}_{period}.ini'
            config=ini(control_config)
            forcing_path=(control_config.parent/config['Input']['METEOPATH']/config['Input']['STATION1']).resolve()
            profile=(control_config.parent/config['Input']['SNOWPATH']/config['Input']['SNOWFILE1']).resolve()
            control=base/'output'/f'{stem}_soil.smet'
            h,first=header_and_first(control)
            fh,_=header_and_first(forcing_path)
            ph,_=header_and_first(profile)
            if any(f in fh['fields'].split() for f in ['PSUM_PH','PSUM_S','PSUM_L']):
                raise ValueError(f'Forcing contains preassigned precipitation phase: {forcing_path}')
            if config['Snowpack']['SNP_SOIL'].lower()!='true' or int(ph['nSoilLayerData'])!=28:
                raise ValueError('Expected the established soil-enabled profile')
            rows.append(dict(site=site,forcing=forcing,period=period,stem=stem,
                control_config=str(control_config),control_output=str(control),
                config=str(base/'config'/f'{forcing}_{EXPERIMENT}_{site}_{period}.ini'),
                output=str(base/'output'/f'{stem}_{EXPERIMENT}.smet'),
                start_UTC=pd.Timestamp(first[0]).isoformat(),end_UTC=last_timestamp(control).isoformat(),
                profile_date=ph['ProfileDate'],forcing_path=str(forcing_path),profile_path=str(profile),
                forcing_sha256=sha256(forcing_path),profile_sha256=sha256(profile),
                control_config_sha256=sha256(control_config),control_output_sha256=sha256(control),
                control_threshold_K=float(config['Input']['PSUM_PH::PRECSPLITTING::snow']),
                sensitivity_threshold_K=273.85,experiment=EXPERIMENT))
    return rows


def prepare(destination_root=MODEL_ROOT,source_root=MODEL_ROOT):
    rows=run_inventory(source_root)
    for site in PERIODS:
        manifest=Path(destination_root)/site/'soil_thresh07_runs.json'
        expected=[row for row in rows if row['site']==site]
        if manifest.exists() and json.loads(manifest.read_text())!=expected:
            raise FileExistsError(f'Existing sensitivity provenance differs; use a separate destination: {manifest}')
    for row in rows:
        config=ini(row['control_config'])
        for key in list(config['Input']):
            if key.upper().startswith('PSUM_PH::'): del config['Input'][key]
        config['Generators'].update({'PSUM_PH::generator1':'PRECSPLITTING',
            'PSUM_PH::arg1::type':'THRESH','PSUM_PH::arg1::snow':'273.85'})
        config['Output']['EXPERIMENT']=EXPERIMENT
        destination=Path(destination_root)/row['site']/'config'/Path(row['config']).name
        destination.parent.mkdir(parents=True,exist_ok=True)
        from io import StringIO
        text=StringIO();config.write(text)
        if destination.exists() and destination.read_text()!=text.getvalue():
            raise FileExistsError(f'Refusing to replace a different configuration: {destination}')
        destination.write_text(text.getvalue())
    for site in PERIODS:
        base=Path(destination_root)/site
        (base/'output').mkdir(exist_ok=True)
        manifest=base/'soil_thresh07_runs.json'
        manifest.write_text(json.dumps([r for r in rows if r['site']==site],indent=2)+'\n')
        script=base/'run_soil_thresh07.sh'
        commands=['#!/usr/bin/env bash','set -euo pipefail','cd -- "$(dirname -- "${BASH_SOURCE[0]}")/config"',
                  'SNOWPACK_BIN="${SNOWPACK_BIN:-snowpack}"']
        for r in rows:
            if r['site']!=site:continue
            prefix=f"../output/{r['stem']}_{EXPERIMENT}"
            commands += [f'output="{prefix}"',
                'if compgen -G "${output}.*" > /dev/null; then',
                '    echo "Refusing to overwrite existing soil_thresh07 products: ${output}" >&2',
                '    exit 1','fi',
                f'"$SNOWPACK_BIN" -c "{Path(r["config"]).name}" -e {r["end_UTC"]} > "${{output}}.log" 2>&1',
                'grep -q "FINISHED running" "${output}.log" || { tail -n 25 "${output}.log" >&2; exit 1; }']
        script.write_text('\n'.join(commands)+'\n');script.chmod(0o755)
    return rows


def read_output(path):
    header,_=header_and_first(path)
    fields=header['fields'].split()
    columns=['timestamp','HS_mod','SWE','MS_Snow','MS_Rain']
    # Raw model depths are cm; SWE and hourly precipitation masses are kg/m².
    with Path(path).open() as stream:
        for line in stream:
            if line.strip()=='[DATA]': break
        frame=pd.read_csv(stream,sep=r'\s+',names=fields,usecols=columns)
    frame.index=pd.DatetimeIndex(pd.to_datetime(frame.pop('timestamp')))
    frame=frame.replace(float(header['nodata']),np.nan)
    multipliers=header['units_multiplier'].split();units=header['plot_unit'].split()
    if float(header['tz'])!=0 or float(multipliers[fields.index('HS_mod')])!=.01 or units[fields.index('HS_mod')]!='m':
        raise ValueError(f'Review snow-depth units: {path}')
    if units[fields.index('SWE')]!='kg/m2': raise ValueError(f'Review SWE units: {path}')
    offsets=header['units_offset'].split()
    for field in ['SWE','MS_Snow','MS_Rain']:
        if float(multipliers[fields.index(field)])!=1 or float(offsets[fields.index(field)])!=0:
            raise ValueError(f'Review native mass units for {field}: {path}')
    for field in ['MS_Snow','MS_Rain']:
        if units[fields.index(field)]!='kg/m2/h': raise ValueError(f'Review hourly precipitation units: {path}')
    if not frame.index.is_unique or not frame.index.is_monotonic_increasing or frame.isna().any().any():
        raise ValueError(f'Invalid modeled snow/precipitation output: {path}')
    return frame.rename(columns={'HS_mod':'HS_cm','SWE':'SWE_mm','MS_Snow':'snowfall_mm','MS_Rain':'rainfall_mm'})


def run_one(row):
    path=Path(row['output']);prefix=path.with_suffix('')
    if list(path.parent.glob(prefix.name+'.*')):raise FileExistsError(prefix)
    log=prefix.with_suffix('.log')
    binary=os.environ.get('SNOWPACK_BIN','snowpack')
    command=[binary,'-c',Path(row['config']).name,'-e',row['end_UTC']]
    with log.open('w') as stream:
        process=subprocess.run(command,cwd=Path(row['config']).parent,stdout=stream,stderr=subprocess.STDOUT)
    result=dict(site=row['site'],forcing=row['forcing'],command=command,returncode=process.returncode,
                log=str(log),finished='FINISHED running' in log.read_text(errors='replace'),complete=False)
    if result['finished'] and process.returncode==0 and path.exists():
        data=read_output(path)
        expected=pd.date_range(row['start_UTC'],row['end_UTC'],freq='h')
        result.update(rows=len(data),complete=data.index.equals(expected))
    result['inputs_preserved']=all(sha256(row[key])==row[key.replace('_path','_sha256')] for key in ['forcing_path','profile_path'])
    result['control_preserved']=(sha256(row['control_config'])==row['control_config_sha256'] and
                                 sha256(row['control_output'])==row['control_output_sha256'])
    prefix.with_suffix('.status.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return result


def run_all(root=MODEL_ROOT,workers=6):
    rows=[r for site in PERIODS for r in json.loads((Path(root)/site/'soil_thresh07_runs.json').read_text())]
    with ThreadPoolExecutor(max_workers=workers) as pool: results=list(pool.map(run_one,rows))
    if not all(r['complete'] and r['inputs_preserved'] and r['control_preserved'] for r in results):
        raise RuntimeError('Some sensitivity runs failed verification; inspect their logs/status JSON.')
    return results


def load_pairs(root=MODEL_ROOT):
    rows=[r for site in PERIODS for r in json.loads((Path(root)/site/'soil_thresh07_runs.json').read_text())]
    pairs={};audit=[]
    for row in rows:
        for path_key,hash_key in [('forcing_path','forcing_sha256'),('profile_path','profile_sha256'),
                                  ('control_config','control_config_sha256'),('control_output','control_output_sha256')]:
            if sha256(row[path_key])!=row[hash_key]:
                raise ValueError(f'Sensitivity source/control changed since preparation: {row[path_key]}')
        baseline=read_output(row['control_output']);candidate=read_output(row['output'])
        expected=pd.date_range(row['start_UTC'],row['end_UTC'],freq='h')
        if not baseline.index.equals(expected) or not candidate.index.equals(expected):
            raise ValueError(f'Paired runs must cover the identical hourly period: {row["stem"]}')
        pair=baseline.add_suffix('_soil').join(candidate.add_suffix('_soil_thresh07'),how='inner')
        for variable in ['HS_cm','SWE_mm','snowfall_mm','rainfall_mm']:
            pair[f'delta_{variable}']=pair[f'{variable}_soil_thresh07']-pair[f'{variable}_soil']
        pairs[(row['site'],row['forcing'])]=pair
        audit.append({k:row[k] for k in ['site','forcing','period','start_UTC','end_UTC','control_threshold_K','sensitivity_threshold_K']})
    return pairs,pd.DataFrame(audit)


def observations(site):
    with xr.open_dataset(OBSERVATIONS[site]) as dataset:
        series=dataset.hs.to_series();unit=dataset.hs.attrs.get('units','').lower()
    if unit in ['m','meter','meters','metre','metres']:series*=100
    elif unit not in ['cm','centimeter','centimeters','centimetre','centimetres']:raise ValueError(unit)
    series.index=pd.DatetimeIndex(pd.to_datetime(series.index,utc=True)).tz_convert(None)
    series=series.groupby(level=0).mean().sort_index()
    return series.where(np.isfinite(series)&series.ge(0))


def existing_melt_rule():
    """Reuse the established step-5 snow-free thresholds and confirmation rule."""
    source=Path(__file__).with_name('5_read_snowpack_output_compare_all_sites_lapserate_soil_figure.ipynb')
    notebook=json.loads(source.read_text())
    names={'SNOW_FREE_CM','SWE_FREE_KG_M2','SNOW_FREE_DAYS','MIN_VALID_HOURS_PER_DAY','MIN_SEASON_PEAK_CM'}
    namespace={'pd':pd,'np':np}
    for cell in notebook['cells']:
        if cell['cell_type']!='code':continue
        for node in ast.parse(''.join(cell['source'])).body:
            if (isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets)) or (isinstance(node,ast.FunctionDef) and node.name=='melt_out'):
                exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    return namespace['melt_out'],{name:namespace[name] for name in names}


def seasonal_summary(pairs,first_water_years=None):
    """Summarize selected seasons; pass original first years after cropping runs."""
    melt_out,rules=existing_melt_rule()
    observed={site:observations(site) for site in PERIODS}
    rows=[]
    for (site,forcing),frame in pairs.items():
        years=frame.index.year+(frame.index.month>=10).astype(int)
        first=int(years.min()) if first_water_years is None else first_water_years[(site,forcing)]
        for wy,season in frame.groupby(years):
            obs=observed[site].reindex(season.index)
            valid=obs.notna()
            expected=pd.date_range(pd.Timestamp(int(wy)-1,10,1),pd.Timestamp(int(wy),10,1),freq='h',inclusive='left')
            row=dict(site=site,forcing=forcing,water_year=int(wy),initialization_sensitive=int(wy)==first,
                     complete_water_year=season.index.equals(expected),paired_hours=len(season),obs_hours=int(valid.sum()),
                     mean_delta_HS_cm=season.delta_HS_cm.mean(),mean_absolute_delta_HS_cm=season.delta_HS_cm.abs().mean(),
                     max_absolute_delta_HS_cm=season.delta_HS_cm.abs().max(),**rules)
            for experiment in ['soil','soil_thresh07']:
                hs=season[f'HS_cm_{experiment}'];swe=season[f'SWE_mm_{experiment}']
                snow=season[f'snowfall_mm_{experiment}'].sum();rain=season[f'rainfall_mm_{experiment}'].sum()
                row[f'peak_HS_{experiment}_cm']=hs.max()
                row[f'peak_SWE_{experiment}_mm']=swe.max()
                row[f'reported_snowfall_{experiment}_mm']=snow
                row[f'reported_rainfall_{experiment}_mm']=rain
                row[f'reported_snow_fraction_{experiment}']=snow/(snow+rain) if snow+rain>0 else np.nan
                row[f'melt_{experiment}'],row[f'melt_{experiment}_status']=melt_out(hs,swe)
                residual=hs[valid]-obs[valid]
                row[f'MAE_{experiment}_cm']=residual.abs().mean()
                row[f'RMSE_{experiment}_cm']=np.sqrt((residual**2).mean())
                row[f'bias_{experiment}_cm']=residual.mean()
            a,b=row['melt_soil_thresh07'],row['melt_soil']
            row['melt_shift_days']=(a-b).days if pd.notna(a) and pd.notna(b) else np.nan
            row['peak_HS_change_cm']=row['peak_HS_soil_thresh07_cm']-row['peak_HS_soil_cm']
            row['peak_SWE_change_mm']=row['peak_SWE_soil_thresh07_mm']-row['peak_SWE_soil_mm']
            row['MAE_change_cm']=row['MAE_soil_thresh07_cm']-row['MAE_soil_cm']
            row['RMSE_change_cm']=row['RMSE_soil_thresh07_cm']-row['RMSE_soil_cm']
            row['reported_snowfall_change_mm']=row['reported_snowfall_soil_thresh07_mm']-row['reported_snowfall_soil_mm']
            rows.append(row)
    return pd.DataFrame(rows),observed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--model-root',type=Path,default=MODEL_ROOT)
    parser.add_argument('--destination-root',type=Path,default=MODEL_ROOT)
    parser.add_argument('--workers',type=int,default=6)
    args=parser.parse_args()
    if args.action=='prepare':
        for row in prepare(args.destination_root,args.model_root):print(json.dumps(row),flush=True)
    else:run_all(args.model_root,args.workers)
