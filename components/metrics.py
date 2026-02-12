"""
Licitaflix — Metrics Component
KPI cards do topo do dashboard.
"""
import streamlit as st


def render_metrics(novas_hoje: int = 0, urgentes: int = 0, 
                   valor_total: float = 0, analisando: int = 0):
    """Renderiza os KPIs do topo em estilo Netflix."""
    cols = st.columns(4)
    
    with cols[0]:
        st.metric(
            label="🆕 Novas Hoje",
            value=str(novas_hoje),
            delta=f"+{novas_hoje}" if novas_hoje > 0 else None
        )
    
    with cols[1]:
        st.metric(
            label="🔴 Urgentes",
            value=str(urgentes),
            delta="⚠️ Atenção" if urgentes > 0 else "Tudo ok"
        )
    
    with cols[2]:
        if valor_total >= 1_000_000:
            valor_fmt = f"R$ {valor_total/1_000_000:.1f}M"
        elif valor_total >= 1_000:
            valor_fmt = f"R$ {valor_total/1_000:.0f}k"
        else:
            valor_fmt = f"R$ {valor_total:.0f}"
        st.metric(
            label="💰 Valor Total",
            value=valor_fmt
        )
    
    with cols[3]:
        st.metric(
            label="🔍 Analisando",
            value=str(analisando)
        )
