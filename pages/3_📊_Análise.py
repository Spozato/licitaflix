"""
📊 Análise — Detalhe de uma licitação
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Análise | Licitaflix", page_icon="📊", layout="wide")

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
    from components.netflix_card import format_brl, badge_status, badge_prioridade, dias_restantes

    # Obter licitação selecionada
    lic_id = st.session_state.get("licitacao_selecionada")
    
    if not lic_id:
        # Mostrar seletor
        st.markdown("## 📊 Análise de Licitação")
        st.info("Selecione uma licitação no Feed ou busque pelo ID abaixo.")
        
        licitacoes = db.listar_licitacoes(limite=20)
        if licitacoes:
            opcoes = {f"{l.get('objeto', '')[:80]} ({format_brl(l.get('valor_estimado'))})": l["id"] for l in licitacoes}
            escolha = st.selectbox("Selecionar licitação", list(opcoes.keys()))
            if escolha:
                lic_id = opcoes[escolha]
                st.session_state["licitacao_selecionada"] = lic_id
        else:
            st.warning("Nenhuma licitação no banco. Faça uma busca primeiro!")
            st.stop()

    if not lic_id:
        st.stop()

    # Carregar dados
    lic = db.buscar_licitacao_por_id(lic_id)
    if not lic:
        st.error("Licitação não encontrada.")
        st.stop()

    # ---- Header ----
    st.markdown(f"## 📋 {lic.get('modalidade', 'Licitação')}")
    
    # Status e prioridade atuais
    status_data = lic.get("licitacao_status", [])
    status_atual = "nova"
    prioridade_atual = "normal"
    notas_atuais = ""
    if status_data:
        s = status_data[0] if isinstance(status_data, list) else status_data
        status_atual = s.get("status", "nova")
        prioridade_atual = s.get("prioridade", "normal")
        notas_atuais = s.get("notas", "") or ""

    # ---- Objeto ----
    st.markdown(
        f"""
        <div style="background:#1e1e2e; border-radius:12px; padding:24px; border-left:4px solid #E50914; margin:16px 0;">
            <h3 style="color:#fff; margin-bottom:12px;">Objeto</h3>
            <p style="color:#ccc; font-size:1.05rem; line-height:1.6;">{lic.get('objeto', 'N/I')}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---- Dados Principais ----
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Valor Estimado", format_brl(lic.get("valor_estimado")))
    with col2:
        st.metric("✅ Valor Homologado", format_brl(lic.get("valor_homologado")))
    with col3:
        dias = dias_restantes(lic.get("data_encerramento_proposta") or lic.get("data_abertura_proposta"))
        prazo = f"{dias}d" if dias is not None else "N/I"
        st.metric("⏰ Prazo", prazo)
    with col4:
        st.metric("📦 Itens", lic.get("numero_itens", "N/I"))

    # ---- Informações detalhadas ----
    st.markdown("---")
    col_info1, col_info2 = st.columns(2)

    with col_info1:
        st.markdown("### 📋 Informações Gerais")
        info_data = {
            "ID Compra": lic.get("id_compra", "N/I"),
            "Nº Processo": lic.get("numero_processo", "N/I"),
            "Nº PNCP": lic.get("numero_controle_pncp", "N/I"),
            "Fonte": lic.get("fonte", "N/I"),
            "Modalidade": lic.get("modalidade", "N/I"),
            "Situação": lic.get("situacao", "N/I"),
            "SRP": "✅ Sim" if lic.get("srp") else "❌ Não",
        }
        for k, v in info_data.items():
            st.markdown(f"**{k}:** {v}")

    with col_info2:
        st.markdown("### 📍 Localização e Órgão")
        loc_data = {
            "Órgão": lic.get("orgao", "N/I"),
            "UASG": lic.get("uasg", "N/I"),
            "UF": lic.get("uf", "N/I"),
            "Município": lic.get("municipio", "N/I"),
        }
        for k, v in loc_data.items():
            st.markdown(f"**{k}:** {v}")

        st.markdown("### 📅 Datas")
        dates = {
            "Publicação": lic.get("data_publicacao", "N/I"),
            "Abertura Proposta": str(lic.get("data_abertura_proposta", "N/I"))[:16],
            "Encerramento": str(lic.get("data_encerramento_proposta", "N/I"))[:16],
            "Resultado": str(lic.get("data_resultado", "N/I"))[:16],
        }
        for k, v in dates.items():
            st.markdown(f"**{k}:** {v}")

    # ---- Perfis que encontraram ----
    perfil_data = lic.get("licitacao_perfil", [])
    if perfil_data:
        st.markdown("---")
        st.markdown("### 🎯 Encontrada por")
        for p in perfil_data:
            if isinstance(p, dict):
                pb = p.get("perfis_busca", {})
                cat = pb.get("categorias", {})
                st.markdown(
                    f"- **{pb.get('nome', '')}** ({cat.get('icone', '')} {cat.get('nome', '')}) "
                    f"· Termo: `{p.get('termo_encontrado', '')}` "
                    f"· Score: {p.get('score_match', 0):.0%}"
                )

    # ---- Ações ----
    st.markdown("---")
    st.markdown("### 🎬 Ações")

    col_act1, col_act2, col_act3, col_act4 = st.columns(4)

    with col_act1:
        if st.button("🔍 Analisar", type="primary", use_container_width=True):
            db.atualizar_status_licitacao(lic_id, "analisando", prioridade_atual)
            st.success("Status: Analisando ✅")
            st.rerun()

    with col_act2:
        if st.button("✅ Participar", use_container_width=True):
            db.atualizar_status_licitacao(lic_id, "participar", "alta")
            st.success("Status: Participar ✅")
            st.rerun()

    with col_act3:
        if st.button("❌ Descartar", use_container_width=True):
            db.atualizar_status_licitacao(lic_id, "descartada", "baixa")
            st.info("Descartada")
            st.rerun()

    with col_act4:
        prioridade_nova = st.selectbox(
            "Prioridade",
            ["urgente", "alta", "normal", "baixa"],
            index=["urgente", "alta", "normal", "baixa"].index(prioridade_atual)
        )
        if prioridade_nova != prioridade_atual:
            db.atualizar_status_licitacao(lic_id, status_atual, prioridade_nova)
            st.rerun()

    # Notas
    notas = st.text_area("📝 Notas / Observações", value=notas_atuais, height=100)
    if st.button("💾 Salvar Notas"):
        db.atualizar_status_licitacao(lic_id, status_atual, prioridade_atual, notas)
        st.success("Notas salvas! ✅")

    # ---- Dados Brutos ----
    with st.expander("🔧 Dados brutos (JSON da API)"):
        st.json(lic.get("dados_brutos", {}))

except Exception as e:
    st.error("⚠️ Erro ao carregar análise.")
    with st.expander("Ver erro"):
        st.code(str(e))
