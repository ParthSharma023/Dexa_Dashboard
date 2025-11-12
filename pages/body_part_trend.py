from dash import dcc, html, Input, Output, callback, ALL, callback_context, register_page, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from dash.exceptions import PreventUpdate
import dash

# Register this page
register_page(__name__, 
             path='/body-part-trend',
             name='Body Part Trends',
             order=2)

# CSV path
MASTER_CSV_URL = "Data/master_dexa_data.csv"     

# Load the data
def load_data():
    try:
        df = pd.read_csv(MASTER_CSV_URL)
        df["Scan Date"] = pd.to_datetime(df["Scan Date"], format="%d-%m-%Y", errors="coerce")
        df.dropna(subset=["Scan Date"], inplace=True)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

# Group body parts
BODY_PART_GROUPS = {
    'Arms': ['Left Arm', 'Right Arm'],
    'Legs': ['Left Leg', 'Right Leg'],
   # 'Torso': ['Left Ribs', 'Right Ribs', 'T Spine', 'L Spine', 'Pelvis'],
    'Total': ['Total'],
    'Regions': ['Android', 'Gynoid']
}

def create_button(part):
    return html.Button(
        part,
        id={'type': 'body-part-button', 'index': part},
        n_clicks=0,
        className='body-part-btn',
        style={
            'margin': '5px',
            'padding': '8px 15px',
            'border': '1px solid #ddd',
            'borderRadius': '4px',
            'backgroundColor': 'white',
            'cursor': 'pointer',
            'minWidth': '120px',
            'textAlign': 'center'
        }
    )

def format_ratio(fat, lean):
    ratio = fat / lean
    denominator = int(round(1 / ratio)) if ratio < 1 else 1
    numerator = round(ratio * denominator, 1)
    return f"{numerator:.1f}:{denominator}"

def create_button_group(group, parts):
    return html.Div([
        html.Label(group, style={'fontWeight': 'bold', 'marginBottom': '5px'}),
        html.Div([create_button(part) for part in parts],
                 style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '5px'})
    ], style={'marginBottom': '15px'})

