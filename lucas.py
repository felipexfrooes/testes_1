import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import uuid
from datetime import datetime, date, timedelta
import calendar
import random

# ==========================================
# Configuração da Página
# ==========================================
st.set_page_config(
    page_title="Finanças Pro", 
    page_icon="💲", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# Utilitários
# ==========================================
def format_currency(value):
    """Formata valor para o padrão brasileiro."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def get_month_name(month_idx):
    """Retorna o nome do mês em português."""
    meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    return meses[month_idx - 1]

def get_prev_month(current_date):
    """Retorna o dia 1 do mês anterior."""
    primeiro_dia = current_date.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia - timedelta(days=1)
    return ultimo_dia_mes_anterior.replace(day=1)

def get_next_month(current_date):
    """Retorna o dia 1 do próximo mês."""
    dias_no_mes = calendar.monthrange(current_date.year, current_date.month)[1]
    return (current_date + timedelta(days=dias_no_mes)).replace(day=1)

# ==========================================
# Geração de Dados Fictícios
# ==========================================
def generate_mock_data():
    data = []
    hoje = date.today()
    categorias = ['Alimentação', 'Lazer', 'Transporte', 'Saúde', 'Habitação', 'Outros']
    
    for i in range(5, -1, -1):
        # Calcula o mês (voltando i meses)
        # Aproximação simples usando timedelta de 30 dias
        m_date = hoje.replace(day=15) - timedelta(days=30 * i)
        
        # Entrada mensal fixa
        data.append({
            'id': str(uuid.uuid4()),
            'description': 'Salário Mensal',
            'category': 'Receita',
            'amount': 5500.0,
            'type': 'entrada',
            'date': m_date.replace(day=5),
            'paymentMethod': 'pix'
        })

        # Despesa fixa
        data.append({
            'id': str(uuid.uuid4()),
            'description': 'Aluguel / Condomínio',
            'category': 'Habitação',
            'amount': 1800.0,
            'type': 'saida',
            'date': m_date.replace(day=10),
            'paymentMethod': 'pix'
        })

        # Despesas variáveis
        for idx, cat in enumerate(categorias):
            if cat == 'Habitação': continue
            data.append({
                'id': str(uuid.uuid4()),
                'description': f'Gasto com {cat}',
                'category': cat,
                'amount': 80 + (random.random() * 450),
                'type': 'saida',
                'date': m_date.replace(day=12 + idx),
                'paymentMethod': 'cartao' if idx % 2 == 0 else 'dinheiro'
            })
            
    # Ordenar do mais recente para o mais antigo
    return sorted(data, key=lambda x: x['date'], reverse=True)

# ==========================================
# Inicialização do Estado (State)
# ==========================================
if 'transactions' not in st.session_state:
    st.session_state.transactions = generate_mock_data()

if 'current_date' not in st.session_state:
    st.session_state.current_date = date.today().replace(day=1)

# ==========================================
# Processamento de Dados
# ==========================================
df_all = pd.DataFrame(st.session_state.transactions)
df_all['date'] = pd.to_datetime(df_all['date']).dt.date
df_all['ano_mes'] = df_all['date'].apply(lambda x: x.strftime('%Y-%m'))

current_date = st.session_state.current_date
current_ano_mes = current_date.strftime('%Y-%m')

# Filtra transações do mês atual
df_month = df_all[df_all['ano_mes'] == current_ano_mes]

# Cálculos do Mês
entradas_mes = df_month[df_month['type'] == 'entrada']['amount'].sum()
saidas_mes = df_month[df_month['type'] == 'saida']['amount'].sum()
saldo_mes = entradas_mes - saidas_mes

# ==========================================
# Interface do Usuário (UI)
# ==========================================

# --- Cabeçalho e Navegação ---
col_title, col_nav1, col_nav2, col_nav3 = st.columns([4, 1, 2, 1])

with col_title:
    st.markdown("## 💲 Finanças Pro")
    st.caption("Gestão financeira pessoal em Reais (BRL)")

with col_nav1:
    if st.button("⬅️ Anterior", use_container_width=True):
        st.session_state.current_date = get_prev_month(current_date)
        st.rerun()

with col_nav2:
    st.markdown(f"<h4 style='text-align: center; margin-top: 5px;'>{get_month_name(current_date.month)} de {current_date.year}</h4>", unsafe_allow_html=True)

with col_nav3:
    if st.button("Próximo ➡️", use_container_width=True):
        st.session_state.current_date = get_next_month(current_date)
        st.rerun()

st.divider()

# --- Dashboards de Resumo (Cards) ---
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Total de Entradas 📈", value=format_currency(entradas_mes))
with col2:
    st.metric(label="Total de Saídas 📉", value=format_currency(saidas_mes))
with col3:
    # Destacar a cor dependendo do saldo no st.metric não é nativo, então usamos HTML
    color = "#10b981" if saldo_mes >= 0 else "#ef4444"
    st.markdown(f"""
        <div style="background-color:{color}; padding: 15px; border-radius: 10px; color: white;">
            <p style="margin:0; font-size: 14px;">Saldo do Mês</p>
            <h2 style="margin:0; color: white;">{format_currency(saldo_mes)}</h2>
        </div>
    """, unsafe_allow_html=True)

st.write("") # Espaçamento

# --- Gráficos ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("#### 📊 Comparativo Mensal (Últimos 6 meses)")
    
    # Agrupar dados para o gráfico de barras
    df_agrupado = df_all.groupby(['ano_mes', 'type'])['amount'].sum().unstack(fill_value=0).reset_index()
    if 'entrada' not in df_agrupado.columns: df_agrupado['entrada'] = 0
    if 'saida' not in df_agrupado.columns: df_agrupado['saida'] = 0
    
    # Pegar os últimos 6 meses
    df_agrupado = df_agrupado.tail(6)
    
    # Formatar os labels (Ex: Jan/23)
    df_agrupado['label_mes'] = df_agrupado['ano_mes'].apply(
        lambda x: f"{get_month_name(int(x.split('-')[1]))}/{x.split('-')[0][-2:]}"
    )

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=df_agrupado['label_mes'], y=df_agrupado['entrada'], name='Receitas', marker_color='#10b981'))
    fig_bar.add_trace(go.Bar(x=df_agrupado['label_mes'], y=df_agrupado['saida'], name='Despesas', marker_color='#f43f5e'))
    fig_bar.update_layout(barmode='group', margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_bar, use_container_width=True)


with col_chart2:
    st.markdown("#### 🍩 Distribuição por Categoria")
    
    df_saidas_mes = df_month[df_month['type'] == 'saida']
    if not df_saidas_mes.empty:
        df_cat = df_saidas_mes.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(
            df_cat, values='amount', names='category', hole=0.65,
            color_discrete_sequence=['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#64748b']
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0), legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Nenhuma despesa registrada para este período.")

st.divider()

# --- Formulário e Tabela de Histórico ---
col_form, col_table = st.columns([1, 2], gap="large")

with col_form:
    st.markdown("#### ➕ Novo Lançamento")
    with st.form("form_novo_lancamento", clear_on_submit=True):
        desc = st.text_input("Descrição", placeholder="Ex: Almoço, Netflix...")
        
        c1, c2 = st.columns(2)
        amount = c1.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        t_date = c2.date_input("Data", value=date.today())
        
        tipo = st.radio("Tipo de Operação", options=['Despesa', 'Receita'], horizontal=True)
        
        if tipo == 'Despesa':
            cat = st.selectbox("Categoria", ['Alimentação', 'Habitação', 'Transporte', 'Lazer', 'Saúde', 'Educação', 'Outros'])
        else:
            cat = 'Receita'
            
        pagamento = st.selectbox("Forma de Pagamento", ['Pix', 'Cartão de Crédito', 'Dinheiro', 'Boleto'])
        
        submitted = st.form_submit_button("Registrar Lançamento", use_container_width=True)
        
        if submitted and desc and amount:
            novo_lancamento = {
                'id': str(uuid.uuid4()),
                'description': desc,
                'category': cat,
                'amount': amount,
                'type': 'saida' if tipo == 'Despesa' else 'entrada',
                'date': t_date,
                'paymentMethod': pagamento.lower()
            }
            # Adiciona ao state e força o recarregamento
            st.session_state.transactions.insert(0, novo_lancamento)
            # Reordena por data decrescente
            st.session_state.transactions = sorted(st.session_state.transactions, key=lambda x: x['date'], reverse=True)
            st.rerun()

with col_table:
    st.markdown(f"#### 📅 Lançamentos do Mês ({len(df_month)} registros)")
    
    if not df_month.empty:
        # Loop para renderizar as linhas com botão de exclusão
        for _, row in df_month.iterrows():
            with st.container():
                r1, r2, r3, r4 = st.columns([2, 4, 3, 1])
                
                # Data
                r1.markdown(f"<span style='color: gray; font-size: 14px;'>{row['date'].strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
                
                # Descrição e Tags
                method_icon = "💳" if "cartao" in row['paymentMethod'] else "💰" if "dinheiro" in row['paymentMethod'] else "💠"
                r2.markdown(f"**{row['description']}**<br><span style='font-size: 11px; background:#e0e7ff; color:#4f46e5; padding:2px 6px; border-radius:4px;'>{row['category']}</span> <span style='font-size: 11px; color:gray;'>{method_icon} {row['paymentMethod'].upper()}</span>", unsafe_allow_html=True)
                
                # Valor
                cor_valor = "green" if row['type'] == 'entrada' else "red"
                sinal = "+" if row['type'] == 'entrada' else "-"
                r3.markdown(f"<div style='text-align: right; color: {cor_valor}; font-weight: bold;'>{sinal} {format_currency(row['amount'])}</div>", unsafe_allow_html=True)
                
                # Botão Excluir
                if r4.button("🗑️", key=f"del_{row['id']}", help="Excluir lançamento"):
                    # Remove do estado
                    st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != row['id']]
                    st.rerun()
                
                st.markdown("<hr style='margin: 5px 0px; opacity: 0.2;'>", unsafe_allow_html=True)
    else:
        st.info(f"Nenhum lançamento encontrado para {get_month_name(current_date.month)}.")