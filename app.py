from dash import Dash, dcc, html, Input, Output
import requests
import wbgapi as wb
import pandas as pd
import plotly.express as px  # for interactive visualizations

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
    html.H1("Economic Trend Analysis Dashboard"),
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
    dcc.Graph(id='data-plot')
])

# Define the callback to update the graph
@app.callback(
    Output('data-plot', 'figure'),
    [Input('country-selector', 'value'),
     Input('data-type-selector', 'value')]
)
def update_graph(selected_country, selected_data_type):
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
    
    country_data = data[data['Country'] == selected_country]
    
    if country_data.empty:
        return px.line(title=f"No data available for {selected_country}")
    
    fig = px.line(country_data, x='Year', y=y_label, title=f'{selected_data_type} Trends for {selected_country}')
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)