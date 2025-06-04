import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64, tempfile, os

# Inicializar la app con Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sistema Farmacia (Dash)"

# ——— Layout Mejorado —————————————————————————————————————————————
app.layout = dbc.Container(fluid=True, children=[

    # Encabezado principal
    dbc.Row(
        dbc.Col(
            html.H2("🧾 Sistema Farmacia", className="text-center py-4"),
            width=12
        )
    ),

    # Stores para mantener datos cargados
    dcc.Store(id="store_catalog", data=None),
    dcc.Store(id="store_base", data=None),

    # Sección: Subida de archivos
    dbc.Row([

        # Card: Subir catálogo
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("📂 Subir catálogo")),
                dbc.CardBody([
                    dcc.Upload(
                        id="upload-catalog",
                        children=html.Div("Arrastra o haz clic para subir (.xlsx)"),
                        style={
                            "border": "2px dashed #aaa",
                            "borderRadius": "5px",
                            "padding": "30px",
                            "textAlign": "center",
                            "backgroundColor": "#f9f9f9"
                        },
                        multiple=False
                    ),
                    html.Div(id="catalog-status", className="text-success mt-2")
                ], className="p-3")
            ], className="h-100 shadow-sm"),
            width=6
        ),

        # Card: Subir base mensual
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(html.H5("📂 Subir base mensual")),
                dbc.CardBody([
                    dcc.Upload(
                        id="upload-base",
                        children=html.Div("Arrastra o haz clic para subir (.xlsx)"),
                        style={
                            "border": "2px dashed #aaa",
                            "borderRadius": "5px",
                            "padding": "30px",
                            "textAlign": "center",
                            "backgroundColor": "#f9f9f9"
                        },
                        multiple=False
                    ),
                    html.Div(id="base-status", className="text-success mt-2")
                ], className="p-3")
            ], className="h-100 shadow-sm"),
            width=6
        ),

    ], className="mb-4"),

    # Sección: Catálogo de Productos
    dbc.Card([
        dbc.CardHeader(html.H4("🔎 Catálogo de Productos"), className="bg-light"),
        dbc.CardBody([
            dag.AgGrid(
                id="catalog-grid",
                columnDefs=[],
                rowData=[],
                dashGridOptions={"rowSelection": "single"},
                style={"height": "300px", "width": "100%"}
            ),
            dbc.Row([
                dbc.Col(html.Div(id="selected-display", className="mt-2"), width=6),
                dbc.Col(
                    dcc.Dropdown(
                        id="manual-dropdown",
                        placeholder="O elige manualmente un código"
                    ),
                    width=6
                )
            ], className="align-items-center mt-3"),
        ], className="p-3")
    ], className="mb-4 shadow-sm"),

    # Sección: Cálculo de Precios
    dbc.Card([
        dbc.CardHeader(html.H4("💲 Cálculo de Precios"), className="bg-light"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    dbc.Input(
                        id="precio-unit",
                        type="number",
                        placeholder="Precio unitario",
                        min=0,
                        step=0.01
                    ),
                    width=4
                ),
                dbc.Col(
                    dbc.Input(
                        id="unidades",
                        type="number",
                        placeholder="Unidades por caja",
                        min=1,
                        step=1
                    ),
                    width=4
                ),
                dbc.Col(html.Div(id="precio-total", className="fs-5 fw-bold"), width=4)
            ], className="g-3"),
            dbc.Row(
                dbc.Col(
                    dbc.Button("➕ Añadir producto", id="add-btn", color="success", className="mt-3 w-100"),
                    width=4
                ),
                className="mt-2"
            ),
            html.Div(id="update-msg", className="mt-2 text-success")
        ], className="p-3")
    ], className="mb-4 shadow-sm"),

    # Sección: Base Mensual Actualizada
    dbc.Card([
        dbc.CardHeader(html.H4("📋 Base Mensual Actualizada"), className="bg-light"),
        dbc.CardBody([
            dag.AgGrid(
                id="base-grid",
                columnDefs=[],
                rowData=[],
                dashGridOptions={"rowSelection": "single"},
                style={"height": "300px", "width": "100%"}
            ),
            dbc.Row([
                dbc.Col(
                    dbc.Button("✏️ Editar seleccionado", id="open-edit-modal", color="primary", className="me-2 w-100"),
                    width=3
                ),
                dbc.Col(
                    dbc.Button("🗑️ Eliminar seleccionado", id="open-del-modal", color="danger", className="w-100"),
                    width=3
                )
            ], className="mt-3 gx-3")
        ], className="p-3")
    ], className="mb-4 shadow-sm"),

    # Modal: Editar Producto
    dbc.Modal([
        dbc.ModalHeader("✏️ Editar producto", className="bg-light"),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col(
                    dbc.Input(
                        id="modal-edit-unit",
                        type="number",
                        placeholder="Nuevo precio unitario",
                        min=0,
                        step=0.01
                    ),
                    width=6
                ),
                dbc.Col(
                    dbc.Input(
                        id="modal-edit-units",
                        type="number",
                        placeholder="Unidades por caja",
                        min=1,
                        step=1
                    ),
                    width=6
                )
            ], className="g-3")
        ], className="p-3"),
        dbc.ModalFooter([
            dbc.Button("💾 Guardar cambios", id="modal-save", color="primary"),
            dbc.Button("Cerrar", id="modal-close", color="secondary", className="ms-2")
        ], className="p-2")
    ], id="edit-modal", is_open=False, size="lg", centered=True),

    # Modal: Eliminar Producto
    dbc.Modal([
        dbc.ModalHeader("🗑️ Eliminar producto", className="bg-light"),
        dbc.ModalBody("¿Confirma eliminar este producto de la base?"),
        dbc.ModalFooter([
            dbc.Button("❌ Eliminar", id="modal-delete", color="danger"),
            dbc.Button("Cancelar", id="modal-cancel", color="secondary", className="ms-2")
        ], className="p-2")
    ], id="delete-modal", is_open=False, size="md", centered=True),

    # Sección: Descargas
    dbc.Card([
        dbc.CardHeader(html.H5("📥 Exportar Base Mensual"), className="bg-light"),
        dbc.CardBody(
            dbc.Row([
                dbc.Col(
                    dbc.Button("📥 Descargar Excel", id="download-excel", color="outline-primary", className="w-100"),
                    width=6
                ),
                dbc.Col(
                    dbc.Button("📥 Descargar CSV", id="download-csv", color="outline-secondary", className="w-100"),
                    width=6
                )
            ], className="g-3")
        , className="p-3")
    ], className="mb-4 shadow-sm"),

    # Descargas (callbacks)
    dcc.Download(id="download-excel-data"),
    dcc.Download(id="download-csv-data"),

    html.Br()
])


