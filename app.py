"""
Personal Finance Manager - Streamlit App
Applicazione one-page per la gestione finanziaria personale
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta
from data_manager import DataManager

# Configurazione pagina
st.set_page_config(
    page_title="Finance Manager",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato per design professionale
st.markdown("""
<style>
    /* Rimuovi padding superiore */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Stile per le metriche */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }
    
    /* Card per obiettivi */
    .goal-card {
        padding: 1.5rem;
        border-radius: 8px;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-bottom: 1rem;
    }
    
    /* Stile tabelle */
    .dataframe {
        font-size: 14px;
    }
    
    /* Header professionale */
    .header-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    
    /* Bottoni */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 12px 24px;
        font-weight: 500;
    }
    
    /* Progress bar personalizzata */
    .stProgress > div > div > div > div {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


class I18N:
    """Gestione localizzazione"""
    
    @staticmethod
    def load_translations(lang='it'):
        """Carica il file di traduzione"""
        try:
            with open(f'i18n/{lang}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback a italiano
            with open('i18n/it.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    
    @staticmethod
    def get(translations, key_path):
        """Recupera una traduzione usando notazione punto"""
        keys = key_path.split('.')
        value = translations
        for key in keys:
            value = value.get(key, key_path)
        return value


def render_header(t):
    """Render ZONA 1: Header con metriche principali"""
    
    # Nome utente
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(t['app_title'])
    with col2:
        # Selettore lingua
        lang_options = {'Italiano': 'it', 'English': 'en', 'Deutsch': 'de'}
        selected_lang = st.selectbox(
            t['language_label'],
            options=list(lang_options.keys()),
            index=list(lang_options.values()).index(st.session_state.language),
            label_visibility="collapsed"
        )
        st.session_state.language = lang_options[selected_lang]
    
    # Input nome utente
    user_name = st.text_input(
        "",
        value=st.session_state.user_name,
        placeholder=t['header']['user_name_placeholder'],
        key="user_name_input"
    )
    st.session_state.user_name = user_name
    
    st.markdown("---")
    
    # Calcola metriche
    net_worth = DataManager.get_net_worth()
    monthly = DataManager.get_current_month_balance()
    monthly_balance = monthly['balance']
    
    # Calcola progresso obiettivi
    total_goals = len(st.session_state.goals)
    active_goals = sum(1 for g in st.session_state.goals 
                      if g['current_amount'] < g['target_amount'])
    
    # Metriche principali
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            t['header']['net_worth'],
            f"€ {net_worth:,.2f}",
            delta=None
        )
    
    with col2:
        delta_color = "normal" if monthly_balance >= 0 else "inverse"
        st.metric(
            t['header']['monthly_balance'],
            f"€ {monthly_balance:,.2f}",
            delta=f"€ {abs(monthly_balance):,.2f}" if monthly_balance != 0 else None
        )
    
    with col3:
        st.metric(
            t['header']['goals_progress'],
            f"{total_goals - active_goals}/{total_goals}",
            delta=f"{active_goals} attivi" if active_goals > 0 else "Completati"
        )
    
    with col4:
        monthly_savings = monthly['income'] - monthly['expenses']
        st.metric(
            t['header']['monthly_savings'],
            f"€ {monthly_savings:,.2f}",
            delta=None
        )
    
    with col5:
        savings_rate = (monthly_savings / monthly['income'] * 100) if monthly['income'] > 0 else 0
        st.metric(
            t['header']['savings_rate'],
            f"{savings_rate:.1f}%",
            delta=None
        )
    
    st.markdown("---")


def render_budget_tab(t):
    """Render TAB 1: Budget & Spese"""
    
    st.subheader(t['budget_tab']['title'])
    
    # Layout a due colonne
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Grafico distribuzione spese
        st.markdown(f"**{t['budget_tab']['spending_chart']}**")
        
        spending = DataManager.get_category_spending()
        if spending:
            df_spending = pd.DataFrame([
                {'Categoria': cat, 'Importo': amt}
                for cat, amt in spending.items()
            ])
            
            fig = px.pie(
                df_spending,
                values='Importo',
                names='Categoria',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                showlegend=True,
                height=350,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessuna spesa registrata questo mese")
    
    with col2:
        # Gestione categorie con budget
        st.markdown(f"**{t['budget_tab']['category']} & {t['budget_tab']['progress']}**")
        
        for category, data in st.session_state.categories.items():
            budget = data['budget']
            spent = data['spent']
            remaining = budget - spent
            progress = (spent / budget) if budget > 0 else 0
            
            # Determina colore
            if progress < 0.7:
                color = "🟢"
            elif progress < 1.0:
                color = "🟡"
            else:
                color = "🔴"
            
            st.write(f"{category}")
            
            # Progress bar
            st.progress(min(progress, 1.0))
            
            # Info riga
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.caption(f"Budget: € {budget:.0f}")
            with col_b:
                st.caption(f"Speso: € {spent:.0f}")
            with col_c:
                if remaining >= 0:
                    st.caption(f"Rimanente: € {remaining:.0f}")
                else:
                    st.caption(f"**Oltre: € {abs(remaining):.0f}**")
            
            st.markdown("---")
    
    # Transazioni recenti
    st.markdown(f"### {t['budget_tab']['recent_transactions']}")
    
    df = DataManager.get_transactions_df()
    if not df.empty:
        # Mostra ultime 10 transazioni
        df_recent = df.sort_values('date', ascending=False).head(10)
        df_display = df_recent[['date', 'description', 'category', 'amount', 'type']].copy()
        df_display['amount'] = df_display['amount'].apply(lambda x: f"€ {x:.2f}")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "Data",
                "description": "Descrizione",
                "category": "Categoria",
                "amount": "Importo",
                "type": "Tipo"
            }
        )
    else:
        st.info(t['budget_tab']['no_transactions'])


def render_goals_tab(t):
    """Render TAB 2: Obiettivi Finanziari"""
    
    st.subheader(t['goals_tab']['title'])
    
    # Pulsante aggiungi obiettivo
    if st.button(f"➕ {t['goals_tab']['add_goal']}", use_container_width=False):
        st.session_state.show_goal_form = True
    
    # Form per nuovo obiettivo
    if st.session_state.get('show_goal_form', False):
        with st.form("new_goal_form"):
            st.markdown("#### Nuovo Obiettivo")
            
            col1, col2 = st.columns(2)
            with col1:
                goal_name = st.text_input(t['goals_tab']['goal_name'])
                target_amount = st.number_input(
                    t['goals_tab']['target_amount'],
                    min_value=0.0,
                    step=100.0
                )
            with col2:
                current_amount = st.number_input(
                    t['goals_tab']['current_amount'],
                    min_value=0.0,
                    step=100.0
                )
                target_date = st.date_input(
                    t['goals_tab']['target_date'],
                    min_value=datetime.now()
                )
            
            col_a, col_b = st.columns([1, 4])
            with col_a:
                submitted = st.form_submit_button(t['goals_tab']['create_goal'])
            with col_b:
                if st.form_submit_button(t['common']['cancel']):
                    st.session_state.show_goal_form = False
                    st.rerun()
            
            if submitted and goal_name and target_amount > 0:
                DataManager.add_goal(
                    goal_name,
                    target_amount,
                    current_amount,
                    target_date.strftime('%Y-%m-%d')
                )
                st.session_state.show_goal_form = False
                st.success(t['common']['success'])
                st.rerun()
    
    st.markdown("---")
    
    # Mostra obiettivi
    if st.session_state.goals:
        # Grid di obiettivi
        cols = st.columns(2)
        
        for idx, goal in enumerate(st.session_state.goals):
            with cols[idx % 2]:
                progress = (goal['current_amount'] / goal['target_amount']) * 100
                
                with st.container():
                    st.markdown(f"### {goal['title']}")
                    
                    # Progress bar
                    st.progress(min(progress / 100, 1.0))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Obiettivo", f"€ {goal['target_amount']:,.0f}")
                    with col2:
                        st.metric("Risparmiato", f"€ {goal['current_amount']:,.0f}")
                    with col3:
                        st.metric("Progresso", f"{progress:.1f}%")
                    
                    st.caption(f"Scadenza: {goal['target_date']}")
                    
                    st.markdown("---")
    else:
        st.info(t['goals_tab']['no_goals'])


def render_investments_tab(t):
    """Render TAB 3: Investimenti & Patrimonio"""
    
    st.subheader(t['investments_tab']['title'])
    
    # Pulsante aggiungi investimento
    if st.button(f"➕ {t['investments_tab']['add_investment']}", use_container_width=False):
        st.session_state.show_investment_form = True
    
    # Form per nuovo investimento
    if st.session_state.get('show_investment_form', False):
        with st.form("new_investment_form"):
            st.markdown("#### Nuovo Investimento")
            
            col1, col2 = st.columns(2)
            with col1:
                inv_name = st.text_input(t['investments_tab']['investment_name'])
                inv_value = st.number_input(
                    t['investments_tab']['value'],
                    min_value=0.0,
                    step=100.0
                )
            with col2:
                inv_return = st.number_input(
                    f"{t['investments_tab']['return']} (%)",
                    min_value=-100.0,
                    max_value=1000.0,
                    step=0.1
                )
                inv_type = st.selectbox(
                    t['investments_tab']['type'],
                    options=list(t['investments_tab']['types'].values())
                )
            
            col_a, col_b = st.columns([1, 4])
            with col_a:
                submitted = st.form_submit_button(t['investments_tab']['create_investment'])
            with col_b:
                if st.form_submit_button(t['common']['cancel']):
                    st.session_state.show_investment_form = False
                    st.rerun()
            
            if submitted and inv_name and inv_value > 0:
                DataManager.add_investment(inv_name, inv_value, inv_return, inv_type)
                st.session_state.show_investment_form = False
                st.success(t['common']['success'])
                st.rerun()
    
    st.markdown("---")
    
    # Layout investimenti
    if st.session_state.investments:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Grafico allocazione asset
            st.markdown(f"**{t['investments_tab']['asset_allocation']}**")
            
            df_inv = pd.DataFrame(st.session_state.investments)
            inv_by_type = df_inv.groupby('type')['value'].sum().reset_index()
            
            fig = px.pie(
                inv_by_type,
                values='value',
                names='type',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Metriche totali
            total_value = sum(inv['value'] for inv in st.session_state.investments)
            avg_return = sum(inv['return_pct'] for inv in st.session_state.investments) / len(st.session_state.investments)
            total_return_amount = sum(inv['value'] * inv['return_pct'] / 100 for inv in st.session_state.investments)
            
            st.markdown(f"**{t['investments_tab']['total_value']}**")
            st.metric("", f"€ {total_value:,.2f}")
            
            st.markdown(f"**{t['investments_tab']['total_return']}**")
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Rendimento €", f"€ {total_return_amount:,.2f}")
            with col_b:
                st.metric("Rendimento %", f"{avg_return:.2f}%")
        
        # Tabella investimenti
        st.markdown("---")
        st.markdown("**Lista Investimenti**")
        
        df_display = df_inv[['name', 'type', 'value', 'return_pct']].copy()
        df_display['value'] = df_display['value'].apply(lambda x: f"€ {x:,.2f}")
        df_display['return_pct'] = df_display['return_pct'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Nome",
                "type": "Tipo",
                "value": "Valore",
                "return_pct": "Rendimento"
            }
        )
    else:
        st.info(t['investments_tab']['no_investments'])


def render_analysis_tab(t):
    """Render TAB 4: Analisi e Report"""
    
    st.subheader(t['analysis_tab']['title'])
    
    # Trend mensile
    monthly_trend = DataManager.get_monthly_trend(6)
    
    if not monthly_trend.empty:
        st.markdown(f"**{t['analysis_tab']['monthly_trend']}**")
        
        fig = go.Figure()
        
        if 'income' in monthly_trend.columns:
            fig.add_trace(go.Bar(
                x=monthly_trend.index,
                y=monthly_trend['income'],
                name='Entrate',
                marker_color='#4CAF50'
            ))
        
        if 'expense' in monthly_trend.columns:
            fig.add_trace(go.Bar(
                x=monthly_trend.index,
                y=monthly_trend['expense'],
                name='Uscite',
                marker_color='#f44336'
            ))
        
        fig.update_layout(
            barmode='group',
            height=400,
            xaxis_title="Mese",
            yaxis_title="Importo (€)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t['analysis_tab']['no_data'])
    
    st.markdown("---")
    
    # Sezione Import/Export
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### {t['analysis_tab']['export_data']}")
        
        # Esporta JSON
        if st.button(f"📄 {t['analysis_tab']['export_json']}", use_container_width=True):
            json_data = DataManager.export_to_json()
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"finance_data_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )
        
        # Esporta CSV
        if st.button(f"📊 {t['analysis_tab']['export_csv']}", use_container_width=True):
            df = DataManager.export_to_csv()
            if not df.empty:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"transactions_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Nessuna transazione da esportare")
    
    with col2:
        st.markdown(f"### {t['analysis_tab']['import_data']}")
        
        uploaded_file = st.file_uploader(
            t['analysis_tab']['upload_file'],
            type=['json']
        )
        
        if uploaded_file is not None:
            try:
                json_data = uploaded_file.read().decode('utf-8')
                if DataManager.import_from_json(json_data):
                    st.success(t['analysis_tab']['import_success'])
                    st.rerun()
            except Exception as e:
                st.error(f"{t['analysis_tab']['import_error']}: {str(e)}")


def render_quick_input(t):
    """Render ZONA 3: Input rapido transazione"""
    
    st.markdown("---")
    st.markdown("### Quick Actions")
    
    with st.expander(f"➕ {t['quick_input']['add_transaction']}", expanded=False):
        with st.form("quick_transaction"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                amount = st.number_input(
                    t['quick_input']['amount_label'],
                    min_value=0.0,
                    step=10.0
                )
                trans_type = st.selectbox(
                    t['quick_input']['type_label'],
                    options=['expense', 'income'],
                    format_func=lambda x: t['budget_tab']['expense'] if x == 'expense' else t['budget_tab']['income']
                )
            
            with col2:
                category = st.selectbox(
                    t['quick_input']['category_label'],
                    options=list(st.session_state.categories.keys())
                )
                trans_date = st.date_input(
                    t['quick_input']['date_label'],
                    value=datetime.now()
                )
            
            with col3:
                description = st.text_input(t['quick_input']['description_label'])
            
            submitted = st.form_submit_button(
                t['quick_input']['submit'],
                use_container_width=True
            )
            
            if submitted:
                if amount > 0:
                    DataManager.add_transaction(
                        amount,
                        category,
                        trans_date.strftime('%Y-%m-%d'),
                        description,
                        trans_type
                    )
                    st.success(t['quick_input']['success'])
                    st.rerun()
                else:
                    st.error(t['quick_input']['amount_required'])


def render_insights_sidebar(t):
    """Render ZONA 4: Insights e suggerimenti nella sidebar"""
    
    with st.sidebar:
        st.markdown(f"## {t['insights']['title']}")
        
        alerts = []
        suggestions = []
        celebrations = []
        
        # Controlla budget superati
        for category, data in st.session_state.categories.items():
            budget = data['budget']
            spent = data['spent']
            
            if spent > budget:
                alerts.append(f"{t['insights']['budget_warning']} **{category}** ({spent - budget:.0f}€)")
            elif spent > budget * 0.8:
                alerts.append(f"{t['insights']['budget_near']} **{category}**")
        
        # Controlla obiettivi raggiunti
        for goal in st.session_state.goals:
            if goal['current_amount'] >= goal['target_amount']:
                celebrations.append(f"{t['insights']['goal_achieved']}: **{goal['title']}**!")
        
        # Suggerimenti di risparmio
        spending = DataManager.get_category_spending()
        if spending:
            max_category = max(spending, key=spending.get)
            if spending[max_category] > 200:  # soglia arbitraria
                suggestions.append(f"{t['insights']['savings_tip']} **{max_category}**")
        
        # Mostra insights
        if celebrations:
            st.success("🎉 " + t['insights']['celebrations'])
            for celebration in celebrations:
                st.markdown(f"- {celebration}")
            st.markdown("---")
        
        if alerts:
            st.warning("⚠️ " + t['insights']['alerts'])
            for alert in alerts:
                st.markdown(f"- {alert}")
            st.markdown("---")
        
        if suggestions:
            st.info("💡 " + t['insights']['suggestions'])
            for suggestion in suggestions:
                st.markdown(f"- {suggestion}")
        
        if not alerts and not suggestions and not celebrations:
            st.success(t['insights']['no_alerts'])


def main():
    """Funzione principale dell'app"""
    
    # Inizializza session state
    DataManager.initialize_session_state()
    
    # Carica traduzioni
    t = I18N.load_translations(st.session_state.language)
    
    # ZONA 1: Header
    render_header(t)
    
    # ZONA 2: Dashboard con tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        t['tabs']['budget'],
        t['tabs']['goals'],
        t['tabs']['investments'],
        t['tabs']['analysis']
    ])
    
    with tab1:
        render_budget_tab(t)
    
    with tab2:
        render_goals_tab(t)
    
    with tab3:
        render_investments_tab(t)
    
    with tab4:
        render_analysis_tab(t)
    
    # ZONA 3: Input rapido
    render_quick_input(t)
    
    # ZONA 4: Insights sidebar
    render_insights_sidebar(t)


if __name__ == "__main__":
    main()
