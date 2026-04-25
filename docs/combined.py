import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Combined Dashboard – Europe & Worldwide", layout="wide")

# ---------------------------------------------------
# DATA LOADING
# ---------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]
    return df

df = load_data()

# ---------------------------------------------------
# TRAVEL CONFIGURATOR
# ---------------------------------------------------
st.header("✈️ Travel Configurator")

# --- 1. Dropdowns ---
departure_options = sorted(df["departure_city"].dropna().unique())
selected_departure = st.selectbox("Departure city", departure_options)

arrival_options = sorted(
    df[df["departure_city"] == selected_departure]["arrival_city"].dropna().unique()
)
selected_arrival = st.selectbox("Arrival city", arrival_options)

# --- 2. Trip type ---
trip_type = st.radio("Trip type", ["One-way", "Round-trip"])

# --- 3. Travel dates ---
departure_date = st.date_input("Departure date")
return_date = st.date_input("Return date") if trip_type == "Round-trip" else None

# --- 4. Train alternative (from dataset) ---
row = df[
    (df["departure_city"] == selected_departure) &
    (df["arrival_city"] == selected_arrival)
]

train_possible = bool(row.iloc[0]["train_alternative_available"]) if not row.empty else False
train_text = "Yes 🚆" if train_possible else "No ❌"
st.markdown(f"**Train alternative available:** {train_text}")

# --- 5. Gamification points ---
points = 50 if train_possible else 0
st.metric("Gamification points", points)

# --- 6. Booking choice ---
booking_choice = st.radio("Preferred travel mode", ["Flight", "Train"])

# --- 7. Booking email ---
secretary_email = "secretariat@company.com"

email_body = f"""
Hello,

Please book the following trip for me:

- From: {selected_departure}
- To: {selected_arrival}
- Departure date: {departure_date}
- Travel mode: {booking_choice}
"""

if trip_type == "Round-trip":
    email_body += f"- Return date: {return_date}\n"

email_body += "\nThank you."

# --- 8. Button + scoreboard ---
if st.button("📧 Generate booking email", key="booking_email_button"):
    st.code(email_body)
    st.success(f"Email text generated – please send it to {secretary_email}.")

    # Celebration ONLY if Train is chosen
    if booking_choice == "Train":
        st.markdown(f"""
        ### 🌟 Great job!
        You earned **{points} points** for your team and made the world a bit greener 🌱
        """)

    # Scoreboard ALWAYS visible
    scoreboard = pd.DataFrame({
        "Team": ["Marketing", "Sales", "HR"],
        "Points": [120, 95, 140]
    })

    st.subheader("🏆 Team Scoreboard")
    st.table(scoreboard)

# ---------------------------------------------------
# MAP FOR SELECTED ROUTE
# ---------------------------------------------------
df_selected_route = df[
    (df["departure_city"] == selected_departure) &
    (df["arrival_city"] == selected_arrival)
]

if not df_selected_route.empty:
    route = df_selected_route.iloc[0]

    map_df = pd.DataFrame({
        "lat": [route["departure_lat"], route["arrival_lat"]],
        "lon": [route["departure_lon"], route["arrival_lon"]],
        "label": ["Start", "Destination"]
    })

    fig = px.scatter_mapbox(
        map_df,
        lat="lat",
        lon="lon",
        hover_name="label",
        zoom=4,
        height=500
    )

    # Color based on train availability
    line_color = "green" if route["train_alternative_available"] else "red"

    fig.add_trace(go.Scattermapbox(
        lat=map_df["lat"],
        lon=map_df["lon"],
        mode="lines",
        line=dict(width=3, color=line_color),
        name="Selected route"
    ))

    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------
# REGION SWITCH
# ---------------------------------------------------
region = st.sidebar.radio("Select region", ["Europe", "Worldwide"])

if region == "Europe":
    st.title("🇪🇺 Europe – Business Travel & CO₂")
else:
    st.title("🌍 Worldwide – Business Travel & CO₂")