# ——— Funciones Helper —————————————————————————————————————————————

def parse_catalog_xlsx(contents):
    _, content_str = contents.split(",", 1)
    decoded = base64.b64decode(content_str)
    return pd.read_excel(io.BytesIO(decoded), header=6)


def parse_base_xlsx(contents):
    _, content_str = contents.split(",", 1)
    decoded = base64.b64decode(content_str)
    df = pd.read_excel(io.BytesIO(decoded))
    df["CodEstab"] = df.get("CodEstab", "").astype(str).str.zfill(7)
    return df


# 1) Carga catálogo
@app.callback(
    Output("store_catalog", "data"),
    Output("catalog-status", "children"),
    Input("upload-catalog", "contents")
)
def load_cat(contents):
    if contents:
        df = parse_catalog_xlsx(contents)
        if "Cod_Prod" not in df.columns:
            return no_update, "❌ Faltan columna 'Cod_Prod'"
        return df.to_dict("records"), "✔️ Catálogo cargado"
    return None, ""


# 2) Render catálogo + manual dropdown
@app.callback(
    Output("catalog-grid", "columnDefs"),
    Output("catalog-grid", "rowData"),
    Output("manual-dropdown", "options"),
    Input("store_catalog", "data")
)
def render_cat(data):
    if data:
        df = pd.DataFrame(data)
        cols = [{"field": c} for c in df.columns]
        opts = [{"label": str(v), "value": v} for v in df["Cod_Prod"].unique()]
        return cols, df.to_dict("records"), opts
    return [], [], []


# 3) Gestión base (upload, add, edit, delete)
@app.callback(
    Output("store_base", "data"),
    Output("base-status", "children"),
    Output("update-msg", "children"),
    Input("upload-base", "contents"),
    Input("add-btn", "n_clicks"),
    Input("modal-save", "n_clicks"),
    Input("modal-delete", "n_clicks"),
    State("store_base", "data"),
    State("manual-dropdown", "value"),
    State("precio-unit", "value"),
    State("unidades", "value"),
    State("modal-edit-unit", "value"),
    State("modal-edit-units", "value"),
    State("base-grid", "selectedRows")
)
def manage_base(upload, add, save, delete, stored, code, pu, uni, mpu, muni, selected):
    df = pd.DataFrame(stored) if stored else pd.DataFrame()
    msg_base, msg_update = "", ""
    trig = ctx.triggered_id

    if trig == "upload-base" and upload:
        df = parse_base_xlsx(upload)
        msg_base = "✔️ Base cargada"
    elif trig == "add-btn" and code and pu is not None and uni is not None:
        if code in df.get("CodProd", []):
            msg_update = f"⚠️ {code} ya existe"
        else:
            nuevo = {
                "CodEstab": "0021870",
                "CodProd": code,
                "Precio 2": pu,
                "Precio 1": pu * uni
            }
            df = pd.concat([df, pd.DataFrame([nuevo])], ignore_index=True)
            msg_update = "✔️ Base actualizada"
    elif trig == "modal-save" and mpu is not None and muni is not None and selected:
        sel = selected[0]["CodProd"]
        idx = df.index[df["CodProd"] == sel]
        if not idx.empty:
            i = idx[0]
            df.at[i, "Precio 2"] = mpu
            df.at[i, "Precio 1"] = mpu * muni
            df.at[i, "CodEstab"] = "0021870"
            msg_update = "✔️ Base actualizada"
    elif trig == "modal-delete" and selected:
        sel = selected[0]["CodProd"]
        df = df[df["CodProd"] != sel].reset_index(drop=True)
        msg_update = "✔️ Base actualizada"

    if not df.empty:
        df["CodEstab"] = "0021870"
    return df.to_dict("records"), msg_base, msg_update


