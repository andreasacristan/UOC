import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="Más allá del medallero | Juegos Paralímpicos",
    page_icon="🏅",
    layout="wide"
)

@st.cache_data
def load_data():
    standings = pd.read_excel("data/medal_standings.xlsx")
    athletes = pd.read_excel("data/medal_athlete.xlsx")
    return standings, athletes

standings, athletes = load_data()

# =========================================================
# LIMPIEZA BÁSICA
# =========================================================
standings.columns = [c.strip().lower().replace(" ", "_") for c in standings.columns]
athletes.columns = [c.strip().lower().replace(" ", "_") for c in athletes.columns]

for df in [standings, athletes]:
    if "games_year" in df.columns:
        df["games_year"] = pd.to_numeric(df["games_year"], errors="coerce")


if "rank_type" in standings.columns:
    standings["rank_type"] = standings["rank_type"].astype(str)
    overall_mask = standings["rank_type"].str.lower().str.contains("overall", na=False)
    if overall_mask.any():
        standings = standings[overall_mask].copy()

if {"npc_gold", "npc_silver", "npc_bronze"}.issubset(standings.columns):
    standings["total_medals"] = (
        standings["npc_gold"].fillna(0) +
        standings["npc_silver"].fillna(0) +
        standings["npc_bronze"].fillna(0)
    )


for col in ["npc_name", "sport", "games_season", "games_country", "games_city", "games_continent"]:
    if col in standings.columns:
        standings[col] = standings[col].astype(str).str.strip()
    if col in athletes.columns:
        athletes[col] = athletes[col].astype(str).str.strip()


if "event" in athletes.columns:
    athletes["gender_inferred"] = np.select(
        [
            athletes["event"].astype(str).str.contains("women", case=False, na=False),
            athletes["event"].astype(str).str.contains("men", case=False, na=False),
            athletes["event"].astype(str).str.contains("mixed", case=False, na=False),
        ],
        ["Women", "Men", "Mixed"],
        default="Unknown"
    )

# =========================================================
# COORDENADAS PARA MAPA
# =========================================================
map_coords = None
if {"npc_name", "npc_name_latitude", "npc_name_longitude"}.issubset(athletes.columns):
    map_coords = (
        athletes[["npc_name", "npc_name_latitude", "npc_name_longitude"]]
        .dropna()
        .drop_duplicates(subset=["npc_name"])
        .copy()
    )

map_df = standings.copy()
if map_coords is not None and "npc_name" in standings.columns:
    map_df = map_df.merge(map_coords, on="npc_name", how="left")

# =========================================================
# FILTROS GLOBAL
# =========================================================
st.sidebar.title("Filtros globales")

# Temporada
selected_season = "Todas"
if "games_season" in standings.columns:
    season_options = ["Todas"] + sorted(standings["games_season"].dropna().unique().tolist())
    selected_season = st.sidebar.selectbox("Temporada", season_options)

# Años
selected_years = []
if "games_year" in standings.columns:
    year_options = sorted(standings["games_year"].dropna().unique().tolist())
    selected_years = st.sidebar.multiselect("Año(s)", year_options, default=year_options)

filtered_standings = standings.copy()
filtered_athletes = athletes.copy()
filtered_map = map_df.copy()


if selected_season != "Todas":
    if "games_season" in filtered_standings.columns:
        filtered_standings = filtered_standings[filtered_standings["games_season"] == selected_season]
        filtered_map = filtered_map[filtered_map["games_season"] == selected_season]
    if "games_season" in filtered_athletes.columns:
        filtered_athletes = filtered_athletes[filtered_athletes["games_season"] == selected_season]

if selected_years:
    if "games_year" in filtered_standings.columns:
        filtered_standings = filtered_standings[filtered_standings["games_year"].isin(selected_years)]
        filtered_map = filtered_map[filtered_map["games_year"].isin(selected_years)]
    if "games_year" in filtered_athletes.columns:
        filtered_athletes = filtered_athletes[filtered_athletes["games_year"].isin(selected_years)]


st.title("🏅 Más allá del medallero: una exploración visual de los Juegos Paralímpicos")

