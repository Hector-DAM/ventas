import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import requests

# Cargar los datos de ventas
df = pd.read_csv('ventas_por_region.csv')

# Reemplazar los nombres de los estados
nombres_estados = {
    "D.F.": "Ciudad de México",
    "Mexico": "México",
    "Nuevo Leon": "Nuevo León",
    "Queretaro": "Querétaro",
    "San Luis Potosi": "San Luis Potosí",
    "Yucatan": "Yucatán",
    "Aguascalientes": "Aguascalientes",
    "Baja California": "Baja California",
    "Baja California Sur": "Baja California Sur",
    "Campeche": "Campeche",
    "Chiapas": "Chiapas",
    "Chihuahua": "Chihuahua",
    "Coahuila de Zaragoza": "Coahuila",
    "Colima": "Colima",
    "Durango": "Durango",
    "Guanajuato": "Guanajuato",
    "Guerrero": "Guerrero",
    "Hidalgo": "Hidalgo",
    "Jalisco": "Jalisco",
    "México": "México",
    "Michoacán de Ocampo": "Michoacán",
    "Morelos": "Morelos",
    "Nayarit": "Nayarit",
    "Nuevo León": "Nuevo León",
    "Oaxaca": "Oaxaca",
    "Puebla": "Puebla",
    "Querétaro": "Querétaro",
    "Quintana Roo": "Quintana Roo",
    "San Luis Potosí": "San Luis Potosí",
    "Sinaloa": "Sinaloa",
    "Sonora": "Sonora",
    "Tabasco": "Tabasco",
    "Tamaulipas": "Tamaulipas",
    "Tlaxcala": "Tlaxcala",
    "Veracruz de Ignacio de la Llave": "Veracruz",
    "Yucatán": "Yucatán",
    "Zacatecas": "Zacatecas",
    "Ciudad de México": "Ciudad de México"
}

# Reemplazar los nombres de los estados en la columna 'final_region'
df["final_region"] = df["final_region"].replace(nombres_estados)


# Descargar el archivo GeoJSON desde la URL
geojson_url = "https://raw.githubusercontent.com/angelnmara/geojson/refs/heads/master/mexicoHigh.json"
response = requests.get(geojson_url)
mexico_geojson = response.json()

# Agrupar los datos por estado, año y mes
grouped_data = df.groupby(['final_region', 'year', 'month_num'], as_index=False)[['total_sales', 'total_items']].sum()

# Crear una lista de años
years_list = sorted(df['year'].unique())

# Crear la aplicación Dash
app = dash.Dash(__name__)

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Crecimiento de Ventas por Estado en México", style={"textAlign": "center"}),

    html.Div([
        dcc.Dropdown(
            id="year1-selector",
            options=[{"label": str(year), "value": year} for year in years_list],
            value=years_list[0],  # Año inicial
            clearable=False,
            placeholder="Selecciona el año inicial",
            style={"width": "30%", "display": "inline-block", "margin-right": "20px"}
        ),
        dcc.Dropdown(
            id="year2-selector",
            options=[{"label": str(year), "value": year} for year in years_list],
            value=years_list[-1],  # Año final
            clearable=False,
            placeholder="Selecciona el año final",
            style={"width": "30%", "display": "inline-block", "margin-right": "20px"}
        ),
        dcc.Dropdown(
            id="mes-selector",
            options=[{"label": str(month), "value": month} for month in grouped_data["month_num"].unique()],
            value=grouped_data["month_num"].unique()[0],  # Mes seleccionado
            clearable=False,
            placeholder="Selecciona un mes",
            style={"width": "30%", "display": "inline-block"}
        ),
        dcc.Dropdown(
            id="metric-selector",
            options=[
                {"label": "Crecimiento (%)", "value": "growth"},
                {"label": "Ventas ($)", "value": "total_sales"},
                {"label": "Piezas Vendidas", "value": "total_items"}
            ],
            value="total_sales",  # Métrica predeterminada
            clearable=False,
            placeholder="Selecciona una métrica",
            style={"width": "30%", "display": "inline-block"}
        )
    ], style={"textAlign": "center"}),

    dcc.Graph(id="mapa-ventas", style={"height": "60vh"}),
    html.H3("Top 5 Estados", style={"textAlign": "center"}),
    dash_table.DataTable(
        id="top5-table",
        columns=[
            {"name": "Estado", "id": "final_region"},
            {"name": "Métrica", "id": "metric"}
        ],
        data=[],
        style_table={"width": "50%", "margin": "auto"},
        style_cell={"textAlign": "center"}
    )
])

# Callback para actualizar el mapa y la tabla
@app.callback(
    [Output("mapa-ventas", "figure"), Output("top5-table", "data")],
    [
        Input("year1-selector", "value"),
        Input("year2-selector", "value"),
        Input("mes-selector", "value"),
        Input("metric-selector", "value")
    ]
)
def actualizar_mapa_y_tabla(year1, year2, mes_seleccionado, metric_seleccionada):
    # Filtrar los datos para los años y mes seleccionados
    df_year1 = grouped_data[(grouped_data["year"] == year1) & (grouped_data["month_num"] == mes_seleccionado)]
    df_year2 = grouped_data[(grouped_data["year"] == year2) & (grouped_data["month_num"] == mes_seleccionado)]

    # Combinar los datos de los dos años
    df_combined = pd.merge(df_year1, df_year2, on='final_region', suffixes=(f'_{year1}', f'_{year2}'))

    # Calcular el crecimiento si la métrica seleccionada es "growth"
    if metric_seleccionada == "growth":
        df_combined['growth'] = ((df_combined[f'total_sales_{year2}'] - df_combined[f'total_sales_{year1}']) / df_combined[f'total_sales_{year1}']) * 100
        metric_column = "growth"
    else:
        metric_column = f"{metric_seleccionada}_{year2}"

    # Crear el mapa coroplético
    fig = px.choropleth(
        df_combined,
        geojson=mexico_geojson,
        locations="final_region",
        featureidkey="properties.name",
        color=metric_column,
        color_continuous_scale="YlGnBu",
        title=f"{'Crecimiento (%)' if metric_seleccionada == 'growth' else 'Ventas ($)' if metric_seleccionada == 'total_sales' else 'Piezas Vendidas'} por Estado (Mes {mes_seleccionado} - {year1} vs {year2})"
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        width=1200,  # Ancho del mapa
        height=600   # Altura del mapa
    )

    # Crear la tabla con los top 5 estados
    top5_data = df_combined.nlargest(5, metric_column)[['final_region', metric_column]]
    top5_data = top5_data.rename(columns={metric_column: "metric"})
    top5_data["metric"] = top5_data["metric"].round(2)  # Redondear a 2 decimales

    return fig, top5_data.to_dict("records")

# Ejecutar la aplicación
if __name__ == "__main__":
    app.run_server(debug=True)
