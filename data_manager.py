"""
Data Manager Module
Gestisce il caricamento, salvataggio, importazione ed esportazione dei dati di sessione
"""

import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any
import streamlit as st


class DataManager:
    """Gestisce tutte le operazioni sui dati dell'applicazione"""
    
    @staticmethod
    def initialize_session_state():
        """Inizializza lo stato di sessione con valori di default"""
        if 'transactions' not in st.session_state:
            st.session_state.transactions = []
        
        if 'goals' not in st.session_state:
            st.session_state.goals = []
        
        if 'investments' not in st.session_state:
            st.session_state.investments = []
        
        if 'categories' not in st.session_state:
            st.session_state.categories = {
                'Alimentari': {'budget': 400, 'spent': 0},
                'Ristoranti': {'budget': 150, 'spent': 0},
                'Trasporti': {'budget': 100, 'spent': 0},
                'Utenze': {'budget': 200, 'spent': 0},
                'Intrattenimento': {'budget': 100, 'spent': 0},
                'Salute': {'budget': 80, 'spent': 0},
                'Shopping': {'budget': 150, 'spent': 0},
                'Altro': {'budget': 50, 'spent': 0}
            }
        
        if 'user_name' not in st.session_state:
            st.session_state.user_name = ''
        
        if 'language' not in st.session_state:
            st.session_state.language = 'it'
    
    @staticmethod
    def add_transaction(amount: float, category: str, date: str, 
                       description: str, transaction_type: str):
        """Aggiunge una nuova transazione"""
        transaction = {
            'id': len(st.session_state.transactions) + 1,
            'date': date,
            'amount': amount,
            'category': category,
            'description': description,
            'type': transaction_type  # 'income' o 'expense'
        }
        st.session_state.transactions.append(transaction)
        
        # Aggiorna la spesa per categoria se è un'uscita
        if transaction_type == 'expense' and category in st.session_state.categories:
            st.session_state.categories[category]['spent'] += amount
    
    @staticmethod
    def add_goal(title: str, target_amount: float, current_amount: float, 
                 target_date: str):
        """Aggiunge un nuovo obiettivo finanziario"""
        goal = {
            'id': len(st.session_state.goals) + 1,
            'title': title,
            'target_amount': target_amount,
            'current_amount': current_amount,
            'target_date': target_date,
            'created_date': datetime.now().strftime('%Y-%m-%d')
        }
        st.session_state.goals.append(goal)
    
    @staticmethod
    def add_investment(name: str, value: float, return_pct: float, 
                      investment_type: str):
        """Aggiunge un nuovo investimento"""
        investment = {
            'id': len(st.session_state.investments) + 1,
            'name': name,
            'value': value,
            'return_pct': return_pct,
            'type': investment_type
        }
        st.session_state.investments.append(investment)
    
    @staticmethod
    def get_current_month_balance() -> Dict[str, float]:
        """Calcola il saldo del mese corrente"""
        current_month = datetime.now().strftime('%Y-%m')
        income = 0
        expenses = 0
        
        for transaction in st.session_state.transactions:
            if transaction['date'].startswith(current_month):
                if transaction['type'] == 'income':
                    income += transaction['amount']
                else:
                    expenses += transaction['amount']
        
        return {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }
    
    @staticmethod
    def get_net_worth() -> float:
        """Calcola il patrimonio netto totale"""
        # Somma tutti gli investimenti
        total_investments = sum(inv['value'] for inv in st.session_state.investments)
        
        # Calcola il saldo totale delle transazioni
        total_income = sum(t['amount'] for t in st.session_state.transactions 
                          if t['type'] == 'income')
        total_expenses = sum(t['amount'] for t in st.session_state.transactions 
                            if t['type'] == 'expense')
        
        return total_investments + (total_income - total_expenses)
    
    @staticmethod
    def get_transactions_df() -> pd.DataFrame:
        """Restituisce le transazioni come DataFrame"""
        if not st.session_state.transactions:
            return pd.DataFrame()
        return pd.DataFrame(st.session_state.transactions)
    
    @staticmethod
    def export_to_json() -> str:
        """Esporta i dati di sessione in formato JSON"""
        data = {
            'transactions': st.session_state.transactions,
            'goals': st.session_state.goals,
            'investments': st.session_state.investments,
            'categories': st.session_state.categories,
            'user_name': st.session_state.user_name,
            'export_date': datetime.now().isoformat()
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @staticmethod
    def export_to_csv() -> pd.DataFrame:
        """Esporta le transazioni in formato CSV"""
        return DataManager.get_transactions_df()
    
    @staticmethod
    def import_from_json(json_data: str) -> bool:
        """Importa i dati da JSON"""
        try:
            data = json.loads(json_data)
            
            if 'transactions' in data:
                st.session_state.transactions = data['transactions']
            if 'goals' in data:
                st.session_state.goals = data['goals']
            if 'investments' in data:
                st.session_state.investments = data['investments']
            if 'categories' in data:
                st.session_state.categories = data['categories']
            if 'user_name' in data:
                st.session_state.user_name = data['user_name']
            
            return True
        except Exception as e:
            st.error(f"Errore nell'importazione: {str(e)}")
            return False
    
    @staticmethod
    def get_category_spending() -> Dict[str, float]:
        """Ottiene la spesa per categoria dal mese corrente"""
        current_month = datetime.now().strftime('%Y-%m')
        spending = {}
        
        for transaction in st.session_state.transactions:
            if (transaction['type'] == 'expense' and 
                transaction['date'].startswith(current_month)):
                category = transaction['category']
                spending[category] = spending.get(category, 0) + transaction['amount']
        
        return spending
    
    @staticmethod
    def get_monthly_trend(months: int = 6) -> pd.DataFrame:
        """Ottiene il trend mensile delle entrate/uscite"""
        if not st.session_state.transactions:
            return pd.DataFrame()
        
        df = DataManager.get_transactions_df()
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M')
        
        # Raggruppa per mese e tipo
        monthly = df.groupby(['month', 'type'])['amount'].sum().unstack(fill_value=0)
        
        # Prendi gli ultimi N mesi
        monthly = monthly.tail(months)
        monthly.index = monthly.index.astype(str)
        
        return monthly
