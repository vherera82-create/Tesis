import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
import io
import base64
from datetime import datetime
import qrcode

from login import mostrar_login
from login import enviar_correo_con_constancia







# def configurar_prueba_tesis():
    #conn = sqlite3.connect('universidad.db')
    #cursor = conn.cursor()

    # 1. Asegurémonos de que existan dos materias relacionadas
    # Materia Requisito
    #cursor.execute("""
    #    INSERT OR IGNORE INTO materias (nombre, carrera, cupo, dia, hora_inicio, hora_fin, UC, aula, Docente, prelacion)
    #    VALUES ('Algoritmos I', 'Ingeniería de Sistemas', 30, 'Lunes', '08:00', '10:00', 3, 'Aula 1', 'Prof. Garcia', 'Ninguna')
    # """)
    
    # Materia Bloqueada
    # cursor.execute("""
     #   INSERT OR IGNORE INTO materias (nombre, carrera, cupo, dia, hora_inicio, hora_fin, UC, aula, Docente, prelacion)
      #  VALUES ('Algoritmos II', 'Ingeniería de Sistemas', 30, 'Martes', '10:00', '12:00', 4, 'Lab 2', 'Prof. Perez', 'Algoritmos I')
    # """)

    # 2. Verificar que Victor (112) NO la tenga aprobada aún
    # cursor.execute("DELETE FROM historial WHERE cedula_estudiante = '112' AND nombre_materia = 'Algoritmos I'")

   # conn.commit()
  #  conn.close()
 #   print("🚀 Datos de prueba listos. Algoritmos II debería salir con candado.")

# configurar_prueba_tesis()










# def corregir_nombres_carreras():
    #conexion = sqlite3.connect('universidad.db')
    #cursor = conexion.cursor()

    # Opción A: Actualizar las materias para que digan "Ingeniería de Sistemas"
    # (Así le saldrán a Victor Herrera CI: 112)
    #cursor.execute("UPDATE materias SET carrera = 'Ingeniería de Sistemas' WHERE carrera = 'Ingeniería'")
    
    # Opción B: Si tienes alumnos de Arquitectura con nombres largos, haz lo mismo:
    # cursor.execute("UPDATE materias SET carrera = 'Arquitectura Moderna' WHERE carrera = 'Arquitectura'")

   # conexion.commit()
  #  conexion.close()
 #   print("✅ Carreras sincronizadas. Ahora la oferta debe aparecer.")

#corregir_nombres_carreras()



# 1. CONFIGURACIÓN
st.set_page_config(page_title="Sistema Académico Puerto Ordaz", layout="wide")

def ejecutar_query(query, params=(), fetch=False):
    try:
        conn = sqlite3.connect('universidad.db')
        cursor = conn.cursor()
        # Aseguramos soporte de claves foráneas por si acaso
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute(query, params)
        resultado = cursor.fetchall() if fetch else None
        conn.commit()
        conn.close()
        return resultado
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

# Asegurar tablas clave (Actualizada con la restricción FK en 3FN)
ejecutar_query("""
    CREATE TABLE IF NOT EXISTS control_inscripcion (
        cedula_estudiante TEXT PRIMARY KEY,
        finalizado INTEGER DEFAULT 0,
        fecha_finalizacion DATETIME,
        FOREIGN KEY (cedula_estudiante) REFERENCES estudiantes(cedula)
    )
""")

