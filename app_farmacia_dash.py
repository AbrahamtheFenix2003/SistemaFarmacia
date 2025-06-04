import dash
from dash import Dash, html, dcc, Input, Output, State, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64, tempfile
import os

# 1) Cambiar a un tema Bootswatch “LUX” para tener colores más vivos
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.LUX],
    title="🧾 Sistema Farmacia"
)

# NAVBAR fijo en la parte superior
navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            # Si quisieras poner un logo, podrías cambiarlo por un html.Img(src="/assets/logo.png", height="30px")
            dbc.Row([
                dbc.Col(html.Span("🧾", className="fs-3")),
                dbc.Col(html.Span("Sistema Farmacia", className="fs-4 ms-2"))
            ], align="center", className="g-0"),
            href="#",
            style={"textDecoration": "none"}
        ),
    ]),
    color="dark",
    dark=True,
    sticky="top",
    className="shadow-sm mb-4"
)

app.layout = dbc.Container(fluid=True, children=[
    navbar,

    # Contenedor principal con padding interno y margen superior
    dbc.Container(
        fluid=False,
        className="px-3 mt-4",  # Aquí combinamos ambos estilos en una sola propiedad
        children=[
            # ---------- PESTAÑAS PRINCIPALES ----------
            dbc.Tabs([
                # --------------------- PESTAÑA 1: Carga de Datos ---------------------
                dbc.Tab(label="📂 Carga de Datos", tab_id="tab-upload", label_style={"fontWeight": "600"}, children=[
                    html.Br(),
                    dbc.Row([
                        # Card para subir catálogo
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("📁 Subir Catálogo", className="mb-0"),
                                        className="bg-white border-0"
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Upload(
                                                id="upload-catalog",
                                                children=html.Div("🔍 Arrastra o haz clic para subir (.xlsx)", className="text-muted"),
                                                style={
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "8px",
                                                    "padding": "30px",
                                                    "textAlign": "center",
                                                    "backgroundColor": "#f8f9fa",
                                                },
                                                multiple=False
                                            ),
                                            html.Div(id="catalog-status", className="text-success mt-2")
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4"
                            ),
                            width=6
                        ),
                        # Card para subir base mensual
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.H5("📁 Subir Base Mensual", className="mb-0"),
                                        className="bg-white border-0"
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Upload(
                                                id="upload-base",
                                                children=html.Div("🔍 Arrastra o haz clic para subir (.xlsx)", className="text-muted"),
                                                style={
                                                    "borderWidth": "2px",
                                                    "borderStyle": "dashed",
                                                    "borderRadius": "8px",
                                                    "padding": "30px",
                                                    "textAlign": "center",
                                                    "backgroundColor": "#f8f9fa",
                                                },
                                                multiple=False
                                            ),
                                            html.Div(id="base-status", className="text-success mt-2")
                                        ]
                                    ),
                                ],
                                className="shadow-sm mb-4"
                            ),
                            width=6
                        )
                    ])
                ]),

                # --------------------- PESTAÑA 2: Gestión de Productos ---------------------
                dbc.Tab(label="📋 Gestión de Productos", tab_id="tab-products", label_style={"fontWeight": "600"}, children=[
                    html.Br(),
                    # Título dentro de la pestaña
                    html.H4("🔍 Catálogo de Productos", className="mt-2 mb-3"),

                    # Card con AgGrid para catálogo
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dag.AgGrid(
                                    id="catalog-grid",
                                    columnDefs=[],
                                    rowData=[],
                                    defaultColDef={"flex": 1, "sortable": True, "filter": True, "resizable": True},
                                    style={"height": "350px", "width": "100%"}
                                ),
                                html.Div(id="catalog-info", className="mt-2")
                            ]
                        ),
                        className="shadow-sm mb-4"
                    ),

                    html.H4("💲 Base Mensual", className="mt-4 mb-3"),
                    # Card con AgGrid para base mensual: movemos rowSelection a dashGridOptions
                    dbc.Card(
                        dbc.CardBody(
                            [
                                dag.AgGrid(
                                    id="base-grid",
                                    columnDefs=[],
                                    rowData=[],
                                    dashGridOptions={"rowSelection": "single"},
                                    defaultColDef={"flex": 1, "sortable": True, "filter": True, "resizable": True},
                                    style={"height": "350px", "width": "100%"}
                                ),
                                html.Div(id="base-info", className="mt-2")
                            ]
                        ),
                        className="shadow-sm mb-4"
                    ),

                    # Botones de Editar / Eliminar
                    dbc.Row(
                        [
                            dbc.Col(dbc.Button("✏️ Editar Seleccionado", id="open-edit-modal", color="primary", className="me-2"), width="auto"),
                            dbc.Col(dbc.Button("🗑️ Eliminar Seleccionado", id="open-del-modal", color="danger"), width="auto"),
                        ],
                        className="mb-5"
                    ),

                    # Modal de edición
                    dbc.Modal(
                        [
                            dbc.ModalHeader(html.H5("✏️ Editar Producto", className="mb-0")),
                            dbc.ModalBody(
                                [
                                    dbc.Label("Nuevo Precio Unitario:", className="fw-bold"),
                                    dbc.Input(id="modal-edit-unit", type="number", placeholder="Precio unitario", min=0, step=0.01),
                                    dbc.Label("Unidades por Caja:", className="fw-bold mt-3"),
                                    dbc.Input(id="modal-edit-units", type="number", placeholder="Unidades por caja", min=1, step=1),
                                ]
                            ),
                            dbc.ModalFooter(
                                [
                                    dbc.Button("💾 Guardar Cambios", id="modal-save", color="success"),
                                    dbc.Button("Cerrar", id="modal-close", color="secondary", className="ms-2")
                                ]
                            )
                        ],
                        id="edit-modal",
                        is_open=False,
                        centered=True
                    ),

                    # Modal de eliminación
                    dbc.Modal(
                        [
                            dbc.ModalHeader(html.H5("🗑️ Eliminar Producto", className="mb-0")),
                            dbc.ModalBody("¿Estás seguro de eliminar este producto de la base mensual?"),
                            dbc.ModalFooter(
                                [
                                    dbc.Button("❌ Eliminar", id="modal-delete", color="danger"),
                                    dbc.Button("Cancelar", id="modal-cancel", color="secondary", className="ms-2")
                                ]
                            )
                        ],
                        id="delete-modal",
                        is_open=False,
                        centered=True
                    )
                ]),

                # --------------------- PESTAÑA 3: Descargas ---------------------
                dbc.Tab(label="📥 Descargas", tab_id="tab-download", label_style={"fontWeight": "600"}, children=[
                    html.Br(),
                    dbc.Row(
                        [
                            dbc.Col(dbc.Button("📄 Descargar Excel", id="download-excel", color="info", className="w-100"), width=6),
                            dbc.Col(dbc.Button("📑 Descargar CSV", id="download-csv", color="secondary", className="w-100"), width=6),
                        ],
                        className="mt-4 mb-5"
                    ),
                    # Componentes invisibles para la descarga
                    dcc.Download(id="download-excel-data"),
                    dcc.Download(id="download-csv-data"),
                ]),
            ], id="tabs", active_tab="tab-upload", className="mb-3"),

            # Espacio final antes del footer
            html.Br(),
            html.Hr(),
            dbc.Row(
                dbc.Col(
                    html.P("© 2025 Sistema Farmacia", className="text-center text-muted"),
                    width=12
                )
            )
        ]
    )  # Fin del contenedor interno (solo un className combinado: "px-3 mt-4")
])  # Fin del layout principal


