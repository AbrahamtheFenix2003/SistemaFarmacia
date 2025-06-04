import dash
from dash import Dash, html, dcc, Input, Output, State, ctx, no_update
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import io, base64
import os
import tempfile # Ya estaba, solo reordenando imports

# --- Inicialización de la App ---
# Usar un tema de Bootstrap más moderno y añadir soporte para iconos Bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP]) # ZEPHYR es un ejemplo, puedes probar otros como FLATLY, LITERA, LUX, MORPH, QUARTZ, VAPOR
app.title = "Sistema Farmacia Avanzado"

# --- Layout Principal Mejorado ---
app.layout = dbc.Container([
    # Store para datos
    dcc.Store(id="store_catalog", data=None),
    dcc.Store(id="store_base", data=None),
    dcc.Store(id='store_selected_catalog_code', data=None), # Para guardar el código seleccionado

    # Encabezado tipo Navbar
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Inicio", href="#", className="text-white")), # Enlace de ejemplo
        ],
        brand=html.Div([
            html.I(className="bi bi-capsule-pill me-2"), # Icono de farmacia
            "Sistema Farmacia Avanzado"
        ]),
        brand_href="#",
        color="primary", # Color primario del tema
        dark=True,
        className="mb-4 shadow-sm" # Margen inferior y sombra suave
    ),

    # Sección de Carga de Archivos
    dbc.Card(
        [
            dbc.CardHeader(html.H5([html.I(className="bi bi-cloud-upload-fill me-2"), "Carga de Archivos"], className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        [
                            dcc.Upload(
                                id="upload-catalog",
                                children=dbc.Button(
                                    ["Subir Catálogo (.xlsx) ", html.I(className="bi bi-file-earmark-excel")],
                                    color="info", outline=True, className="w-100"
                                ),
                                multiple=False,
                                className="mb-2"
                            ),
                            html.Div(id="catalog-status", className="text-muted small")
                        ], md=6
                    ),
                    dbc.Col(
                        [
                            dcc.Upload(
                                id="upload-base",
                                children=dbc.Button(
                                    ["Subir Base Mensual (.xlsx) ", html.I(className="bi bi-file-earmark-excel-fill")], # Icono diferente
                                    color="info", outline=True, className="w-100"
                                ),
                                multiple=False,
                                className="mb-2"
                            ),
                            html.Div(id="base-status", className="text-muted small")
                        ], md=6
                    )
                ])
            ])
        ], className="mb-4"
    ),

    # Sección de Catálogo de Productos y Selección
    dbc.Card(
        [
            dbc.CardHeader(html.H5([html.I(className="bi bi-search me-2"), "Catálogo de Productos"], className="mb-0")),
            dbc.CardBody([
                dag.AgGrid(
                    id="catalog-grid",
                    columnDefs=[],
                    rowData=[],
                    dashGridOptions={"rowSelection": "single", "pagination": True, "paginationPageSize": 5}, # Paginación
                    style={"height": "300px"},
                    className="ag-theme-alpine" # Tema más moderno para la tabla
                ),
                html.Div(id="selected-display", className="mt-2 p-2 border rounded bg-light"), # Mejor feedback visual
                dbc.Label("O elige manualmente un código del catálogo:", html_for="manual-dropdown", className="mt-3"),
                dcc.Dropdown(id="manual-dropdown", placeholder="Buscar o elegir un código...", className="mb-2")
            ])
        ], className="mb-4"
    ),

    # Sección de Cálculo de Precios e Inserción
    dbc.Card(
        [
            dbc.CardHeader(html.H5([html.I(className="bi bi-calculator-fill me-2"), "Cálculo de Precios e Inserción"], className="mb-0")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroup([
                            dbc.InputGroupText("Precio Unit."),
                            dbc.Input(id="precio-unit", type="number", placeholder="Ej: 10.50", min=0, step=0.01)
                        ]), md=4, className="mb-2 mb-md-0"
                    ),
                    dbc.Col(
                        dbc.InputGroup([
                            dbc.InputGroupText("Unidades/Caja"),
                            dbc.Input(id="unidades", type="number", placeholder="Ej: 100", min=1, step=1)
                        ]), md=4, className="mb-2 mb-md-0"
                    ),
                    dbc.Col(
                        html.Div(id="precio-total", className="p-2 bg-light border rounded text-center h-100 d-flex align-items-center justify-content-center", style={"minHeight": "38px"}), # Alineación y altura mínima
                        md=4
                    )
                ], className="mb-3 align-items-center"), # Alineación vertical
                dbc.Button(
                    [html.I(className="bi bi-plus-circle-fill me-2"), "Añadir producto a la Base"],
                    id="add-btn", color="success", className="w-100"
                ),
                html.Div(id="update-msg", className="mt-2 text-center")
            ])
        ], className="mb-4"
    ),

    # Sección de Base Mensual Actualizada
    dbc.Card(
        [
            dbc.CardHeader(html.H5([html.I(className="bi bi-clipboard-data-fill me-2"), "Base Mensual Actualizada"], className="mb-0")),
            dbc.CardBody([
                dag.AgGrid(
                    id="base-grid",
                    columnDefs=[],
                    rowData=[],
                    dashGridOptions={"rowSelection": "single", "pagination": True, "paginationPageSize": 10}, # Paginación
                    style={"height": "400px"}, # Más altura
                    className="ag-theme-alpine" # Tema moderno
                ),
                dbc.Row([
                    dbc.Col(dbc.Button([html.I(className="bi bi-pencil-square me-1"), "Editar Seleccionado"], id="open-edit-modal", color="warning", className="w-100"), md=6, className="mt-1"),
                    dbc.Col(dbc.Button([html.I(className="bi bi-trash-fill me-1"), "Eliminar Seleccionado"], id="open-del-modal", color="danger", className="w-100"), md=6, className="mt-1")
                ], className="mt-3")
            ])
        ], className="mb-4"
    ),

    # Modales (sin cambios estructurales mayores, solo estilo de botones si es necesario)
    dbc.Modal([
        dbc.ModalHeader(html.H5([html.I(className="bi bi-pencil me-2"), "Editar Producto"])),
        dbc.ModalBody([
            dbc.Label("Nuevo Precio Unitario:", html_for="modal-edit-unit"),
            dbc.Input(id="modal-edit-unit", type="number", placeholder="Precio unitario", min=0, step=0.01, className="mb-3"),
            dbc.Label("Nuevas Unidades por Caja:", html_for="modal-edit-units"),
            dbc.Input(id="modal-edit-units", type="number", placeholder="Unidades por caja", min=1, step=1)
        ]),
        dbc.ModalFooter([
            dbc.Button([html.I(className="bi bi-x-circle me-1"), "Cerrar"], id="modal-close", color="secondary", outline=True),
            dbc.Button([html.I(className="bi bi-save-fill me-1"), "Guardar Cambios"], id="modal-save", color="primary")
        ])
    ], id="edit-modal", is_open=False, centered=True),

    dbc.Modal([
        dbc.ModalHeader(html.H5([html.I(className="bi bi-exclamation-triangle-fill me-2"),"Confirmar Eliminación"])),
        dbc.ModalBody("¿Está seguro de que desea eliminar este producto de la base mensual? Esta acción no se puede deshacer."),
        dbc.ModalFooter([
            dbc.Button([html.I(className="bi bi-x-circle me-1"), "Cancelar"], id="modal-cancel", color="secondary", outline=True),
            dbc.Button([html.I(className="bi bi-trash3-fill me-1"), "Eliminar Definitivamente"], id="modal-delete", color="danger")
        ])
    ], id="delete-modal", is_open=False, centered=True),

    # Sección de Descargas
    dbc.Card(
        [
            dbc.CardHeader(html.H5([html.I(className="bi bi-download me-2"), "Descargar Base Modificada"], className="mb-0")),
            dbc.CardBody(
                dbc.Row([
                    dbc.Col(dbc.Button([html.I(className="bi bi-file-earmark-excel-fill me-1"), "Descargar Excel"], id="download-excel", color="primary", outline=True, className="w-100"), md=6, className="mb-2 mb-md-0"),
                    dbc.Col(dbc.Button([html.I(className="bi bi-filetype-csv me-1"), "Descargar CSV"], id="download-csv", color="secondary", outline=True, className="w-100"), md=6)
                ])
            )
        ], className="mb-4"
    ),
    dcc.Download(id="download-excel-data"),
    dcc.Download(id="download-csv-data"),

    # Pie de página (opcional)
    html.Footer(
        dbc.Container(
            html.P("© 2025 Sistema Farmacia - Desarrollado con Dash", className="text-center text-muted small py-3"),
            fluid=True
        ),
        className="mt-5"
    )

], fluid=True, className="bg-light") # Fondo general claro para contraste


