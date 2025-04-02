import streamlit as st
import pandas as pd
import hashlib
import pyodbc
from db_connection import get_db_connection, execute_query


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest().upper()

def check_login(email, password):
    conn = get_db_connection()
    if conn:
        hashed_password = hash_password(password)
        query = "SELECT id, nome, email, is_admin FROM usuarios WHERE email=? AND senha=?"
        user = execute_query(query, (email, hashed_password), fetch=True)
        return user[0] if user else None
    return None

def create_user(name, email, password):
    try:
        if not name or not email or not password:
            st.error("Todos os campos são obrigatórios!")
            return
    
        hashed_password = hash_password(password)
        query = "INSERT INTO usuarios (nome, email, senha, is_admin) VALUES (?, ?, ?, 0)"
        return execute_query(query, (name, email, hashed_password))

    except Exception as e:
        st.error(f"Erro ao criar usuário: {e}")

def get_users():
    try:
        conn = get_db_connection()
        if conn:
            query = "SELECT id, nome, email FROM usuarios"
            df = pd.read_sql(query, conn)
            conn.close()
            return df
    except Exception as e:
        st.error(f"Erro ao buscar usuários: {e}")
        return pd.DataFrame()  
    
def delete_user(user_id):
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            query = "DELETE FROM usuarios WHERE id = ?"
            cursor.execute(query, (user_id,))
            conn.commit()
            conn.close()
            st.success("Usuário deletado com sucesso!")
            st.rerun()  
    except Exception as e:
        st.error(f"Erro ao deletar usuário: {e}")



def get_powerbi_url():
    query = "SELECT TOP 1 link FROM powerbi_config"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else "https://app.powerbi.com/view?r=seu_relatorio"

def set_powerbi_url(new_url):
    query = "DELETE FROM powerbi_config"
    execute_query(query)
    query = "INSERT INTO powerbi_config (link) VALUES (?)"
    execute_query(query, (new_url,))

st.set_page_config(layout="wide")

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.is_admin = False
    st.session_state.user_name = ""

if "logout" in st.session_state and st.session_state["logout"]:
    for key in list(st.session_state.keys()):
        del st.session_state[key]  
    st.rerun()  

def logout():
    st.session_state["logout"] = True  

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <style>
        /* Esconde elementos indesejados */
        .block-container {max-width: 400px; margin: auto; padding-top: 5rem;}
        header {display: none !important;}
        .stDeployButton {display: none !important;}

        /* Remove o cabeçalho e alguns botões padrão do Streamlit */
        .block-container {max-width: 400px; margin: auto; padding-top: 5rem;}
        header {display: none !important;}
        .stDeployButton {display: none !important;}

        /* Define o fundo da página */
        body {
            background-color: #0A2A43;
        }

        /* Centraliza o container do login */
        .login-container {
            width: 100%;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Caixa branca para o login */
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
            text-align: center;
            width: 350px;
        }

        /* Título do login */
        .login-title {
            font-size: 26px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #000;
        }

        /* Labels */
        .login-label {
            text-align: left;
            font-weight: bold;
            font-size: 14px;
            display: block;
            margin-bottom: 5px;
        }

        /* Campos de entrada */
        .login-input {
            width: 100%;
            padding: 12px;
            margin-bottom: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
            transition: border 0.3s;
        }
        .login-input:focus {
            border-color: #0A2A43;
            outline: none;
        }

        /* Botão de login */
        .login-button {
            width: 100%;
            background-color: #0A2A43;
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s, transform 0.1s;
        }
        .login-button:hover {
            background-color: #08385A;
        }
        .login-button:active {
            transform: scale(0.98);
        }

        /* Link de esqueci minha senha */
        .forgot-password {
            margin-top: 10px;
            font-size: 14px;
        }
        .forgot-password a {
            color: #0A2A43;
            text-decoration: none;
        }
        .forgot-password a:hover {
            text-decoration: underline;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-title">LOGIN</div>', unsafe_allow_html=True)

        email = st.text_input("Usuário", key="login_email", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", key="login_password", placeholder="Digite sua senha")


        if st.button("LOGIN", key="login-button"):
            user = check_login(email, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.is_admin = int(user[3]) == 1
                st.session_state.user_name = user[1]
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Credenciais inválidas!")

else:
    st.sidebar.write(f"Bem-vindo, {st.session_state.user_name}!")
    if st.session_state.is_admin:
        st.sidebar.title("Administração")
        option = st.sidebar.radio("Escolha uma opção", ["Usuários", "Configurar Power BI"])
        
        if option == "Usuários":
            st.subheader("Adicionar Novo Usuário")

            name = st.text_input("Nome")
            email = st.text_input("Email")
            password = st.text_input("Senha", type="password")

            if st.button("Criar Usuário"):
                create_user(name, email, password)

            users_df = get_users()

            st.subheader("Usuários Cadastrados")

            if not users_df.empty:
                st.write(users_df)

                user_to_delete = st.selectbox("Selecione um usuário para deletar:", users_df["id"].astype(str) + " - " + users_df["nome"])
                
                if st.button("Excluir Usuário"):
                    user_id = user_to_delete.split(" - ")[0] 
                    delete_user(user_id)
            else:
                st.info("Nenhum usuário cadastrado ainda.")        
        
        elif option == "Configurar Power BI":
            st.subheader("Configurar URL do Power BI")
            current_url = get_powerbi_url()
            new_url = st.text_input("Novo link do Power BI", value=current_url)
            
            if st.button("Salvar"):
                if new_url.strip() == "":
                    st.error("O link do Power BI não pode estar vazio!")
                else:
                    set_powerbi_url(new_url)
                    st.success("Link atualizado com sucesso!")
    else:
            st.markdown(
                """<style>
                .block-container {padding: 0; margin: 0; width: 100%; max-width: 100%; overflow: hidden;}
                iframe {width: 100vw; height: 108vh; border: none;}
                header {display: none !important;}
                .stDeployButton {display: none !important;}
                .st-emotion-cache-18ni7ap {padding: 0px;}
                .main {padding-left: 0px; padding-right: 0px;}
                </style>""", 
                unsafe_allow_html=True
            )

            powerbi_url = get_powerbi_url()
            st.markdown(f"<iframe src='{powerbi_url}' allowFullScreen></iframe>", unsafe_allow_html=True)

    
    st.sidebar.button("Logout", on_click=logout)