# 4) Render base
@app.callback(
    Output("base-grid", "columnDefs"),
    Output("base-grid", "rowData"),
    Input("store_base", "data")
)
def render_base(data):
    if data:
        df = pd.DataFrame(data)
        cols = [{"field": c} for c in df.columns]
        return cols, df.to_dict("records")
    return [], []


# 5) Toggle y poblar modal editar
@app.callback(
    [
        Output("edit-modal", "is_open"),
        Output("modal-edit-unit", "value"),
        Output("modal-edit-units", "value")
    ],
    [
        Input("open-edit-modal", "n_clicks"),
        Input("modal-close", "n_clicks"),
        Input("modal-save", "n_clicks")
    ],
    [
        State("edit-modal", "is_open"),
        State("base-grid", "selectedRows")
    ],
    prevent_initial_call=True
)
def toggle_and_populate_edit(o_click, c_click, save_click, is_open, selected):
    trig = ctx.triggered_id
    if trig == "open-edit-modal" and selected:
        row = selected[0]
        unit_price = row.get("Precio 2")
        total_price = row.get("Precio 1")
        units = int(total_price / unit_price) if unit_price else None
        return True, unit_price, units
    if trig in ["modal-close", "modal-save"]:
        return False, no_update, no_update
    return is_open, no_update, no_update


# 6) Toggle modal eliminar
@app.callback(
    Output("delete-modal", "is_open"),
    [
        Input("open-del-modal", "n_clicks"),
        Input("modal-cancel", "n_clicks"),
        Input("modal-delete", "n_clicks")
    ],
    [
        State("delete-modal", "is_open"),
        State("base-grid", "selectedRows")
    ],
    prevent_initial_call=True
)
def toggle_delete(open_click, cancel_click, delete_click, is_open, selected):
    trig = ctx.triggered_id
    if trig == "open-del-modal" and selected:
        return True
    if trig in ["modal-cancel", "modal-delete"]:
        return False
    return is_open


# 7) Sincronizar selección catálogo
@app.callback(
    Output("manual-dropdown", "value"),
    Output("selected-display", "children"),
    Input("catalog-grid", "selectedRows"),
    Input("manual-dropdown", "value"),
    prevent_initial_call=True
)
def sync_selection(rows, manual):
    trig = ctx.triggered_id
    if trig == "catalog-grid" and rows:
        code = rows[0]["Cod_Prod"]
        return code, f"✅ Seleccionaste: {code}"
    if trig == "manual-dropdown" and manual is not None:
        return manual, f"✅ Seleccionaste: {manual}"
    return no_update, no_update


# 8) Autofill unidades
@app.callback(
    Output("unidades", "value"),
    Input("manual-dropdown", "value"),
    State("store_catalog", "data")
)
def autofill_units(code, data):
    if code and data:
        df = pd.DataFrame(data)
        row = df[df["Cod_Prod"] == code]
        if not row.empty:
            frac = row.iloc[0].get("Fracción")
            if pd.notnull(frac):
                return int(frac)
    return no_update


# 9) Calcular total
@app.callback(
    Output("precio-total", "children"),
    Input("precio-unit", "value"),
    Input("unidades", "value")
)
def calc_total(u, un):
    if u is not None and un is not None:
        return f"💰 Total: {u * un:.2f}"
    return ""


# 10) Descargar Excel
@app.callback(
    Output("download-excel-data", "data"),
    Input("download-excel", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_excel(n, data):
    if not data:
        return dash.no_update
    df = pd.DataFrame(data)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    with pd.ExcelWriter(tmp_file.name, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Base")
        ws = writer.sheets["Base"]
        fmt_txt = writer.book.add_format({"num_format": "@"})
        fmt_num = writer.book.add_format({"num_format": "0.00"})
        for i, c in enumerate(df.columns):
            if c == "CodProd":
                ws.set_column(i, i, 15, fmt_txt)
            elif c in ["Precio 1", "Precio 2"]:
                ws.set_column(i, i, 15, fmt_num)
            else:
                ws.set_column(i, i, 15)
    return dcc.send_file(tmp_file.name)


# 11) Descargar CSV
@app.callback(
    Output("download-csv-data", "data"),
    Input("download-csv", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_csv(n, data):
    if not data:
        return dash.no_update
    df = pd.DataFrame(data)
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", mode="w", newline='', encoding='utf-8')
    df.to_csv(tmp_file.name, index=False)
    return dcc.send_file(tmp_file.name)


# ——— Arranque —————————————————————————————————————————————
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