# ——— Funciones Helper (sin cambios) ———————————————————————————————————————————
def parse_catalog_xlsx(contents):
    _, content_str = contents.split(",", 1)
    decoded = base64.b64decode(content_str)
    try:
        df = pd.read_excel(io.BytesIO(decoded), header=6)
        return df
    except Exception as e:
        print(f"Error parsing catalog: {e}")
        return pd.DataFrame()


def parse_base_xlsx(contents):
    _, content_str = contents.split(",", 1)
    decoded = base64.b64decode(content_str)
    try:
        df = pd.read_excel(io.BytesIO(decoded))
        # Asegurar que CodEstab existe y es string antes de zfill
        if "CodEstab" not in df.columns:
            df["CodEstab"] = "0000000" # Valor por defecto si no existe
        else:
            df["CodEstab"] = df["CodEstab"].astype(str).str.zfill(7)
        return df
    except Exception as e:
        print(f"Error parsing base: {e}")
        return pd.DataFrame()


# ——— Callbacks (Lógica sin cambios, adaptaciones menores para nuevos stores o feedback) ———

# 1) Carga catálogo
@app.callback(
    Output("store_catalog", "data"),
    Output("catalog-status", "children"),
    Output("catalog-status", "className"), # Para cambiar color del mensaje
    Input("upload-catalog", "contents"),
    prevent_initial_call=True
)
def load_cat(contents):
    if contents:
        df = parse_catalog_xlsx(contents)
        if df.empty:
             return no_update, [html.I(className="bi bi-x-circle-fill me-1"), "Error al leer el archivo de catálogo."], "text-danger mt-2 small"
        if "Cod_Prod" not in df.columns:
            return no_update, [html.I(className="bi bi-exclamation-triangle-fill me-1"), "Falta la columna 'Cod_Prod' en el catálogo."], "text-warning mt-2 small"
        return df.to_dict("records"), [html.I(className="bi bi-check-circle-fill me-1"), "Catálogo cargado exitosamente."], "text-success mt-2 small"
    return None, "", "text-muted mt-2 small"


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
        if df.empty or "Cod_Prod" not in df.columns:
            return [], [], []
        
        # Hacer todas las columnas visibles y con filtro de texto por defecto
        cols = [{"field": c, "filter": "agTextColumnFilter", "floatingFilter": True, "sortable": True} for c in df.columns]
        opts = [{"label": f"{idx} - {str(v)}", "value": v} for idx, v in enumerate(df["Cod_Prod"].unique())] # Añadir un índice para mejor visualización si hay muchos códigos
        return cols, df.to_dict("records"), opts
    return [], [], []


