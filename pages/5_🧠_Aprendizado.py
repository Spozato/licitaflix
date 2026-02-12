"""
🧠 Aprendizado — Sistema de aprendizado de termos
"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

st.set_page_config(page_title="Aprendizado | Licitaflix", page_icon="🧠", layout="wide")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "..", "styles", "netflix.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    '<div class="logo-container"><span class="logo-text">🎬 LICITAFLIX</span></div>',
    unsafe_allow_html=True
)

st.markdown("# 🧠 Aprendizado de Termos")
st.markdown("O sistema analisa suas buscas e sugere novos termos automaticamente.")

try:
    from services import supabase_client as db

    categorias = db.listar_categorias()
    
    for cat in categorias:
        perfis = db.listar_perfis(categoria_id=cat["id"])
        if not perfis:
            continue
            
        st.markdown(f'<div class="row-title">{cat["icone"]} {cat["nome"]}</div>', unsafe_allow_html=True)
        
        for perfil in perfis:
            with st.expander(f"📊 {perfil['nome']}", expanded=False):
                termos = db.listar_termos(perfil["id"], apenas_ativos=False)
                
                if not termos:
                    st.caption("Nenhum termo cadastrado.")
                    continue

                # Performance dos termos
                st.markdown("#### 📈 Performance dos Termos")
                
                # Ordenar por score
                termos_ord = sorted(termos, key=lambda t: t.get("score_relevancia", 0), reverse=True)
                
                for t in termos_ord:
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                    
                    with col1:
                        origem_icon = {
                            "manual": "✍️",
                            "aprendido": "🧠",
                            "sugerido": "💡"
                        }.get(t.get("origem", ""), "❓")
                        st.markdown(f"{origem_icon} **{t['termo']}**")
                    
                    with col2:
                        score = t.get("score_relevancia", 1.0)
                        bar_color = "#4ade80" if score >= 0.7 else "#f59e0b" if score >= 0.4 else "#ef4444"
                        st.markdown(
                            f'<div style="background:#2a2a2a; border-radius:4px; overflow:hidden;">'
                            f'<div style="background:{bar_color}; width:{score*100:.0f}%; height:8px;"></div>'
                            f'</div>'
                            f'<span style="font-size:0.75rem; color:#888;">{score:.0%}</span>',
                            unsafe_allow_html=True
                        )
                    
                    with col3:
                        st.caption(f"Encontrou: {t.get('vezes_encontrado', 0)}x")
                    
                    with col4:
                        st.caption(f"Útil: {t.get('vezes_util', 0)}x")
                    
                    with col5:
                        if t.get("ativo"):
                            if st.button("⏸️", key=f"pause_{t['id']}"):
                                db.atualizar_termo(t["id"], {"ativo": False})
                                st.rerun()
                        else:
                            if st.button("▶️", key=f"play_{t['id']}"):
                                db.atualizar_termo(t["id"], {"ativo": True})
                                st.rerun()

                # Sugestões
                sugestoes = db.listar_sugestoes(perfil["id"])
                if sugestoes:
                    st.markdown("#### 💡 Termos Sugeridos")
                    st.caption("Termos descobertos automaticamente nos objetos das licitações.")
                    
                    for s in sugestoes:
                        scol1, scol2, scol3 = st.columns([3, 1, 1])
                        with scol1:
                            st.markdown(f"💡 **{s['termo_sugerido']}** (apareceu {s.get('frequencia', 1)}x)")
                        with scol2:
                            if st.button("✅ Aceitar", key=f"aceitar_{s['id']}"):
                                db.responder_sugestao(s["id"], True)
                                db.adicionar_termo(perfil["id"], s["termo_sugerido"], origem="aprendido")
                                st.success(f"Termo '{s['termo_sugerido']}' adicionado!")
                                st.rerun()
                        with scol3:
                            if st.button("❌ Rejeitar", key=f"rejeitar_{s['id']}"):
                                db.responder_sugestao(s["id"], False)
                                st.rerun()

    # Histórico de buscas
    st.markdown("---")
    st.markdown("### 📊 Histórico de Buscas Recentes")
    
    sb = db.get_client()
    historico = sb.table("historico_buscas").select(
        "*, perfis_busca(nome)"
    ).order("data_busca", desc=True).limit(30).execute().data
    
    if historico:
        import pandas as pd
        df = pd.DataFrame([{
            "Data": str(h.get("data_busca", ""))[:16],
            "Perfil": h.get("perfis_busca", {}).get("nome", ""),
            "Termo": h.get("termo_usado", ""),
            "Resultados": h.get("total_resultados", 0),
            "Úteis": h.get("resultados_uteis", 0),
        } for h in historico])
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.caption("Nenhuma busca registrada ainda.")

except Exception as e:
    st.error("⚠️ Erro ao carregar aprendizado.")
    with st.expander("Ver erro"):
        st.code(str(e))
