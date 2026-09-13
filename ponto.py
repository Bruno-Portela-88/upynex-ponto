import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from streamlit_autorefresh import st_autorefresh


# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="UPYNEX - Beta 1.0",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS VISUAIS UPYNEX ---
st.markdown("""
    <style>
    [data-testid="collapsedControl"] { display: none; }
    section[data-testid="stSidebar"] { display: none; }
    
    .stApp {
        background-color: #FFFFFF;
        color: #1A1A1A;
        font-family: 'Segoe UI', sans-serif;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0A0A0A;
        letter-spacing: -0.5px;
    }
    .neon-badge {
        background: #00F0FF;
        color: #0A0A0A;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 4px;
        border: 1px solid #39FF14;
        box-shadow: 0 0 8px rgba(0, 240, 255, 0.4);
    }
    .notice-card {
        background-color: #0A0A0A;
        color: #FFFFFF;
        border-left: 5px solid #39FF14;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-box {
        background-color: #F8F9FA;
        border: 1px solid #E5E7EB;
        border-left: 4px solid #00F0FF;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
    }
    .alerta-sucesso {
        background-color: #0A2611;
        border: 1px solid #39FF14;
        color: #39FF14;
        padding: 12px 16px;
        border-radius: 6px;
        font-weight: 600;
        margin-bottom: 15px;
    }
    /* Cores dos Botões Operacionais */
    .btn-entrada button {
        background-color: #0A0A0A !important;
        border: 2px solid #39FF14 !important;
        color: #39FF14 !important;
        font-weight: 700 !important;
    }
    .btn-entrada button:hover {
        background-color: #1a331a !important;
        box-shadow: 0 0 12px rgba(57, 255, 20, 0.4) !important;
    }
    .btn-saida button {
        background-color: #0A0A0A !important;
        border: 2px solid #FF5722 !important;
        color: #FF5722 !important;
        font-weight: 700 !important;
    }
    .btn-saida button:hover {
        background-color: #331f1a !important;
        box-shadow: 0 0 12px rgba(255, 87, 34, 0.4) !important;
    }
    /* Blocos de Tarefas */
    /* Estilo Exclusivo para o Card Interativo de Tarefas */
    .card-tarefa-box button {
        background-color: #F8F9FA !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 6px solid var(--borda-tarefa, #FF4B4B) !important;
        border-radius: 8px !important;
        padding: 12px 14px !important;
        text-align: left !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .card-tarefa-box button:hover {
        background-color: #FFFFFF !important;
        box-shadow: 0 6px 14px rgba(0,0,0,0.1) !important;
        transform: translateY(-2px) !important;
    }
    .card-tarefa-box button p {
        color: #1A202C !important;
        font-weight: 500 !important;
        line-height: 1.4 !important;
        text-align: left !important;
    }
    .task-card-pendente {
        background-color: #2D0A0A;
        border: 2px solid #FF4B4B;
        color: #FFFFFF;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .task-card-andamento {
        background-color: #0A1B2D;
        border: 2px solid #00F0FF;
        color: #FFFFFF;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .task-badge-timer {
        background-color: #1A1A1A;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 6px;
    }
    .stButton>button {
        background-color: #0A0A0A;
        color: #FFFFFF;
        border: 1px solid #00F0FF;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        border-color: #39FF14;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.3);
        color: #39FF14;
    }
    </style>
""", unsafe_allow_html=True)

# --- ESTRUTURA DE ARQUIVOS LOCAIS ---
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
FILE_USERS = os.path.join(DATA_DIR, "usuarios.csv")
FILE_PONTOS = os.path.join(DATA_DIR, "pontos.csv")
FILE_CONFIG = os.path.join(DATA_DIR, "config.csv")
FILE_TAREFAS = os.path.join(DATA_DIR, "tarefas.csv")
FILE_SESSOES = os.path.join(DATA_DIR, "sessoes.csv")
FILE_PAGAMENTOS = os.path.join(DATA_DIR, "pagamentos.csv")

PIN_PADRAO = "123456"

def carregar_dados():
    # 1. Configurações
    if not os.path.exists(FILE_CONFIG):
        df_cfg = pd.DataFrame([
            {"chave": "pin_admin", "valor": "123456"},
            {"chave": "aviso_geral", "valor": "Bem-vindo à plataforma UPYNEX. Mantenha seus registros e tarefas em dia."}
        ])
        df_cfg.to_csv(FILE_CONFIG, index=False)
    else:
        df_cfg = pd.read_csv(FILE_CONFIG, dtype=str)
        if "aviso_geral" not in df_cfg["chave"].values:
            df_cfg = pd.concat([df_cfg, pd.DataFrame([{"chave": "aviso_geral", "valor": "Bem-vindo à plataforma UPYNEX."}])], ignore_index=True)
            df_cfg.to_csv(FILE_CONFIG, index=False)

    # 2. Usuários
    if not os.path.exists(FILE_USERS):
        df_users = pd.DataFrame(columns=[
            "id", "nome", "documento", "tipo_pix", "chave_pix", 
            "valor_hora", "pin", "primeiro_acesso", "novo_pin_solicitado"
        ])
        df_users.to_csv(FILE_USERS, index=False)
    else:
        df_users = pd.read_csv(FILE_USERS, dtype=str)
        for col in ["primeiro_acesso", "novo_pin_solicitado"]:
            if col not in df_users.columns:
                df_users[col] = "sim" if col == "primeiro_acesso" else ""
        df_users.to_csv(FILE_USERS, index=False)

    # 3. Pontos
    if not os.path.exists(FILE_PONTOS):
        df_pontos = pd.DataFrame(columns=["id_colaborador", "data", "tipo", "hora", "minutos_acumulados"])
        df_pontos.to_csv(FILE_PONTOS, index=False)
    else:
        df_pontos = pd.read_csv(FILE_PONTOS, dtype=str)

    # 4. Tarefas
    if not os.path.exists(FILE_TAREFAS):
        df_tarefas = pd.DataFrame(columns=["id", "id_colaborador", "titulo", "descricao", "prazo_limite", "status", "data_envio"])
        df_tarefas.to_csv(FILE_TAREFAS, index=False)
    else:
        df_tarefas = pd.read_csv(FILE_TAREFAS, dtype=str)
        if "prazo_limite" not in df_tarefas.columns:
            df_tarefas["prazo_limite"] = ""
            df_tarefas.to_csv(FILE_TAREFAS, index=False)

    # 5. Sessões e Heartbeats (Agente)
    if not os.path.exists(FILE_SESSOES):
        df_sessoes = pd.DataFrame(columns=["id_colaborador", "ultimo_pulso", "status_conexao", "maquina_id"])
        df_sessoes.to_csv(FILE_SESSOES, index=False)
    else:
        df_sessoes = pd.read_csv(FILE_SESSOES, dtype=str)

    # 6. Pagamentos e Adiantamentos
    if not os.path.exists(FILE_PAGAMENTOS):
        df_pags = pd.DataFrame(columns=["id", "id_colaborador", "data", "hora", "valor_pago", "observacao"])
        df_pags.to_csv(FILE_PAGAMENTOS, index=False)
    else:
        df_pags = pd.read_csv(FILE_PAGAMENTOS, dtype=str)

    return df_users, df_pontos, df_cfg, df_tarefas, df_sessoes, df_pags

