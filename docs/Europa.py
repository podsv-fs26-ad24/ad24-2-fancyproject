import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from streamlit_plotly_events import plotly_events

st.set_page_config(page_title="Europa – Geschäftsreisen", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["route"] = df["departure_iata"] + " → " + df["arrival_iata"]
    return df

df = load_data()

# Europa-Filter (Koordinaten)
df_eu = df[
    (df["departure_lat"].between(35, 70)) &
    (df["departure_lon"].between(-15, 35)) &
    (df["arrival_lat"].between(35, 70)) &
    (df["arrival_lon"].between(-15, 35))
].copy()

st.title("🇪🇺 Europa – Geschäftsreisen & CO₂")

# Filter: Jahr, Business Unit, Stadt
col1, col2, col3 = st.columns(3)

with col1:
    years = sorted(df_eu["year"].unique())
    selected_year = st.selectbox("Jahr", years)

with col2:
    bus_units = ["Alle"] + sorted(df_eu["business_unit"].unique())
    selected_bu = st.selectbox("Business Unit", bus_units)

with col3:
    all_cities = sorted(
        set(df_eu["departure_city"].dropna().unique()) |
        set(df_eu["arrival_city"].dropna().unique())
    )
    selected_city = st.selectbox("Ort (Abflug/Ankunft)", ["Alle"] + all_cities)

mask = df_eu["year"] == selected_year
if selected_bu != "Alle":
    mask &= df_eu["business_unit"] == selected_bu
if selected_city != "Alle":
    mask &= (
        (df_eu["departure_city"] == selected_city) |
        (df_eu["arrival_city"] == selected_city)
    )

filtered = df_eu[mask].copy()

# KPIs
total_trips = len(filtered)
total_co2 = filtered["CO2e RFI2.7 (t)"].sum()
total_km = filtered["km"].sum()
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
colC.metric("Top-Route", top_route)
colD.metric("Bahn-Alternative", f"{train_pct:.0f}%")

st.subheader("Flugrouten in Europa")

clicked_route = st.session_state.get("clicked_route_eu", None)

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
            lonaxis=dict(range=[-15, 35]),
            lataxis=dict(range=[35, 70]),
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
        st.session_state["clicked_route_eu"] = route_name
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

    st.plotly_chart(fig_bu, use_container_width=True)

st.subheader("Top-Routen in Europa")

if not filtered.empty:
    top_routes = (
        filtered.groupby("route")
        .agg(co2=("CO2e RFI2.7 (t)", "sum"), km=("km", "mean"))
        .sort_values("co2", ascending=False)
        .head(10)
    )
    st.dataframe(top_routes)


# ############
# # to start streamlit enter in terminal: streamlit run Europa.py