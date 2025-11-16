from dash import html, dcc, register_page, Input, Output, callback
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

register_page(__name__, path="/dexa-dashboard", name="Population Benchmarks", order=3)

# Load data
CSV_PATH = "Data/fat_mass_benchmark_results.csv"
df = pd.read_csv(CSV_PATH)

# Parse dates
df["Scan Date"] = pd.to_datetime(df["Scan Date"], format="%m-%d-%Y")

# Only keep Total body data
df = df[df["Body Part"].str.lower() == "total"].sort_values("Scan Date")

# Category color mapping
CATEGORY_COLORS = {
    '🔵 Well Below Expected': '#3498db',
    '🟦 Below Expected': '#5dade2',
    '🟢 Within Expected': '#27ae60',
    '🟧 Above Expected': '#e67e22',
    '🔴 Well Above Expected': '#e74c3c',
    '⚪ No Comparison': '#95a5a6'
}

# Layout
layout = html.Div([
    # Header
    html.Div([
        html.H1("Population Benchmarks", style={
            'textAlign': 'center',
            'marginBottom': '10px',
            'color': '#2c3e50',
            'fontWeight': '600'
        }),
        html.P("Compare patient body composition to national NHANES reference data", style={
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

    # Patient selector
    html.Div([
        html.Label("Select Patient", style={
            'fontWeight': '600',
            'color': '#2c3e50',
            'fontSize': '15px',
            'marginBottom': '10px',
            'display': 'block'
        }),
        dcc.Dropdown(
            id='patient-selector-benchmark',
            options=[{'label': p, 'value': p} for p in sorted(df["Patient Name"].unique())],
            value=sorted(df["Patient Name"].unique())[0] if not df.empty else None,
            clearable=False,
            style={'fontSize': '16px'}
        )
    ], style={
        'width': '400px',
        'margin': '0 auto 25px auto',
        'backgroundColor': 'white',
        'padding': '20px',
        'borderRadius': '8px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
    }),

    # Main content area
    html.Div([
        # Left side - Current status cards
        html.Div([
            # Current status card
            html.Div([
                html.H3("📊 Current Status", style={
                    'marginBottom': '20px',
                    'color': '#2c3e50',
                    'fontSize': '20px',
                    'borderBottom': '2px solid #ecf0f1',
                    'paddingBottom': '10px'
                }),
                html.Div(id='current-status-card-benchmark')
            ], style={
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),

            # Progress tracker
            html.Div([
                html.H3("📈 Progress Tracking", style={
                    'marginBottom': '20px',
                    'color': '#2c3e50',
                    'fontSize': '20px',
                    'borderBottom': '2px solid #ecf0f1',
                    'paddingBottom': '10px'
                }),
                html.Div(id='progress-card-benchmark')
            ], style={
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),

            # Reference info
            html.Div([
                html.H3("ℹ️ About NHANES", style={
                    'marginBottom': '15px',
                    'color': '#2c3e50',
                    'fontSize': '18px'
                }),
                html.P([
                    "Reference data from ",
                    html.Strong("NHANES 2003-2004"),
                    " study of U.S. population body composition."
                ], style={'fontSize': '13px', 'color': '#7f8c8d', 'marginBottom': '10px'}),
                html.P(
                    "Medians calculated by age group, sex, and ethnicity.",
                    style={'fontSize': '13px', 'color': '#7f8c8d', 'marginBottom': '0'}
                )
            ], style={
                'backgroundColor': '#ecf0f1',
                'padding': '15px',
                'borderRadius': '8px',
                'borderLeft': '4px solid #3498db'
            })
        ], style={
            'width': '30%',
            'float': 'left',
            'padding': '0 15px 0 0'
        }),

        # Right side - Main graph
        html.Div([
            html.Div([
                dcc.Graph(id='fat-mass-benchmark-graph', style={'height': '600px'})
            ], style={
                'backgroundColor': 'white',
                'padding': '20px',
                'borderRadius': '8px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                'marginBottom': '20px'
            }),

            # Interpretation banner
            html.Div(
                id='interpretation-banner-benchmark',
                style={
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '8px',
                    'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
                    'textAlign': 'center'
                }
            )
        ], style={
            'width': '68%',
            'float': 'right',
            'padding': '0'
        })
    ], style={'overflow': 'hidden'})
], style={
    'backgroundColor': '#f5f7fa',
    'padding': '20px',
    'minHeight': '100vh'
})

# Callback
@callback(
    [Output('current-status-card-benchmark', 'children'),
     Output('progress-card-benchmark', 'children'),
     Output('fat-mass-benchmark-graph', 'figure'),
     Output('interpretation-banner-benchmark', 'children')],
    Input('patient-selector-benchmark', 'value')
)
def update_benchmark_chart(patient_name):
    if not patient_name:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="Select a patient to view benchmark data",
            template="plotly_white"
        )
        return (
            [html.P("Select a patient", style={'color': '#7f8c8d'})],
            [html.P("Select a patient", style={'color': '#7f8c8d'})],
            empty_fig,
            html.P("Select a patient to begin", style={'color': '#7f8c8d'})
        )

    patient_df = df[df["Patient Name"] == patient_name].sort_values("Scan Date")

    if patient_df.empty:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title="No data available for this patient",
            template="plotly_white"
        )
        return (
            [html.P("No data available", style={'color': '#7f8c8d'})],
            [html.P("No data available", style={'color': '#7f8c8d'})],
            empty_fig,
            html.P("No data available", style={'color': '#7f8c8d'})
        )

    # Get latest and first records
    latest = patient_df.iloc[-1]
    first = patient_df.iloc[0]

    # ========== CURRENT STATUS CARD ==========
    category = latest.get("Category", "")
    category_color = CATEGORY_COLORS.get(category, '#95a5a6')
    
    current_status = [
        # Category badge
        html.Div(
            category,
            style={
                'backgroundColor': category_color,
                'color': 'white',
                'padding': '10px 20px',
                'borderRadius': '20px',
                'display': 'inline-block',
                'fontSize': '14px',
                'fontWeight': '600',
                'marginBottom': '20px'
            }
        ),
        
        # Current fat mass
        html.Div([
            html.Div("Current Fat Mass", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest['TotalBodyFat_g']/1000:.1f}", style={
                    'fontSize': '32px',
                    'fontWeight': 'bold',
                    'color': '#2c3e50'
                }),
                html.Span(" kg", style={'fontSize': '18px', 'color': '#7f8c8d'})
            ])
        ], style={'marginBottom': '20px'}),
        
        # NHANES median
        html.Div([
            html.Div("Population Median", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
            html.Div([
                html.Span(f"{latest['NHANES_Median_FatMass_g']/1000:.1f}", style={
                    'fontSize': '28px',
                    'fontWeight': 'bold',
                    'color': '#3498db'
                }),
                html.Span(" kg", style={'fontSize': '16px', 'color': '#7f8c8d'})
            ])
        ], style={'marginBottom': '20px'}),
        
        # Difference
        html.Div([
            html.Div("Difference from Median", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
            html.Div(
                f"{latest['FatMass_vs_Median_percent']:+.1f}%",
                style={
                    'fontSize': '24px',
                    'fontWeight': 'bold',
                    'color': category_color
                }
            )
        ], style={'marginBottom': '20px'}),
        
        # Demographics
        html.Div([
            html.Div("Demographics", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '8px'}),
            html.Div(f"{latest['Sex']}, {latest['Age Group']}, {latest['Ethnicity']}", 
                    style={'fontSize': '14px', 'color': '#2c3e50'})
        ])
    ]

    # ========== PROGRESS CARD ==========
    if len(patient_df) > 1:
        # Calculate changes
        fat_change_g = latest['TotalBodyFat_g'] - first['TotalBodyFat_g']
        fat_change_pct = (fat_change_g / first['TotalBodyFat_g']) * 100
        
        # Determine trend
        if abs(fat_change_pct) < 2:
            trend_icon = "➡️"
            trend_text = "Stable"
            trend_color = "#95a5a6"
        elif fat_change_g < 0:
            trend_icon = "📉"
            trend_text = "Decreasing"
            trend_color = "#27ae60"
        else:
            trend_icon = "📈"
            trend_text = "Increasing"
            trend_color = "#e74c3c"
        
        progress_card = [
            html.Div([
                html.Span(trend_icon, style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Span(trend_text, style={'fontSize': '18px', 'fontWeight': '600', 'color': trend_color})
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Div("Total Change", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
                html.Div(
                    f"{fat_change_g/1000:+.1f} kg ({fat_change_pct:+.1f}%)",
                    style={'fontSize': '20px', 'fontWeight': 'bold', 'color': trend_color}
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Div("Tracking Period", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
                html.Div(
                    f"{first['Scan Date'].strftime('%b %Y')} → {latest['Scan Date'].strftime('%b %Y')}",
                    style={'fontSize': '14px', 'color': '#2c3e50'}
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Div("Total Scans", style={'color': '#7f8c8d', 'fontSize': '13px', 'marginBottom': '5px'}),
                html.Div(f"{len(patient_df)} scans", style={'fontSize': '16px', 'fontWeight': '600', 'color': '#2c3e50'})
            ])
        ]
    else:
        progress_card = [
            html.Div([
                html.Span("📍", style={'fontSize': '24px', 'marginRight': '10px'}),
                html.Span("Baseline Scan", style={'fontSize': '18px', 'fontWeight': '600', 'color': '#7f8c8d'})
            ], style={'marginBottom': '15px'}),
            html.P(
                "Only one scan available. Future scans will enable progress tracking.",
                style={'fontSize': '14px', 'color': '#7f8c8d', 'lineHeight': '1.6'}
            )
        ]

    # ========== MAIN GRAPH ==========
    fig = go.Figure()

    # Patient's actual fat mass
    fig.add_trace(go.Scatter(
        x=patient_df["Scan Date"],
        y=patient_df["TotalBodyFat_g"]/1000,  # Convert to kg
        mode='lines+markers',
        name='Actual Fat Mass',
        line=dict(color='#e74c3c', width=4),
        marker=dict(size=10, line=dict(width=2, color='white')),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Fat Mass: %{y:.1f} kg<extra></extra>'
    ))

    # NHANES median reference
    fig.add_trace(go.Scatter(
        x=patient_df["Scan Date"],
        y=patient_df["NHANES_Median_FatMass_g"]/1000,  # Convert to kg
        mode='lines+markers',
        name='Population Median',
        line=dict(color='#3498db', width=3, dash='dash'),
        marker=dict(size=8),
        hovertemplate='<b>%{x|%b %d, %Y}</b><br>Median: %{y:.1f} kg<extra></extra>'
    ))

    # Add shaded region for "within expected" range (±15%)
    median_values = patient_df["NHANES_Median_FatMass_g"]/1000
    upper_bound = median_values * 1.15
    lower_bound = median_values * 0.85

    fig.add_trace(go.Scatter(
        x=patient_df["Scan Date"].tolist() + patient_df["Scan Date"].tolist()[::-1],
        y=upper_bound.tolist() + lower_bound.tolist()[::-1],
        fill='toself',
        fillcolor='rgba(39, 174, 96, 0.1)',
        line=dict(width=0),
        showlegend=True,
        name='Expected Range (±15%)',
        hoverinfo='skip'
    ))

    fig.update_layout(
        title={
            'text': f"Fat Mass Trajectory vs Population Benchmark",
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title="Scan Date",
        yaxis_title="Fat Mass (kg)",
        template="plotly_white",
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        yaxis=dict(gridcolor='#ecf0f1')
    )

    # ========== INTERPRETATION BANNER ==========
    interpretation = latest.get("Interpretation", "No interpretation available")
    
    interpretation_banner = html.Div([
        html.Div(
            category,
            style={
                'fontSize': '20px',
                'fontWeight': '600',
                'color': category_color,
                'marginBottom': '10px'
            }
        ),
        html.Div(
            interpretation,
            style={
                'fontSize': '16px',
                'color': '#2c3e50',
                'lineHeight': '1.6'
            }
        )
    ])

    return current_status, progress_card, fig, interpretation_banner