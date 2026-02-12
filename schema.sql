-- ============================================
-- LICITAFLIX — Schema Supabase
-- Execute no SQL Editor do Supabase
-- ============================================

-- Categorias agrupam perfis (ex: "Produtos", "Obras")
CREATE TABLE IF NOT EXISTS categorias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nome TEXT NOT NULL,
    icone TEXT DEFAULT '📦',
    cor TEXT DEFAULT '#E50914',
    ativa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Perfis de busca dentro de cada categoria
CREATE TABLE IF NOT EXISTS perfis_busca (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    categoria_id UUID REFERENCES categorias(id) ON DELETE SET NULL,
    nome TEXT NOT NULL,
    descricao TEXT,
    valor_minimo NUMERIC,
    valor_maximo NUMERIC,
    regioes TEXT[] DEFAULT '{}',
    modalidades INT[] DEFAULT '{}',
    ativo BOOLEAN DEFAULT TRUE,
    buscar_hoje BOOLEAN DEFAULT TRUE,
    ultima_busca TIMESTAMPTZ,
    total_encontradas INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Termos de busca vinculados a um perfil
CREATE TABLE IF NOT EXISTS termos_busca (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    perfil_id UUID REFERENCES perfis_busca(id) ON DELETE CASCADE,
    termo TEXT NOT NULL,
    origem TEXT DEFAULT 'manual',
    score_relevancia FLOAT DEFAULT 1.0,
    vezes_encontrado INT DEFAULT 0,
    vezes_util INT DEFAULT 0,
    ativo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Licitações encontradas
CREATE TABLE IF NOT EXISTS licitacoes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    id_compra TEXT UNIQUE,
    numero_controle_pncp TEXT,
    fonte TEXT NOT NULL,
    modalidade TEXT,
    modalidade_codigo INT,
    objeto TEXT NOT NULL,
    valor_estimado NUMERIC,
    valor_homologado NUMERIC,
    orgao TEXT,
    uasg TEXT,
    uf TEXT,
    municipio TEXT,
    situacao TEXT,
    data_publicacao DATE,
    data_abertura_proposta TIMESTAMPTZ,
    data_encerramento_proposta TIMESTAMPTZ,
    data_resultado TIMESTAMPTZ,
    numero_itens INT,
    numero_processo TEXT,
    srp BOOLEAN DEFAULT FALSE,
    dados_brutos JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vincula licitação aos perfis que a encontraram
CREATE TABLE IF NOT EXISTS licitacao_perfil (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    licitacao_id UUID REFERENCES licitacoes(id) ON DELETE CASCADE,
    perfil_id UUID REFERENCES perfis_busca(id) ON DELETE CASCADE,
    termo_encontrado TEXT,
    score_match FLOAT,
    UNIQUE(licitacao_id, perfil_id)
);

-- Status de cada licitação no pipeline do usuário
CREATE TABLE IF NOT EXISTS licitacao_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    licitacao_id UUID REFERENCES licitacoes(id) ON DELETE CASCADE UNIQUE,
    status TEXT DEFAULT 'nova',
    prioridade TEXT DEFAULT 'normal',
    notas TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Histórico de buscas para aprendizado
CREATE TABLE IF NOT EXISTS historico_buscas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    perfil_id UUID REFERENCES perfis_busca(id) ON DELETE CASCADE,
    termo_usado TEXT,
    total_resultados INT,
    resultados_uteis INT DEFAULT 0,
    data_busca TIMESTAMPTZ DEFAULT NOW()
);

-- Termos sugeridos pelo sistema
CREATE TABLE IF NOT EXISTS termos_sugeridos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    perfil_id UUID REFERENCES perfis_busca(id) ON DELETE CASCADE,
    termo_sugerido TEXT,
    frequencia INT DEFAULT 1,
    aceito BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- DADOS INICIAIS — Categorias e Perfis
-- ============================================

INSERT INTO categorias (nome, icone, cor) VALUES
    ('Produtos', '📦', '#E50914'),
    ('Obras', '🏗️', '#FF6B00'),
    ('Reformas', '🔧', '#0D7377');

-- Perfis de Produtos
INSERT INTO perfis_busca (categoria_id, nome, descricao) VALUES
    ((SELECT id FROM categorias WHERE nome = 'Produtos'), 'Lousa de Vidro', 'Lousas, quadros e painéis de vidro'),
    ((SELECT id FROM categorias WHERE nome = 'Produtos'), 'Tintas', 'Tintas látex, acrílica, PVA e correlatos'),
    ((SELECT id FROM categorias WHERE nome = 'Produtos'), 'Óleo e Lubrificantes', 'Óleos lubrificantes, minerais e correlatos');

-- Perfis de Obras
INSERT INTO perfis_busca (categoria_id, nome, descricao) VALUES
    ((SELECT id FROM categorias WHERE nome = 'Obras'), 'Drenagem', 'Obras de drenagem pluvial e urbana'),
    ((SELECT id FROM categorias WHERE nome = 'Obras'), 'Barragem', 'Construção e manutenção de barragens e açudes'),
    ((SELECT id FROM categorias WHERE nome = 'Obras'), 'Quadras Esportivas', 'Construção e reforma de quadras poliesportivas');

-- Perfis de Reformas
INSERT INTO perfis_busca (categoria_id, nome, descricao) VALUES
    ((SELECT id FROM categorias WHERE nome = 'Reformas'), 'Reforma de Fachada', 'Retrofit, revitalização e pintura de fachadas'),
    ((SELECT id FROM categorias WHERE nome = 'Reformas'), 'Pintura Predial', 'Pintura e manutenção predial geral');

-- ============================================
-- TERMOS DE BUSCA INICIAIS
-- ============================================

-- Lousa de Vidro
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'lousa de vidro'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'quadro de vidro'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'painel de vidro'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'lousa temperada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'quadro branco vidro'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Lousa de Vidro'), 'lousa magnética');