st.markdown("""
Esta visualización propone una lectura narrativa de los Juegos Paralímpicos en dos niveles.

En una primera parte, ofrece una visión general para observar la evolución histórica, la distribución geográfica del medallero y la estructura deportiva del evento.  
En una segunda parte, permite comparar países seleccionados para analizar sus trayectorias, sus diferencias entre temporadas y sus perfiles deportivos.

El objetivo no es solo mostrar datos, sino responder preguntas concretas a través de la visualización.
""")


# =========================================================
# KPIS GENERALES
# =========================================================
st.subheader("Resumen general")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_medals = int(filtered_standings["total_medals"].sum()) if "total_medals" in filtered_standings.columns else 0
    st.metric("Medallas totales", f"{total_medals:,}")

with col2:
    total_countries = filtered_standings["npc_name"].nunique() if "npc_name" in filtered_standings.columns else 0
    st.metric("Países", total_countries)

with col3:
    total_sports = filtered_athletes["sport"].nunique() if "sport" in filtered_athletes.columns else 0
    st.metric("Deportes", total_sports)

with col4:
    total_editions = filtered_standings["games_year"].nunique() if "games_year" in filtered_standings.columns else 0
    st.metric("Ediciones", total_editions)

st.divider()

# =========================================================
# SECCIÓN 1: EVOLUCIÓN TEMPORAL
# =========================================================
st.header("1. Evolución global de los Juegos Paralímpicos")

st.markdown("""
**Pregunta:** ¿Cómo ha cambiado el volumen del medallero a lo largo del tiempo?

Esta primera vista ofrece una lectura general de la evolución histórica. Aunque el número de medallas no resume por sí solo toda la complejidad del evento, sí permite observar cambios en escala, continuidad y dimensión competitiva entre distintas ediciones.
Separar verano e invierno permite entender que los Juegos Paralímpicos no siguen un único patrón competitivo, sino que presentan dinámicas diferentes según la temporada.
""")

if {"games_year", "games_season", "total_medals"}.issubset(filtered_standings.columns):
    season_year = (
        filtered_standings.groupby(["games_year", "games_season"], as_index=False)["total_medals"]
        .sum()
        .sort_values("games_year")
    )

    fig_season = px.line(
        season_year,
        x="games_year",
        y="total_medals",
        color="games_season",
        markers=True,
        title="Evolución de medallas según la temporada"
    )
    fig_season.update_layout(
        xaxis_title="Año",
        yaxis_title="Total de medallas",
        legend_title="Temporada"
    )
    st.plotly_chart(fig_season, use_container_width=True)

st.markdown("""
Separar verano e invierno permite ver que no se trata de un único patrón competitivo, sino de dos contextos distintos con niveles de participación y concentración diferentes.
""")

# =========================================================
# SECCIÓN 2: MAPA
# =========================================================
st.header("2. Geografía del medallero")

st.markdown("""
**Pregunta:** ¿Dónde se concentra el rendimiento paralímpico?

El mapa introduce una dimensión geográfica en el análisis. No se trata solo de saber qué países ganan más, sino de observar cómo se distribuye espacialmente el medallero y qué áreas del mundo concentran una mayor presencia competitiva.
""")

if {
    "npc_name",
    "npc_name_latitude",
    "npc_name_longitude",
    "total_medals"
}.issubset(filtered_map.columns):

    map_agg = (
        filtered_map.groupby(
            ["npc_name", "npc_name_latitude", "npc_name_longitude"],
            as_index=False
        )[["total_medals", "npc_gold", "npc_silver", "npc_bronze"]]
        .sum()
    )

    fig_map = px.scatter_geo(
        map_agg,
        lat="npc_name_latitude",
        lon="npc_name_longitude",
        size="total_medals",
        color="total_medals",
        hover_name="npc_name",
        hover_data={
            "npc_gold": True,
            "npc_silver": True,
            "npc_bronze": True,
            "npc_name_latitude": False,
            "npc_name_longitude": False
        },
        projection="natural earth",
        title="Distribución geográfica del total de medallas"
    )
    fig_map.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0)
    )
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("""
    El tamaño de cada punto representa el volumen total de medallas y permite detectar rápidamente qué países tienen un mayor peso dentro del panorama paralímpico.
    """)
