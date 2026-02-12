"""
Licitaflix — Netflix Card Component
Gera HTML dos cards estilo Netflix para licitações.
"""
import streamlit as st
from datetime import datetime, date


def format_brl(value):
    """Formata valor em BRL."""
    if value is None:
        return "N/I"
    try:
        v = float(value)
        if v >= 1_000_000:
            return f"R$ {v/1_000_000:.1f}M"
        elif v >= 1_000:
            return f"R$ {v/1_000:.0f}k"
        else:
            return f"R$ {v:.0f}"
    except (ValueError, TypeError):
        return "N/I"


def dias_restantes(data_str):
    """Calcula dias restantes até uma data."""
    if not data_str:
        return None
    try:
        if isinstance(data_str, str):
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            target = dt.date() if hasattr(dt, 'date') else dt
        else:
            target = data_str
        delta = (target - date.today()).days
        return delta
    except (ValueError, TypeError):
        return None


def badge_prioridade(prioridade: str) -> str:
    """Retorna HTML do badge de prioridade."""
    icons = {
        "urgente": "🔴",
        "alta": "🟠",
        "normal": "🟢",
        "baixa": "⚪"
    }
    icon = icons.get(prioridade, "⚪")
    return f'<span class="card-badge badge-{prioridade}">{icon} {prioridade.upper()}</span>'


def badge_status(status: str) -> str:
    """Retorna HTML do badge de status."""
    labels = {
        "nova": "🆕 Nova",
        "analisando": "🔍 Analisando",
        "participar": "✅ Participar",
        "descartada": "❌ Descartada",
        "ganha": "🏆 Ganha",
        "perdida": "💔 Perdida"
    }
    label = labels.get(status, status)
    return f'<span class="card-badge badge-{status}">{label}</span>'


def badge_categoria(categoria: dict) -> str:
    """Retorna HTML do badge de categoria."""
    if not categoria:
        return ""
    icone = categoria.get("icone", "📦")
    nome = categoria.get("nome", "")
    classe = nome.lower().replace(" ", "-") if nome else "produto"
    classmap = {
        "produtos": "badge-produto",
        "obras": "badge-obra",
        "reformas": "badge-reforma",
    }
    badge_class = classmap.get(nome.lower(), "badge-normal")
    return f'<span class="card-badge {badge_class}">{icone} {nome}</span>'


def render_card(lic: dict, show_actions: bool = True):
    """
    Renderiza um card Netflix para uma licitação.
    
    Args:
        lic: dict com dados da licitação
        show_actions: se mostra botões de ação
    """
    objeto = (lic.get("objeto") or "Sem descrição")[:150]
    valor = format_brl(lic.get("valor_estimado"))
    modalidade = lic.get("modalidade", "N/I")
    uf = lic.get("uf", "")
    municipio = lic.get("municipio", "")
    local = f"{municipio} · {uf}" if municipio else (uf or "Brasil")
    
    # Status e prioridade
    status_data = lic.get("licitacao_status", [])
    status = "nova"
    prioridade = "normal"
    if status_data:
        s = status_data[0] if isinstance(status_data, list) else status_data
        status = s.get("status", "nova")
        prioridade = s.get("prioridade", "normal")
    
    # Prazo
    dias = dias_restantes(lic.get("data_encerramento_proposta") or lic.get("data_abertura_proposta"))
    prazo_text = ""
    if dias is not None:
        if dias < 0:
            prazo_text = "Encerrada"
        elif dias == 0:
            prazo_text = "🔴 Hoje!"
        elif dias <= 3:
            prazo_text = f"🔴 {dias}d restantes"
        elif dias <= 7:
            prazo_text = f"🟡 {dias}d restantes"
        else:
            prazo_text = f"{dias}d restantes"

    # Categoria do perfil vinculado
    perfil_data = lic.get("licitacao_perfil", [])
    categoria_badge = ""
    perfil_nome = ""
    if perfil_data:
        p = perfil_data[0] if isinstance(perfil_data, list) else perfil_data
        pb = p.get("perfis_busca", {})
        if pb:
            perfil_nome = pb.get("nome", "")
            cat = pb.get("categorias", {})
            if cat:
                categoria_badge = badge_categoria(cat)

    # Border color based on priority
    border_colors = {
        "urgente": "#E50914",
        "alta": "#FF6B00",
        "normal": "#0D7377",
        "baixa": "#333"
    }
    border_color = border_colors.get(prioridade, "#0D7377")

    html = f"""
    <div class="netflix-card" style="border-left-color: {border_color};">
        <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px;">
            {categoria_badge}
            {badge_prioridade(prioridade)}
        </div>
        <div class="card-title">{objeto}</div>
        <div class="card-value">{valor}</div>
        <div class="card-meta">📋 {modalidade}</div>
        <div class="card-meta">📍 {local}</div>
        {"<div class='card-meta'>⏰ " + prazo_text + "</div>" if prazo_text else ""}
        {"<div class='card-meta' style='color:#E50914;font-weight:600;'>🎯 " + perfil_nome + "</div>" if perfil_nome else ""}
        <div style="margin-top:8px;">
            {badge_status(status)}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_card_mini(lic: dict):
    """Renderiza versão mini do card (para carrossel)."""
    objeto = (lic.get("objeto") or "Sem descrição")[:80]
    valor = format_brl(lic.get("valor_estimado"))
    uf = lic.get("uf", "BR")

    html = f"""
    <div class="netflix-card" style="min-height:120px; padding:14px;">
        <div class="card-title" style="font-size:0.82rem;">{objeto}</div>
        <div class="card-value" style="font-size:1.1rem;">{valor}</div>
        <div class="card-meta">📍 {uf}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
