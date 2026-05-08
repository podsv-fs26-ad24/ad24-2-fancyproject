import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Europe – Business Travel", layout="wide")

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
# BUSINESS UNIT RENAME + COLORS
# ---------------------------------------------------

# Mapping alte BU → neue BU
bu_rename = {
    "BU1": "Sales & Customer Markets",
    "BU3": "Operations & Delivery",
    "BU2": "Technology & Innovation",
    "BU4": "Corporate Services"
}






# Europa-Filter (Koordinaten)
df_eu = df[
    (df["departure_lat"].between(35, 70)) &
    (df["departure_lon"].between(-15, 35)) &
    (df["arrival_lat"].between(35, 70)) &
    (df["arrival_lon"].between(-15, 35))
].copy()


# Mapping anwenden
df["business_unit"] = df["business_unit"].replace(bu_rename)
df_eu["business_unit"] = df_eu["business_unit"].replace(bu_rename)

# Corporate Farben
bu_colors = {
    "Sales & Customer Markets": "#65524D",
    "Operations & Delivery": "#817E9F",
    "Technology & Innovation": "#D5A021",
    "Corporate Services": "#009B72"
}


st.title("Europe – Company Business Travel & CO₂")





# ---------------------------------------------------
# FILTER + KPI + MAP (in one line)
# ---------------------------------------------------

filter_col, space1, kpi_col, space2, map_col = st.columns([3,1,2,1,6])

# ---------------- FILTER ----------------
with filter_col:
    st.subheader("Travel Filter")

    years = ["All"] + sorted(df_eu["year"].unique())
    selected_year = st.selectbox("Year (starting 2017)", years)

    bus_units = ["All"] + list(bu_rename.values())
    selected_bu = st.selectbox("Business Unit", bus_units)

    departure_options = sorted(df_eu["departure_city"].dropna().unique())
    selected_departure = st.selectbox("Departure city", ["All"] + departure_options)

    if selected_departure != "All":
        arrival_options = sorted(
            df_eu[df_eu["departure_city"] == selected_departure]["arrival_city"]
            .dropna()
            .unique()
        )
    else:
        arrival_options = sorted(df_eu["arrival_city"].dropna().unique())

    selected_arrival = st.selectbox("Arrival city", ["All"] + list(arrival_options))


# ---------------- FILTER LOGIC ----------------
mask = pd.Series(True, index=df_eu.index)

if selected_year != "All":
    mask &= df_eu["year"] == selected_year

if selected_bu != "All":
    mask &= df_eu["business_unit"] == selected_bu

if selected_departure != "All":
    mask &= df_eu["departure_city"] == selected_departure

if selected_arrival != "All":
    mask &= df_eu["arrival_city"] == selected_arrival

filtered = df_eu[mask].copy()


# ---------------- KPI ----------------
with kpi_col:
    st.subheader("KPIs")

    if selected_year == "All":
        df_kpi = df_eu.copy()
    else:
        df_kpi = df_eu[df_eu["year"] == selected_year]

    total_trips = len(df_kpi)
    total_co2 = df_kpi["CO2e RFI2.7 (t)"].sum()

    if not df_kpi.empty:
        top_route = (
            df_kpi.groupby("route")["CO2e RFI2.7 (t)"]
            .sum()
            .sort_values(ascending=False)
            .index[0]
        )
    else:
        top_route = "–"

    if top_route != "–":
        df_top = df_kpi[df_kpi["route"] == top_route]
        train_alt_label = "YES" if df_top["train_alternative_available"].sum() > 0 else "NO"
    else:
        train_alt_label = "NO"

    # KPIs untereinander
    st.metric("Number of Travels", total_trips)
    st.metric("Total CO₂", f"{total_co2:.1f} t")
    st.metric("Top-Route", top_route)
    st.metric("Train-Alternative", train_alt_label)


