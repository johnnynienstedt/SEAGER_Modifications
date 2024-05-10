#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 11:20:59 2024

@author: johnnynienstedt
"""

#
# First Data Acquisition for SEAGER2
# Johnny Nienstedt 2/20/24
#


# This script acquires and saves data on every pitch thrown in MLB from 2021
# to 2023. The goal of this script is to set a besaline for a) the overall run
# values (batter POV) of pitches as a function of location and b) the run 
# values for swings and takes at each location. This script takes approximately
# 8 hours to run on an RPI 5.


# user must install pandas if not already installed

import requests
import pandas as pd
import time
import numpy as np
import math

def get_data_by_year(year = 2023):
    
    year = str(year)
    
    print('Acquiring league data for ' + year)
    
    # time data acquisition
    timer_start = time.perf_counter()
    start_hr = time.localtime()[3]
    start_min = time.localtime()[4]
    
    # initialize data frame
    league_rv = pd.DataFrame(
        {
             "XLOC": ['NA'],
             "ZLOC": ['NA'],
             "RV_00": ['NA'],
             "RV_10": ['NA'],
             "RV_20": ['NA'],
             "RV_30": ['NA'],
             "RV_01": ['NA'],
             "RV_11": ['NA'],
             "RV_21": ['NA'],
             "RV_31": ['NA'],
             "RV_02": ['NA'],
             "RV_12": ['NA'],
             "RV_22": ['NA'],
             "RV_32": ['NA'],
             "CS": ['NA'],
             "CONTACT": ['NA'],
             "xWOBACON": ['NA'],
             "CRV": ['NA'],
             "FOUL": ['NA']
        }
    )
    
    #
    # find swing/take run values by location
    #
    
    # (SHOULD PROBABLY TRY TO ACCOUNT FOR BATTER HANDEDNESS IN SOME WAY)
    
    for X in range(-15,15):
        x = round(X/10, 2)
        for Z in range(5,40):
            z = round(Z/10, 2)
            
            
            #
            # get baseline rv for each count
            #
            counts = ['00', '10', '20', '30', '01', '11', '21', '31', '02', '12', '22', '32']
            rv = []
            for j in range(len(counts)):
                url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=" + counts[j] + "%7C&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=api_plate_x&metric_1_gt=" + str(x) + "&metric_1_lt=" + str(x + 0.1) + "&metric_2=api_plate_z&metric_2_gt=" + str(z) + "&metric_2_lt=" + str(z + 0.1) + "&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_metric1_lt=on&chk_metric2_lt=on&chk_metric1_gt=on&chk_metric2_gt=on&chk_stats_batter_run_value_per_100=on#results"
                t = requests.get(url).text
                
                skey = '>\n                                        <span>\n                                            '
                ekey = '\n                                        </span>\n                                    </td>\n'
                start = t.find(skey)
                end = t.find(ekey)
                
                try:
                    rv.append(round(float(t[start + len(skey):end])/100, 4))
                    
                except ValueError:
                    rv.append(0)
                    
            
            #
            # get cs%
            #
            url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=ball%7Cblocked%5C.%5C.ball%7Cpitchout%7Chit%5C.%5C.by%5C.%5C.pitch%7Cintent%5C.%5C.ball%7C&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=api_plate_x&metric_1_gt=" + str(x) + "&metric_1_lt=" + str(x + 0.1) + "&metric_2=api_plate_z&metric_2_gt=" + str(z) + "&metric_2_lt=" + str(z + 0.1) + "&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_metric1_lt=on&chk_metric2_lt=on&chk_metric1_gt=on&chk_metric2_gt=on&chk_takes=on#results"
            t = requests.get(url).text
            
            skey = 'align-right column-sort"><span>'
            ekey = '</span></td>\n                                <td class="tr-data align-right"><span>'
            start1 = t.find(skey)
            end1 = t.find('</span></td>\n                                <td class="tr-data align-right"><span>')
            end2 = t.find('</span></td>\n                                <td class="tr-data align-right "><span>')
            
            try:
                ball = int(t[start1 + len(skey):end1])
                tot = int(t[end1 + len(ekey):end2])
                cs = round(1 - ball/tot, 4)
                
            except ValueError:
                cs = 1
                
            if cs < 0:
                cs = 0
    
                
            #
            # get contact%, rv, xWOBA
            #
            url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=hit%5C.%5C.into%5C.%5C.play%7C&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=api_plate_x&metric_1_gt=" + str(x) + "&metric_1_lt=" + str(x + 0.1) + "&metric_2=api_plate_z&metric_2_gt=" + str(z) + "&metric_2_lt=" + str(z + 0.1) + "&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_metric1_lt=on&chk_metric2_lt=on&chk_metric1_gt=on&chk_metric2_gt=on&chk_swings=on&chk_stats_xwoba=on&chk_stats_batter_run_value_per_100=on#results"
            t = requests.get(url).text
            
            skey = '<td class="tr-data align-right "><span>'
            ekey1 = '</span></td>\n                                    <td \n                                        class="tr-data align-right "\n                                    >\n                                        <span>\n                                            '
            ekey2 = '\n                                        </span>\n                                    </td>\n                                    <td \n                                        class="tr-data align-right "\n                                    >\n                                        <span>\n                                            '
            start = t.find(skey)
            end1 = t.find(ekey1)
            end2 = t.find(ekey2)
            end3 = t.find('\n                                        </span>\n                                    </td>\n                                <td style="text-align: right')
            
            try:
                cont = round(float(t[start + len(skey):end1])/100, 4)
                xwob = round(float(t[end1 + len(ekey1):end2]), 4)
                crv = round(float(t[end2 + len(ekey2):end3])/100, 4)
                
            except ValueError:
                cont = 0
                xwob = 0
                crv = 0
            
            
            #
            # get fb%
            #
            url = "https://baseballsavant.mlb.com/statcast_search?hfPT=&hfAB=&hfGT=R%7C&hfPR=foul%7Cfoul%5C.%5C.bunt%7Cfoul%5C.%5C.pitchout%7C&hfZ=&hfStadium=&hfBBL=&hfNewZones=&hfPull=&hfC=&hfSea=" + year + "%7C&hfSit=&player_type=batter&hfOuts=&hfOpponent=&pitcher_throws=&batter_stands=&hfSA=&game_date_gt=&game_date_lt=&hfMo=&hfTeam=&home_road=&hfRO=&position=&hfInfield=&hfOutfield=&hfInn=&hfBBT=&hfFlag=&metric_1=api_plate_x&metric_1_gt=" + str(x) + "&metric_1_lt=" + str(x + 0.1) + "&metric_2=api_plate_z&metric_2_gt=" + str(z) + "&metric_2_lt=" + str(z + 0.1) + "&group_by=league&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&player_event_sort=api_p_release_speed&sort_order=desc&chk_metric1_lt=on&chk_metric2_lt=on&chk_metric1_gt=on&chk_metric2_gt=on&chk_stats_batter_run_value_per_100=on#results"
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
            
            
            #
            # append new row to data frame
            #
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
                    "CS": [cs],
                    "CONTACT": [cont],
                    "xWOBACON": [xwob],
                    "CRV": [crv],
                    "FOUL": [foul]
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
            print(str(round(100*p, 1)) + '% - expected finishing time: ' + str(hr) + ':' + str(mn)) 
        
    league_rv = league_rv.drop([0])
    
    ball_rv = np.zeros([4, 3])
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
    
    strike_rv = np.zeros([4, 3])
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
    
    ###############################################################################
    
    #
    # calculate rv difference for swings vs takes by count
    #
    def calculate_rv(cs,cont,crv,foul,balls,strikes, sw_tk):
        rvs = strike_rv[balls][strikes]
        rvb = ball_rv[balls][strikes]
        if strikes == 2:
            swing_rv = (cont*crv + (1-cont)*rvs)
        else:
            swing_rv = (cont*crv + (1-cont + foul)*rvs)
    
        take_rv = cs*rvs + (1 - cs)*rvb
        tot_rv = swing_rv - take_rv    
        
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
            
            league_rv[swing] = league_rv.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'swing'), axis = 1)
            league_rv[take] = league_rv.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'take'), axis = 1)
            league_rv[delta] = league_rv.apply(lambda x: calculate_rv(x.CS, x.CONTACT, x.CRV, x.FOUL, b, s, 'delta'), axis = 1)
    
    league_rv.to_csv('league_rv_' + year + '.csv', index = False)
    
    tot_time = time.perf_counter() - timer_start
    hours = str(math.floor(tot_time/3600))
    mins = str(round(tot_time % 3600 / 60))
    print('This operation took', hours, 'hours and', mins, 'minutes.')
    
    
    
# get_data_by_year(2021)
# get_data_by_year(2022)
# get_data_by_year(2023)
get_data_by_year(2024)

