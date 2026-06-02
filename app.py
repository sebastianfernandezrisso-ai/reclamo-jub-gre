import streamlit as st
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
def safe(v):
    return v if v is not None else ""
def generar_pdf(dato):
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "REPORTE DE RECLAMO")

    y -= 40
    pdf.setFont("Helvetica", 10)

    pdf.drawString(50, y, f"Nombre: {safe(dato.get('nombre_apellido'))}")
    y -= 20
    pdf.drawString(50, y, f"DNI: {safe(dato.get('dni'))}")
    y -= 20
    pdf.drawString(50, y, f"CUIL: {safe(dato.get('cuil'))}")
    y -= 20
    pdf.drawString(50, y, f"Fecha nacimiento: {safe(dato.get('fecha_nacimiento'))}")
    y -= 20
    pdf.drawString(50, y, f"Celular: {safe(dato.get('celular'))}")
    y -= 20
    pdf.drawString(50, y, f"Cuenta ABC: {safe(dato.get('cuenta_abc'))}")
    y -= 20
    pdf.drawString(50, y, f"Cuenta IPS: {safe(dato.get('cuenta_ips'))}")
    y -= 20
    pdf.drawString(50, y, f"Trámite: {safe(dato.get('tramite_resuelto'))}")
    y -= 20
    pdf.drawString(50, y, f"Tipo jubilación: {safe(dato.get('tipo_jubilacion'))}")

    y -= 40
    pdf.drawString(50, y, "RECLAMO:")
    y -= 20

    texto = safe(dato.get("reclamo"))

    for linea in str(texto).split("\n"):
        pdf.drawString(60, y, linea[:100])
        y -= 15

    pdf.save()
    buffer.seek(0)
    return buffer
# =========================
# CONFIG
# =========================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Sistema Reclamos", layout="wide")

st.title("Sistema de Reclamos")

tab1, tab2 = st.tabs(["Carga", "Busqueda"])

# =========================
# TAB 1 - CARGA
# =========================

with tab1:

    st.header("Carga de Reclamo")
    mensaje_error = st.empty()
    mensaje_ok = st.empty()
    # =========================
    # TIPO DE AREA
    # =========================

    area = st.selectbox(
        "Área",
        ["Jubilaciones", "Gremiales"]
    )

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input("Nombre y Apellido *")
        dni = st.number_input("DNI *", step=1)
        cuil = st.number_input("CUIL", step=1)

        fecha_nac = st.text_input(
            "Fecha de nacimiento (DD/MM/AAAA)",
            placeholder="31/12/1980"
        )

        celular = st.text_input("Celular")

    with col2:

        cuenta_abc = st.text_input("Cuenta ABC")

        # SOLO JUBILACIONES
        if area == "Jubilaciones":
            cuenta_ips = st.text_input("Cuenta IPS")

        tramite = st.selectbox(
            "¿Tramite Resuelto?",
            ["SI", "NO"]
        )
        quien_toma_reclamo = st.text_input(
            "Quién tomó el reclamo *"
        )
        # =========================
        # TIPOS SEGUN AREA
        # =========================

        if area == "Jubilaciones":

            tipo_tramite = st.selectbox(
                "Tipo jubilación *",
                [
                    "CIERRE DE COMPUTOS",
                    "CESE ORDINARIO",
                    "CCT",
                    "RECONOCIMIENTO DE SERVICIOS",
                    "RETRIBUCION ESPECIAL"
                ]
            )

        else:

            tipo_tramite = st.selectbox(
                "Tipo de reclamo gremial *",
                [
                    "LICENCIAS",
                    "RECLAMO SUELDO",
                    "MAD",
                    "INGRESO A LA DOCENCIA",
                    "OTROS"
                ]
            )

    reclamo = st.text_area("RECLAMO", height=200)


    # =========================
    # GUARDAR
    # =========================

    if st.button("Guardar"):

        # =========================
        # VALIDACIONES
        # =========================

        errores = []

        if nombre.strip() == "":
            errores.append("Apellido y Nombre")

        if int(dni) <= 0:
            errores.append("DNI")

        if quien_toma_reclamo.strip() == "":
            errores.append("Quién tomó el reclamo")

        if reclamo.strip() == "":
            errores.append("Reclamo")

        # SOLO JUBILACIONES
        if area == "Jubilaciones":

            if cuenta_ips.strip() == "":
                errores.append("Cuenta IPS")

        # =========================
        # MOSTRAR ERRORES
        # =========================

        if len(errores) > 0:

            mensaje_error.error(
                "Debe completar los siguientes campos obligatorios:\n\n- "
                + "\n- ".join(errores)
            )

        else:

            datos = {
                "area": area,
                "nombre_apellido": nombre,
                "dni": int(dni),
                "cuil": int(cuil),
                "fecha_nacimiento": fecha_nac,
                "celular": celular,
                "cuenta_abc": cuenta_abc,
                "cuenta_ips": cuenta_ips if area == "Jubilaciones" else None,
                "tramite_resuelto": True if tramite == "SI" else False,
                "tipo_jubilacion": tipo_tramite,
                "quien_toma_reclamo": quien_toma_reclamo,
                "fecha_carga": datetime.now().isoformat(),
                "reclamo": reclamo,
            }
            # =========================
