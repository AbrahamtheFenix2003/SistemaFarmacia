import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Sistema Farmacia (Dash)"

# ——— Layout —————————————————————————————————————————————
app.layout = dbc.Container([
    html.H2("🧾 Sistema Farmacia"),

    # Stores en memoria
    dcc.Store(id="store_catalog", data=None),
    dcc.Store(id="store_base", data=None),

    # Subida de archivos
    dbc.Row([
        dbc.Col([
            dcc.Upload(
                id="upload-catalog",
                children=html.Div("📂 Subir catálogo (.xlsx)"),
                style={"border":"1px dashed #ccc","padding":"10px","textAlign":"center"},
                multiple=False
            ),
            html.Div(id="catalog-status", style={"marginTop":"5px"})
        ]),
        dbc.Col([
            dcc.Upload(
                id="upload-base",
                children=html.Div("📂 Subir base mensual (.xlsx)"),
                style={"border":"1px dashed #ccc","padding":"10px","textAlign":"center"},
                multiple=False
            ),
            html.Div(id="base-status", style={"marginTop":"5px"})
        ])
    ], className="mb-4"),

    # Catálogo
    html.H4("🔎 Catálogo de Productos"),
    dag.AgGrid(
        id="catalog-grid",
        columnDefs=[], rowData=[],
        dashGridOptions={"rowSelection":"single"},
        style={"height":"300px"}
    ),
    html.Div(id="selected-display", className="mt-2"),

    # Dropdown sincronizado
    dcc.Dropdown(id="manual-dropdown", placeholder="O elige manualmente un código"),
    html.Hr(),

    # Cálculo de precios
    html.H4("💲 Cálculo de Precios"),
    dbc.Row([
        dbc.Col(dbc.Input(id="precio-unit", type="number", placeholder="Precio unitario", min=0, step=0.01), width=4),
        dbc.Col(dbc.Input(id="unidades", type="number", placeholder="Unidades por caja", min=1, step=1), width=4),
        dbc.Col(html.Div(id="precio-total"), width=4)
    ], className="mb-4"),

    # Acción añadir
    dbc.Button("➕ Añadir producto", id="add-btn", color="success"),
    html.Div(id="update-msg", className="mt-2 text-success"),
    html.Hr(),

    # Base Mensual y Acciones
    html.H4("📋 Base Mensual Actualizada"),
    dag.AgGrid(
        id="base-grid", columnDefs=[], rowData=[],
        dashGridOptions={"rowSelection":"single"}, style={"height":"300px"}
    ),
    html.Div([
        dbc.Button("✏️ Editar seleccionado", id="open-edit-modal", color="primary", className="me-2"),
        dbc.Button("🗑️ Eliminar seleccionado", id="open-del-modal", color="danger")
    ], className="mt-3 mb-4"),

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
    ], id="delete-modal", is_open=False),

    html.Hr(),
    # Descargas
    dbc.Row([
        dbc.Col(html.Button("📥 Descargar Excel", id="download-excel", className="btn btn-outline-primary"), width=6),
        dbc.Col(html.Button("📥 Descargar CSV", id="download-csv", className="btn btn-outline-secondary"), width=6)
    ]),
    dcc.Download(id="download-excel-data"), dcc.Download(id="download-csv-data")
], fluid=True)

# Helper functions

def parse_catalog_xlsx(contents):
    _, content_str = contents.split(",",1)
    decoded = base64.b64decode(content_str)
    return pd.read_excel(io.BytesIO(decoded), header=6)


def parse_base_xlsx(contents):
    _, content_str = contents.split(",",1)
    decoded = base64.b64decode(content_str)
    df = pd.read_excel(io.BytesIO(decoded))
    df["CodEstab"] = df.get("CodEstab","").astype(str).str.zfill(7)
    return df

# 1) Carga catálogo
@app.callback(
    Output("store_catalog","data"), Output("catalog-status","children"),
    Input("upload-catalog","contents")
)
def load_cat(contents):
    if contents:
        df = parse_catalog_xlsx(contents)
        if "Cod_Prod" not in df.columns:
            return dash.no_update, "❌ Faltan columna 'Cod_Prod'"
        return df.to_dict("records"), "✔️ Catálogo cargado"
    return None, ""

