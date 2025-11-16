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
        df["Scan Date"] = pd.to_datetime(df["Scan Date"], format="%m-%d-%Y", errors="coerce")
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
            'padding': '10px 16px',
            'border': '2px solid #ddd',
            'borderRadius': '6px',
            'backgroundColor': 'white',
            'cursor': 'pointer',
            'minWidth': '110px',
            'textAlign': 'center',
            'fontSize': '14px',
            'fontWeight': '500',
            'transition': 'all 0.2s',
            'color': '#2c3e50'
        }
    )

def format_ratio(fat, lean):
    ratio = fat / lean
    denominator = int(round(1 / ratio)) if ratio < 1 else 1
    numerator = round(ratio * denominator, 1)
    return f"{numerator:.1f}:{denominator}"

def create_button_group(group, parts):
    return html.Div([
        html.Label(group, style={
            'fontWeight': '600', 
            'marginBottom': '8px',
            'color': '#2c3e50',
            'fontSize': '14px',
            'display': 'block'
        }),
        html.Div([create_button(part) for part in parts],
                 style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '8px'})
    ], style={'marginBottom': '20px'})

def layout():
    return html.Div([
        # Header
        html.Div([
            html.H1("Body Part Analysis", style={
                'textAlign': 'center', 
                'marginBottom': '10px',
                'color': '#2c3e50',
                'fontWeight': '600'
            }),
            html.P("Compare composition trends across different body regions", style={
                'textAlign': 'center',
                'color': '#7f8c8d',
                'marginBottom': '0'
            })
        ], style={
            'backgroundColor': 'white', 
            'padding': '25px', 
            'marginBottom': '20px',
            'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
        }),
        
        # Main content area
        html.Div([
            # Left sidebar - Controls
            html.Div([
                # Patient selector
                html.Div([
                    html.Label("Select Patient", style={
                        'fontWeight': '600', 
                        'marginBottom': '10px',
                        'color': '#2c3e50',
                        'fontSize': '15px',
                        'display': 'block'
                    }),
                    dcc.Dropdown(
                        id='patient-dropdown',
                        options=[{'label': name, 'value': name} 
                                 for name in sorted(df["Patient Name"].dropna().unique())],
                        value=sorted(df["Patient Name"].dropna().unique())[0] if not df.empty else None,
                        clearable=False,
                        style={'marginBottom': '25px'}
                    )
                ]),

                # Body part selection
                html.Div([
                    html.Label("Select Body Parts", style={
                        'fontWeight': '600', 
                        'marginBottom': '12px',
                        'color': '#2c3e50',
                        'fontSize': '15px',
                        'display': 'block'
                    }),
                    *[create_button_group(group, parts) for group, parts in BODY_PART_GROUPS.items()]
                ], style={
                    'backgroundColor': 'white', 
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                
                # Stats card
                html.Div([
                    html.Div(id='stats-card')
                ], style={
                    'backgroundColor': 'white', 
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
            ], style={
                'width': '22%', 
                'float': 'left', 
                'padding': '0 15px 0 0'
            }),
            
            # Right side - Graphs
            html.Div([
                # Main trends graph
                html.Div([
                    dcc.Graph(id='mass-trends', style={'height': '500px'})
                ], style={
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'marginBottom': '20px'
                }),
                
                # Ratio trend graph
                html.Div([
                    dcc.Graph(id='ratio-trend', style={'height': '400px'})
                ], style={
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                })
            ], style={
                'width': '76%', 
                'float': 'right', 
                'padding': '0'
            })
        ], style={'overflow': 'hidden'})
    ], style={
        'backgroundColor': '#f5f7fa', 
        'padding': '20px', 
        'minHeight': '100vh'
    })

@callback(
    [Output('mass-trends', 'figure'),
     Output('ratio-trend', 'figure'),
     Output('stats-card', 'children'),
     Output({'type': 'body-part-button', 'index': ALL}, 'style')],
    [Input({'type': 'body-part-button', 'index': ALL}, 'n_clicks'),
     Input('patient-dropdown', 'value')],
    [State({'type': 'body-part-button', 'index': ALL}, 'style')],
    prevent_initial_call=False
)
def update_charts(n_clicks, selected_patient, current_styles):
    # Build button IDs
    ctx = callback_context
    button_ids = [{'type': 'body-part-button', 'index': k['id']['index']} 
                  for k in ctx.inputs_list[0]]

    # Determine which buttons are selected
    selected_parts = []
    
    if ctx.triggered and ctx.triggered[0]['prop_id'] != '.':
        # A button was clicked
        triggered_id = ctx.triggered[0]['prop_id']
        triggered_dict = eval(triggered_id.split('.')[0])
        triggered_index = next(i for i, btn in enumerate(button_ids) 
                               if btn['index'] == triggered_dict['index'])
        
        # Check current selection state
        currently_selected = []
        for i, style in enumerate(current_styles):
            if style and style.get('backgroundColor') == '#3498db':
                currently_selected.append(i)
        
        # Toggle logic
        if triggered_index in currently_selected:
            currently_selected.remove(triggered_index)
        else:
            # If clicking Total, deselect others
            if button_ids[triggered_index]['index'] == 'Total':
                currently_selected = [triggered_index]
            else:
                # Deselect Total if it's selected
                total_index = next(i for i, btn in enumerate(button_ids) if btn['index'] == 'Total')
                if total_index in currently_selected:
                    currently_selected.remove(total_index)
                currently_selected.append(triggered_index)
        
        # If nothing selected, default to Total
        if not currently_selected:
            total_index = next(i for i, btn in enumerate(button_ids) if btn['index'] == 'Total')
            currently_selected = [total_index]
        
        selected_indices = currently_selected
    else:
        # Initial load - select Total by default
        total_index = next(i for i, btn in enumerate(button_ids) if btn['index'] == 'Total')
        selected_indices = [total_index]
    
    # Build selected parts list
    selected_parts = [button_ids[i]['index'] for i in selected_indices]
    
    # Update button styles
    new_styles = []
    for i, btn in enumerate(button_ids):
        if i in selected_indices:
            # Selected style
            new_styles.append({
                'margin': '5px',
                'padding': '10px 16px',
                'border': '2px solid #3498db',
                'borderRadius': '6px',
                'backgroundColor': '#3498db',
                'cursor': 'pointer',
                'minWidth': '110px',
                'textAlign': 'center',
                'fontSize': '14px',
                'fontWeight': '600',
                'transition': 'all 0.2s',
                'color': 'white'
            })
        else:
            # Unselected style
            new_styles.append({
                'margin': '5px',
                'padding': '10px 16px',
                'border': '2px solid #ddd',
                'borderRadius': '6px',
                'backgroundColor': 'white',
                'cursor': 'pointer',
                'minWidth': '110px',
                'textAlign': 'center',
                'fontSize': '14px',
                'fontWeight': '500',
                'transition': 'all 0.2s',
                'color': '#2c3e50'
            })
    
    # Filter data by patient + body part
    if selected_patient:
        filtered_df = df[
            (df['Body Part'].isin(selected_parts)) &
            (df['Patient Name'] == selected_patient)
        ].sort_values(['Scan Date', 'Body Part'])
    else:
        filtered_df = df[df['Body Part'].isin(selected_parts)].sort_values(['Scan Date', 'Body Part'])
    
    if filtered_df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No data available",
            template="plotly_white",
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return empty_fig, empty_fig, [html.P("Select a patient and body part", style={'color': '#7f8c8d'})], new_styles
    
    # Color palette
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', 
              '#1abc9c', '#e67e22', '#34495e', '#16a085', '#c0392b']
    
    # ========== FAT + LEAN MASS TRENDS ==========
    main_fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    for i, part in enumerate(selected_parts):
        part_data = filtered_df[filtered_df['Body Part'] == part]
        
        # Fat mass (dotted line, left axis)
        main_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], 
                y=part_data['Fat (g)'],
                name=f"{part} - Fat",
                line=dict(color=colors[i % len(colors)], width=3, dash='dot'),
                mode='lines+markers',
                marker=dict(size=6)
            ), 
            secondary_y=False
        )
        
        # Lean mass (solid line, right axis)
        main_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], 
                y=part_data['Lean (g)'],
                name=f"{part} - Lean",
                line=dict(color=colors[i % len(colors)], width=3),
                mode='lines+markers',
                marker=dict(size=6)
            ), 
            secondary_y=True
        )
    
    main_fig.update_layout(
        title={
            'text': "Fat Mass & Lean Mass Trends",
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="#ddd",
            borderwidth=1
        )
    )
    
    main_fig.update_yaxes(
        title_text="Fat Mass (g)", 
        secondary_y=False, 
        gridcolor='#ecf0f1',
        showgrid=True
    )
    main_fig.update_yaxes(
        title_text="Lean Mass (g)", 
        secondary_y=True, 
        gridcolor='#ecf0f1',
        showgrid=False
    )
    
    # ========== RATIO TREND ==========
    ratio_fig = go.Figure()
    
    for i, part in enumerate(selected_parts):
        part_data = filtered_df[filtered_df['Body Part'] == part]
        ratio = part_data['Fat (g)'] / part_data['Lean (g)']
        
        ratio_fig.add_trace(
            go.Scatter(
                x=part_data['Scan Date'], 
                y=ratio, 
                name=part,
                line=dict(color=colors[i % len(colors)], width=3),
                mode='lines+markers',
                marker=dict(size=7)
            )
        )
    
    ratio_fig.update_layout(
        title={
            'text': "Fat-to-Lean Mass Ratio",
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        yaxis_title="Fat:Lean Ratio",
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        yaxis=dict(gridcolor='#ecf0f1'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # ========== STATS CARD ==========
    latest_date = filtered_df['Scan Date'].max()
    latest_data = filtered_df[filtered_df['Scan Date'] == latest_date]
    
    stats_card = [
        html.H4("Latest Measurements", style={
            'marginBottom': '20px',
            'color': '#2c3e50',
            'fontSize': '18px',
            'borderBottom': '2px solid #ecf0f1',
            'paddingBottom': '10px'
        }),
        html.Div(
            f"{latest_date.strftime('%b %d, %Y')}",
            style={
                'marginBottom': '20px',
                'color': '#7f8c8d',
                'fontSize': '14px',
                'fontStyle': 'italic'
            }
        )
    ]
    
    for i, part in enumerate(selected_parts):
        part_data = latest_data[latest_data['Body Part'] == part]
        if not part_data.empty:
            fat = part_data['Fat (g)'].iloc[0]
            lean = part_data['Lean (g)'].iloc[0]
            
            stats_card.append(
                html.Div([
                    html.Div(
                        part,
                        style={
                            'fontWeight': '600',
                            'color': colors[i % len(colors)],
                            'fontSize': '15px',
                            'marginBottom': '8px'
                        }
                    ),
                    html.Div([
                        html.Span("Fat: ", style={'color': '#7f8c8d', 'fontSize': '13px'}),
                        html.Span(f"{fat:,.0f}g", style={'fontWeight': 'bold', 'color': '#2c3e50'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span("Lean: ", style={'color': '#7f8c8d', 'fontSize': '13px'}),
                        html.Span(f"{lean:,.0f}g", style={'fontWeight': 'bold', 'color': '#2c3e50'})
                    ], style={'marginBottom': '5px'}),
                    html.Div([
                        html.Span("Ratio: ", style={'color': '#7f8c8d', 'fontSize': '13px'}),
                        html.Span(f"{format_ratio(fat, lean)}", style={'fontWeight': 'bold', 'color': '#2c3e50'})
                    ])
                ], style={
                    'marginBottom': '20px',
                    'paddingBottom': '15px',
                    'borderBottom': '1px solid #ecf0f1' if i < len(selected_parts) - 1 else 'none'
                })
            )
    
    return main_fig, ratio_fig, stats_card, new_styles