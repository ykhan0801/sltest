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
from shapely.geometry import mapping
from folium.plugins import BeautifyIcon
from branca.element import Template, MacroElement
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

margins_css = """
    <style>
        .main > div {
            padding-left: 1rem;
            padding-right: 4rem;
            padding-top: 3rem;
            padding-bottom: 0rem;
        }
    </style>
"""

st.markdown(margins_css, unsafe_allow_html=True)

# Map settings
map_centre = (53.33985783249015, -6.273211120984975)
zoom = 9

main_path = os.path.dirname(__file__)
data_path = os.path.join(main_path, "data")
gis_path = os.path.join(main_path, "GIS") 

logo_image_path = os.path.join(main_path,'..', 'pics', "logo2.png")
st.sidebar.image(logo_image_path, width = 300)

# Read in data for OD pairs and fares, filter for the ticket selection
fare_zone_data = pd.read_csv(os.path.join(main_path, '..', 'data', "ODPairs(withZones).csv"), encoding='unicode_escape')
fares_df = pd.read_csv(os.path.join(main_path,'..', 'data',  "Fares.csv"), encoding='unicode_escape')
period_fares_df = pd.read_csv(os.path.join(main_path,'..', 'data',  "PeriodFares2.csv"), encoding='unicode_escape')

payment_list = list(fares_df["PaymentMeans"].unique())
payment_list.append('Period ')
chosen_payment_type = st.sidebar.selectbox("Select a Payment Type:", payment_list, index=1)

if chosen_payment_type == 'Period ':
    ticket_list = list(period_fares_df["TicketType"].unique())
    chosen_ticket_type = st.sidebar.selectbox("Select a Ticket Type:", ticket_list, index=0)
    period_fares_df = period_fares_df[(period_fares_df['TicketType']==chosen_ticket_type)].reset_index(drop=True)
else:
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
zone_2 = gpd.read_file(os.path.join(main_path, '..', 'GIS', "33km_Boundary.shp"), encoding='unicode_escape')
zone_3 = gpd.read_file(os.path.join(main_path, '..', 'GIS', "43km_Boundary.shp"), encoding='unicode_escape')

# Join pair data with rail nodes shape data, fare data
fares_from_chosen_station = fare_zone_data.loc[fare_zone_data["Origin"]==chosen_station]
fares_from_chosen_station = fares_from_chosen_station.merge(rail_nodes, left_on="Destination", right_on="stop_name")

if chosen_payment_type == 'Period ':
    fares_from_chosen_station = fares_from_chosen_station.merge(period_fares_df, left_on="Zone", right_on="FareZone")
else:
    fares_from_chosen_station = fares_from_chosen_station.merge(fares_df, left_on="Value", right_on="FareZone")

unique_fares = fares_df.drop_duplicates(subset=['Fare'])
fare_num = len(fares_df)
cm  = plt.get_cmap('viridis_r')
indices = np.linspace(0, 1, fare_num)

#colour_dict = {}
#for i, index in enumerate(indices):
#    rgba = cm(index)
#    rgb = rgba[:3]
#    k = fares_df.iloc[i]['FareZone']
#    colour_dict[f'{k}'] = rgb

#keys = list(colour_dict.keys())
#for i in range(1, len(keys)):
#    key = keys[i]
#    prev_key = keys[i-1]
#    if fares_df.iloc[i]['Fare'] == fares_df.iloc[i-1]['Fare']:
#        colour_dict[key] = colour_dict[prev_key]

colour_dict2 = {
    "D1": (252, 137, 5),
    "D2": (245, 225, 2),
    "D10": (136, 245, 2),
    "D14": (3, 166, 6),
    "D11": (2, 242, 238),
    "D90": (2, 242, 238),
    "D12": (2, 110, 242),
    "D91": (2, 110, 242),
    "D13": (1, 31, 138),
    "D92": (1, 31, 138),
    "D93": (112, 4, 201),
    "D94": (247, 2, 231),
    "D95": (184, 4, 79),
}

colour_dict2 = {k: tuple(v/255 for v in rgb) for k, rgb in colour_dict2.items()}

# Create map
m = folium.Map(
    location=map_centre,
    zoom_start=zoom,
    control_scale=True,
    tiles="CartoDB positron",
)

#Polygon shapes for city and commuter zones.
folium.GeoJson(city_zone, style_function=lambda x:{
    'fillColor' : '#db078d',
    'color' : '#db078d',
    'weight': 2,
    'fillOpacity': 0.05
}).add_to(m)

folium.GeoJson(commuter_zone, style_function=lambda x:{
    'fillColor' : '#5b0896',
    'color' : '#5b0896',
    'weight': 2,
    'fillOpacity': 0.05
}).add_to(m)

folium.GeoJson(zone_2, style_function=lambda x:{
    'color' : 'green',
    'weight': 2,
    'dashArray': '5, 5',
    'fillOpacity': 0
}).add_to(m)

folium.GeoJson(zone_3, style_function=lambda x:{
    'color' : 'green',
    'weight': 2,
    'dashArray': '5, 5',
    'fillOpacity': 0
}).add_to(m)

