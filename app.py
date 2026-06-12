import io
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from supabase import create_client


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

    campos = [
        ("Nombre", "nombre_apellido"),
        ("DNI", "dni"),
        ("CUIL", "cuil"),
        ("Fecha nacimiento", "fecha_nacimiento"),
        ("Celular", "celular"),
        ("Cuenta ABC", "cuenta_abc"),
        ("Cuenta IPS", "cuenta_ips"),
        ("Tramite", "tramite_resuelto"),
        ("Tipo jubilacion/reclamo", "tipo_jubilacion"),
    ]

    for etiqueta, clave in campos:
        pdf.drawString(50, y, f"{etiqueta}: {safe(dato.get(clave))}")
        y -= 20

    y -= 20
    pdf.drawString(50, y, "RECLAMO:")
    y -= 20

    for linea in str(safe(dato.get("reclamo"))).split("\n"):
        pdf.drawString(60, y, linea[:100])
        y -= 15

    pdf.save()
    buffer.seek(0)
    return buffer


def limpiar_busqueda():
    st.session_state.resultados = []
    st.session_state.persona = None
    st.session_state.mostrar_formulario_nuevo = False
    st.session_state.mostrar_nuevo_reclamo = False
    st.session_state.modo_edicion = False


def guardar_ficha(datos):
    supabase.table("reclamos").insert(datos).execute()


def posicionar_en_sector(nombre_sector):
    components.html(
        f"""
        <script>
            setTimeout(() => {{
                const elemento = window.parent.document.getElementById("{nombre_sector}");
                if (elemento) {{
                    elemento.scrollIntoView({{
                        behavior: "smooth",
                        block: "start"
                    }});
                }}
            }}, 300);
        </script>
        """,
        height=0,
    )


def ancla_sector(nombre_sector):
    st.markdown(
        f'<div id="{nombre_sector}" style="scroll-margin-top: 90px;"></div>',
        unsafe_allow_html=True,
    )


def formulario_ficha(dato=None, modo="nuevo"):
    es_edicion = modo == "editar"

    area_default = dato.get("area", "Jubilaciones") if dato else "Jubilaciones"
    area_index = 0 if area_default == "Jubilaciones" else 1

    area = st.selectbox("Area", ["Gremiales","Jubilaciones"], index=area_index)

    col1, col2 = st.columns(2)

    with col1:
        nombre = st.text_input(
            "Nombre y Apellido *",
            value=safe(dato.get("nombre_apellido")) if dato else "",
        )
        dni_valor = int(dato.get("dni") or 0) if dato else 0
        dni = st.number_input("DNI *", min_value=0, step=1, value=dni_valor)
        cuil_valor = int(dato.get("cuil") or 0) if dato else 0
        cuil = st.number_input("CUIL", min_value=0, step=1, value=cuil_valor)
        fecha_nac = st.text_input(
            "Fecha de nacimiento (DD/MM/AAAA)",
            value=safe(dato.get("fecha_nacimiento")) if dato else "",
            placeholder="31/12/1980",
        )
        celular = st.text_input(
            "Celular",
            value=safe(dato.get("celular")) if dato else "",
        )

    with col2:
        cuenta_abc = st.text_input(
            "Cuenta ABC",
            value=safe(dato.get("cuenta_abc")) if dato else "",
        )
        cuenta_ips = None
        if area == "Jubilaciones":
            cuenta_ips = st.text_input(
                "Cuenta IPS *",
                value=safe(dato.get("cuenta_ips")) if dato else "",
            )

        tramite_actual = dato.get("tramite_resuelto") if dato else False
        tramite = st.selectbox(
            "Tramite Resuelto?",
            ["SI", "NO"],
            index=0 if tramite_actual else 1,
        )

        quien_toma_reclamo = st.text_input(
            "Quien tomo el reclamo *",
            value=safe(dato.get("quien_toma_reclamo")) if dato else "",
        )

        if area == "Jubilaciones":
            opciones_tipo = [
                "CIERRE DE COMPUTOS",
                "CESE ORDINARIO",
                "CCT",
                "RECONOCIMIENTO DE SERVICIOS",
                "RETRIBUCION ESPECIAL",
            ]
            label_tipo = "Tipo jubilacion *"
        else:
            opciones_tipo = [
                "LICENCIAS",
                "RECLAMO SUELDO",
                "MAD",
                "INGRESO A LA DOCENCIA",
                "OTROS",
            ]
            label_tipo = "Tipo de reclamo gremial *"

        tipo_actual = dato.get("tipo_jubilacion") if dato else opciones_tipo[0]
        if tipo_actual not in opciones_tipo:
            tipo_actual = opciones_tipo[0]

        tipo_tramite = st.selectbox(
            label_tipo,
            opciones_tipo,
            index=opciones_tipo.index(tipo_actual),
        )

    reclamo = st.text_area(
        "Reclamo *",
        value=safe(dato.get("reclamo")) if dato else "",
        height=180,
    )

    col_guardar, col_cancelar = st.columns(2)

    with col_guardar:
        guardar = st.button("Guardar", type="primary", use_container_width=True)

    with col_cancelar:
        cancelar = False
        if es_edicion:
            cancelar = st.button("Cancelar cambios", use_container_width=True)

    if cancelar:
        st.session_state.modo_edicion = False
        st.rerun()

    if guardar:
        errores = []

        if nombre.strip() == "":
            errores.append("Nombre y Apellido")
        if int(dni) <= 0:
            errores.append("DNI")
        if quien_toma_reclamo.strip() == "":
            errores.append("Quien tomo el reclamo")
        if reclamo.strip() == "":
            errores.append("Reclamo")
        if area == "Jubilaciones" and cuenta_ips.strip() == "":
            errores.append("Cuenta IPS")

        if errores:
            st.error(
                "Debe completar los siguientes campos obligatorios:\n\n- "
                + "\n- ".join(errores)
            )
            return

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
            "fecha_carga": dato.get("fecha_carga") if es_edicion else datetime.now().isoformat(),
            "reclamo": reclamo,
        }

        if es_edicion:
            supabase.table("reclamos").update(datos).eq("id", dato["id"]).execute()
            st.session_state.persona = {**dato, **datos}
            st.session_state.modo_edicion = False
            st.success("Ficha guardada correctamente")
            st.rerun()

        existe = supabase.table("reclamos").select("id").eq("dni", int(dni)).execute()
        if existe.data:
            st.error(
                f"El DNI {int(dni)} ya se encuentra cargado. Busque a la persona "
                "y use la ficha existente."
            )
            return

        guardar_ficha(datos)
        st.success("Ficha nueva guardada correctamente")
        limpiar_busqueda()
        st.rerun()


