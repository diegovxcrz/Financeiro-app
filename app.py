import streamlit as st
import pandas as pd
import plotly.express as px
from ofxparse import OfxParser
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("Controle financeiro")

# Inicializar histórico na sessão
if 'transacoes' not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor'])

# --- SIDEBAR: IMPORTAÇÃO E CADASTRO MANUAL ---
st.sidebar.header("📥 Importar Extrato Bancário")
uploaded_file = st.sidebar.file_uploader("Envie um ficheiro .ofx ou .csv", type=['ofx', 'csv'])

if uploaded_file is not None:
    novas_transacoes = []
    
    if uploaded_file.name.endswith('.ofx'):
        ofx = OfxParser.parse(uploaded_file)
        account = ofx.account
        statement = account.statement
        for transaction in statement.transactions:
            novas_transacoes.append({
                'Data': transaction.date.strftime('%Y-%m-%d'),
                'Descrição': transaction.memo or transaction.payee or 'Lançamento Banco',
                'Categoria': 'Outros',
                'Tipo': 'Entrada' if transaction.amount > 0 else 'Saída',
                'Valor': abs(float(transaction.amount))
            })
    elif uploaded_file.name.endswith('.csv'):
        df_csv = pd.read_csv(uploaded_file)
        # Ajuste as colunas de acordo com o padrão do seu banco
        st.sidebar.info("Certifique-se de que o CSV tem as colunas: Data, Descrição, Valor")

    if novas_transacoes:
        df_novas = pd.DataFrame(novas_transacoes)
        if st.sidebar.button("Confirmar Importação"):
            st.session_state.transacoes = pd.concat([st.session_state.transacoes, df_novas], ignore_index=True).drop_duplicates()
            st.sidebar.success(f"{len(df_novas)} transações importadas!")

# Formulário para adição manual
st.sidebar.markdown("---")
st.sidebar.header("➕ Nova Transação Manual")
with st.sidebar.form("form_transacao", clear_on_submit=True):
    desc = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
    categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Lazer", "Salário", "Outros"])
    data = st.date_input("Data", datetime.now())
    
    submitted = st.form_submit_button("Guardar Transação")
    if submitted and desc and valor > 0:
        nova_row = pd.DataFrame([{
            'Data': data.strftime('%Y-%m-%d'),
            'Descrição': desc,
            'Categoria': categoria,
            'Tipo': tipo,
            'Valor': valor
        }])
        st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova_row], ignore_index=True)
        st.sidebar.success("Adicionado com sucesso!")

# --- PAINEL PRINCIPAL ---
df = st.session_state.transacoes

# Métricas Principais
total_entradas = df[df['Tipo'] == 'Entrada']['Valor'].sum() if not df.empty else 0.0
total_saidas = df[df['Tipo'] == 'Saída']['Valor'].sum() if not df.empty else 0.0
saldo = total_entradas - total_saidas

col1, col2, col3 = st.columns(3)
col1.metric("Total Entradas", f"R$ {total_entradas:,.2f}")
col2.metric("Total Saídas", f"R$ {total_saidas:,.2f}")
col3.metric("Saldo Atual", f"R$ {saldo:,.2f}", delta=f"R$ {saldo:,.2f}")

st.markdown("---")

