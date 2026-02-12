"""
⚙️ Perfis — CRUD de perfis de busca e termos
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Perfis | Licitaflix", page_icon="⚙️", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "netflix.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="logo-container"><span class="logo-text">🎬 LICITAFLIX</span></div>',
    unsafe_allow_html=True
)

st.markdown("# ⚙️ Perfis de Busca")

try:
    from services import supabase_client as db

    tab_perfis, tab_categorias, tab_novo = st.tabs(["📋 Perfis", "📁 Categorias", "➕ Novo Perfil"])

    # ---- TAB: Perfis existentes ----
    with tab_perfis:
        categorias = db.listar_categorias(apenas_ativas=False)
        
        for cat in categorias:
            st.markdown(f'<div class="row-title">{cat["icone"]} {cat["nome"]}</div>', unsafe_allow_html=True)
            
            perfis = db.listar_perfis(categoria_id=cat["id"], apenas_ativos=False)
            
            if not perfis:
                st.caption("Nenhum perfil nesta categoria.")
                continue

            for perfil in perfis:
                with st.expander(f"{'✅' if perfil['ativo'] else '⏸️'} {perfil['nome']} — {perfil.get('descricao', '')}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Descrição:** {perfil.get('descricao', 'N/I')}")
                        st.markdown(f"**Regiões:** {', '.join(perfil.get('regioes', []) or ['Todas'])}")
                        st.markdown(f"**Total encontradas:** {perfil.get('total_encontradas', 0)}")
                        st.markdown(f"**Última busca:** {str(perfil.get('ultima_busca', 'Nunca'))[:16]}")
                    
                    with col2:
                        ativo = st.checkbox("Ativo", value=perfil["ativo"], key=f"ativo_{perfil['id']}")
                        if ativo != perfil["ativo"]:
                            db.atualizar_perfil(perfil["id"], {"ativo": ativo})
                            st.rerun()
                        
                        buscar = st.checkbox("Buscar hoje", value=perfil.get("buscar_hoje", True), key=f"hoje_{perfil['id']}")
                        if buscar != perfil.get("buscar_hoje", True):
                            db.atualizar_buscar_hoje(perfil["id"], buscar)
                            st.rerun()

                    # Termos de busca
                    st.markdown("#### 📝 Termos de Busca")
                    termos = db.listar_termos(perfil["id"], apenas_ativos=False)
                    
                    if termos:
                        for t in termos:
                            tcol1, tcol2, tcol3, tcol4 = st.columns([3, 1, 1, 1])
                            with tcol1:
                                origem_icon = {"manual": "✍️", "aprendido": "🧠", "sugerido": "💡"}.get(t.get("origem", ""), "")
                                st.markdown(f"{origem_icon} `{t['termo']}`")
                            with tcol2:
                                st.caption(f"Score: {t.get('score_relevancia', 1.0):.2f}")
                            with tcol3:
                                st.caption(f"Encontrou: {t.get('vezes_encontrado', 0)}x")
                            with tcol4:
                                if not t.get("ativo", True):
                                    st.caption("⏸️ Inativo")
                    
                    # Adicionar novo termo
                    novo_termo = st.text_input(
                        "Adicionar termo",
                        placeholder="ex: quadro de vidro temperado",
                        key=f"novo_termo_{perfil['id']}"
                    )
                    if st.button("➕ Adicionar", key=f"add_termo_{perfil['id']}"):
                        if novo_termo.strip():
                            db.adicionar_termo(perfil["id"], novo_termo.strip())
                            st.success(f"Termo '{novo_termo}' adicionado! ✅")
                            st.rerun()

            st.markdown("---")

    # ---- TAB: Categorias ----
    with tab_categorias:
        st.markdown("### 📁 Categorias")
        for cat in categorias:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"{cat['icone']} **{cat['nome']}**")
            with col2:
                st.markdown(
                    f"<span style='display:inline-block; width:20px; height:20px; "
                    f"background:{cat['cor']}; border-radius:4px;'></span> {cat['cor']}",
                    unsafe_allow_html=True
                )
            with col3:
                st.markdown("✅ Ativa" if cat['ativa'] else "⏸️ Inativa")
        
        st.markdown("---")
        st.markdown("### ➕ Nova Categoria")
        nc_nome = st.text_input("Nome da categoria", placeholder="ex: Pavimentação")
        nc_icone = st.text_input("Ícone (emoji)", value="📦", max_chars=4)
        nc_cor = st.color_picker("Cor", value="#E50914")
        if st.button("Criar Categoria"):
            if nc_nome.strip():
                db.criar_categoria(nc_nome.strip(), nc_icone, nc_cor)
                st.success(f"Categoria '{nc_nome}' criada! ✅")
                st.rerun()

    # ---- TAB: Novo Perfil ----
    with tab_novo:
        st.markdown("### ➕ Novo Perfil de Busca")
        
        categorias_opcoes = {f"{c['icone']} {c['nome']}": c["id"] for c in categorias}
        cat_escolhida = st.selectbox("Categoria", list(categorias_opcoes.keys()))
        cat_id = categorias_opcoes[cat_escolhida]
        
        np_nome = st.text_input("Nome do perfil", placeholder="ex: Asfalto e Pavimentação")
        np_descricao = st.text_area("Descrição", placeholder="Obras de pavimentação e recapeamento asfáltico")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            np_val_min = st.number_input("Valor mínimo (R$)", min_value=0, value=0, step=10000)
        with col_v2:
            np_val_max = st.number_input("Valor máximo (R$)", min_value=0, value=0, step=10000)
        
        from services.api_client import UFS
        np_regioes = st.multiselect("Regiões (UF)", UFS, default=[])
        
        np_termos = st.text_area(
            "Termos de busca (um por linha)",
            placeholder="asfalto\npavimentação\nrecapeamento\nCBUQ\nasfalto a quente",
            height=150
        )
        
        if st.button("🚀 Criar Perfil", type="primary"):
            if np_nome.strip():
                result = db.criar_perfil(
                    nome=np_nome.strip(),
                    categoria_id=cat_id,
                    descricao=np_descricao,
                    valor_minimo=np_val_min if np_val_min > 0 else None,
                    valor_maximo=np_val_max if np_val_max > 0 else None,
                    regioes=np_regioes or None
                )
                
                # Adicionar termos
                if result and np_termos.strip():
                    perfil_id = result[0]["id"]
                    linhas = [l.strip() for l in np_termos.strip().split("\n") if l.strip()]
                    for linha in linhas:
                        db.adicionar_termo(perfil_id, linha)
                
                st.success(f"Perfil '{np_nome}' criado com {len(np_termos.strip().split(chr(10)))} termos! ✅")
                st.rerun()
            else:
                st.error("Nome é obrigatório!")

except Exception as e:
    st.error("⚠️ Erro ao carregar perfis.")
    with st.expander("Ver erro"):
        st.code(str(e))