def formulario_nuevo_reclamo(persona):
    st.subheader("Agregar reclamo nuevo")

    nuevo_reclamo = st.text_area("Nuevo reclamo *", height=180)
    nuevo_estado = st.selectbox(
        "Estado del tramite",
        ["SI", "NO"],
        index=0 if persona.get("tramite_resuelto") else 1,
    )
    quien_toma = st.text_input("Quien tomo el reclamo *")

    col_guardar, col_cancelar = st.columns(2)

    with col_guardar:
        guardar = st.button(
            "Guardar reclamo nuevo",
            type="primary",
            use_container_width=True,
        )

    with col_cancelar:
        cancelar = st.button("Cancelar", use_container_width=True)

    if cancelar:
        st.session_state.mostrar_nuevo_reclamo = False
        st.rerun()

    if guardar:
        errores = []
        if nuevo_reclamo.strip() == "":
            errores.append("Nuevo reclamo")
        if quien_toma.strip() == "":
            errores.append("Quien tomo el reclamo")

        if errores:
            st.error(
                "Debe completar los siguientes campos obligatorios:\n\n- "
                + "\n- ".join(errores)
            )
            return

        nuevo = {
            "area": persona.get("area"),
            "nombre_apellido": persona.get("nombre_apellido"),
            "dni": int(persona.get("dni")),
            "cuil": int(persona.get("cuil") or 0),
            "fecha_nacimiento": persona.get("fecha_nacimiento"),
            "celular": persona.get("celular"),
            "cuenta_abc": persona.get("cuenta_abc"),
            "cuenta_ips": persona.get("cuenta_ips"),
            "tramite_resuelto": True if nuevo_estado == "SI" else False,
            "tipo_jubilacion": persona.get("tipo_jubilacion"),
            "quien_toma_reclamo": quien_toma,
            "reclamo": nuevo_reclamo,
            "fecha_carga": datetime.now().isoformat(),
        }

        try:
            supabase.table("reclamos").insert(nuevo).execute()
            st.session_state.mostrar_nuevo_reclamo = False
            st.success("Reclamo nuevo guardado correctamente")
            st.rerun()
        except Exception as e:
            st.error(
                "No se pudo guardar el reclamo nuevo. Si el error dice que el DNI "
                "ya existe, hay que quitar la restriccion UNIQUE de la columna dni "
                "en Supabase para permitir varios reclamos de una misma persona."
            )
            st.exception(e)