# ---------------------------------------------------------
# TU FUNCIÓN GENERAR_PDF_HORARIO (ADAPTADA A 3FN)
# ---------------------------------------------------------
def generar_pdf_horario(nombre_completo, cedula, carrera, materias_inscritas):
    """
    Estructura esperada en cada tupla de 'materias_inscritas' bajo el nuevo modelo:
    row[0] -> id_seccion
    row[1] -> nombre_materia
    row[2] -> dia
    row[3] -> rango_horario (Ej: "08:00 - 10:00") -> Construido desde SQL
    row[4] -> id_materia
    row[5] -> UC
    row[6] -> aula
    row[7] -> docente
    """
    pdf = FPDF()
    pdf.add_page()
    
    fecha_hoy = datetime.now().strftime('%d/%m/%Y')
    datos_qr = f"VERIFICACIÓN ACADÉMICA\nEstudiante: {nombre_completo}\nCI: {cedula}\nCarrera: {carrera}\nFecha: {fecha_hoy}\nEstatus: INSCRITO"
    
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(datos_qr)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    img_buffer = io.BytesIO()
    img_qr.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    
    pdf.set_fill_color(31, 39, 245)
    pdf.rect(0, 0, 210, 5, 'F') 
    pdf.image(img_buffer, x=170, y=10, w=30, h=30)
    
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_xy(10, 15)
    pdf.cell(0, 8, "SISTEMA DE GESTIÓN ACADÉMICA", ln=True, align='L')
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(0, 5, "UNIVERSIDAD - SEDE PUERTO ORDAZ", ln=True, align='L')
    
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(155, 10, "  COMPROBANTE DE INSCRIPCIÓN ACADÉMICA", 0, ln=True, fill=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.cell(95, 6, f"ESTUDIANTE:  {str(nombre_completo).upper()}", 0)
    pdf.cell(60, 6, f"CÉDULA: {cedula}", 0, ln=True)
    pdf.cell(95, 6, f"CARRERA: {str(carrera).upper()}", 0)
    pdf.cell(60, 6, f"PERÍODO: 2026-I", 0, ln=True)
    pdf.cell(95, 6, f"FECHA DE EMISIÓN: {fecha_hoy}", 0, ln=True)

    total_uc = sum(int(row[5]) for row in materias_inscritas)
    porcentaje = min(total_uc / 21, 1.0)
    pdf.ln(3)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.cell(50, 5, f"CARGA ACADÉMICA: {total_uc} / 21 UC", ln=True)
    pdf.set_fill_color(230, 230, 230); pdf.rect(10, pdf.get_y(), 100, 3, 'F')
    pdf.set_fill_color(31, 39, 245); pdf.rect(10, pdf.get_y(), 100 * porcentaje, 3, 'F')
    pdf.ln(8)
    
    # Encabezados de tabla originales
    pdf.set_text_color(255, 255, 255); pdf.set_font("Helvetica", 'B', 8); pdf.set_fill_color(200, 200, 200)
    pdf.cell(55, 7, " ASIGNATURA", 1, 0, 'L', fill=True)
    pdf.cell(45, 7, " DOCENTE", 1, 0, 'L', fill=True)
    pdf.cell(10, 7, " UC", 1, 0, 'C', fill=True)
    pdf.cell(20, 7, " DÍA", 1, 0, 'C', fill=True)
    pdf.cell(35, 7, " HORARIO", 1, 0, 'C', fill=True)
    pdf.cell(25, 7, " AULA", 1, 1, 'C', fill=True)
    
    pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", '', 7)
    for i, row in enumerate(materias_inscritas):
        m_nom, m_dia, m_hora, m_uc, m_aula, m_doc = row[1], row[2], row[3], row[5], row[6], row[7]
        bg = (245, 245, 245) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*bg)
        pdf.cell(55, 5, f" {m_nom[:30]}", 1, 0, 'L', fill=True)
        pdf.cell(45, 5, f" {m_doc[:25]}", 1, 0, 'L', fill=True)
        pdf.cell(10, 5, f" {m_uc}", 1, 0, 'C', fill=True)
        pdf.cell(20, 5, f" {m_dia[:12]}", 1, 0, 'C', fill=True)
        pdf.cell(35, 5, f" {m_hora[:22]}", 1, 0, 'C', fill=True)
        pdf.cell(25, 5, f" {m_aula[:10]}", 1, 1, 'C', fill=True)

    pdf.ln(2)
    pdf.set_font("Helvetica", 'B', 8); pdf.set_fill_color(240, 240, 240)
    pdf.cell(170, 6, "TOTAL UNIDADES DE CRÉDITO:", 1, 0, 'R', fill=True)
    pdf.cell(20, 6, f"{total_uc}", 1, 1, 'C', fill=True)

    if pdf.get_y() > 110: pdf.set_y(110)
    
    # Forzamos que el calendario empiece ordenado
    if pdf.get_y() > 140:
        pdf.add_page() 
    else:
        pdf.set_y(120) 

    # --- Proyección de horario semanal ---
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(0, 8, "PROYECCIÓN DE HORARIO SEMANAL", 0, 1, 'C')
    pdf.ln(2)

    # Configuración de celdas
    ancho_hora = 20
    ancho_dia = 34  
    alto_celda = 6

    # Encabezados
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Helvetica", 'B', 7)
    pdf.cell(ancho_hora, alto_celda, "HORA", 1, 0, 'C', True)
    for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]:
        pdf.cell(ancho_dia, alto_celda, dia.upper(), 1, 0, 'C', True)
    pdf.ln()

    # Bloques de tiempo
    bloques_pdf = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

    pdf.set_font("Helvetica", '', 6)
    for bloque in bloques_pdf:
        pdf.set_fill_color(255, 255, 255) 
        pdf.cell(ancho_hora, alto_celda, bloque, 1, 0, 'C')
        
        h_bloque_int = int(bloque.split(":")[0])
        
        for dia in ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]:
            materia_nombre = ""
            for m in materias_inscritas:
                try:
                    # Explicación: m[3] tiene el formato "HH:MM - HH:MM" gracias al JOIN
                    h_i, h_f = m[3].split(" - ")
                    h_ini_int = int(h_i.split(":")[0])
                    h_fin_int = int(h_f.split(":")[0])
                    
                    if m[2] == dia and h_ini_int <= h_bloque_int < h_fin_int:
                        materia_nombre = m[1][:22] 
                except:
                    continue
            
            if materia_nombre:
                pdf.set_fill_color(230, 240, 255) 
                pdf.cell(ancho_dia, alto_celda, materia_nombre, 1, 0, 'C', True)
            else:
                pdf.cell(ancho_dia, alto_celda, "", 1, 0, 'C')
        pdf.ln()
        
    y_f = 270
    pdf.line(20, y_f, 80, y_f); pdf.set_xy(20, y_f+2); pdf.cell(60, 5, "Firma del Alumno", 0, 0, 'C')
    pdf.line(130, y_f, 185, y_f); pdf.set_xy(125, y_f+1); pdf.cell(60, 5, "Sello y Firma Autorizada", 0, 0, 'C')

    return bytes(pdf.output())