else:
    st.info("No se han podido generar las coordenadas necesarias para el mapa.")

    

# =========================================================
# SECCIÓN 3: ESTRUCTURA DEPORTIVA
# =========================================================
st.header("3. Estructura deportiva de la competición")

st.markdown("""
**Pregunta:** ¿Qué deportes tienen más peso dentro del conjunto de datos?

Para complementar la dimensión geográfica e histórica, esta sección se centra en la estructura deportiva. En lugar de limitarse a un ranking de países, permite observar qué disciplinas concentran más actividad y presencia en el dataset.
""")

if "sport" in filtered_athletes.columns:
    sport_agg = (
        filtered_athletes.groupby("sport", as_index=False)
        .agg(
            records=("sport", "size"),
            athletes_sum=("athletes", "sum") if "athletes" in filtered_athletes.columns else ("sport", "size"),
            events_sum=("events", "sum") if "events" in filtered_athletes.columns else ("sport", "size")
        )
        .sort_values("records", ascending=False)
    )

    fig_treemap = px.treemap(
        sport_agg,
        path=["sport"],
        values="records",
        color="athletes_sum",
        color_continuous_scale="Blues",
        title="Treemap de deportes según presencia en el dataset"
    )
    st.plotly_chart(fig_treemap, use_container_width=True)

    st.markdown("""
    El treemap ofrece una vista más visual y menos convencional de la estructura deportiva, mostrando de forma simultánea el peso relativo de cada disciplina y su volumen de atletas.
    """)
else:
    st.info("No hay información suficiente para construir la visualización por deportes.")
    
    
# =========================================================
# SECCIÓN 4: EXPLORACIÓN COMPARATIVA
# =========================================================
st.divider()
st.header("4. Explora y compara países")

st.markdown("""
Hasta este punto, la visualización ha ofrecido una lectura general del fenómeno.  
A continuación, la interfaz pasa a una lógica más exploratoria: en lugar de agregar todos los países juntos, permite **comparar explícitamente varios países seleccionados** y observar cómo cambian sus trayectorias, perfiles y especializaciones deportivas.
""")

country_options = []
if "npc_name" in filtered_standings.columns:
    country_options = sorted(filtered_standings["npc_name"].dropna().unique().tolist())

default_countries = [c for c in ["Spain", "China", "United States"] if c in country_options]
if not default_countries and len(country_options) >= 3:
    default_countries = country_options[:3]

selected_countries = st.multiselect(
    "Selecciona países para comparar",
    country_options,
    default=default_countries
)

if not selected_countries:
    st.warning("Selecciona al menos un país para activar la comparación.")
    st.stop()

compare_standings = filtered_standings[filtered_standings["npc_name"].isin(selected_countries)].copy()
compare_athletes = filtered_athletes[filtered_athletes["npc_name"].isin(selected_countries)].copy()

# -------------------------
# KPIs comparativos
# -------------------------
st.subheader("Resumen comparativo")

summary = (
    compare_standings.groupby("npc_name", as_index=False)
    .agg(
        total_medals=("total_medals", "sum"),
        gold=("npc_gold", "sum"),
        silver=("npc_silver", "sum"),
        bronze=("npc_bronze", "sum")
    )
    .sort_values("total_medals", ascending=False)
)

kpi_cols = st.columns(len(selected_countries))
for i, country in enumerate(selected_countries):
    row = summary[summary["npc_name"] == country]
    with kpi_cols[i]:
        if not row.empty:
            total = int(row["total_medals"].iloc[0])
            gold = int(row["gold"].iloc[0])
            st.metric(country, f"{total} medallas", f"{gold} oros")
        else:
            st.metric(country, "0 medallas")

# -------------------------
# Evolución comparativa
# -------------------------
st.subheader("4.1 ¿Cómo ha evolucionado el rendimiento de los países seleccionados?")

