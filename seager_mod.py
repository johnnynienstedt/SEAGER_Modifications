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
from scipy import stats
from tqdm import tqdm
import pybaseball

# enable caching
pybaseball.cache.enable()

# scrape all pitch data
def get_pitch_data():
    
    ###########################################################################
    ############################# Get Pitch Data ##############################
    ###########################################################################

    pitch_data_2021 = pybaseball.statcast('2021-04-01', '2021-10-03')
    pitch_data_2022 = pybaseball.statcast('2022-04-07', '2022-10-05')
    pitch_data_2023 = pybaseball.statcast('2023-03-30', '2023-10-01')
    pitch_data_2024 = pybaseball.statcast('2024-03-28', '2024-9-27')
    year_pitch_data = [pitch_data_2021, pitch_data_2022, pitch_data_2023, pitch_data_2024]
    all_pitch_data = pd.concat([pitch_data_2021, pitch_data_2022, pitch_data_2023, pitch_data_2024])

    return all_pitch_data, year_pitch_data

# get league data for all years
def get_league_data(pitch_data):
    
    ###########################################################################
    ############################# Get League Data #############################
    ###########################################################################
    
    print()
    print('Gathering League Data')
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
    
    
    global swing_types, take_types, bunt_types
    
    swing_types = ['hit_into_play', 'foul', 'swinging_strike', 'foul_tip', 
                   'swinging_strike_blocked', 'swinging_pitchout',
                   'foul_pitchout']
    take_types = ['ball', 'called_strike', 'blocked_ball', 'hit_by_pitch', 
                  'pitchout']
    bunt_types = ['missed_bunt', 'foul_bunt', 'foul_tip_bunt']
    
    
    # initialize data frame and array
    league_rv = np.empty([4,4,3,13])
    # indices are:
        # data type (rv = 0, swing_rate = 1, swing_rv = 2, take_rv = 3)
        # balls
        # strikes
        # MLBAM zone
    
    #
    # evaluate pitches in range of MLBAM zones (2.2 ft wide x 3 ft tall)
    #            
    
    # get swing RV based on contact%, whiff%, and xWOBACON
    for j in tqdm(range(13)):
        
        if j < 9: zone = j + 1
        else: zone = j + 2
            
        for s in range(3):
            for b in range(4):
                
                # data for pitches here in this count
                pitches = pitch_data[(pitch_data.zone == zone) &
                                     (pitch_data.balls == b) &
                                     (pitch_data.strikes == s)]
                n = len(pitches)
                
                
                # pitches swung at
                swings = pitches[pitches.description.isin(swing_types)]
                
                # number of swings
                n_swings = len(swings)
                
                if n != 0:
                    swing_rate = n_swings/n
                else:
                    swing_rate = 0
                
                league_rv[1][b][s][j] = swing_rate
                
                
                # contact & foul ball percentage
                if n_swings != 0:
                    contact = sum(swings.description == 'hit_into_play')/n_swings
                    foul = sum(swings.description == 'foul')/n_swings
                    whiff = 1 - contact - foul
                else:
                    contact, foul, whiff = 0, 0, 0
                            
                # observed run value on balls in play
                if contact != 0:
                    xwobacon = swings[swings.description == 'hit_into_play']['estimated_woba_using_speedangle'].fillna(0).mean()
                    bip_rv = 0.6679*xwobacon - 0.192
                else:
                    bip_rv  = 0
                    
                # calculated run value for swings, based on RE24
                if s == 2:
                    swing_rv = (contact*bip_rv + whiff*strike_rv[b][s])
                else:
                    swing_rv = (contact*bip_rv + (whiff + foul)*strike_rv[b][s])
                
                league_rv[2][b][s][j] = swing_rv
                
    
    
    ###########################################################################
    ############################## Make Heatmaps ##############################
    ###########################################################################
    
    
    print()
    print()
    print('Making Heatmaps')
    print()
    
    # strike zone dimensions
    zone_height = 35
    zone_width = 30
    
    # number of iterations for numerical solution
    n_iter = 10
    
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
    
    # Initialize arrays
    league_zonemaps = np.empty([4, 4, 3, zone_width, zone_height])
    league_heatmaps = np.empty([5, 4, 3, zone_width, zone_height])
    # ^ extra 5th pouch is for cs%
    
    # first get called strike % (more granular than swing rv)
    for X in tqdm(range(-15, 15)):
        x = X/13.5
        xx = (X + 1)/13.5
        for Z in range(35):
            z = (Z*32/35 + 14)/12
            zz = ((Z + 1)*32/35 + 14)/12
            
            pitches = pitch_data[(pitch_data.plate_x >= x) &
                                 (pitch_data.plate_x < xx) &
                                 (pitch_data.plate_z >= z) &
                                 (pitch_data.plate_z < zz)]
            
            # pitches taken
            takes = pitches[pitches.description.isin(take_types)]
            
            # percentage of taken pitches called stikes
            n_takes = len(takes)
            cs = sum(takes.description == 'called_strike')/n_takes
            
            league_heatmaps[4][0][0][X + 15][Z] = cs
    
            # different values of TRV for each count
            for s in range(3):
                for b in range(4):
                    
                    # and calculate TRV using RE24
                    take_rv = cs*strike_rv[b,s] + (1 - cs)*ball_rv[b,s]
                    
                    # append to array
                    league_heatmaps[3][b][s][X+15][Z] = take_rv
    
    
    # now merge zone data to make swing heatmaps
    for i in range(1,3):
        for b in range(4):
            for s in range(3):
                
                # initialize heat map
                rv_map = np.zeros([zone_width, zone_height])
                
                # initial condition set/reset function
                def set_conds(rv_map, reset = False):
                    
                    # initial conditions
                    z1 = league_rv[i][b][s][0]
                    z2 = league_rv[i][b][s][1]
                    z3 = league_rv[i][b][s][2]
                    z4 = league_rv[i][b][s][3]
                    z5 = league_rv[i][b][s][4]
                    z6 = league_rv[i][b][s][5]
                    z7 = league_rv[i][b][s][6]
                    z8 = league_rv[i][b][s][7]
                    z9 = league_rv[i][b][s][8]
                    z11 = league_rv[i][b][s][9]
                    z12 = league_rv[i][b][s][10]
                    z13 = league_rv[i][b][s][11]
                    z14 = league_rv[i][b][s][12]
                    
                    
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
                        rv_map[x0,y4:y5] = z11
                        rv_map[x0:x1,y5-1] = z11
                        
                        rv_map[x4:x5,y5-1] = z12
                        rv_map[x5-1,y4:y5] = z12
                        
                        rv_map[x0:x1,y0] = z13
                        rv_map[x0,y0:y1] = z13
                        
                        rv_map[x5-1,y0:y1] = z14
                        rv_map[x4:x5,y0] = z14
                        
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
    
                # set initial conditions
                rv_map = set_conds(rv_map)
                league_zonemaps[i][b][s] = rv_map

    
                # make heatmaps using np.roll method
                for n in range(n_iter):
                    rv_map = 0.25*(np.roll(rv_map, zone_height - 1, axis = 1) + np.roll(rv_map, 1 - zone_height, axis = 1) + np.roll(rv_map, zone_width - 1, axis = 0) + np.roll(rv_map, 1 - zone_width, axis = 0))
                    rv_map = set_conds(rv_map, reset = True)  
                
                # append heatmaps to arrays
                league_heatmaps[i][b][s] = rv_map
                       
    # calculate expected RV by location and count
    for s in range(3):
        for b in range(4):
            swing_rate = league_heatmaps[1][b][s]
            take_rate = 1 - swing_rate
            swing_rv = league_heatmaps[2][b][s]
            take_rv = league_heatmaps[3][b][s]
            
            xrv = swing_rate*swing_rv + take_rate*take_rv
            
            league_heatmaps[0][b][s] = xrv
              
    np.save('league_heatmaps.npy', np.array(league_heatmaps, dtype=float), allow_pickle=True)
    np.save('league_zonemaps.npy', np.array(league_zonemaps, dtype=float), allow_pickle=True)
    
    return league_heatmaps
    
