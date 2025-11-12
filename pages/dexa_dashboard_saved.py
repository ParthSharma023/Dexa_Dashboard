from dash import html, dcc, register_page, Input, Output, callback
import pandas as pd
import plotly.graph_objects as go

register_page(__name__, path="/dexa-dashboard", order=3)

# --- Load and clean data ---
CSV_PATH = "Data/fat_mass_benchmark_results.csv"
df = pd.read_csv(CSV_PATH)

# Parse dates safely
df["Scan Date"] = pd.to_datetime(df["Scan Date"], errors="coerce", dayfirst=True)

# Only keep Total body data (ignore arm/leg etc. for simplicity)
df = df[df["Body Part"].str.lower() == "total"]

# --- Layout ---
layout = html.Div([
    html.H2("Fat Mass Benchmark Comparison", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Patient selector
    html.Div([
        html.Label("Select Patient:", style={'fontWeight': 'bold'}),
        dcc.Dropdown(
            id='patient-selector',
            options=[{'label': p, 'value': p} for p in sorted(df["Patient Name"].unique())],
            value=sorted(df["Patient Name"].unique())[0] if not df.empty else None,
            clearable=False,
            style={'width': '400px'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '30px'}),

    # Graph
    dcc.Graph(id='fat-mass-benchmark-graph', style={'height': '500px'}),

    # Summary
    html.Div(
        id='benchmark-summary',
        style={
            'textAlign': 'center',
            'marginTop': '35px',   # ⬅️ increased space
            'paddingBottom': '15px',  # ⬅️ adds breathing room above footer
            'fontSize': '16px',
            'fontWeight': 'bold',
            'maxWidth': '900px',
            'margin': '35px auto 0 auto'  # centers and adds vertical margin
        }
    )
])


# --- Callback ---
@callback(
    Output('fat-mass-benchmark-graph', 'figure'),
    Output('benchmark-summary', 'children'),
    Input('patient-selector', 'value')
)
def update_benchmark_chart(patient_name):
    if not patient_name:
        return go.Figure(), "Please select a patient."

    patient_df = df[df["Patient Name"] == patient_name].sort_values("Scan Date")

    if patient_df.empty:
        return go.Figure(), "No data available for this patient."

    # Create figure
    fig = go.Figure()

    # Patient’s actual fat mass
    fig.add_trace(go.Scatter(
        x=patient_df["Scan Date"],
        y=patient_df["TotalBodyFat_g"],
        mode='lines+markers',
        name='Actual Fat Mass (g)',
        line=dict(width=3),
        marker=dict(size=8)
    ))

    # NHANES median reference
    fig.add_trace(go.Scatter(
        x=patient_df["Scan Date"],
        y=patient_df["NHANES_Median_FatMass_g"],
        mode='lines+markers',
        name='NHANES Median (g)',
        line=dict(width=3, dash='dash'),
        marker=dict(size=6)
    ))

    # Layout cleanup
    fig.update_layout(
        title=f"Fat Mass vs NHANES Benchmark — {patient_name}",
        xaxis_title="Scan Date",
        yaxis_title="Fat Mass (grams)",
        legend_title="Legend",
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#eee'),
        yaxis=dict(showgrid=True, gridcolor='#eee')
    )

    # Use latest record’s interpretation for summary
    latest = patient_df.iloc[-1]
    interpretation = latest.get("Interpretation", "No interpretation available")
    category = latest.get("Category", "")
    message = latest.get("Patient_Message", "")

    summary_text = f"({category}) — {message}"

    return fig, summary_text