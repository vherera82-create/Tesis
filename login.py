import streamlit as st
import smtplib
import random
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from email.mime.base import MIMEBase
from email import encoders

# =====================================================================
# CONFIGURACIÓN DE CORREO GMAIL (Ajusta esto con tus datos reales)
# =====================================================================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
CORREO_EMISOR = "vherera82@gmail.com"          # <-- Tu Gmail de pruebas
CORREO_PASSWORD = "aqip vydt bdnv tdcr"       # <-- Tu contraseña de aplicación de 16 letras




def enviar_correo_con_constancia(correo_destino, nombre_alumno, pdf_bytes, nombre_archivo="Constancia_Inscripcion.pdf"):
    """Envía un correo electrónico al estudiante adjuntando su constancia en PDF."""
    try:
        msg = MIMEMultipart()
        msg['From'] = CORREO_EMISOR
        msg['To'] = correo_destino
        msg['Subject'] = "📄 Tu Constancia de Inscripción Oficial"
        
        # Cuerpo del correo en HTML
        cuerpo_html = f"""
        <html>
            <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
                <h2>¡Felicidades, {nombre_alumno}!</h2>
                <p>Tu proceso de inscripción ha sido finalizado con éxito en el sistema.</p>
                <p>Adjunto a este correo encontrarás tu <b>Constancia de Inscripción Oficial</b> con el resumen de tus materias y horarios para este período académico.</p>
                <br>
                <p style="font-size: 12px; color: #777;">Este es un correo automático, por favor no lo respondas.</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(cuerpo_html, 'html'))
        
        # Procesar el archivo adjunto (PDF)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{nombre_archivo}"')
        msg.attach(part)
        
        # Conexión y envío seguro a través de Gmail
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(CORREO_EMISOR, CORREO_PASSWORD)
        server.sendmail(CORREO_EMISOR, correo_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error al enviar la constancia por correo: {e}")
        return False










def enviar_correo(correo_destino, asunto, cuerpo_mensaje):
    """Función unificada para conectarse a Gmail y enviar correos en formato HTML."""
    try:
        msg = MIMEMultipart()
        msg['From'] = CORREO_EMISOR
        msg['To'] = correo_destino
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo_mensaje, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(CORREO_EMISOR, CORREO_PASSWORD)
        server.sendmail(CORREO_EMISOR, correo_destino, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"Error de conexión de correo: {e}")
        return False

# =====================================================================
# INTERFAZ PRINCIPAL DE LOGIN Y REGISTRO (Unificada)
# =====================================================================
def mostrar_login(ejecutar_query):
    # Usamos pestañas de Streamlit para separar de forma limpia Iniciar Sesión de Registrarse
    tab_login, tab_registro = st.tabs(["🔑 Iniciar Sesión", "📝 Registrar Nuevo Usuario"])
    
    # -----------------------------------------------------------------
    # PESTAÑA 1: INICIAR SESIÓN (Validación con Cédula y Contraseña)
    # -----------------------------------------------------------------
    with tab_login:
        ced_log = st.text_input("Cédula Estudiantil:", key="login_ced")
        pass_log = st.text_input("Contraseña:", type="password", key="login_pass")
        
        if st.button("Ingresar", use_container_width=True, key="btn_ingresar"):
            if not ced_log or not pass_log:
                st.warning("Por favor, rellene todos los campos.")
            else:
                # Buscamos que coincidan Cédula y Contraseña de manera estricta
                user = ejecutar_query("SELECT * FROM estudiantes WHERE cedula = ? AND contrasena = ?", (ced_log, pass_log), fetch=True)
                if user:
                    st.session_state.logueado = True
                    st.session_state.user = user[0]
                    st.success("¡Ingreso exitoso!")
                    st.rerun()
                else: 
                    st.error("Cédula o contraseña incorrecta, o el usuario aún no se ha registrado.")


        st.markdown("<div style='text-align: center; margin-top: -10px;'>", unsafe_allow_html=True)
        if st.button("¿Olvidaste tu contraseña?", use_container_width=True):
            recuperar_contrasena_modal(ejecutar_query)
        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------------------
    # PESTAÑA 2: PROCESO DE REGISTRO CON PIN DE SEGURIDAD
    # -----------------------------------------------------------------
    with tab_registro:
        # Inicializamos los estados de la sesión intermedio si no existen
        if "reg_paso" not in st.session_state:
            st.session_state.reg_paso = 1  # Paso 1: Pedir Cédula | Paso 2: Validar PIN
        if "reg_cedula" not in st.session_state:
            st.session_state.reg_cedula = ""
        if "reg_pin_generado" not in st.session_state:
            st.session_state.reg_pin_generado = ""
        if "reg_user_data" not in st.session_state:
            st.session_state.reg_user_data = None

        # --- PASO 1: Ingresar Cédula y solicitar PIN ---
        if st.session_state.reg_paso == 1:
            st.write("Introduce tu cédula para iniciar la verificación de tu cuenta.")
            ced_reg = st.text_input("Cédula a Registrar:", key="reg_ced")
            
            if st.button("Enviar PIN de Verificación", use_container_width=True):
                if not ced_reg:
                    st.warning("Por favor, ingresa tu cédula.")
                else:
                    # Buscamos al estudiante en la base de datos
                    alumno = ejecutar_query("SELECT cedula, nombre, apellido, correo, contrasena FROM estudiantes WHERE cedula = ?", (ced_reg,), fetch=True)
                    
                    if not alumno:
                        st.error("Esta cédula no se encuentra cargada en el sistema académico. Diríjase a control de estudios.")
                    else:
                        cedula, nombre, apellido, correo, contrasena_actual = alumno[0]
                        
                        if not correo:
                            st.error("El alumno existe pero no tiene un correo electrónico asociado en el sistema.")
                        elif contrasena_actual is not None:
                            st.warning("Este usuario ya generó sus credenciales de acceso anteriormente.")
                        else:
                            # Generamos el PIN aleatorio de 6 dígitos
                            pin_generado = str(random.randint(100000, 999999))
                            
                            cuerpo_html = f"""
                            <html>
                                <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
                                    <h2>¡Hola, {nombre}!</h2>
                                    <p>Estás registrando tu usuario en el Sistema de Inscripción.</p>
                                    <p>Tu PIN de seguridad de un solo uso es:</p>
                                    <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; border-radius: 5px; border: 1px solid #ddd; max-width: 200px; margin: 10px 0;">
                                        {pin_generado}
                                    </div>
                                    <p>Ingresa este código en la aplicación para validar tu identidad y activar tu cuenta.</p>
                                    <p style="font-size: 12px; color: #777;">Si tú no solicitaste este código, por favor ignora este correo.</p>
                                </body>
                            </html>
                            """
                            
                            st.info("Enviando código al correo registrado...")
                            if enviar_correo(correo, "🔐 Tu PIN de Verificación de Registro", cuerpo_html):
                                st.session_state.reg_pin_generado = pin_generado
                                st.session_state.reg_cedula = cedula
                                st.session_state.reg_user_data = alumno[0]
                                st.session_state.reg_paso = 2
                                st.success("Se ha enviado un PIN de seguridad al correo asociado.")
                                st.rerun()
                            else:
                                st.error("No se pudo enviar el correo electrónico. Revise sus credenciales SMTP.")

        # --- PASO 2: Confirmar PIN y entregar contraseña aleatoria ---
        elif st.session_state.reg_paso == 2:
            alumno = st.session_state.reg_user_data
            nombre_completo = f"{alumno[1]} {alumno[2]}"
            correo_destino = alumno[3]
            
            st.info(f"👤 Alumno: **{nombre_completo}**\n\n📧 El PIN fue enviado a: `{correo_destino}`")
            pin_usuario = st.text_input("Ingrese el PIN recibido de 6 dígitos:", max_chars=6, key="input_pin")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Validar PIN y Crear Usuario", use_container_width=True, type="primary"):
                    if pin_usuario == st.session_state.reg_pin_generado:
                        
                        # Generamos una contraseña aleatoria y segura de 10 caracteres
                        caracteres = string.ascii_letters + string.digits
                        nueva_contrasena = "".join(secrets.choice(caracteres) for _ in range(10))
                        
                        # Guardamos la contraseña de manera definitiva en la BD
                        ejecutar_query("UPDATE estudiantes SET contrasena = ? WHERE cedula = ?", (nueva_contrasena, st.session_state.reg_cedula))
                        
                        cuerpo_exito_html = f"""
                        <html>
                            <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
                                <h2>¡Registro Exitoso, {alumno[1]}!</h2>
                                <p>Tu cuenta ha sido verificada y activada de forma segura.</p>
                                <p>A partir de ahora, puedes acceder usando los siguientes datos:</p>
                                <table style="border-collapse: collapse; margin: 15px 0;">
                                    <tr>
                                        <td style="padding: 5px 10px; font-weight: bold;">Usuario (Cédula):</td>
                                        <td style="padding: 5px 10px; background-color: #f4f4f4;">{st.session_state.reg_cedula}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 5px 10px; font-weight: bold;">Contraseña Temporal:</td>
                                        <td style="padding: 5px 10px; background-color: #e8f0fe; font-family: monospace; font-size: 16px;">{nueva_contrasena}</td>
                                    </tr>
                                </table>
                                <p>⚠️ <b>Recomendación:</b> Copia tu contraseña e ingresa en la pestaña "Iniciar Sesión".</p>
                            </body>
                        </html>
                        """
                        
                        if enviar_correo(correo_destino, "🚀 Credenciales de Acceso Creadas", cuerpo_exito_html):
                            st.success("🎉 ¡Usuario creado! La contraseña fue enviada a tu correo.")
                            # Limpiamos el estado del registro para regresar al inicio
                            st.session_state.reg_paso = 1
                            st.session_state.reg_pin_generado = ""
                            st.session_state.reg_cedula = ""
                            st.session_state.reg_user_data = None
                        else:
                            st.error("Usuario guardado en la Base de Datos, pero falló el envío del correo final.")
                    else:
                        st.error("El PIN ingresado es incorrecto. Verifíquelo de nuevo.")
                        
            with col_b2:
                if st.button("❌ Cancelar / Volver", use_container_width=True):
                    st.session_state.reg_paso = 1
                    st.session_state.reg_pin_generado = ""
                    st.session_state.reg_cedula = ""
                    st.session_state.reg_user_data = None
                    st.rerun()




@st.dialog("🔄 Recuperar Contraseña")
def recuperar_contrasena_modal(ejecutar_query):
    st.write("Introduce tu cédula y te enviaremos una nueva contraseña de acceso a tu correo registrado.")
    ced_recup = st.text_input("Cédula del Estudiante:", key="recup_ced")
    
    if st.button("Enviar Nueva Contraseña", use_container_width=True, type="primary"):
        if not ced_recup:
            st.warning("Por favor, ingresa tu cédula.")
        else:
            # Buscamos al estudiante
            alumno = ejecutar_query("SELECT nombre, correo, contrasena FROM estudiantes WHERE cedula = ?", (ced_recup,), fetch=True)
            
            if not alumno:
                st.error("Esta cédula no está registrada en el sistema.")
            else:
                nombre, correo, contrasena_actual = alumno[0]
                
                if contrasena_actual is None:
                    st.warning("Este usuario aún no ha activado su cuenta. Por favor, ve a la pestaña 'Registrar Nuevo Usuario'.")
                elif not correo:
                    st.error("El usuario no tiene un correo válido asociado en el sistema.")
                else:
                    # Generamos una nueva clave segura
                    caracteres = string.ascii_letters + string.digits
                    nueva_contrasena = "".join(secrets.choice(caracteres) for _ in range(10))
                    
                    # Actualizamos de inmediato en la Base de Datos
                    ejecutar_query("UPDATE estudiantes SET contrasena = ? WHERE cedula = ?", (nueva_contrasena, ced_recup))
                    
                    cuerpo_recup_html = f"""
                    <html>
                        <body style="font-family: sans-serif; line-height: 1.6; color: #333;">
                            <h2>Hola, {nombre}.</h2>
                            <p>Hemos procesado tu solicitud de recuperación de credenciales.</p>
                            <p>Tu nueva contraseña temporal de acceso es:</p>
                            <div style="background-color: #e8f0fe; padding: 15px; text-align: center; font-size: 20px; font-family: monospace; font-weight: bold; border-radius: 5px; border: 1px solid #b3d4fc; max-width: 250px; margin: 10px 0;">
                                {nueva_contrasena}
                            </div>
                            <p>Te recomendamos iniciar sesión y resguardar tu nueva clave.</p>
                        </body>
                    </html>
                    """
                    
                    st.info("Enviando correo de recuperación...")
                    if enviar_correo(correo, "🔄 Tu Nueva Contraseña de Acceso", cuerpo_recup_html):
                        st.success("🎉 ¡Hecho! Revisa tu correo electrónico, te hemos enviado tu nueva contraseña.")
                        # Nota: En los fragmentos de Streamlit dentro de st.dialog, no se requiere rerun forzado para cerrar el modal si el flujo concluye con éxito.
                    else:
                        st.error("No se pudo enviar el correo electrónico. Verifique la configuración del servidor SMTP.")