"""
🔍 Buscar Hoje — Seletor diário de perfis para busca
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Buscar Hoje | Licitaflix", page_icon="🔍", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "netflix.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="logo-container"><span class="logo-text">🎬 LICITAFLIX</span></div>',
    unsafe_allow_html=True
)

st.markdown("# 🔍 O Que Buscar Hoje?")
st.markdown("Selecione os perfis e categorias para buscar novas licitações.")

try:
    from services import supabase_client as db
    from services.search_engine import SearchEngine

    # Carregar categorias e perfis
    categorias = db.listar_categorias()
    
    if not categorias:
        st.warning("Nenhuma categoria encontrada. Execute o schema.sql no Supabase primeiro.")
        st.stop()

    # Dias de busca
    col_config1, col_config2 = st.columns([1, 3])
    with col_config1:
        dias = st.selectbox("📅 Buscar últimos", [3, 7, 14, 30], index=1, format_func=lambda x: f"{x} dias")

    st.markdown("---")

    # Renderizar categorias com perfis
    perfis_selecionados = []
    
    for cat in categorias:
        perfis = db.listar_perfis(categoria_id=cat["id"])
        
        if not perfis:
            continue

        st.markdown(f'<div class="row-title">{cat["icone"]} {cat["nome"]}</div>', unsafe_allow_html=True)
        
        # Botão para selecionar/deselecionar todos da categoria
        col_title, col_btn = st.columns([3, 1])
        with col_btn:
            if st.button(f"Selecionar Todos", key=f"all_{cat['id']}"):
                for p in perfis:
                    db.atualizar_buscar_hoje(p["id"], True)
                st.rerun()

        # Cards de perfis
        cols = st.columns(min(len(perfis), 4))
        for i, perfil in enumerate(perfis):
            with cols[i % len(cols)]:
                # Contar termos
                termos = db.listar_termos(perfil["id"])
                n_termos = len(termos)
                
                # Toggle
                ativo = st.checkbox(
                    f"**{perfil['nome']}**",
                    value=perfil.get("buscar_hoje", True),
                    key=f"check_{perfil['id']}"
                )
                
                # Atualizar se mudou
                if ativo != perfil.get("buscar_hoje", True):
                    db.atualizar_buscar_hoje(perfil["id"], ativo)
                
                st.caption(f"📝 {n_termos} termos · 📊 {perfil.get('total_encontradas', 0)} encontradas")
                
                ultima = perfil.get("ultima_busca")
                if ultima:
                    st.caption(f"🕐 Última: {str(ultima)[:16]}")
                
                if ativo:
                    perfis_selecionados.append(perfil)
        
        st.markdown("---")

    # ---- Botão de busca ----
    total_termos = 0
    for p in perfis_selecionados:
        termos = db.listar_termos(p["id"])
        total_termos += len(termos)

    st.markdown(f"### 🎯 {len(perfis_selecionados)} perfis selecionados · ~{total_termos} termos")

    if st.button(f"🚀 BUSCAR SELECIONADOS", type="primary", use_container_width=True):
        engine = SearchEngine()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        resultados_total = {"encontradas": 0, "novas": 0}
        resultados_por_perfil = []

        for i, perfil in enumerate(perfis_selecionados):
            # Carregar termos do perfil
            perfil["termos_busca"] = db.listar_termos(perfil["id"])
            
            status_text.markdown(f"🔍 **Buscando:** {perfil['nome']}...")
            progress_bar.progress((i) / len(perfis_selecionados))
            
            try:
                resultado = engine.buscar_por_perfil(perfil, dias_atras=dias)
                resultados_total["encontradas"] += resultado["encontradas"]
                resultados_total["novas"] += resultado["novas"]
                resultados_por_perfil.append({
                    "nome": perfil["nome"],
                    **resultado
                })
            except Exception as e:
                st.error(f"Erro buscando {perfil['nome']}: {e}")
                resultados_por_perfil.append({
                    "nome": perfil["nome"],
                    "encontradas": 0,
                    "novas": 0,
                    "erro": str(e)
                })

        progress_bar.progress(1.0)
        status_text.empty()

        # Resultado final
        st.markdown("---")
        st.markdown(
            f"""
            <div class="search-hero" style="padding:24px;">
                <h2 style="color:#4ade80;">✅ Busca Concluída!</h2>
                <p style="font-size:1.3rem; color:#fff;">
                    <strong>{resultados_total['encontradas']}</strong> licitações relevantes · 
                    <strong>{resultados_total['novas']}</strong> novas salvas
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Detalhes por perfil
        st.markdown("### 📊 Resultados por Perfil")
        for r in resultados_por_perfil:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{r['nome']}**")
            with col2:
                st.markdown(f"🎯 {r.get('encontradas', 0)} matches")
            with col3:
                st.markdown(f"🆕 {r.get('novas', 0)} novas")
            if r.get("erro"):
                st.error(f"⚠️ {r['erro']}")

except Exception as e:
    st.error("⚠️ Erro ao conectar com Supabase. Verifique as credenciais e o schema.")
    with st.expander("Ver erro"):
        st.code(str(e))