# get player data
def get_player_data(pitch_data):
    
    
    ###########################################################################
    ############################# Get Player Data #############################
    ###########################################################################
    
    
    
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
    
    
    global swing_types, take_types, bunt_types
    
    swing_types = ['hit_into_play', 'foul', 'swinging_strike', 'foul_tip', 
                   'swinging_strike_blocked', 'swinging_pitchout',
                   'foul_pitchout']
    take_types = ['ball', 'called_strike', 'blocked_ball', 'hit_by_pitch', 
                  'pitchout']
    bunt_types = ['missed_bunt', 'foul_bunt', 'foul_tip_bunt']
    
    
    print()
    print("Gathering Player Data")
    print()
        
    
    # load player data
    pdat_2021 = pd.read_csv('players_2021.csv')
    pdat_2022 = pd.read_csv('players_2022.csv')
    pdat_2023 = pd.read_csv('players_2023.csv')
    pdat_2024 = pd.read_csv('players_2024.csv')

    pdat = pd.concat([pdat_2021, pdat_2022, pdat_2023, pdat_2024], ignore_index=True)

    pdat = pd.DataFrame({
                        'ID': pdat['player_id'], 
                        'Name': pdat['player_name']
                        })

    pdat = pdat.drop_duplicates()

    player_id = list(pdat['ID'])
    
    # intialise list of dictionaries
    player_rv = np.empty([len(player_id), 4, 3, 13])
    
    # Get batter stats for each zone to be converted to RV
    for i in tqdm(range(len(player_id))):         
        # get player rv for each zone
        for j in range(13):
        
            if j < 9: zone = j + 1
            else: zone = j + 2
            
            # data for pitches in this zone to this player
            pitches = pitch_data[(pitch_data.batter == player_id[i]) & 
                                   (pitch_data.zone == zone)]
                        
            
            # pitches swung at
            swings = pitches[pitches.description.isin(swing_types)]
            
            # number of swings
            n_swings = len(swings)
            
            # contact & foul ball percentage
            if n_swings != 0:
                contact = sum(swings.description == 'hit_into_play')/n_swings
                foul = sum(swings.description == 'foul')/n_swings
                whiff = 1 - contact - foul
            else:
                contact, foul, whiff = 0, 0, 0
                
            # observed run value on balls in play
            if contact != 0:
                xwobacon = swings[swings.description == 'hit_into_play']['estimated_woba_using_speedangle'].fillna(0).mean()
                bip_rv = 0.6679*xwobacon - 0.192
            else:
                bip_rv  = 0


            # calculated run value for swings, based on RE24
            for s in range(3):
                for b in range(4):
                    
                    # swings
                    if s == 2:
                        swing_rv = contact*bip_rv + whiff*strike_rv[b][s]
                    else:
                        swing_rv = contact*bip_rv + (whiff + foul)*strike_rv[b][s]
                    
                    player_rv[i][b][s][j] = swing_rv
    
    
    
    ###########################################################################
    ############################## Make Heatmaps ##############################
    ###########################################################################
    
    
    
    print()
    print("Making Heatmaps")
    print()
    
    # player list
    player_name = list(pdat['Name'])
    player_id = list(pdat['ID'])
    n_players = len(player_name)
    
    # strike zone dimensions
    zone_height = 35
    zone_width = 30
    
    # number of iterations for numerical solution
    n_iter = 10
    
    # Initialize array
    player_heatmaps = np.empty([n_players, 4, 3, 11, zone_width, zone_height])
    
    for i in tqdm(range(len(player_id))):        
        for b in range(4):
            for s in range(3):
                
                # initialize heat map
                swing_rv = np.zeros([zone_width, zone_height])
                
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
                
                # initial conditions
                z1 = player_rv[i][b][s][0]
                z2 = player_rv[i][b][s][1]
                z3 = player_rv[i][b][s][2]
                z4 = player_rv[i][b][s][3]
                z5 = player_rv[i][b][s][4]
                z6 = player_rv[i][b][s][5]
                z7 = player_rv[i][b][s][6]
                z8 = player_rv[i][b][s][7]
                z9 = player_rv[i][b][s][8]
                z11 = player_rv[i][b][s][9]
                z12 = player_rv[i][b][s][10]
                z13 = player_rv[i][b][s][11]
                z14 = player_rv[i][b][s][12]

                
                # initial condition set/reset function
                def set_conds(rv_map, reset = False):
                    
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
                        rv_map[x0,y4:y5] = z11
                        rv_map[x0:x1,y5-1] = z11
                        
                        rv_map[x4:x5,y5-1] = z12
                        rv_map[x5-1,y4:y5] = z12
                        
                        rv_map[x0:x1,y0] = z13
                        rv_map[x0,y0:y1] = z13
                        
                        rv_map[x5-1,y0:y1] = z14
                        rv_map[x4:x5,y0] = z14
                        
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
    
                # set initial conditions
                swing_rv = set_conds(swing_rv)
                player_heatmaps[i][b][s][0] = swing_rv
    
                # make heatmap using np.roll method
                for n in range(n_iter):
                    swing_rv = 0.25*(np.roll(swing_rv, zone_height - 1, axis = 1) + np.roll(swing_rv, 1 - zone_height, axis = 1) + np.roll(swing_rv, zone_width - 1, axis = 0) + np.roll(swing_rv, 1 - zone_width, axis = 0))
                    swing_rv = set_conds(swing_rv, reset = True)       
                    player_heatmaps[i][b][s][n + 1] = swing_rv
                
                    
              
    np.save('player_heatmaps.npy', np.array(player_heatmaps, dtype=float), allow_pickle=True)
    
    return player_heatmaps
    
