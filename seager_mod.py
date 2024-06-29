#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 12:30:00 2024

@author: johnnynienstedt
"""

#
# League Data Acquisition for SEAGER modification
# Johnny Nienstedt 2/20/24
#
# Major update - switched from requests to pybaseball 6/16/24
# Runtime down to ~30 minutes
#

# The goal of this script is to evaluate player swing decisions in the context
# of run value over expectation, based on pitch location and count. There are 
# two separate evaluation methods included here. The first, 'classic,' defines
# expected run value based on league-wide tendencies. This is analogous to the
# original SEAGER metric developed by Robert Orr. The second, 'player,' instead
# uses a proprietary estimation of expected run value derived from their own
# offensive profile. This method seeks to completely isolate swing decisions,
# removing as much of the swing results as possible.


import pandas as pd
import numpy as np
import time
import math
from scipy import stats
import pybaseball

# enable caching
pybaseball.cache.enable()
    
# get pitch data
def get_pitch_data(year):
    
    ###########################################################################
    ############################# Get Pitch Data ##############################
    ###########################################################################


    
    year = str(year)
    
    print()
    print('Gathering Pitch-by-Pitch Data for', year)
    print()
    
    # determine opening day and last day of regular season
    schedule = pybaseball.schedule_and_record(int(year), 'HOU')
    
    # opening day
    day1 = int(schedule['Date'][1][-2:])
    if day1 < 10:
        start_date = year + '-04-0' + str(day1)
    else:
        start_date = year + '-03-' + str(day1)
        
    # last day
    day162 = int(schedule['Date'][162][-2:])
    if day162 < 10:
        end_date = year + '-10-0' + str(day162)
    else:
        end_date = year + '-09-' + str(day162)
         

    # get pitch-by-pitch data for this year
    pitch_data = pybaseball.statcast(start_date, end_date)
    
    return year, pitch_data

# get league data
def get_league_data(year, pitch_data):
    
    ###########################################################################
    ############################# Get League Data #############################
    ###########################################################################
    
    
    print()
    print('Gathering League Data for', year)
    print()
    
    # RE24 values
    global ball_rv, strike_rv
    ball_rv = np.zeros([4, 3])
    strike_rv = np.zeros([4, 3])
    
    ball_rv[0][0] = 0.032
    ball_rv[1][0] = 0.088
    ball_rv[2][0] = 0.143
    ball_rv[3][0] = 0.051
    ball_rv[0][1] = 0.024
    ball_rv[1][1] = 0.048
    ball_rv[2][1] = 0.064
    ball_rv[3][1] = 0.168
    ball_rv[0][2] = 0.021
    ball_rv[1][2] = 0.038
    ball_rv[2][2] = 0.085
    ball_rv[3][2] = 0.234
    strike_rv[0][0] = -0.037
    strike_rv[1][0] = -0.035
    strike_rv[2][0] = -0.062
    strike_rv[3][0] = -0.117
    strike_rv[0][1] = -0.051
    strike_rv[1][1] = -0.054
    strike_rv[2][1] = -0.069
    strike_rv[3][1] = -0.066
    strike_rv[0][2] = -0.150
    strike_rv[1][2] = -0.171
    strike_rv[2][2] = -0.209
    strike_rv[3][2] = -0.294
    
    
    global swing_types, take_types
    
    swing_types = ['hit_into_play', 'foul', 'swinging_strike',
                   'foul_tip', 'swinging_strike_blocked']
    take_types = ['ball', 'called_strike', 'blocked_ball',
                  'hit_by_pitch', 'pitchout']

    
    # time data acquisition
    timer_start = time.perf_counter()
    start_hr = time.localtime()[3]
    start_min = time.localtime()[4]
    
    
    # initialize data frame
    league_rv = pd.DataFrame()
    
    
    # evaluate reasonable range of pitches (# 3 ft wide and 3.5 ft tall)
    # 88% of pitches are in this region
    for X in range(-15,15):
        x = round(X/10, 2)
        for Z in range(5,40):
            z = round(Z/10, 2)
            
            # get baseline rv for each count
            rv = []
            swing_rate = []
            rv_swing = []
            rv_take = []
            
            for s in range(3):
                for b in range(4):
                    
                    # data for pitches here in this count
                    pitches = pitch_data[(pitch_data.plate_x >= x) & 
                                           (pitch_data.plate_x < x + 0.1) & 
                                           (pitch_data.plate_z >= z) & 
                                           (pitch_data.plate_z < z + 0.1) &
                                           (pitch_data.balls == b) &
                                           (pitch_data.strikes == s)]
                    n = len(pitches)
                    
                    
                    
                    # pitches swung at
                    swings = pitches[pitches.description.isin(swing_types)]
                    
                    # number of swings
                    n_swings = len(swings)
                    
                    if n != 0:
                        swing_rate.append(n_swings/n)
                    else:
                        swing_rate.append(0)
                    
                    # contact & foul ball percentage
                    if n_swings != 0:
                        contact = len(swings.description == 'hit_into_play')/n_swings
                        foul = len(swings.description == 'foul')/n_swings
                    else:
                        contact, foul = 0, 0
                                
                    # observed run value on balls in play
                    if contact != 0:
                        xwobacon = swings[swings.description == 'hit_into_play']['estimated_woba_using_speedangle'].fillna(0).mean()
                        bip_rv = 0.579713*xwobacon - 0.158091
                    else:
                        bip_rv  = 0
                            
                    # calculated run value for swings, based on RE24
                    if s == 2:
                        swing_rv = (contact*bip_rv + (1 - contact)*strike_rv[b][s])
                    else:
                        swing_rv = (contact*bip_rv + (1 - contact + foul)*strike_rv[b][s])
                    
                    rv_swing.append(swing_rv)
                    
                    
                    
                    # pitches taken
                    takes = pitches[pitches.description.isin(take_types)]
                    
                    # number of takes
                    n_takes = len(takes)
                    
                    # percentage of taken pitches called stikes
                    if n_takes != 0:
                        cs = len(takes[(takes.description == 'called_strike')])/n_takes
                    else:
                        if n_swings > 0:
                            cs = 1
                        else:
                            cs = 0
                    
                    # calculated run value on takes, based on RE24
                    take_rv = cs*strike_rv[b,s] + (1 - cs)*ball_rv[b,s]
                    rv_take.append(take_rv)
                    
                    
                    # aggregate league run value on pitches in this location & count
                    if n_swings == 0:
                        this_rv = take_rv
                    
                    elif n_takes == 0:
                        this_rv = swing_rv
                    
                    else:
                        this_rv = (swing_rv*n_swings + take_rv*n_takes)/(n_swings + n_takes)
    
                    # append this count to list for this location
                    rv.append(this_rv)
            
            
            
            new_row = pd.DataFrame(
                {
                    "XLOC": [round(x + 0.05, 2)],
                    "ZLOC": [round(z + 0.05, 2)],
                    "RV_00": [rv[0]],
                    "RV_10": [rv[1]],
                    "RV_20": [rv[2]],
                    "RV_30": [rv[3]],
                    "RV_01": [rv[4]],
                    "RV_11": [rv[5]],
                    "RV_21": [rv[6]],
                    "RV_31": [rv[7]],
                    "RV_02": [rv[8]],
                    "RV_12": [rv[9]],
                    "RV_22": [rv[10]],
                    "RV_32": [rv[11]],
                    "SWING_00": [swing_rate[0]],
                    "SWING_10": [swing_rate[1]],
                    "SWING_20": [swing_rate[2]],
                    "SWING_30": [swing_rate[3]],
                    "SWING_01": [swing_rate[4]],
                    "SWING_11": [swing_rate[5]],
                    "SWING_21": [swing_rate[6]],
                    "SWING_31": [swing_rate[7]],
                    "SWING_02": [swing_rate[8]],
                    "SWING_12": [swing_rate[9]],
                    "SWING_22": [swing_rate[10]],
                    "SWING_32": [swing_rate[11]],
                    "SRV_00": [rv_swing[0]],
                    "SRV_10": [rv_swing[1]],
                    "SRV_20": [rv_swing[2]],
                    "SRV_30": [rv_swing[3]],
                    "SRV_01": [rv_swing[4]],
                    "SRV_11": [rv_swing[5]],
                    "SRV_21": [rv_swing[6]],
                    "SRV_31": [rv_swing[7]],
                    "SRV_02": [rv_swing[8]],
                    "SRV_12": [rv_swing[9]],
                    "SRV_22": [rv_swing[10]],
                    "SRV_32": [rv_swing[11]],
                    "TRV_00": [rv_take[0]],
                    "TRV_10": [rv_take[1]],
                    "TRV_20": [rv_take[2]],
                    "TRV_30": [rv_take[3]],
                    "TRV_01": [rv_take[4]],
                    "TRV_11": [rv_take[5]],
                    "TRV_21": [rv_take[6]],
                    "TRV_31": [rv_take[7]],
                    "TRV_02": [rv_take[8]],
                    "TRV_12": [rv_take[9]],
                    "TRV_22": [rv_take[10]],
                    "TRV_32": [rv_take[11]]
                }
            )
            
            league_rv = pd.concat([league_rv, new_row], ignore_index = True)
            
            now = time.perf_counter()
            p = ((X + 15)*35 + Z - 4)/1050
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
            if round(100*p,1) in range(100):
                print(str(round(100*p)) + '% - expected finishing time: ' + str(hr) + ':' + str(mn)) 
    
    # interpolate NaN vlaues
    league_rv = league_rv.interpolate(method='nearest', limit_direction='both')
    league_rv = league_rv.interpolate(method='linear', limit_direction='both')
    
    # save to csv
    league_rv.to_csv('league_rv_' + year + '.csv', index = False)
            
    tot_time = time.perf_counter() - timer_start
    hours = str(math.floor(tot_time/3600))
    mins = str(round(tot_time % 3600 / 60))
    print()
    if hours == '0':
        print('This operation took', mins, 'minutes.')
    else:
        if mins == '1':
            print('This operation took', hours, 'hours and one minute.')
        
        else:
            print('This operation took', hours, 'hours and', mins, 'minutes.')
    
    return league_rv

# get player data
def get_player_data(year, pitch_data):
    
    ###########################################################################
    ############################# Get Player Data #############################
    ###########################################################################
    
    
    
    print()
    print("Gathering Player Data for", year)
    print()
    
    # load player data
    pdat = pd.read_csv('players_' + year + '.csv')
    global player_id, player_name
    player_id = list(pdat['player_id'])
    player_name = list(pdat['player_name'])
    
    # intialise list of dictionaries
    rows = []
    
    # called strike% by zone
    cs = ['na', 0.776, 0.909, 0.802, 0.955, 1, 0.957, 0.874, 0.924, 0.823, 'na', 0.048, 0.076, 0.064, 0.047]
    
    # timing
    timer_start = time.perf_counter()
    start_min = time.localtime()[4]
    start_hr = time.localtime()[3]
    
    # Get batter stats for each zone to be converted to RV
    for i in range(len(player_id)): 
        print(player_name[i], end = ' - ')
        
        # get player rv for each zone
        for j in range(13):
            
            rv_swing = []
            rv_take = []
            rv_delta = []
            
            if j < 9: zone = j + 1
            else: zone = j + 2
            
            # data for pitches in this zone to this player
            pitches = pitch_data[(pitch_data.batter == player_id[i]) & 
                                   (pitch_data.zone == zone)]
            
            n = len(pitches)
            
            
            
            # pitches swung at
            swings = pitches[pitches.description.isin(swing_types)]
            
            # number of swings
            n_swings = len(swings)
            
            # contact & foul ball percentage
            if n_swings != 0:
                contact = sum(swings.description == 'hit_into_play')/n_swings
                foul = sum(swings.description == 'foul')/n_swings
            else:
                contact, foul = 0, 0
                
            # observed run value on balls in play
            if contact != 0:
                xwobacon = swings[swings.description == 'hit_into_play']['estimated_woba_using_speedangle'].fillna(0).mean()
                bip_rv = 0.579713*xwobacon - 0.158091
            else:
                bip_rv  = 0
            
            
            # pitches taken
            takes = pitches[pitches.description.isin(take_types)]
            
            # number of takes
            n_takes = len(takes)
            
            
            
            # calculated run value for swings and takes, based on RE24
            for s in range(3):
                for b in range(4):
                    
                    # swings
                    if s == 2:
                        swing_rv = (contact*bip_rv + (1 - contact)*strike_rv[b][s])
                    else:
                        swing_rv = (contact*bip_rv + (1 - contact + foul)*strike_rv[b][s])
                    
                    rv_swing.append(swing_rv)
                    
                    # takes
                    take_rv = cs[zone]*strike_rv[b,s] + (1 - cs[zone])*ball_rv[b,s]
                    rv_take.append(take_rv)
            
            rv_delta = [rv_swing[i] - rv_take[i] for i in range(len(rv_swing))]
            
            
            
            # aggregate player run value on pitches in this zone
            if n_swings == 0:
                rv = rv_take
            
            elif n_takes == 0:
                rv = rv_swing
            
            else:
                rv = [(rv_swing[i]*n_swings + rv_take[i]*n_takes)/n for i in range(len(rv_swing))]



            new_row = {
                     "NAME": player_name[i],
                     "ID": player_id[i],
                     "ZONE": zone,
                     "N_P": n,
                     "RV_00": rv[0],
                     "RV_10": rv[1],
                     "RV_20": rv[2],
                     "RV_30": rv[3],
                     "RV_01": rv[4],
                     "RV_11": rv[5],
                     "RV_21": rv[6],
                     "RV_31": rv[7],
                     "RV_02": rv[8],
                     "RV_12": rv[9],
                     "RV_22": rv[10],
                     "RV_32": rv[11],
                     "SRV_00": rv_swing[0],
                     "SRV_10": rv_swing[1],
                     "SRV_20": rv_swing[2],
                     "SRV_30": rv_swing[3],
                     "SRV_01": rv_swing[4],
                     "SRV_11": rv_swing[5],
                     "SRV_21": rv_swing[6],
                     "SRV_31": rv_swing[7],
                     "SRV_02": rv_swing[8],
                     "SRV_12": rv_swing[9],
                     "SRV_22": rv_swing[10],
                     "SRV_32": rv_swing[11],
                     "TRV_00": rv_take[0],
                     "TRV_10": rv_take[1],
                     "TRV_20": rv_take[2],
                     "TRV_30": rv_take[3],
                     "TRV_01": rv_take[4],
                     "TRV_11": rv_take[5],
                     "TRV_21": rv_take[6],
                     "TRV_31": rv_take[7],
                     "TRV_02": rv_take[8],
                     "TRV_12": rv_take[9],
                     "TRV_22": rv_take[10],
                     "TRV_32": rv_take[11],
                     "DRV_00": rv_delta[0],
                     "DRV_10": rv_delta[1],
                     "DRV_20": rv_delta[2],
                     "DRV_30": rv_delta[3],
                     "DRV_01": rv_delta[4],
                     "DRV_11": rv_delta[5],
                     "DRV_21": rv_delta[6],
                     "DRV_31": rv_delta[7],
                     "DRV_02": rv_delta[8],
                     "DRV_12": rv_delta[9],
                     "DRV_22": rv_delta[10],
                     "DRV_32": rv_delta[11]
                     
                     }
            
            rows.append(new_row)


        # estimate finishing time
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


    # create data frame
    player_rv_z = pd.DataFrame(rows)

    # save to csv
    player_rv_z.to_csv('player_rv_z_' + year + '.csv', index = False)
    
    # finish time
    tot_time = time.perf_counter() - timer_start
    hours = str(math.floor(tot_time/3600))
    mins = str(round(tot_time % 3600 / 60))
    print()
    if hours == '0':
        print('This operation took', mins, 'minutes.')
    else:
        if mins == '1':
            print('This operation took', hours, 'hours and one minute.')
        
        else:
            print('This operation took', hours, 'hours and', mins, 'minutes.')
    
    return player_rv_z

# make player heatmaps
def player_heatmap(year, player_rv_z):
    
    
    
    ###########################################################################
    ############################## Make Heatmaps ##############################
    ###########################################################################
    
    
    
    print()
    print("Making Heatmaps for", year)
    print()
    
    year = str(year)
    
    # strike zone dimensions
    zone_height = 35
    zone_width = 30
    
    # number of iterations for numerical solution
    n_iter = 10
    
    # Initialize rows of dataframe
    rows = []
    zone_rows = []
    loc_rows = []
    
    for i in range(len(player_id)):
        print(player_name[i], end = ' - ')
        
        # initialize list to hold results for all counts (one for each player)
        rvbc = []
        
        for b in range(4):
            for s in range(3):
                
                count = str(b) + str(s)
                n_p = player_rv_z.at[i + 1, 'N_P']
                
                # Initialize heat maps
                swing_rv = np.zeros((zone_width, zone_height))
                take_rv = np.zeros((zone_width, zone_height))
                delta_rv = np.zeros((zone_width, zone_height))
                
                # create zones
                x0, y0 = 0, 0
                x1, y1 = 5, 6
                x15, y15 = 9, 10
                x2, y2 = 12, 14
                x25, y25 = 15, 18
                x3, y3 = 18, 22
                x35, y35 = 21, 26
                x4, y4 = 25, 30
                x5, y5 = 30, 35
                
                
                def set_conds(rv_map, action, reset = False):
                    
                    if action == 's':
                        a = 'SRV_'
                    if action == 't':
                        a = 'TRV_'
                    if action == 'd':
                        a = 'DRV_'
                    
                    # initial conditions
                    z1 = player_rv_z.at[i*13, a + count]
                    z2 = player_rv_z.at[i*13 + 1, a + count]
                    z3 = player_rv_z.at[i*13 + 2, a + count]
                    z4 = player_rv_z.at[i*13 + 3, a + count]
                    z5 = player_rv_z.at[i*13 + 4, a + count]
                    z6 = player_rv_z.at[i*13 + 5, a + count]
                    z7 = player_rv_z.at[i*13 + 6, a + count]
                    z8 = player_rv_z.at[i*13 + 7, a + count]
                    z9 = player_rv_z.at[i*13 + 8, a + count]
                    z11 = player_rv_z.at[i*13 + 9, a + count]
                    z12 = player_rv_z.at[i*13 + 10, a + count]
                    z13 = player_rv_z.at[i*13 + 11, a + count]
                    z14 = player_rv_z.at[i*13 + 12, a + count]
                    
                    if not reset:
                        # Set the initial conditions by zone
                        rv_map[x1:x2, y3:y4] = z1
                        rv_map[x2:x3, y3:y4] = z2
                        rv_map[x3:x4, y3:y4] = z3
                        rv_map[x1:x2, y2:y3] = z4
                        rv_map[x2:x3, y2:y3] = z5
                        rv_map[x3:x4, y2:y3] = z6
                        rv_map[x1:x2, y1:y2] = z7
                        rv_map[x2:x3, y1:y2] = z8
                        rv_map[x3:x4, y1:y2] = z9
                        rv_map[x0:x1, y25:y5] = z11
                        rv_map[x1:x25, y4:y5] = z11
                        rv_map[x25:x5, y4:y5] = z12
                        rv_map[x4:x5, y25:y5] = z12
                        rv_map[x0:x1, y0:y25] = z13
                        rv_map[x1:x25, y0:y1] = z13
                        rv_map[x25:x5, y0:y1] = z14
                        rv_map[x4:x5, y0:y25] = z14
                    
                    # reset boundary conditions
                    if reset: 
                        rv_map[x0,y25:y5] = z11
                        rv_map[x0:x25,y5 - 1] = z11
                        
                        rv_map[x25:x5,y5 - 1] = z12
                        rv_map[x5 - 1,y25:y5] = z12
                        
                        rv_map[x0:x25,y0] = z13
                        rv_map[x0,y0:y25] = z13
                        
                        rv_map[x5 - 1,y0:y25] = z14
                        rv_map[x25:x5,y0] = z14
                        
                        rv_map[x15,y35] = z1
                        rv_map[x25,y35] = z2
                        rv_map[x35,y35] = z3
                        rv_map[x15,y25] = z4
                        rv_map[x25,y25] = z5
                        rv_map[x35,y25] = z6
                        rv_map[x15,y15] = z7
                        rv_map[x25,y15] = z8
                        rv_map[x35,y15] = z9
                    
                    return rv_map
    
                # For plotting purposes
                set_conds(swing_rv, 's')
                set_conds(take_rv, 't')
                set_conds(delta_rv, 'd')
                
                zone_rows.append([swing_rv, take_rv, delta_rv])
    
    
                #
                # Swing RV
                #
                
                set_conds(swing_rv, 's')
                m = swing_rv.mean()
    
                # calculate swing_rv using relaxation method
                for n in range(n_iter):
                    swing_rv = 0.25*(np.roll(swing_rv, zone_height - 1, axis = 1) + np.roll(swing_rv, 1 - zone_height, axis = 1) + np.roll(swing_rv, zone_width - 1, axis = 0) + np.roll(swing_rv, 1 - zone_width, axis = 0))
                    swing_rv = set_conds(swing_rv, 's', reset = True)                
                
                swing_rv = swing_rv - swing_rv.mean() + m
    
                
                #
                # Take RV
                #
                
                set_conds(take_rv, 't')
                m = take_rv.mean()
                
                # calculate take_rv using relaxation method
                for n in range(n_iter):
                    take_rv = 0.25*(np.roll(take_rv, zone_height - 1, axis = 1) + np.roll(take_rv, 1 - zone_height, axis = 1) + np.roll(take_rv, zone_width - 1, axis = 0) + np.roll(take_rv, 1 - zone_width, axis = 0))
                    take_rv = set_conds(take_rv, 't', reset = True)    
    
                take_rv = take_rv - take_rv.mean() + m
    
                
                rvbc.append([swing_rv, take_rv])
                
                # For more plotting purposes:
                loc_rows.append([swing_rv, take_rv])
                
    
    
        for x in range(zone_width):
            xloc = round((x - 15)/10 + 0.05, 2)
            for z in range(zone_height):
                zloc = round((z + 5)/10 + 0.05, 2)
                rows.append(
                    {
                          "NAME": player_name[i],
                          "ID": player_id[i],
                          "N_P": n_p,
                          "XLOC": xloc,
                          "ZLOC": zloc,
                          "SRV_00": rvbc[0][0][x][z],
                          "SRV_10": rvbc[1][0][x][z],
                          "SRV_20": rvbc[2][0][x][z],
                          "SRV_30": rvbc[3][0][x][z],
                          "SRV_01": rvbc[4][0][x][z],
                          "SRV_11": rvbc[5][0][x][z],
                          "SRV_21": rvbc[6][0][x][z],
                          "SRV_31": rvbc[7][0][x][z],
                          "SRV_02": rvbc[8][0][x][z],
                          "SRV_12": rvbc[9][0][x][z],
                          "SRV_22": rvbc[10][0][x][z],
                          "SRV_32": rvbc[11][0][x][z],
                          "TRV_00": rvbc[0][1][x][z],
                          "TRV_10": rvbc[1][1][x][z],
                          "TRV_20": rvbc[2][1][x][z],
                          "TRV_30": rvbc[3][1][x][z],
                          "TRV_01": rvbc[4][1][x][z],
                          "TRV_11": rvbc[5][1][x][z],
                          "TRV_21": rvbc[6][1][x][z],
                          "TRV_31": rvbc[7][1][x][z],
                          "TRV_02": rvbc[8][1][x][z],
                          "TRV_12": rvbc[9][1][x][z],
                          "TRV_22": rvbc[10][1][x][z],
                          "TRV_32": rvbc[11][1][x][z]
                    }
                )
                
    
            
                    
        p = (i + 1)/len(player_id)
        print(str(round(100*p, 1)) + '%')
          
    print()      
    print('Saving to cloud - this should take about one minute...')
    print()
              
    player_rv = pd.DataFrame(rows)
    
    np.save('zone_maps_' + year + '.npy', np.array(zone_rows, dtype=float), allow_pickle=True)
    np.save('loc_maps_' + year + '.npy', np.array(loc_rows, dtype=float), allow_pickle=True)
    player_rv.to_csv('player_rv_' + year + '.csv', index = False)
    
    print('Done!')
    
    return player_rv
    
# calculate swing/take runs
def swing_take(year, pitch_data, league_rv, player_rv):
    
    
    ###########################################################################
    ######################## Swing Decision Evaluation ########################
    ###########################################################################
    
    
    
    print()
    print('Evaluating Swing Decisons for', year)
    print()
    
    
    # initialize lists
    c_rows = []
    p_rows = []

    # timing
    timer_start = time.perf_counter()
    start_min = time.localtime()[4]
    start_hr = time.localtime()[3]
    n_pitches = 0
    total_pitches = len(pitch_data)

    # loop over all players
    for i in range(len(player_id)): 
        
        print(player_name[i], end = ' - ')
        
        # initialize values
        classic_xrv = 0
        
        c_good_swings = 0
        c_good_swing_runs = 0
        c_bad_swings = 0
        c_bad_swing_runs = 0
        
        c_good_takes = 0
        c_good_take_runs = 0
        c_bad_takes = 0
        c_bad_take_runs = 0
        
        
        player_xrv = 0
        
        p_good_swings = 0
        p_good_swing_runs = 0
        p_bad_swings = 0
        p_bad_swing_runs = 0
        
        p_good_takes = 0
        p_good_take_runs = 0
        p_bad_takes = 0
        p_bad_take_runs = 0
        
        
        ns, nt = 0, 0
        
        
        
        # data for pitches to this player
        pitches = pitch_data[pitch_data.batter == player_id[i]]
        
        
        for index, row in pitches.iterrows():
            
            # determine location
            x = row.plate_x
            z = row.plate_z
            
            if pd.isna(x):
                continue
            
            # round appropriately to proper zone
            if x >= 0:
                x = round(round(math.floor(10*x)/10, 1) + 0.05, 2)
            if x < 0:
                x = round(round(math.ceil(10*x)/10, 1) + 0.05, 2)
            
            z = round(round(math.floor(10*z)/10, 1) + 0.05, 2)
            
            # assign out of range values to border
            if x < - 1.45: x = -1.45
            if x > 1.45: x = 1.45
            if z < 0.55: z = 0.55
            if z > 3.95: z = 3.95
                    
            # fetch league and player data for this location
            league_data = league_rv.loc[(league_rv.XLOC == x) & 
                                        (league_rv.ZLOC == z)]
            
            player_data = player_rv.loc[(player_rv.XLOC == x) & 
                                        (player_rv.ZLOC == z) &
                                        (player_rv.ID == player_id[i])]
            
            # determine count
            b = row.balls
            if b > 3: b = 3
            s = row.strikes
            if s > 2: s = 2
            
            c = str(b) + str(s)
        
        
            # classic expected run value (using league stats)
            classic_xrv = classic_xrv + float(league_data['RV_' + c])
            
            # player expected run value (using player stats)
            league_swing = float(league_data['SWING_' + c])
            player_srv = float(player_data['SRV_' + c])
            league_trv = float(league_data['TRV_' + c])
            player_xrv = player_xrv + league_swing*player_srv + (1 - league_swing)*league_trv
            
            
            # classic actual run value for swings and takes
            classic_srv = float(league_data['SRV_' + c])
            classic_trv = float(league_data['TRV_' + c])
            
            # player actual run value for swings and takes
            player_srv = float(player_data['SRV_' + c])
            player_trv = float(player_data['TRV_' + c])
            
            
            # if the player swung
            if row.description in swing_types:
                
                ns = ns + 1
                
                if classic_srv > classic_trv:
                    c_good_swings = c_good_swings + 1
                    c_good_swing_runs = c_good_swing_runs + classic_srv
                else:
                    c_bad_swings = c_bad_swings + 1
                    c_bad_swing_runs = c_bad_swing_runs + classic_srv
                    
                    
                if player_srv > player_trv:
                    p_good_swings = p_good_swings + 1
                    p_good_swing_runs = p_good_swing_runs + player_srv
                else:
                    p_bad_swings = p_bad_swings + 1
                    p_bad_swing_runs = p_bad_swing_runs + player_srv
            
            
            # if the player did not swing
            if row.description in take_types:

                nt = nt + 1
                
                if classic_trv > classic_srv:
                    c_good_takes = c_good_takes + 1
                    c_good_take_runs = c_good_take_runs + classic_trv
                else:
                    c_bad_takes = c_bad_takes + 1
                    c_bad_take_runs = c_bad_take_runs + classic_trv
                    
                    
                if player_trv > player_srv:
                    p_good_takes = p_good_takes + 1
                    p_good_take_runs = p_good_take_runs + player_trv
                else:
                    p_bad_takes = p_bad_takes + 1
                    p_bad_take_runs = p_bad_take_runs + player_trv

    
        csrv = c_good_swing_runs + c_bad_swing_runs
        ctrv = c_good_take_runs + c_bad_take_runs
        n_p = round(ns + nt)
        c_sel = (c_good_takes/(c_good_takes + c_bad_swings))*100
        c_ag = (c_bad_takes/(c_bad_takes + c_good_swings))*100
        
        c_rows.append(
            {
                'NAME': player_name[i],
                'ID': player_id[i],
                'N_SWINGS': ns,
                'N_TAKES': nt,
                'N_P': n_p,
                'GOOD_SWINGS': c_good_swings,
                'G%S': round(c_good_swings/ns*100, 1),
                'GS%': round(c_good_swings/n_p*100, 1),
                'GS_RV': round(c_good_swing_runs, 1),
                'BAD_SWINGS': c_bad_swings,
                'B%S': round(c_bad_swings/ns*100, 1),
                'BS%': round(c_bad_swings/n_p*100, 1),
                'BS_RV': round(c_bad_swing_runs, 1),
                'SRV': round(csrv, 1),
                'GOOD_TAKES': c_good_takes,
                'G%T': round(c_good_takes/nt*100, 1),
                'GT%': round(c_good_takes/n_p*100, 1),
                'GT_RV': round(c_good_take_runs, 1),
                'BAD_TAKES': c_bad_takes,
                'B%T': round(c_bad_takes/nt*100, 1),
                'BT%': round(c_bad_takes/n_p*100, 1),
                'BT_RV': round(c_bad_take_runs, 1),
                'TRV': round(ctrv, 1),
                'EXP_RV': round(classic_xrv, 1),
                'TOT_RV': round(csrv + ctrv, 1),
                'SWTR': round(csrv + ctrv - classic_xrv, 1),
                'SWTR_Per650': round((csrv + ctrv - classic_xrv)/n_p*2542, 1),
                'Correct%': round((c_good_swings + c_good_takes)/n_p*100, 1),
                'Selective%': round(c_sel, 1),
                'OverAgression%': round(c_ag, 1),
                'SEAGER': round(c_sel - c_ag, 1)
            }
        )
        
        
        psrv = p_good_swing_runs + p_bad_swing_runs
        ptrv = p_good_take_runs + p_bad_take_runs
        p_sel = (p_good_takes/(p_good_takes + p_bad_swings))*100
        p_ag = (p_bad_takes/(p_bad_takes + p_good_swings))*100
        
        p_rows.append(
            {
                'NAME': player_name[i],
                'ID': player_id[i],
                'N_SWINGS': ns,
                'N_TAKES': nt,
                'N_P': n_p,
                'GOOD_SWINGS': p_good_swings,
                'G%S': round(p_good_swings/ns*100, 1),
                'GS%': round(p_good_swings/n_p*100, 1),
                'GS_RV': round(p_good_swing_runs, 1),
                'BAD_SWINGS': p_bad_swings,
                'B%S': round(p_bad_swings/ns*100, 1),
                'BS%': round(p_bad_swings/n_p*100, 1),
                'BS_RV': round(p_bad_swing_runs, 1),
                'SRV': round(psrv, 1),
                'GOOD_TAKES': p_good_takes,
                'G%T': round(p_good_takes/nt*100, 1),
                'GT%': round(p_good_takes/n_p*100, 1),
                'GT_RV': round(p_good_take_runs, 1),
                'BAD_TAKES': p_bad_takes,
                'B%T': round(p_bad_takes/nt*100, 1),
                'BT%': round(p_bad_takes/n_p*100, 1),
                'BT_RV': round(p_bad_take_runs, 1),
                'TRV': round(ptrv, 1),
                'EXP_RV': round(player_xrv, 1),
                'TOT_RV': round(psrv + ptrv, 1),
                'SWTR': round(psrv + ptrv - player_xrv, 1),
                'SWTR_Per650': round((psrv + ptrv - player_xrv)/n_p*2542, 1),
                'Correct%': round((p_good_swings + p_good_takes)/n_p*100, 1),
                'Selective%': round(p_sel, 1),
                'OverAgression%': round(p_ag, 1),
                'SEAGER': round(p_sel - p_ag, 1)
            }
        )
    
    
        n_pitches = n_pitches + n_p
        
        now = time.perf_counter()
        p = n_pitches/total_pitches
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

    # finish time
    tot_time = time.perf_counter() - timer_start
    hours = str(math.floor(tot_time/3600))
    mins = str(round(tot_time % 3600 / 60))
    print()
    if hours == '0':
        print('This operation took', mins, 'minutes.')
    else:
        if mins == '1':
            print('This operation took', hours, 'hours and one minute.')
        
        else:
            print('This operation took', hours, 'hours and', mins, 'minutes.')

    # percentiles
    def percentile(col, x):
        return round(stats.percentileofscore(col, x))

    classic_st['Total_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SWTR'], x.SWTR), axis = 1)
    classic_st['Rate_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SWTR_Per650'], x.SWTR_Per650), axis = 1)

    player_st['Total_Percentile'] = player_st.apply(lambda x: percentile(player_st['SWTR'], x.SWTR), axis = 1)
    player_st['Rate_Percentile'] = player_st.apply(lambda x: percentile(player_st['SWTR_Per650'], x.SWTR_Per650), axis = 1)


    # save to csv
    classic_st.to_csv('classic_st_' + year + '.csv')
    player_st.to_csv('player_st_' + year + '.csv')


    return classic_st, player_st

# combine into one
def full_process(year):
    year, pitch_data = get_pitch_data(year)
    league_rv = get_league_data(year, pitch_data)
    player_rv_z = get_player_data(year, pitch_data)
    player_rv = player_heatmap(year, player_rv_z)
    classic_st, player_st = swing_take(year, pitch_data, league_rv, player_rv)

full_process(2021)
full_process(2022)
full_process(2023)
full_process(2024)