# ————————————————— CALLBACKS (sin cambios) —————————————————

@app.callback(
    Output("store_catalog", "data"),
    Output("catalog-status", "children"),
    Input("upload-catalog", "contents"),
    State("upload-catalog", "filename"),
    prevent_initial_call=True
)
def manage_catalog(contents, filename):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        data = df.to_dict("records")
        return data, "✔️ Catálogo cargado"
    return no_update, no_update

@app.callback(
    Output("store_base", "data"),
    Output("base-status", "children"),
    Input("upload-base", "contents"),
    State("upload-base", "filename"),
    prevent_initial_call=True
)
def manage_base_upload(contents, filename):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        data = df.to_dict("records")
        return data, "✔️ Base mensual cargada"
    return no_update, no_update

@app.callback(
    Output("catalog-grid", "columnDefs"),
    Output("catalog-grid", "rowData"),
    Input("store_catalog", "data")
)
def update_catalog_grid(data):
    if data:
        df = pd.DataFrame(data)
        columns = [{"headerName": col, "field": col} for col in df.columns]
        return columns, data
    return [], []

@app.callback(
    Output("base-grid", "columnDefs"),
    Output("base-grid", "rowData"),
    Input("store_base", "data")
)
def update_base_grid(data):
    if data:
        df = pd.DataFrame(data)
        columns = [{"headerName": col, "field": col} for col in df.columns]
        return columns, data
    return [], []

