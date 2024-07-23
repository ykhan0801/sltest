import os
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from streamlit_folium import st_folium
from shapely.geometry import Polygon
from shapely.geometry import mapping
from folium.plugins import BeautifyIcon
from branca.element import Template, MacroElement

# st.set_page_config(layout="centered")
st.set_page_config(layout="wide")

# Map settings
map_centre = (53.33985783249015, -6.273211120984975)
zoom = 9

main_path = os.path.dirname(__file__)
data_path = os.path.join(main_path, "..", "data")
gis_path = os.path.join(main_path, "..", "GIS")
image_path = os.path.join(main_path, "..", "pics")
ENCODING = "unicode_escape"

logo_image_path = os.path.join(image_path, "logo2.png")
st.sidebar.image(logo_image_path, width=300)

# Read in data for OD pairs and fares, filter for the ticket selection
fare_zone_data = pd.read_csv(
    os.path.join(data_path, "OD_Pairs2.csv"), encoding=ENCODING
)
fares_df = pd.read_csv(os.path.join(data_path, "Fares.csv"), encoding=ENCODING)

payment_list = list(fares_df["PaymentMeans"].unique())
chosen_payment_type = st.sidebar.selectbox(
    "Select a Payment Type:", payment_list, index=1
)
fares_df = fares_df[(fares_df["PaymentMeans"] == chosen_payment_type)].reset_index(
    drop=True
)

ticket_list = list(fares_df["TicketType"].unique())
chosen_ticket_type = st.sidebar.selectbox("Select a Ticket Type:", ticket_list, index=0)
fares_df = fares_df[(fares_df["TicketType"] == chosen_ticket_type)].reset_index(
    drop=True
)
fares_df = fares_df.sort_values(["Fare", "FareZone"])

station_list = sorted(list(fare_zone_data["Origin"].unique()))
chosen_station = st.sidebar.selectbox(
    "Select an Origin Station:", station_list, index=0
)

# Read in shape files for stations, zones
rail_nodes = gpd.read_file(
    os.path.join(gis_path, "Irish_Rail_Stations.shp"),
    encoding=ENCODING,
)
city_zone = gpd.read_file(
    os.path.join(gis_path, "City_Zone_Boundary.shp"),
    encoding=ENCODING,
)
commuter_zone = gpd.read_file(
    os.path.join(gis_path, "Commuter_Zone_Boundary.shp"),
    encoding=ENCODING,
)

# Join pair data with rail nodes shape data, fare data
fares_from_chosen_station = fare_zone_data.loc[
    fare_zone_data["Origin"] == chosen_station
]
fares_from_chosen_station = fares_from_chosen_station.merge(
    rail_nodes, left_on="Destination", right_on="stop_name"
)
fares_from_chosen_station = fares_from_chosen_station.merge(
    fares_df, left_on="Value", right_on="FareZone"
)

unique_fares = fares_df.drop_duplicates(subset=["Fare"])
fare_num = len(fares_df)
cm = plt.get_cmap("viridis_r")
indices = np.linspace(0, 1, fare_num)

# colour_dict = {}
# for i, index in enumerate(indices):
#    rgba = cm(index)
#    rgb = rgba[:3]
#    k = fares_df.iloc[i]['FareZone']
#    colour_dict[f'{k}'] = rgb

# keys = list(colour_dict.keys())
# for i in range(1, len(keys)):
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

colour_dict2 = {k: tuple(v / 255 for v in rgb) for k, rgb in colour_dict2.items()}

# Create map
m = folium.Map(
    location=map_centre,
    zoom_start=zoom,
    control_scale=True,
    tiles="CartoDB positron",
)

# @st.cache_data
# def load_rail(main_path):
#    rail_df = gpd.read_file(os.path.join(main_path, '..', 'GIS', "routesint.shp"))
#    return rail_df

# Rail Lines
# rail_df = load_rail(main_path)
# folium.GeoJson(rail_df, name='multi_line', style_function=lambda x:{
#    'color': '#9E9E9E',
#    'weight': 1}).add_to(m)

# Polygon shapes for city and commuter zones.
folium.GeoJson(
    city_zone,
    style_function=lambda x: {
        "fillColor": "#db078d",
        "color": "#db078d",
        "weight": 2,
        "fillOpacity": 0.05,
    },
).add_to(m)

folium.GeoJson(
    commuter_zone,
    style_function=lambda x: {
        "fillColor": "#5b0896",
        "color": "#5b0896",
        "weight": 2,
        "fillOpacity": 0.05,
    },
).add_to(m)