# ---------------------------------------------------------
# INTERFAZ PRINCIPAL
# ---------------------------------------------------------
import streamlit as st
import pandas as pd
import base64

st.title("🎓 Control de Inscripciones")
tab_alumno, tab_admin = st.tabs(["👤 Portal Alumno", "⚙️ Administración"])

with tab_alumno:
    if 'logueado' not in st.session_state: 
        st.session_state.logueado = False
    
    if not st.session_state.logueado:
        mostrar_login(ejecutar_query)
        

    else:
        ced, nom, ape, carr, *_ = st.session_state.user
        
        # --- ENCABEZADO DE SESIÓN CON BOTÓN DE SALIDA ---
        col_user, col_logout = st.columns([4, 1])
        with col_user:
            st.info(f"📍 **Sesión:** {nom} {ape} | **Carrera:** {carr}")
        with col_logout:
            if st.button("🚪 Salir", use_container_width=True):
                st.session_state.logueado = False
                st.session_state.user = None
                st.rerun()


        # =====================================================================
# SECCIÓN DE SEGURIDAD EN LA BARRA LATERAL (Cambiar Contraseña)
# =====================================================================
        with st.sidebar:
            st.markdown("---")
            st.subheader("🔐 Seguridad de la Cuenta")
            
            # Usamos un expansor para que no ocupe espacio visual a menos que el usuario lo abra
            with st.expander("Cambiar mi contraseña"):
                with st.form("form_cambiar_pass", clear_on_submit=True):
                    pass_actual = st.text_input("Contraseña Actual:", type="password")
                    pass_nueva = st.text_input("Nueva Contraseña:", type="password")
                    pass_nueva_conf = st.text_input("Confirmar Nueva Contraseña:", type="password")
                    
                    btn_cambiar = st.form_submit_button("Actualizar Contraseña", use_container_width=True)
                    
                    if btn_cambiar:
                        # 1. Validar que no haya campos vacíos
                        if not pass_actual or not pass_nueva or not pass_nueva_conf:
                            st.warning("Por favor, rellene todos los campos.")
                        
                        # 2. Verificar que la contraseña actual sea la correcta
                        # st.session_state.user[4] o el índice donde guardas la contraseña actualmente en tu tupla
                        # Como alternativa segura, consultamos directo a la base de datos con la cédula actual (ced)
                        else:
                            user_db = ejecutar_query("SELECT contrasena FROM estudiantes WHERE cedula = ?", (ced,), fetch=True)
                            contrasena_correcta_db = user_db[0][0] if user_db else None
                            
                            if pass_actual != contrasena_correcta_db:
                                st.error("La contraseña actual es incorrecta.")
                            
                            # 3. Verificar que la nueva contraseña coincida con la confirmación
                            elif pass_nueva != pass_nueva_conf:
                                st.error("La nueva contraseña y su confirmación no coinciden.")
                            
                            # 4. Validar un mínimo de seguridad (por ejemplo, longitud)
                            elif len(pass_nueva) < 6:
                                st.warning("La nueva contraseña debe tener al menos 6 caracteres.")
                            
                            # 5. Todo correcto -> Guardar en la Base de Datos
                            else:
                                ejecutar_query("UPDATE estudiantes SET contrasena = ? WHERE cedula = ?", (pass_nueva, ced))
                                st.success("🔒 ¡Contraseña actualizada con éxito!")
                                
                                # Opcional: Actualizamos la contraseña en el estado de la sesión si la manejas ahí
                                # Aunque al consultar directo a la BD en el paso 2, el sistema ya se mantiene sincronizado.
        
        # 1. Verificar si ya Finalizó
        res_ins = ejecutar_query("SELECT finalizado FROM control_inscripcion WHERE cedula_estudiante = ?", (ced,), fetch=True)
        finalizado = res_ins[0][0] if res_ins else 0

        # 2. Verificar Pago
        pago = ejecutar_query("SELECT estado FROM pagos WHERE cedula_estudiante = ?", (ced,), fetch=True)

        if not pago:
            st.warning("⚠️ Inscripción bloqueada. Adjunte su pago.")
            archivo = st.file_uploader("Subir Pago", type=['png', 'jpg', 'jpeg'])
            if st.button("Enviar Pago", use_container_width=True) and archivo:
                ejecutar_query("INSERT INTO pagos (cedula_estudiante, comprobante, estado) VALUES (?, ?, 'Pendiente')", (ced, archivo.read()))
                st.rerun()
        elif pago[0][0] == 'Pendiente':
            st.info("⏳ Pago en revisión.")
        else:
            # Traer historial
            inscritas = ejecutar_query("""
                SELECT 
                    i.id, 
                    m.nombre,      -- <- Añadimos el nombre aquí para la interfaz
                    s.dia, 
                    s.hora_inicio || ' - ' || s.hora_fin, 
                    'Cursando' AS estado, 
                    m.UC, 
                    s.aula, 
                    s.docente,
                    s.id AS id_seccion  -- <- Añadimos el ID de sección para devolver el cupo
                FROM inscripciones i
                JOIN secciones s ON i.id_seccion = s.id
                JOIN materias m ON s.id_materia = m.id
                WHERE i.cedula_estudiante = ?
            """, (ced,), fetch=True)

            if finalizado == 1:
                st.success("✅ Inscripción Cerrada.")
                if inscritas:
                    try:
                        pdf_bytes = generar_pdf_horario(f"{nom} {ape}", ced, carr, inscritas)
                        
                        # --- SE MANTIENE TU CONSTRUCCIÓN ORIGINAL DE BOTÓN HTML (BASE64) ---
                        b64 = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="Horario_{ced}.pdf" style="text-decoration: none;"><button style="width: 100%; background-color: #1B5FF2; color: white; padding: 10px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">📥 DESCARGAR COMPROBANTE (PDF)</button></a>'
                        st.markdown(href, unsafe_allow_html=True)

                        st.subheader("Tu Horario Inscrito")
                        for m in inscritas:
                            st.write(f"🔹 **{m[1]}** - {m[2]} ({m[3]})")
                            
                    except Exception as e:
                        st.error(f"Error al visualizar el comprobante: {e}")

            else:
                col1, col2 = st.columns(2)
        
                # Total de UC una sola vez
                total_actual_uc = sum(int(r[5]) for r in inscritas) if inscritas else 0

                # ---------------------------------------------------------
                # COLUMNA 1: MI SELECCIÓN
                # ---------------------------------------------------------
                with col1:
                    st.markdown("### 📅 Proyección de Horario Semanal")

                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
                    bloques = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"]

                    tabla_horario = pd.DataFrame("", index=bloques, columns=dias_semana)

                    if inscritas:
                        # Añadimos 'id_seccion' al final para recibir el noveno dato de la consulta SQL
                        for h_id, m_nom, m_dia, m_horario, _, m_uc, _, _, id_seccion in inscritas:          
                            try:
                                h_inicio, h_fin = m_horario.split(" - ")
                                h_ini_int = int(h_inicio.split(":")[0])
                                h_fin_int = int(h_fin.split(":")[0])
                                
                                for b in bloques:
                                    hora_bloque = int(b.split(":")[0])
                                    if m_dia in dias_semana and h_ini_int <= hora_bloque < h_fin_int:
                                        tabla_horario.at[b, m_dia] = m_nom
                            except:
                                continue

                        # Función para aplicar color en las celdas con datos
                        def estilo_celdas(val):
                            if val != "":
                                return 'background-color: #1B5FF2; color: white; font-weight: bold; border: 1px solid white; text-align: center; font-size: 0.8rem;'
                            return ''
                        

                        try:
                          st.table(tabla_horario.style.map(estilo_celdas))

                
                        except: 
                         st.table(tabla_horario.style.applymap(estilo_celdas))

                        # Se usa .map() en vez de applymap para compatibilidad
                        
                    else:
                        st.info("El calendario se actualizará al inscribir materias.") 

                    st.subheader("📝 Mi Selección")
                    
                    # --- BARRA DE PROGRESO PERSONALIZADA ---
                    if total_actual_uc == 21:
                        color_barra = "#0BD932" 
                    elif total_actual_uc >= 12:
                        color_barra = "#0019FC" 
                    else:
                        color_barra = "#FC0000" 

                    st.markdown(f"""
                        <div style="width: 100%; background-color: #f0f2f6; border-radius: 10px; border: 1px solid #dcdcdc;">
                            <div style="width: {min((total_actual_uc/21)*100, 100)}%; background-color: {color_barra}; 
                            height: 25px; border-radius: 10px; text-align: center; color: white; 
                            font-weight: bold; line-height: 25px; transition: width 0.5s;">
                                {total_actual_uc} / 21 UC
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("") 

                    # Modificamos las variables para capturar el nombre y el id_seccion al final
                    for h_id, m_nom, m_dia, m_horario, _, m_uc, _, _, id_seccion in inscritas:
                        with st.container(border=True):
                            st.write(f"✅ **{m_nom}** ({m_uc} UC)")
                            
                            if st.button(f"Retirar {m_nom}", key=f"ret_{h_id}_{ced}"):
                                # 1. Devolvemos el cupo a la SECCIÓN correspondiente, no a la materia
                                ejecutar_query("UPDATE secciones SET cupo = cupo + 1 WHERE id = ?", (id_seccion,))
                                
                                # 2. Eliminamos el registro de la tabla INSCRIPCIONES, no del historial
                                ejecutar_query("DELETE FROM inscripciones WHERE id = ?", (h_id,))
                                
                                st.success(f"Materia {m_nom} retirada con éxito.")
                                st.rerun()

                    st.divider()

                    # 3. SECCIÓN DE CIERRE 
                    if inscritas:
                        if st.button("🚀 FINALIZAR INSCRIPCIÓN", type="primary", use_container_width=True, key="btn_finalizar_main"):
                            ejecutar_query("""
                                INSERT OR REPLACE INTO control_inscripcion (cedula_estudiante, finalizado, fecha_finalizacion) 
                                VALUES (?, 1, CURRENT_TIMESTAMP)
                            """, (ced,))

                            correo_alumno = st.session_state.user[5] 
                            nombre_alumno = f"{nom} {ape}"
                            st.info("Generando constancia y enviando al correo...")
                            pdf_bytes = generar_pdf_horario(f"{nom} {ape}", ced, carr, inscritas)

                            # 4. Enviar el correo con el archivo adjunto
                            if enviar_correo_con_constancia(correo_alumno, nombre_alumno, pdf_bytes):
                                st.success("¡Inscripción finalizada con éxito y constancia enviada al correo!")
                            else:
                                st.warning("⚠️ Inscripción guardada, pero no se pudo enviar el correo de respaldo.")



                            st.balloons()
                            st.success("¡Inscripción finalizada con éxito!")




                            st.rerun() 
                    else:
                        st.info("Selecciona materias de la oferta para comenzar.")

                # ---------------------------------------------------------
                # COLUMNA 2: OFERTA 
                # ---------------------------------------------------------
                with col2:
                    st.subheader(f"📚 Oferta para {carr}")
                    
                    oferta = ejecutar_query("""
                    SELECT 
                        m.id AS id_materia, 
                        m.nombre, 
                        s.cupo, 
                        s.dia, 
                        s.hora_inicio, 
                        s.hora_fin, 
                        m.UC, 
                        s.aula, 
                        s.docente, 
                        m.prelacion_id, 
                        m.semestre,
                        s.id AS id_seccion
                    FROM materias m
                    JOIN secciones s ON m.id = s.id_materia
                    WHERE m.id_carrera = ? 
                    -- 👇 REGLA CLAVE: Oculta las materias que el alumno ya tiene en su selección actual
                    AND m.id NOT IN (
                        SELECT sec.id_materia 
                        FROM inscripciones ins
                        JOIN secciones sec ON ins.id_seccion = sec.id
                        WHERE ins.cedula_estudiante = ?
                    )
                    ORDER BY m.semestre ASC
                """, (carr, ced), fetch=True) # 👈 Asegúrate de pasar tanto 'carr' como 'ced' en los parámetros de la tupla
                                    
                    bloqueadas = [r[0] for r in inscritas] 

                    if not oferta:
                        st.warning("No hay materias disponibles para tu carrera.")
                    else:
                        oferta_limpia = []
                        nombres_vistos = set()

                        for m in oferta:
                            if m[1] not in nombres_vistos: 
                                oferta_limpia.append(m)
                                nombres_vistos.add(m[1])

                        for m_id, m_nom, m_cup, m_dia, m_h_i, m_h_f, m_uc, m_aul, m_doc, m_pre, m_sem, id_seccion in oferta:
                            
                            if m_id not in bloqueadas: 
                                es_aprobada = False
                                if m_pre == "Ninguna" or m_pre is None:
                                    es_aprobada = True
                                else:
                                    check = ejecutar_query("""
                                        SELECT COUNT(*) FROM historial 
                                        WHERE cedula_estudiante = ? AND (nombre_materia = ? OR materia_id = ?) AND estado = 'Aprobada'
                                    """, (ced, m_pre, m_pre), fetch=True)
                                    if check and check[0][0] > 0:
                                        es_aprobada = True

                                icono = "📖" if es_aprobada else "🔒 BLOQUEADA"
                                
                                # Valida que dentro del expander uses ÚNICAMENTE las variables locales que declaraste arriba en el for
                                with st.expander(f"📚 Semestre {m_sem} - {m_nom} (Cupos: {m_cup})"):
                                    if not es_aprobada:
                                        st.error(f"🚫 Debes aprobar primero: **{m_pre}**")
                                    else:
                                        st.write(f"👨‍🏫 **Docente:** {m_doc} | 🏫 **Aula:** {m_aul}")
                                        st.write(f"⏰ **Horario:** {m_dia} ({m_h_i} - {m_h_f}) | 💎 **Créditos:** {m_uc} UC")

                                        # Muy importante: la clave (key) debe usar id_seccion para no duplicarse entre filas
                                        if st.button(f"Inscribir {m_nom}", key=f"btn_ins_{id_seccion}_{ced}", disabled=(m_cup <= 0)):
                                            tiene_problema = False
                                            materia_conflicto = ""                  

                                            # Validación de Choque Horario
                                            for insc_info in inscritas:
                                                i_nom = insc_info[1]
                                                i_dia = insc_info[2]
                                                i_horario = insc_info[3]
                                                
                                                if i_horario and " - " in i_horario:
                                                    h_ini_i, h_fin_i = i_horario.split(" - ")
                                                    if m_dia == i_dia:
                                                        if (m_h_i < h_fin_i) and (m_h_f > h_ini_i):
                                                            tiene_problema = True
                                                            materia_conflicto = i_nom
                                                            break
                                            
                                            if tiene_problema:
                                                st.error(f"❌ Choque de horario con: **{materia_conflicto}**")

                                            # Validación de Límite UC
                                            elif total_actual_uc + m_uc > 21:
                                                st.error("❌ Superas el límite de 21 UC.")
                                                tiene_problema = True

                                            # Guardar si todo está OK (Uso estricto de la 3FN)
                                            if not tiene_problema:
                                                # 1. Restamos el cupo directamente en la SECCIÓN seleccionada, no en materias
                                                ejecutar_query("UPDATE secciones SET cupo = cupo - 1 WHERE id = ?", (id_seccion,))
                                                
                                                # 2. Insertamos el registro en INSCRIPCIONES vinculando al alumno con la sección
                                                ejecutar_query("""
                                                    INSERT INTO inscripciones (cedula_estudiante, id_seccion) 
                                                    VALUES (?, ?)
                                                """, (ced, id_seccion))
                                                
                                                st.success(f"✅ **{m_nom}** inscrita exitosamente.")
                                                st.rerun()











#Apartado Admind
with tab_admin:
    st.header("⚙️ Gestión")
    st.subheader("💳 Validación de Pagos por Carrera")

    # 1. Filtro de búsqueda para el Admin
    carreras_disponibles = ["Todas", "Ingeniería de Sistemas", "Ingeniería Electrónica", "Ingeniería Eléctrica", "Ingeniería Civil", "Arquitectura"]
    filtro_carrera = st.selectbox("Filtrar pagos por:", carreras_disponibles)

    # 2. Construcción de la consulta según el filtro
    query_pagos = """
        SELECT p.id, p.cedula_estudiante, e.nombre || ' ' || e.apellido, p.comprobante, e.id_carrera
        FROM pagos p
        JOIN estudiantes e ON p.cedula_estudiante = e.cedula
        WHERE p.estado = 'Pendiente'
    """
    
    params = []
    if filtro_carrera != "Todas":
        query_pagos += " AND e.id_carrera = ?"
        params.append(filtro_carrera)

    pagos_pendientes = ejecutar_query(query_pagos, params, fetch=True)

    if pagos_pendientes:
        st.write(f"Mostrando **{len(pagos_pendientes)}** pagos pendientes.")
        for id_pago, ci_est, nombre_est, foto_blob, carr_est in pagos_pendientes:
            with st.expander(f"📌 {nombre_est} - {carr_est} (CI: {ci_est})"):
                col_img, col_btn = st.columns([2, 1])
                
                with col_img:
                    # Visualización del capture (Blob)
                    st.image(foto_blob, caption=f"Comprobante de {nombre_est}", use_container_width=True)
                
                with col_btn:
                    st.info(f"Carrera: {carr_est}")
                    if st.button("✅ Aprobar Pago", key=f"app_{id_pago}"):
                        ejecutar_query("UPDATE pagos SET estado = 'Aprobado' WHERE id = ?", (id_pago,))
                        st.success("¡Pago Validado!")
                        st.rerun()
                    
                    if st.button("❌ Rechazar", key=f"rej_{id_pago}"):
                        ejecutar_query("DELETE FROM pagos WHERE id = ?", (id_pago,))
                        st.warning("Pago eliminado.")
                        st.rerun()
    else:
        st.info(f"No hay pagos pendientes para: {filtro_carrera}")

    st.divider()
    st.subheader("📊 Métricas Generales de Inscripción")

    # --- SE MANTIENE id_materia EN EL COUNT COMO ME INDICAS ---
    admin_data = ejecutar_query("""
        SELECT e.cedula, e.nombre || ' ' || e.apellido, e.id_carrera, COUNT(h.id_materia), IFNULL(c.finalizado, 0)
        FROM estudiantes e 
        LEFT JOIN historial h ON e.cedula = h.cedula_estudiante AND h.estado = 'Cursando'
        LEFT JOIN control_inscripcion c ON e.cedula = c.cedula_estudiante
        GROUP BY e.cedula
    """, fetch=True)
    
    if admin_data:
        df = pd.DataFrame(admin_data, columns=['CI', 'Nombre Completo', 'Carrera', 'Materias Inscritas', 'Finalizado'])
        




        # POR SI ACASO: Si llega a colarse un NULL (None) en Python, esto lo convierte en 0 de inmediato
        df['Finalizado'] = df['Finalizado'].fillna(0).astype(int)
        df['Materias Inscritas'] = df['Materias Inscritas'].fillna(0).astype(int)


        # Mapeo visual usando .map() para evitar advertencias de depreciación en Pandas
        df['Estado Proceso'] = df['Finalizado'].map({1: "🟢 Finalizado", 0: "⏳ En Selección"})
        
        c1, c2 = st.columns(2)
        c1.metric("Total Alumnos", len(df))
        c2.metric("Inscripciones Listas", len(df[df['Finalizado'] == 1]))
        
        # Mostramos la tabla limpia
        st.dataframe(df[['CI', 'Nombre Completo', 'Carrera', 'Materias Inscritas', 'Estado Proceso']], use_container_width=True)

    st.divider()
    st.subheader("🗑️ Zona de Peligro")
    with st.expander("Opciones de Reseteo de Datos"):
        st.warning("🚨 Estas acciones son críticas y borrarán registros de forma permanente.")
        
        if st.button("Resetear Cupos e Inscripciones", type="secondary"):
            ejecutar_query("DELETE FROM historial WHERE estado = 'Cursando'")
            ejecutar_query("DELETE FROM control_inscripcion")
            ejecutar_query("UPDATE secciones SET cupo = 30")
            
            st.success("Sistema reseteado: Cupos restaurados y procesos de inscripción liberados.")
            st.rerun()

        if st.button("Limpiar Comprobantes de Pago", type="secondary"):
            ejecutar_query("DELETE FROM pagos")
            st.success("Todos los registros de pagos han sido eliminados.")
            st.rerun()