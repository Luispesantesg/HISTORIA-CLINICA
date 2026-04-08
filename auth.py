import streamlit as st
import hmac

def verificar_autenticacion() -> bool:
    if st.session_state.get("autenticado", False):
        return True

    st.title("🔒 Portal de Acceso Restringido")
    st.markdown("Sistema de Historia Clínica Electrónica - Control de Acceso")
    
    with st.form("formulario_login"):
        usuario = st.text_input("Identificador de Usuario:").strip()
        contrasena = st.text_input("Clave de Acceso:", type="password").strip()
        submit = st.form_submit_button("Iniciar Sesión", type="primary", width='stretch')

        if submit:
            try:
                matriz_usuarios = st.secrets["credenciales"]
                if usuario in matriz_usuarios:
                    pass_valida = hmac.compare_digest(contrasena, matriz_usuarios[usuario])
                    if pass_valida:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_activo"] = usuario
                        st.rerun()
                    else:
                        st.error("Brecha de Seguridad: Contraseña inválida. Acceso denegado.")
                else:
                    st.error("Brecha de Seguridad: Identificador de usuario no reconocido.")
            except KeyError:
                st.error("Falla Crítica: El bloque [credenciales] no está definido en secrets.toml.")
    return False