df_users, df_pontos, df_cfg, df_tarefas, df_sessoes, df_pags = carregar_dados()

def get_cfg(chave):
    res = df_cfg[df_cfg["chave"] == chave]
    return res["valor"].iloc[0] if not res.empty else ""

def set_cfg(chave, valor):
    global df_cfg
    if chave in df_cfg["chave"].values:
        df_cfg.loc[df_cfg["chave"] == chave, "valor"] = valor
    else:
        df_cfg = pd.concat([df_cfg, pd.DataFrame([{"chave": chave, "valor": valor}])], ignore_index=True)
    df_cfg.to_csv(FILE_CONFIG, index=False)

# --- SENTINELA: CORTE AUTOMÁTICO APÓS 3 MINUTOS SEM PULSO ---
def processar_saidas_automaticas_inatividade():
    global df_pontos, df_sessoes
    if df_pontos.empty or df_sessoes.empty:
        return
    
    agora = datetime.now()
    hoje_str = str(date.today())
    houve_alteracao = False

    for _, row_user in df_users.iterrows():
        u_id = row_user["id"]
        sessao_u = df_sessoes[df_sessoes["id_colaborador"] == u_id]
        
        pts_hoje_u = df_pontos[(df_pontos["id_colaborador"] == u_id) & (df_pontos["data"] == hoje_str)]
        if not pts_hoje_u.empty and pts_hoje_u.iloc[-1]["tipo"] == "Entrada":
            if sessao_u.empty:
                continue
            
            ultimo_pulso_str = sessao_u.iloc[-1]["ultimo_pulso"]
            try:
                dt_pulso = datetime.strptime(str(ultimo_pulso_str).strip(), "%Y-%m-%d %H:%M:%S")
                diferenca_min = (agora - dt_pulso).total_seconds() / 60.0
                
                if diferenca_min >= 3.0:
                    hora_saida_auto = dt_pulso.strftime('%H:%M:%S')
                    novo_ponto_auto = pd.DataFrame([{
                        "id_colaborador": u_id,
                        "data": hoje_str,
                        "tipo": "Saída (Automática - Queda de Sinal)",
                        "hora": hora_saida_auto,
                        "minutos_acumulados": "0"
                    }])
                    df_pontos = pd.concat([df_pontos, novo_ponto_auto], ignore_index=True)
                    
                    idx_sess = sessao_u.index[-1]
                    df_sessoes.at[idx_sess, "status_conexao"] = "desconectado"
                    houve_alteracao = True
            except:
                continue
                
    if houve_alteracao:
        df_pontos.to_csv(FILE_PONTOS, index=False)
        df_sessoes.to_csv(FILE_SESSOES, index=False)

processar_saidas_automaticas_inatividade()

# Controle de Sessão Persistente (Resistente ao F5)
params = st.query_params

if "view" not in st.session_state:
    if "colab" in params:
        st.session_state.view = "colaborador"
        st.session_state.colab_id = params["colab"]
    elif "admin" in params and params["admin"] == "1":
        st.session_state.view = "admin"
        st.session_state.admin_autenticado = True
    else:
        st.session_state.view = "home"

if "colab_id" not in st.session_state:
    st.session_state.colab_id = params.get("colab", None)

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = (params.get("admin") == "1")

