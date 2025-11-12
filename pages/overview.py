from dash import dcc, html, Input, Output, callback, register_page
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Register as home page
register_page(__name__, path="/", order=1)

# GitHub raw URLs for the CSVs (replace <username> and <repo> with your actual details)
MASTER_CSV_URL = "Data/master_dexa_data.csv" 
COMPOSITION_CSV_URL = "Data/composition_indices.csv"

def load_data():
    master_df = pd.read_csv(MASTER_CSV_URL)
    master_df["Scan Date"] = pd.to_datetime(master_df["Scan Date"], format="%d-%m-%Y")
    
    composition_df = pd.read_csv(COMPOSITION_CSV_URL)
    composition_df["Scan Date"] = pd.to_datetime(composition_df["Scan Date"], dayfirst=True)
    
    return master_df.sort_values('Scan Date'), composition_df.sort_values('Scan Date')

def get_trend_symbol(current, previous):
    return "↑" if current > previous else "↓" if current < previous else "→"

master_df, composition_df = load_data()

# Layout
layout = html.Div([
    html.H2("DEXA Analysis Overview", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Patient selector
    html.Div([
        html.Label("Select Patient:"),
        dcc.Dropdown(
            id='patient-selector',
            options=[{'label': name, 'value': name} 
                    for name in sorted(master_df["Patient Name"].unique())],
            value=sorted(master_df["Patient Name"].unique())[0],
            clearable=False
        )
    ], style={'width': '300px', 'margin': '0 auto 30px auto'}),
    
    # Stats Cards in a grid
    html.Div([
        # Latest Scan Card
        html.Div([
            html.H4("Latest DEXA Scan", style={'marginBottom': '10px', 'textAlign': 'center'}),
            html.Div(id='latest-scan-info', style={'textAlign': 'center'})
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        
        # Current Ratios Card
        html.Div([
            html.H4("Current Ratios", style={'marginBottom': '10px', 'textAlign': 'center'}),
            html.Div(id='ratios-info', style={'textAlign': 'center'})
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        
        # Current Body Composition Card
        html.Div([
            html.H4("Current Body Composition", style={'marginBottom': '10px', 'textAlign': 'center'}),
            html.Div(id='composition-info', style={'textAlign': 'center'})
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        
        # Records Card
        html.Div([
            html.H4("Personal Records", style={'marginBottom': '10px', 'textAlign': 'center'}),
            html.Div(id='records-info', style={'textAlign': 'center'})
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'})
    ], style={'display': 'grid', 'gridTemplateColumns': '1fr 1fr', 'gap': '20px', 'marginBottom': '30px'}),
    
    # Main Graph
    html.Div([
        dcc.Graph(id='main-trends-graph')
    ], style={'marginBottom': '30px'}),
    
    # Bottom Graphs
    html.Div([
        html.Div([
            dcc.Graph(id='visceral-fat-graph')
        ], style={'width': '48%', 'display': 'inline-block'}),
        
        html.Div([
            dcc.Graph(id='body-composition-graph')
        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
    ])
])

@callback(
    [Output('latest-scan-info', 'children'),
     Output('ratios-info', 'children'),
     Output('composition-info', 'children'),
     Output('records-info', 'children'),
     Output('main-trends-graph', 'figure'),
     Output('visceral-fat-graph', 'figure'),
     Output('body-composition-graph', 'figure')],
    Input('patient-selector', 'value')
)
def update_page_content(selected_patient):
    patient_master_df = master_df[master_df['Patient Name'] == selected_patient]
    patient_composition_df = composition_df[composition_df['Patient Name'] == selected_patient]
    
    total_df = patient_master_df[patient_master_df['Body Part'] == 'Total'].sort_values('Scan Date')
    latest_date = total_df['Scan Date'].max()
    
    # Latest scan info
    latest_weight = total_df[total_df['Scan Date'] == latest_date]['Total Mass (kg)'].iloc[0]
    prev_weight = total_df.iloc[-2]['Total Mass (kg)'] if len(total_df) > 1 else latest_weight
    
    latest_scan = [
        html.P(f"Date: {latest_date.strftime('%d %b %Y')}"),
        html.P(f"Weight: {latest_weight:.1f} kg {get_trend_symbol(latest_weight, prev_weight)}"),
        html.P(f"Days since last scan: {(pd.Timestamp.now() - latest_date).days}")
    ]
    
    # Current Ratios info
    latest_comp = patient_composition_df.iloc[-1]
    ratios_info = [
        html.P(f"BMI: {latest_comp['BMI (kg/m²)']:.1f}"),
        html.P(f"FMI: {latest_comp['Fat Mass Index (FMI)']:.1f}"),
        html.P(f"Android/Gynoid: {latest_comp['Android/Gynoid Fat Ratio']:.2f}"),
        html.P(f"Trunk/Leg Ratio: {latest_comp['Trunk/Legs Fat Ratio']:.2f}"),
        html.P(f"Lean Mass Index: {latest_comp['Lean Mass Index (kg/m²)']:.1f}")
    ]
    
    # Current Body Composition info
    prev_comp = patient_composition_df.iloc[-2] if len(patient_composition_df) > 1 else latest_comp
    composition_info = [
        html.P(f"Body Fat: {latest_comp['Total Body Fat (%)']:.1f}% {get_trend_symbol(latest_comp['Total Body Fat (%)'], prev_comp['Total Body Fat (%)'])}"),
        html.P(f"Lean Mass: {latest_comp['Total Lean Body (%)']:.1f}% {get_trend_symbol(latest_comp['Total Lean Body (%)'], prev_comp['Total Lean Body (%)'])}"),
        html.P(f"Bone Mass: {latest_comp['Total Bone Mass (%)']:.1f}%")
    ]
    
    # Records info
    min_lean = total_df['Lean (g)'].min() / 1000  # Convert to kg
    max_lean = total_df['Lean (g)'].max() / 1000
    records_info = [
        html.P(f"Lowest Weight: {total_df['Total Mass (kg)'].min():.1f} kg ({total_df.loc[total_df['Total Mass (kg)'].idxmin(), 'Scan Date'].strftime('%d %b %Y')})"),
        html.P(f"Lowest Body Fat: {patient_composition_df['Total Body Fat (%)'].min():.1f}% ({patient_composition_df.loc[patient_composition_df['Total Body Fat (%)'].idxmin(), 'Scan Date'].strftime('%d %b %Y')})"),
        html.P(f"Highest Lean Mass: {max_lean:.1f} kg ({total_df.loc[total_df['Lean (g)'].idxmax(), 'Scan Date'].strftime('%d %b %Y')})"),
        html.P(f"Lowest Lean Mass: {min_lean:.1f} kg ({total_df.loc[total_df['Lean (g)'].idxmin(), 'Scan Date'].strftime('%d %b %Y')})")
    ]
    
    # Main trends graph
    main_fig = make_subplots(specs=[[{"secondary_y": True}]])
    main_fig.add_trace(go.Scatter(x=total_df['Scan Date'], y=total_df['Total Mass (kg)'],
                                  name="Total Weight", line=dict(color='#2C3E50', width=3)),
                       secondary_y=False)
    main_fig.add_trace(go.Scatter(x=total_df['Scan Date'], y=total_df['Lean (g)']/1000,
                                  name="Lean Mass", line=dict(color='#E74C3C', width=3)),
                       secondary_y=True)
    main_fig.update_layout(
        title="Weight and Lean Mass Trends",
        height=400,
        template="plotly_white",
        showlegend=True,
    )
    
    # Visceral fat graph
    visceral_fig = px.line(patient_composition_df, x='Scan Date', y='Visceral Fat Area (cm²)',
                          title="Visceral Fat Area Trend")
    
    # Body composition graph
    comp_fig = go.Figure()
    comp_fig.add_trace(go.Scatter(x=patient_composition_df['Scan Date'], 
                                  y=patient_composition_df['Total Body Fat (%)'], name="Fat %"))
    comp_fig.add_trace(go.Scatter(x=patient_composition_df['Scan Date'], 
                                  y=patient_composition_df['Total Lean Body (%)'], name="Lean %"))
    
    return latest_scan, ratios_info, composition_info, records_info, main_fig, visceral_fig, comp_fig
