import os
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import streamlit as st
from streamlit_folium import st_folium
from pathlib import Path
from shapely.geometry import Polygon
from folium.plugins import BeautifyIcon
from branca.element import Template, MacroElement
import streamlit.components.v1 as components

# st.set_page_config(layout="centered")
st.set_page_config(layout="wide")

# Origin station and ticket selection
#chosen_station = "Greystones"
#chosen_ticket_type = "Child Single"
#chosen_payment_type = "Leap Fares"

# Map settings
map_centre = (53.33985783249015, -6.273211120984975)
zoom = 9

#main_path = r"C:\Users\ykhan1\DevOps\DataScienceTeam\Projects\NTA Fare Calculations"
main_path = os.path.dirname(__file__)
data_path = os.path.join(main_path, "data")
gis_path = os.path.join(main_path, "GIS") 

# Read in data for OD pairs and fares, filter for the ticket selection
fare_zone_data = pd.read_csv(os.path.join(main_path, '..', 'data', "OD_Pairs.csv"), encoding='unicode_escape')
fares_df = pd.read_csv(os.path.join(main_path,'..', 'data',  "Fares.csv"), encoding='unicode_escape')

payment_list = list(fares_df["PaymentMeans"].unique())
chosen_payment_type = st.sidebar.selectbox("Select a Payment Type:", payment_list, index=1)
fares_df = fares_df[(fares_df['PaymentMeans']==chosen_payment_type)].reset_index(drop=True)
                    
ticket_list = list(fares_df["TicketType"].unique())
chosen_ticket_type = st.sidebar.selectbox("Select a Ticket Type:", ticket_list, index=0)
fares_df = fares_df[(fares_df['TicketType']==chosen_ticket_type)].reset_index(drop=True)
fares_df = fares_df.sort_values(["Fare", "FareZone"])

station_list = sorted(list(fare_zone_data["Origin"].unique()))
chosen_station = st.sidebar.selectbox("Select an Origin Station:", station_list, index=0)

# Read in shape files for stations, zones
rail_nodes = gpd.read_file(os.path.join(main_path, '..', 'GIS', "Irish_Rail_Stations.shp"), encoding='unicode_escape')
city_zone = gpd.read_file(os.path.join(main_path, '..', 'GIS', "City_Zone_Boundary.shp"), encoding='unicode_escape')
commuter_zone = gpd.read_file(os.path.join(main_path, '..', 'GIS', "Commuter_Zone_Boundary.shp"), encoding='unicode_escape')

# Join pair data with rail nodes shape data, fare data
fares_from_chosen_station = fare_zone_data.loc[fare_zone_data["Origin"]==chosen_station]
fares_from_chosen_station = fares_from_chosen_station.merge(rail_nodes, left_on="Destination", right_on="stop_name")
fares_from_chosen_station = fares_from_chosen_station.merge(fares_df, left_on="Value", right_on="FareZone")

fare_num = len(fares_df)
cm  = plt.get_cmap('Blues')
indices = np.linspace(0, 1, fare_num)

colour_dict = {}
for i, index in enumerate(indices):
    rgba = cm(index)
    rgb = rgba[:3]
    k = fares_df.iloc[i]['FareZone']
    colour_dict[f'{k}'] = rgb

# Create map
m = folium.Map(
    location=map_centre,
    zoom_start=zoom,
    control_scale=True,
    tiles="CartoDB positron",
)

#Polygon shapes for city and commuter zones.
folium.GeoJson(city_zone, style_function=lambda x:{
    'fillColor' : 'blue',
    'color' : '#db078d',
    'weight': 2,
    'fillOpacity': 0
}).add_to(m)

folium.GeoJson(commuter_zone, style_function=lambda x:{
    'fillColor' : 'red',
    'color' : '#5b0896',
    'weight': 2,
    'fillOpacity': 0
}).add_to(m)

destination_list = sorted(list(fare_zone_data["Destination"].unique()))
destination_list.insert(0, "Any")
destination_station = st.sidebar.selectbox("Select a Destination Station:", destination_list, index=0)

if destination_station == chosen_station:
    st.sidebar.write("The selected origin and destination stations are the same.")