# 2) Render catálogo + manual dropdown
@app.callback(
    Output("catalog-grid","columnDefs"), Output("catalog-grid","rowData"),
    Output("manual-dropdown","options"), Input("store_catalog","data")
)
def render_cat(data):
    if data:
        df = pd.DataFrame(data)
        cols = [{"field":c} for c in df.columns]
        opts = [{"label":str(v),"value":v} for v in df["Cod_Prod"].unique()]
        return cols, df.to_dict("records"), opts
    return [], [], []

# 3) Carga/gestión base (upload, add, edit, delete)
@app.callback(
    Output("store_base","data"), Output("base-status","children"), Output("update-msg","children"),
    Input("upload-base","contents"), Input("add-btn","n_clicks"),
    Input("modal-save","n_clicks"), Input("modal-delete","n_clicks"),
    State("store_base","data"), State("manual-dropdown","value"),
    State("precio-unit","value"), State("unidades","value"),
    State("modal-edit-unit","value"), State("modal-edit-units","value"),
    State("base-grid","selectedRows")
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
            df = pd.concat([df, pd.DataFrame([{
                "CodEstab":"0021870",
                "CodProd":code,
                "Precio 2":pu,
                "Precio 1":pu*uni
            }])], ignore_index=True)
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
    Output("base-grid","columnDefs"), Output("base-grid","rowData"),
    Input("store_base","data")
)
def render_base(data):
    if data:
        df = pd.DataFrame(data)
        cols = [{"field":c} for c in df.columns]
        return cols, df.to_dict("records")
    return [], []

# 5) Toggle & populate modal Editar
@app.callback(
    [Output("edit-modal","is_open"),
     Output("modal-edit-unit","value"),
     Output("modal-edit-units","value")],
    [Input("open-edit-modal","n_clicks"),
     Input("modal-close","n_clicks"),
     Input("modal-save","n_clicks")],
    [State("edit-modal","is_open"),
     State("base-grid","selectedRows")],
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

# 6) Toggle modal Eliminar
@app.callback(
    Output("delete-modal","is_open"),
    [Input("open-del-modal","n_clicks"),
     Input("modal-cancel","n_clicks"),
     Input("modal-delete","n_clicks")],
    [State("delete-modal","is_open"),
     State("base-grid","selectedRows")],
    prevent_initial_call=True
)
def toggle_delete(open_click, cancel_click, delete_click, is_open, selected):
    trig = ctx.triggered_id
    if trig == "open-del-modal" and selected:
        return True
    if trig in ["modal-cancel", "modal-delete"]:
        return False
    return is_open

# 7) Sync selection
@app.callback(
    Output("manual-dropdown","value"), Output("selected-display","children"),
    Input("catalog-grid","selectedRows"), Input("manual-dropdown","value"),
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
    Output("unidades","value"),
    Input("manual-dropdown","value"),
    State("store_catalog","data")
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

# 9) Calc total
@app.callback(
    Output("precio-total","children"), Input("precio-unit","value"), Input("unidades","value")
)
def calc_total(u, un):
    if u is not None and un is not None:
        return f"💰 Total: {u*un:.2f}"
    return ""

# 10) Descargar Excel
@app.callback(
    Output("download-excel-data","data"),
    Input("download-excel","n_clicks"),
    State("store_base","data"),
    prevent_initial_call=True
)
def download_excel(n, data):
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Base")
        ws = writer.sheets["Base"]
        fmt_txt = writer.book.add_format({"num_format":"@"})
        fmt_num = writer.book.add_format({"num_format":"0.00"})
        for i, c in enumerate(df.columns):
            if c == "CodProd":
                ws.set_column(i, i, 15, fmt_txt)
            elif c in ["Precio 1","Precio 2"]:
                ws.set_column(i, i, 15, fmt_num)
            else:
                ws.set_column(i, i, 15)
    return dcc.send_bytes(buf.getvalue(), "base_actualizada.xlsx")

# 11) Descargar CSV
@app.callback(
    Output("download-csv-data","data"),
    Input("download-csv","n_clicks"),
    State("store_base","data"),
    prevent_initial_call=True
)
def download_csv(n, data):
    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_csv, "base_actualizada.csv", index=False)

if __name__ == "__main__":
    app.run(debug=True)