zones = [{'Name': 'Dublin City Zone', 'coords': [53.32247450706408, -6.107001714337153]},
         {'Name': 'Zone 2', 'coords': [53.3220643646633, -5.8913950198858664]},
         {'Name': 'Zone 3', 'coords': [53.3220643646633, -5.749946052328708]},
         {'Name': 'Zone 4', 'coords': [53.322884645929506, -5.593390884352822]}]

from folium.features import DivIcon

for zone in zones:
    folium.Marker(
        location=zone['coords'],
        icon=DivIcon(
            icon_size=(150,36),
            icon_anchor=(0,0),
            html= f'<div style="font-size: 6pt">{zone["Name"]}</div>'
        )
    ).add_to(m)

destination_list = sorted(list(fare_zone_data["Destination"].unique()))
destination_list.insert(0, "Any")
destination_station = st.sidebar.selectbox("Select a Destination Station:", destination_list, index=0)

if destination_station == chosen_station:
    st.sidebar.write("WARNING! The selected origin and destination stations are the same.")

if destination_station != chosen_station and destination_station !="Any":
    for i, row in fares_from_chosen_station.iterrows():
        if row['Origin'] == chosen_station and row['Destination'] == destination_station:
            fare_type = fares_from_chosen_station.iloc[i]['Value']
            fare_cost = fares_from_chosen_station.iloc[i]['Fare']
    st.sidebar.markdown('### You Have Selected:')
    st.sidebar.write(f" A {chosen_payment_type[:-1]} - {chosen_ticket_type} Ticket from {chosen_station} to {destination_station}, which costs €{fare_cost:.2f}.")

if destination_station == "Any" and chosen_payment_type != 'Period ':
    #Loop through unique stations to add marker on map
    for i, row in fares_from_chosen_station.iterrows():
        coords = [row["geometry"].xy[1][0], row["geometry"].xy[0][0]]
        fare_zone = row['Value']
        origin = fares_from_chosen_station.iloc[i]['Origin']
        destination = fares_from_chosen_station.iloc[i]['Destination']
        fare = "€" +  f"{fares_from_chosen_station.iloc[i]['Fare']:.2f}"
        tool_tip = f"<b>Origin:</b> {origin}<br> <b>Destination:</b> {destination}<br> <b>Fare:</b> {fare}<br> <b>Fare Zone:</b> {fare_zone}"

        folium.CircleMarker(
                        location=coords,
                        radius=6,
                        color="#4e4e4e",
                        opacity=0.6,
                        weight=1,
                        fill_color=colors.rgb2hex(colour_dict2[fare_zone], keep_alpha=True),
                        fill_opacity=1,
                        tooltip=tool_tip,
                    ).add_to(m)
elif destination_station != chosen_station  and destination_station != 'Any':
    coords = [rail_nodes.loc[rail_nodes['stop_name'] == destination_station, 'stop_lat'].iloc[0], 
                rail_nodes.loc[rail_nodes['stop_name'] == destination_station, 'stop_lon'].iloc[0]]
    if chosen_payment_type == 'Period ':
        fare_zone = fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Zone'].values[0]
        d_zone = fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Value'].values[0]
        colour = colors.rgb2hex(colour_dict2[d_zone], keep_alpha=True)
    else:
        fare_zone = fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Value'].values[0]
        colour = colors.rgb2hex(colour_dict2[fare_zone], keep_alpha=True)
    origin = chosen_station
    destination = destination_station
    fare = "€" +  f"{fares_from_chosen_station.loc[fares_from_chosen_station['Destination'] == destination_station, 'Fare'].values[0]:.2f}"
    tool_tip = f"<b>Origin:</b> {origin}<br> <b>Destination:</b> {destination}<br> <b>Fare:</b> {fare}<br> <b>Fare Zone:</b> {fare_zone}"

    folium.CircleMarker(
                    location=coords,
                    radius=6,
                    color="#4e4e4e",
                    opacity=0.6,
                    weight=1,
                    fill_color=colour,
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
colour_map_dict = {key: tuple(int(255* value)for value in rgb) for key, rgb in colour_dict2.items()}

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
@import url('https://fonts.googleapis.com/css2?family=Prompt:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
table{
border: 1px solid black;
font-family: "Prompt";
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

map_col, legend_col = st.columns([0.85,0.15])
with map_col:
    if chosen_payment_type != 'Period ':
        components.html(legend_table_html,height=100,)
    else:
        st.header("")
    st_data = st_folium(m, width=1200, returned_objects=[])
    
with legend_col:
    st.header("")
    if chosen_payment_type != 'Period ':
        st.header("")
    else:
        st.text("")
    legend_image_path = os.path.join(main_path,'..', 'pics', "legend2.png")
    st.image(legend_image_path, width = 250)

    buffer = 6
    for i in range(buffer):
        st.header("")
    st.text("")
    systra_image_path = os.path.join(main_path,'..', 'pics', "Systra.png")
    st.image(systra_image_path, width = 120)
