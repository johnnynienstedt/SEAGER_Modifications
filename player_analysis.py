#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 18:51:49 2024

@author: johnnynienstedt
"""

#
# Player and League Analyisis
# Johnny Nienstedt 6/21/24
#

import pandas as pd
import random
import time
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.lines import Line2D
import numpy as np
import sqlite3
import os
import pybaseball

pybaseball.cache.enable()



###############################################################################



# import player lists
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
player_name = list(pdat['Name'])
player_id = list(pdat['ID'])


# import league and player data
league_heatmaps = np.load('league_heatmaps.npy')
player_heatmaps = np.load('player_heatmaps.npy')



###############################################################################



def get_X(x):
    X = x*13.5 + 15
    return X

def get_Z(z):
    Z = (z*12 - 14)*35/32
    return Z

# plot function for league heatmaps
def plot_league_heatmap(count = '0-0', action = 'DELTA'):
    
    counts = ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2']
    if count not in counts:
        raise ValueError('Please enter the count in b-s format; e.g. 3-2')
        
    # image size
    X = 30
    Z = 35
    
    # Initialize data
    b = int(count[0])
    s = int(count[2])

    pvals = np.zeros((X,Z), dtype='float')

            
    if   action == 'SWING':    pvals = league_heatmaps[2][b][s]
    elif action == 'TAKE':     pvals = league_heatmaps[3][b][s]
    elif action == 'DELTA':    pvals = league_heatmaps[2][b][s] - league_heatmaps[3][b][s]
    elif action == 'EXPECTED': pvals = league_heatmaps[0][b][s]
    else:
        raise ValueError("Options for 'action' are: SWING, TAKE, DELTA, EXPECTED")
            
    pvals = pvals.transpose()
    
    #
    # make plot
    #
    fig, ax = plt.subplots(constrained_layout=True)
    
    plt.pcolormesh(pvals, cmap='bwr', vmin = 0, vmax = 1)
    plt.colorbar(shrink=0.7, extend='both', label='League-wide Run Value', ticks=[0,0.5, 0.1])
    
    # make strike zone outline
    lw = 1/72
    left, right, bot, top = get_X(-17/24), get_X(17/24), get_Z(1.5), get_Z(3.5)
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    
    # set ticks and labels
    xlabels = [-1, 0, 1]
    xticks = [get_X(x) for x in xlabels]
    ax.set_xticks(xticks, xlabels)
    ylabels = [1.5, 2.0, 2.5, 3.0, 3.5]
    yticks = [get_Z(z) for z in ylabels]
    ax.set_yticks(yticks, ylabels)
    
    # set title and axis labels
    if action == 'DELTA':
        plt.title('League-wide Swing minus Take\nRun Value (' + count[0] + '-' + count[2] + ' count)')
    else:
        plt.title('League-wide ' + action.title() + ' \nRun Value (' + count[0] + '-' + count[2] + ' count)')

    plt.ylabel('Height (ft)')
    plt.xlabel('Catcher POV Horizontal Axis (ft)')
    
    # force correct aspect ratio
    ax.set_aspect(1)
    plt.show()
        

# Plot function for player heat map
def plot_player_heatmap(pid = '608369', count = '0-0', action = 'DELTA'):
    
    # determine player index and name
    pid = int(pid)
    i = player_id.index(pid)
    player = player_name[i]
    player = player.split(', ')[1] + ' ' + player.split(', ')[0]

    # image size
    X = 30
    Z = 35
    pvals = np.zeros((X,Z), dtype='float')

    # count
    b = int(count[0])
    s = int(count[2])

    # get correct map
    if   action == 'SWING': 
        
        #
        # dynamic plot
        #
        pvals = player_heatmaps[i][b][s]
        
        # enable interactive mode
        plt.ion()
        
        fig, ax = plt.subplots(constrained_layout=True)
        
        # initial plot
        mesh = ax.pcolormesh(pvals[0].transpose(), cmap='bwr', vmin=-0.2, vmax=0.2)
        cbar = plt.colorbar(mesh, ax=ax, shrink=0.7, extend='both', label='Expected Player Run Value', ticks=[-0.1, 0, 0.1])
        
        # set initial ticks and labels
        xlabels = [-1, 0, 1]
        xticks = [get_X(x) for x in xlabels]
        ax.set_xticks(xticks)
        ax.set_xticklabels(xlabels)
        
        ylabels = [1.5, 2.0, 2.5, 3.0, 3.5]
        yticks = [get_Z(z) for z in ylabels]
        ax.set_yticks(yticks)
        ax.set_yticklabels(ylabels)
        
        # set initial axis labels and title
        ylabel = ax.set_ylabel('Height (ft)')
        xlabel = ax.set_xlabel('Catcher POV Horizontal Axis (ft)')
        title = ax.set_title('')
        
        # force correct aspect ratio
        ax.set_aspect(1)
        
        # loop over maps
        for j in range(11):
            # Update plot data
            mesh.set_array(pvals[j].transpose().ravel())
            
            # Update colorbar
            cbar.update_normal(mesh)
        
            # Update ticks and labels
            ax.set_xticks(xticks)
            ax.set_xticklabels(xlabels)
            ax.set_yticks(yticks)
            ax.set_yticklabels(ylabels)
            
            # Update axis labels and title
            ylabel.set_text('Height (ft)')
            xlabel.set_text('Catcher POV Horizontal Axis (ft)')
            
            if action == 'DELTA':
                title.set_text('Swing minus Take Run Value for\n' + player.title() + ' (' + count[0] + '-' + count[2] + ' count)')
            else:
                title.set_text(action.title() + ' Run Value for\n' + player.title() + ' (' + count[0] + '-' + count[2] + ' count)')
            
            # Pause to create the animation effect
            if j == 0:
                plt.pause(2)
            
            # make strike zone outline
            if j == 10:
                lw = 1/72
                left, right, bot, top = get_X(-17/24), get_X(17/24), get_Z(1.5), get_Z(3.5)
                plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
                plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
                plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
                plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
             
            plt.pause(0.1)
        

        plt.ioff()
        plt.show()
        
        return   
    elif action == 'TAKE': pvals = league_heatmaps[3][b][s]
    elif action == 'DELTA': pvals = player_heatmaps[i][b][s][10] - league_heatmaps[3][b][s]
    else:
        raise ValueError("Options for 'action' are: SWING, TAKE, DELTA")

    pvals = pvals.transpose()
    
    fig, ax = plt.subplots(constrained_layout=True)
    
    # colormap and colorbar
    mesh = ax.pcolormesh(pvals, cmap='bwr', vmin=-0.2, vmax=0.2)
    cbar = plt.colorbar(mesh, ax=ax, shrink=0.7, extend='both', label='Expected Player Run Value', ticks=[-0.1, 0, 0.1])
    
    # set  ticks and labels
    xlabels = [-1, 0, 1]
    xticks = [get_X(x) for x in xlabels]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)
    
    ylabels = [1.5, 2.0, 2.5, 3.0, 3.5]
    yticks = [get_Z(z) for z in ylabels]
    ax.set_yticks(yticks)
    ax.set_yticklabels(ylabels)
    
    # set  axis labels and title
    ylabel = ax.set_ylabel('Height (ft)')
    xlabel = ax.set_xlabel('Catcher POV Horizontal Axis (ft)')
    if action == 'DELTA':
        plt.title('Swing minus Take Run Value for\n' + player.title() + ' (' + count[0] + '-' + count[2] + ' count)')
    else:
        plt.title(action.title() + ' Run Value for\n' + player.title() + ' (' + count[0] + '-' + count[2] + ' count)')
    
    #make strike zone outline
    lw = 1/72
    left, right, bot, top = get_X(-17/24), get_X(17/24), get_Z(1.5), get_Z(3.5)
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)

    # Force correct aspect ratio
    ax.set_aspect(1)
    
    plt.show()


# player selection
def select_player():
    
    instr = input("\nEnter an MLB batter, or type R for random:\n").lower()
    
    # separate first and last names
    player_name = list(pdat.Name)
    player_id = list(pdat.ID)
    first_list = []
    last_list = []
    for i in range(len(player_name)):
        name = player_name[i]
        player_name[i] = ' '.join(reversed(name.lower().split(', ')))
        first_list.append(player_name[i].split()[0])
        last_list.append(player_name[i].split()[1])
    
    if instr in player_name:
        player = instr
        i = player_name.index(instr)
        print()
        print(player.title() + ' selected.')
        print()
        return i, player_id[i], player.title()

    
    def choose_random():
        global player
        i = random.randrange(0, len(player_name) - 1)
        player = player_name[i]
        print('\n' + player.title() + ' selected.')
        return i, player_id[i], player.title()
        
    
    def dym(first, last):
        instr = input("\nDid you mean " + first.title() + ' ' + last.title() + '? (Y/N)\n')
        return instr


    def try_again():
        instr = input("\nCouldn't find that player. Please try again:\n").lower()
        return instr


    def yes():
        global player, i
        player = player_name[i]
        print('\n' + player.title() + ' selected.')
        return i, player_id[i], player.title()
    
    def check_matches(last_list, first_list, targets):
        last_matches = [i for i in range(len(last_list)) if last_list[i] in targets]
        first_matches = [i for i in range(len(first_list)) if first_list[i] in targets]
        return last_matches, first_matches
    
    
    # Handle improper entries
    def resolve_entry(instr):
        bad = 0
        global i
        
        while True:
            
            # Break for correct input
            if instr in player_name:
                player = instr
                i = player_name.index(player)
                i, player_id, player = yes()
                return i, player_id, player
            
            # Choose random player
            if instr == 'r':
                i, player_id, player = choose_random()
                return i, player_id, player

            # Handle one-word entries
            if len(instr.split()) > 1:
                first = instr.lower().split()[0]
                last = instr.lower().split()[1]
            else:
                first = instr.lower()
                last = instr.lower()
            
            # Make suggestions for partially correct names
            l, f = check_matches(last_list, first_list, [first, last])

            for n in range(len(l)):
                instr = dym(first_list[l[n]], last)
                if instr in ['Y', 'y']:
                    i = l[n]
                    i, player_id, player = yes()
                    return i, player_id, player
                    
            for n in range(len(f)):
                instr = dym(first, last_list[f[n]])
                if instr in ['Y', 'y']:
                    i = f[n]
                    i, player_id, player = yes()
                    return i, player_id, player
            
            # Re-prompt if no match is found
            instr = try_again()
            
            # Allow a maximum of three tries
            bad = bad + 1
            if bad > 2:
                print("\nToo many attempts. Selecting a random player...")
                time.sleep(1)
                i, player_id, player = choose_random()
                return i, player_id, player

    i, player_id, player = resolve_entry(instr)
    
    return i, player_id, player
    

# display random pitch
def random_pitch(pid = '608369', year = '2024'):
    
    year = str(year)
    
    i = pdat[pdat['ID'] == int(pid)].index[0]
    name = pdat.Name[i]
    name = name.split(', ')[1] + ' ' + name.split(', ')[0]
    
    global xlist, zlist
    xlist, zlist = [], []
    for X in range(-15, 15):
        xlist.append(X/13.5 + 1/27)
    for Z in range(35):
        zlist.append((Z*32/35 + 14)/12 + 1/27)
    
    # data for pitches to this player
    if year == '2021':
        start_dt, end_dt = '2021-04-01', '2021-10-03'
    if year == '2022':
        start_dt, end_dt = '2022-04-07', '2022-10-05'
    if year == '2023':
        start_dt, end_dt = '2023-03-30', '2023-10-01'
    if year == '2024':
        start_dt, end_dt = '2024-03-28', '2024-9-27'
    
    pitches = pybaseball.statcast_batter(start_dt, end_dt, pid)
    
    swing_types = ['hit_into_play', 'foul', 'swinging_strike', 'foul_tip', 
                   'swinging_strike_blocked', 'swinging_pitchout',
                   'foul_pitchout']
    take_types = ['ball', 'called_strike', 'blocked_ball', 'hit_by_pitch', 
                  'pitchout']
    bunt_types = ['missed_bunt', 'foul_bunt', 'foul_tip_bunt']
    
    r = np.random.randint(0, len(pitches))
    row = pitches.iloc[r]
    
    # determine location
    px = row.plate_x
    pz = row.plate_z

    # determine suitability
    while (row.description in bunt_types) | (px < xlist[0]) | (px > xlist[29]) | (pz < zlist[0]) | (pz > zlist[34]):
        r = np.random.randint(0, len(pitches))
        row = pitches.iloc[r]
        px = row.plate_x
        pz = row.plate_z
    
    # round appropriately to proper zone
    x = min(xlist, key=lambda d:abs(d-px))
    z = min(zlist, key=lambda d:abs(d-pz))
    
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
    
    # called strike rate
    cs = league_heatmaps[4][0][0][ix][iz]
    
    # classic actual run value for swings and takes
    classic_srv = league_heatmaps[2][b][s][ix][iz]
    trv = league_heatmaps[3][b][s][ix][iz]
    
    # player actual run value for swings (trv is the same)
    player_srv = player_heatmaps[i][b][s][10][ix][iz]
    
    # classic expected run value (using league stats)
    classic_xrv = league_heatmaps[0][b][s][ix][iz]
    
    # player expected run value (using player stats)
    league_swing = league_heatmaps[1][b][s][ix][iz]
    player_xrv = league_swing*player_srv + (1 - league_swing)*trv


    #
    # evaluate swing decision
    #
    
    # if the player swung
    if row.description in swing_types:
        
        decision = 'swing'
        crv = classic_srv - classic_xrv
        prv = player_srv - player_xrv
    
    # if the player did not swing
    if row.description in take_types:
        
        decision = 'take'
        crv = trv - classic_xrv
        prv = trv - player_xrv

    # plotting
    global pitch_types
    pitch_types = {
                    'CH': 'changeup',
                    'CS': 'slow curve',
                    'CU': 'curvenall',
                    'EP': 'eephus',
                    'FC': 'cutter',
                    'FF': '4-seam fastball',
                    'FO': 'forkball',
                    'FS': 'splitter',
                    'KC': 'knucke curve',
                    'KN': 'knuckleball',
                    'PO': 'pitchout',
                    'SC': 'screwball',
                    'SI': 'sinker',
                    'SL': 'slider',
                    'ST': 'sweeper',
                    'SV': 'slurve',
                    'FA': 'unknown'
        }


    colormap = plt.cm.bwr
    normalize = matplotlib.colors.Normalize(vmin=-0.02, vmax=0.02)  
    
    
    # classic
    fig, ax = plt.subplots(constrained_layout=True)
    xbias = 0.2
    ybias = 0
    plt.title('Random pitch to ' + name + ' in ' + year)
    plt.xlabel('Catcher POV Horizontal Axis (ft)')
    plt.ylabel('Height (ft)')
    plt.xlim([-10/9, 10/9])
    plt.ylim([14/12, 46/12])
    ax.set_xticks([-1,0,1])
    ax.set_yticks([1.5,2,2.5,3,3.5])
    ax.set_aspect(1)
    lw = 1/72
    left, right, bot, top = -17/24, 17/24, 18/12, 42/12
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    fig.set_size_inches(32/6, 26.6/6, forward=True)
    sp = ' '
    plt.text(-4.2 + xbias, 3.6 + ybias, sp*20 + 'Count: ' + str(b) + '-' + str(s), fontsize = 12)
    # plt.text(-4.2 + xbias, 3.3, 'Pitch type: ' + row.p_throws + 'H ' + pitch_types[row.pitch_type])
    plt.text(-4.2 + xbias, 3.4 + ybias, sp*16 + 'Location: (' + str(row.plate_x) + ', ' + str(row.plate_z) + ')', fontsize = 12)
    plt.text(-4.2 + xbias + 0.02, 3.2 + ybias, sp*2 + 'Called strike rate: ' + str(round(cs*100)) + '%', fontsize = 12)
    plt.text(-4.2 + xbias, 3.0 + ybias, sp*13 + 'Swing rate: ' + str(round(league_swing*100)) + '%', fontsize = 12)
    plt.text(-4.2 + xbias, 2.7 + ybias, sp*5 + 'Swing run value: ' + str(round(classic_srv, 3)), fontsize = 12)
    plt.text(-4.2 + xbias, 2.5 + ybias, sp*7 + 'Take run value: ' + str(round(trv, 3)), fontsize = 12)
    plt.text(-4.215 + xbias, 2.3 + ybias, 'Expected run value: ' + str(round(classic_xrv, 3)), fontsize = 12)
    plt.text(-4.2 + xbias, 2.0 + ybias, sp*16 + 'Decision: ' + decision, fontsize = 12)
    plt.text(-4.19 + xbias, 1.8 + ybias, sp*6 + 'Decision value: ' + str(round(crv, 3)) + ' runs', fontsize = 12)
    plt.text(-3.72 + xbias, 1.43 + ybias, 'League Verdict:', fontsize = 18)
    if crv >= 0:
        if decision == 'swing':
            if classic_srv >= 0:
                plt.text(-4 + xbias, 1.2 + ybias, 'Swung at a hittable pitch.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)

            else:
                plt.text(-3.75 + xbias, 1.2 + ybias, 'Protected the plate.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
        else:
            if trv >= 0:
                plt.text(-3.65 + xbias, 1.2 + ybias, 'Took a bad pitch.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
            else:
                plt.text(-3.9 + xbias, 1.2 + ybias, "Took a pitcher's pitch.", fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
    else:
        if decision == 'swing':
            if trv <= 0:
                plt.text(-3.95 + xbias, 1.2 + ybias, "Swung at a pitcher's pitch.", fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)
            else:
                plt.text(-3.8 + xbias, 1.2 + ybias, 'Swung at a bad pitch.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)

        else:
            if classic_srv >= 0:
                plt.text(-3.77 + xbias, 1.2 + ybias, 'Took a hittable pitch.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)
            else:
                plt.text(-3.73 + xbias, 1.2 + ybias, 'Took a likely strike.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)


    plt.scatter(px, pz, c=crv, s=400, cmap=colormap, norm=normalize)
    plt.colorbar(shrink=0.5, extend='both', label='Decision Run Value', ticks=[-0.01,0,0.01])
    plt.show()
    
    input('\nDisplaying CLASSIC evaluation of example pitch. Press ENTER to display PLAYER evaluation...')
    
    # player
    fig, ax = plt.subplots(constrained_layout=True)
    plt.title('Random pitch to ' + name + ' in ' + year)
    plt.xlabel('Catcher POV Horizontal Axis (ft)')
    plt.ylabel('Height (ft)')
    plt.xlim([-10/9, 10/9])
    plt.ylim([14/12, 46/12])
    ax.set_xticks([-1,0,1])
    ax.set_yticks([1.5,2,2.5,3,3.5])
    ax.set_aspect(1)
    lw = 1/72
    left, right, bot, top = -17/24, 17/24, 18/12, 42/12
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    fig.set_size_inches(32/6, 26.6/6, forward=True)
    sp = ' '
    plt.text(-4.2 + xbias, 3.6 + ybias, sp*20 + 'Count: ' + str(b) + '-' + str(s), fontsize = 12)
    # plt.text(-4.2 + xbias, 3.3 + ybias, 'Pitch type: ' + row.p_throws + 'H ' + pitch_types[row.pitch_type])
    plt.text(-4.2 + xbias, 3.4 + ybias, sp*16 + 'Location: (' + str(row.plate_x) + ', ' + str(row.plate_z) + ')', fontsize = 12)
    plt.text(-4.2 + xbias + 0.02, 3.2 + ybias, sp*2 + 'Called strike rate: ' + str(round(cs*100)) + '%', fontsize = 12)
    plt.text(-4.2 + xbias, 3.0 + ybias, sp*13 + 'Swing rate: ' + str(round(league_swing*100)) + '%', fontsize = 12)
    plt.text(-4.2 + xbias, 2.7 + ybias, sp*5 + 'Swing run value: ' + str(round(player_srv, 3)), fontsize = 12)
    plt.text(-4.2 + xbias, 2.5 + ybias, sp*7 + 'Take run value: ' + str(round(trv, 3)), fontsize = 12)
    plt.text(-4.215 + xbias, 2.3 + ybias, 'Expected run value: ' + str(round(player_xrv, 3)), fontsize = 12)
    plt.text(-4.2 + xbias, 2.0 + ybias, sp*16 + 'Decision: ' + decision, fontsize = 12)
    plt.text(-4.19 + xbias, 1.8 + ybias, sp*6 + 'Decision value: ' + str(round(prv, 3)) + ' runs', fontsize = 12)
    plt.text(-3.61 + xbias, 1.43 + ybias, 'Player Verdict:', fontsize = 18)
    if prv >= 0:
        if decision == 'swing':
            if player_srv >= 0:
                plt.text(-4 + xbias, 1.2 + ybias, 'Swung at a hittable pitch.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)

            else:
                plt.text(-3.75 + xbias, 1.2 + ybias, 'Protected the plate.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
        else:
            if trv >= 0:
                plt.text(-3.65 + xbias, 1.2 + ybias, 'Took a bad pitch.', fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
            else:
                plt.text(-3.9 + xbias, 1.2 + ybias, "Took a pitcher's pitch.", fontsize = 15)
                plt.text(-3.54 + xbias, 1.0 + ybias, 'Good decision.', fontsize = 15)
    else:
        if decision == 'swing':
            if trv <= 0:
                plt.text(-3.95 + xbias, 1.2 + ybias, "Swung at a pitcher's pitch.", fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)
            else:
                plt.text(-3.8 + xbias, 1.2 + ybias, 'Swung at a bad pitch.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)

        else:
            if player_srv >= 0:
                plt.text(-3.77 + xbias, 1.2 + ybias, 'Took a hittable pitch.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)
            else:
                plt.text(-3.73 + xbias, 1.2 + ybias, 'Took a likely strike.', fontsize = 15)
                plt.text(-3.4 + xbias, 1.0 + ybias, 'Bad decision.', fontsize = 15)


    plt.scatter(px, pz, c=prv, s=400, cmap=colormap, norm=normalize)
    plt.colorbar(shrink=0.5, extend='both', label='Decision Run Value', ticks=[-0.01,0,0.01])
    plt.show()


# full at_bat
def full_ab():
    1 == 1
    # yeah
    

# pitch by pitch analysis
def pitch_by_pitch(pid, year):
    
    year = str(year)
    
    i = pdat[pdat['ID'] == int(pid)].index[0]
    name = pdat.Name[i]
    name = name.split(', ')[1] + ' ' + name.split(', ')[0]
    
    xlist, zlist = [], []
    for X in range(-15, 15):
        xlist.append(X/13.5 + 1/27)
    for Z in range(35):
        zlist.append((Z*32/35 + 14)/12 + 1/27)
    
    # data for pitches to this player
    if year == '2021':
        start_dt, end_dt = '2021-04-01', '2021-10-03'
    if year == '2022':
        start_dt, end_dt = '2022-04-07', '2022-10-05'
    if year == '2023':
        start_dt, end_dt = '2023-03-30', '2023-10-01'
    if year == '2024':
        start_dt, end_dt = '2024-03-28', '2024-9-27'
    
    pitches = pybaseball.statcast_batter(start_dt, end_dt, pid)
    
    swing_types = ['hit_into_play', 'foul', 'swinging_strike', 'foul_tip', 
                   'swinging_strike_blocked', 'swinging_pitchout',
                   'foul_pitchout']
    take_types = ['ball', 'called_strike', 'blocked_ball', 'hit_by_pitch', 
                  'pitchout']
    bunt_types = ['missed_bunt', 'foul_bunt', 'foul_tip_bunt']
    
    px = []
    pz = []
    dc = []
    dp = []
    
    for index, row in pitches.iterrows():
        
        # determine location
        x = row.plate_x
        z = row.plate_z
        
        if row.description not in bunt_types:
            px.append(x)
            pz.append(z)
        
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
        player_srv = player_heatmaps[i][b][s][10][ix][iz]
        
        
        #
        # evaluate swing decision
        #
        
        # if the player swung
        if row.description in swing_types:
            
            # classic
            if classic_srv > trv:
                dc.append('gs')
            else:
                dc.append('bs')
                
            # player
            if player_srv > trv:
                dp.append('gs')
            else:
                dp.append('bs')
        
        
        # if the player did not swing
        if row.description in take_types:
            
            if trv > classic_srv:
                dc.append('gt')
            else:
                dc.append('bt')
                
            if trv > player_srv:
                dp.append('gt')
            else:
                dp.append('bt')
 
    colordict = {'gs': 'cornflowerblue',
                 'gt': 'limegreen',
                 'bs': 'orange',
                 'bt': 'tomato'}
    
    fig, ax = plt.subplots(constrained_layout=True)
    plt.title('Classic Decsion Map\n' + name + ' ' + year)
    plt.xlabel('Catcher POV Horizontal Axis (ft)')
    plt.ylabel('Height (ft)')
    plt.xlim([-10/9, 10/9])
    plt.ylim([14/12, 46/12])
    ax.set_aspect(1)
    lw = 1/72
    left, right, bot, top = -17/24, 17/24, 18/12, 42/12
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.scatter(px, pz, c=[colordict[d] for d in dc], s=30, label=list(colordict.values()))
    legend_elements = [Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor='cornflowerblue', label='Good Swings'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='orange', label='Bad Swings'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='limegreen', label='Good Takes'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='tomato', label='Bad Takes')]
    ax.legend(handles=legend_elements, bbox_to_anchor=(1.04, 0.5), loc="center left")
    plt.show()
    
    input('\nDisplaying classic decision map. Press ENTER to display player decison map...')
    
    fig, ax = plt.subplots(constrained_layout=True)
    plt.title('Player Decsion Map\n' + name + ' ' + year)
    plt.xlabel('Catcher POV Horizontal Axis (ft)')
    plt.ylabel('Height (ft)')
    plt.xlim([-10/9, 10/9])
    plt.ylim([14/12, 46/12])
    ax.set_aspect(1)
    lw = 1/72
    left, right, bot, top = -17/24, 17/24, 18/12, 42/12
    plt.plot(np.linspace(left, right, 100), np.linspace(top,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, right, 100), np.linspace(bot,bot,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(left, left, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.plot(np.linspace(right, right, 100), np.linspace(bot,top,100), color = 'black', linewidth = lw*72)
    plt.scatter(px, pz, c=[colordict[d] for d in dp], s=30, label=list(colordict.values()))
    legend_elements = [Line2D([0], [0], marker='o', color='w', markersize=10, markerfacecolor='cornflowerblue', label='Good Swings'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='orange', label='Bad Swings'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='limegreen', label='Good Takes'),
                         Line2D([0], [0], marker='o', color='w', markersize=10,  markerfacecolor='tomato', label='Bad Takes')]
    ax.legend(handles=legend_elements, bbox_to_anchor=(1.04, 0.5), loc="center left")
    plt.show()


# display stats
def display(pid):
    
    i = player_id.index(int(pid))
    player = player_name[i]
    
    # Define the database file name
    c_filename = 'classic_stats.db'
    p_filename = 'player_stats.db'
    
    # Remove the existing database file if it exists
    if os.path.exists(c_filename):
        os.remove(c_filename)
        os.remove(p_filename)
    
    # Create a SQLite database connection
    c_conn = sqlite3.connect(c_filename)
    p_conn = sqlite3.connect(p_filename)
    
    # Load data
    classic_2021 = pd.read_csv('classic_st_2021.csv')
    classic_2022 = pd.read_csv('classic_st_2022.csv')
    classic_2023 = pd.read_csv('classic_st_2023.csv')
    classic_2024 = pd.read_csv('classic_st_2024.csv')
    player_2021 = pd.read_csv('player_st_2021.csv')
    player_2022 = pd.read_csv('player_st_2022.csv')
    player_2023 = pd.read_csv('player_st_2023.csv')
    player_2024 = pd.read_csv('player_st_2024.csv')
    
    # Add a 'Year' column to each DataFrame
    classic_2021['Year'] = 2021
    classic_2022['Year'] = 2022
    classic_2023['Year'] = 2023
    classic_2024['Year'] = 2024
    player_2021['Year'] = 2021
    player_2022['Year'] = 2022
    player_2023['Year'] = 2023
    player_2024['Year'] = 2024
    
    # Write the DataFrames to the SQLite database
    classic_2021.to_sql('c_stats', c_conn, if_exists='append', index=False)
    classic_2022.to_sql('c_stats', c_conn, if_exists='append', index=False)
    classic_2023.to_sql('c_stats', c_conn, if_exists='append', index=False)
    classic_2024.to_sql('c_stats', c_conn, if_exists='append', index=False)
    player_2021.to_sql('p_stats', p_conn, if_exists='append', index=False)
    player_2022.to_sql('p_stats', p_conn, if_exists='append', index=False)
    player_2023.to_sql('p_stats', p_conn, if_exists='append', index=False)
    player_2024.to_sql('p_stats', p_conn, if_exists='append', index=False)
    
    # Function to query the classic statistics
    def query_classic_stats(player_id):
        query = """
        SELECT Year, SEAGER_Percentile, Selective_Percentile, Agression_Percentile, SWTR_Percentile
        FROM c_stats
        WHERE ID = ?
        GROUP BY Name, Year
        ORDER BY Year
        """
        cursor = c_conn.execute(query, (player_id,))
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        df = pd.DataFrame(results, columns=columns)
        return df
    
    # Function to query the player statistics
    def query_player_stats(player_id):
        query = """
        SELECT Year, SEAGER_Percentile, Selective_Percentile, Agression_Percentile, SWTR_Percentile
        FROM p_stats
        WHERE ID = ?
        GROUP BY Name, Year
        ORDER BY Year
        """
        cursor = p_conn.execute(query, (player_id,))
        columns = [column[0] for column in cursor.description]
        results = cursor.fetchall()
        df = pd.DataFrame(results, columns=columns)
        return df
    
    # Query the database for a specific player
    classic_stats = query_classic_stats(pid)
    player_stats = query_player_stats(pid)
    
    # Rename columns
    classic_stats.columns = [x.split('_')[0] if '_' in x else x for x in classic_stats.columns]
    player_stats.columns = [x.split('_')[0] if '_' in x else x for x in player_stats.columns]
    
    print('\n__________________________________________________________')
    print('\nClassic swing decision percentiles for ' + player.title() + ':\n')
    print(classic_stats.to_string(index=False))
    print('\nPlayer swing decision percentiles for ' + player.title() + ':\n')
    print(player_stats.to_string(index=False))
    print('__________________________________________________________')
    
    years = list(classic_stats.Year)
    
    return years


# league options
def l_options():
    
    counts = ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2']
    
    print('\nChoose a count to examine league stats.')
        
    # count
    c = input("Enter a count in B-S format:\n")
    
    while c not in counts:
        c = input("Enter a count in B-S format:\n")
    
    # show heatmap
    for a in ['SWING', 'TAKE', 'DELTA']:
        plot_league_heatmap(c, a)
    
    print('\nDisplaying league-wide ' + a + ' run values for ' + c)
    
    instr = input('\nWould you like to view another count and/or action? (Y/N)\n')
    
    if instr in ['y', 'Y']:
        l_options()
    

# specific player options
def this_p_options(i, pid, player):
    
    instr = input('\nWhat would you like to see? Enter H for heatmaps or D for swing decisions.\n')
    
    if instr in ['h', 'H']:
    
        counts = ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2']
        
        print('\nHeatmaps selected. Choose a count to examine for ' + player + '.')
            
        # count
        c = input("\nEnter a count in B-S format:\n")
        
        while c not in counts:
            c = input("\nEnter a count in B-S format:\n")
            
        for a in ['SWING', 'TAKE', 'DELTA']:
            
            # show heatmap
            plot_player_heatmap(pid, c, a)

            

    elif instr in ['d', 'D']:    
        
        print('\nSwing Decisions selected.')
        time.sleep(1)

        # show percentiles
        years = display(pid)
        time.sleep(1)
        instr = input('\n\nWould you like to see swing decision maps for ' + player + '? (Y/N)\n')
        
        if instr in ['y', 'Y']:
            
            if len(years) == 1:
                random_pitch(pid, years[0])
                
                instr = input('\nPress ENTER to see full decision map...')
                time.sleep(1)
                
                pitch_by_pitch(pid, years[0])
                
            # choose year
            else:
                year = input('\nChoose year:\n')
                while int(year) not in years:
                    year = input('\nMust be a year with data - see above.\n')
                
                print()
                random_pitch(pid, year)
                
                instr = input('\nPress ENTER to see full decision map...')
                time.sleep(1)
                
                pitch_by_pitch(pid, year)
                
    instr = input('\nWould you like to view more maps and/or stats for ' + player + '? (Y/N)\n')
    
    if instr in ['y', 'Y']:
        this_p_options(i, pid, player)
    else:
        instr = input('\nWould you like to view another player? (Y/N)\n')

        if instr in ['y', 'Y']:
            p_options()
        

# player options
def p_options():
    
    # select player
    i, pid, player = select_player()
    this_p_options(i, pid, player)

# user options
def options():
    
    instr = input('\nEnter P to examine a player or L for the league as a whole.\n')
    
    if instr in ['p', 'P']:
        
        p_options()
    
    if instr in ['l', 'L']:
        
        l_options()
        


###############################################################################



# # # plot 0-0 league heatmap
# plot_league_heatmap('heatmap', '21', 'DELTA')
# input('\nDisplaying league-wide run values - press ENTER to select a player for analysis...\n')

# # select player
# i = select_player()
# pid = str(player_id[i])


# # plot 0-0 swing zone map for this player
# plot_player_heatmap(pid, 'zonemap', '21', 'SWING')
# input('Displaying run value heat map for '+ player.title() + ' - press ENTER to show example pitch...\n')

# # plot 0-0 delta heatmap for this player
# plot_player_heatmap(pid, 'heatmap', '21', 'SWING')
# input('Displaying run value heat map for '+ player.title() + ' - press ENTER to show example pitch...\n')

# # display example pitch to this batter
# random_pitch(pid, year)
# input('Displaying example pitch - press ENTER to show total swing decision values...\n')

# # display pitch-by-pitch decision values for this player
# pitch_by_pitch(pid, year)
# input('Displaying decsision values for '+ player.title() + ' - press ENTER to show swing/take statistics...\n')

# # display relevant stats for this player
# display(pid)
# time.sleep(2)

options()


