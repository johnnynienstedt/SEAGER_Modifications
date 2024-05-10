#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 26 22:05:01 2024

@author: johnnynienstedt
"""

#
# Make heatmaps
# Johnny Nienstedt 2/23/24
#
# Changed to rolling method 3/15
#

# This program follows player_data.py This program numerically solves
# laplace's equation for a 'heat map' of the strike zone for each player. This
# is necessary because each player only has so much raw data, so it is better
# to obtain that data in large zones and then mesh the data together to get a 
# more sensitive model. After icorporating np.roll() for numerical solving,
# this program only takes a couple minutes to run. Be aware, this program 
# produces CSV files around 700 MB.

import numpy as np
import pandas as pd

def player_heatmap(year):
    
    year = str(year)
    
    player_pref = pd.read_csv('player_pref_' + year + '.csv')
    pdat = pd.read_csv('players_' + year + '.csv')
    
    player_id = list(pdat['player_id'])
    player_name = list(pdat['player_name'])
    
    # strike zone dimensions
    zone_height = 35
    zone_width = 30
    
    # number of iterations for numerical solution
    n_iter = 10
    
    # Initialize rows of dataframe
    rows = []
    zone_rows = []
    loc_rows = []
    
    # initialize arrays
    
    for i in range(len(player_id)):
        print(player_name[i], end = ' - ')
        
        # initialize list to hold results for all counts (one for each player)
        rvbc = []
        
        for b in range(4):
            for s in range(3):
                
                count = str(b) + str(s)
                n_p = player_pref.at[i + 1, 'N_P']
                
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
                        a = 'SWING_'
                    if action == 't':
                        a = 'TAKE_'
                    if action == 'd':
                        a = 'DELTA_'
                    
                    # initial conditions
                    z1 = player_pref.at[i*13, a + count]
                    z2 = player_pref.at[i*13 + 1, a + count]
                    z3 = player_pref.at[i*13 + 2, a + count]
                    z4 = player_pref.at[i*13 + 3, a + count]
                    z5 = player_pref.at[i*13 + 4, a + count]
                    z6 = player_pref.at[i*13 + 5, a + count]
                    z7 = player_pref.at[i*13 + 6, a + count]
                    z8 = player_pref.at[i*13 + 7, a + count]
                    z9 = player_pref.at[i*13 + 8, a + count]
                    z11 = player_pref.at[i*13 + 9, a + count]
                    z12 = player_pref.at[i*13 + 10, a + count]
                    z13 = player_pref.at[i*13 + 11, a + count]
                    z14 = player_pref.at[i*13 + 12, a + count]
                    
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
                        
                        # delta_rv[x1:x2, y3:y4] = z1
                        # delta_rv[x2:x3, y3:y4] = z2
                        # delta_rv[x3:x4, y3:y4] = z3
                        # delta_rv[x1:x2, y2:y3] = z4
                        # delta_rv[x2:x3, y2:y3] = z5
                        # delta_rv[x3:x4, y2:y3] = z6
                        # delta_rv[x1:x2, y1:y2] = z7
                        # delta_rv[x2:x3, y1:y2] = z8
                        # delta_rv[x3:x4, y1:y2] = z9
                    
                    return rv_map
    
                # For plotting purposes
                set_conds(swing_rv, 's')
                set_conds(take_rv, 's')
                set_conds(delta_rv, 's')
                
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
    
                
                #
                # Delta RV
                #
                
                set_conds(delta_rv, 'd')
                m = delta_rv.mean()
    
                # calculate delta_rv using relaxation method
                for n in range(n_iter):
                    delta_rv = 0.25*(np.roll(delta_rv, zone_height - 1, axis = 1) + np.roll(delta_rv, 1 - zone_height, axis = 1) + np.roll(delta_rv, zone_width - 1, axis = 0) + np.roll(delta_rv, 1 - zone_width, axis = 0))
                    delta_rv = set_conds(delta_rv, 'd', reset = True)
                
                delta_rv = delta_rv - delta_rv.mean() + m
                
                rvbc.append([swing_rv, take_rv, delta_rv])
                
                # For more plotting purposes:
                loc_rows.append([swing_rv, take_rv, delta_rv])
                
    
    
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
                          "SWING_00": rvbc[0][0][x][z],
                          "SWING_10": rvbc[1][0][x][z],
                          "SWING_20": rvbc[2][0][x][z],
                          "SWING_30": rvbc[3][0][x][z],
                          "SWING_01": rvbc[4][0][x][z],
                          "SWING_11": rvbc[5][0][x][z],
                          "SWING_21": rvbc[6][0][x][z],
                          "SWING_31": rvbc[7][0][x][z],
                          "SWING_02": rvbc[8][0][x][z],
                          "SWING_12": rvbc[9][0][x][z],
                          "SWING_22": rvbc[10][0][x][z],
                          "SWING_32": rvbc[11][0][x][z],
                          "TAKE_00": rvbc[0][1][x][z],
                          "TAKE_10": rvbc[1][1][x][z],
                          "TAKE_20": rvbc[2][1][x][z],
                          "TAKE_30": rvbc[3][1][x][z],
                          "TAKE_01": rvbc[4][1][x][z],
                          "TAKE_11": rvbc[5][1][x][z],
                          "TAKE_21": rvbc[6][1][x][z],
                          "TAKE_31": rvbc[7][1][x][z],
                          "TAKE_02": rvbc[8][1][x][z],
                          "TAKE_12": rvbc[9][1][x][z],
                          "TAKE_22": rvbc[10][1][x][z],
                          "TAKE_32": rvbc[11][1][x][z],
                          "DELTA_00": rvbc[0][2][x][z],
                          "DELTA_10": rvbc[1][2][x][z],
                          "DELTA_20": rvbc[2][2][x][z],
                          "DELTA_30": rvbc[3][2][x][z],
                          "DELTA_01": rvbc[4][2][x][z],
                          "DELTA_11": rvbc[5][2][x][z],
                          "DELTA_21": rvbc[6][2][x][z],
                          "DELTA_31": rvbc[7][2][x][z],
                          "DELTA_02": rvbc[8][2][x][z],
                          "DELTA_12": rvbc[9][2][x][z],
                          "DELTA_22": rvbc[10][2][x][z],
                          "DELTA_32": rvbc[11][2][x][z]
                    }
                )
                
    
            
                    
        p = (i + 1)/len(player_id)
        print(str(round(100*p, 1)) + '%')
          
    print()      
    print('Saving to cloud - this should take about one minute...')
    print()
              
    player_rv = pd.DataFrame(rows)
      
    player_rv['RV_00'] = player_rv['SWING_00'] - player_rv['TAKE_00']
    player_rv['RV_10'] = player_rv['SWING_10'] - player_rv['TAKE_10']
    player_rv['RV_20'] = player_rv['SWING_20'] - player_rv['TAKE_20']
    player_rv['RV_30'] = player_rv['SWING_30'] - player_rv['TAKE_30']
    player_rv['RV_01'] = player_rv['SWING_01'] - player_rv['TAKE_01']
    player_rv['RV_11'] = player_rv['SWING_11'] - player_rv['TAKE_11']
    player_rv['RV_21'] = player_rv['SWING_21'] - player_rv['TAKE_21']
    player_rv['RV_31'] = player_rv['SWING_31'] - player_rv['TAKE_31']
    player_rv['RV_02'] = player_rv['SWING_02'] - player_rv['TAKE_02']
    player_rv['RV_12'] = player_rv['SWING_12'] - player_rv['TAKE_12']
    player_rv['RV_22'] = player_rv['SWING_22'] - player_rv['TAKE_22']
    player_rv['RV_32'] = player_rv['SWING_32'] - player_rv['TAKE_32']
    
    np.save('zone_maps_' + year + '.npy', np.array(zone_rows, dtype=float), allow_pickle=True)
    np.save('loc_maps_' + year + '.npy', np.array(loc_rows, dtype=float), allow_pickle=True)
    player_rv.to_csv('player_rv_' + year + '.csv', index = False)
    

player_heatmap(2021)
player_heatmap(2022)
player_heatmap(2023)
player_heatmap(2024)





