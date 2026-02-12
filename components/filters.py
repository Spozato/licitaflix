"""
Licitaflix — Filters Component
Sidebar filters for the dashboard.
"""
import streamlit as st
from services.api_client import UFS, MODALIDADES


def render_sidebar_filters() -> dict:
    """Renderiza filtros na sidebar e retorna dict com filtros selecionados."""
    
    st.sidebar.markdown(
        '<div class="logo-container">'
        '<span class="logo-text">🎬 LICITAFLIX</span>'
        '</div>',
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")
    
    filtros = {}
    
    st.sidebar.markdown("### 🔍 Filtros")
    
    # Busca por texto
    busca = st.sidebar.text_input("Buscar no objeto", placeholder="ex: lousa de vidro")
    if busca:
        filtros["busca_texto"] = busca
    
    # UF
    uf = st.sidebar.selectbox("📍 UF", ["Todas"] + UFS)
    if uf != "Todas":
        filtros["uf"] = uf
    
    # Modalidade
    mod_options = ["Todas"] + [f"{k} - {v}" for k, v in MODALIDADES.items()]
    mod = st.sidebar.selectbox("📋 Modalidade", mod_options)
    if mod != "Todas":
        filtros["modalidade"] = mod.split(" - ")[1]
    
    # Status
    status = st.sidebar.selectbox(
        "📊 Status",
        ["Todos", "nova", "analisando", "participar", "descartada", "ganha", "perdida"]
    )
    if status != "Todos":
        filtros["status"] = status
    
    # Faixa de valor
    st.sidebar.markdown("### 💰 Valor Estimado")
    val_min = st.sidebar.number_input("Mínimo (R$)", min_value=0, value=0, step=10000)
    val_max = st.sidebar.number_input("Máximo (R$)", min_value=0, value=0, step=10000)
    if val_min > 0:
        filtros["valor_min"] = val_min
    if val_max > 0:
        filtros["valor_max"] = val_max
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<p style="text-align:center; color:#555; font-size:0.75rem;">'
        'Licitaflix v1.0 · Powered by ComprasGov API'
        '</p>',
        unsafe_allow_html=True
    )
    
    return filtros