# --- MOTOR DE CÁLCULO DE HORAS REAIS ---
def calcular_espelho_diario(df_pts_colab, valor_hora):
    if df_pts_colab.empty:
        return pd.DataFrame(columns=["data", "entradas", "saidas", "horas_decimais", "duracao_formatada", "valor_dia"]), 0.0, 0.0
    
    df_pts_colab = df_pts_colab.sort_values(by=["data", "hora"])
    dias_unicos = df_pts_colab["data"].unique()
    linhas_resumo = []
    minutos_geral = 0
    
    for d in dias_unicos:
        pts_dia = df_pts_colab[df_pts_colab["data"] == d]
        entradas = []
        saidas = []
        minutos_dia = 0
        ultima_entrada = None
        
        for _, row in pts_dia.iterrows():
            tipo = row["tipo"]
            h_str = str(row["hora"]).strip()
            
            try:
                if len(h_str.split(':')) == 3:
                    h_obj = datetime.strptime(h_str, "%H:%M:%S")
                else:
                    h_obj = datetime.strptime(h_str, "%H:%M")
            except:
                continue
                
            if "Entrada" in tipo:
                entradas.append(h_str)
                ultima_entrada = h_obj
            elif "Saída" in tipo:
                saidas.append(h_str)
                if ultima_entrada is not None:
                    diff_min = (h_obj - ultima_entrada).total_seconds() / 60
                    if diff_min > 0:
                        minutos_dia += diff_min
                    ultima_entrada = None
                    
        h_decimais = minutos_dia / 60.0
        val_dia = h_decimais * valor_hora
        minutos_geral += minutos_dia
        
        h_int = int(minutos_dia // 60)
        m_int = int(minutos_dia % 60)
        duracao_str = f"{h_int}h {m_int:02d}m"
        
        linhas_resumo.append({
            "data": d,
            "entradas": " | ".join(entradas) if entradas else "Sem registro",
            "saidas": " | ".join(saidas) if saidas else "Ponto em aberto",
            "horas_decimais": round(h_decimais, 2),
            "duracao_formatada": duracao_str,
            "valor_dia": round(val_dia, 2)
        })
        
    df_resultado = pd.DataFrame(linhas_resumo)
    total_horas = minutos_geral / 60.0
    total_valor = total_horas * valor_hora
    return df_resultado, total_horas, total_valor

# --- JANELA FLUTUANTE CENTRALIZADA (MODAL DE TAREFAS - EXPANDIDO) ---
@st.dialog("Detalhes da Tarefa", width="large")
def modal_detalhes_tarefa(row_tarefa, idx_tarefa):
    st.markdown(f"""
        <div style="font-size: 1.7rem; font-weight: 800; color: #0A0A0A; line-height: 1.2; margin-bottom: 8px;">
            {row_tarefa['titulo']}
        </div>
    """, unsafe_allow_html=True)
    
    timer_txt, is_atrasado = formatar_contagem_regressiva(row_tarefa["prazo_limite"])
    cor_timer = "#D32F2F" if is_atrasado else "#0288D1"
    
    st.markdown(f"**Prazo restante:** <span style='color:{cor_timer}; font-weight:700;'>{timer_txt}</span>", unsafe_allow_html=True)
    if row_tarefa["prazo_limite"]:
        st.caption(f"Limite para entrega: {row_tarefa['prazo_limite']}")
    
    st.write("---")
    st.markdown("##### Orientações Detalhadas")
    
    texto_instrucao = row_tarefa['descricao'] if str(row_tarefa['descricao']).strip() else "Sem orientações adicionais."
    
    # Bloco amplo com tipografia escura (#0A0A0A) e fonte aumentada
    st.markdown(f"""
        <div style="
            background-color: #EBF8FF;
            border-left: 5px solid #00F0FF;
            border-top: 1px solid #BEE3F8;
            border-right: 1px solid #BEE3F8;
            border-bottom: 1px solid #BEE3F8;
            border-radius: 8px;
            padding: 18px 22px;
            color: #0A0A0A;
            font-size: 1.15rem;
            line-height: 1.6;
            font-weight: 500;
            margin-bottom: 12px;
        ">
            {texto_instrucao}
        </div>
    """, unsafe_allow_html=True)
    
    st.caption(f"Atribuída em: {row_tarefa['data_envio']}")
    st.write("---")
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("Marcar como Lida", key=f"dlg_lida_{row_tarefa['id']}", use_container_width=True):
            df_tarefas.at[idx_tarefa, "status"] = "em_andamento"
            df_tarefas.to_csv(FILE_TAREFAS, index=False)
            st.rerun()
    with c_btn2:
        if st.button("✅ Pronto / Feito", key=f"dlg_feita_{row_tarefa['id']}", use_container_width=True):
            df_tarefas.at[idx_tarefa, "status"] = "concluida"
            df_tarefas.to_csv(FILE_TAREFAS, index=False)
            st.rerun()

# --- AUXILIARES: QR CODE E CONTAGEM REGRESSIVA ---
def gerar_qr_pix(chave):
    qr = qrcode.QRCode(version=1, box_size=6, border=2)
    qr.add_data(chave)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def formatar_contagem_regressiva(prazo_str):
    if not prazo_str or str(prazo_str).strip() == "":
        return "Sem prazo estipulado", False
    try:
        dt_prazo = datetime.strptime(prazo_str, "%Y-%m-%d %H:%M")
        agora = datetime.now()
        diff = dt_prazo - agora
        if diff.total_seconds() < 0:
            atraso = abs(diff)
            dias = atraso.days
            horas = atraso.seconds // 3600
            minutos = (atraso.seconds % 3600) // 60
            txt = f"⚠️ Atrasada há {dias}d {horas}h {minutos}m" if dias > 0 else f"⚠️ Atrasada há {horas}h {minutos}m"
            return txt, True
        else:
            dias = diff.days
            horas = diff.seconds // 3600
            minutos = (diff.seconds % 3600) // 60
            txt = f"⏳ Restam {dias}d {horas}h {minutos}m" if dias > 0 else f"⏳ Restam {horas}h {minutos}m"
            return txt, False
    except:
        return "Prazo indefinido", False

# --- GERADOR DE RELATÓRIO PDF OFICIAL COM PAGAMENTOS ---
def gerar_pdf_extrato(nome, documento, chave_pix, mes_ano, df_resumo_diario, total_horas, total_valor, df_pags_mes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    elements = []
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold',
        fontSize=18, leading=22, textColor=colors.HexColor("#0A0A0A")
    )
    elements.append(Paragraph("UPYNEX - Extrato Consolidado de Ponto", title_style))
    elements.append(Paragraph(f"Demonstrativo Oficial de Rendimento Mensal - <b>{mes_ano}</b>", styles['Normal']))
    elements.append(Spacer(1, 15))
    
    info_texto = f"""
    <b>Colaborador:</b> {nome} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Documento:</b> {documento}<br/>
    <b>Chave Pix:</b> {chave_pix} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Data de Emissão:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}
    """
    elements.append(Paragraph(info_texto, styles['Normal']))
    elements.append(Spacer(1, 15))
    
    # 1. Tabela de Pontos
    tabela_dados = [["Data", "Entradas Registradas", "Saídas Registradas", "Horas Efetivas", "Valor (R$)"]]
    if not df_resumo_diario.empty:
        for _, row in df_resumo_diario.iterrows():
            tabela_dados.append([
                row["data"], row["entradas"], row["saidas"], row["duracao_formatada"], f"R$ {row['valor_dia']:.2f}"
            ])
    else:
        tabela_dados.append(["Sem registros", "-", "-", "-", "-"])
    tabela_dados.append(["TOTAL PRODUZIDO BRUTO", "", "", f"{total_horas:.2f} horas", f"R$ {total_valor:.2f}"])
    
    t = Table(tabela_dados, colWidths=[70, 160, 160, 80, 70])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0A0A0A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F8F9FA")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#0A0A0A")),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # 2. Tabela de Pagamentos / Repasses Efetuados
    elements.append(Paragraph("<b>Demonstrativo de Adiantamentos e Pagamentos Efetuados:</b>", styles['Normal']))
    elements.append(Spacer(1, 6))
    
    t_pags_dados = [["Data", "Horário", "Descrição / Observação", "Valor Pago (R$)"]]
    total_pago = 0.0
    if not df_pags_mes.empty:
        for _, r_pg in df_pags_mes.iterrows():
            v_float = float(r_pg["valor_pago"])
            total_pago += v_float
            t_pags_dados.append([r_pg["data"], r_pg["hora"], r_pg["observacao"], f"R$ {v_float:.2f}"])
    else:
        t_pags_dados.append(["Nenhum adiantamento registrado", "-", "-", "R$ 0.00"])
        
    saldo_restante = total_valor - total_pago
    t_pags_dados.append(["TOTAL JÁ REPASSADO", "", "", f"R$ {total_pago:.2f}"])
    t_pags_dados.append(["SALDO RESTANTE A LIQUIDAR", "", "", f"R$ {saldo_restante:.2f}"])
    
    tp = Table(t_pags_dados, colWidths=[80, 70, 240, 150])
    tp.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2D140A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor("#FFF3E0")),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor("#1B5E20")),
    ]))
    elements.append(tp)
    elements.append(Spacer(1, 35))
    
    assinaturas_dados = [
        ["_______________________________________", "_______________________________________"],
        [f"{nome}", "Diretoria UPYNEX"],
        ["Assinatura do Colaborador", "Recibo de Liquidação e Quitação"]
    ]
    t_ass = Table(assinaturas_dados, colWidths=[270, 270])
    t_ass.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor("#4B5563"))
    ]))
    elements.append(t_ass)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