st.markdown("""
Esta comparación permite detectar trayectorias más estables, crecimientos más intensos o diferencias claras de escala entre países.
""")
medals_by_year_country = (
    compare_standings.groupby(["games_year", "npc_name"], as_index=False)["total_medals"]
    .sum()
    .sort_values("games_year")
)

fig_compare_line = px.line(
    medals_by_year_country,
    x="games_year",
    y="total_medals",
    color="npc_name",
    markers=True,
    title="Comparación de medallas por año"
)
fig_compare_line.update_layout(
    xaxis_title="Año",
    yaxis_title="Total de medallas",
    legend_title="País"
)
st.plotly_chart(fig_compare_line, use_container_width=True)

# -------------------------
# Verano vs invierno por país
# -------------------------
st.subheader("4.2 ¿Cambian estos perfiles entre verano e invierno?")

st.markdown("""
Esta visualización compara el rendimiento de los países seleccionados en ambas temporadas y permite observar si su presencia competitiva es similar o si depende claramente del contexto de verano o invierno.
""")

if {"games_year", "games_season", "npc_name", "total_medals"}.issubset(compare_standings.columns):
    season_country_year = (
        compare_standings.groupby(["games_year", "games_season", "npc_name"], as_index=False)["total_medals"]
        .sum()
        .sort_values("games_year")
    )

    fig_season_country = px.line(
        season_country_year,
        x="games_year",
        y="total_medals",
        color="npc_name",
        facet_col="games_season",
        markers=True,
        title="Evolución de medallas por país en verano e invierno"
    )

    fig_season_country.update_layout(
        xaxis_title="Año",
        yaxis_title="Total de medallas",
        legend_title="País"
    )

    st.plotly_chart(
        fig_season_country,
        use_container_width=True,
        key="country_season_facet_comparison"
    )

st.markdown("""
La separación por temporada ayuda a detectar perfiles deportivos distintos y a evitar una lectura demasiado agregada del rendimiento paralímpico.
""")


# -------------------------
# 4.3 Concentración del rendimiento por deporte
# -------------------------
st.subheader("4.3 ¿En qué deportes se concentra el rendimiento de cada país?")

st.markdown("""
Esta visualización muestra la distribución de los registros de medalla del dataset detallado para cada combinación de país y deporte.

Su objetivo no es representar toda la participación deportiva, sino observar si el rendimiento de cada país aparece más concentrado en unas pocas disciplinas o más repartido entre varios deportes.
""")

if "sport" in compare_athletes.columns:
    sport_country = (
        compare_athletes.groupby(["npc_name", "sport"], as_index=False)
        .size()
        .rename(columns={"size": "medal_records"})
    )


    top_sports = (
        sport_country.groupby("sport", as_index=False)["medal_records"]
        .sum()
        .sort_values("medal_records", ascending=False)
        .head(12)["sport"]
        .tolist()
    )

    sport_country = sport_country[sport_country["sport"].isin(top_sports)]

    heatmap_df = sport_country.pivot(
        index="npc_name",
        columns="sport",
        values="medal_records"
    ).fillna(0)

    fig_heatmap = px.imshow(
        heatmap_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        title="Heatmap país × deporte"
    )

    fig_heatmap.update_layout(
        xaxis_title="Deporte",
        yaxis_title="País"
    )

    st.plotly_chart(
        fig_heatmap,
        use_container_width=True,
        key="country_sport_heatmap"
    )

    st.markdown("""
    Cuanto más intenso es el color, mayor es el número de registros de medalla en esa combinación de país y deporte. Esto permite detectar perfiles más especializados y comparar si distintos países concentran su rendimiento en disciplinas similares o diferentes.
    """)
else:
    st.info("No hay suficiente información deportiva para generar esta visualización.")
    
    
# -------------------------
# 4.4 Diversidad deportiva
# -------------------------
st.subheader("4.4 ¿Qué países muestran una presencia más diversa?")

st.markdown("""
Como complemento al heatmap anterior, esta visualización resume cuántos deportes distintos aparecen asociados a cada país dentro de los datos filtrados.

Mientras que la vista anterior mostraba en qué deportes se concentra el rendimiento, aquí el objetivo es comparar el grado de diversidad deportiva de cada país de forma sintética.
""")

