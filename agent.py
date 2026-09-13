import os
import sys
import time
import json
import uuid
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pandas as pd
from plyer import notification
import pystray
from PIL import Image, ImageDraw

# --- DIRETÓRIOS E ARQUIVOS (BLINDAGEM TOTAL WINDOWS) ---
appdata_upynex = os.path.join(os.environ.get("LOCALAPPDATA", ""), "UPYNEX")

if os.path.exists(os.path.join(appdata_upynex, "data", "usuarios.csv")):
    BASE_DIR = appdata_upynex
elif getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_AGENT_FILE = os.path.join(BASE_DIR, "config_agent.json")

FILE_USERS = os.path.join(DATA_DIR, "usuarios.csv")
FILE_PONTOS = os.path.join(DATA_DIR, "pontos.csv")
FILE_SESSOES = os.path.join(DATA_DIR, "sessoes.csv")
FILE_TAREFAS = os.path.join(DATA_DIR, "tarefas.csv")

# Controle em memória para não disparar pop-ups repetidos
tarefas_notificadas = set()
tarefas_alerta_duas_horas = set()

def emitir_notificacao(titulo, mensagem):
    """Emite uma notificação nativa no canto da tela do Windows."""
    try:
        notification.notify(
            title=titulo,
            message=mensagem,
            app_name="UPYNEX Agent",
            timeout=8
        )
    except Exception:
        pass

