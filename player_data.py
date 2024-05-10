#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 11:09:22 2024

@author: johnnynienstedt
"""

#
# Retrieve all player data
# Johnny Nienstedt 2/25/24
#

# This script mirrors league_data.py but scrapes data for each player rather
# than the whole league. The goals are to set a baseline run value for each
# batter and to find their areas of strength and weakness in the strike zone.
# IIRC, this program takes about 12 hours to run with an uninterrupted internet
# connection.

import pandas as pd
import requests
import time
import math
import numpy as np


def get_pdata_by_year(year):
    
    year = str(year)
    
    # load data
    pdat = pd.read_csv('players' + year + '.csv')
    player_id = list(pdat['player_id'])
    player_name = list(pdat['player_name'])
    
    print('Acquiring player data for ' + year)
    
    # intialise list of dictionaries
    rows = []
    
    timer_start = time.perf_counter()
    start_min = time.localtime()[4]
    start_hr = time.localtime()[3]
    
    #
    # Get batter contact% and xWOBACON for each attack zone (and convert to RV)
    #
    for i in range(len(player_id)): 
        print(player_name[i], end = ' - ')
        
        for j in range(13):
            
            if j < 9: zone = j + 1
            else: zone = j + 2
            
            #
            # get contact%, xWOBACON, and RV (calculated from xWOBACON)
            #
            url = 'https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=hit%5C.%5C.into%5C.%5C.play%7C&hfZ=' + str(zone) + '%7C&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=' + year + '%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&batters_lookup%5B%5D=' + str(player_id[i]) + '&hfFlag=&metric_1=&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_metric1_lt=on&chk_metric2_lt=on&chk_zones=on&chk_metric1_gt=on&chk_metric2_gt=on&chk_swings=on&chk_stats_xwoba=on&chk_stats_batter_run_value_per_100=on#results'        
            t = requests.get(url).text
            
            skey = '<td class="tr-data align-right"><span>'
            ekey1 = '</span></td>\n                                <td class="tr-data align-right "><span>'
            ekey2 = '</span></td>\n                                    <td \n                                        class="tr-data align-right "\n                                    >\n                                        <span>\n                                            '
            ekey3 = '\n                                        </span>\n                                    </td>\n                                    <td \n                                        class="tr-data align-right "\n                                    >\n                                        <span>\n                                            '
            start = t.find(skey)
            end1 = t.find(ekey1)
            end2 = t.find(ekey2)
            end3 = t.find(ekey3)
            
            try:
                n_p = int(t[start + len(skey):end1])
                cont = round(float(t[end1 + len(ekey1):end2])/100, 4)
                xwob = round(float(t[end2 + len(ekey2):end3]), 4)
                crv = round((57.9713*xwob - 15.8091)/100, 4)
                
            except ValueError:
                n_p = 0
                cont = 0
                xwob = 0
                crv = 0
                foul = 0
    
    
            #
            # get fb%
            #
            url = 'https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=foul%7Cfoul%5C.%5C.bunt%7Cfoul%5C.%5C.pitchout%7C&hfZ=' +str(zone) + '%7C&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=' + year + '%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&batters_lookup%5B%5D=' + str(player_id[i]) + '&hfFlag=&metric_1=&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_zones=on&chk_swings=on&chk_stats_xwoba=on&chk_stats_batter_run_value_per_100=on#results'        
            t = requests.get(url).text
            
            skey = 'align-right column-sort"><span>'
            ekey = '</span></td>\n                                <td class="tr-data align-right"><span>'
            start1 = t.find(skey)
            end1 = t.find('</span></td>\n                                <td class="tr-data align-right"><span>')
            end2 = t.find('</span></td>\n                                <td class="tr-data align-right "><span>')
            
            try:
                fouls = int(t[start1 + len(skey):end1])
                tot = int(t[end1 + len(ekey):end2])
                foul = round(fouls/tot, 4)
                
            except ValueError:
                foul = 0
    
    
            new_row = {
                     "NAME": player_name[i],
                     "ID": player_id[i],
                     "ZONE": zone,
                     "N_P": n_p,
                     "CONTACT": cont,
                     "CRV": crv,
                     "FOUL": foul
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
    
    player_pref = pd.DataFrame(rows)
    
    
    #
    # calculate rv difference for swings vs takes by count
    #
    
    ball_rv = np.zeros([4,3])
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
    
    strike_rv = np.zeros([4,3])
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
    
    
    # assign cs% by zone (from actual data)
    def cs_by_zone(zone):
        cs_list = ['na', 0.776, 0.909, 0.802, 0.955, 1, 0.957, 0.874, 0.924, 0.823, 'na', 0.048, 0.076, 0.064, 0.047]
        return cs_list[zone]
    
    player_pref['CS'] = player_pref.apply(lambda x: cs_by_zone(x.ZONE), axis = 1)
    
    
    def calculate_rv(cs,cont,crv,foul,balls,strikes, sw_tk):
        
        rvs = strike_rv[balls][strikes]
        rvb = ball_rv[balls][strikes]
        if strikes == 2:
            swing_rv = round((cont*crv + (1-cont)*rvs), 4)
        else:
            swing_rv = round((cont*crv + (1-cont + foul)*rvs), 4)
    
        take_rv = round(cs*rvs + (1 - cs)*rvb, 4)
        tot_rv = round(swing_rv - take_rv, 4)
        
        if sw_tk == 'swing':
            return swing_rv
        
        if sw_tk == 'take':
            return take_rv
        
        if sw_tk == 'delta':
            return tot_rv
    
    for b in range(4):
        for s in range(3):
            c = str(b) + str(s)
            
            swing = 'SWING_' + c
            take = 'TAKE_' + c
            delta = 'DELTA_' + c
            
            player_pref[swing] = player_pref.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'swing'), axis = 1)
            player_pref[take] = player_pref.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'take'), axis = 1)
            player_pref[delta] = player_pref.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'delta'), axis = 1)
    
    player_pref.to_csv('player_pref_' + year + '.csv', index = False)
    
    tot_time = time.perf_counter() - timer_start
    hours = str(math.floor(tot_time/3600))
    mins = str(round(tot_time % 3600 / 60))
    print('This operation took', hours, 'hours and', mins, 'minutes.')



#get_pdata_by_year(2021)
#get_pdata_by_year(2022)
#get_pdata_by_year(2023)
#get_pdata_by_year(2024)



