# _*_ coding: utf-8 _*_

"""
Synoptic analysis or diagnostic maps for numeric weather model.
"""
import numpy as np
from nmc_met_io.retrieve_micaps_server import get_model_grid,get_model_3D_grid
from nmc_met_map.graphics import synoptic_graphics
import nmc_met_map.lib.utility as utl
import metpy.calc as mpcalc
from metpy.units import units
import xarray as xr

def gh_uv_mslp(initial_time=None, fhour=0, day_back=0,model='ECMWF',
    gh_lev='500',uv_lev='850',
    map_ratio=19/9,zoom_ratio=20,cntr_pnt=[102,34],
    south_China_sea=True,area = '全国',city=False,output_dir=None,
    Global=False):

    if(area != '全国'):
        south_China_sea=False

    # micaps data directory
    try:
        data_dir = [utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=gh_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=uv_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=uv_lev),
                    utl.Cassandra_dir(data_type='surface',data_source=model,var_name='PRMSL')]
    except KeyError:
        raise ValueError('Can not find all directories needed')

    # get filename
    if(initial_time != None):
        filename = utl.model_filename(initial_time, fhour)
    else:
        filename=utl.filename_day_back_model(day_back=day_back,fhour=fhour)

    # retrieve data from micaps server
    gh = get_model_grid(data_dir[0], filename=filename)
    if gh is None:
        return
    
    u = get_model_grid(data_dir[1], filename=filename)
    if u is None:
        return
        
    v = get_model_grid(data_dir[2], filename=filename)
    if v is None:
        return
    mslp = get_model_grid(data_dir[3], filename=filename)
    if mslp is None:
        return
    init_time = gh.coords['forecast_reference_time'].values


    # prepare data

    if(area != None):
        cntr_pnt,zoom_ratio=utl.get_map_area(area_name=area)

    map_extent=[0,0,0,0]
    map_extent[0]=cntr_pnt[0]-zoom_ratio*1*map_ratio
    map_extent[1]=cntr_pnt[0]+zoom_ratio*1*map_ratio
    map_extent[2]=cntr_pnt[1]-zoom_ratio*1
    map_extent[3]=cntr_pnt[1]+zoom_ratio*1

    delt_x=(map_extent[1]-map_extent[0])*0.2
    delt_y=(map_extent[3]-map_extent[2])*0.1

#+ to solve the problem of labels on all the contours
    idx_x1 = np.where((gh.coords['lon'].values > map_extent[0]-delt_x) & 
        (gh.coords['lon'].values < map_extent[1]+delt_x))
    idx_y1 = np.where((gh.coords['lat'].values > map_extent[2]-delt_y) & 
        (gh.coords['lat'].values < map_extent[3]+delt_y))

    idx_x2 = np.where((mslp.coords['lon'].values > map_extent[0]-delt_x) & 
        (mslp.coords['lon'].values < map_extent[1]+delt_x))
    idx_y2 = np.where((mslp.coords['lat'].values > map_extent[2]-delt_y) & 
        (mslp.coords['lat'].values < map_extent[3]+delt_y))