# VALIDAR DNI DUPLICADO
# =========================

            existe = (
    supabase.table("reclamos")
    .select("id")
    .eq("dni", int(dni))
    .execute()
            )

            if existe.data:

                    mensaje_error.error(
                f"El DNI {int(dni)} ya se encuentra cargado"
                )

            else:

                    supabase.table("reclamos").insert(datos).execute()

                    mensaje_ok.success("Reclamo guardado correctamente")
            
# =========================
# TAB 2 - BUSQUEDA
# =========================

if "modo_edicion" not in st.session_state:
    st.session_state.modo_edicion = False

with tab2:

    st.header("Búsqueda de Reclamos")

    buscar_dni = st.text_input("Buscar por DNI")
    buscar_apellido = st.text_input("Buscar por Apellido")

    resultados = []

    # =========================
    # BUSQUEDA
    # =========================
    if buscar_dni:

        response = (
            supabase.table("reclamos")
            .select("*")
            .eq("dni", buscar_dni)
            .order("id", desc=True)
            .execute()
        )

        resultados = response.data or []

    elif buscar_apellido:

        response = (
            supabase.table("reclamos")
            .select("*")
            .ilike("nombre_apellido", f"%{buscar_apellido}%")
            .order("id", desc=True)
            .execute()
        )

        resultados = response.data or []

    # =========================
    # RESULTADOS
    # =========================
    if resultados:

        opciones = [
            f"{r.get('fecha_carga','Sin fecha')} - {r.get('nombre_apellido','')}"
            for r in resultados
        ]

        seleccion = st.selectbox(
            "Historial de reclamos",
            range(len(opciones)),
            format_func=lambda x: opciones[x],
            key="selector_historial"
        )

        dato = resultados[seleccion]

        st.subheader("Datos del Reclamo")

        # =========================
        # BOTONES
        # =========================
        colb1, colb2 = st.columns(2)

        with colb1:
            if st.button("📄 Generar PDF"):
                pdf_buffer = generar_pdf(dato)

                st.download_button(
                    label="Descargar PDF",
                    data=pdf_buffer,
                    file_name=f"reclamo_{dato.get('dni','')}.pdf",
                    mime="application/pdf"
                )

        with colb2:
            if st.button("✏️ Editar"):
                st.session_state.modo_edicion = True

        editable = st.session_state.modo_edicion

               # =========================
        # CAMPOS
        # =========================
        col1, col2 = st.columns(2)

        with col1:

            nombre_edit = st.text_input(
                "Nombre",
                value=dato.get("nombre_apellido", ""),
                disabled=not editable,
                key=f"nombre_edit_{dato['id']}"
            )

            dni_edit = st.number_input(
                "DNI",
                value=int(dato.get("dni") or 0),
                disabled=not editable,
                key=f"dni_edit_{dato['id']}"
            )

            cuil_edit = st.number_input(
                "CUIL",
                value=int(dato.get("cuil") or 0),
                disabled=not editable,
                key=f"cuil_edit_{dato['id']}"
            )

            fecha_edit = st.text_input(
                "Fecha nacimiento",
                value=dato.get("fecha_nacimiento", ""),
                disabled=not editable,
                key=f"fecha_edit_{dato['id']}"
            )

            # SOLO JUBILACIONES
            if dato.get("area") == "Jubilaciones":

                cuenta_ips_edit = st.text_input(
                    "Cuenta IPS",
                    value=dato.get("cuenta_ips", ""),
                    disabled=not editable,
                    key=f"cuenta_ips_edit_{dato['id']}"
                )

        with col2:

            cuenta_abc_edit = st.text_input(
                "Cuenta ABC",
                value=dato.get("cuenta_abc", ""),
                disabled=not editable,
                key=f"cuenta_abc_edit_{dato['id']}"
            )

            celular_edit = st.text_input(
                "Celular",
                value=dato.get("celular", ""),
                disabled=not editable,
                key=f"celular_edit_{dato['id']}"
            )

            tramite_edit = st.selectbox(
                "Trámite Resuelto",
                ["SI", "NO"],
                index=0 if dato.get("tramite_resuelto") else 1,
                disabled=not editable,
                key=f"tramite_edit_{dato['id']}"
            )

            # =========================
            # TIPO SEGUN AREA
            # =========================

            if dato.get("area") == "Jubilaciones":

                opciones_tipo = [
                    "CIERRE DE COMPUTOS",
                    "CESE ORDINARIO",
                    "CCT",
                    "RECONOCIMIENTO DE SERVICIOS",
                    "RETRIBUCION ESPECIAL"
                ]

                label_tipo = "Tipo jubilación"

            else:

                opciones_tipo = [
                    "LICENCIAS",
                    "RECLAMO SUELDO",
                    "MAD",
                    "INGRESO A LA DOCENCIA",
                    "OTROS"
                ]

                label_tipo = "tipo de reclamo gremial"

            tipo_actual = dato.get("tipo_jubilacion")

            if tipo_actual not in opciones_tipo:
                tipo_actual = opciones_tipo[0]

            tipo_edit = st.selectbox(
                label_tipo,
                opciones_tipo,
                index=opciones_tipo.index(tipo_actual),
                disabled=not editable,
                key=f"tipo_edit_{dato['id']}"
            )

        # =========================
        # HISTORIAL
        # =========================
        st.divider()
        st.subheader("📜 Historial de reclamos")

        historial = [
            r for r in resultados
            if r.get("dni") == dato.get("dni")
        ]

        if historial:

            reclamo_sel = st.selectbox(
                "Seleccionar reclamo",
                range(len(historial)),
                format_func=lambda x: f"{historial[x].get('fecha_carga','')} - Reclamo {x+1}",
                key="selector_reclamo"
            )

            reclamo_actual = historial[reclamo_sel]

            st.text_area(
                "Reclamo seleccionado",
                value=reclamo_actual.get("reclamo",""),
                height=200,
                disabled=True
            )

        # =========================
        # NUEVO RECLAMO
        # =========================
        st.divider()
        st.subheader("➕ Agregar nuevo reclamo")

        nuevo_reclamo = st.text_area(
            "Nuevo reclamo",
            height=180,
            key=f"nuevo_reclamo_{dato['id']}"
        )

        nuevo_estado = st.selectbox(
            "Estado del trámite",
            ["SI", "NO"],
            key=f"nuevo_estado_{dato['id']}"
        )

        if st.button("Agregar reclamo nuevo"):

            nuevo = {
                "nombre_apellido": dato.get("nombre_apellido"),
                "dni": int(dato.get("dni")),
                "cuil": int(dato.get("cuil")),
                "fecha_nacimiento": dato.get("fecha_nacimiento"),
                "celular": dato.get("celular"),
                "cuenta_abc": dato.get("cuenta_abc"),
                "cuenta_ips": dato.get("cuenta_ips"),
                "tramite_resuelto": True if nuevo_estado == "SI" else False,
                "tipo_jubilacion": dato.get("tipo_jubilacion"),
                "reclamo": nuevo_reclamo,
                "fecha_carga": datetime.now().isoformat(),
            }

            supabase.table("reclamos").insert(nuevo).execute()

            st.success("Nuevo reclamo agregado correctamente")

    elif buscar_dni or buscar_apellido:
        st.warning("No se encontraron resultados")