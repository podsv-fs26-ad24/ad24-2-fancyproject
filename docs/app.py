import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_data
def load_data():
    df = pd.read_excel("traveldata-export.xlsx", sheet_name="travel_data")
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_data()

df.columns = df.columns.str.strip().str.replace(" ", "_").str.replace("(", "").str.replace(")", "")

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
# FILTER ANWENDEN
# -----------------------------
filtered = df[
    (df["date"].dt.year == year) &
    (df["transport_mode"].isin(transport)) &
    (df["subunit"].isin(subunit)) &
    (df["haul"].isin(haul)) &
    (df["train_alternative_available"].isin(train))
]

# st.subheader("Gefilterte Daten")
# st.write(filtered)

# # Top 10 Orte nach CO₂
# top10 = (
#     filtered
#     .sort_values("CO2e_RFI2_t", ascending=False)
#     .head(10)
# )

# fig = px.bar(
#     top10.sort_values("CO2e_RFI2_t"),
#     x="CO2e_RFI2_t",
#     y="arrival_city",
#     title="Top 10 CO₂-Emissionen nach Zielstadt",
#     text="CO2e_RFI2_t"
# )

# fig.update_traces(
#     textposition="outside",
#     texttemplate="%{text:.1f} t"
# )

# fig.update_layout(
#     height=800,
#     bargap=0.15
# )

# st.plotly_chart(fig)



# # Beispielplot für alle Städte
# fig = px.bar(
#     filtered,
#     x="CO2e_RFI2_t",
#     y="arrival_city",    
#     title="CO₂-Emissionen nach Zielstadt"
# )

# fig.update_layout(
#     height=1800
# )

# # st.plotly_chart(fig)



# # -----------------------------
# # GLOBE / WELTKARTE MIT ROUTEN
# # -----------------------------

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
        projection_type="orthographic",   # Globus
        showland=True,
        landcolor="rgb(230, 230, 230)",
        showcountries=True,
        countrycolor="rgb(200, 200, 200)",
        coastlinecolor="rgb(150, 150, 150)",
        lataxis=dict(showgrid=True, gridwidth=0.5),
        lonaxis=dict(showgrid=True, gridwidth=0.5),
    )
)

# st.plotly_chart(fig_map)











######### neue variante ###########
# KPI-Bereich
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("Flüge gesamt", f"{len(filtered)}")
kpi2.metric("CO₂ gesamt (t)", f"{filtered['CO2e_RFI2_t'].sum():.1f}")
kpi3.metric("Top-Ziel", filtered.groupby("arrival_city")["CO2e_RFI2_t"].sum().idxmax())
kpi4.metric("Bahn-Alternative (%)", f"{(filtered['train_alternative_available'] == 'WAHR').mean() * 100:.0f}%")



left, right = st.columns([2, 1])   # Globus breiter

with left:
    st.subheader("Transportwege auf dem Globus")
    st.plotly_chart(fig_map, use_container_width=True)

with right:
    st.subheader("Top 10 CO₂-Emissionen nach Zielort")
    st.plotly_chart(fig, use_container_width=True)



st.subheader("Gefilterte Routen")
st.dataframe(filtered[["departure_city", "arrival_city", "km", "CO2e_RFI2_t"]])















# # Sidebar filters
# year = st.sidebar.selectbox("Jahr", sorted(df["date"].dt.year.unique()))
# transport = st.sidebar.selectbox("Transportart", df["transport_mode"].unique())

# filtered = df[
#     (df["date"].dt.year == year) &
#     (df["transport_mode"] == transport)
# ]

# st.title("Geschäftsreisen & CO₂-Emissionen")

# # Example plot
# fig = px.bar(
#     filtered,
#     x="arrival_cit",
#     y="CO2e RFI2",
#     title="CO₂-Emissionen nach Zielstadt"
# )
# st.plotly_chart(fig)