# ---------------------------------------------------
# EUROPE FILTER
# ---------------------------------------------------
@st.cache_data
def filter_europe(df):
    return df[
        (df["departure_lat"].between(35, 70)) &
        (df["departure_lon"].between(-15, 35)) &
        (df["arrival_lat"].between(35, 70)) &
        (df["arrival_lon"].between(-15, 35))
    ].copy()

df_eu = filter_europe(df)
df_active = df_eu if region == "Europe" else df

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------
years = sorted(df_active["year"].unique())
selected_year = st.sidebar.selectbox("Year", years)

bus_units = ["All"] + sorted(df_active["business_unit"].dropna().unique())
selected_bu = st.sidebar.selectbox("Business Unit", bus_units)

all_cities = sorted(
    set(df_active["departure_city"].dropna().unique()) |
    set(df_active["arrival_city"].dropna().unique())
)
selected_city = st.sidebar.selectbox("City (Departure/Arrival)", ["All"] + all_cities)

# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------
mask = df_active["year"] == selected_year

if selected_bu != "All":
    mask &= df_active["business_unit"] == selected_bu

if selected_city != "All":
    mask &= (
        (df_active["departure_city"] == selected_city) |
        (df_active["arrival_city"] == selected_city)
    )

filtered = df_active[mask].copy()

# ---------------------------------------------------
# ROUTE AGGREGATION (INCLUDING TRAIN AVAILABILITY)
# ---------------------------------------------------
if not filtered.empty:
    routes = (
        filtered.groupby(
            ["departure_lat", "departure_lon",
             "arrival_lat", "arrival_lon",
             "route", "train_alternative_available"]
        )
        .agg(
            co2=("CO2e RFI2.7 (t)", "sum"),
            km=("km", "mean")
        )
        .reset_index()
    )
else:
    routes = pd.DataFrame()

