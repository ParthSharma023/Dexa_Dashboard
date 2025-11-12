from dash import dcc, html, Input, Output, callback, register_page, dash_table
import pandas as pd
import plotly.graph_objects as go
import os

register_page(__name__, path="/symmetry", order=4)

# GitHub raw URL for master CSV
MASTER_CSV_URL = "Data/master_dexa_data.csv"     

# Load data
try:
    df = pd.read_csv(MASTER_CSV_URL)
    df["Scan Date"] = pd.to_datetime(df["Scan Date"], format="%d-%m-%Y", errors="coerce")
    df.dropna(subset=["Scan Date"], inplace=True)
except Exception as e:
    raise Exception(f"Error loading data from GitHub: {e}")

def calculate_symmetry_score(left, right):
    """
    Calculate symmetry score between -1 and 1
    -1: left side much bigger
    0: perfect symmetry
    1: right side much bigger
    """
    avg = (left + right) / 2
    diff = (right - left) / avg
    return diff

def calculate_symmetry(df):
    symmetry_data = []
    for unique_id, group in df.groupby("Unique ID"):
        row = {"Unique ID": unique_id, 
               "Scan Date": group["Scan Date"].iloc[0], 
               "Patient Name": group["Patient Name"].iloc[0]}
        body_parts = group.set_index("Body Part")

        if "Left Arm" in body_parts.index and "Right Arm" in body_parts.index:
            row["Arm Symmetry"] = calculate_symmetry_score(
                body_parts.loc["Left Arm", "Lean (g)"],
                body_parts.loc["Right Arm", "Lean (g)"]
            )

        if "Left Ribs" in body_parts.index and "Right Ribs" in body_parts.index:
            row["Ribs Symmetry"] = calculate_symmetry_score(
                body_parts.loc["Left Ribs", "Lean (g)"],
                body_parts.loc["Right Ribs", "Lean (g)"]
            )

        if "Left Leg" in body_parts.index and "Right Leg" in body_parts.index:
            row["Leg Symmetry"] = calculate_symmetry_score(
                body_parts.loc["Left Leg", "Lean (g)"],
                body_parts.loc["Right Leg", "Lean (g)"]
            )

        symmetry_data.append(row)

    symmetry_df = pd.DataFrame(symmetry_data)
    return symmetry_df

def create_symmetry_plot(df, symmetry_type):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["Scan Date"],
        y=df[symmetry_type],
        mode='lines+markers',
        name=symmetry_type,
        line=dict(width=2),
        marker=dict(size=8)
    ))

    fig.update_layout(
        title={
            'text': f"{symmetry_type}",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Date",
        yaxis_title="Symmetry Score",
        yaxis_range=[-0.5, 0.5],
        plot_bgcolor='white',
        paper_bgcolor='white',
        showlegend=False,
        xaxis=dict(
            showline=True,
            showgrid=False,
            linecolor='black',
            linewidth=1,
            mirror=True
        ),
        yaxis=dict(
            showgrid=False,
            linecolor='black',
            linewidth=1,
            mirror=True
        ),
        height=300,
        margin=dict(l=50, r=50, t=50, b=50),
        annotations=[
            dict(x=0.02, y=0.98, xref="paper", yref="paper",
                 text="Right side dominant →", showarrow=False),
            dict(x=0.02, y=0.02, xref="paper", yref="paper",
                 text="← Left side dominant", showarrow=False)
        ],
        shapes=[
            # Border rectangle
            dict(
                type='rect',
                xref='paper',
                yref='paper',
                x0=0,
                y0=0,
                x1=1,
                y1=1,
                line=dict(
                    color='black',
                    width=1,
                ),
                layer='below'
            ),
            # Red shading for left dominance (negative values)
            dict(
                type='rect',
                xref='paper',
                yref='y',
                x0=0,
                y0=-0.5,
                x1=1,
                y1=0,
                fillcolor='rgba(255,0,0,0.05)',
                line=dict(width=0),
                layer='below'
            ),
            # Green shading for right dominance (positive values)
            dict(
                type='rect',
                xref='paper',
                yref='y',
                x0=0,
                y0=0,
                x1=1,
                y1=0.5,
                fillcolor='rgba(0,255,0,0.05)',
                line=dict(width=0),
                layer='below'
            ),
            # Zero line
            dict(
                type='line',
                xref='paper',
                yref='y',
                x0=0,
                y0=0,
                x1=1,
                y1=0,
                line=dict(
                    color='black',
                    width=1,
                    dash='dash'
                ),
                layer='below'
            )
        ]
    )
    
    return fig

# Create the symmetry dataframe
symmetry_df = calculate_symmetry(df)

print("Symmetry DF columns:", symmetry_df.columns.tolist())

# Page layout
layout = html.Div([
    html.H2("Symmetry Analysis", style={'textAlign': 'center'}),

    # Patient selection dropdown
    html.Div([
        html.Label("Select Patient:"),
        dcc.Dropdown(
            id='symmetry-patient-dropdown',
            options=[{'label': name, 'value': name} 
                    for name in sorted(symmetry_df["Patient Name"].unique())],
            value=symmetry_df["Patient Name"].unique()[0],
            clearable=False
        )
    ], style={'width': '30%', 'margin': '20px auto'}),

    # Graphs container
    html.Div([
        dcc.Graph(id='arm-symmetry-graph', style={'marginBottom': '20px'}),
        dcc.Graph(id='ribs-symmetry-graph', style={'marginBottom': '20px'}),
        dcc.Graph(id='leg-symmetry-graph', style={'marginBottom': '20px'})
    ], style={'padding': '20px'}),

    # Data table
    html.Div([
        html.H3("Symmetry Data", style={'textAlign': 'center'}),
        dash_table.DataTable(
            id='symmetry-table',
            columns=[
                {"name": "Scan Date", "id": "Scan Date"},
                {"name": "Arm Symmetry", "id": "Arm Symmetry"},
                {"name": "Ribs Symmetry", "id": "Ribs Symmetry"},
                {"name": "Leg Symmetry", "id": "Leg Symmetry"}
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], style={'margin': '20px'})
])

@callback(
    [Output('arm-symmetry-graph', 'figure'),
     Output('ribs-symmetry-graph', 'figure'),
     Output('leg-symmetry-graph', 'figure'),
     Output('symmetry-table', 'data')],
    Input('symmetry-patient-dropdown', 'value')
)
def update_symmetry_graphs(selected_patient):
    filtered_df = symmetry_df[symmetry_df["Patient Name"] == selected_patient].sort_values("Scan Date")
    
    # Create figures for each symmetry type
    arm_fig = create_symmetry_plot(filtered_df, "Arm Symmetry")
    ribs_fig = create_symmetry_plot(filtered_df, "Ribs Symmetry")
    leg_fig = create_symmetry_plot(filtered_df, "Leg Symmetry")
    
    # Prepare table data
    table_data = filtered_df.copy()
    table_data["Scan Date"] = table_data["Scan Date"].dt.strftime('%Y-%m-%d')
    table_data = table_data[["Scan Date", "Arm Symmetry", "Ribs Symmetry", "Leg Symmetry"]].round(3)
    table_data = table_data.to_dict('records')
    
    return arm_fig, ribs_fig, leg_fig, table_data
