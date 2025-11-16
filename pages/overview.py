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

# CSV paths
MASTER_CSV_URL = "Data/master_dexa_data.csv" 
COMPOSITION_CSV_URL = "Data/composition_indices.csv"

def load_data():
    master_df = pd.read_csv(MASTER_CSV_URL)
    master_df["Scan Date"] = pd.to_datetime(master_df["Scan Date"], format="%m-%d-%Y")
    
    composition_df = pd.read_csv(COMPOSITION_CSV_URL)
    composition_df["Scan Date"] = pd.to_datetime(composition_df["Scan Date"], format="%m-%d-%Y")
    
    return master_df.sort_values('Scan Date'), composition_df.sort_values('Scan Date')

def get_trend_symbol(current, previous):
    return "↑" if current > previous else "↓" if current < previous else "→"

def get_trend_color(current, previous, lower_is_better=False):
    """Returns color based on trend direction"""
    if current > previous:
        return '#27ae60' if not lower_is_better else '#e74c3c'  # green if good, red if bad
    elif current < previous:
        return '#e74c3c' if not lower_is_better else '#27ae60'
    return '#95a5a6'  # gray for no change

master_df, composition_df = load_data()

# Layout with improved visual hierarchy
layout = html.Div([
    # Header with patient selector
    html.Div([
        html.H1("DEXA Patient Story", style={
            'textAlign': 'center', 
            'marginBottom': '10px',
            'color': '#2c3e50',
            'fontWeight': '600'
        }),
        html.Div([
            dcc.Dropdown(
                id='patient-selector',
                options=[{'label': name, 'value': name} 
                        for name in sorted(master_df["Patient Name"].unique())],
                value=sorted(master_df["Patient Name"].unique())[0],
                clearable=False,
                style={'fontSize': '16px'}
            )
        ], style={'width': '400px', 'margin': '0 auto 30px auto'})
    ], style={'backgroundColor': 'white', 'padding': '20px', 'marginBottom': '20px', 
              'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'}),
    
    # Key Metrics Banner (Big Numbers)
    html.Div(id='key-metrics-banner', style={
        'display': 'grid', 
        'gridTemplateColumns': 'repeat(4, 1fr)', 
        'gap': '15px', 
        'marginBottom': '25px'
    }),
    
    # Main Story Section - 2 columns
    html.Div([
        # Left: Timeline & Composition
        html.Div([
            # Body Composition Over Time (Primary Story)
            html.Div([
                dcc.Graph(id='body-composition-timeline', style={'height': '400px'})
            ], style={
                'backgroundColor': 'white', 
                'padding': '20px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),
            
            # Weight & Lean Mass Trends
            html.Div([
                dcc.Graph(id='weight-lean-trends', style={'height': '350px'})
            ], style={
                'backgroundColor': 'white', 
                'padding': '20px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ], style={'width': '65%', 'display': 'inline-block', 'verticalAlign': 'top'}),
        
        # Right: Current Status & Insights
        html.Div([
            # Current Snapshot Card
            html.Div([
                html.H3("📊 Current Status", style={
                    'marginBottom': '15px', 
                    'color': '#2c3e50',
                    'fontSize': '20px'
                }),
                html.Div(id='current-status-card')
            ], style={
                'backgroundColor': 'white', 
                'padding': '20px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),
            
            # Progress & Records
            html.Div([
                html.H3("🏆 Progress & Records", style={
                    'marginBottom': '15px', 
                    'color': '#2c3e50',
                    'fontSize': '20px'
                }),
                html.Div(id='progress-records-card')
            ], style={
                'backgroundColor': 'white', 
                'padding': '20px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),
            
            # Key Ratios
            html.Div([
                html.H3("📐 Key Ratios", style={
                    'marginBottom': '15px', 
                    'color': '#2c3e50',
                    'fontSize': '20px'
                }),
                html.Div(id='ratios-card')
            ], style={
                'backgroundColor': 'white', 
                'padding': '20px', 
                'borderRadius': '8px', 
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
            })
        ], style={'width': '33%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'})
    ]),
    
    # Bottom: Visceral Fat (Important Health Metric)
    html.Div([
        dcc.Graph(id='visceral-fat-graph', style={'height': '300px'})
    ], style={
        'backgroundColor': 'white', 
        'padding': '20px', 
        'borderRadius': '8px', 
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginTop': '25px'
    })
], style={'backgroundColor': '#f5f7fa', 'padding': '20px', 'minHeight': '100vh'})

@callback(
    [Output('key-metrics-banner', 'children'),
     Output('current-status-card', 'children'),
     Output('progress-records-card', 'children'),
     Output('ratios-card', 'children'),
     Output('body-composition-timeline', 'figure'),
     Output('weight-lean-trends', 'figure'),
     Output('visceral-fat-graph', 'figure')],
    Input('patient-selector', 'value')
)
def update_page_content(selected_patient):
    patient_master_df = master_df[master_df['Patient Name'] == selected_patient]
    patient_composition_df = composition_df[composition_df['Patient Name'] == selected_patient]
    
    total_df = patient_master_df[patient_master_df['Body Part'] == 'Total'].sort_values('Scan Date')
    latest_date = total_df['Scan Date'].max()
    latest_row = total_df[total_df['Scan Date'] == latest_date].iloc[0]
    latest_comp = patient_composition_df.iloc[-1]
    
    # Previous values for comparison
    prev_row = total_df.iloc[-2] if len(total_df) > 1 else latest_row
    prev_comp = patient_composition_df.iloc[-2] if len(patient_composition_df) > 1 else latest_comp
    
    # ========== KEY METRICS BANNER (Big Numbers) ==========
    key_metrics = [
        # Weight
        html.Div([
            html.Div("Current Weight", style={'fontSize': '14px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest_row['Total Mass (kg)']:.1f}", style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.Span(" kg", style={'fontSize': '18px', 'color': '#7f8c8d'})
            ]),
            html.Div(
                f"{get_trend_symbol(latest_row['Total Mass (kg)'], prev_row['Total Mass (kg)'])} {abs(latest_row['Total Mass (kg)'] - prev_row['Total Mass (kg)']):.1f} kg", 
                style={'fontSize': '14px', 'color': get_trend_color(latest_row['Total Mass (kg)'], prev_row['Total Mass (kg)'], lower_is_better=False), 'marginTop': '5px'}
            )
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
        
        # Body Fat %
        html.Div([
            html.Div("Body Fat", style={'fontSize': '14px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest_comp['Total Body Fat (%)']:.1f}", style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.Span(" %", style={'fontSize': '18px', 'color': '#7f8c8d'})
            ]),
            html.Div(
                f"{get_trend_symbol(latest_comp['Total Body Fat (%)'], prev_comp['Total Body Fat (%)'])} {abs(latest_comp['Total Body Fat (%)'] - prev_comp['Total Body Fat (%)']):.1f}%", 
                style={'fontSize': '14px', 'color': get_trend_color(latest_comp['Total Body Fat (%)'], prev_comp['Total Body Fat (%)'], lower_is_better=True), 'marginTop': '5px'}
            )
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
        
        # Lean Mass
        html.Div([
            html.Div("Lean Mass", style={'fontSize': '14px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest_row['Lean (g)']/1000:.1f}", style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.Span(" kg", style={'fontSize': '18px', 'color': '#7f8c8d'})
            ]),
            html.Div(
                f"{get_trend_symbol(latest_row['Lean (g)'], prev_row['Lean (g)'])} {abs(latest_row['Lean (g)'] - prev_row['Lean (g)'])/1000:.1f} kg", 
                style={'fontSize': '14px', 'color': get_trend_color(latest_row['Lean (g)'], prev_row['Lean (g)'], lower_is_better=False), 'marginTop': '5px'}
            )
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'}),
        
        # BMI
        html.Div([
            html.Div("BMI", style={'fontSize': '14px', 'color': '#7f8c8d', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest_comp['BMI (kg/m²)']:.1f}", style={'fontSize': '36px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
                html.Span(" kg/m²", style={'fontSize': '18px', 'color': '#7f8c8d'})
            ]),
            html.Div(
                f"{get_trend_symbol(latest_comp['BMI (kg/m²)'], prev_comp['BMI (kg/m²)'])} {abs(latest_comp['BMI (kg/m²)'] - prev_comp['BMI (kg/m²)']):.1f}", 
                style={'fontSize': '14px', 'color': get_trend_color(latest_comp['BMI (kg/m²)'], prev_comp['BMI (kg/m²)'], lower_is_better=False), 'marginTop': '5px'}
            )
        ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center'})
    ]
    
    # ========== CURRENT STATUS CARD ==========
    days_since = (pd.Timestamp.now() - latest_date).days
    current_status = [
        html.Div([
            html.Span("Last Scan: ", style={'fontWeight': 'bold', 'color': '#2c3e50'}),
            html.Span(f"{latest_date.strftime('%b %d, %Y')}", style={'color': '#7f8c8d'}),
            html.Span(f" ({days_since} days ago)", style={'color': '#95a5a6', 'fontSize': '13px'})
        ], style={'marginBottom': '15px', 'paddingBottom': '15px', 'borderBottom': '1px solid #ecf0f1'}),
        
        html.Div([
            html.Div("Fat Mass", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_row['Fat (g)']/1000:.1f} kg", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '12px'}),
        
        html.Div([
            html.Div("Bone Mass", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_row['BMC (g)']/1000:.2f} kg ({latest_comp['Total Bone Mass (%)']:.1f}%)", 
                    style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '12px'}),
        
        html.Div([
            html.Div("Basal Metabolic Rate", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_comp['Basal Metabolic Rate (kcal/day)']:.0f} kcal/day", 
                    style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ])
    ]
    
    # ========== PROGRESS & RECORDS CARD ==========
    progress_records = [
        html.Div([
            html.Div("💪 Best Lean Mass", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '3px'}),
            html.Div(f"{total_df['Lean (g)'].max()/1000:.1f} kg", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#27ae60'}),
            html.Div(f"{total_df.loc[total_df['Lean (g)'].idxmax(), 'Scan Date'].strftime('%b %Y')}", 
                    style={'fontSize': '12px', 'color': '#95a5a6'})
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Div("🎯 Lowest Body Fat", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '3px'}),
            html.Div(f"{patient_composition_df['Total Body Fat (%)'].min():.1f}%", 
                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#27ae60'}),
            html.Div(f"{patient_composition_df.loc[patient_composition_df['Total Body Fat (%)'].idxmin(), 'Scan Date'].strftime('%b %Y')}", 
                    style={'fontSize': '12px', 'color': '#95a5a6'})
        ], style={'marginBottom': '15px'}),
        
        html.Div([
            html.Div("⚖️ Weight Range", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '3px'}),
            html.Div(f"{total_df['Total Mass (kg)'].min():.1f} - {total_df['Total Mass (kg)'].max():.1f} kg", 
                    style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'}),
            html.Div(f"Δ {total_df['Total Mass (kg)'].max() - total_df['Total Mass (kg)'].min():.1f} kg range", 
                    style={'fontSize': '12px', 'color': '#95a5a6'})
        ])
    ]
    
    # ========== RATIOS CARD ==========
    ratios = [
        html.Div([
            html.Div("Fat Mass Index", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_comp['Fat Mass Index (FMI)']:.1f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '12px'}),
        
        html.Div([
            html.Div("Lean Mass Index", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_comp['Lean Mass Index (kg/m²)']:.1f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '12px'}),
        
        html.Div([
            html.Div("Android/Gynoid Ratio", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_comp['Android/Gynoid Fat Ratio']:.2f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ], style={'marginBottom': '12px'}),
        
        html.Div([
            html.Div("Trunk/Leg Ratio", style={'color': '#7f8c8d', 'fontSize': '13px'}),
            html.Div(f"{latest_comp['Trunk/Legs Fat Ratio']:.2f}", style={'fontSize': '18px', 'fontWeight': 'bold', 'color': '#2c3e50'})
        ])
    ]
    
    # ========== BODY COMPOSITION TIMELINE (Main Story Graph) ==========
    comp_fig = go.Figure()
    
    # Calculate dynamic y-axis range based on data
    bf_min = patient_composition_df['Total Body Fat (%)'].min()
    bf_max = patient_composition_df['Total Body Fat (%)'].max()
    
    # Add 5% padding to the range for visual comfort
    y_range_min = max(0, bf_min - 5)  # Don't go below 0
    y_range_max = min(100, bf_max + 5)  # Don't go above 100
    
    # Show only Body Fat % with proper dynamic scale
    comp_fig.add_trace(go.Scatter(
        x=patient_composition_df['Scan Date'], 
        y=patient_composition_df['Total Body Fat (%)'],
        name="Body Fat %",
        line=dict(color='#e74c3c', width=4),
        mode='lines+markers',
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.1)'
    ))
    
    comp_fig.update_layout(
        title={
            'text': "Body Fat Percentage Over Time",
            'font': {'size': 20, 'color': '#2c3e50', 'family': 'Arial, sans-serif'}
        },
        yaxis=dict(
            range=[y_range_min, y_range_max],  # Dynamic range based on data
            title="Body Fat (%)",
            gridcolor='#ecf0f1',
            showgrid=True
        ),
        xaxis=dict(
            title="",
            gridcolor='#ecf0f1'
        ),
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified'
    )
    
    # ========== WEIGHT & LEAN MASS TRENDS ==========
    weight_lean_fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    weight_lean_fig.add_trace(
        go.Scatter(
            x=total_df['Scan Date'], 
            y=total_df['Total Mass (kg)'],
            name="Weight",
            line=dict(color='#2c3e50', width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=False
    )
    
    weight_lean_fig.add_trace(
        go.Scatter(
            x=total_df['Scan Date'], 
            y=total_df['Lean (g)']/1000,
            name="Lean Mass",
            line=dict(color='#3498db', width=3),
            mode='lines+markers',
            marker=dict(size=6)
        ),
        secondary_y=True
    )
    
    weight_lean_fig.update_layout(
        title={
            'text': "Weight & Lean Mass Progression",
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    weight_lean_fig.update_yaxes(title_text="Weight (kg)", secondary_y=False, gridcolor='#ecf0f1')
    weight_lean_fig.update_yaxes(title_text="Lean Mass (kg)", secondary_y=True, gridcolor='#ecf0f1')
    
    # ========== VISCERAL FAT GRAPH ==========
    visceral_fig = go.Figure()
    
    visceral_fig.add_trace(go.Scatter(
        x=patient_composition_df['Scan Date'],
        y=patient_composition_df['Visceral Fat Area (cm²)'],
        name="Visceral Fat",
        line=dict(color='#c0392b', width=3),
        mode='lines+markers',
        marker=dict(size=7),
        fill='tozeroy',
        fillcolor='rgba(192, 57, 43, 0.1)'
    ))
    
    visceral_fig.update_layout(
        title={
            'text': "⚠️ Visceral Fat Area Trend (Health Risk Indicator)",
            'font': {'size': 18, 'color': '#2c3e50'}
        },
        yaxis=dict(title="Visceral Fat (cm²)", gridcolor='#ecf0f1'),
        xaxis=dict(title="", gridcolor='#ecf0f1'),
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified'
    )
    
    return key_metrics, current_status, progress_records, ratios, comp_fig, weight_lean_fig, visceral_fig