if destination_station == "Any":
    #Loop through unique stations to add marker on map
    for i, row in fares_from_chosen_station.iterrows():
        coords = [row["geometry"].xy[1][0], row["geometry"].xy[0][0]]
        fare_zone = row['Value']
        origin = fares_from_chosen_station.iloc[i]['Origin']
        destination = fares_from_chosen_station.iloc[i]['Destination']
        fare = "€" +  f"{fares_from_chosen_station.iloc[i]['Fare']:.2f}"
        tool_tip = f"Origin: {origin}, Destination: {destination}, Fare: {fare}, Fare Zone:{fare_zone}"

        folium.CircleMarker(
                        location=coords,
                        radius=5,
                        color="#4e4e4e",
                        opacity=0.6,
                        weight=1,
                        fill_color=colors.rgb2hex(colour_dict[fare_zone], keep_alpha=True),
                        fill_opacity=1,
                        tooltip=tool_tip,
                    ).add_to(m)
elif destination_station != chosen_station:
    coords = [rail_nodes.loc[rail_nodes['stop_name'] == destination_station, 'stop_lat'].iloc[0], 
                rail_nodes.loc[rail_nodes['stop_name'] == destination_station, 'stop_lon'].iloc[0]]
    fare_zone = fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Value'].values[0]
    origin = chosen_station
    destination = destination_station
    fare = "€" +  f"{fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Fare'].values[0]:.2f}"
    tool_tip = f"Origin: {origin}, Destination: {destination}, Fare: {fare}, Fare Zone:{fare_zone}"

    folium.CircleMarker(
                    location=coords,
                    radius=5,
                    color="#4e4e4e",
                    opacity=0.6,
                    weight=1,
                    fill_color=colors.rgb2hex(colour_dict[fare_zone], keep_alpha=True),
                    fill_opacity=1,
                    tooltip=tool_tip,
                ).add_to(m)

    
# Star marker for origin station
icon_star = BeautifyIcon(
icon='diamond',
inner_icon_style='color:red;font-size:12px;',
background_color='transparent',
border_color='transparent',
)

origin_coords = [rail_nodes.loc[rail_nodes['stop_name'] == chosen_station, 'stop_lat'].iloc[0], 
                rail_nodes.loc[rail_nodes['stop_name'] == chosen_station, 'stop_lon'].iloc[0]]
folium.Marker(location=origin_coords, tooltip=f'Origin Station: {chosen_station}', icon=icon_star).add_to(m)

colour_map_dict = {key: tuple(int(255* value)for value in rgb) for key, rgb in colour_dict.items()}

# Horizontal Legend
fare_zone_html_string = ""
fare_price_html_string = ""
colour_html_string = ""
for fare_key, x in colour_map_dict.items():
    rgb_str = 'rgb' + str(x)
    formatted_price = f"{fares_df.loc[fares_df['FareZone'] == fare_key, 'Fare'].iloc[0]:.2f}"
    fare_zone_html_string += f"<td>{fare_key}</td>"
    fare_price_html_string += f"<td>€{formatted_price}</td>"
    colour_html_string += "<td style=" + f'"background-color: {rgb_str};"' + "></td>"   

legend_table_html = '''
<!doctype html>
<html lang="en">
<head><style>
table{
border: 1px solid black;
}
th, td {
padding:8px;windows move 
text-align: center;
}
</style></head>
<body>
    <table cellspacing="0">
        <tbody>
        <tr>   
'''+fare_zone_html_string

legend_html_end = "</tr><tr>" + fare_price_html_string + "</tr><tr>" + colour_html_string + "</tr></tbody></table></body></html>"
legend_table_html += legend_html_end

m.save(os.path.join(main_path, '..', "outputs\output.html"))


legend_vertical_html = '''
<!doctype html>
<html lang="en">
<head><style>
table{
border: 1px solid black;
}
th, td {
padding:8px;windows move 
text-align: center;
}
</style></head>
<body>
    <table cellspacing="0">
        <tbody>
        <tr>   
        <td style= "background-color: rgb(219, 7, 141);"</td><td> - City Zone Boundary</td>
        </tr>
        <tr> 
        <td style= "background-color: rgb(91, 8, 150);"></td><td> - Commuter Zone Boundary</td>  
        </tr>
        <tr>
        <td style="background-color: rgb(255, 0, 0);"></td><td> - Origin Station</td>
        </tr>
    </table>
<body>
</head>
</html>
'''

map_col, legend_col = st.columns([0.8,0.2])
with map_col:
    #st.header("NTA Fare Calculations Map")
    components.html(legend_table_html,
    height=100,
    )
    st_data = st_folium(m, width=1200, returned_objects=[])
with legend_col:
    st.header("")
    st.header("")
    components.html(legend_vertical_html, height=300)
