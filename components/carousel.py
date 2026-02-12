"""
Licitaflix — Carousel Component
Renderiza carrosséis horizontais estilo Netflix.
"""
import streamlit as st
from components.netflix_card import render_card, render_card_mini


def render_carousel(titulo: str, licitacoes: list, subtitulo: str = "", max_items: int = 8):
    """
    Renderiza uma row/carrossel de cards estilo Netflix.
    
    Args:
        titulo: Título da row (ex: "🔴 URGENTE")
        licitacoes: Lista de dicts de licitações
        subtitulo: Texto auxiliar
        max_items: Máximo de items a mostrar
    """
    if not licitacoes:
        return

    st.markdown(f'<div class="row-title">{titulo}</div>', unsafe_allow_html=True)
    if subtitulo:
        st.markdown(f'<div class="row-subtitle">{subtitulo}</div>', unsafe_allow_html=True)

    items = licitacoes[:max_items]
    
    # Usar colunas do Streamlit para simular carrossel
    cols = st.columns(min(len(items), 4))
    for i, lic in enumerate(items):
        with cols[i % len(cols)]:
            if st.container():
                render_card(lic, show_actions=False)
                # Botão para ver detalhes
                if st.button("Ver mais", key=f"btn_{titulo}_{i}_{lic.get('id', i)}"):
                    st.session_state["licitacao_selecionada"] = lic.get("id")
                    st.switch_page("pages/3_📊_Análise.py")


def render_carousel_mini(titulo: str, licitacoes: list, max_items: int = 6):
    """Carrossel com cards mini."""
    if not licitacoes:
        return

    st.markdown(f'<div class="row-title">{titulo}</div>', unsafe_allow_html=True)

    items = licitacoes[:max_items]
    cols = st.columns(min(len(items), 5))
    for i, lic in enumerate(items):
        with cols[i % len(cols)]:
            render_card_mini(lic)