# evaluate swing/take decisions
def swing_take(year, year_pitch_data, league_heatmaps, player_heatmaps):
    
    
    ###########################################################################
    ######################## Swing Decision Evaluation ########################
    ###########################################################################
    
    
    
    print()
    print('Evaluating Swing Decisons for', year)
    print()
    
    # select proper year
    pitch_data = year_pitch_data[int(year) - 2021]
    pdat = pd.read_csv('players_' + year + '.csv')
    player_name = pdat.player_name
    player_id = pdat.player_id

    # RE24 values
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
        
    swing_types = ['hit_into_play', 'foul', 'swinging_strike', 'foul_tip', 
                   'swinging_strike_blocked', 'swinging_pitchout',
                   'foul_pitchout']
    take_types = ['ball', 'called_strike', 'blocked_ball', 'hit_by_pitch', 
                  'pitchout']
    bunt_types = ['missed_bunt', 'foul_bunt', 'foul_tip_bunt']


    # initialize lists
    c_rows = [None] * len(player_id)
    p_rows = [None] * len(player_id)

    # loop over all players
    for i in tqdm(range(len(player_id))): 
                
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
        
        
        xlist = []
        zlist = []
        for X in range(-15, 15):
            xlist.append(X/13.5 + 1/27)
        for Z in range(35):
            zlist.append((Z*32/35 + 14)/12 + 1/27)
        
        # data for pitches to this player
        pitches = pitch_data[pitch_data.batter == player_id[i]]
        
        for index, row in pitches.iterrows():
            
            # determine location
            x = row.plate_x
            z = row.plate_z
            
            if pd.isna(x):
                continue
            
            if row.description in bunt_types:
                continue
            
            # round appropriately to proper zone
            x = min(xlist, key=lambda d:abs(d-x))
            z = min(zlist, key=lambda d:abs(d-z))
            
            # get proper index for matrix retrieval
            ix = xlist.index(x)
            iz = zlist.index(z)
            
            # determine count
            b = row.balls
            s = row.strikes
            if b > 3: b = 3
            if s > 2: s = 2
            
            #
            # fetch data from league and player heatmaps
            #
        
            # classic actual run value for swings and takes
            classic_srv = league_heatmaps[2][b][s][ix][iz]
            trv = league_heatmaps[3][b][s][ix][iz]
            
            # player actual run value for swings (trv is the same)
            player_srv = player_heatmaps[i][b][s][ix][iz]
            
            # classic expected run value (using league stats)
            classic_xrv = classic_xrv + league_heatmaps[0][b][s][ix][iz]
            
            # player expected run value (using player stats)
            league_swing = league_heatmaps[1][b][s][ix][iz]
            player_xrv = player_xrv + league_swing*player_srv + (1 - league_swing)*trv
            
            
            #
            # evaluate swing decision
            #
            
            bias = 0
            
            # if the player swung
            if row.description in swing_types:
                
                ns = ns + 1
                
                # classic
                if classic_srv > trv + bias:
                    c_good_swings = c_good_swings + 1
                    c_good_swing_runs = c_good_swing_runs + classic_srv
                else:
                    c_bad_swings = c_bad_swings + 1
                    c_bad_swing_runs = c_bad_swing_runs + classic_srv
                    
                    
                # player
                if player_srv > trv + bias:
                    p_good_swings = p_good_swings + 1
                    p_good_swing_runs = p_good_swing_runs + player_srv
                else:
                    p_bad_swings = p_bad_swings + 1
                    p_bad_swing_runs = p_bad_swing_runs + player_srv
            
            
            # if the player did not swing
            if row.description in take_types:

                nt = nt + 1
                
                if trv > classic_srv + bias:
                    c_good_takes = c_good_takes + 1
                    c_good_take_runs = c_good_take_runs + trv
                else:
                    c_bad_takes = c_bad_takes + 1
                    c_bad_take_runs = c_bad_take_runs + trv
                    
                    
                if trv > player_srv + bias:
                    p_good_takes = p_good_takes + 1
                    p_good_take_runs = p_good_take_runs + trv
                else:
                    p_bad_takes = p_bad_takes + 1
                    p_bad_take_runs = p_bad_take_runs + trv
                    
                    
                    
        csrv = c_good_swing_runs + c_bad_swing_runs
        ctrv = c_good_take_runs + c_bad_take_runs
        n_p = round(ns + nt)
        
        # hittable pitches taken
        c_hpt = c_bad_takes/nt*100  
        # weird selectiveness metric
        c_sel = c_good_takes/(c_good_takes + c_good_swings)*100
        
        c_rows[i] = {
                    'NAME': player_name[i],
                    'ID': player_id[i],
                    'N_SWINGS': ns,
                    'N_TAKES': nt,
                    'N_P': n_p,
                    'G%S': round(c_good_swings/ns*100, 1),
                    'GS_RV': round(c_good_swing_runs, 1),
                    'B%S': round(c_bad_swings/ns*100, 1),
                    'BS_RV': round(c_bad_swing_runs, 1),
                    'SRV': round(csrv, 1),
                    'G%T': round(c_good_takes/nt*100, 1),
                    'GT_RV': round(c_good_take_runs, 1),
                    'B%T': round(c_hpt, 1),
                    'BT_RV': round(c_bad_take_runs, 1),
                    'TRV': round(ctrv, 1),
                    'TOT_RV': round(csrv + ctrv, 1),
                    'EXP_RV': round(classic_xrv, 1),
                    'SWTR': round(csrv + ctrv - classic_xrv, 1),
                    'SWTR_Per650': round((csrv + ctrv - classic_xrv)/n_p*2542, 1),
                    'EXP_RV+': round(player_xrv, 1),
                    'SWTR+': round(csrv + ctrv - player_xrv, 1),
                    'SWTR_Per650+': round((csrv + ctrv - player_xrv)/n_p*2542, 1),
                    'Correct%': round((c_good_swings + c_good_takes)/n_p*100, 1),
                    'Selective': round(c_sel, 1),
                    'Agression': round(c_hpt, 1),
                    'SEAGER': round(c_sel - c_hpt, 1),
                    'L_SEAGER': round(c_good_swings/ns*100 - c_hpt, 1)
                    }
        
        
        psrv = p_good_swing_runs + p_bad_swing_runs
        ptrv = p_good_take_runs + p_bad_take_runs
        
        # hittable pitches taken
        p_hpt = p_bad_takes/nt*100  
        # weird selectiveness metric
        p_sel = p_good_takes/(p_good_takes + p_good_swings)*100
        
        p_rows[i] = {
                    'NAME': player_name[i],
                    'ID': player_id[i],
                    'N_SWINGS': ns,
                    'N_TAKES': nt,
                    'N_P': n_p,
                    'G%S': round(p_good_swings/ns*100, 1),
                    'GS_RV': round(p_good_swing_runs, 1),
                    'B%S': round(p_bad_swings/ns*100, 1),
                    'BS_RV': round(p_bad_swing_runs, 1),
                    'SRV': round(psrv, 1),
                    'G%T': round(p_good_takes/nt*100, 1),
                    'GT_RV': round(p_good_take_runs, 1),
                    'B%T': round(p_hpt, 1),
                    'BT_RV': round(p_bad_take_runs, 1),
                    'TRV': round(ptrv, 1),
                    'TOT_RV': round(psrv + ptrv, 1),
                    'EXP_RV': round(player_xrv, 1),
                    'SWTR': round(psrv + ptrv - player_xrv, 1),
                    'SWTR_Per650': round((psrv + ptrv - player_xrv)/n_p*2542, 1),
                    'Correct%': round((p_good_swings + p_good_takes)/n_p*100, 1),
                    'Selective': round(p_sel, 1),
                    'Agression': round(p_hpt, 1),
                    'SEAGER': round(p_sel - p_hpt, 1),
                    'L_SEAGER': round(p_good_swings/ns*100 - p_hpt, 1)
                    }
        
        
    # make dataframes
    classic_st = pd.DataFrame(c_rows)
    player_st = pd.DataFrame(p_rows)


    # percentiles
    def percentile(col, x):
        return round(stats.percentileofscore(col, x))

    classic_st['SEAGER_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SEAGER'], x.SEAGER), axis = 1)
    classic_st['Selective_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['Selective'], x.Selective), axis = 1)
    classic_st['Agression_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['Agression'], x.Agression), axis = 1)
    classic_st['SWTR_Percentile'] = classic_st.apply(lambda x: percentile(classic_st['SWTR_Per650'], x.SWTR_Per650), axis = 1)

    player_st['SEAGER_Percentile'] = player_st.apply(lambda x: percentile(player_st['SEAGER'], x.SEAGER), axis = 1)
    player_st['Selective_Percentile'] = player_st.apply(lambda x: percentile(player_st['Selective'], x.Selective), axis = 1)
    player_st['Agression_Percentile'] = player_st.apply(lambda x: percentile(player_st['Agression'], x.Agression), axis = 1)
    player_st['SWTR_Percentile'] = player_st.apply(lambda x: percentile(player_st['SWTR_Per650'], x.SWTR_Per650), axis = 1)

    classic_st['Agression_Percentile'] = 100 - classic_st['Agression_Percentile']
    player_st['Agression_Percentile'] = 100 - player_st['Agression_Percentile']


    # save to csv
    classic_st.to_csv('classic_st_' + year + '.csv')
    player_st.to_csv('player_st_' + year + '.csv')

    return classic_st, player_st


# run everything
all_pitch_data, year_pitch_data = get_pitch_data()
league_heatmaps = get_league_data(all_pitch_data)
player_heatmaps = get_player_data(all_pitch_data)
for year in range(2021, 2025):
    year = str(year)
    classic_st, player_st = swing_take(year, year_pitch_data, league_heatmaps,
                                        player_heatmaps)