# 3) Gestión base (upload, add, edit, delete)
@app.callback(
    Output("store_base", "data"),
    Output("base-status", "children"),
    Output("base-status", "className"),
    Output("update-msg", "children"),
    Output("update-msg", "className"),
    Input("upload-base", "contents"),
    Input("add-btn", "n_clicks"),
    Input("modal-save", "n_clicks"),
    Input("modal-delete", "n_clicks"),
    State("store_base", "data"),
    State("store_selected_catalog_code", "data"), # Usar el código del store
    State("precio-unit", "value"),
    State("unidades", "value"),
    State("modal-edit-unit", "value"),
    State("modal-edit-units", "value"),
    State("base-grid", "selectedRows"),
    prevent_initial_call=True
)
def manage_base(upload_content, add_clicks, save_clicks, delete_clicks,
                stored_base_data, selected_catalog_code,
                precio_unit, unidades_caja,
                modal_precio_unit, modal_unidades_caja, selected_base_rows):
    df_base = pd.DataFrame(stored_base_data) if stored_base_data else pd.DataFrame()
    msg_base_status, class_base_status = "", "text-muted mt-2 small"
    msg_update, class_update = "", "mt-2 text-center"
    triggered_id = ctx.triggered_id

    cod_estab_default = "0021870" # Definir una sola vez

    if triggered_id == "upload-base" and upload_content:
        df_temp = parse_base_xlsx(upload_content)
        if not df_temp.empty:
            df_base = df_temp
            msg_base_status = [html.I(className="bi bi-check-circle-fill me-1"), "Base mensual cargada exitosamente."]
            class_base_status = "text-success mt-2 small"
        else:
            msg_base_status = [html.I(className="bi bi-x-circle-fill me-1"), "Error al leer el archivo de base mensual."]
            class_base_status = "text-danger mt-2 small"


    elif triggered_id == "add-btn":
        if not selected_catalog_code:
            msg_update = [html.I(className="bi bi-exclamation-circle me-1"), "Por favor, seleccione un código de producto del catálogo."]
            class_update = "mt-2 text-center text-warning"
        elif precio_unit is None or unidades_caja is None:
            msg_update = [html.I(className="bi bi-exclamation-circle me-1"), "Por favor, ingrese precio unitario y unidades por caja."]
            class_update = "mt-2 text-center text-warning"
        elif precio_unit <= 0 or unidades_caja <= 0:
            msg_update = [html.I(className="bi bi-exclamation-circle me-1"), "Precio y unidades deben ser mayores a cero."]
            class_update = "mt-2 text-center text-warning"
        else:
            # Verificar si el código ya existe en la base
            # Asegurarse que 'CodProd' existe en df_base o es un df vacío
            if not df_base.empty and "CodProd" in df_base.columns and selected_catalog_code in df_base["CodProd"].values:
                msg_update = [html.I(className="bi bi-exclamation-triangle-fill me-1"), f"El código {selected_catalog_code} ya existe en la base."]
                class_update = "mt-2 text-center text-warning"
            else:
                new_row = pd.DataFrame([{
                    "CodEstab": cod_estab_default,
                    "CodProd": selected_catalog_code,
                    "Precio 2": precio_unit, # Precio unitario
                    "Precio 1": round(precio_unit * unidades_caja, 2) # Precio por caja
                }])
                df_base = pd.concat([df_base, new_row], ignore_index=True)
                msg_update = [html.I(className="bi bi-check-circle-fill me-1"), f"Producto {selected_catalog_code} añadido exitosamente."]
                class_update = "mt-2 text-center text-success"

    elif triggered_id == "modal-save" and selected_base_rows:
        if modal_precio_unit is not None and modal_unidades_caja is not None and modal_precio_unit > 0 and modal_unidades_caja > 0:
            selected_row_data = selected_base_rows[0]
            cod_prod_to_edit = selected_row_data["CodProd"]
            
            idx = df_base.index[df_base["CodProd"] == cod_prod_to_edit].tolist()
            if idx:
                i = idx[0]
                df_base.at[i, "Precio 2"] = modal_precio_unit
                df_base.at[i, "Precio 1"] = round(modal_precio_unit * modal_unidades_caja, 2)
                df_base.at[i, "CodEstab"] = cod_estab_default # Reafirmar
                msg_update = [html.I(className="bi bi-check-circle-fill me-1"), f"Producto {cod_prod_to_edit} actualizado."]
                class_update = "mt-2 text-center text-success"
            else:
                msg_update = [html.I(className="bi bi-x-circle me-1"), "Error: No se encontró el producto para editar."]
                class_update = "mt-2 text-center text-danger"
        else:
            msg_update = [html.I(className="bi bi-exclamation-circle me-1"), "Datos de edición inválidos. Precio y unidades deben ser mayores a cero."]
            class_update = "mt-2 text-center text-warning"


    elif triggered_id == "modal-delete" and selected_base_rows:
        selected_row_data = selected_base_rows[0]
        cod_prod_to_delete = selected_row_data["CodProd"]
        df_base = df_base[df_base["CodProd"] != cod_prod_to_delete].reset_index(drop=True)
        msg_update = [html.I(className="bi bi-trash-fill me-1"), f"Producto {cod_prod_to_delete} eliminado."]
        class_update = "mt-2 text-center text-info" # Usar info para eliminación

    # Asegurar CodEstab para toda la base, especialmente si se cargó una sin él
    if not df_base.empty:
        if "CodEstab" not in df_base.columns:
             df_base["CodEstab"] = cod_estab_default
        else:
            df_base["CodEstab"] = df_base["CodEstab"].fillna(cod_estab_default).astype(str).str.zfill(7)


    return df_base.to_dict("records"), msg_base_status, class_base_status, msg_update, class_update


