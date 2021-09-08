import pandas as pd
import numpy as np
from plotly import graph_objects as go

def global_layout():
    '''make stuff look cool '''
    layout = go.Layout(
    images=[dict(
        source="https://raw.githubusercontent.com/elastufka/presentations/master/images/ZU_logo1.png",
        xref="paper", yref="paper",
        x=0, y=1.05,
        sizex=0.2, sizey=0.2,
        xanchor="right", yanchor="bottom"
      )])
    return layout

def gender_ratio(seven_on,wline,mline):
    wcount,mcount=0,0
 
    for p in seven_on:
        if p in wline:
            wcount +=1
        else:
            mcount +=1
    if wcount > mcount:
        return 1
    else:
        return 0

def is_break(line, action, receiver):
    try:
        their_goal=np.isnan(receiver)
        if line == 'O' and action == 'Goal': #their break
            return -1
        elif line == 'D' and action == 'Goal': #their hold
            return -.5
    except TypeError:
        if line == 'D' and action == 'Goal': #our break
            return 1
        elif line == 'O' and action == 'Goal': #our hold
            return .5
    return None
    
def give_and_go(df,idx,row):
    '''for either person or gender matchup'''
    if row.Passer == df.Receiver[idx+1]:
        return 1, row.Passer_matchup + row.Receiver_matchup, [row.Passer,row.Receiver]
    else:
        return None,None, None

def is_hockey_assist(df,idx,row):
    if row.Action=='Catch' and df.Action[idx+1]!='Throwaway' and df.Action[idx+2]=='Goal' and type(df.Receiver[idx+2]) !=float: #make sure it's our goal
        return row.Receiver
    else:
        return None
    
def is_assist(df,idx,row):
    if row.Action=='Catch' and df.Action[idx+1]=='Goal' and type(df.Receiver[idx+1]) !=float: #make sure it's our goal
        return row.Receiver
    else:
        return None
        
def is_turn(df,idx,row):
    if row.Action=='Throwaway' or row.Action == 'D' or row.Action == 'Drop':
        return 1
    else:
        return 0
        
def goal_scorer(df,idx,row):
    if row.Action=='Goal' and type(row.Receiver) != float: #make sure it's our goal
        return row.Receiver
    else:
        return None
        
def sort_touches(idx,row):
    ''' touch by M or W?'''
    if row.Action in ['Catch','Goal','Throwaway','Pull','PullOb']:
        return row.Passer_matchup
    elif row.Action =='D': #not Defense oops
        return row.Defender_matchup
    elif row.Action =='Drop':
        return row.Receiver_matchup
    else:
        return None
        
def game_flow_fig(df,opponent,slidew,slideh):
    '''well this is a hot mess'''
    opdf=df.where(df.Opponent==opponent)
    pkeys=['Player '+str(i) for i in range(7)]
    pkeys.append('Scorer')
    pkeys.append('Assist')
    pkeys.append('W4_M3')
    gdf=opdf.groupby('PointID')[pkeys].first().reset_index()
    total_points=gdf.index.max()+1
    breaks=opdf.Break.dropna().reset_index(drop=True).values
    turns=opdf.groupby('PointID')[['Turn','Catch','Break']].sum().reset_index()
    #print(turns)
    fig_dict = {
        "data": [],
        "layout": {},
        "frames": []
    }

    # fill in most of layout
    fig_dict["layout"]["xaxis"] = {"range": [0.5, total_points+.5], "title": "Points"}
    ticktext=['Their Break','Their Hold','','Our Hold','Our Break']
    fig_dict["layout"]["yaxis"] = {"title":'Point Type',"range":[-1.1,1.5],"ticktext":ticktext,"tickvals":[-1,-.5,0,.5,1]}
    fig_dict["layout"]["hovermode"] = "closest"
    fig_dict["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 500, "redraw": False},
                                    "fromcurrent": True, "transition": {"duration": 300,
                                                                        "easing": "quadratic-in-out"}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                      "mode": "immediate",
                                      "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "bottom",
        "xanchor": "right",
        "currentvalue": {
            "font": {"size": 14},
            "prefix": "Point:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b":10,'t':10},
        "len": 0.9,
        "x": 1,
        "y": -.4,
        "steps": []
    }

    frames=[go.Frame(data=go.Scatter(x=[0],y=[0],line_shape='hv',mode='lines+markers'),name=f'frame{0}')
    ]
    for p in range(1,total_points):
        annotations=[]
        if gdf.W4_M3[p-1] == 1:
            gstring="4W3M: "
        else:
            gstring="4M3W: "
        pstring=gstring+ ','.join([gdf[k][p-1] for k in pkeys[:-3]])
        namestr=gdf.PointID[p-1][-4:]
        title='FucZH '+str(int(namestr[:2]))+'-'+str(int(namestr[2:]))+' '+opponent
        annotations=[go.layout.Annotation(x=p,y=breaks[p-1],xref="x",yref="y",text=pstring,font = dict(color='blue'))]
        annotations.append(go.layout.Annotation(x=.5,y=1.4,xref="paper",yref="y",text=title,showarrow=False,font = dict(size = 18,color='orange')))
        tstring=f"Completed Passes: {turns.Catch[p-1]:.0f},Turns: {turns.Turn[p-1]:.0f}"
        annotations.append(go.layout.Annotation(x=total_points-3,y=1.3,xref="x",yref="y",text=tstring,showarrow=False))

        if breaks[p-1] > 0: #we scored
            sstring=f"Assist: {gdf.Assist[p-1]}, Goal:{gdf.Scorer[p-1]}"
            annotations.append(go.layout.Annotation(x=total_points-3,y=1.4,xref="x",yref="y",text=sstring,showarrow=False))
        layout_i = go.Layout(annotations=annotations)
        
        frames.append(go.Frame(data=go.Scatter(x=list(range(1,p+1)),y=breaks[:p],line_shape='hvh',mode='lines+markers'),layout=layout_i,name=f'frame{p}'))
        #frame['layout'].update(title_text=title)
        #frames.append(frame)
        #print(breaks[:p],frames[p-1]['data'][0]['y'])
        slider_step = {"args": [[f'frame{p}'],
            {"frame": {"duration": 300, "redraw": False},
             "mode": "immediate",
             "transition": {"duration": 300}}
        ],
            "label": p,
            "method": "animate"}
        sliders_dict["steps"].append(slider_step)

    fig_dict['data']={'x':[0],'y':[0],'mode':'lines+markers'}
    fig_dict['frames']=frames
    fig_dict["layout"]["sliders"] = [sliders_dict]
    fig = go.Figure(fig_dict)

    #plotly.offline.plot(fig,'testfig.html')
    logo_layout=global_layout()
    fig.update_layout(logo_layout)
    fig.update_layout(title='Game Flow',width=slidew,height=slideh)
    #fig.update_yaxes(ticktext=['Their Break', 'Their Hold','','Our Hold','Our Break'])
    return fig


