import geopandas as gpd  # Importing geopandas library for working with geospatial data
import hvplot.pandas  # Importing hvplot library for interactive plotting with pandas
import numpy as np  # Importing numpy library for numerical computations
import pandas as pd  # Importing pandas library for data manipulation and analysis
import panel as pn  # Importing panel library for creating interactive dashboards
import plotly.express as px  # Importing plotly express for creating interactive visualizations
from bokeh.resources import INLINE  # Importing INLINE resources for Bokeh plots
from IPython.display import HTML  # Importing HTML for displaying HTML content in the notebook
import folium  # Importing folium library for creating interactive leaflet maps
from folium import Choropleth, GeoJson, features  # Importing modules from folium for specific functionalities
from folium.plugins import MarkerCluster  # Importing MarkerCluster plugin for clustering markers on maps
import json  # Importing JSON library for working with JSON data

# Load CSV files
firearm_data = pd.read_csv("FM.CSV")  # Reading firearm mortality data from a CSV file into a pandas DataFrame
homicide_data = pd.read_csv("HM.CSV")  # Reading homicide mortality data from a CSV file into a pandas DataFrame
overdose_data = pd.read_csv("DOM.CSV")  # Reading drug overdose mortality data from a CSV file into a pandas DataFrame

# Rename columns to ensure consistency
firearm_data = firearm_data.rename(columns={'DEATHS COUNT': 'DEATHS'})  # Renaming column for consistency
homicide_data = homicide_data.rename(columns={'DEATHS COUNT': 'DEATHS'})  # Renaming column for consistency
overdose_data = overdose_data.rename(columns={'DEATHS COUNT': 'DEATHS'})  # Renaming column for consistency

# Load GeoJSON file
with open('us-states.json') as f:
    geojson_data = json.load(f)  # Loading US states boundaries from a GeoJSON file

