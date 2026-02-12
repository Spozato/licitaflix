"""
📋 Feed — Feed de licitações estilo Netflix
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Feed | Licitaflix", page_icon="📋", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "netflix.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="logo-container"><span class="logo-text">🎬 LICITAFLIX</span></div>',
    unsafe_allow_html=True
)

try:
    from services import supabase_client as db
    from components.netflix_card import render_card, format_brl, badge_status, badge_prioridade
    from components.carousel import render_carousel
    from components.metrics import render_metrics
    from components.filters import render_sidebar_filters

    # Sidebar filters
    filtros = render_sidebar_filters()

    # Load data
    licitacoes = db.listar_licitacoes(filtros=filtros, limite=100)
    
    if not licitacoes:
        st.markdown(
            """
            <div style="text-align:center; padding:80px; color:#666;">
                <h2>📭 Nenhuma licitação encontrada</h2>
                <p>Faça uma busca em <strong>🔍 Buscar Hoje</strong> ou ajuste os filtros.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.stop()

    # Metrics
    from datetime import date
    novas_hoje = sum(1 for l in licitacoes if l.get("created_at", "")[:10] == date.today().isoformat())
    urgentes = sum(
        1 for l in licitacoes
        if l.get("licitacao_status") and isinstance(l["licitacao_status"], list) and l["licitacao_status"]
        and l["licitacao_status"][0].get("prioridade") == "urgente"
    )
    valor_total = sum(float(l.get("valor_estimado") or 0) for l in licitacoes)
    analisando = sum(
        1 for l in licitacoes
        if l.get("licitacao_status") and isinstance(l["licitacao_status"], list) and l["licitacao_status"]
        and l["licitacao_status"][0].get("status") == "analisando"
    )
    render_metrics(novas_hoje, urgentes, valor_total, analisando)

    # View toggle
    st.markdown("---")
    view = st.radio("Visualização", ["🎬 Netflix", "📋 Lista"], horizontal=True, label_visibility="collapsed")

    if view == "🎬 Netflix":
        # Netflix carousels
        urgentes_list = [
            l for l in licitacoes
            if l.get("licitacao_status") and isinstance(l["licitacao_status"], list)
            and l["licitacao_status"] and l["licitacao_status"][0].get("prioridade") == "urgente"
        ]
        novas_list = [
            l for l in licitacoes
            if l.get("licitacao_status") and isinstance(l["licitacao_status"], list)
            and l["licitacao_status"] and l["licitacao_status"][0].get("status") == "nova"
        ]
        analisando_list = [
            l for l in licitacoes
            if l.get("licitacao_status") and isinstance(l["licitacao_status"], list)
            and l["licitacao_status"] and l["licitacao_status"][0].get("status") == "analisando"
        ]

        if urgentes_list:
            render_carousel("🔴 URGENTE — Prazo Curto", urgentes_list)
        if analisando_list:
            render_carousel("🔍 EM ANÁLISE", analisando_list)
        if novas_list:
            render_carousel("🆕 NOVAS", novas_list[:12])
        
        # All remaining
        outras = [l for l in licitacoes if l not in urgentes_list + analisando_list]
        if outras:
            render_carousel("📋 TODAS AS LICITAÇÕES", outras[:12])

    else:
        # List view
        st.markdown(f"### 📋 {len(licitacoes)} licitações encontradas")
        
        for lic in licitacoes:
            with st.container():
                col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
                
                with col1:
                    objeto = (lic.get("objeto") or "")[:120]
                    st.markdown(f"**{objeto}**")
                    st.caption(f"📋 {lic.get('modalidade', '')} · 📍 {lic.get('uf', '')} · {lic.get('orgao', '')[:50] if lic.get('orgao') else ''}")
                
                with col2:
                    st.markdown(f"**{format_brl(lic.get('valor_estimado'))}**")
                
                with col3:
                    status_data = lic.get("licitacao_status", [])
                    if status_data and isinstance(status_data, list) and status_data:
                        st.markdown(badge_status(status_data[0].get("status", "nova")), unsafe_allow_html=True)
                
                with col4:
                    if st.button("📊", key=f"detail_{lic['id']}"):
                        st.session_state["licitacao_selecionada"] = lic["id"]
                        st.switch_page("pages/3_📊_Análise.py")
                
                st.markdown("---")

except Exception as e:
    st.error("⚠️ Erro ao carregar feed.")
    with st.expander("Ver erro"):
        st.code(str(e))