def janela_pareamento():
    """Janela visual de primeiro acesso para autorizar a máquina."""
    if not os.path.exists(FILE_USERS):
        messagebox.showerror("UPYNEX - Erro", f"Base de dados não encontrada.\nCaminho verificado: {FILE_USERS}")
        return None

    try:
        df_u = pd.read_csv(FILE_USERS, dtype=str)
    except Exception as e:
        messagebox.showerror("UPYNEX - Erro", f"Falha ao ler base de colaboradores: {e}")
        return None

    if df_u.empty:
        messagebox.showwarning("UPYNEX", "Nenhum colaborador registrado no sistema.")
        return None

    dados_salvos = {}

    root = tk.Tk()
    root.title("UPYNEX Agent - Pareamento de Máquina")
    root.geometry("380x320")
    root.resizable(False, False)
    root.configure(bg="#0A0A0A")

    # Centralizar na tela
    root.eval('tk::PlaceWindow . center')

    lbl_topo = tk.Label(root, text="UPYNEX SENTINEL", font=("Segoe UI", 14, "bold"), fg="#00F0FF", bg="#0A0A0A")
    lbl_topo.pack(pady=(20, 5))

    lbl_sub = tk.Label(root, text="Vincule este computador ao seu registro", font=("Segoe UI", 9), fg="#A0AEC0", bg="#0A0A0A")
    lbl_sub.pack(pady=(0, 15))

    lbl_user = tk.Label(root, text="Selecione seu Nome:", font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#0A0A0A")
    lbl_user.pack(anchor="w", padx=40)

    lista_nomes = df_u["nome"].tolist()
    var_nome = tk.StringVar(root)
    var_nome.set(lista_nomes[0])
    opt_user = tk.OptionMenu(root, var_nome, *lista_nomes)
    opt_user.config(bg="#1A1A1A", fg="#FFFFFF", activebackground="#2A2A2A", activeforeground="#00F0FF", highlightthickness=0, width=30)
    opt_user.pack(padx=40, pady=(4, 12))

    lbl_pin = tk.Label(root, text="PIN de Acesso:", font=("Segoe UI", 9, "bold"), fg="#FFFFFF", bg="#0A0A0A")
    lbl_pin.pack(anchor="w", padx=40)

    ent_pin = tk.Entry(root, show="*", font=("Segoe UI", 11), bg="#1A1A1A", fg="#39FF14", insertbackground="#39FF14", justify="center", width=33)
    ent_pin.pack(padx=40, pady=(4, 20))
    ent_pin.focus_set()

    def confirmar():
        nome_sel = var_nome.get()
        pin_sel = ent_pin.get().strip()

        colab = df_u[(df_u["nome"] == nome_sel) & (df_u["pin"] == pin_sel)]
        if colab.empty:
            messagebox.showerror("Acesso Negado", "PIN incorreto para o colaborador selecionado.")
            return

        user_row = colab.iloc[0]
        dados_salvos["id_colaborador"] = str(user_row["id"])
        dados_salvos["nome"] = str(user_row["nome"])
        dados_salvos["maquina_id"] = f"DESKTOP-{uuid.getnode()}"

        with open(CONFIG_AGENT_FILE, "w", encoding="utf-8") as f:
            json.dump(dados_salvos, f, indent=4)

        messagebox.showinfo("Sucesso", f"Máquina autorizada e vinculada com sucesso a {user_row['nome']}!")
        root.destroy()

    btn_vincular = tk.Button(root, text="Ativar Terminal", font=("Segoe UI", 10, "bold"), bg="#0A0A0A", fg="#39FF14",
                             activebackground="#1A1A1A", activeforeground="#00F0FF", relief="solid", bd=1, width=28, command=confirmar)
    btn_vincular.pack(pady=5)

    root.mainloop()
    return dados_salvos if dados_salvos else None

def obter_configuracao():
    """Carrega o pareamento salvo ou abre a tela de primeiro vínculo."""
    if os.path.exists(CONFIG_AGENT_FILE):
        try:
            with open(CONFIG_AGENT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return janela_pareamento()

def loop_monitoramento(cfg, stop_event):
    """Ciclo contínuo de envio de pulso, vigilância de conexão e prazos."""
    colab_id = str(cfg["id_colaborador"])
    maquina_id = str(cfg["maquina_id"])
    ponto_estava_aberto = False

    while not stop_event.is_set():
        agora = datetime.now()
        hoje_str = agora.strftime("%Y-%m-%d")
        agora_str = agora.strftime("%Y-%m-%d %H:%M:%S")

        # 1. Enviar Heartbeat (Sinal de Vida ao sessoes.csv)
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            if os.path.exists(FILE_SESSOES):
                df_sess = pd.read_csv(FILE_SESSOES, dtype=str)
            else:
                df_sess = pd.DataFrame(columns=["id_colaborador", "ultimo_pulso", "status_conexao", "maquina_id"])

            idx = df_sess[df_sess["id_colaborador"] == colab_id].index
            if len(idx) > 0:
                df_sess.loc[idx, "ultimo_pulso"] = agora_str
                df_sess.loc[idx, "status_conexao"] = "online"
                df_sess.loc[idx, "maquina_id"] = maquina_id
            else:
                nova_sess = pd.DataFrame([{
                    "id_colaborador": colab_id,
                    "ultimo_pulso": agora_str,
                    "status_conexao": "online",
                    "maquina_id": maquina_id
                }])
                df_sess = pd.concat([df_sess, nova_sess], ignore_index=True)

            df_sess.to_csv(FILE_SESSOES, index=False)
        except Exception:
            pass

        # 2. Sentinela de Corte Automático por Inatividade/Queda
        try:
            if os.path.exists(FILE_PONTOS):
                df_pts = pd.read_csv(FILE_PONTOS, dtype=str)
                pts_hoje = df_pts[(df_pts["id_colaborador"] == colab_id) & (df_pts["data"] == hoje_str)]
                
                if not pts_hoje.empty:
                    ultimo_tipo = str(pts_hoje.iloc[-1]["tipo"])
                    if "Entrada" in ultimo_tipo:
                        ponto_estava_aberto = True
                    elif "Saída (Automática" in ultimo_tipo and ponto_estava_aberto:
                        emitir_notificacao(
                            "UPYNEX Alerta",
                            "Seu ponto foi desconectado automaticamente por perda de sinal (3 min sem pulso). Acesse o painel para registrar nova entrada."
                        )
                        ponto_estava_aberto = False
                    elif "Saída" in ultimo_tipo:
                        ponto_estava_aberto = False
        except Exception:
            pass

        # 3. Monitoramento de Novas Tarefas e Limite de 2 Horas
        try:
            if os.path.exists(FILE_TAREFAS):
                df_tar = pd.read_csv(FILE_TAREFAS, dtype=str)
                tarefas_ativas = df_tar[(df_tar["id_colaborador"] == colab_id) & (df_tar["status"] != "concluida")]

                for _, tar in tarefas_ativas.iterrows():
                    tar_id = str(tar["id"])

                    # Notifica nova tarefa pendente
                    if tar["status"] == "pendente" and tar_id not in tarefas_notificadas:
                        emitir_notificacao(
                            "Nova Tarefa Atribuída",
                            f"{tar['titulo']}\nAbra seu painel UPYNEX para ver as orientações."
                        )
                        tarefas_notificadas.add(tar_id)

                    # Alerta de proximidade de vencimento (menos de 2 horas)
                    prazo_str = str(tar.get("prazo_limite", "")).strip()
                    if prazo_str and tar_id not in tarefas_alerta_duas_horas:
                        try:
                            dt_prazo = datetime.strptime(prazo_str, "%Y-%m-%d %H:%M")
                            minutos_restantes = (dt_prazo - agora).total_seconds() / 60.0
                            if 0 < minutos_restantes <= 120:
                                emitir_notificacao(
                                    "Atenção ao Prazo",
                                    f"Restam menos de 2 horas para entregar: {tar['titulo']}"
                                )
                                tarefas_alerta_duas_horas.add(tar_id)
                        except Exception:
                            pass
        except Exception:
            pass

        # Pulso emitido a cada 30 segundos
        for _ in range(30):
            if stop_event.is_set():
                break
            time.sleep(1)

def criar_icone():
    """Gera dinamicamente o ícone futurista com a paleta da UPYNEX."""
    img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Fundo circular escuro
    d.ellipse([2, 2, 62, 62], fill=(10, 10, 10, 255), outline=(0, 240, 255, 255), width=3)
    # Ponto verde central indicando atividade
    d.ellipse([22, 22, 42, 42], fill=(57, 255, 20, 255))
    return img

def main():
    cfg = obter_configuracao()
    if not cfg:
        sys.exit(0)

    # Inicia thread com o loop em segundo plano
    stop_event = threading.Event()
    t_monitor = threading.Thread(target=loop_monitoramento, args=(cfg, stop_event), daemon=True)
    t_monitor.start()

    def encerrar_agente(icon, item):
        stop_event.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(f"Colaborador: {cfg['nome']}", lambda: None, enabled=False),
        pystray.MenuItem(f"ID Terminal: {cfg['maquina_id']}", lambda: None, enabled=False),
        pystray.MenuItem("Status: Sentinela Ativo", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Encerrar Sentinela", encerrar_agente)
    )

    icone_tray = pystray.Icon("UPYNEX_Agent", criar_icone(), f"UPYNEX - {cfg['nome']}", menu)
    emitir_notificacao("UPYNEX Ativo", f"Terminal conectado e monitorando para {cfg['nome']}.")
    icone_tray.run()

if __name__ == "__main__":
    main()