def mostrar_ficha(persona):
    tramite = "SI" if persona.get("tramite_resuelto") else "NO"

    st.subheader("Datos de la ficha")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Nombre y Apellido:** {safe(persona.get('nombre_apellido'))}")
        st.write(f"**DNI:** {safe(persona.get('dni'))}")
        st.write(f"**CUIL:** {safe(persona.get('cuil'))}")
        st.write(f"**Fecha de nacimiento:** {safe(persona.get('fecha_nacimiento'))}")
        st.write(f"**Celular:** {safe(persona.get('celular'))}")

    with col2:
        st.write(f"**Area:** {safe(persona.get('area'))}")
        st.write(f"**Cuenta ABC:** {safe(persona.get('cuenta_abc'))}")
        st.write(f"**Cuenta IPS:** {safe(persona.get('cuenta_ips'))}")
        st.write(f"**Tramite resuelto:** {tramite}")
        st.write(f"**Tipo de tramite:** {safe(persona.get('tipo_jubilacion'))}")
        st.write(f"**Quien tomo el reclamo:** {safe(persona.get('quien_toma_reclamo'))}")
        st.write(f"**Fecha de carga:** {safe(persona.get('fecha_carga'))}")

    st.text_area(
        "Ultimo reclamo",
        value=safe(persona.get("reclamo")),
        height=150,
        disabled=True,
    )


def abrir_nueva_ficha():
    st.session_state.pagina = "busqueda"
    st.session_state.mostrar_formulario_nuevo = True
    st.session_state.mostrar_nuevo_reclamo = False
    st.session_state.modo_edicion = False
    st.session_state.persona = None


def abrir_nuevo_reclamo():
    if st.session_state.persona:
        st.session_state.pagina = "historial"
        st.session_state.mostrar_nuevo_reclamo = True
        st.session_state.modo_edicion = False
        return True
    else:
        st.warning("Primero busque y seleccione una persona")
        return False


def abrir_edicion():
    if st.session_state.persona:
        st.session_state.pagina = "busqueda"
        st.session_state.modo_edicion = True
        st.session_state.mostrar_nuevo_reclamo = False
        st.session_state.mostrar_formulario_nuevo = False
        return True
    else:
        st.warning("Primero busque y seleccione una persona")
        return False


def abrir_historial():
    if st.session_state.persona:
        st.session_state.pagina = "historial"
        st.session_state.mostrar_nuevo_reclamo = False
        return True
    else:
        st.warning("Primero busque y seleccione una persona")
        return False


