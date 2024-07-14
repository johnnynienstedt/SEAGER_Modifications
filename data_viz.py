#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jun 22 15:22:23 2024

@author: johnnynienstedt
"""

import pandas as pd
import sqlite3
import os
import random
import time
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats



###############################################################################
################################ Player Stats #################################
###############################################################################

def get_player_stats():

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
    first_list = []
    last_list = []

    for i in range(len(player_name)):
        name = player_name[i]
        player_name[i] = ' '.join(reversed(name.lower().split(', ')))
        first_list.append(name.lower().split(', ')[1])
        last_list.append(name.lower().split(', ')[0])

    # player selection
    def select_player():
        
        instr = input("\nEnter an MLB batter, or type 'r' for random:\n").lower()
        
        if instr in player_name:
            player = instr
            i = player_name.index(instr)
            print()
            print(player.title() + ' selected.')
            print()
            return i
        
        
        def choose_random():
            global player
            i = random.randrange(0, len(player_name) - 1)
            player = player_name[i]
            print('\n' + player.title() + ' selected.')
            return i
            
        
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
            return i
        
        def check_matches(last_list, first_list, targets):
            last_matches = []
            first_matches = []
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
                    i = yes()
                    return i
                
                # Choose random player
                if instr == 'r':
                    i = choose_random()
                    return i

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
                        i = yes()
                        return i
                        
                for n in range(len(f)):
                    instr = dym(first, last_list[f[n]])
                    if instr in ['Y', 'y']:
                        i = f[n]
                        i = yes()
                        return i
                
                # Re-prompt if no match is found
                instr = try_again()
                
                # Allow a maximum of three tries
                bad = bad + 1
                if bad > 2:
                    print("\nToo many attempts. Selecting a random player...")
                    time.sleep(1)
                    i = choose_random()
                    return i

        i = resolve_entry(instr)
        
        return i
        
    i = select_player()
    pid = str(player_id[i])
    
    # Define the database file name
    c_filename = 'classic_stats.db'
    p_filename = 'player_stats.db'
    
    # Remove the existing database file if it exists
    if os.path.exists(c_filename):
        os.remove(c_filename)
        os.remove(p_filename)
    
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
    
    # Create a SQLite database connection
    c_conn = sqlite3.connect(c_filename)
    p_conn = sqlite3.connect(p_filename)
    
    
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
    
    
    print('\nClassic percentiles:\n')
    print(classic_stats.to_string(index=False))
    print('\nPlayer percentiles:\n')
    print(player_stats.to_string(index=False))
    

    # # Merge into one df
    # full_stats = pd.merge(classic_stats, player_stats, on='Year')
    # print(full_stats)
    
    # Close the database connection
    c_conn.close()
    p_conn.close()
    
# get_player_stats()

###############################################################################
############################### Overall Stats #################################
###############################################################################

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
classic_2021.insert(3, 'Year', 2021)
classic_2022.insert(3, 'Year', 2022)
classic_2023.insert(3, 'Year', 2023)
classic_2024.insert(3, 'Year', 2024)
player_2021.insert(3, 'Year', 2021)
player_2022.insert(3, 'Year', 2022)
player_2023.insert(3, 'Year', 2023)
player_2024.insert(3, 'Year', 2024)


classic_stats = pd.concat([classic_2021, classic_2022, classic_2023, classic_2024], ignore_index=True)
player_stats = pd.concat([player_2021, player_2022, player_2023, player_2024], ignore_index=True)

full_stats = pd.merge(classic_stats, player_stats, how='left', on=['NAME', 'ID', 'Year', 'N_SWINGS', 'N_TAKES', 'N_P'])

full_stats.drop(full_stats.columns[full_stats.columns.str.contains('unnamed', case=False)], axis=1, inplace=True)
full_stats = full_stats.drop(full_stats[full_stats.N_P < 1000].index)
full_stats = full_stats.sort_values(['ID', 'Year'], ignore_index = True)



###############################################################################
########################### Internal Correlations #############################
###############################################################################



# Correlation between classic and player within years
def pvc(colname):
    
    x = full_stats[colname + '_y']
    y = full_stats[colname + '_x']
    m, b, r, p, std_err = stats.linregress(x, y)
    
    plt.scatter(x, y, s=3)
    plt.plot(x, m*x+b, '-k')
    plt.title('Player vs. Classic ' + colname)
    plt.xlabel('Player ' + colname)
    plt.ylabel('Classic' + colname)
    
    left = x.min()
    top = y.max()*0.9
    
    plt.text(left, top, '$R^2$ = ' + str(round(r**2, 2)))
    plt.show()

# pvc('L_SEAGER')


# Stickiness year over year
def yoy(colname):
    
    p_rows = []
    c_rows = []
    for i in range(len(full_stats) - 1):
        if full_stats['ID'][i + 1] == full_stats['ID'][i]:
            c1 = full_stats[colname + '_x'][i]
            c2 = full_stats[colname + '_x'][i + 1]
            c3 = full_stats['N_P'][i]
            c_rows.append({'Year1': c1,
                         'Year2': c2,
                         'N_P': c3})
            
            p1 = full_stats[colname + '_y'][i]
            p2 = full_stats[colname + '_y'][i + 1]
            p_rows.append({'Year1': p1,
                         'Year2': p2,
                         'N_P': c3})
            
            
    classic_pairs = pd.DataFrame(c_rows)
    player_pairs = pd.DataFrame(p_rows)
    
    
    #classic
    x = classic_pairs.Year1
    y = classic_pairs.Year2
    
    m, b, r, p, std_err = stats.linregress(x, y)
    
    plt.scatter(x, y, s=3)
    plt.plot(x, m*x+b, '--k')
    plt.title(colname + ' Year Over Year - Classic')
    plt.xlabel('Year 1 ' + colname)
    plt.ylabel('Year 2 ' + colname)
        
    left = x.min()
    top = y.max()*0.9
    
    plt.text(left, top, '$R$ = ' + str(round(r, 2)))
    plt.show()


    # player
    x = player_pairs.Year1
    y = player_pairs.Year2
    
    m, b, r, p, std_err = stats.linregress(x, y)
    
    plt.scatter(x, y, s=3)
    plt.plot(x, m*x+b, '--k')
    plt.title(colname + ' Year Over Year - Player')
    plt.xlabel('Year 1 ' + colname)
    plt.ylabel('Year 2 ' + colname)
        
    left = x.min()
    top = y.max()*0.9
    
    plt.text(left, top, '$R$ = ' + str(round(r, 2)))
    plt.show()
    
    return classic_pairs, player_pairs

# cp, pp = yoy('SEAGER')


# Stickiness as a function of pitches seen (when does it stabilize?)
# This is essentially defunct since I used it to set the qualification limit 
# to 1000 pitches

def stabilization(cp, pp):
    
    r_squared = []
    step = 100
    for i in range(1000,cp.N_P.max(),step):
        x = cp.Year1[(cp.N_P > i) & (cp.N_P < i + step)]
        y = cp.Year2[(cp.N_P > i) & (cp.N_P < i + step)]
        m, b, r, p, std_err = stats.linregress(x, y)
        r_squared.append(r**2)
    
    x = np.arange(1000,cp.N_P.max(),step)
    plt.scatter(x, r_squared)
    plt.title('Year Over Year Correlation - Classic S/T Percentile')
    plt.xlabel('Number of Pitches in Preceeding Season')
    plt.ylabel('R Squared Correlation')
    plt.ylim([0,1])
    plt.show()


    # stickiness as a function of pitches seen (when does it stabilize?)
    r_squared = []
    step = 100
    for i in range(1000,pp.N_P.max(),step):
        x = pp.Year1[(pp.N_P > i) & (pp.N_P < i + step)]
        y = pp.Year2[(pp.N_P > i) & (pp.N_P < i + step)]
        m, b, r, p, std_err = stats.linregress(x, y)
        r_squared.append(r**2)
    
    x = np.arange(1000,pp.N_P.max(),step)
    plt.scatter(x, r_squared)
    plt.title('Year Over Year Correlation - Player S/T Percentile')
    plt.xlabel('Number of Pitches in Preceeding Season')
    plt.ylabel('R Squared Correlation')
    plt.ylim([0,1])
    
    # we can see that the player specific version is stickier (by a bit). This is good!
    
    # Based on the above, I will now trim the database to include only seasons of
    # more than 1000 pitches seen, then reexamine the P/C correlations.
    
    plt.show()
    
# stabilization(cp, pp)


###############################################################################
########################### External Correlations #############################
###############################################################################


# import player lists
pdat_2021 = pd.read_csv('players_2021.csv')
pdat_2022 = pd.read_csv('players_2022.csv')
pdat_2023 = pd.read_csv('players_2023.csv')
pdat_2024 = pd.read_csv('players_2024.csv')

pdat_2021['Year'] = 2021
pdat_2022['Year'] = 2022
pdat_2023['Year'] = 2023
pdat_2024['Year'] = 2024

pstats = pd.concat([pdat_2021, pdat_2022, pdat_2023, pdat_2024], ignore_index=True)
pstats = pstats.rename(columns={'player_id':'ID'})
fuller_stats = pd.merge(full_stats, pstats, on=['ID', 'Year'])

def inseason_corr(ind_colname, dep_colname):

    x = fuller_stats[ind_colname]
    y = fuller_stats[dep_colname]
    m, b, r, p, std_err = stats.linregress(x, y)
    plt.scatter(x, y, s=3)
    plt.plot(x, m*x+b, '--k')
    plt.title(ind_colname + ' vs. ' + dep_colname)
    plt.xlabel(ind_colname)
    plt.ylabel(dep_colname)
        
    left = x.min()
    top = y.max()*0.9
    
    plt.text(left, top, '$R$ = ' + str(round(r, 2)))
    plt.show()
    
    return r
    
# r = inseason_corr('SEAGER_y', 'iso')


def nextseason_corr(ind_colname, dep_colname):
    
    i_rows = []
    d_rows = []
    for i in range(len(fuller_stats) - 1):
        if fuller_stats['ID'][i + 1] == fuller_stats['ID'][i]:
            i1 = fuller_stats[ind_colname][i]
            i2 = fuller_stats[ind_colname][i + 1]
            i3 = fuller_stats['N_P'][i]
            i_rows.append({'Year1': i1,
                         'Year2': i2,
                         'N_P': i3})
            
            d1 = fuller_stats[dep_colname][i]
            d2 = fuller_stats[dep_colname][i + 1]
            d_rows.append({'Year1': d1,
                         'Year2': d2,
                         'N_P': i3})
            
            
    ind_pairs = pd.DataFrame(i_rows)
    dep_pairs = pd.DataFrame(d_rows)
    
    
    x = ind_pairs.Year1
    y = dep_pairs.Year2
    
    m, b, r, p, std_err = stats.linregress(x, y)
    
    plt.scatter(x, y, s=3)
    plt.plot(x, m*x+b, '--k')
    plt.title(ind_colname + ' vs. Next Season ' + dep_colname)
    plt.xlabel('Year 1 ' + ind_colname)
    plt.ylabel('Year 2 ' + dep_colname)
        
    left = x.min()
    top = y.max()*0.9
    
    plt.text(left, top, '$R$ = ' + str(round(r, 2)))
    plt.show()
    
    return r


r = inseason_corr('SEAGER_x', 'iso')
time.sleep(1)
r = nextseason_corr('SEAGER_x', 'iso')
time.sleep(1)
r = inseason_corr('SEAGER_y', 'iso')
time.sleep(1)
r = nextseason_corr('SEAGER_y', 'iso')