-- Tintas
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta latex'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta acrílica'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta pva'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta para parede'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta imobiliária'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Tintas'), 'tinta para pintura');

-- Óleo e Lubrificantes
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Óleo e Lubrificantes'), 'óleo lubrificante'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Óleo e Lubrificantes'), 'óleo mineral'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Óleo e Lubrificantes'), 'óleo para motor'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Óleo e Lubrificantes'), 'lubrificante');

-- Drenagem
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'drenagem'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'drenagem pluvial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'drenagem urbana'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'galeria pluvial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'rede pluvial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'bueiro'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'canalização'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'microdrenagem'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Drenagem'), 'macrodrenagem');

-- Barragem
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'barragem'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'barramento'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'açude'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'reservatório'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'contenção de água'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Barragem'), 'barragem de terra');

-- Quadras Esportivas
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'construção de quadra'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'quadra poliesportiva'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'quadra esportiva'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'quadra coberta'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'reforma de quadra'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Quadras Esportivas'), 'quadra de esportes');

-- Reforma de Fachada
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'reforma de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'retrofit de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'revitalização de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'recuperação de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'revestimento de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'pintura de fachada'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Reforma de Fachada'), 'fachada predial');

-- Pintura Predial
INSERT INTO termos_busca (perfil_id, termo) VALUES
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'pintura predial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'reforma predial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'manutenção predial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'revitalização predial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'restauração predial'),
    ((SELECT id FROM perfis_busca WHERE nome = 'Pintura Predial'), 'pintura externa');

-- ============================================
-- RLS (Row Level Security) — Desabilitar para simplificar
-- ============================================
ALTER TABLE categorias ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfis_busca ENABLE ROW LEVEL SECURITY;
ALTER TABLE termos_busca ENABLE ROW LEVEL SECURITY;
ALTER TABLE licitacoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE licitacao_perfil ENABLE ROW LEVEL SECURITY;
ALTER TABLE licitacao_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico_buscas ENABLE ROW LEVEL SECURITY;
ALTER TABLE termos_sugeridos ENABLE ROW LEVEL SECURITY;

-- Políticas públicas (acesso total via anon key — app pessoal)
CREATE POLICY "allow_all" ON categorias FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON perfis_busca FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON termos_busca FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON licitacoes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON licitacao_perfil FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON licitacao_status FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON historico_buscas FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all" ON termos_sugeridos FOR ALL USING (true) WITH CHECK (true);
