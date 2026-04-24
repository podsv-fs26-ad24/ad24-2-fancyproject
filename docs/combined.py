import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Combined Dashboard – Europa & Weltweit", layout="wide")

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
# REGION SWITCH
# ---------------------------------------------------
region = st.sidebar.radio("Region auswählen", ["Europa", "Weltweit"])

if region == "Europa":
    st.title("🇪🇺 Europa – Geschäftsreisen & CO₂")
else:
    st.title("🌍 Weltweit – Geschäftsreisen & CO₂")

# ---------------------------------------------------
# EUROPA FILTER
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

df_active = df_eu if region == "Europa" else df

# ---------------------------------------------------
# SIDEBAR FILTER
# ---------------------------------------------------
years = sorted(df_active["year"].unique())
selected_year = st.sidebar.selectbox("Jahr", years)

bus_units = ["Alle"] + sorted(df_active["business_unit"].dropna().unique())
selected_bu = st.sidebar.selectbox("Business Unit", bus_units)

all_cities = sorted(
    set(df_active["departure_city"].dropna().unique()) |
    set(df_active["arrival_city"].dropna().unique())
)
selected_city = st.sidebar.selectbox("Ort (Abflug/Ankunft)", ["Alle"] + all_cities)

# ---------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------
mask = df_active["year"] == selected_year

if selected_bu != "Alle":
    mask &= df_active["business_unit"] == selected_bu

if selected_city != "Alle":
    mask &= (
        (df_active["departure_city"] == selected_city) |
        (df_active["arrival_city"] == selected_city)
    )

filtered = df_active[mask].copy()

# ---------------------------------------------------
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

    st.subheader("✈ Flugrouten weltweit")
    st.plotly_chart(fig_map, use_container_width=True, key="map_world")

    st.subheader("🏆 Gamification – CO₂‑Reduktion pro Business Unit")
    st.dataframe(leaderboard)

    st.subheader("📉 CO₂‑Trend pro Business Unit")
    st.plotly_chart(fig_co2_trend, use_container_width=True, key="trend_world")