# ---------------- MAP ----------------
with map_col:
    st.subheader("Company Travel Routes in Europe")

    if not filtered.empty:
        routes = (
            filtered.groupby(
                ["departure_lat", "departure_lon",
                 "arrival_lat", "arrival_lon", "route"]
            )
            .agg(
                co2=("CO2e RFI2.7 (t)", "sum"),
                km=("km", "mean"),
                train_alt=("train_alternative_available", "max")
            )
            .reset_index()
        )

        fig = go.Figure()

        for idx, r in routes.iterrows():

            if r["train_alt"] == 1:
                line_color = "#83781B"   # Zug-Alternative
            else:
                line_color = "#DCC9B6"   # Flug

            fig.add_trace(go.Scattergeo(
                lon=[r["departure_lon"], r["arrival_lon"]],
                lat=[r["departure_lat"], r["arrival_lat"]],
                mode="lines",
                line=dict(width=2, color=line_color),
                hovertext=(
                    f"{r['route']}<br>"
                    f"CO₂: {r['co2']:.1f} t<br>"
                    f"Distance: {r['km']:.0f} km<br>"
                    f"Train alternative: {'YES' if r['train_alt'] == 1 else 'NO'}"
                ),
                hoverinfo="text",
                name=r["route"],
            ))

        fig.update_layout(
            height=550,
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

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No routes found for the selected filters.")



# ---------------------------------------------------
# EMISSIONS BY BUSINESS UNIT  +  TOP ROUTES (SIDE BY SIDE)
# ---------------------------------------------------

col_left, col_spacer, col_right = st.columns([4, 1, 5])

with col_left:
    st.subheader("CO₂ Emissions by Business Unit")

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
            color="business_unit",
            color_discrete_map=bu_colors
        )

        # Zeilenumbruch NUR nach "&"
        tick_labels = [
            label.replace("&", "&<br>") 
            for label in bu["business_unit"]
        ]

        fig_bu = px.bar(
            bu,
            x="business_unit",
            y="CO2e RFI2.7 (t)",
            color="business_unit",
            color_discrete_map=bu_colors
        )

        # Legende ausblenden
        fig_bu.update_layout(showlegend=False)

        # X‑Achsenlabels setzen
        fig_bu.update_xaxes(
            tickmode="array",
            tickvals=bu["business_unit"],
            ticktext=tick_labels,
            title_text="Business Unit"
        )

        # # optional: adapt letter size
        # fig_bu.update_xaxes(tickfont=dict(size=11))


        st.plotly_chart(fig_bu, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with col_right:
    st.subheader("Top-Routes in Europe")

    if not filtered.empty:
        top_routes = (
            filtered.groupby("route")
            .agg(
                co2=("CO2e RFI2.7 (t)", "sum"),
                km=("km", "mean")
            )
            .sort_values("co2", ascending=False)
            .head(10)
            .reset_index()
        )

        top_routes = top_routes.rename(columns={
            "route": "Route",
            "co2": "CO₂‑Sum [t]",
            "km": "Ø‑Kilometer"
        })

        top_routes["Ø‑Kilometer"] = top_routes["Ø‑Kilometer"].round(0)

        st.dataframe(top_routes, use_container_width=True)
    else:
        st.info("No routes available for selected filters.")



# ---------------------------------------------------
# SIMULATION DATE + TARGET TRACKING (SIDE BY SIDE)
# ---------------------------------------------------
col_date, col_spacer, col_target = st.columns([3, 2, 5])



# ---------------------------------------------------
# SIMULATION DATE
# ---------------------------------------------------
with col_date:

    st.subheader("Simulation Date")
    sim_date = st.date_input("Select simulated current date", value=pd.to_datetime("2025-06-30"))
    sim_year = sim_date.year
    sim_day_of_year = sim_date.timetuple().tm_yday
    days_in_year = 366 if sim_year % 4 == 0 else 365
    progress = sim_day_of_year / days_in_year


# ---------------------------------------------------
# TARGET TRACKING (–5% per year, based on previous year)
# ---------------------------------------------------

with col_target:

    df_trend = df[df["year"] <= 2025]

    # CO₂ pro Jahr und Business Unit
    co2_by_year_bu = (
        df_trend.groupby(["year", "business_unit"])["CO2e RFI2.7 (t)"]
        .sum()
        .reset_index(name="co2")
    )

    tracking_rows = []

    for bu in co2_by_year_bu["business_unit"].unique():

        # Vorjahreswert bestimmen
        prev_year = sim_year - 1
        prev_data = co2_by_year_bu[
            (co2_by_year_bu["business_unit"] == bu) &
            (co2_by_year_bu["year"] == prev_year)
        ]

        if prev_data.empty:
            continue

        prev_value = prev_data["co2"].iloc[0]

        # Ziel für das aktuelle Jahr: -5% vom Vorjahr
        target_full_year = prev_value * 0.95

        # Ziel bis zum simulierten Datum
        target_partial = target_full_year * progress

        # Ist-Wert bis zum simulierten Datum
        df_current = df_trend[
            (df_trend["business_unit"] == bu) &
            (df_trend["date"].dt.year == sim_year) &
            (df_trend["date"] <= pd.to_datetime(sim_date))
        ]

        actual_partial = df_current["CO2e RFI2.7 (t)"].sum()

        # Status bestimmen
        if actual_partial <= target_partial:
            status = "🟢 On Track"
        elif actual_partial <= target_partial * 1.10:
            status = "🟡 Slightly Behind"
        else:
            status = "🔴 Off Track"

        tracking_rows.append({
            "Business Unit": bu,
            "Target (YTD)": round(target_partial, 2),
            "Actual (YTD)": round(actual_partial, 2),
            "Status": status
        })

    tracking_df = pd.DataFrame(tracking_rows)

    st.subheader("CO₂ Reduction Target Tracking (–5% vs previous year)")
    st.dataframe(tracking_df)


# ---------------------------------------------------
# CO₂ TREND WITH TARGET + ACTUAL (ALL BUSINESS UNITS)
# ---------------------------------------------------

df_trend = df[df["year"] <= 2025]

# Jahreswerte pro Business Unit
co2_year_bu = (
    df_trend.groupby(["year", "business_unit"])["CO2e RFI2.7 (t)"]
    .sum()
    .reset_index(name="co2")
)

# Letztes abgeschlossenes Jahr
last_full_year = sim_year - 1

# Historische Werte (bis letztes Jahr)
historical = co2_year_bu[co2_year_bu["year"] <= last_full_year]

# Jahrfraktion für Simulationsdatum (z.B. 2025.49)
sim_day_of_year = sim_date.timetuple().tm_yday
days_in_year = 366 if sim_year % 4 == 0 else 365
year_frac = sim_year + (sim_day_of_year - 1) / days_in_year

fig = go.Figure()

# ---------------------------------------------------
# 1) HISTORISCHE WERTE (Linien)
# ---------------------------------------------------
for bu in historical["business_unit"].unique():
    df_bu = historical[historical["business_unit"] == bu]
    fig.add_trace(go.Scatter(
        x=df_bu["year"],
        y=df_bu["co2"],
        mode="lines+markers",
        name=f"{bu} historical"
    ))

# ---------------------------------------------------
# 2) TARGET-LINIE 2025 (95% vom Vorjahr, gepunktet)
# ---------------------------------------------------
for bu in historical["business_unit"].unique():

    # Vorjahreswert
    prev_val = historical[
        (historical["business_unit"] == bu) &
        (historical["year"] == last_full_year)
    ]["co2"].iloc[0]

    # Zielwert für das ganze Jahr
    target_full_year = prev_val * 0.95

    # Zielkurve: von 1.1.2025 bis 31.12.2025
    fig.add_trace(go.Scatter(
        x=[sim_year, sim_year + 1],
        y=[prev_val, target_full_year],
        mode="lines",
        line=dict(dash="dot"),   # gepunktet
        name=f"{bu} target 95%"
    ))
# ---------------------------------------------------
# 3) ACTUAL-LINIE 2025 (von 1.1. bis Simulation Date)
# ---------------------------------------------------
for bu in historical["business_unit"].unique():

    df_current = df_trend[
        (df_trend["business_unit"] == bu) &
        (df_trend["date"].dt.year == sim_year) &
        (df_trend["date"] <= pd.to_datetime(sim_date))
    ]

    actual_ytd = df_current["CO2e RFI2.7 (t)"].sum()

    # Linie von 1.1.2025 (0 t) bis Simulation Date (actual_ytd)
    fig.add_trace(go.Scatter(
        x=[sim_year, year_frac],
        y=[0, actual_ytd],
        mode="lines+markers",
        line=dict(width=3),
        marker=dict(size=9),
        name=f"{bu} actual {sim_year}"
    ))

# ---------------------------------------------------
# Layout
# ---------------------------------------------------
fig.update_layout(
    title=f"CO₂ Trend & Target Projection for Business Units (as of {sim_date})",
    xaxis_title="Year",
    yaxis_title="CO₂ Emissions [t]",
    height=550
)

st.subheader("CO₂ Trend with Target Projection (Business Units)")
st.plotly_chart(fig, use_container_width=True)



# ---------------------------------------------------
# CO₂ BY YEAR & BUSINESS UNIT (Gamification + Trend)
# ---------------------------------------------------
fig_co2_trend_bu = px.line(
    co2_by_year_bu,
    x="year",
    y="co2",
    color="business_unit",
    markers=True,
    title="CO₂‑Trend by Business Units (up to 2025)",
    color_discrete_map=bu_colors
)

fig_co2_trend_bu.update_layout(
    height=450,
    xaxis_title="Year",
    yaxis_title="CO₂‑Emissions [t]",
    legend_title="Business Unit"
)

st.subheader("CO₂‑Trend by Business Unit")
st.plotly_chart(fig_co2_trend_bu, use_container_width=True, key="trendplot_units")


# # ---------------------------------------------------
# # TOP ROUTES IN EUROPE
# # ---------------------------------------------------
# st.subheader("Top-Routes in Europe")

# if not filtered.empty:
#     top_routes = (
#         filtered.groupby("route")
#         .agg(
#             co2=("CO2e RFI2.7 (t)", "sum"),
#             km=("km", "mean")
#         )
#         .sort_values("co2", ascending=False)
#         .head(10)
#         .reset_index()
#     )

#     # nicer display of headers
#     top_routes = top_routes.rename(columns={
#         "route": "Route",
#         "co2": "CO₂‑Sum [t]",
#         "km": "Ø‑Kilometer"
#     })

#     # round km
#     top_routes["Ø‑Kilometer"] = top_routes["Ø‑Kilometer"].round(0)

#     st.dataframe(top_routes)


# ############
# # to start streamlit enter in terminal: streamlit run Europa.py