# =========================================================
# TELA 1: DASHBOARD PRINCIPAL (HOME)
# =========================================================
if st.session_state.view == "home":
    st.markdown('<div class="main-title">UPYNEX <span class="neon-badge">BETA 1.0</span></div>', unsafe_allow_html=True)
    st.caption("Painel Central de Produtividade e Pontualidade")
    
    aviso_texto = get_cfg("aviso_geral")
    st.markdown(f"""
        <div class="notice-card">
            <h4 style="margin:0 0 6px 0; color:#39FF14; font-size:1.05rem;">📢 Observações Gerais da Diretoria</h4>
            <p style="margin:0; font-size:0.95rem; line-height:1.4;">{aviso_texto}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Acesso do Colaborador")
    if df_users.empty:
        st.info("Nenhum colaborador registrado. Acesso restrito.")
    else:
        col1, col2 = st.columns([5, 5])
        with col1:
            nome_escolhido = st.selectbox("Selecione seu nome:", df_users["nome"].tolist(), key="home_user_sel")
            user_sel = df_users[df_users["nome"] == nome_escolhido].iloc[0]
        with col2:
            pin_colab = st.text_input("PIN de Acesso (4 a 6 dígitos):", key="login_pin")
            
        if st.button("Entrar no Meu Espaço", use_container_width=True):
            if pin_colab == user_sel["pin"]:
              st.session_state.colab_id = user_sel["id"]
              st.session_state.view = "colaborador"
              st.query_params["colab"] = user_sel["id"]
              st.rerun()
            else:
                st.error("PIN incorreto.")

    st.write("---")
    r_col1, r_col2 = st.columns([2, 8])
    with r_col1:
        with st.popover("⚙️ Administrador"):
            st.markdown("##### Acesso Master")
            pin_adm_input = st.text_input("PIN Master:", key="adm_pin_popup")
            if st.button("Acessar Painel Master"):
                if pin_adm_input == get_cfg("pin_admin"):
                    st.session_state.admin_autenticado = True
                    st.session_state.view = "admin"
                    st.rerun()
                else:
                    st.error("PIN Master incorreto.")

# =========================================================
# TELA 2: ÁREA EXCLUSIVA DO COLABORADOR
# =========================================================
elif st.session_state.view == "colaborador":

   # 1. Recupera primeiro os dados do colaborador
    user_data = df_users[df_users["id"] == st.session_state.colab_id].iloc[0]

    # 2. Atualização automática contínua e sentinela
    st_autorefresh(interval=15 * 1000, key="auto_refresh_colab")
    processar_saidas_automaticas_inatividade()

    # 3. Bloco Inteligente de Download do Instalador
    status_instalacao = str(user_data.get("instalado", "0"))

    if status_instalacao == "0":
        st.warning("⚠️ **Atenção:** Você ainda não instalou o aplicativo sentinela neste computador.")
        caminho_setup = os.path.join("assets", "UPYNEX_Setup.exe")
        
        if os.path.exists(caminho_setup):
            with open(caminho_setup, "rb") as f_exe:
                st.download_button(
                    label="📥 Baixar UPYNEX Sentinel (.exe)",
                    data=f_exe,
                    file_name="UPYNEX_Setup.exe",
                    mime="application/octet-stream",
                    use_container_width=True
                )
        else:
            st.info("Arquivo de instalação em preparação pelo suporte.")
    else:
        st.caption("🛡️ Terminal Sentinela instalado e vinculado a este perfil.")
        
    # Atualiza a tela a cada 15 segundos nativamente sem intervenção humana
    st_autorefresh(interval=15 * 1000, key="auto_refresh_colab")
    
    # Processa imediatamente as saídas por inatividade antes de desenhar o restante da tela
    processar_saidas_automaticas_inatividade()

    # Gatilho de atualização contínua em tempo real (a cada 15 segundos)
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        window.parent.setTimeout(function() {
            window.parent.document.dispatchEvent(new KeyboardEvent('keydown', {'key': 'r'}));
        }, 15000);
        </script>
        """,
        height=0,
        width=0
    )

    user_data = df_users[df_users["id"] == st.session_state.colab_id].iloc[0]
    idx_user = df_users[df_users["id"] == st.session_state.colab_id].index[0]
    vh_colab = float(user_data["valor_hora"]) if "valor_hora" in user_data and str(user_data["valor_hora"]).replace('.','',1).isdigit() else 25.0
    
    # Atualização periódica automática em tempo real (a cada 30 segundos)
    @st.fragment(run_every=30)
    def monitor_tempo_real():
        processar_saidas_automaticas_inatividade()

    sess_atual = df_sessoes[df_sessoes["id_colaborador"] == user_data["id"]]
    status_app = "🔴 Desconectado"
    if not sess_atual.empty:
        try:
            ultimo_p = datetime.strptime(sess_atual.iloc[-1]["ultimo_pulso"], "%Y-%m-%d %H:%M:%S")
            if (datetime.now() - ultimo_p).total_seconds() <= 180:
                status_app = "🟢 Conectado"
        except:
            pass

    c_topo1, c_topo2 = st.columns([8, 2])
    with c_topo1:
        st.markdown(f'<div class="main-title">Olá, {user_data["nome"]}</div>', unsafe_allow_html=True)
        st.caption(f"Painel Individual Operacional &nbsp;|&nbsp; Status: **{status_app}**")
    with c_topo2:
        if st.button("⬅️ Sair / Início"):
          st.session_state.view = "home"
          st.session_state.colab_id = None
          st.session_state.pop("msg_ponto_sucesso", None)
          st.query_params.clear()
          st.rerun()

    if "msg_ponto_sucesso" in st.session_state:
        st.markdown(f"""
            <div class="alerta-sucesso">
                ✅ {st.session_state["msg_ponto_sucesso"]}
            </div>
        """, unsafe_allow_html=True)

    tab_ponto, tab_extrato, tab_pin = st.tabs(["⏱️ Bater Ponto", "📄 Histórico & Espelho Mensal", "🔑 Alterar Senha / PIN"])
    
    # 1. BATER PONTO E TAREFAS
    with tab_ponto:
        col_esq, col_meio, col_tarefas = st.columns([3.5, 3.5, 3])
        
        with col_esq:
            agora = datetime.now()
            hoje_str = str(date.today())
            pontos_hoje = df_pontos[(df_pontos["id_colaborador"] == user_data["id"]) & (df_pontos["data"] == hoje_str)]
            
            tipo_batida = "Entrada"
            classe_btn = "btn-entrada"
            if not pontos_hoje.empty and "Entrada" in pontos_hoje.iloc[-1]["tipo"]:
                tipo_batida = "Saída"
                classe_btn = "btn-saida"

            st.markdown(f"""
                <div class="metric-box">
                    <small style="color:#666;">Data e Horário</small>
                    <h3 style="margin: 4px 0; color: #0A0A0A; font-size: 1.8rem;">{agora.strftime('%H:%M:%S')}</h3>
                    <span style="font-weight: 500;">{agora.strftime('%d/%m/%Y')}</span>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f'<div class="{classe_btn}">', unsafe_allow_html=True)
            if st.button(f"Confirmar {tipo_batida}", key="btn_bater_ponto", use_container_width=True):
                novo_ponto = pd.DataFrame([{
                    "id_colaborador": user_data["id"],
                    "data": hoje_str,
                    "tipo": tipo_batida,
                    "hora": agora.strftime('%H:%M:%S'),
                    "minutos_acumulados": "0"
                }])
                df_pontos = pd.concat([df_pontos, novo_ponto], ignore_index=True)
                df_pontos.to_csv(FILE_PONTOS, index=False)
                st.session_state["msg_ponto_sucesso"] = f"Ponto de {tipo_batida} registrado às {agora.strftime('%H:%M:%S')}!"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with col_meio:
            st.markdown("##### Resumo do Mês Atual")
            mes_corrente_str = date.today().strftime("%Y-%m")
            pts_mes_atual = df_pontos[(df_pontos["id_colaborador"] == user_data["id"]) & (df_pontos["data"].str.startswith(mes_corrente_str))]
            
            df_res_atual, h_atual, v_atual = calcular_espelho_diario(pts_mes_atual, vh_colab)
            dias_at = df_res_atual.shape[0]
            
            st.markdown(f"""
                <div class="metric-box">
                    <p style="margin:0; color:#666;">Dias com Ponto em {date.today().strftime('%m/%Y')}:</p>
                    <h4 style="margin:0 0 8px 0; color:#0A0A0A;">{dias_at} dias</h4>
                    <p style="margin:0; color:#666;">Total de Horas Trabalhadas:</p>
                    <h4 style="margin:0 0 8px 0; color:#00F0FF;">{h_atual:.2f} horas</h4>
                    <p style="margin:0; color:#666;">Saldo Acumulado Realizado:</p>
                    <h4 style="margin:0; color:#39FF14;">R$ {v_atual:.2f}</h4>
                </div>
            """, unsafe_allow_html=True)

        with col_tarefas:
            st.markdown("##### 📌 Tarefas")
            tarefas_user = df_tarefas[
                (df_tarefas["id_colaborador"] == user_data["id"]) & 
                (df_tarefas["status"] != "concluida")
            ]
            
            if tarefas_user.empty:
                st.info("Nenhuma tarefa pendente.")
            else:
                for idx, row in tarefas_user.iterrows():
                    status_atual = row["status"]
                    timer_txt, is_atrasado = formatar_contagem_regressiva(row["prazo_limite"])
                    tag_status = "🔴 PENDENTE" if status_atual == "pendente" else "🔵 EM ANDAMENTO"
                    borda_cor = "#FF4B4B" if status_atual == "pendente" else "#00F0FF"
                    
                    rotulo_card = f"**{tag_status}**  \n**{row['titulo']}**  \n⏳ *{timer_txt}*"
                    
                    # Injeta a variável da cor da borda dinâmica e envelopa na classe exclusiva
                    st.markdown(f'<div class="card-tarefa-box" style="--borda-tarefa: {borda_cor}; margin-bottom: 8px;">', unsafe_allow_html=True)
                    if st.button(rotulo_card, key=f"card_t_{row['id']}", use_container_width=True):
                        modal_detalhes_tarefa(row, idx)
                    st.markdown('</div>', unsafe_allow_html=True)

    # 2. HISTÓRICO E ESPELHO DETALHADO MÊS A MÊS
    with tab_extrato:
        st.markdown("#### Espelho Mensal de Horas e Valores")
        pts_colab_all = df_pontos[df_pontos["id_colaborador"] == user_data["id"]]
        
        if pts_colab_all.empty:
            st.info("Nenhuma batida de ponto registrada até o momento.")
        else:
            meses_disponiveis = sorted(list(set(pts_colab_all["data"].str.slice(0, 7))), reverse=True)
            mes_selecionado = st.selectbox("Selecione o Mês para Análise:", meses_disponiveis, key="colab_mes_sel")
            
            pts_mes = pts_colab_all[pts_colab_all["data"].str.startswith(mes_selecionado)]
            df_diario, h_total_m, v_total_m = calcular_espelho_diario(pts_mes, vh_colab)
            
            st.markdown(f"##### Detalhamento Dia a Dia ({mes_selecionado})")
            if df_diario.empty:
                st.write("Sem registros no período selecionado.")
            else:
                df_mostra = df_diario.rename(columns={
                    "data": "Data",
                    "entradas": "Entradas",
                    "saidas": "Saídas",
                    "duracao_formatada": "Horas Efetivas",
                    "valor_dia": "Valor do Dia (R$)"
                })
                st.dataframe(df_mostra[["Data", "Entradas", "Saídas", "Horas Efetivas", "Valor do Dia (R$)"]], use_container_width=True)
                
                # Balanço com Pagamentos
                pags_colab_user = df_pags[
                    (df_pags["id_colaborador"] == user_data["id"]) & 
                    (df_pags["data"].str.startswith(mes_selecionado))
                ]
                pago_user = pags_colab_user["valor_pago"].astype(float).sum() if not pags_colab_user.empty else 0.0
                remanescente_user = v_total_m - pago_user
                
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Produzido", f"R$ {v_total_m:.2f}")
                m2.metric("Adiantamentos Recebidos", f"R$ {pago_user:.2f}")
                m3.metric("Saldo a Receber", f"R$ {remanescente_user:.2f}")
                
                if not pags_colab_user.empty:
                    st.write("---")
                    st.markdown("##### Histórico de Adiantamentos Recebidos")
                    st.dataframe(pags_colab_user[["data", "hora", "valor_pago", "observacao"]].rename(columns={
                        "data": "Data", "hora": "Horário", "valor_pago": "Valor (R$)", "observacao": "Descrição"
                    }), use_container_width=True)

    # 3. ALTERAÇÃO DE PIN
    with tab_pin:
        st.markdown("#### Gerenciar Senha / PIN")
        if user_data["primeiro_acesso"] == "sim":
            st.info("Primeiro acesso ativo. Defina seu novo PIN pessoal definitivo:")
            np1 = st.text_input("Novo PIN:", key="np_prim")
            np2 = st.text_input("Confirme o Novo PIN:", key="np_prim_conf")
            if st.button("Salvar Meu PIN"):
                if len(np1) >= 4 and np1 == np2:
                    df_users.at[idx_user, "pin"] = np1
                    df_users.at[idx_user, "primeiro_acesso"] = "nao"
                    df_users.to_csv(FILE_USERS, index=False)
                    st.success("PIN cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("PINs não conferem ou possuem menos de 4 dígitos.")
        else:
            st.write("Solicite a alteração da sua senha para aprovação da diretoria.")
            p_sol = st.text_input("Novo PIN desejado:", key="np_sol")
            if st.button("Solicitar Alteração"):
                if len(p_sol) >= 4:
                    df_users.at[idx_user, "novo_pin_solicitado"] = p_sol
                    df_users.to_csv(FILE_USERS, index=False)
                    st.success("Solicitação enviada ao Gestor.")
                    st.rerun()
                else:
                    st.error("Mínimo de 4 dígitos.")

# =========================================================
# TELA 3: PAINEL EXCLUSIVO DO ADMINISTRADOR
# =========================================================
elif st.session_state.view == "admin":
    if not st.session_state.admin_autenticado:
        st.session_state.view = "home"
        st.rerun()
        
    c_ad1, c_ad2 = st.columns([8, 2])
    with c_ad1:
        st.markdown('<div class="main-title">Painel Administrativo Master</div>', unsafe_allow_html=True)
        st.caption("Gestão de Colaboradores, Liquidação Pix e Fechamento Mensal")
    with c_ad2:
        if st.button("⬅️ Sair do Admin"):
          st.session_state.admin_autenticado = False
          st.session_state.view = "home"
          st.query_params.clear()
          st.rerun()
            
    t_avisos, t_cad, t_lista, t_tarefas_adm, t_aprov, t_master = st.tabs([
        "📢 Mural Geral",
        "➕ Cadastrar Colaborador",
        "📋 Gestão, Pix & Fechamento",
        "📌 Tarefas",
        "🔑 Aprovações de PIN",
        "🛡️ PIN Master"
    ])
    
    # 1. Mural
    with t_avisos:
        st.markdown("#### Mural Principal")
        txt_novo_aviso = st.text_area("Texto exibido na entrada:", value=get_cfg("aviso_geral"))
        if st.button("Publicar no Mural"):
            set_cfg("aviso_geral", txt_novo_aviso)
            st.success("Mural atualizado com sucesso!")
            
    # 2. Cadastro
    with t_cad:
        st.markdown("#### Cadastrar Novo Colaborador")
        with st.form("form_cad_colab", clear_on_submit=False):
            fn = st.text_input("Nome Completo:")
            fd = st.text_input("Documento (opcional):")
            ft = st.selectbox("Tipo de Chave Pix:", ["Telefone", "CPF", "E-mail", "Chave Aleatória"])
            fc = st.text_input("Chave Pix:")
            fv = st.number_input("Valor Base por Hora (R$):", min_value=0.0, value=25.0, step=0.5)
            
            v_minuto = fv / 60
            v_diaria = fv * 8
            v_mensal = fv * 168
            
            st.markdown("##### Estimativa Salarial Referencial (Seg-Sex)")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f"""
                    <div class="metric-box">
                        <small style="color:#666;">Por Minuto</small>
                        <h4 style="margin:0; color:#0A0A0A;">R$ {v_minuto:.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                    <div class="metric-box">
                        <small style="color:#666;">Por Diária Base (8h)</small>
                        <h4 style="margin:0; color:#00F0FF;">R$ {v_diaria:.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown(f"""
                    <div class="metric-box">
                        <small style="color:#666;">Por Mês (~168h)</small>
                        <h4 style="margin:0; color:#39FF14;">R$ {v_mensal:.2f}</h4>
                    </div>
                """, unsafe_allow_html=True)
                
            st.info(f"PIN padrão de primeiro acesso: **{PIN_PADRAO}**.")
            btn_salvar_colab = st.form_submit_button("Salvar Colaborador")
            
            if btn_salvar_colab:
                nome_limpo = fn.strip() if fn else ""
                chave_limpa = fc.strip() if fc else "Não informada"
                doc_limpo = fd.strip() if fd else "Não informado"
                
                if len(nome_limpo) > 0:
                    novo_id = str(len(df_users) + 1)
                    novo_reg = pd.DataFrame([{
                        "id": novo_id,
                        "nome": nome_limpo,
                        "documento": doc_limpo,
                        "tipo_pix": ft,
                        "chave_pix": chave_limpa,
                        "valor_hora": str(fv),
                        "pin": PIN_PADRAO,
                        "primeiro_acesso": "sim",
                        "novo_pin_solicitado": "nao",
                        "instalado": "0"
                    }])
                    df_users = pd.concat([df_users, novo_reg], ignore_index=True)
                    df_users.to_csv(FILE_USERS, index=False)
                    st.success(f"Colaborador(a) {nome_limpo} cadastrado(a) com sucesso!")
                    st.rerun()
                else:
                    st.error("O campo 'Nome Completo' é obrigatório.")

    # 3. Gestão, Pix, Fechamento Mensal, Pagamentos e PDF
    with t_lista:
        st.markdown("#### Gestão de Colaboradores e Fechamento Mensal")
        if df_users.empty:
            st.info("Nenhum colaborador registrado.")
        else:
            col_sel_nome = st.selectbox("Selecione o Colaborador:", df_users["nome"].tolist(), key="adm_colab_detalhes")
            user_adm_data = df_users[df_users["nome"] == col_sel_nome].iloc[0]
            idx_adm_user = df_users[df_users["nome"] == col_sel_nome].index[0]
            vh_adm = float(user_adm_data["valor_hora"]) if "valor_hora" in user_adm_data and str(user_adm_data["valor_hora"]).replace('.','',1).isdigit() else 25.0
            
            sess_adm = df_sessoes[df_sessoes["id_colaborador"] == user_adm_data["id"]]
            status_terminal = "🔴 Desconectado"
            maq_info = "Nenhuma máquina vinculada"
            if not sess_adm.empty:
                maq_info = sess_adm.iloc[-1].get("maquina_id", "Identificador Padrão")
                try:
                    ultimo_p_adm = datetime.strptime(sess_adm.iloc[-1]["ultimo_pulso"], "%Y-%m-%d %H:%M:%S")
                    if (datetime.now() - ultimo_p_adm).total_seconds() <= 180:
                        status_terminal = "🟢 Máquina Online e Ativa"
                except:
                    pass

            c_det1, c_det2 = st.columns([6, 4])
            with c_det1:
                st.markdown(f"### {user_adm_data['nome']}")
                st.write(f"**Documento:** {user_adm_data['documento']}")
                st.write(f"**Valor por Hora:** R$ {vh_adm:.2f}")
                st.write(f"**PIN Atual:** `{user_adm_data['pin']}`")
                st.write(f"**Terminal Executável:** {status_terminal} (`{maq_info}`)")

                # Status da Instalação e Controle de Reinstalação
                is_inst = str(user_adm_data.get("instalado", "0")) == "1"
                if is_inst:
                    st.write("**Instalação:** 🟢 Instalado no Computador")
                    if st.button("🔄 Liberar Nova Instalação", key=f"reinst_{user_adm_data['id']}"):
                        df_users.at[idx_adm_user, "instalado"] = "0"
                        df_users.to_csv(FILE_USERS, index=False)
                        st.success(f"Instalação liberada para {user_adm_data['nome']}!")
                        st.rerun()
                else:
                    st.write("**Instalação:** 🟡 Aguardando Download / Instalação")
                
                st.write("---")
                st.markdown("##### Alterar PIN do Colaborador")
                p_forc = st.text_input("Novo PIN:", key="adm_p_force")
                if st.button("Salvar Novo PIN"):
                    if len(p_forc) >= 4:
                        df_users.at[idx_adm_user, "pin"] = p_forc
                        df_users.at[idx_adm_user, "primeiro_acesso"] = "nao"
                        df_users.at[idx_adm_user, "novo_pin_solicitado"] = ""
                        df_users.to_csv(FILE_USERS, index=False)
                        st.success(f"PIN alterado para {user_adm_data['nome']}!")
                        st.rerun()
                    else:
                        st.error("Mínimo de 4 dígitos.")
                        
                st.write("---")
                st.markdown("##### Excluir Colaborador")
                if st.button(f"🗑️ Excluir definitivamente {user_adm_data['nome']}", key="btn_del_user"):
                    df_users = df_users.drop(idx_adm_user).reset_index(drop=True)
                    df_users.to_csv(FILE_USERS, index=False)
                    st.warning("Colaborador removido.")
                    st.rerun()

            with c_det2:
                st.markdown("##### Pagamento via Pix")
                st.write(f"**Tipo:** {user_adm_data['tipo_pix']}")
                st.write(f"**Chave:** `{user_adm_data['chave_pix']}`")
                
                if str(user_adm_data["chave_pix"]).strip() and user_adm_data["chave_pix"] != "Não informada":
                    qr_code_bytes = gerar_qr_pix(str(user_adm_data["chave_pix"]))
                    st.image(qr_code_bytes, caption="Escaneie pelo aplicativo bancário", width=190)
                else:
                    st.info("Chave Pix não informada.")

                st.write("---")
                st.markdown("##### 💵 Registrar Pagamento / Adiantamento")
                with st.form(f"form_pag_{user_adm_data['id']}", clear_on_submit=True):
                    v_pg = st.number_input("Valor Pago (R$):", min_value=0.0, value=10.0, step=5.0)
                    col_dt_p, col_hr_p = st.columns(2)
                    with col_dt_p:
                        d_pg = st.date_input("Data do Pagamento:", value=date.today())
                    with col_hr_p:
                        h_pg = st.time_input("Horário da Transação:", value=datetime.now().time())
                    obs_pg = st.text_input("Observação / Descrição:", value="Adiantamento Pix")
                    
                    btn_confirmar_pg = st.form_submit_button("Confirmar Baixa")
                    if btn_confirmar_pg:
                        if v_pg > 0:
                            novo_pg = pd.DataFrame([{
                                "id": str(len(df_pags) + 1),
                                "id_colaborador": user_adm_data["id"],
                                "data": str(d_pg),
                                "hora": h_pg.strftime('%H:%M:%S'),
                                "valor_pago": str(v_pg),
                                "observacao": obs_pg.strip()
                            }])
                            df_pags = pd.concat([df_pags, novo_pg], ignore_index=True)
                            df_pags.to_csv(FILE_PAGAMENTOS, index=False)
                            st.success(f"Pagamento de R$ {v_pg:.2f} lançado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Digite um valor maior que zero.")

            # Módulo de Fechamento de Mês e PDF Oficial
            st.write("---")
            st.markdown("### 📊 Fechamento Mensal e Exportação Oficial")
            pts_adm_colab = df_pontos[df_pontos["id_colaborador"] == user_adm_data["id"]]
            
            if pts_adm_colab.empty:
                st.write("Este colaborador ainda não possui batidas registradas.")
            else:
                meses_adm = sorted(list(set(pts_adm_colab["data"].str.slice(0, 7))), reverse=True)
                mes_escolhido_adm = st.selectbox("Selecione o Mês para Fechamento e PDF:", meses_adm, key="adm_mes_fechamento")
                
                pts_adm_mes = pts_adm_colab[pts_adm_colab["data"].str.startswith(mes_escolhido_adm)]
                df_adm_diario, h_total_adm, v_total_adm = calcular_espelho_diario(pts_adm_mes, vh_adm)
                
                # Filtrar Pagamentos do Mês
                pags_colab_mes = df_pags[
                    (df_pags["id_colaborador"] == user_adm_data["id"]) & 
                    (df_pags["data"].str.startswith(mes_escolhido_adm))
                ]
                tot_pago_mes = pags_colab_mes["valor_pago"].astype(float).sum() if not pags_colab_mes.empty else 0.0
                saldo_restante_mes = v_total_adm - tot_pago_mes
                
                st.markdown(f"##### Espelho Diário de {user_adm_data['nome']} em {mes_escolhido_adm}")
                st.dataframe(df_adm_diario.rename(columns={
                    "data": "Data", "entradas": "Entradas", "saidas": "Saídas",
                    "duracao_formatada": "Horas Efetivas", "valor_dia": "Valor Líquido (R$)"
                })[["Data", "Entradas", "Saídas", "Horas Efetivas", "Valor Líquido (R$)"]], use_container_width=True)
                
                if not pags_colab_mes.empty:
                    st.markdown(f"##### Demonstrativo de Adiantamentos em {mes_escolhido_adm}")
                    st.dataframe(pags_colab_mes[["data", "hora", "valor_pago", "observacao"]].rename(columns={
                        "data": "Data", "hora": "Horário", "valor_pago": "Valor (R$)", "observacao": "Descrição"
                    }), use_container_width=True)

                col_tot1, col_tot2, col_tot3, col_tot4 = st.columns([2.5, 2.5, 2.5, 4.5])
                col_tot1.metric("Horas Trabalhadas", f"{h_total_adm:.2f} h")
                col_tot2.metric("Total Produzido", f"R$ {v_total_adm:.2f}")
                col_tot3.metric("Total Já Pago", f"R$ {tot_pago_mes:.2f}")
                col_tot4.metric("Saldo Restante", f"R$ {saldo_restante_mes:.2f}")
                
                st.write("")
                pdf_oficial_bytes = gerar_pdf_extrato(
                    user_adm_data["nome"],
                    user_adm_data["documento"],
                    user_adm_data["chave_pix"],
                    mes_escolhido_adm,
                    df_adm_diario,
                    h_total_adm,
                    v_total_adm,
                    pags_colab_mes
                )
                st.download_button(
                    label=f"📥 Baixar Relatório PDF Completo ({mes_escolhido_adm})",
                    data=pdf_oficial_bytes,
                    file_name=f"UPYNEX_Extrato_{user_adm_data['nome']}_{mes_escolhido_adm}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

    # 4. Atribuição de Tarefas com Prazo
    with t_tarefas_adm:
        st.markdown("#### Atribuir Nova Tarefa com Prazo")
        if df_users.empty:
            st.info("Cadastre um colaborador para atribuir tarefas.")
        else:
            with st.form("form_nova_tarefa"):
                dest_nome = st.selectbox("Destinatário:", df_users["nome"].tolist())
                dest_id = df_users[df_users["nome"] == dest_nome].iloc[0]["id"]
                t_titulo = st.text_input("Título Curto da Tarefa:")
                t_desc = st.text_area("Orientações e Instruções:")
                
                c_pr1, c_pr2 = st.columns(2)
                with c_pr1:
                    dt_limite = st.date_input("Data Limite:", value=date.today() + timedelta(days=1))
                with c_pr2:
                    hr_limite = st.time_input("Hora Limite:", value=datetime.strptime("18:00", "%H:%M").time())
                    
                prazo_formatado = f"{dt_limite} {hr_limite.strftime('%H:%M')}"
                
                btn_send_t = st.form_submit_button("Enviar Tarefa")
                if btn_send_t:
                    if t_titulo.strip() and t_desc.strip():
                        novo_id_t = str(len(df_tarefas) + 1)
                        nova_t = pd.DataFrame([{
                            "id": novo_id_t,
                            "id_colaborador": dest_id,
                            "titulo": t_titulo.strip(),
                            "descricao": t_desc.strip(),
                            "prazo_limite": prazo_formatado,
                            "status": "pendente",
                            "data_envio": datetime.now().strftime('%d/%m/%Y %H:%M')
                        }])
                        df_tarefas = pd.concat([df_tarefas, nova_t], ignore_index=True)
                        df_tarefas.to_csv(FILE_TAREFAS, index=False)
                        st.success(f"Tarefa enviada com sucesso para {dest_nome}!")
                        st.rerun()
                    else:
                        st.error("Título e Orientações são obrigatórios.")

            st.write("---")
            st.markdown("#### Acompanhamento das Tarefas")
            if df_tarefas.empty:
                st.write("Nenhuma tarefa em andamento.")
            else:
                for idx_t, row_t in df_tarefas.iterrows():
                    user_nome_dest = df_users[df_users["id"] == row_t["id_colaborador"]]["nome"].values
                    nome_alvo = user_nome_dest[0] if len(user_nome_dest) > 0 else "Desconhecido"
                    
                    status_cor = "🔴 Pendente" if row_t["status"] == "pendente" else ("🔵 Em Andamento" if row_t["status"] == "em_andamento" else "🟢 Concluída")
                    t_timer, _ = formatar_contagem_regressiva(row_t["prazo_limite"])
                    
                    col_t1, col_t2, col_t3 = st.columns([5, 3, 2])
                    col_t1.write(f"**{row_t['titulo']}** ({nome_alvo}) - {t_timer}")
                    col_t2.write(f"Status: **{status_cor}**")
                    if col_t3.button("Remover", key=f"del_t_{row_t['id']}"):
                        df_tarefas = df_tarefas.drop(idx_t).reset_index(drop=True)
                        df_tarefas.to_csv(FILE_TAREFAS, index=False)
                        st.rerun()

    # 5. Aprovações de PIN
    with t_aprov:
        st.markdown("#### Solicitações de Troca de PIN")
        pendentes = df_users[df_users["novo_pin_solicitado"].fillna("").str.strip() != ""]
        if pendentes.empty:
            st.info("Nenhuma solicitação pendente.")
        else:
            for idx, row in pendentes.iterrows():
                ca, cb, cc = st.columns([4, 2, 2])
                ca.write(f"**{row['nome']}** solicitou o PIN: `{row['novo_pin_solicitado']}`")
                if cb.button("Aprovar", key=f"ap_{row['id']}"):
                    df_users.at[idx, "pin"] = str(row["novo_pin_solicitado"])
                    df_users.at[idx, "novo_pin_solicitado"] = ""
                    df_users.to_csv(FILE_USERS, index=False)
                    st.success(f"Novo PIN aprovado para {row['nome']}!")
                    st.rerun()
                if cc.button("Recusar", key=f"rc_{row['id']}"):
                    df_users.at[idx, "novo_pin_solicitado"] = ""
                    df_users.to_csv(FILE_USERS, index=False)
                    st.warning("Solicitação recusada.")
                    st.rerun()

    # 6. PIN Master do Gestor
    with t_master:
        st.markdown("#### Alterar Senha Master do Administrador")
        n_adm1 = st.text_input("Novo PIN Master:", key="n_adm1")
        n_adm2 = st.text_input("Confirmar Novo PIN Master:", key="n_adm2")
        if st.button("Salvar Novo PIN Master"):
            if len(n_adm1) >= 4 and n_adm1 == n_adm2:
                set_cfg("pin_admin", n_adm1)
                st.success("PIN Master atualizado!")
                st.rerun()
            else:
                st.error("PINs não conferem ou possuem menos de 4 dígitos.")