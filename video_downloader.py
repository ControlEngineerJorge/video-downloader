#!/usr/bin/env python3

import yt_dlp
import os
import threading
import tkinter as tk
import subprocess
import json
from datetime import datetime
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Label
#from tkinter import PhotoImage

CONFIG_FILE = "config.json"
LOG_FILE = "downloads.log"


def salvar_config(link, pasta):
    config = {"link": link, "pasta": pasta}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                config = json.load(f)
                link = config.get("link", "")
                pasta = config.get("pasta", "")

                # Corrige duplicações: limpa e insere apenas se for diferente do valor atual
                entrada_link.delete(0, tk.END)
                entrada_link.insert(0, link)

                entrada_pasta.delete(0, tk.END)
                if os.path.isabs(pasta):
                    entrada_pasta.insert(0, pasta)
                else:
                    # Garante que seja absoluto, evita problemas
                    entrada_pasta.insert(0, os.path.abspath(pasta))
            except json.JSONDecodeError:
                pass

#def carregar_config():
#    if os.path.exists(CONFIG_FILE):
#        with open(CONFIG_FILE, "r") as f:
#            try:
#                config = json.load(f)
#                entrada_link.insert(0, config.get("link", ""))
#                entrada_pasta.insert(0, config.get("pasta", ""))
#            except json.JSONDecodeError:
#                pass

def log_download(titulo, caminho):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {titulo} -> {caminho}\n")

def escolher_pasta():
    pasta = filedialog.askdirectory()
    if pasta:
        entrada_pasta.delete(0, tk.END)
        entrada_pasta.insert(0, pasta)

def abrir_pasta():
    pasta = entrada_pasta.get()
    if os.path.exists(pasta):
        if os.name == 'nt':  # Windows
            os.startfile(pasta)
        elif os.name == 'posix':  # Linux/macOS
            subprocess.Popen(['xdg-open', pasta])
    else:
        messagebox.showerror("Erro", "A pasta não existe.")

def atualizar_progresso(d):
    if d['status'] == 'downloading':
        porcentagem = float(d['_percent_str'].strip('%'))
        barra_progresso['value'] = porcentagem
        texto_progresso['text'] = f"{porcentagem:.1f}%"
        root.update_idletasks()

    elif d['status'] == 'finished':
        barra_progresso['value'] = 100
        texto_progresso['text'] = "100%"
        root.update_idletasks()

        resposta = messagebox.askquestion(
            "Download Concluído ✅",
            "Download concluído com sucesso!\n\nDeseja abrir a pasta de destino?",
            icon="info"
        )

        if resposta == "yes":
            abrir_pasta()
        else:
            root.destroy()

def iniciar_download():
    url = entrada_link.get()
    pasta = entrada_pasta.get()

    if not url:
        messagebox.showwarning("Erro", "Insira um link válido.")
        return
    if not pasta:
        messagebox.showwarning("Erro", "Escolha um local para salvar o vídeo.")
        return

    salvar_config(url, pasta)
    threading.Thread(target=baixar_video, args=(url, pasta), daemon=True).start()

def baixar_video(url, pasta):
    os.makedirs(pasta, exist_ok=True)

    # Obter informações do vídeo antes do download
    ydl_opts_info = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            titulo = info.get('title', 'video')
            extensao = info.get('ext', 'mp4')
            nome_arquivo = f"{titulo}.{extensao}"
            caminho_arquivo = os.path.join(pasta, nome_arquivo)

            if os.path.exists(caminho_arquivo):
                messagebox.showinfo("Arquivo já existe", f"O vídeo \"{nome_arquivo}\" já foi baixado.")
                return
    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao obter informações do vídeo:\n{e}")
        return

    # Opções para download real
    opcoes = {
        'outtmpl': os.path.join(pasta, '%(title)s.%(ext)s'),
        'format': 'bv*+ba/b',
        'merge_output_format': 'mp4',
        'progress_hooks': [atualizar_progresso]
    }

    with yt_dlp.YoutubeDL(opcoes) as ydl:
        ydl.download([url])

    log_download(titulo, caminho_arquivo)

# Interface gráfica
root = tk.Tk()

# Carrega e aplica ícone .png à janela
#icone = PhotoImage(file="iconvd.png")
#root.iconphoto(True, icone)

root.title("Downloader de Vídeos")

largura_janela = 600
altura_janela = 230
largura_tela = root.winfo_screenwidth()
altura_tela = root.winfo_screenheight()
pos_x = (largura_tela // 3) - (largura_janela // 1)
pos_y = (altura_tela // 2) - (altura_janela // 2)
root.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
root.resizable(False, False)

menu = tk.Menu(root)
root.config(menu=menu)
menu.add_command(label="Sair", command=root.quit)

frame = tk.Frame(root)
frame.pack(pady=10, padx=10, fill="both", expand=True)

tk.Label(frame, text="Link do Vídeo:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
entrada_link = tk.Entry(frame, width=52)
entrada_link.grid(row=0, column=1, padx=5, pady=2, columnspan=2)

tk.Label(frame, text="Local de Download:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
entrada_pasta = tk.Entry(frame, width=40)
entrada_pasta.insert(0, os.path.join(os.path.expanduser("~"), "Downloads"))
entrada_pasta.grid(row=1, column=1, padx=5, pady=2)

btn_escolher_pasta = tk.Button(frame, text="Escolher", command=escolher_pasta)
btn_escolher_pasta.grid(row=1, column=2, padx=5, pady=2)

btn_download = tk.Button(frame, text="Iniciar Download", command=iniciar_download)
btn_download.grid(row=2, column=0, columnspan=2, pady=10)

btn_abrir_pasta = tk.Button(frame, text="Abrir Pasta", command=abrir_pasta)
btn_abrir_pasta.grid(row=2, column=2, pady=10)

barra_progresso = Progressbar(frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
barra_progresso.grid(row=3, column=0, columnspan=3, pady=5)

texto_progresso = Label(frame, text="0%")
texto_progresso.grid(row=3, column=2)

carregar_config()
root.mainloop()
