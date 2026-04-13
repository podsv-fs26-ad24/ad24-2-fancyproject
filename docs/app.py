import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ---------------------------------------------------
# DATA LOADING
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx", sheet_name="travel_data")
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()

# clear column names
df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("(", "").str.replace(")", "")

st.set_page_config(layout="wide")
st.title("Geschäftsreisen & CO₂-Emissionen – Dashboard")

# -----------------------------
# SIDEBAR FILTER
# -----------------------------
st.sidebar.header("Filter")

# Jahr
years = sorted(df["date"].dt.year.unique())
year = st.sidebar.selectbox("Jahr", years)

# Transportmodus
transport_modes = df["transport_mode"].unique()
transport = st.sidebar.multiselect("Transportmodus", transport_modes, default=transport_modes)

# Business Subunit
subunits = df["subunit"].unique()
subunit = st.sidebar.multiselect("Business Unit", subunits, default=subunits)

# Haul-Typ (short/medium/long)
haul_types = df["haul"].unique()
haul = st.sidebar.multiselect("Flugdistanz (Haul)", haul_types, default=haul_types)

# Bahn-Alternative
train_options = df["train_alternative_available"].unique()
train = st.sidebar.multiselect("Bahn-Alternative", train_options, default=train_options)

# -----------------------------
# FILTERED DATA
# -----------------------------
# unschöner barplot, 10 routen -> 5 bars
filtered = df[
    (df["date"].dt.year == year) &
    (df["transport_mode"].isin(transport)) &
    (df["subunit"].isin(subunit)) &
    (df["haul"].isin(haul)) &
    (df["train_alternative_available"].isin(train))
]

filtered["route"] = filtered.apply(
    lambda r: " - ".join(sorted([r["departure_city"], r["arrival_city"]])),
    axis=1
)

routes = (
    filtered
    .groupby("route")["CO2e_RFI2_t"]
    .sum()
    .reset_index()
)

top10_routes = routes.sort_values("CO2e_RFI2_t", ascending=False).head(10)



# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Flüge gesamt", f"{len(filtered)}")
kpi2.metric("CO₂ gesamt (t)", f"{filtered['CO2e_RFI2_t'].sum():.1f}")

if len(filtered) > 0:
    kpi3.metric("Top-Ziel", filtered.groupby("arrival_city")["CO2e_RFI2_t"].sum().idxmax())
else:
    kpi3.metric("Top-Ziel", "-")

kpi4.metric("Bahn-Alternative (%)", f"{(filtered['train_alternative_available'] == 'WAHR').mean() * 100:.0f}%")



# ---------------------------------------------------
# TOP 10 BAR CHART
# ---------------------------------------------------
# top10 = (
#     filtered
#     .sort_values("CO2e_RFI2_t", ascending=False)
#     .head(10)
# )

# fig_top10 = px.bar(
#     top10.sort_values("CO2e_RFI2_t"),
#     x="CO2e_RFI2_t",
#     y="arrival_city",
#     title="Top 10 CO₂-Emissionen nach Zielort",
#     text="CO2e_RFI2_t"
# )

# fig_top10.update_traces(
#     textposition="outside",
#     texttemplate="%{text:.1f} t"
# )

# fig_top10.update_layout(
#     height=800,
#     bargap=0.15
# )

fig_top10 = px.bar(
    top10_routes.sort_values("CO2e_RFI2_t"),
    x="CO2e_RFI2_t",
    y="route",
    title="Top 10 CO₂-intensivste Strecken",
    text="CO2e_RFI2_t"
)

fig_top10.update_traces(
    textposition="outside",
    texttemplate="%{text:.1f} t"
)

fig_top10.update_layout(
    height=800,
    bargap=0.15
)

# ---------------------------------------------------
# ROUTE DEFINIEREN (richtungslos)
# ---------------------------------------------------
filtered["route"] = filtered.apply(
    lambda r: " - ".join(sorted([r["departure_city"], r["arrival_city"]])),
    axis=1
)

# ---------------------------------------------------
# CO₂ PRO ROUTE
# ---------------------------------------------------
routes_co2 = (
    filtered
    .groupby("route")["CO2e_RFI2_t"]
    .sum()
    .reset_index()
)

top10_routes = routes_co2.sort_values("CO2e_RFI2_t", ascending=False).head(10)

fig_top10 = px.bar(
    top10_routes.sort_values("CO2e_RFI2_t"),
    x="CO2e_RFI2_t",
    y="route",
    title="Top 10 CO₂-intensivste Strecken",
    text="CO2e_RFI2_t"
)