if "sport" in compare_athletes.columns:
    diversity = (
        compare_athletes.groupby("npc_name")["sport"]
        .nunique()
        .reset_index(name="sports_with_presence")
        .sort_values("sports_with_presence", ascending=True)
    )

    fig_diversity = px.scatter(
        diversity,
        x="sports_with_presence",
        y="npc_name",
        size="sports_with_presence",
        color="npc_name",
        title="Diversidad deportiva de los países seleccionados"
    )

    fig_diversity.update_layout(
        xaxis_title="Número de deportes distintos",
        yaxis_title="País",
        showlegend=False
    )

    st.plotly_chart(
        fig_diversity,
        use_container_width=True,
        key="sport_diversity_dotplot"
    )

    st.markdown("""
    Esta vista permite identificar rápidamente qué países aparecen asociados a un abanico más amplio de deportes y cuáles presentan un perfil más reducido o especializado.
    """)
else:
    st.info("No hay suficiente información deportiva para calcular la diversidad.")
    
    
    
# -------------------------
# 4.5 Relación entre diversidad deportiva y medallas
# -------------------------
st.subheader("4.5 ¿Existe relación entre competir en más deportes y ganar más medallas?")

st.markdown("""
Esta visualización sitúa a los países seleccionados dentro del contexto general del conjunto de datos.

El eje horizontal representa el número de deportes distintos en los que aparece cada país, mientras que el eje vertical muestra el total de medallas. De este modo, se puede observar si una mayor diversidad deportiva parece asociarse con un mayor volumen de éxito.
""")


country_total = (
    filtered_standings.groupby("npc_name", as_index=False)
    .agg(
        total_medals=("total_medals", "sum"),
        gold=("npc_gold", "sum") if "npc_gold" in filtered_standings.columns else ("total_medals", "sum")
    )
)


country_sports = (
    filtered_athletes.groupby("npc_name")["sport"]
    .nunique()
    .reset_index(name="sports_count")
)


profile = country_total.merge(country_sports, on="npc_name", how="left")
profile["sports_count"] = profile["sports_count"].fillna(0)

profile["selected"] = profile["npc_name"].isin(selected_countries)
profile["group"] = profile["selected"].map({
    True: "Países seleccionados",
    False: "Resto de países"
})


fig_profile = px.scatter(
    profile,
    x="sports_count",
    y="total_medals",
    size="total_medals",
    color="group",
    hover_name="npc_name",
    hover_data={
        "sports_count": True,
        "total_medals": True,
        "gold": True,
        "group": False
    },
    labels={
        "sports_count": "Número de deportes distintos",
        "total_medals": "Total de medallas",
        "group": ""
    },
    color_discrete_map={
        "Países seleccionados": "#1f4e79",
        "Resto de países": "#c7c7c7"
    },
    title="Relación entre diversidad deportiva y medallas ganadas"
)

fig_profile.update_traces(
    marker=dict(
        line=dict(width=0.8, color="white")
    ),
    opacity=0.8
)


selected_profile = profile[profile["selected"]].copy()

fig_profile.add_scatter(
    x=selected_profile["sports_count"],
    y=selected_profile["total_medals"],
    mode="text",
    text=selected_profile["npc_name"],
    textposition="top center",
    showlegend=False
)

fig_profile.update_layout(
    xaxis_title="Número de deportes distintos",
    yaxis_title="Total de medallas",
    legend_title="",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=20, r=20, t=60, b=20)
)

fig_profile.update_xaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    zeroline=False
)

fig_profile.update_yaxes(
    showgrid=True,
    gridcolor="rgba(0,0,0,0.08)",
    zeroline=False
)

st.plotly_chart(fig_profile, use_container_width=True, key="sports_vs_medals_scatter")



# =========================================================
# TABLAS
# =========================================================
with st.expander("Ver datos filtrados de medal_standings"):
    st.dataframe(filtered_standings)

with st.expander("Ver datos filtrados de medal_athlete"):
    st.dataframe(filtered_athletes)