# Gráficos e Tabelas
if not df.empty:
    col_graf1, col_graf2 = st.columns(2)
    
    with col_graf1:
        st.subheader("📊 Comparativo Entradas vs Saídas")
        fig_bar = px.bar(df.groupby('Tipo')['Valor'].sum().reset_index(), x='Tipo', y='Valor', color='Tipo',
                         color_discrete_map={'Entrada': '#10b981', 'Saída': '#ef4444'})
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_graf2:
        st.subheader("🍕 Saídas por Categoria")
        df_saidas = df[df['Tipo'] == 'Saída']
        if not df_saidas.empty:
            fig_pie = px.pie(df_saidas, names='Categoria', values='Valor', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sem saídas registradas para exibir o gráfico.")

    st.subheader("📋 Extrato de Transações")
    st.dataframe(df.sort_values(by='Data', ascending=False), use_container_width=True)
else:
    st.info("Nenhuma transação registada. Importe um ficheiro OFX/CSV ou adicione manualmente no menu lateral.")

    import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ofxparse import OfxParser
import datetime

# Configuração do tema
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class ControleFinanceiro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Controle Financeiro")
        self.geometry("1200x800")
        self.configure(fg_color="#0b1329")  # Fundo azul-escuro igual da imagem

        # Dados das transações
        self.transacoes = pd.DataFrame(columns=['Data', 'Descrição', 'Categoria', 'Tipo', 'Valor'])

        self.criar_interface()

    def criar_interface(self):
        # --- HEADER / TOPO ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=15)

        # Título e Subtítulo
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")
        
        lbl_titulo = ctk.CTkLabel(title_box, text="Controle Financeiro", font=("Segoe UI", 22, "bold"), text_color="#22c55e")
        lbl_titulo.pack(anchor="w")
        lbl_sub = ctk.CTkLabel(title_box, text="Seu Controle Financeiro Simples e Eficiente", font=("Segoe UI", 12), text_color="#94a3b8")
        lbl_sub.pack(anchor="w")

        # Botões do Topo
        btn_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_box.pack(side="right")

        btn_importar = ctk.CTkButton(btn_box, text="📥 Importar Banco (OFX/CSV)", fg_color="#2563eb", hover_color="#1d4ed8", font=("Segoe UI", 13, "bold"), command=self.importar_arquivo)
        btn_importar.pack(side="left", padx=5)

        btn_nova = ctk.CTkButton(btn_box, text="+ Nova Transação", fg_color="#10b981", hover_color="#059669", text_color="#022c22", font=("Segoe UI", 13, "bold"), command=self.abrir_modal_nova)
        btn_nova.pack(side="left", padx=5)

        # --- CARDS DE RESUMO ---
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)

        # Total Entradas
        card_in = ctk.CTkFrame(cards_frame, fg_color="#131f37", border_color="#10b981", border_width=1, corner_radius=12)
        card_in.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card_in, text="TOTAL ENTRADAS", font=("Segoe UI", 11, "bold"), text_color="#94a3b8").pack(anchor="w", padx=15, pady=(15,0))
        self.lbl_entradas = ctk.CTkLabel(card_in, text="R$ 0,00", font=("Segoe UI", 24, "bold"), text_color="#10b981")
        self.lbl_entradas.pack(anchor="w", padx=15, pady=(5,15))

        # Total Saídas
        card_out = ctk.CTkFrame(cards_frame, fg_color="#131f37", border_color="#ef4444", border_width=1, corner_radius=12)
        card_out.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card_out, text="TOTAL SAÍDAS", font=("Segoe UI", 11, "bold"), text_color="#94a3b8").pack(anchor="w", padx=15, pady=(15,0))
        self.lbl_saidas = ctk.CTkLabel(card_out, text="R$ 0,00", font=("Segoe UI", 24, "bold"), text_color="#ef4444")
        self.lbl_saidas.pack(anchor="w", padx=15, pady=(5,15))

        # Saldo Total
        card_saldo = ctk.CTkFrame(cards_frame, fg_color="#131f37", border_color="#3b82f6", border_width=1, corner_radius=12)
        card_saldo.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card_saldo, text="SALDO NO PERÍODO", font=("Segoe UI", 11, "bold"), text_color="#94a3b8").pack(anchor="w", padx=15, pady=(15,0))
        self.lbl_saldo = ctk.CTkLabel(card_saldo, text="R$ 0,00", font=("Segoe UI", 24, "bold"), text_color="#ffffff")
        self.lbl_saldo.pack(anchor="w", padx=15, pady=(5,15))

        # --- ÁREA DOS GRÁFICOS ---
        charts_frame = ctk.CTkFrame(self, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Container Gráfico 1 - Comparativo
        self.card_g1 = ctk.CTkFrame(charts_frame, fg_color="#131f37", corner_radius=12)
        self.card_g1.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(self.card_g1, text="📊 Comparativo: Entradas vs Saídas", font=("Segoe UI", 14, "bold"), text_color="#f8fafc").pack(anchor="w", padx=15, pady=10)

        # Container Gráfico 2 - Categorias
        self.card_g2 = ctk.CTkFrame(charts_frame, fg_color="#131f37", corner_radius=12)
        self.card_g2.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(self.card_g2, text="🍕 Despesas por Categoria", font=("Segoe UI", 14, "bold"), text_color="#f8fafc").pack(anchor="w", padx=15, pady=10)

        self.atualizar_graficos()

    def importar_arquivo(self):
        caminho = filedialog.askopenfilename(filetypes=[("Arquivos de Extrato", "*.ofx *.csv")])
        if not caminho:
            return

        novas = []
        try:
            if caminho.lower().endswith('.ofx'):
                with open(caminho, 'rb') as f:
                    ofx = OfxParser.parse(f)
                    for t in ofx.account.statement.transactions:
                        tipo = 'Entrada' if t.amount > 0 else 'Saída'
                        novas.append({
                            'Data': t.date.strftime('%Y-%m-%d'),
                            'Descrição': t.memo or t.payee or 'Lançamento Banco',
                            'Categoria': 'Outros',
                            'Tipo': tipo,
                            'Valor': abs(float(t.amount))
                        })
            elif caminho.lower().endswith('.csv'):
                df_csv = pd.read_csv(caminho)
                # Tenta mapear colunas comuns
                for _, row in df_csv.iterrows():
                    val = float(row.get('Valor', 0))
                    novas.append({
                        'Data': str(row.get('Data', datetime.date.today())),
                        'Descrição': str(row.get('Descrição', 'Lançamento CSV')),
                        'Categoria': str(row.get('Categoria', 'Outros')),
                        'Tipo': 'Entrada' if val >= 0 else 'Saída',
                        'Valor': abs(val)
                    })

            if novas:
                df_novas = pd.DataFrame(novas)
                self.transacoes = pd.concat([self.transacoes, df_novas], ignore_index=True)
                messagebox.showinfo("Sucesso", f"{len(novas)} transações importadas!")
                self.atualizar_tela()
        except Exception as e:
            messagebox.showerror("Erro ao Importar", f"Não foi possível ler o arquivo:\n{e}")

    def abrir_modal_nova(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Nova Transação")
        modal.geometry("380x420")
        modal.grab_set()

        ctk.CTkLabel(modal, text="Nova Transação", font=("Segoe UI", 16, "bold")).pack(pady=15)

        ent_desc = ctk.CTkEntry(modal, placeholder_text="Descrição (ex: Supermercado)")
        ent_desc.pack(fill="x", padx=20, pady=8)

        ent_valor = ctk.CTkEntry(modal, placeholder_text="Valor (R$)")
        ent_valor.pack(fill="x", padx=20, pady=8)

        combo_tipo = ctk.CTkOptionMenu(modal, values=["Saída", "Entrada"])
        combo_tipo.pack(fill="x", padx=20, pady=8)

        combo_cat = ctk.CTkOptionMenu(modal, values=["Alimentação", "Transporte", "Moradia", "Lazer", "Outros"])
        combo_cat.pack(fill="x", padx=20, pady=8)

        def salvar():
            try:
                desc = ent_desc.get()
                val = float(ent_valor.get().replace(',', '.'))
                tipo = combo_tipo.get()
                cat = combo_cat.get()
                data = datetime.date.today().strftime('%Y-%m-%d')

                nova = pd.DataFrame([{
                    'Data': data,
                    'Descrição': desc,
                    'Categoria': cat,
                    'Tipo': tipo,
                    'Valor': val
                }])
                self.transacoes = pd.concat([self.transacoes, nova], ignore_index=True)
                self.atualizar_tela()
                modal.destroy()
            except ValueError:
                messagebox.showerror("Erro", "Insira um valor numérico válido.")

        ctk.CTkButton(modal, text="Salvar", fg_color="#10b981", hover_color="#059669", command=salvar).pack(pady=20)

    def atualizar_tela(self):
        df = self.transacoes
        tot_in = df[df['Tipo'] == 'Entrada']['Valor'].sum() if not df.empty else 0.0
        tot_out = df[df['Tipo'] == 'Saída']['Valor'].sum() if not df.empty else 0.0
        saldo = tot_in - tot_out

        self.lbl_entradas.configure(text=f"R$ {tot_in:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.lbl_saidas.configure(text=f"R$ {tot_out:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        self.lbl_saldo.configure(text=f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        self.atualizar_graficos()

    def atualizar_graficos(self):
        # Limpar gráficos anteriores
        for widget in self.card_g1.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()
        for widget in self.card_g2.winfo_children():
            if isinstance(widget, FigureCanvasTkAgg):
                widget.get_tk_widget().destroy()

        df = self.transacoes

        # --- GRÁFICO 1: BARRAS (Entradas vs Saídas) ---
        fig1, ax1 = plt.subplots(figsize=(4, 3), facecolor='#131f37')
        ax1.set_facecolor('#131f37')

        tot_in = df[df['Tipo'] == 'Entrada']['Valor'].sum() if not df.empty else 0
        tot_out = df[df['Tipo'] == 'Saída']['Valor'].sum() if not df.empty else 0

        bars = ax1.bar(['Entradas', 'Saídas'], [tot_in, tot_out], color=['#10b981', '#ef4444'], width=0.5)
        ax1.tick_params(colors='white', labelsize=9)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['left'].set_color('#334155')
        ax1.spines['bottom'].set_color('#334155')

        canvas1 = FigureCanvasTkAgg(fig1, master=self.card_g1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # --- GRÁFICO 2: ROSCA (Despesas por Categoria) ---
        fig2, ax2 = plt.subplots(figsize=(4, 3), facecolor='#131f37')
        ax2.set_facecolor('#131f37')

        df_saidas = df[df['Tipo'] == 'Saída']
        if not df_saidas.empty:
            cat_data = df_saidas.groupby('Categoria')['Valor'].sum()
            colors = ['#f59e0b', '#3b82f6', '#10b981', '#8b5cf6', '#ec4899']
            wedges, texts, autotexts = ax2.pie(
                cat_data, labels=cat_data.index, autopct='%1.0f%%',
                colors=colors[:len(cat_data)], startangle=90,
                textprops=dict(color="white", fontsize=8), wedgeprops=dict(width=0.4, edgecolor='#131f37')
            )
        else:
            ax2.text(0.5, 0.5, 'Sem Saídas', color='#94a3b8', ha='center', va='center')

        canvas2 = FigureCanvasTkAgg(fig2, master=self.card_g2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

if __name__ == "__main__":
    app = ControleFinanceiro()
    app.mainloop()