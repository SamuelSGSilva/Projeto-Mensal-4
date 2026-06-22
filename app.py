import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="Dashboard CENIPA", layout="wide", page_icon="✈️")

st.title("✈️ Painel de Monitoramento de Segurança Aérea")
st.markdown("Dashboard interativo construído a partir dos dados do Projeto Mensal 3.")
st.caption("**Fonte dos dados:** Centro de Investigação e Prevenção de Acidentes Aeronáuticos (CENIPA).")

# Carregamento da Base de Dados
@st.cache_data(show_spinner="Carregando dados...")
def load_data():
    df = pd.read_excel('dataset_pm3_preparado.xlsx') 
    
    if 'ocorrencia_dia' in df.columns:
        df['ocorrencia_dia'] = pd.to_datetime(df['ocorrencia_dia'], errors='coerce')
        df['Ano'] = df['ocorrencia_dia'].dt.year
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros Interativos")

# Filtro de Ano
anos = df['Ano'].dropna().astype(int).unique() if 'Ano' in df.columns else []
ano_selecionado = st.sidebar.multiselect("Selecione o(s) Ano(s):", sorted(anos))

# Filtro de Estado
estados = df['ocorrencia_uf'].dropna().unique() if 'ocorrencia_uf' in df.columns else []
estado_selecionado = st.sidebar.multiselect("Selecione a(s) UF(s):", sorted(estados))

# NOVIDADE 1: Filtro de Classificação
classificacoes = df['ocorrencia_classificacao'].dropna().unique() if 'ocorrencia_classificacao' in df.columns else []
class_selecionada = st.sidebar.multiselect("Selecione a Gravidade:", sorted(classificacoes))

# Aplicação dos filtros no dataframe
df_filtrado = df.copy()
if ano_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Ano'].isin(ano_selecionado)]
if estado_selecionado:
    df_filtrado = df_filtrado[df_filtrado['ocorrencia_uf'].isin(estado_selecionado)]
if class_selecionada:
    df_filtrado = df_filtrado[df_filtrado['ocorrencia_classificacao'].isin(class_selecionada)]

st.divider()

# --- INDICADORES (KPIs) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Total de Ocorrências (Filtradas)", value=f"{len(df_filtrado):,}".replace(',', '.'))
with col2:
    estado_top = df_filtrado['ocorrencia_uf'].mode()[0] if not df_filtrado.empty and 'ocorrencia_uf' in df_filtrado.columns else "N/A"
    st.metric(label="Estado com Mais Registros", value=estado_top)
with col3:
    class_top = df_filtrado['ocorrencia_classificacao'].mode()[0] if not df_filtrado.empty and 'ocorrencia_classificacao' in df_filtrado.columns else "N/A"
    st.metric(label="Classificação Mais Comum", value=class_top)

st.divider()

# --- GRÁFICOS (VISUALIZAÇÕES) ---
colA, colB = st.columns(2)

with colA:
    # Gráfico 1: Evolução Temporal
    if 'Ano' in df_filtrado.columns:
        df_ano = df_filtrado.groupby('Ano').size().reset_index(name='Contagem')
        fig_ano = px.line(df_ano, x='Ano', y='Contagem', title='1. Evolução Temporal das Ocorrências', markers=True)
        st.plotly_chart(fig_ano, use_container_width=True)
        
    # Gráfico 3: Tipo de Aeronave
    if 'aeronave_equipamento' in df_filtrado.columns:
        df_equip = df_filtrado['aeronave_equipamento'].value_counts().reset_index()
        df_equip.columns = ['Equipamento', 'Contagem']
        fig_equip = px.bar(df_equip.head(8), x='Equipamento', y='Contagem', title='3. Ocorrências por Tipo de Aeronave')
        st.plotly_chart(fig_equip, use_container_width=True)
        
    # NOVIDADE 2: Gráfico de Fases de Operação
    if 'aeronave_fase_operacao' in df_filtrado.columns:
        df_fase = df_filtrado['aeronave_fase_operacao'].value_counts().reset_index()
        df_fase.columns = ['Fase', 'Contagem']
        fig_fase = px.bar(df_fase.head(8), x='Contagem', y='Fase', orientation='h', title='5. Top Fases de Operação (Pouso, Decolagem, etc.)', color_discrete_sequence=['#5D69B1'])
        fig_fase.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_fase, use_container_width=True)

with colB:
    # Gráfico 2: Top Estados
    if 'ocorrencia_uf' in df_filtrado.columns:
        df_uf = df_filtrado['ocorrencia_uf'].value_counts().reset_index()
        df_uf.columns = ['UF', 'Contagem']
        fig_uf = px.bar(df_uf.head(10), x='Contagem', y='UF', orientation='h', title='2. Top 10 Estados (UF) com Mais Ocorrências')
        fig_uf.update_layout(yaxis={'categoryorder':'total ascending'}) 
        st.plotly_chart(fig_uf, use_container_width=True)

    # Gráfico 4: Distribuição da Classificação (Treemap)
    if 'ocorrencia_classificacao' in df_filtrado.columns:
        df_class = df_filtrado['ocorrencia_classificacao'].value_counts().reset_index()
        df_class.columns = ['Classificação', 'Contagem']
        
        fig_class = px.treemap(
            df_class, path=['Classificação'], values='Contagem', 
            title='4. Distribuição da Gravidade', color='Contagem', color_continuous_scale='Blues'
        )
        fig_class.update_traces(textinfo="label+value+percent parent")
        fig_class.update_layout(margin=dict(t=50, l=25, r=25, b=25)) 
        st.plotly_chart(fig_class, use_container_width=True)

# NOVIDADE 3: Tabela de Detalhamento
st.divider()
st.subheader("📋 Detalhamento das Ocorrências (Últimos Registros)")

# Seleciona as colunas mais interessantes para a tabela (verifica se elas existem na base)
colunas_interesse = ['ocorrencia_dia', 'ocorrencia_cidade', 'ocorrencia_uf', 'ocorrencia_classificacao', 'aeronave_equipamento', 'aeronave_fase_operacao']
colunas_presentes = [col for col in colunas_interesse if col in df_filtrado.columns]

if colunas_presentes:
    # Formata a data para ficar bonitinha na tabela (DD/MM/AAAA)
    df_exibicao = df_filtrado[colunas_presentes].copy()
    if 'ocorrencia_dia' in df_exibicao.columns:
        df_exibicao['ocorrencia_dia'] = df_exibicao['ocorrencia_dia'].dt.strftime('%d/%m/%Y')
        
    st.dataframe(df_exibicao.head(100), use_container_width=True, hide_index=True)
