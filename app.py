from dash import Dash, dcc, html, Input, Output, State
import requests
import wbgapi as wb
import pandas as pd
import plotly.express as px  # for interactive visualizations
import os

# Fetch GDP, Unemployment, and Inflation data from World Bank API
def fetch_data(indicator):
    try:
        data = wb.data.DataFrame(indicator, 'all')
        data.reset_index(inplace=True)
        data.rename(columns={'economy': 'Country'}, inplace=True)
        data = data.melt(id_vars=['Country'], var_name='Year', value_name=indicator)
        data['Year'] = data['Year'].str.replace('YR', '').astype(int)
        return data
    except wb.APIResponseError as e:
        print(f"APIError: {e}")
    except requests.exceptions.RequestException as e:
        print(f"RequestException: {e}")
    return pd.DataFrame()

gdp_data = fetch_data('NY.GDP.MKTP.CD')
unemployment_data = fetch_data('SL.UEM.TOTL.ZS')
inflation_data = fetch_data('FP.CPI.TOTL')

# Initialize the Dash app
app = Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("GlobalEconomica"),
    dcc.Dropdown(
        id='country-selector',
        options=[{'label': country, 'value': country} for country in gdp_data['Country'].unique()],
        placeholder="Select a country"
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
    dcc.Graph(id='data-plot'),
    html.Button("Download Data", id="download-data-button"),
    dcc.Download(id="download-data"),
    html.Button("Download Plot", id="download-plot-button"),
    dcc.Download(id="download-plot"),
])

# Define the callback to update the graph
@app.callback(
    Output('data-plot', 'figure'),
    [Input('country-selector', 'value'),
     Input('data-type-selector', 'value'),
     Input('year-range-slider', 'value')]
)
def update_graph(selected_country, selected_data_type, selected_years):
    if selected_country is None or selected_data_type is None:
        return px.line(title="Select a country and data type to view trends")
    
    if selected_data_type == 'GDP':
        data = gdp_data
        y_label = 'NY.GDP.MKTP.CD'
    elif selected_data_type == 'Unemployment':
        data = unemployment_data
        y_label = 'SL.UEM.TOTL.ZS'
    elif selected_data_type == 'Inflation':
        data = inflation_data
        y_label = 'FP.CPI.TOTL'
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    if country_data.empty:
        return px.line(title=f"No data available for {selected_country}")
    
    fig = px.line(country_data, x='Year', y=y_label, title=f'{selected_data_type} Trends for {selected_country}')
    return fig

# Define the callback to download data
@app.callback(
    Output("download-data", "data"),
    Input("download-data-button", "n_clicks"),
    State('country-selector', 'value'),
    State('data-type-selector', 'value'),
    State('year-range-slider', 'value'),
    prevent_initial_call=True
)
def download_data(n_clicks, selected_country, selected_data_type, selected_years):
    if selected_country is None or selected_data_type is None:
        return None
    
    if selected_data_type == 'GDP':
        data = gdp_data
        y_label = 'NY.GDP.MKTP.CD'
    elif selected_data_type == 'Unemployment':
        data = unemployment_data
        y_label = 'SL.UEM.TOTL.ZS'
    elif selected_data_type == 'Inflation':
        data = inflation_data
        y_label = 'FP.CPI.TOTL'
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    csv_string = country_data.to_csv(index=False)
    return dict(content=csv_string, filename=f"{selected_country}_{selected_data_type}_data.csv")

import plotly.io as pio

# Set the Kaleido executable path
pio.kaleido.scope.default_format = "png"
pio.kaleido.scope.default_width = 800
pio.kaleido.scope.default_height = 600
pio.kaleido.scope.default_scale = 1

# Set the path to the Kaleido executable
pio.kaleido.scope.kaleido_path = os.path.expanduser("~/kaleido_files")

# Define the callback to download the plot
@app.callback(
    Output("download-plot", "data"),
    Input("download-plot-button", "n_clicks"),
    State('country-selector', 'value'),
    State('data-type-selector', 'value'),
    State('year-range-slider', 'value'),
    prevent_initial_call=True
)
def download_plot(n_clicks, selected_country, selected_data_type, selected_years):
    if selected_country is None or selected_data_type is None:
        return None
    
    if selected_data_type == 'GDP':
        data = gdp_data
        y_label = 'NY.GDP.MKTP.CD'
    elif selected_data_type == 'Unemployment':
        data = unemployment_data
        y_label = 'SL.UEM.TOTL.ZS'
    elif selected_data_type == 'Inflation':
        data = inflation_data
        y_label = 'FP.CPI.TOTL'
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    if country_data.empty:
        return None
    
    fig = px.line(country_data, x='Year', y=y_label, title=f'{selected_data_type} Trends for {selected_country}')
    
    try:
        img_bytes = fig.to_image(format="png", engine="kaleido")
        return dict(content=img_bytes, filename=f"{selected_country}_{selected_data_type}_plot.png")
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)