# ---------------------------------------------------
# MAP (GREEN TRAIN ROUTES, RED FLIGHT ROUTES)
# ---------------------------------------------------
@st.cache_data
def build_map(routes, region):
    fig = go.Figure()

    for _, r in routes.iterrows():

        line_color = "green" if r["train_alternative_available"] else "red"

        fig.add_trace(go.Scattergeo(
            lon=[r["departure_lon"], r["arrival_lon"]],
            lat=[r["departure_lat"], r["arrival_lat"]],
            mode="lines",
            line=dict(width=2, color=line_color),
            hovertext=f"{r['route']}<br>CO₂: {r['co2']:.1f} t<br>Distance: {r['km']:.0f} km<br>Train: {'Yes' if r['train_alternative_available'] else 'No'}",
            hoverinfo="text"
        ))

    if region == "Europe":
        lon_range = [-15, 35]
        lat_range = [35, 70]
    else:
        lon_range = None
        lat_range = None

    fig.update_layout(
        height=650,
        geo=dict(
            projection_type="natural earth",
            lonaxis=dict(range=lon_range),
            lataxis=dict(range=lat_range),
            showland=True,
            landcolor="#e8f0f8",
            showocean=True,
            oceancolor="#b8d4e8",
            showcountries=True,
            countrycolor="#c0cfe0",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    return fig

fig_map = build_map(routes, region)

# ---------------------------------------------------
# LAYOUT
# ---------------------------------------------------
st.subheader("✈ Flight & Train Routes")
st.plotly_chart(fig_map, use_container_width=True)

# GAMIFICATION + TREND
# ---------------------------------------------------
co2_by_year_unit = (
    df.groupby(["year", "business_unit"])["CO2e RFI2.7 (t)"]
    .sum()
    .reset_index(name="co2")
)

co2_by_year_unit["pct_change"] = (
    co2_by_year_unit.groupby("business_unit")["co2"]
    .pct_change() * 100
)

latest_year = co2_by_year_unit["year"].max()

leaderboard = (
    co2_by_year_unit[co2_by_year_unit["year"] == latest_year]
    .sort_values("pct_change")
    .reset_index(drop=True)
)

fig_co2_trend = px.line(
    co2_by_year_unit,
    x="year",
    y="co2",
    color="business_unit",
    markers=True,
    title="📉 CO₂‑Trend pro Business Unit über die Jahre"
)
fig_co2_trend.update_layout(height=450)

# ---------------------------------------------------
# KPIs
# ---------------------------------------------------
total_trips = len(filtered)
total_co2 = filtered["CO2e RFI2.7 (t)"].sum()
train_pct = filtered["train_alternative_available"].mean() * 100 if total_trips > 0 else 0

top_route = (
    filtered.groupby("route")["CO2e RFI2.7 (t)"]
    .sum()
    .sort_values(ascending=False)
    .index[0]
    if not filtered.empty else "–"
)

colA, colB, colC, colD = st.columns(4)
colA.metric("Reisen", total_trips)
colB.metric("CO₂ gesamt", f"{total_co2:.1f} t")
colC.metric("Top‑Route", top_route)
colD.metric("Bahn‑Alternative", f"{train_pct:.0f}%")

# ---------------------------------------------------
# ROUTE AGGREGATION
# ---------------------------------------------------
if not filtered.empty:
    routes = (
        filtered.groupby(
            ["departure_lat", "departure_lon",
             "arrival_lat", "arrival_lon", "route"]
        )
        .agg(
            co2=("CO2e RFI2.7 (t)", "sum"),
            km=("km", "mean")
        )
        .reset_index()
    )
else:
    routes = pd.DataFrame()

# ---------------------------------------------------
# MAP
# ---------------------------------------------------
@st.cache_data
def build_map(routes, region):
    fig = go.Figure()

    for _, r in routes.iterrows():
        fig.add_trace(go.Scattergeo(
            lon=[r["departure_lon"], r["arrival_lon"]],
            lat=[r["departure_lat"], r["arrival_lat"]],
            mode="lines",
            line=dict(width=2, color="rgba(200,50,50,0.5)"),
            hovertext=f"{r['route']}<br>CO₂: {r['co2']:.1f} t<br>Distanz: {r['km']:.0f} km",
            hoverinfo="text"
        ))

    if region == "Europa":
        lon_range = [-15, 35]
        lat_range = [35, 70]
    else:
        lon_range = None
        lat_range = None

    fig.update_layout(
        height=650,
        geo=dict(
            projection_type="natural earth",
            lonaxis=dict(range=lon_range),
            lataxis=dict(range=lat_range),
            showland=True,
            landcolor="#e8f0f8",
            showocean=True,
            oceancolor="#b8d4e8",
            showcountries=True,
            countrycolor="#c0cfe0",
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    return fig

fig_map = build_map(routes, region)

# ---------------------------------------------------
# LAYOUT
# ---------------------------------------------------
if region == "Europa":

    st.subheader("✈ Flugrouten in Europa")
    st.plotly_chart(fig_map, use_container_width=True, key="map_eu")

    st.subheader("Emissionen nach Business Unit")
    if not filtered.empty:
        bu = (
            filtered.groupby("business_unit")["CO2e RFI2.7 (t)"]
            .sum()
            .reset_index()
        )
        fig_bu = px.bar(
            bu,
            x="business_unit",
            y="CO2e RFI2.7 (t)",
            title="CO₂ nach Business Unit",
            color="business_unit"
        )
        st.plotly_chart(fig_bu, use_container_width=True, key="bu_eu")

    st.subheader("🏆 Gamification – CO₂‑Reduktion pro Business Unit")
    st.dataframe(leaderboard)

    st.subheader("📉 CO₂‑Trend pro Business Unit")
    st.plotly_chart(fig_co2_trend, use_container_width=True, key="trend_eu")

else:
    st.subheader("🏆 Gamification – CO₂‑Reduktion pro Business Unit")
    st.dataframe(leaderboard)

    st.subheader("📉 CO₂‑Trend pro Business Unit")
    st.plotly_chart(fig_co2_trend, use_container_width=True, key="trend_world")
