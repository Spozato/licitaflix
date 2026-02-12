"""
🎬 LICITAFLIX — App Principal
Monitor inteligente de licitações públicas.
"""
import streamlit as st
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ---- Page Config ----
st.set_page_config(
    page_title="Licitaflix",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- Load Netflix CSS ----
css_path = os.path.join(os.path.dirname(__file__), "styles", "netflix.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ---- Sidebar Logo ----
st.sidebar.markdown(
    '<div class="logo-container">'
    '<span class="logo-text">🎬 LICITAFLIX</span>'
    '</div>',
    unsafe_allow_html=True
)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Navegação")
st.sidebar.page_link("app.py", label="🏠 Home", icon="🏠")
st.sidebar.page_link("pages/1_🔍_Buscar.py", label="🔍 Buscar Hoje")
st.sidebar.page_link("pages/2_📋_Feed.py", label="📋 Feed")
st.sidebar.page_link("pages/3_📊_Análise.py", label="📊 Análise")
st.sidebar.page_link("pages/4_⚙️_Perfis.py", label="⚙️ Perfis de Busca")

st.sidebar.markdown("---")
st.sidebar.markdown(
    '<p style="text-align:center; color:#555; font-size:0.75rem;">'
    'Licitaflix v1.0<br/>Powered by ComprasGov API'
    '</p>',
    unsafe_allow_html=True
)

# ---- Hero Section ----
st.markdown(
    """
    <div class="search-hero fade-in">
        <h1>🎬 LICITAFLIX</h1>
        <p style="color:#b3b3b3; font-size:1.1rem; margin-bottom:24px;">
            Monitor inteligente de licitações públicas<br/>
            <span style="color:#777;">Busque, analise e participe das melhores oportunidades</span>
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---- Quick Stats ----
try:
    from services import supabase_client as db
    from components.metrics import render_metrics
    from components.carousel import render_carousel

    licitacoes = db.listar_licitacoes(limite=100)
    
    # Calcular métricas
    from datetime import date
    novas_hoje = sum(
        1 for l in licitacoes 
        if l.get("created_at", "")[:10] == date.today().isoformat()
    )
    urgentes = sum(
        1 for l in licitacoes 
        if l.get("licitacao_status") and (
            (l["licitacao_status"][0]["prioridade"] if isinstance(l["licitacao_status"], list) and l["licitacao_status"] else "") == "urgente"
        )
    )
    valor_total = sum(
        float(l.get("valor_estimado") or 0) for l in licitacoes
    )
    analisando = sum(
        1 for l in licitacoes
        if l.get("licitacao_status") and (
            (l["licitacao_status"][0]["status"] if isinstance(l["licitacao_status"], list) and l["licitacao_status"] else "") == "analisando"
        )
    )

    render_metrics(novas_hoje, urgentes, valor_total, analisando)

    # ---- Carousels ----
    if licitacoes:
        # Urgentes
        urgentes_list = [
            l for l in licitacoes
            if l.get("licitacao_status") and (
                isinstance(l["licitacao_status"], list) and l["licitacao_status"] and
                l["licitacao_status"][0].get("prioridade") == "urgente"
            )
        ]
        if urgentes_list:
            render_carousel("🔴 URGENTE — Prazo Curto", urgentes_list)

        # Novas
        novas_list = [
            l for l in licitacoes
            if l.get("licitacao_status") and (
                isinstance(l["licitacao_status"], list) and l["licitacao_status"] and
                l["licitacao_status"][0].get("status") == "nova"
            )
        ][:12]
        if novas_list:
            render_carousel("🆕 NOVAS RECENTES", novas_list)

        # Por categoria (se tiver perfis vinculados)
        obras = [
            l for l in licitacoes
            if any(
                p.get("perfis_busca", {}).get("categorias", {}).get("nome") == "Obras"
                for p in (l.get("licitacao_perfil") or [])
                if isinstance(p, dict)
            )
        ]
        if obras:
            render_carousel("🏗️ OBRAS", obras)

        produtos = [
            l for l in licitacoes
            if any(
                p.get("perfis_busca", {}).get("categorias", {}).get("nome") == "Produtos"
                for p in (l.get("licitacao_perfil") or [])
                if isinstance(p, dict)
            )
        ]
        if produtos:
            render_carousel("📦 PRODUTOS", produtos)

        reformas = [
            l for l in licitacoes
            if any(
                p.get("perfis_busca", {}).get("categorias", {}).get("nome") == "Reformas"
                for p in (l.get("licitacao_perfil") or [])
                if isinstance(p, dict)
            )
        ]
        if reformas:
            render_carousel("🔧 REFORMAS", reformas)
    else:
        st.markdown(
            """
            <div style="text-align:center; padding:60px; color:#666;">
                <h2>🔍 Nenhuma licitação encontrada ainda</h2>
                <p>Vá para <strong>🔍 Buscar Hoje</strong> para fazer sua primeira busca!</p>
            </div>
            """,
            unsafe_allow_html=True
        )

except Exception as e:
    st.warning(f"⚠️ Conecte ao Supabase para ver dados ao vivo. Execute o schema.sql primeiro.")
    st.info("Vá ao SQL Editor do Supabase e cole o conteúdo de `schema.sql`.")
    with st.expander("📋 Ver erro"):
        st.code(str(e))

    # Show empty state
    st.markdown(
        """
        <div style="text-align:center; padding:60px; color:#666;">
            <h2 style="color:#E50914;">🚀 Primeiros passos</h2>
            <p style="font-size:1.1rem;">
                1. Execute o <code>schema.sql</code> no SQL Editor do Supabase<br/>
                2. Volte aqui e vá para <strong>🔍 Buscar Hoje</strong><br/>
                3. Selecione os perfis e clique em Buscar!
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