fig_top10.update_traces(textposition="outside", texttemplate="%{text:.1f} t")
fig_top10.update_layout(height=800, bargap=0.15)

# ---------------------------------------------------
# ANZAHL FLÜGE FÜR DIESE TOP‑10 ROUTEN
# ---------------------------------------------------
route_counts = (
    filtered
    .groupby("route")
    .size()
    .reset_index(name="flights")
)

top10_flights = route_counts[route_counts["route"].isin(top10_routes["route"])]

# Reihenfolge der CO₂-Top10 übernehmen
order = top10_routes["route"].iloc[::-1]
# top10_flights = top10_flights.set_index("route").loc[order].reset_index()


fig_top10_flights = px.bar(
    top10_flights,
    x="flights",
    y="route",
    title="Anzahl Flüge für die CO₂-intensivsten Strecken",
    text="flights"
)

fig_top10_flights.update_traces(textposition="outside", texttemplate="%{text}")
fig_top10_flights.update_layout(
    height=600, 
    bargap=0.15, 
    yaxis=dict(
        categoryorder="array", 
        categoryarray=order))

# ---------------------------------------------------
# RENDERING
# ---------------------------------------------------
st.subheader("Top 10 CO₂-intensivste Strecken")
st.plotly_chart(fig_top10, use_container_width=True, key="top10_co2")

st.subheader("Anzahl Flüge für diese Strecken")
st.plotly_chart(fig_top10_flights, use_container_width=True, key="top10_flights_count")



# ---------------------------------------------------
# KENNZAHLEN BERECHNEN
# ---------------------------------------------------

# Gesamtflüge
total_flights = len(filtered)

# Gesamt-CO2
total_co2 = filtered["CO2e_RFI2_t"].sum()

# Beliebteste Route (meiste Flüge)
popular_route = (
    filtered["route"]
    .value_counts()
    .idxmax()
    if total_flights > 0 else "-"
)

popular_route_flights = (
    filtered["route"]
    .value_counts()
    .max()
    if total_flights > 0 else 0
)

# Anteil Bahn-Alternative
train_share = (filtered["train_alternative_available"] == "WAHR").mean() * 100

# Mögliche Einsparung (CO₂ der Strecken mit Bahn-Alternative)
possible_savings = filtered.loc[
    filtered["train_alternative_available"] == "WAHR",
    "CO2e_RFI2_t"
].sum()


# ---------------------------------------------------
# GLOBE MAP
# ---------------------------------------------------
fig_map = go.Figure()

for _, row in filtered.iterrows():
    fig_map.add_trace(
        go.Scattergeo(
            lon=[row["departure_lon"], row["arrival_lon"]],
            lat=[row["departure_lat"], row["arrival_lat"]],
            mode="lines",
            line=dict(width=1, color="orange"),
            opacity=0.6,
            hoverinfo="text",
            text=f"{row['departure_city']} → {row['arrival_city']}<br>CO₂: {row['CO2e_RFI2_t']} t<br>Distanz: {row['km']} km"
        )
    )

fig_map.update_layout(
    title="Transportwege auf dem Globus",
    showlegend=False,
    width=1200,
    height=900,
    geo=dict(
        projection_type="orthographic",
        showland=True,
        landcolor="rgb(230, 230, 230)",
        showcountries=True,
        countrycolor="rgb(200, 200, 200)",
        coastlinecolor="rgb(150, 150, 150)",
    )
)

# ---------------------------------------------------
# LAYOUT: MAP LEFT, TOP10 RIGHT
# ---------------------------------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("Kennzahlen zum Reiseverhalten")

    st.markdown(f"""
    **Flüge gesamt:** {total_flights}  
    **CO₂ gesamt:** {total_co2:.1f} t  
    **Beliebteste Route:** {popular_route} ({popular_route_flights} Flüge)  
    **Bahn-Alternative:** {train_share:.0f}%  
    **Mögliche Einsparung:** {possible_savings:.1f} t CO₂  
    """)

    st.subheader("Transportwege auf dem Globus")
    st.plotly_chart(fig_map, use_container_width=True, key="map")


with right:
    st.subheader("Top 10 CO₂-intensivste Strecken")
    st.plotly_chart(fig_top10, use_container_width=True, key="top10")

# ---------------------------------------------------
# TABLE
# ---------------------------------------------------
st.subheader("Gefilterte Routen")
st.dataframe(filtered[["departure_city", "arrival_city", "km", "CO2e_RFI2_t"]])





############
# to start streamlit enter in terminal: streamlit run app.py