#do all the calculations from https://www.ultianalytics.com/calcs.html
import pandas as pd
import numpy as np

#### player-specific. Input: player dataframe...
def calc_player_statistics(df,player_name):
    '''all the calculations'''
    player_df=dfd.loc[dfd.isin([player_name]).any(axis=1)] #player involved...
    player_stat_df=pd.DataFrame({'Player':player_name},index=[0])
    funcs1=[points_played,o_points_played,d_points_played]
    funcs2=[plusminus, goals, assists, Ds, touches, catches, throws, throwaways,drops,throws_to_M,throws_to_W,receives_from_M,receives_from_W]
    for f in funcs1:
        player_stat_df[f.__name__]=f(player_df)
    player_stat_df['o_efficiency']=o_efficiency(player_df,player_stat_df['o_points_played'][0])
    player_stat_df['d_efficiency']=d_efficiency(player_df,player_stat_df['d_points_played'][0])
    for f in funcs2:
        player_stat_df[f.__name__]=f(player_df, player_name)
    return player_stat_df

def plusminus(player_df,player_name):
    '''
    +1 for a goal.
    +1 for an assist.
    +1 for a D.
    -1 for a drop.
    -1 for a passer turnover (throwaway, stalled, misc. penalty).
    +2 for a callahan (+1 for D and +1 for goal). ->should be counted already
    -1 for being callahaned.->don't know what this looks like yet'''
    pm=0
    pm+=goals(player_df,player_name)
    pm+=assists(player_df,player_name)
    pm+=Ds(player_df,player_name)
    pm-=throwaways(player_df,player_name)
    pm-=drops(player_df,player_name)
    return pm
    
def goals(player_df,player_name):
    try:
        return player_df.where(player_df.Receiver==player_name)['Action'].value_counts()['Goal']
    except KeyError:
        return 0

def assists(player_df,player_name):
    try:
       return player_df.where(player_df.Passer==player_name)['Action'].value_counts()['Goal']
    except KeyError:
        return 0

def Ds(player_df,player_name):
    try:
        return player_df.where(player_df.Defender==player_name)['Action'].value_counts()['D']
    except KeyError:
        return 0

def points_played(player_df):
    '''total number of points played. A player that subs in/out is credited half a point.
    Note: currently don't know what Action is a substitution...'''
    return len(player_df.groupby(['Our Score - End of Point','Their Score - End of Point']))
    
def o_points_played(player_df):
    '''total number of o-line points the player played. A player that subs in/out is credited a half point.'''
    return len(player_df.where(player_df.Line=='O').groupby(['Our Score - End of Point','Their Score - End of Point']))

def d_points_played(player_df):
    '''total number of d-line points the player played. A player that subs in/out is credited a half point.'''
    return len(player_df.where(player_df.Line=='D').groupby(['Our Score - End of Point','Their Score - End of Point']))

def o_efficiency(player_df, n_opoints):
    '''
    +1 for an O-line goal for a point in which the player was on the field.
    -1 for an opponent score against the O-line (a break) in which the player was on the field1.
    total divided by number of O-line points in which the player was on the field.
    Players substituted out before the goal are not affected.'''
    try:
        ominus=player_df.where(player_df.Line=='O').where(player_df['Event Type']=='Defense').where(player_df.Action=='Goal').groupby(['Tournamemnt','Our Score - End of Point','Their Score - End of Point'])['Action'].value_counts().sum()
    except IndexError:
        ominus=0
    try:
        oplus=player_df.where(player_df.Line=='O').where(player_df['Event Type']=='Offense').where(player_df.Action=='Goal').groupby(['Tournamemnt','Our Score - End of Point','Their Score - End of Point'])['Action'].value_counts().sum()
    except IndexError:
        oplus=0
    return float((oplus-ominus)/n_opoints)