# Function to create choropleth map with selected mortality data
def create_choropleth(year, mortality_type, data_type):
    # Selecting data based on the specified mortality type and year
    if mortality_type == 'Firearm Mortality':
        selected_data = firearm_data[(firearm_data['YEAR'] == year)]
    elif mortality_type == 'Homicide Mortality':
        selected_data = homicide_data[(homicide_data['YEAR'] == year)]
    elif mortality_type == 'Drug Overdose Mortality':
        selected_data = overdose_data[(overdose_data['YEAR'] == year)]
    
    # Dropping rows with NaN values in the selected column
    selected_data = selected_data.dropna(subset=['RATE', 'DEATHS'])
    
    # Choosing 'RATE' or 'DEATHS' based on data type
    if data_type == 'Mortality Rate':
        name = 'RATE'
    else:
        name = 'DEATHS'
    
    # Changing the data type of the column to float64
    selected_data[name] = selected_data[name].astype('float64')

    # Creating a map centered at USA
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=3)

    # Adding a base map layer showing regions
    folium.TileLayer(name="Regions Map", tiles='cartodbpositron', overlay=True).add_to(m)
    
    # Adding a base map layer showing satellite imagery
    folium.TileLayer(name="Satellite Map", tiles='https://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                     attr='Google', overlay=True, control=False, subdomains=['mt0', 'mt1', 'mt2', 'mt3']).add_to(m)
    
    # Adding a MarkerCluster layer for clustering markers
    marker_cluster = MarkerCluster().add_to(m)

    # Adding markers to the MarkerCluster layer
    for index, row in selected_data.iterrows():
        popup_text = f"State Name: {row['STATE']}\n{data_type}: {row[name]}"
        folium.Marker(location=[row['LAT'], row['LON']], popup=popup_text).add_to(marker_cluster)

    # Adding a choropleth layer to represent the selected data
    Choropleth(
        geo_data=geojson_data,
        name='choropleth',
        data=selected_data,
        columns=['STATE', name],
        key_on='feature.properties.NAME',
        fill_color='YlOrRd',
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name='{} ({})'.format(mortality_type, data_type)
    ).add_to(m)

    # Adding GeoJSON boundaries to the map
    GeoJson(geojson_data, style_function=lambda x: {'fillColor': 'transparent', 'color': 'black'}).add_to(m)

    # Adding layer control to the map
    folium.LayerControl().add_to(m)

    return m

# Function to calculate state rankings
def calculate_rankings(year, mortality_type, data_type, sort_order):
    # Selecting data based on the specified mortality type and year
    if mortality_type == 'Firearm Mortality':
        selected_data = firearm_data[(firearm_data['YEAR'] == year)]
    elif mortality_type == 'Homicide Mortality':
        selected_data = homicide_data[(homicide_data['YEAR'] == year)]
    elif mortality_type == 'Drug Overdose Mortality':
        selected_data = overdose_data[(overdose_data['YEAR'] == year)]
    
    # Dropping rows with NaN values in the selected column
    selected_data = selected_data.dropna(subset=['RATE', 'DEATHS'])

    # Choosing 'RATE' or 'DEATHS' based on data type
    if data_type == 'Mortality Rate':
        name = 'RATE'
    else:
        name = 'DEATHS'
    
    # Calculating rankings
    selected_data['Rank'] = selected_data[name].rank(ascending=sort_order)
    
    # Sorting data by rank
    selected_data = selected_data.sort_values(by='Rank', ascending=(sort_order == 'Descending'))
    
    # Resetting index and dropping the original index column
    selected_data.reset_index(drop=True, inplace=True)
    
    # Creating a DataFrame with state, rank, and selected data
    rankings_data = selected_data[['STATE', name]].copy()
    rankings_data.columns = ['State', 'Value']
    rankings_data['Rank'] = rankings_data['Value'].rank(ascending=(sort_order == 'Ascending'), method='dense')
    
    return rankings_data[['Rank', 'State', 'Value']]

# Function to create bar chart
def create_bar_chart(year, mortality_type, data_type):
    # Selecting data based on the specified mortality type and year
    if mortality_type == 'Firearm Mortality':
        selected_data = firearm_data[(firearm_data['YEAR'] == year)]
    elif mortality_type == 'Homicide Mortality':
        selected_data = homicide_data[(homicide_data['YEAR'] == year)]
    elif mortality_type == 'Drug Overdose Mortality':
        selected_data = overdose_data[(overdose_data['YEAR'] == year)]
    
    # Dropping rows with NaN values in the selected column
    selected_data = selected_data.dropna(subset=['RATE', 'DEATHS'])

    # Choosing 'RATE' or 'DEATHS' based on data type
    if data_type == 'Mortality Rate':
        name = 'RATE'
    else:
        name = 'DEATHS'
    
    # Sorting data by state
    selected_data = selected_data.sort_values(by='STATE')
    
    # Calculating mean average
    mean_average = selected_data[name].mean()
    
    # Creating bar chart
    bar_chart = px.bar(selected_data, x='STATE', y=name, title=f'{mortality_type} {data_type} for {year}')
    
    # Adding mean average line
    bar_chart.add_hline(y=mean_average, line_dash="dot", line_color="red", annotation_text=f"Mean: {mean_average:.2f}")
    
    return bar_chart

# Define options for dropdowns
years = [2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021]
mortality_types = ['Firearm Mortality', 'Homicide Mortality', 'Drug Overdose Mortality']
data_types = ['Mortality Rate', 'Deaths Count']
sort_orders = ['Ascending', 'Descending']

# Creating widgets for selecting options
year_dropdown = pn.widgets.Select(options=years, value=2014, name='Year')
mortality_type_dropdown = pn.widgets.Select(options=mortality_types, value='Firearm Mortality', name='Mortality Type')
data_type_radio = pn.widgets.RadioBoxGroup(options=data_types, value='Mortality Rate', name='Data Type')
sort_order_radio = pn.widgets.RadioBoxGroup(options=sort_orders, value='Descending', name='Sort Order')

# Define the callback function to update dashboard elements
def update_map_and_rankings(event):
    year = year_dropdown.value
    mortality_type = mortality_type_dropdown.value
    data_type = data_type_radio.value
    sort_order = sort_order_radio.value
    map_pane.object = create_choropleth(year, mortality_type, data_type)
    rankings_pane.object = calculate_rankings(year, mortality_type, data_type, sort_order)
    bar_chart_pane.object = create_bar_chart(year, mortality_type, data_type)

# Attaching the callback function to widget events
year_dropdown.param.watch(update_map_and_rankings, 'value')
mortality_type_dropdown.param.watch(update_map_and_rankings, 'value')
data_type_radio.param.watch(update_map_and_rankings, 'value')
sort_order_radio.param.watch(update_map_and_rankings, 'value')

# Create initial map pane
map_pane = pn.pane.HTML(width=900, height=600)

# Create initial rankings panel
rankings_pane = pn.pane.DataFrame()

# Create initial bar chart panel
bar_chart_pane = pn.pane.Plotly(width=900, height=500)

# Create layout for the dashboard
dashboard = pn.Column(
    pn.Row(year_dropdown, mortality_type_dropdown, data_type_radio, sort_order_radio),
    pn.Row(
        pn.Column(map_pane, bar_chart_pane),
        rankings_pane,
    )
)

# Update the map, rankings, and bar chart initially
update_map_and_rankings(None)

# Save the dashboard to an HTML file
dashboard.save('dashboard.html', embed=True, max_opts=9999, width=1920, height=1080)

# Incorporate the dashboard as an HTML object
from IPython.display import HTML

# Read the HTML content from the saved file
with open('dashboard.html', 'r') as file:
    html_content = file.read()

# Display the HTML content in the notebook
HTML(html_content)
