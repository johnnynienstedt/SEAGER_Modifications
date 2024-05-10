#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 11:09:22 2024

@author: johnnynienstedt
"""

#
# Form rankings
# Johnny Nienstedt 2/23/24
#

# This program follows league_rv.py and player_heatmap.py. This program determines if
# a player swung at or took every pitch they saw in the desired season, by count
# and location. These programs together will give a grade for the player's swing
# decisions, both in relation to league RV (classic) and his own strenghts (player).

import pandas as pd
import requests
from bs4 import BeautifulSoup
import math
import time
from scipy import stats

# def swing_take(year):

year = 2021

year = str(year)

# load data
pdat = pd.read_csv('players_' + year + '.csv')
league_rv = pd.read_csv('league_rv_' + year + '.csv')
player_rv = pd.read_csv('player_rv_' + year + '.csv')

player_id = list(pdat['player_id'])
player_name = list(pdat['player_name'])

# create session for requests
s = requests.Session()

# initialize lists
c_rows = []
p_rows = []
counts = ['00', '10', '20', '30', '01', '11', '21', '31', '02', '12', '22', '32']


# timing
timer_start = time.perf_counter()
start_min = time.localtime()[4]
start_hr = time.localtime()[3]

# loop over all players
for i in range(len(player_id)): 
    
    print(player_name[i], end = ' - ')
    
    # batter lookup string
    pid = player_id[i]
    batter_lookup = 'batters_lookup%5B%5D=' + str(pid)
    
    # initialize values
    cexp_rv = 0
    
    c_good_swings = 0
    c_good_swing_runs = 0
    c_bad_swings = 0
    c_bad_swing_runs = 0
    
    c_good_takes = 0
    c_good_take_runs = 0
    c_bad_takes = 0
    c_bad_take_runs = 0
    
    
    pexp_rv = 0
    
    p_good_swings = 0
    p_good_swing_runs = 0
    p_bad_swings = 0
    p_bad_swing_runs = 0
    
    p_good_takes = 0
    p_good_take_runs = 0
    p_bad_takes = 0
    p_bad_take_runs = 0
    
    
    ns, nt = 0, 0
    
    
    #
    # swings
    #
    for j in range(len(counts)):
                
        # for every pitch, scrape location
        url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=foul%7Cfoul%5C.%5C.bunt%7Cbunt%5C.%5C.foul%5C.%5C.tip%7Cfoul%5C.%5C.pitchout%7Chit%5C.%5C.into%5C.%5C.play%7Cmissed%5C.%5C.bunt%7Cfoul%5C.%5C.tip%7Cswinging%5C.%5C.strike%7Cswinging%5C.%5C.strike%5C.%5C.blocked%7C&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=" + counts[j] + "%7C&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&" + batter_lookup + "&hfFlag=&metric_1=&group_by=name-event&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_plate_x&sort_order=desc&chk_swings=on&chk_event_plate_x=on&chk_event_plate_z=on#results"
        t = s.get(url).text
        soup = BeautifulSoup(t, 'html.parser')
        
        # get table data (x and z location)
        table = soup.find('table', id = 'search_results')
                
        # skip to next count if there are no results
        try:
            table.find_all('tbody')
        except AttributeError:
            continue
        
        for pitch_data in table.find_all('tbody'):
            rows = pitch_data.find_all('tr')
        
        # scrape rows of table
        r = 1
        for row in rows:
            
            # only every other row contains data
            if r % 2 == 0:
                r = r + 1
                continue
            
            # handle end of table
            try:
                px = float(row.find_all('td')[6].text.split()[0])
                pz = float(row.find_all('td')[7].text.split()[0])
            except IndexError:
                continue
            
                
            # round appropriately to proper zone
            if px >= 0:
                px = round(round(math.floor(10*px)/10, 1) + 0.05, 2)
            if px < 0:
                px = round(round(math.ceil(10*px)/10, 1) + 0.05, 2)
            
            pz = round(round(math.floor(10*pz)/10, 1) + 0.05, 2)
            
            # assign out of range values to border
            if px < - 1.45: px = -1.45
            if px > 1.45: px = 1.45
            if pz < 0.55: pz = 0.55
            if pz > 3.95: pz = 3.95
            
            #
            # add values cumulatively
            #
            
            # expected run value of this pitch (by league and by player):
            new_cexp_rv = round(float(league_rv.loc[(league_rv['XLOC'] == px) & (league_rv['ZLOC'] == pz)]['RV_' + counts[j]]), 4)
            new_pexp_rv = round(float(player_rv.loc[(player_rv['ID'] == pid) & (player_rv['XLOC'] == px) & (player_rv['ZLOC'] == pz)]['RV_' + counts[j]]), 4)
            
            cexp_rv = cexp_rv + new_cexp_rv
            pexp_rv = pexp_rv + new_pexp_rv

            
            # run value earned (or lost) for SWINGING at this pitch (by l & p):
            new_cswing_rv = round(float(league_rv.loc[(league_rv['XLOC'] == px) & (league_rv['ZLOC'] == pz)]['SWING_' + counts[j]]), 4)
            new_pswing_rv = round(float(player_rv.loc[(player_rv['ID'] == pid) & (player_rv['XLOC'] == px) & (player_rv['ZLOC'] == pz)]['SWING_' + counts[j]]), 4)
            
            
            if new_cswing_rv > 0:
                c_good_swings = c_good_swings + 1
                c_good_swing_runs = c_good_swing_runs + new_cswing_rv
            else:
                c_bad_swings = c_bad_swings + 1
                c_bad_swing_runs = c_bad_swing_runs + new_cswing_rv
                
                
            if new_pswing_rv > 0:
                p_good_swings = p_good_swings + 1
                p_good_swing_runs = p_good_swing_runs + new_pswing_rv
            else:
                p_bad_swings = p_bad_swings + 1
                p_bad_swing_runs = p_bad_swing_runs + new_pswing_rv
            
            ns = ns + 1
            
            r = r + 1
        
    #
    # takes
    #
    for j in range(len(counts)):
        url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7Cblocked%5C.%5C.ball%7Ccalled%5C.%5C.strike%7Cpitchout%7Chit%5C.%5C.by%5C.%5C.pitch%7Cintent%5C.%5C.ball%7C&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=" + counts[j] + "%7C&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&" + batter_lookup + "&hfFlag=&metric_1=&group_by=name-event&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_plate_x&sort_order=desc&chk_swings=on&chk_event_plate_x=on&chk_event_plate_z=on#results"
        t = s.get(url).text
        soup = BeautifulSoup(t, 'html.parser')
        
        # scrape table data (x and z location)
        table = soup.find('table', id = 'search_results')
        
        # skip to next count if there are no results
        try:
            table.find_all('tbody')
        except AttributeError:
            continue
        
        for pitch_data in table.find_all('tbody'):
            rows = pitch_data.find_all('tr')
        
        r = 1
        for row in rows:
            if r % 2 == 0:
                r = r + 1
                continue
            
            try:
                px = float(row.find_all('td')[6].text.split()[0])
                pz = float(row.find_all('td')[7].text.split()[0])
            except IndexError:
                continue
            
            # round appropriately to proper zone
            if px >= 0:
                px = round(round(math.floor(10*px)/10, 1) + 0.05, 2)
            if px < 0:
                px = round(round(math.ceil(10*px)/10, 1) + 0.05, 2)
            
            pz = round(round(math.floor(10*pz)/10, 1) + 0.05, 2)
            
            # assign out of range values to border
            if px < - 1.45: px = -1.45
            if px > 1.45: px = 1.45
            if pz < 0.55: pz = 0.55
            if pz > 3.95: pz = 3.95
            
            
            #
            # add values cumulatively
            #
            
            # expected run value of this pitch (by league and by player):
            new_cexp_rv = round(float(league_rv.loc[(league_rv['XLOC'] == px) & (league_rv['ZLOC'] == pz)]['RV_' + counts[j]]), 4)
            new_pexp_rv = round(float(player_rv.loc[(player_rv['ID'] == pid) & (player_rv['XLOC'] == px) & (player_rv['ZLOC'] == pz)]['RV_' + counts[j]]), 4)
            
            cexp_rv = cexp_rv + new_cexp_rv
            pexp_rv = pexp_rv + new_pexp_rv
            
            
            # run value earned (or lost) for TAKING this pitch (by l & p):
            new_ctake_rv = round(float(league_rv.loc[(league_rv['XLOC'] == px) & (league_rv['ZLOC'] == pz)]['TAKE_' + counts[j]]), 4)
            new_ptake_rv = round(float(player_rv.loc[(player_rv['ID'] == pid) & (player_rv['XLOC'] == px) & (player_rv['ZLOC'] == pz)]['TAKE_' + counts[j]]), 4)
            
            if new_ctake_rv > 0:
                c_good_takes = c_good_takes + 1
                c_good_take_runs = c_good_take_runs + new_ctake_rv
            else:
                c_bad_takes = c_bad_takes + 1
                c_bad_take_runs = c_bad_take_runs + new_ctake_rv
                
                
            if new_ptake_rv > 0:
                p_good_takes = p_good_takes + 1
                p_good_take_runs = p_good_take_runs + new_ptake_rv
            else:
                p_bad_takes = p_bad_takes + 1
                p_bad_take_runs = p_bad_take_runs + new_ptake_rv

            nt = nt + 1
            
            r = r + 1

    csrv = c_good_swing_runs + c_bad_swing_runs
    ctrv = c_good_take_runs + c_bad_take_runs
    
    c_rows.append(
        {
            'NAME': player_name[i],
            'ID': pid,
            'NS': ns,
            'NT': nt,
            'GSRV': round(c_good_swing_runs, 1),
            'BSRV': round(c_bad_swing_runs, 1),
            'SRV': round(csrv, 1),
            'GTRV': round(c_good_take_runs, 1),
            'BTRV': round(c_bad_take_runs, 1),
            'TRV': round(ctrv, 1),
            'EXP_RV': round(cexp_rv, 1),
            'TOT_RV': round(csrv + ctrv, 1),
            'SWTR': round(csrv + ctrv - cexp_rv, 1),
            'SWTR_Per650': round((csrv + ctrv -cexp_rv)/(ns + nt)*2542, 1)
        }
    )
    
    
    psrv = p_good_swing_runs + p_bad_swing_runs
    ptrv = p_good_take_runs + p_bad_take_runs
    
    p_rows.append(
        {
            'NAME': player_name[i],
            'ID': pid,
            'NS': ns,
            'NT': nt,
            'GSRV': round(p_good_swing_runs, 1),
            'BSRV': round(p_bad_swing_runs, 1),
            'SRV': round(psrv, 1),
            'GTRV': round(p_good_take_runs, 1),
            'BTRV': round(p_bad_take_runs, 1),
            'TRV': round(ptrv, 1),
            'EXP_RV': round(pexp_rv, 1),
            'TOT_RV': round(psrv + ptrv, 1),
            'SWTR': round(psrv + ptrv - pexp_rv, 1),
            'SWTR_Per650': round((psrv + ptrv -pexp_rv)/(ns + nt)*2542, 1)
        }
    )

    now = time.perf_counter()
    p = (i + 1)/len(player_id)
    exp = round((now - timer_start)/p)
    exp_hr = math.floor(exp/3600)
    exp_min = round((exp % 3600)/60)
    mn = start_min + exp_min
    if mn > 59: 
        mn = mn - 60
        exp_hr = exp_hr + 1
    if mn < 10: mn = '0' + str(mn)
    hr = start_hr + exp_hr
    while hr > 12: hr = hr - 12
    print(str(round(100*p, 1)) + '% - expected finishing time: ' + str(hr) + ':' + str(mn))   
    
    
classic_st = pd.DataFrame(c_rows)
player_st = pd.DataFrame(p_rows)


# percentiles
def percentile(col, x):
    return round(stats.percentileofscore(col, x))

classic_st['Total_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SWTR'], x.SWR), axis = 1)
classic_st['Rate_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SWTR_Per650'], x.SWR), axis = 1)

player_st['Total_Percentile'] = player_st.apply(lambda x: percentile(player_st['SWTR'], x.SWR), axis = 1)
player_st['Rate_Percentile'] = player_st.apply(lambda x: percentile(player_st['SWTR_Per650'], x.SWR), axis = 1)


# save to csv
classic_st.to_csv('classic_st' + year + '.csv')
player_st.to_csv('player_st' + year + '.csv')


# swing_take(2021)
# swing_take(2022)2
# swing_take(2023)
# swing_take(2024)