def d_efficiency(player_df,n_dpoints):
    '''
    +1 for an D-line goal for a point in which the player was on the field.
    -1 for an opponent score against the D-line in which the player was on the field1.
    total divided by number of D-line points in which the player was on the field.
    Players substituted out before the goal are not affected.'''
    try:
        dplus=player_df.where(player_df.Line=='D').where(player_df['Event Type']=='Defense').where(player_df.Action=='Goal').groupby(['Tournamemnt','Our Score - End of Point','Their Score - End of Point'])['Action'].value_counts().sum()
    except IndexError:
        dplus=0
    try:
        dminus=player_df.where(player_df.Line=='D').where(player_df['Event Type']=='Offense').where(player_df.Action=='Goal').groupby(['Tournamemnt','Our Score - End of Point','Their Score - End of Point'])['Action'].value_counts().sum()
    except IndexError:
        dminus=0
    return float((dplus-dminus)/n_dpoints)

def minutes_played():
    return None

def touches(player_df,player_name):
    '''
    +1 when offense player picks up or catches a disc after the pull.
    +1 when player recieves a pass. No additional count when this player subsequently passes.
    +1 when player catches a goal.
    +1 when player has a callahan <- not yet implemented.'''
    touches=0
    for i,row in player_df.iterrows():
        roles=[row.Passer,row.Receiver]
        if player_name in roles and row.Action in ['Catch','Throwaway','Goal']:
                if row.Passer==player_name:
                    #print(row.Passer,row.Action,player_df.Receiver.iloc[i-1],player_df.Action.iloc[i-1])
                    try:
                        if player_df.Receiver.iloc[i-1]==player_name: #they received the pass, then threw it
                            pass
                        else: #they picked it up
                            touches+=1
                    except IndexError:
                        #first touch of game
                        touches +=1
                else:
                    touches +=1
                #print(row.Passer,row.Receiver,row.Action,touches)

    return touches

def catches(player_df,player_name):
    '''
    +1 when offense player catches the disc (including for a goal) passed from another player.'''
    ncatches=0
    ccounts=player_df.where(player_df.Receiver==player_name)['Action'].value_counts()
    if 'Catch' in ccounts.keys():
        ncatches+=ccounts['Catch']
    if 'Goal' in ccounts.keys():
        ncatches+=ccounts['Goal']
    return ncatches

def throws(player_df,player_name):
    '''+1 when offense player passes to another player (including for a goal) regardless of whether the pass is caught, i.e., includes drops and throwaways.'''
    return player_df.where(player_df.Passer==player_name)['Action'].value_counts().sum()

def throwaways(player_df,player_name):
    try:
        return player_df.where(player_df.Passer==player_name)['Action'].value_counts()['Throwaway']
    except KeyError:
        return 0

def drops(player_df,player_name):
    try:
        return player_df.where(player_df.Receiver==player_name)['Action'].value_counts()['Drop'].sum()
    except KeyError:
        return 0

def throw_percentage(throws,passer_turnovers):
    '''(throws - passer turnovers) ÷ throws'''
    return float((throws - passer_turnovers)/throws)

def catch_percentage():
    '''catches ÷ (catches + drops)'''
    return float(catches/(catches + drops))
    
#### extras for mixed teams
def throws_to_W(player_df,player_name):
    return player_df.where(player_df.Passer==player_name).where(player_df['Receiver_matchup']=='W')['Action'].value_counts().sum()

def throws_to_M(player_df,player_name):
    return player_df.where(player_df.Passer==player_name).where(player_df['Receiver_matchup']=='M')['Action'].value_counts().sum()

def receives_from_W(player_df,player_name):
    return player_df.where(player_df.Receiver==player_name).where(player_df['Passer_matchup']=='W')['Action'].value_counts().sum()

def receives_from_M(player_df,player_name):
    return player_df.where(player_df.Receiver==player_name).where(player_df['Passer_matchup']=='M')['Action'].value_counts().sum()

#### team-specific:
def offensive_productivity(df):
    '''# of goals ÷ # of O-line2 points'''
    return 0

def break_opportunities(df):
    return 0

def conversion_rate(df):
    '''where opportunities = # of O-line points2 + # of the other team's turnovers...
    # of goals / opportunities'''
    return 0