destination_list = sorted(list(fare_zone_data["Destination"].unique()))
destination_list.insert(0, "Any")
destination_station = st.sidebar.selectbox(
    "Select a Destination Station:", destination_list, index=0
)

if destination_station == chosen_station:
    st.sidebar.write(
        "WARNING! The selected origin and destination stations are the same."
    )

if destination_station != chosen_station and destination_station != "Any":
    st.sidebar.markdown("### You Have Selected:")
    st.sidebar.write(
        f" A {chosen_payment_type[:-1]} - {chosen_ticket_type} Ticket from {chosen_station} to {destination_station}."
    )
    for i, row in fares_from_chosen_station.iterrows():
        if (
            row["Origin"] == chosen_station
            and row["Destination"] == destination_station
        ):
            fare_type = fares_from_chosen_station.iloc[i]["Value"]
            fare_cost = fares_from_chosen_station.iloc[i]["Fare"]
            st.sidebar.write(
                f"This journey is in Zone {fare_type} and will cost €{fare_cost:.2f}."
            )

if destination_station == "Any":
    stations_to_display = fares_from_chosen_station
elif destination_station != chosen_station:
    stations_to_display = fares_from_chosen_station.loc[
        fares_from_chosen_station["Destination"] == destination_station
    ]

# Loop through unique stations to add marker on map
for i, row in stations_to_display.iterrows():
    coords = [row["geometry"].xy[1][0], row["geometry"].xy[0][0]]
    fare_zone = row["Value"]
    origin = fares_from_chosen_station.iloc[i]["Origin"]
    destination = fares_from_chosen_station.iloc[i]["Destination"]
    fare = "€" + f"{fares_from_chosen_station.iloc[i]['Fare']:.2f}"
    # tool_tip = f"Origin: {origin}, Destination: {destination}, Fare: {fare}, Fare Zone:{fare_zone}"
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

# Star marker for origin station
icon_star = BeautifyIcon(
    icon="diamond",
    inner_icon_style="color:red;font-size:12px;",
    background_color="transparent",
    border_color="transparent",
)

origin_coords = [
    rail_nodes.loc[rail_nodes["stop_name"] == chosen_station, "stop_lat"].iloc[0],
    rail_nodes.loc[rail_nodes["stop_name"] == chosen_station, "stop_lon"].iloc[0],
]
folium.Marker(
    location=origin_coords, tooltip=f"Origin Station: {chosen_station}", icon=icon_star
).add_to(m)

colour_map_dict = {
    key: tuple(int(255 * value) for value in rgb) for key, rgb in colour_dict2.items()
}

# Horizontal Legend
fare_zone_html_string = ""
fare_price_html_string = ""
colour_html_string = ""
for fare_key, x in colour_map_dict.items():
    rgb_str = "rgb" + str(x)
    formatted_price = (
        f"{fares_df.loc[fares_df['FareZone'] == fare_key, 'Fare'].iloc[0]:.2f}"
    )
    fare_zone_html_string += f"<td>{fare_key}</td>"
    fare_price_html_string += f"<td>€{formatted_price}</td>"
    colour_html_string += "<td style=" + f'"background-color: {rgb_str};"' + "></td>"

legend_table_html = (
    """
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
"""
    + fare_zone_html_string
)

legend_html_end = (
    "</tr><tr>"
    + fare_price_html_string
    + "</tr><tr>"
    + colour_html_string
    + "</tr></tbody></table></body></html>"
)
legend_table_html += legend_html_end

# m.save(os.path.join(main_path, '..', "outputs\output.html"))

legend_vertical_html = """
<!doctype html>
<html lang="en">
<head><style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap');
table{
border: 1px solid black;
width: 100%;
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
        <td style= "background-color: rgb(219, 7, 141); "</td><td> - City Zone Boundary</td>
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
"""

map_col, legend_col = st.columns([0.85, 0.15])
with map_col:
    # st.header("NTA Fare Calculations Map")
    components.html(
        legend_table_html,
        height=100,
    )
    st_data = st_folium(m, width=1200, returned_objects=[])
with legend_col:
    st.header("")
    st.header("")
    legend_image_path = os.path.join(image_path, "legend2.png")
    st.image(legend_image_path, width=250)
    # components.html(legend_vertical_html, height=300)
    for i in range(6):
        st.header("")
    st.text("")
    systra_image_path = os.path.join(image_path, "Systra.png")
    st.image(systra_image_path, width=120)

st.write("Map Data", st_data)
if st_data and st_data.get("last_object_clicked"):
    last_clicked = st_data["last_object_clicked"]
    st.write(f"Clicked Location: {last_clicked}")