#- to solve the problem of labels on all the contours

    gh = {'lon': gh.coords['lon'].values[idx_x1],
             'lat': gh.coords['lat'].values[idx_y1],
             'data': gh['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':gh_lev,
             'model':model,
             'fhour':fhour,
             'init_time':init_time}
    uv = {'lon': u.coords['lon'].values[idx_x1],
             'lat': u.coords['lat'].values[idx_y1],
             'udata': u['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'vdata': v['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':uv_lev}
    mslp = {'lon': mslp.coords['lon'].values[idx_x2],
            'lat': mslp.coords['lat'].values[idx_y2],
             'data': mslp['data'].values[0,idx_y2[0][0]:(idx_y2[0][-1]+1),idx_x2[0][0]:(idx_x2[0][-1]+1)]}

    synoptic_graphics.draw_gh_uv_mslp(
        mslp=mslp, gh=gh, uv=uv,
        map_extent=map_extent, regrid_shape=20,
        city=city,south_China_sea=south_China_sea,
        output_dir=output_dir,Global=Global)

def gh_uv_wsp(initial_time=None, fhour=6, day_back=0,model='ECMWF',
    gh_lev='500',uv_lev='850',
    map_ratio=19/9,zoom_ratio=20,cntr_pnt=[102,34],
    south_China_sea=True,area = '全国',city=False,output_dir=None,
    Global=False):

    """
    Analysis 500hPa geopotential height, 850hPa wind barbs, and
    convective precipitation ratio.

    :param initial_time: initial time, string or datetime ojbect.
                         like '18042008' or datetime(2018, 4, 20, 8).
    :param fhour: forecast hour.
    :param model: model name.
    :param gh_lev: geopotential height level.
    :param uv_lev: wind level
    :param map_extent: [lonmin, lonmax, latmin, latmax],
                       longitude and latitude range.
    :return: None.
    """

    if(area != '全国'):
        south_China_sea=False

    # micaps data directory
    try:
        data_dir = [utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=gh_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=uv_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=uv_lev)]
    except KeyError:
        raise ValueError('Can not find all directories needed')

    # get filename
    if(initial_time != None):
        filename = utl.model_filename(initial_time, fhour)
    else:
        filename=utl.filename_day_back_model(day_back=day_back,fhour=fhour)

    # retrieve data from micaps server
    gh = get_model_grid(data_dir[0], filename=filename)
    if gh is None:
        return
    
    u = get_model_grid(data_dir[1], filename=filename)
    if u is None:
        return
        
    v = get_model_grid(data_dir[2], filename=filename)
    if v is None:
        return
    
    init_time = gh.coords['forecast_reference_time'].values

    # prepare data

    if(area != None):
        cntr_pnt,zoom_ratio=utl.get_map_area(area_name=area)

    map_extent=[0,0,0,0]
    map_extent[0]=cntr_pnt[0]-zoom_ratio*1*map_ratio
    map_extent[1]=cntr_pnt[0]+zoom_ratio*1*map_ratio
    map_extent[2]=cntr_pnt[1]-zoom_ratio*1
    map_extent[3]=cntr_pnt[1]+zoom_ratio*1

    delt_x=(map_extent[1]-map_extent[0])*0.2
    delt_y=(map_extent[3]-map_extent[2])*0.1

#+ to solve the problem of labels on all the contours
    idx_x1 = np.where((gh.coords['lon'].values > map_extent[0]-delt_x) & 
        (gh.coords['lon'].values < map_extent[1]+delt_x))
    idx_y1 = np.where((gh.coords['lat'].values > map_extent[2]-delt_y) & 
        (gh.coords['lat'].values < map_extent[3]+delt_y))

    idx_x2 = np.where((u.coords['lon'].values > map_extent[0]-delt_x) & 
        (u.coords['lon'].values < map_extent[1]+delt_x))
    idx_y2 = np.where((u.coords['lat'].values > map_extent[2]-delt_y) & 
        (u.coords['lat'].values < map_extent[3]+delt_y))
#- to solve the problem of labels on all the contours
    gh = {'lon': gh.coords['lon'].values[idx_x1],
             'lat': gh.coords['lat'].values[idx_y1],
             'data': gh['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':gh_lev,
             'model':model,
             'fhour':fhour,
             'init_time':init_time}
    uv = {'lon': u.coords['lon'].values[idx_x1],
             'lat': u.coords['lat'].values[idx_y1],
             'udata': u['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'vdata': v['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':uv_lev}
    wsp = {'lon': u.coords['lon'].values[idx_x2],
            'lat': u.coords['lat'].values[idx_y2],
             'data': np.squeeze((u['data'].values[0,0,idx_y2[0][0]:(idx_y2[0][-1]+1),idx_x2[0][0]:(idx_x2[0][-1]+1)])**2+
             (v['data'].values[0,0,idx_y2[0][0]:(idx_y2[0][-1]+1),idx_x2[0][0]:(idx_x2[0][-1]+1)])**2)**0.5}


    synoptic_graphics.draw_gh_uv_wsp(
        wsp=wsp, gh=gh, uv=uv,
        map_extent=map_extent, regrid_shape=20,
        city=city,south_China_sea=south_China_sea,
        output_dir=output_dir,Global=Global) 

def gh_uv_r6(initial_time=None, fhour=6, day_back=0,model='ECMWF',
    gh_lev='500',uv_lev='850',
    map_ratio=19/9,zoom_ratio=20,cntr_pnt=[102,34],
    south_China_sea=True,area = '全国',city=False,output_dir=None,
    Global=False):

    if(area != '全国'):
        south_China_sea=False

    # micaps data directory
    try:
        data_dir = [utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl=gh_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=uv_lev),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=uv_lev),
                    utl.Cassandra_dir(data_type='surface',data_source=model,var_name='RAIN06')]
    except KeyError:
        raise ValueError('Can not find all directories needed')

    # get filename
    if(initial_time != None):
        filename = utl.model_filename(initial_time, fhour)
    else:
        filename=utl.filename_day_back_model(day_back=day_back,fhour=fhour)

    # retrieve data from micaps server
    gh = get_model_grid(data_dir[0], filename=filename)
    if gh is None:
        return
    
    u = get_model_grid(data_dir[1], filename=filename)
    if u is None:
        return
        
    v = get_model_grid(data_dir[2], filename=filename)
    if v is None:
        return
    r6 = get_model_grid(data_dir[3], filename=filename)
    
    init_time = gh.coords['forecast_reference_time'].values


    # prepare data

    if(area != None):
        cntr_pnt,zoom_ratio=utl.get_map_area(area_name=area)

    map_extent=[0,0,0,0]
    map_extent[0]=cntr_pnt[0]-zoom_ratio*1*map_ratio
    map_extent[1]=cntr_pnt[0]+zoom_ratio*1*map_ratio
    map_extent[2]=cntr_pnt[1]-zoom_ratio*1
    map_extent[3]=cntr_pnt[1]+zoom_ratio*1

    delt_x=(map_extent[1]-map_extent[0])*0.2
    delt_y=(map_extent[3]-map_extent[2])*0.1

#+ to solve the problem of labels on all the contours
    idx_x1 = np.where((gh.coords['lon'].values > map_extent[0]-delt_x) & 
        (gh.coords['lon'].values < map_extent[1]+delt_x))
    idx_y1 = np.where((gh.coords['lat'].values > map_extent[2]-delt_y) & 
        (gh.coords['lat'].values < map_extent[3]+delt_y))

    idx_x2 = np.where((r6.coords['lon'].values > map_extent[0]-delt_x) & 
        (r6.coords['lon'].values < map_extent[1]+delt_x))
    idx_y2 = np.where((r6.coords['lat'].values > map_extent[2]-delt_y) & 
        (r6.coords['lat'].values < map_extent[3]+delt_y))
#- to solve the problem of labels on all the contours

    gh = {'lon': gh.coords['lon'].values[idx_x1],
             'lat': gh.coords['lat'].values[idx_y1],
             'data': gh['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':gh_lev,
             'model':model,
             'fhour':fhour,
             'init_time':init_time}
    uv = {'lon': u.coords['lon'].values[idx_x1],
             'lat': u.coords['lat'].values[idx_y1],
             'udata': u['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'vdata': v['data'].values[0,0,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
             'lev':uv_lev}
    r6 = {'lon': r6.coords['lon'].values[idx_x2],
            'lat': r6.coords['lat'].values[idx_y2],
             'data': r6['data'].values[0,idx_y2[0][0]:(idx_y2[0][-1]+1),idx_x2[0][0]:(idx_x2[0][-1]+1)]}

    synoptic_graphics.draw_gh_uv_r6(
        r6=r6, gh=gh, uv=uv,
        map_extent=map_extent, regrid_shape=20,
        city=city,south_China_sea=south_China_sea,
        output_dir=output_dir,Global=Global)


def PV_Div_uv(initial_time=None, fhour=6, day_back=0,model='ECMWF',
    map_ratio=19/9,zoom_ratio=20,cntr_pnt=[102,34],
    levels=[1000, 950, 925, 900, 850, 800, 700,600,500,400,300,250,200,100],lvl_ana=250,
    Global=False,
    south_China_sea=True,area = '全国',city=False,output_dir=None
     ):

    # micaps data directory
    try:
        data_dir = [utl.Cassandra_dir(data_type='high',data_source=model,var_name='RH',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='UGRD',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='VGRD',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='TMP',lvl=''),
                    utl.Cassandra_dir(data_type='high',data_source=model,var_name='HGT',lvl='')]
    except KeyError:
        raise ValueError('Can not find all directories needed')

    # get filename
    if(initial_time != None):
        filename = utl.model_filename(initial_time, fhour)
    else:
        filename=utl.filename_day_back_model(day_back=day_back,fhour=fhour)
        
    # retrieve data from micaps server
    rh=get_model_3D_grid(directory=data_dir[0][0:-1],filename=filename,levels=levels, allExists=False)
    if rh is None:
        return

    u=get_model_3D_grid(directory=data_dir[1][0:-1],filename=filename,levels=levels, allExists=False)
    if u is None:
        return

    v=get_model_3D_grid(directory=data_dir[2][0:-1],filename=filename,levels=levels, allExists=False)
    if v is None:
        return

    t=get_model_3D_grid(directory=data_dir[3][0:-1],filename=filename,levels=levels, allExists=False)
    if t is None:
        return

    # get filename
    if(initial_time != None):
        filename = utl.model_filename(initial_time, fhour)
    else:
        filename=utl.filename_day_back_model(day_back=day_back,fhour=fhour)

    lats = np.squeeze(rh['lat'].values)
    lons = np.squeeze(rh['lon'].values)

    pres = np.array(levels)*100 * units('Pa')
    tmpk = mpcalc.smooth_n_point(t['data'].values.squeeze(), 9, 2)*units('degC')
    thta = mpcalc.potential_temperature(pres[:, None, None], tmpk)

    uwnd = mpcalc.smooth_n_point(u['data'].values.squeeze(), 9, 2)*units.meter/units.second
    vwnd = mpcalc.smooth_n_point(v['data'].values.squeeze(), 9, 2)*units.meter/units.second

    dx, dy = mpcalc.lat_lon_grid_deltas(lons, lats)

    # Comput the PV on all isobaric surfaces
    pv = mpcalc.potential_vorticity_baroclinic(thta, pres[:, None, None], uwnd, vwnd,
                                            dx[None, :, :], dy[None, :, :],
                                            lats[None, :, None] * units('degrees'))
    div = mpcalc.divergence(uwnd, vwnd, dx[None, :, :], dy[None, :, :], dim_order='yx')

    # prepare data
    idx_z1 = list(pres.m).index(((lvl_ana * units('hPa')).to(pres.units)).m)
    if(area != None):
        cntr_pnt,zoom_ratio=utl.get_map_area(area_name=area)

    map_extent=[0,0,0,0]
    map_extent[0]=cntr_pnt[0]-zoom_ratio*1*map_ratio
    map_extent[1]=cntr_pnt[0]+zoom_ratio*1*map_ratio
    map_extent[2]=cntr_pnt[1]-zoom_ratio*1
    map_extent[3]=cntr_pnt[1]+zoom_ratio*1

    delt_x=(map_extent[1]-map_extent[0])*0.2
    delt_y=(map_extent[3]-map_extent[2])*0.1

    #+ to solve the problem of labels on all the contours
    idx_x1 = np.where((lons > map_extent[0]-delt_x) & 
        (lons < map_extent[1]+delt_x))
    idx_y1 = np.where((lats > map_extent[2]-delt_y) & 
        (lats < map_extent[3]+delt_y))
    #- to solve the problem of labels on all the contours
    init_time = u.coords['forecast_reference_time'].values
    pv = {
        'lon': lons[idx_x1],
        'lat': lats[idx_y1],
        'data': np.array(pv)[idx_z1,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
        'lev':str(lvl_ana),
        'model':model,
        'fhour':fhour,
        'init_time':init_time}
    uv = {
        'lon': lons[idx_x1],
        'lat': lats[idx_y1],
        'udata': np.array(uwnd)[idx_z1,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
        'vdata': np.array(vwnd)[idx_z1,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
        'lev':str(lvl_ana)}
    div = {
        'lon': lons[idx_x1],
        'lat': lats[idx_y1],
        'data': np.array(div)[idx_z1,idx_y1[0][0]:(idx_y1[0][-1]+1),idx_x1[0][0]:(idx_x1[0][-1]+1)],
        'lev':str(lvl_ana)}

    synoptic_graphics.draw_PV_Div_uv(
        pv=pv, uv=uv, div=div,
        map_extent=map_extent, regrid_shape=20,
        city=city,south_China_sea=south_China_sea,
        output_dir=output_dir,Global=Global)