# 4) Render base
@app.callback(
    Output("base-grid", "columnDefs"),
    Output("base-grid", "rowData"),
    Input("store_base", "data")
)
def render_base(data):
    if data:
        df = pd.DataFrame(data)
        if df.empty:
            return [], []
        # Hacer todas las columnas visibles y con filtro de texto por defecto
        cols = [{"field": c, "filter": "agTextColumnFilter", "floatingFilter": True, "sortable": True} for c in df.columns]
        return cols, df.to_dict("records")
    return [], []


# 5) Toggle y poblar modal editar
@app.callback(
    Output("edit-modal", "is_open"),
    Output("modal-edit-unit", "value"),
    Output("modal-edit-units", "value"),
    Input("open-edit-modal", "n_clicks"),
    Input("modal-close", "n_clicks"),
    Input("modal-save", "n_clicks"), # Cerrar modal al guardar
    State("edit-modal", "is_open"),
    State("base-grid", "selectedRows"),
    prevent_initial_call=True
)
def toggle_and_populate_edit(open_clicks, close_clicks, save_clicks, is_open, selected_rows):
    triggered_id = ctx.triggered_id

    if triggered_id == "open-edit-modal":
        if selected_rows:
            row = selected_rows[0]
            precio_unitario = row.get("Precio 2")
            precio_total_caja = row.get("Precio 1")
            unidades_en_caja = None
            if precio_unitario and precio_unitario != 0 and precio_total_caja is not None: # Evitar división por cero
                unidades_en_caja = int(round(precio_total_caja / precio_unitario))
            return True, precio_unitario, unidades_en_caja
        return no_update, no_update, no_update # No abrir si no hay selección

    if triggered_id in ["modal-close", "modal-save"]: # Cerrar en ambos casos
        return False, None, None # Limpiar campos al cerrar

    return is_open, no_update, no_update


