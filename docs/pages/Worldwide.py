import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="Weltweit – Geschäftsreisen", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]
    return df

df = load_data()

st.title("🌐 Weltweite Geschäftsreisen & CO₂")

col1, col2, col3 = st.columns(3)

with col1:
    years = sorted(df["year"].unique())
    selected_year = st.selectbox("Jahr", years)

with col2:
    bus_units = ["Alle"] + sorted(df["business_unit"].unique())
    selected_bu = st.selectbox("Business Unit", bus_units)

with col3:
    all_cities = sorted(
        set(df["departure_city"].dropna().unique()) |
        set(df["arrival_city"].dropna().unique())
    )
    selected_city = st.selectbox("Ort (Abflug/Ankunft)", ["Alle"] + all_cities)

mask = df["year"] == selected_year
if selected_bu != "Alle":
    mask &= df["business_unit"] == selected_bu
if selected_city != "Alle":
    mask &= (
        (df["departure_city"] == selected_city) |
        (df["arrival_city"] == selected_city)
    )

filtered = df[mask].copy()

# KPIs
total_trips = len(filtered)
total_co2 = filtered["CO2e RFI2.7 (t)"].sum()
total_km = filtered["km"].sum()

colA, colB, colC = st.columns(3)
colA.metric("Reisen", total_trips)
colB.metric("CO₂ gesamt", f"{total_co2:.1f} t")
colC.metric("km gesamt", f"{total_km:,.0f}")

st.subheader("Weltweite Flugrouten")

clicked_route = st.session_state.get("clicked_route_world", None)

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

    fig = go.Figure()

    for idx, r in routes.iterrows():
        is_selected = (r["route"] == clicked_route)
        fig.add_trace(go.Scattergeo(
            lon=[r["departure_lon"], r["arrival_lon"]],
            lat=[r["departure_lat"], r["arrival_lat"]],
            mode="lines",
            line=dict(
                width=6 if is_selected else 2,
                color="rgba(255,0,0,0.9)" if is_selected else "rgba(200,50,50,0.5)"
            ),
            hovertext=f"{r['route']}<br>CO₂: {r['co2']:.1f} t<br>Distanz: {r['km']:.0f} km",
            hoverinfo="text",
            customdata=[r["route"], r["co2"], r["km"]],
            name=r["route"]
        ))

    fig.update_layout(
        height=650,
        geo=dict(
            projection_type="natural earth",
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

    events = plotly_events(fig, click_event=True, hover_event=False, select_event=False)

    if events:
        cd = events[0]["customdata"]
        route_name, co2_val, km_val = cd
        st.session_state["clicked_route_world"] = route_name
        clicked_route = route_name

    if clicked_route:
        r = routes[routes["route"] == clicked_route].iloc[0]
        duration_h = r["km"] / 800.0
        st.info(
            f"**Ausgewählte Route:** {clicked_route}  \n"
            f"**Distanz:** {r['km']:.0f} km  \n"
            f"**Flugdauer (geschätzt):** {duration_h:.1f} h  \n"
            f"**CO₂‑Ausstoss:** {r['co2']:.2f} t"
        )
else:
    st.info("Keine Daten für diese Auswahl.")

st.subheader("Top-Routen weltweit")

if not filtered.empty:
    top_routes = (
        filtered.groupby("route")
        .agg(co2=("CO2e RFI2.7 (t)", "sum"), km=("km", "mean"))
        .sort_values("co2", ascending=False)
        .head(10)
    )
    st.dataframe(top_routes)
