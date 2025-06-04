import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64
import os
import tempfile

# Inicializar la app con Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sistema Farmacia (Dash)"

# Layout con pestañas para mejor organización visual
app.layout = dbc.Container(fluid=True, children=[
    # Encabezado
    html.H2("🧾 Sistema Farmacia", className="text-center my-4"),

    # Pestañas
    dbc.Tabs([
        # Pestaña 1: Carga de Datos
        dbc.Tab(label="Carga de Datos", children=[
            # Stores para mantener datos cargados
            dcc.Store(id="store_catalog", data=None),
            dcc.Store(id="store_base", data=None),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("📂 Subir catálogo"),
                    dbc.CardBody([
                        dcc.Upload(
                            id="upload-catalog",
                            children=html.Div("Arrastra o haz clic para subir (.xlsx)"),
                            style={"border": "1px dashed #aaa", "padding": "20px", "textAlign": "center"},
                            multiple=False
                        ),
                        html.Div(id="catalog-status", className="text-success mt-2")
                    ])
                ]), width=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("📂 Subir base mensual"),
                    dbc.CardBody([
                        dcc.Upload(
                            id="upload-base",
                            children=html.Div("Arrastra o haz clic para subir (.xlsx)"),
                            style={"border": "1px dashed #aaa", "padding": "20px", "textAlign": "center"},
                            multiple=False
                        ),
                        html.Div(id="base-status", className="text-success mt-2")
                    ])
                ]), width=6)
            ], className="mb-4")
        ]),

        # Pestaña 2: Gestión de Productos
        dbc.Tab(label="Productos", children=[
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("📋 Catálogo de Productos"),
                    dbc.CardBody([
                        dag.AgGrid(
                            id="catalog-grid",
                            columnDefs=[],
                            rowData=[],
                            defaultColDef={"flex": 1, "sortable": True, "filter": True, "resizable": True},
                            style={"height": "400px", "width": "100%"}
                        ),
                        html.Div(id="catalog-info", className="mt-2")
                    ])
                ]), width=12)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("🛒 Base Mensual"),
                    dbc.CardBody([
                        dag.AgGrid(
                            id="base-grid",
                            columnDefs=[],
                            rowData=[],
                            rowSelection="single",
                            defaultColDef={"flex": 1, "sortable": True, "filter": True, "resizable": True},
                            style={"height": "400px", "width": "100%"}
                        ),
                        html.Div(id="base-info", className="mt-2")
                    ])
                ]), width=12)
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dbc.Button("✏️ Editar seleccionado", id="open-edit-modal", color="primary", className="me-2"), width="auto"),
                dbc.Col(dbc.Button("🗑️ Eliminar seleccionado", id="open-del-modal", color="danger"), width="auto")
            ], className="mb-4"),
            # Modal Editar
            dbc.Modal([
                dbc.ModalHeader("Editar producto"),
                dbc.ModalBody([
                    dbc.Input(id="modal-edit-unit", type="number", placeholder="Nuevo precio unitario", min=0, step=0.01),
                    dbc.Input(id="modal-edit-units", type="number", placeholder="Unidades por caja", min=1, step=1, className="mt-2")
                ]),
                dbc.ModalFooter([
                    dbc.Button("💾 Guardar cambios", id="modal-save", color="primary"),
                    dbc.Button("Cerrar", id="modal-close", color="secondary", className="ms-2")
                ])
            ], id="edit-modal", is_open=False),
            # Modal Eliminar
            dbc.Modal([
                dbc.ModalHeader("Eliminar producto"),
                dbc.ModalBody("¿Confirma eliminar este producto de la base?"),
                dbc.ModalFooter([
                    dbc.Button("❌ Eliminar", id="modal-delete", color="danger"),
                    dbc.Button("Cancelar", id="modal-cancel", color="secondary", className="ms-2")
                ])
            ], id="delete-modal", is_open=False)
        ]),

        # Pestaña 3: Descargas
        dbc.Tab(label="Descargas", children=[
            dbc.Row([
                dbc.Col(html.Button("📥 Descargar Excel", id="download-excel", className="btn btn-outline-primary"), width=6),
                dbc.Col(html.Button("📥 Descargar CSV", id="download-csv", className="btn btn-outline-secondary"), width=6)
            ], className="mt-4"),
            dcc.Download(id="download-excel-data"),
            dcc.Download(id="download-csv-data")
        ])
    ], className="mb-4")
])

# Callbacks y lógica existente (sin modificaciones)
# Asume que las funciones parse_catalog_xlsx, parse_base_xlsx, etc. ya están definidas en el código original.

@app.callback(
    Output("store_catalog", "data"),
    Output("catalog-status", "children"),
    Input("upload-catalog", "contents"),
    State("upload-catalog", "filename")
)
def manage_catalog(contents, filename):
    if contents:
        # Lógica de parseo (desde el código original)
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
    State("upload-base", "filename")
)
def manage_base_upload(contents, filename):
    if contents:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        df = pd.read_excel(io.BytesIO(decoded))
        data = df.to_dict("records")
        return data, "✔️ Base cargada"
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

# Arranque
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