# 6) Toggle modal eliminar
@app.callback(
    Output("delete-modal", "is_open"),
    Input("open-del-modal", "n_clicks"),
    Input("modal-cancel", "n_clicks"),
    Input("modal-delete", "n_clicks"), # Cerrar modal al eliminar
    State("delete-modal", "is_open"),
    State("base-grid", "selectedRows"), # Solo para verificar si hay algo seleccionado
    prevent_initial_call=True
)
def toggle_delete(open_clicks, cancel_clicks, delete_clicks, is_open, selected_rows):
    triggered_id = ctx.triggered_id
    if triggered_id == "open-del-modal":
        if selected_rows: # Solo abrir si hay algo seleccionado
            return True
        return no_update # No abrir si no hay selección
    if triggered_id in ["modal-cancel", "modal-delete"]:
        return False
    return is_open


# 7) Sincronizar selección catálogo y guardar en dcc.Store
@app.callback(
    Output("manual-dropdown", "value", allow_duplicate=True), # Allow duplicate para evitar error con el siguiente callback
    Output("selected-display", "children"),
    Output("store_selected_catalog_code", "data"), # Guardar el código seleccionado
    Input("catalog-grid", "selectedRows"),
    Input("manual-dropdown", "value"),
    prevent_initial_call=True # Importante
)
def sync_selection(grid_selected_rows, dropdown_value):
    triggered_id = ctx.triggered_id
    code_to_store = no_update
    display_message = no_update
    dropdown_update_value = no_update

    if triggered_id == "catalog-grid" and grid_selected_rows:
        code = grid_selected_rows[0]["Cod_Prod"]
        display_message = [html.I(className="bi bi-check-circle-fill me-1 text-success"), f"Seleccionado del catálogo: ", html.Strong(code)]
        code_to_store = code
        dropdown_update_value = code # Actualizar dropdown
    elif triggered_id == "manual-dropdown" and dropdown_value is not None:
        display_message = [html.I(className="bi bi-check-circle-fill me-1 text-info"), f"Seleccionado manualmente: ", html.Strong(dropdown_value)]
        code_to_store = dropdown_value
        # No necesitamos actualizar el dropdown_update_value aquí porque ya es el valor del dropdown
    else:
        # Si no hay selección o se deselecciona, limpiar
        display_message = [html.I(className="bi bi-info-circle me-1 text-muted"), "Ningún producto seleccionado del catálogo."]
        code_to_store = None
        # dropdown_update_value = None # Podría deseleccionar el dropdown

    return dropdown_update_value, display_message, code_to_store