def layout():
    return html.Div([
        html.H2("Body Part Analysis", style={'textAlign': 'center', 'marginBottom': '20px'}),
        
        # Controls
        html.Div([
            # Patient selector
            html.Div([
                html.Label("Select Patient:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                dcc.Dropdown(
                    id='patient-dropdown',
                    options=[{'label': name, 'value': name} 
                             for name in sorted(df["Patient Name"].dropna().unique())],
                    value=None,
                    placeholder="Choose a patient",
                    style={'marginBottom': '20px'}
                )
            ]),

            # Body part buttons
            html.Div([
                html.Label("Select Body Parts:", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                *[create_button_group(group, parts) for group, parts in BODY_PART_GROUPS.items()]
            ], style={'backgroundColor': 'white', 'padding': '20px',
                      'borderRadius': '8px','boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                      'marginBottom': '20px'}),
            
            # Stats card
            html.Div(id='stats-card', style={'backgroundColor': 'white', 'padding': '20px',
                                             'borderRadius': '8px','boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
        ], style={'width': '15%', 'float': 'left', 'padding': '10px'}),
        
        # Graphs
        html.Div([
            dcc.Graph(id='mass-trends', style={'marginBottom': '20px', 'height': '500px'}),
            dcc.Graph(id='ratio-trend', style={'height': '400px'})
        ], style={'width': '80%', 'float': 'right', 'padding': '10px'})
    ])

@callback(
    [Output('mass-trends', 'figure'),
     Output('ratio-trend', 'figure'),
     Output('stats-card', 'children'),
     Output({'type': 'body-part-button', 'index': ALL}, 'className')],
    [Input({'type': 'body-part-button', 'index': ALL}, 'n_clicks'),
     Input('patient-dropdown', 'value')],
    [State({'type': 'body-part-button', 'index': ALL}, 'className')],
    prevent_initial_call=True
)
def update_charts(n_clicks, selected_patient, current_classes):
    if not any(n_clicks):
        raise PreventUpdate

    # Build button IDs
    ctx = callback_context
    button_ids = [{'type': 'body-part-button', 'index': k['id']['index']} 
                  for k in ctx.inputs_list[0]]

    triggered = ctx.triggered[0] if ctx.triggered else None
    if triggered is None:
        return dash.no_update
        
    triggered_id = triggered['prop_id']
    triggered_dict = eval(triggered_id.split('.')[0])
    triggered_index = next(i for i, btn in enumerate(button_ids) 
                           if btn['index'] == triggered_dict['index'])

    new_classes = []
    selected_parts = []

    # Handle "Total" button special case
    total_index = next(i for i, btn in enumerate(button_ids) if btn['index'] == 'Total')
    was_total_selected = 'selected' in (current_classes[total_index] or '')
    is_clicking_non_total = triggered_index != total_index
    
    for i, _ in enumerate(n_clicks):
        is_total = button_ids[i]['index'] == 'Total'
        if was_total_selected and is_clicking_non_total:
            if is_total:
                new_classes.append('body-part-btn')
            elif i == triggered_index:
                new_classes.append('body-part-btn selected')
            else:
                new_classes.append('body-part-btn')
        else:
            is_selected = 'body-part-btn selected' if (
                ('selected' not in (current_classes[i] or '') and i == triggered_index) or
                ('selected' in (current_classes[i] or '') and i != triggered_index)
            ) else 'body-part-btn'
            new_classes.append(is_selected)
        if 'selected' in new_classes[-1]:
            selected_parts.append(button_ids[i]['index'])
    
    if not selected_parts:
        selected_parts = ['Total']
        new_classes = ['body-part-btn selected' if id['index'] == 'Total' else 'body-part-btn' 
                       for id in button_ids]
    
    # Filter data by patient + body part
    if selected_patient:
        filtered_df = df[
            (df['Body Part'].isin(selected_parts)) &
            (df['Patient Name'] == selected_patient)
        ].sort_values(['Scan Date', 'Body Part'])
    else:
        filtered_df = df[df['Body Part'].isin(selected_parts)].sort_values(['Scan Date', 'Body Part'])
    
    if filtered_df.empty:
        return px.line(), px.line(), [html.P("No data available")], new_classes
    
    # Fat + Lean trend plot
    main_fig = make_subplots(specs=[[{"secondary_y": True}]])
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for i, part in enumerate(selected_parts):
        part_data = filtered_df[filtered_df['Body Part'] == part]
        main_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], y=part_data['Fat (g)'],
                name=f"{part} - Fat",
                line=dict(color=colors[i], width=3, dash='dot'),
                mode='lines+markers'
            ), secondary_y=False
        )
        main_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], y=part_data['Lean (g)'],
                name=f"{part} - Lean",
                line=dict(color=colors[i], width=3),
                mode='lines+markers'
            ), secondary_y=True
        )
    
    main_fig.update_layout(
        title="Fat Mass and Lean Mass Trends", template="plotly_white",
        plot_bgcolor='white', paper_bgcolor='white',
        yaxis=dict(showgrid=False, title="Fat Mass (g)"),
        yaxis2=dict(showgrid=False, title="Lean Mass (g)")
    )
    
    # Ratio trend
    ratio_fig = go.Figure()
    for i, part in enumerate(selected_parts):
        part_data = filtered_df[filtered_df['Body Part'] == part]
        ratio = part_data['Fat (g)'] / part_data['Lean (g)']
        ratio_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], y=ratio, name=f"{part}",
                line=dict(color=colors[i], width=3), mode='lines+markers'
            )
        )
    ratio_fig.update_layout(
        title="Fat-to-Lean Mass Ratio Trend", template="plotly_white",
        yaxis_title="Fat:Lean Mass Ratio", plot_bgcolor='white', paper_bgcolor='white'
    )
    
    # Stats card
    latest_date = filtered_df['Scan Date'].max()
    latest_data = filtered_df[filtered_df['Scan Date'] == latest_date]
    stats_card = [html.H4("Latest Measurements", style={'marginBottom': '15px'})]
    for part in selected_parts:
        part_data = latest_data[latest_data['Body Part'] == part]
        if not part_data.empty:
            fat, lean = part_data['Fat (g)'].iloc[0], part_data['Lean (g)'].iloc[0]
            stats_card.extend([
                html.H5(part, style={'marginTop': '10px', 'marginBottom': '5px'}),
                html.P(f"Fat Mass: {fat:,.0f}g"),
                html.P(f"Lean Mass: {lean:,.0f}g"),
                html.P(f"Fat:Lean Ratio: {format_ratio(fat, lean)}")
            ])
    
    return main_fig, ratio_fig, stats_card, new_classes
