from dash import Dash, dcc, html, page_container
import dash
import warnings

# Initialize the app
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)
app.title = "DEXA Dashboard"

# Import pages here
from pages import overview, body_part_trend

# App Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("DEXA Dashboard", style={'textAlign': 'center', 'margin': '0', 'padding': '1rem'})
    ], style={
        'backgroundColor': 'white',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'marginBottom': '1rem'
    }),
    
    # Navigation
    html.Div([
        dcc.Link("Overview", href="/", className='nav-link'),
        dcc.Link("Body Part Trends", href="/body-part-trend", className='nav-link'),
        dcc.Link("Benchmarks", href="/dexa-dashboard", className='nav-link'),
        dcc.Link("Symmetry", href="/symmetry", className='nav-link')
    ], style={
        'textAlign': 'center',
        'padding': '1rem',
        'backgroundColor': 'white',
        'borderBottom': '1px solid #eee',
        'marginBottom': '2rem'
    }),
    
    # Main content (for page content)
    html.Div(page_container, style={
        'maxWidth': '1200px',
        'margin': '0 auto',
        'padding': '0 1rem',
        'marginBottom': '60px'
    }),
    
    # Footer
    # Footer
    html.Footer(
        html.P(
            "DEXA Analysis Dashboard",
            style={
                'textAlign': 'center',
                'padding': '1rem',
                'color': '#666',
                'backgroundColor': 'white',
                'borderTop': '1px solid #eee',
                'marginTop': '40px'
            }
        )
    )
])

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                background-color: #f5f6fa;
                color: #2c3e50;
            }
            
            .nav-link {
                color: #2c3e50;
                text-decoration: none;
                padding: 0.5rem 1rem;
                margin: 0 0.5rem;
                border-radius: 4px;
                transition: background-color 0.3s;
            }
            
            .nav-link:hover {
                background-color: #3498db;
                color: white;
            }
            
            .js-plotly-plot {
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                background: white;
                padding: 1rem;
            }

            button.selected {
                background-color: #3498db !important;
                color: white !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)  # Production configuration