@app.callback(
    Output("edit-modal", "is_open"),
    Output("modal-edit-unit", "value"),
    Output("modal-edit-units", "value"),
    Input("open-edit-modal", "n_clicks"),
    State("base-grid", "selectedRows"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def open_edit(n_clicks, selected, stored):
    if n_clicks and selected:
        sel = selected[0]
        return True, sel.get("Precio 2"), sel.get("Precio 1") / (sel.get("Precio 2") if sel.get("Precio 2") else 1)
    return False, None, None

@app.callback(
    Output("delete-modal", "is_open"),
    Input("open-del-modal", "n_clicks"),
    State("base-grid", "selectedRows"),
    State("delete-modal", "is_open"),
    prevent_initial_call=True
)
def open_delete(n_clicks, selected, is_open):
    if n_clicks and selected:
        return True
    return False

@app.callback(
    Output("store_base", "data"),
    Output("base-info", "children"),
    Input("modal-save", "n_clicks"),
    State("modal-edit-unit", "value"),
    State("modal-edit-units", "value"),
    State("store_base", "data"),
    State("base-grid", "selectedRows"),
    prevent_initial_call=True
)
def save_edit(n_clicks, mpu, muni, stored, selected):
    if selected and mpu is not None and muni is not None:
        df = pd.DataFrame(stored)
        sel_code = selected[0]["CodProd"]
        idx = df.index[df["CodProd"] == sel_code][0]
        df.at[idx, "Precio 2"] = mpu
        df.at[idx, "Precio 1"] = mpu * muni
        return df.to_dict("records"), "✔️ Base actualizada"
    return no_update, no_update

@app.callback(
    Output("store_base", "data"),
    Output("base-info", "children"),
    Input("modal-delete", "n_clicks"),
    State("store_base", "data"),
    State("base-grid", "selectedRows"),
    prevent_initial_call=True
)
def confirm_delete(n_clicks, stored, selected):
    if selected:
        df = pd.DataFrame(stored)
        sel_code = selected[0]["CodProd"]
        df = df[df["CodProd"] != sel_code]
        return df.to_dict("records"), "✔️ Producto eliminado"
    return no_update, no_update

@app.callback(
    Output("download-excel-data", "data"),
    Input("download-excel", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_excel(n, data):
    if data:
        df = pd.DataFrame(data)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", mode="wb")
        df.to_excel(tmp_file.name, index=False)
        return dcc.send_file(tmp_file.name)
    return no_update

@app.callback(
    Output("download-csv-data", "data"),
    Input("download-csv", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_csv(n, data):
    if data:
        df = pd.DataFrame(data)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline='', encoding='utf-8')
        df.to_csv(tmp_file.name, index=False)
        return dcc.send_file(tmp_file.name)
    return no_update


# Inicia el servidor
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