def aplicar_estilo_menu_fijo():
    st.markdown(
        """
        <style>
        .st-key-menu_superior {
            position: fixed;
            top: 3.8rem;
            left: 0;
            right: 0;
            z-index: 9999;
            background: var(--background-color);
            border-bottom: 1px solid rgba(128, 128, 128, 0.35);
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
            padding: 0.55rem max(1rem, calc((100vw - 1120px) / 2)) 0.65rem;
        }

        .st-key-menu_superior [data-testid="stHorizontalBlock"] {
            align-items: center;
        }

        .st-key-menu_superior hr {
            display: none;
        }

        .bloque-espacio-menu {
            height: 78px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_menu_superior():
    with st.container(key="menu_superior"):
        col_agregar, col_modificar, col_ir, col_estado = st.columns([1, 1, 1, 4])

        with col_agregar:
            with st.popover("Agregar", use_container_width=True):
                if st.button("Nueva ficha", use_container_width=True):
                    abrir_nueva_ficha()
                    st.rerun()
                if st.button("Nuevo reclamo", use_container_width=True):
                    if abrir_nuevo_reclamo():
                        st.rerun()

        with col_modificar:
            with st.popover("Modificar", use_container_width=True):
                if st.button("Editar ficha", use_container_width=True):
                    if abrir_edicion():
                        st.rerun()

        with col_ir:
            with st.popover("Ir a...", use_container_width=True):
                if st.button("Ver historial de reclamos", use_container_width=True):
                    if abrir_historial():
                        st.rerun()

        with col_estado:
            persona = st.session_state.get("persona")
            if persona:
                st.caption(
                    f"Persona seleccionada: {persona.get('nombre_apellido', '')} - "
                    f"DNI {persona.get('dni', '')}"
                )
            else:
                st.caption("Sin persona seleccionada")

    st.markdown('<div class="bloque-espacio-menu"></div>', unsafe_allow_html=True)


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Sistema Reclamos", layout="wide")

if "pagina" not in st.session_state:
    st.session_state.pagina = "busqueda"
if "resultados" not in st.session_state:
    st.session_state.resultados = []
if "persona" not in st.session_state:
    st.session_state.persona = None
if "mostrar_formulario_nuevo" not in st.session_state:
    st.session_state.mostrar_formulario_nuevo = False
if "mostrar_nuevo_reclamo" not in st.session_state:
    st.session_state.mostrar_nuevo_reclamo = False
if "modo_edicion" not in st.session_state:
    st.session_state.modo_edicion = False

st.title("Registro de reclamo - Gremial/Jubilaciones")
aplicar_estilo_menu_fijo()
mostrar_menu_superior()

if st.session_state.pagina == "busqueda":
    st.header("Busqueda de persona")

    col_busqueda, col_boton = st.columns([4, 1])

    with col_busqueda:
        texto_busqueda = st.text_input(
            "Buscar por DNI o Apellido",
            placeholder="Ingrese DNI o apellido",
        )

    with col_boton:
        st.write("")
        buscar = st.button("Buscar", type="primary", use_container_width=True)

    col_nuevo, col_limpiar = st.columns([1, 4])
    with col_nuevo:
        st.write("")

    with col_limpiar:
        if st.button("Limpiar busqueda"):
            limpiar_busqueda()
            st.rerun()

    if buscar:
        st.session_state.mostrar_formulario_nuevo = False
        st.session_state.mostrar_nuevo_reclamo = False
        st.session_state.modo_edicion = False
        st.session_state.persona = None

        busqueda = texto_busqueda.strip()
        if busqueda == "":
            st.warning("Ingrese un DNI o apellido para buscar")
        elif busqueda.isdigit():
            response = (
                supabase.table("reclamos")
                .select("*")
                .eq("dni", int(busqueda))
                .order("id", desc=True)
                .execute()
            )
            st.session_state.resultados = response.data or []
        else:
            response = (
                supabase.table("reclamos")
                .select("*")
                .ilike("nombre_apellido", f"%{busqueda}%")
                .order("id", desc=True)
                .execute()
            )
            st.session_state.resultados = response.data or []

    if st.session_state.resultados:
        opciones = [
            f"{r.get('nombre_apellido', '')} - DNI {r.get('dni', '')}"
            for r in st.session_state.resultados
        ]

        seleccion = st.selectbox(
            "Persona encontrada",
            range(len(opciones)),
            format_func=lambda x: opciones[x],
        )

        st.session_state.persona = st.session_state.resultados[seleccion]
        persona = st.session_state.persona

        st.success("Persona encontrada")
        mostrar_ficha(persona)

        if st.session_state.modo_edicion:
            st.divider()
            st.subheader("Editar ficha")
            formulario_ficha(persona, modo="editar")

    elif buscar and texto_busqueda.strip():
        st.warning("No se encontro una persona con esa busqueda")

    if st.session_state.mostrar_formulario_nuevo:
        ancla_sector("sector-nueva-ficha")
        posicionar_en_sector("sector-nueva-ficha")
        st.divider()
        st.subheader("Agregar ficha nueva")
        formulario_ficha(modo="nuevo")

else:
    st.header("Historial de reclamos")

    col_volver, col_espacio = st.columns([1, 2])

    with col_volver:
        if st.button("Volver", type="primary", use_container_width=True):
            st.session_state.pagina = "busqueda"
            st.session_state.mostrar_nuevo_reclamo = False
            st.rerun()

    persona = st.session_state.persona

    if not persona:
        st.info("Primero busque y seleccione una persona")
    else:
        st.write(f"**{persona.get('nombre_apellido', '')}**")
        st.write(f"DNI: {persona.get('dni', '')}")

        if st.session_state.mostrar_nuevo_reclamo:
            ancla_sector("sector-nuevo-reclamo")
            posicionar_en_sector("sector-nuevo-reclamo")
            st.divider()
            formulario_nuevo_reclamo(persona)
            st.divider()

        historial_response = (
            supabase.table("reclamos")
            .select("*")
            .eq("dni", int(persona.get("dni")))
            .order("id", desc=True)
            .execute()
        )

        historial = historial_response.data or []

        if historial:
            reclamo_sel = st.selectbox(
                "Seleccionar reclamo",
                range(len(historial)),
                format_func=lambda x: (
                    f"{historial[x].get('fecha_carga', 'Sin fecha')} - Reclamo {x + 1}"
                ),
            )

            reclamo_actual = historial[reclamo_sel]

            st.text_area(
                "Reclamo seleccionado",
                value=safe(reclamo_actual.get("reclamo")),
                height=220,
                disabled=True,
            )

            pdf_buffer = generar_pdf(reclamo_actual)
            st.download_button(
                label="Descargar PDF del reclamo",
                data=pdf_buffer,
                file_name=f"reclamo_{reclamo_actual.get('dni', '')}_{reclamo_actual.get('id', '')}.pdf",
                mime="application/pdf",
            )
        else:
            st.info("Todavia no hay reclamos cargados en el historial")
