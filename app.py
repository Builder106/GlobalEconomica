from dash import Dash, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import requests
import wbgapi as wb
import pandas as pd
import plotly.express as px

def fetch_data(indicator):
    """Fetch data from World Bank API for a given indicator."""
    try:
        data = wb.data.DataFrame(indicator, 'all')
        data.reset_index(inplace=True)
        data.rename(columns={'economy': 'Country'}, inplace=True)
        data = data.melt(id_vars=['Country'], var_name='Year', value_name=indicator)
        data['Year'] = data['Year'].str.replace('YR', '').astype(int)
        return data
    except (wb.APIResponseError, requests.exceptions.RequestException) as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

def fetch_regions():
    """Fetch region data from World Bank API."""
    try:
        regions = wb.economy.DataFrame()
        regions.reset_index(inplace=True)
        regions = regions[['id', 'name', 'region']]
        regions.rename(columns={'id': 'Country', 'name': 'Country Name', 'region': 'Region'}, inplace=True)
        return regions
    except (wb.APIResponseError, requests.exceptions.RequestException) as e:
        print(f"Error fetching regions: {e}")
        return pd.DataFrame()

gdp_data = fetch_data('NY.GDP.MKTP.CD')
unemployment_data = fetch_data('SL.UEM.TOTL.ZS')
inflation_data = fetch_data('FP.CPI.TOTL')

regions = fetch_regions()

# Merge region data with country data
gdp_data = gdp_data.merge(regions, on='Country', how='left')
unemployment_data = unemployment_data.merge(regions, on='Country', how='left')
inflation_data = inflation_data.merge(regions, on='Country', how='left')

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
app.title = "GlobalEconomica"

def serve_layout():
    return html.Div([
        dcc.Store(id='theme-store', data=dbc.themes.BOOTSTRAP),
        dcc.Location(id='url', refresh=False),
        html.Div(id='theme-container', children=[
            html.Div(className="header", children=[
                html.H1("GlobalEconomica", style={'textAlign': 'center'}),
                dbc.Row(
                    dbc.Col(
                        html.Div([
                            html.I(className="fa fa-sun", style={'margin-right': '10px'}),
                            dbc.Switch(id='theme-switch', className='mt-2'),
                            html.I(className="fa fa-moon", style={'margin-left': '10px'})
                        ], style={'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),
                        width={"size": 2, "offset": 5}
                    )
                )
            ]),
            html.Div(className="container", children=[
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Select Country and Data Type", className="card-title"),
                        dcc.Dropdown(
                            id='country-selector',
                            options=[{'label': f"{row['Country Name']}", 'value': row['Country']} for _, row in regions.iterrows()],
                            placeholder="Select a country or region",
                            searchable=True
                        ),
                        dcc.Dropdown(
                            id='data-type-selector',
                            options=[
                                {'label': 'GDP', 'value': 'GDP'},
                                {'label': 'Unemployment Rate', 'value': 'Unemployment'},
                                {'label': 'Inflation Rate', 'value': 'Inflation'}
                            ],
                            placeholder="Select data type"
                        ),
                        dcc.RangeSlider(
                            id='year-range-slider',
                            min=gdp_data['Year'].min(),
                            max=gdp_data['Year'].max(),
                            value=[gdp_data['Year'].min(), gdp_data['Year'].max()],
                            marks={str(year): str(year) for year in range(gdp_data['Year'].min(), gdp_data['Year'].max() + 1, 5)},
                            step=1
                        ),
                        html.Button("Download Data", id="download-data-button", className="btn btn-primary mt-3"),
                        dcc.Download(id="download-data")
                    ])
                ]),
                dbc.Card([
                    dbc.CardBody([
                        dcc.Graph(id='data-plot')
                    ])
                ])
            ])
        ])
    ])

app.layout = serve_layout

def get_data_by_type(data_type):
    """Return the appropriate dataset and column name based on the selected data type."""
    if data_type == 'GDP':
        return gdp_data, 'NY.GDP.MKTP.CD'
    elif data_type == 'Unemployment':
        return unemployment_data, 'SL.UEM.TOTL.ZS'
    elif data_type == 'Inflation':
        return inflation_data, 'FP.CPI.TOTL'
    return None, None

@app.callback(
    Output('data-plot', 'figure'),
    [Input('country-selector', 'value'),
     Input('data-type-selector', 'value'),
     Input('year-range-slider', 'value')]
)
def update_graph(selected_country, selected_data_type, selected_years):
    if not selected_country or not selected_data_type:
        return px.line(title="Select a country and data type to view trends")
    
    data, column_name = get_data_by_type(selected_data_type)
    if data is None:
        return px.line(title="Invalid data type selected")
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    if country_data.empty:
        return px.line(title=f"No data available for {selected_country}")
    
    if selected_data_type in ['Unemployment', 'Inflation']:
        country_data[column_name] = country_data[column_name] / 100

    fig = px.line(country_data, x='Year', y=column_name, title=f'{selected_data_type} Trends for {selected_country}')
    
    if selected_data_type in ['Unemployment', 'Inflation']:
        fig.update_layout(yaxis_tickformat='.1%')

    return fig

@app.callback(
    Output("download-data", "data"),
    Input("download-data-button", "n_clicks"),
    State('country-selector', 'value'),
    State('data-type-selector', 'value'),
    State('year-range-slider', 'value'),
    prevent_initial_call=True
)
def download_data(n_clicks, selected_country, selected_data_type, selected_years):
    if not selected_country or not selected_data_type:
        return None
    
    data, y_label = get_data_by_type(selected_data_type)
    if data is None:
        return None
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    if country_data.empty:
        return None
    
    return dcc.send_data_frame(country_data.to_csv, f"{selected_country}_{selected_data_type}_data.csv")

@app.callback(
    Output('theme-store', 'data'),
    Input('theme-switch', 'value')
)
def toggle_theme(dark_mode):
    return dbc.themes.DARKLY if dark_mode else dbc.themes.BOOTSTRAP

@app.callback(
    Output('theme-container', 'children'),
    Input('theme-store', 'data')
)
def update_theme(theme):
    app.external_stylesheets = [theme, dbc.icons.FONT_AWESOME]
    return serve_layout().children

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)