# 8) Autofill unidades desde el catálogo al seleccionar un producto
@app.callback(
    Output("unidades", "value"),
    Input("store_selected_catalog_code", "data"), # Reaccionar al código guardado
    State("store_catalog", "data"),
    prevent_initial_call=True
)
def autofill_units(selected_code, catalog_data):
    if selected_code and catalog_data:
        df_catalog = pd.DataFrame(catalog_data)
        if df_catalog.empty or "Cod_Prod" not in df_catalog.columns:
            return no_update
        
        product_row = df_catalog[df_catalog["Cod_Prod"] == selected_code]
        if not product_row.empty:
            # Buscar una columna que pueda contener las unidades, como "Fracción", "PRESENTACION", "UNID X EMP" etc.
            # Esto es un ejemplo, debes adaptarlo a los nombres de columna reales de tu catálogo.
            fraccion = product_row.iloc[0].get("Fracción") # Original
            if pd.notnull(fraccion):
                try:
                    return int(fraccion)
                except ValueError:
                    pass # Intentar otras columnas

            # Ejemplo con otra columna (ajusta 'NombreColumnaUnidades' según tu archivo)
            # unidades_col_alternativa = product_row.iloc[0].get("NombreColumnaUnidades")
            # if pd.notnull(unidades_col_alternativa):
            #     try:
            #         return int(unidades_col_alternativa)
            #     except ValueError:
            #         pass
            
            # Si no se encuentra "Fracción" o no es numérico, no actualizar.
            # Podrías añadir lógica para buscar en otras columnas si "Fracción" no existe o no es útil.
            return no_update # O un valor por defecto, ej: 1
    return no_update


# 9) Calcular total
@app.callback(
    Output("precio-total", "children"),
    Input("precio-unit", "value"),
    Input("unidades", "value")
)
def calc_total(precio_u, unidades_c):
    if precio_u is not None and unidades_c is not None:
        if precio_u > 0 and unidades_c > 0:
            total = round(precio_u * unidades_c, 2)
            return [html.I(className="bi bi-receipt-cutoff me-2"), html.Strong(f"Total Caja: S/ {total:.2f}")]
        else:
            return [html.I(className="bi bi-exclamation-triangle me-2 text-warning"), "Valores inválidos"]
    return [html.I(className="bi bi-calculator me-2 text-muted"), "Esperando datos..."]


# 10) Descargar Excel
@app.callback(
    Output("download-excel-data", "data"),
    Input("download-excel", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_excel(n_clicks, base_data):
    if not base_data:
        return no_update
    df = pd.DataFrame(base_data)
    if df.empty:
        return no_update

    # Usar un nombre de archivo temporal que se limpiará automáticamente
    # Opcionalmente, especificar un nombre de archivo para el usuario
    filename = "base_farmacia_actualizada.xlsx"
    
    # Crear un BytesIO buffer para no escribir en disco directamente si no es necesario (para send_bytes)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="BaseActualizada")
        workbook = writer.book
        worksheet = writer.sheets["BaseActualizada"]

        # Formatos
        text_format = workbook.add_format({'num_format': '@'})
        currency_format = workbook.add_format({'num_format': 'S/ #,##0.00'}) # Formato moneda Soles
        general_num_format = workbook.add_format({'num_format': '0'})

        # Aplicar formatos y ajustar anchos de columna
        for idx, col in enumerate(df.columns):
            series = df[col]
            max_len = max((series.astype(str).map(len).max(), len(str(series.name)))) + 2 # +2 para un poco de padding
            
            if col == "CodProd":
                worksheet.set_column(idx, idx, max_len, text_format)
            elif col in ["Precio 1", "Precio 2"]: # Asumiendo que estos son precios
                worksheet.set_column(idx, idx, max_len, currency_format)
            elif pd.api.types.is_numeric_dtype(series.dtype) and not pd.api.types.is_float_dtype(series.dtype) : # Enteros
                 worksheet.set_column(idx, idx, max_len, general_num_format)
            else: # Otros (texto, flotantes generales)
                worksheet.set_column(idx, idx, max_len) # Autofit aproximado

    output.seek(0) # Mover el cursor al inicio del buffer
    return dcc.send_bytes(output.getvalue(), filename)


# 11) Descargar CSV
@app.callback(
    Output("download-csv-data", "data"),
    Input("download-csv", "n_clicks"),
    State("store_base", "data"),
    prevent_initial_call=True
)
def download_csv(n_clicks, base_data):
    if not base_data:
        return no_update
    df = pd.DataFrame(base_data)
    if df.empty:
        return no_update
    
    filename = "base_farmacia_actualizada.csv"
    # Usar send_data_frame para CSV es más directo
    return dcc.send_data_frame(df.to_csv, filename=filename, index=False, encoding='utf-8-sig') # utf-8-sig para mejor compatibilidad con Excel


# --- Arranque de la App ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050)) # Puerto común para Dash
    app.run(debug=True, host="0.0.0.0", port=port) # debug=True para desarrollo
