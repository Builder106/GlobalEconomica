from dash import Dash, dcc, html, Input, Output, State
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

gdp_data = fetch_data('NY.GDP.MKTP.CD')
unemployment_data = fetch_data('SL.UEM.TOTL.ZS')
inflation_data = fetch_data('FP.CPI.TOTL')

app = Dash(__name__)

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
])

def get_data_by_type(data_type):
    """Return the appropriate dataset and label based on the selected data type."""
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
    
    data, y_label = get_data_by_type(selected_data_type)
    if data is None:
        return px.line(title="Invalid data type selected")
    
    country_data = data[(data['Country'] == selected_country) & 
                        (data['Year'] >= selected_years[0]) & 
                        (data['Year'] <= selected_years[1])]
    
    if country_data.empty:
        return px.line(title=f"No data available for {selected_country}")
    
    fig = px.line(country_data, x='Year', y=y_label, title=f'{selected_data_type} Trends for {selected_country}')
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

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)