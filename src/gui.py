import customtkinter as ctk
import pyautogui
import time
import threading
import keyboard
import logging
from logging.handlers import RotatingFileHandler
import os
import tkinter.messagebox as messagebox
from tkinter import filedialog
from .automation import AutomationEngine, ClickStep

# Configuração de Logging
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        RotatingFileHandler("logs/app.log", maxBytes=1_000_000, backupCount=3, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class DraggableMarker(ctk.CTkToplevel):
    """Marcador visual que pode ser arrastado."""
    def __init__(self, parent, step_index, x, y, on_move_callback):
        super().__init__(parent)
        self.step_index = step_index
        self.on_move_callback = on_move_callback
        
        # Remove barra de título e bordas
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.geometry(f"20x20+{x-10}+{y-10}") # Centraliza no ponto
        
        # Cor visual
        self.frame = ctk.CTkFrame(self, fg_color="red", corner_radius=10)
        self.frame.pack(expand=True, fill="both")
        
        # Label com número
        self.lbl = ctk.CTkLabel(self.frame, text=str(step_index + 1), text_color="white", font=("Arial", 10, "bold"))
        self.lbl.pack(expand=True)
        
        # Bindings de arraste
        self.frame.bind("<Button-1>", self.start_move)
        self.frame.bind("<B1-Motion>", self.do_move)
        self.frame.bind("<ButtonRelease-1>", self.stop_move)
        self.lbl.bind("<Button-1>", self.start_move)
        self.lbl.bind("<B1-Motion>", self.do_move)
        self.lbl.bind("<ButtonRelease-1>", self.stop_move)
        
        self.x_offset = 0
        self.y_offset = 0

    def start_move(self, event):
        self.x_offset = event.x
        self.y_offset = event.y

    def do_move(self, event):
        x = self.winfo_x() + event.x - self.x_offset
        y = self.winfo_y() + event.y - self.y_offset
        self.geometry(f"+{x}+{y}")

    def stop_move(self, event):
        # Compensa o offset visual para pegar o centro
        center_x = self.winfo_x() + 10
        center_y = self.winfo_y() + 10
        self.on_move_callback(self.step_index, center_x, center_y)

class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AutoClicker Modular")
        self.geometry("600x530") # Aumentado um pouco para caber novos botoes
        
        self.engine = AutomationEngine()
        self.markers = []
        self.markers_visible = False
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._init_ui()
        self._setup_hotkeys()

    def _setup_hotkeys(self):
        try:
            keyboard.add_hotkey('F9', self.stop_execution)
        except ImportError:
            print("Biblioteca keyboard não encontrada ou sem permissão.")

    def _init_ui(self):
        # Frame de Configuração (Inputs)
        self.config_frame = ctk.CTkFrame(self)
        self.config_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Inputs HBox
        self.input_box = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.input_box.pack(pady=5, padx=5, fill="x")

        # X
        self.lbl_x = ctk.CTkLabel(self.input_box, text="X:")
        self.lbl_x.pack(side="left", padx=5)
        self.entry_x = ctk.CTkEntry(self.input_box, width=60)
        self.entry_x.pack(side="left", padx=5)
        
        # Y
        self.lbl_y = ctk.CTkLabel(self.input_box, text="Y:")
        self.lbl_y.pack(side="left", padx=5)
        self.entry_y = ctk.CTkEntry(self.input_box, width=60)
        self.entry_y.pack(side="left", padx=5)
        
        # Delay
        self.lbl_delay = ctk.CTkLabel(self.input_box, text="Delay (s):")
        self.lbl_delay.pack(side="left", padx=5)
        self.entry_delay = ctk.CTkEntry(self.input_box, width=60)
        self.entry_delay.insert(0, "1.0")
        self.entry_delay.pack(side="left", padx=5)
        
        # Ação (Tipo)
        self.lbl_btn = ctk.CTkLabel(self.input_box, text="Ação:")
        self.lbl_btn.pack(side="left", padx=5)
        self.opt_action = ctk.CTkOptionMenu(
            self.input_box, 
            values=["Click Left", "Click Right", "Digitar Texto"],
            command=self.on_action_change,
            width=120
        )
        self.opt_action.pack(side="left", padx=5)

        # Campo de Texto
        self.entry_text = ctk.CTkEntry(self.input_box, placeholder_text="Texto...", width=120)
        
        # Checkboxes para Texto
        self.text_opts_frame = ctk.CTkFrame(self.input_box, fg_color="transparent")
        # Será mostrado apenas quando Digitar Texto
        
        self.chk_use_file = ctk.CTkCheckBox(self.text_opts_frame, text="Usar Arq.", width=60)
        self.chk_use_file.pack(side="left", padx=2)
        
        self.chk_clear_field = ctk.CTkCheckBox(self.text_opts_frame, text="Limpar", width=60)
        self.chk_clear_field.pack(side="left", padx=2)

        # Actions Box
        self.action_box = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.action_box.pack(pady=5, padx=5, fill="x")

        self.btn_capture = ctk.CTkButton(self.action_box, text="Capturar (3s)", command=self.start_capture_thread, fg_color="orange")
        self.btn_capture.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_add = ctk.CTkButton(self.action_box, text="Adicionar Passo", command=self.add_step)
        self.btn_add.pack(side="left", padx=5, expand=True, fill="x")

        # Data & File Box
        self.file_box = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.file_box.pack(pady=5, padx=5, fill="x")
        
        self.btn_load_data = ctk.CTkButton(self.file_box, text="Carregar Dados (.txt)", command=self.load_data, fg_color="purple", width=120)
        self.btn_load_data.pack(side="left", padx=5)
        
        self.lbl_data_info = ctk.CTkLabel(self.file_box, text="Dados: 0 linhas", text_color="gray")
        self.lbl_data_info.pack(side="left", padx=5)

        # File Operations
        self.op_box = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.op_box.pack(pady=5, padx=5, fill="x")

        self.btn_save = ctk.CTkButton(self.op_box, text="Salvar JSON", command=self.save_sequence, fg_color="green", width=80)
        self.btn_save.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_load = ctk.CTkButton(self.op_box, text="Carregar JSON", command=self.load_sequence, fg_color="blue", width=80)
        self.btn_load.pack(side="left", padx=5, expand=True, fill="x")

        self.btn_clear = ctk.CTkButton(self.op_box, text="Limpar Lista", command=self.clear_list, fg_color="gray", width=80)
        self.btn_clear.pack(side="left", padx=5, expand=True, fill="x")

        self.chk_markers = ctk.CTkCheckBox(self.op_box, text="Marcadores", command=self.toggle_markers)
        self.chk_markers.pack(side="right", padx=5)

        # Lista de Passos
        self.list_frame = ctk.CTkScrollableFrame(self, label_text="Sequência de Passos")
        self.list_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Controles de Execução
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.btn_execute = ctk.CTkButton(self.control_frame, text="Executar Sequência", command=self.start_execution_thread, fg_color="green")
        self.btn_execute.pack(side="left", padx=5, pady=10, expand=True, fill="x")

        # Opções de Loop (Adicionado na Fase 4)
        self.loop_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.loop_frame.pack(side="left", padx=5)

        self.chk_infinite = ctk.CTkCheckBox(self.loop_frame, text="Loop Infinito", command=self.toggle_infinite_loop)
        self.chk_infinite.pack(side="top", pady=2)
        
        self.chk_confirm = ctk.CTkCheckBox(self.loop_frame, text="Confirmar Loops")
        self.chk_confirm.pack(side="top", pady=2)
        
        self.loop_count_frame = ctk.CTkFrame(self.loop_frame, fg_color="transparent")
        self.loop_count_frame.pack(side="top", pady=2)
        
        self.lbl_loops = ctk.CTkLabel(self.loop_count_frame, text="Loops:")
        self.lbl_loops.pack(side="left", padx=2)
        
        self.entry_loops = ctk.CTkEntry(self.loop_count_frame, width=40)
        self.entry_loops.insert(0, "1")
        self.entry_loops.pack(side="left", padx=2)

        self.btn_stop = ctk.CTkButton(self.control_frame, text="PARAR (F9)", command=self.stop_execution, fg_color="red")
        self.btn_stop.pack(side="left", padx=5, pady=10, expand=True, fill="x")
        
        # Status Bar
        self.lbl_status = ctk.CTkLabel(self, text="Pronto.")
        self.lbl_status.grid(row=3, column=0, sticky="w", padx=10, pady=5)

    def on_action_change(self, choice):
        if choice == "Digitar Texto":
            self.entry_text.pack(side="left", padx=5)
            self.text_opts_frame.pack(side="left", padx=5)
        else:
            self.entry_text.pack_forget()
            self.text_opts_frame.pack_forget()

    def load_data(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if filepath:
            try:
                count = self.engine.load_data_file(filepath)
                self.lbl_data_info.configure(text=f"Dados: {count} linhas")
                self.lbl_status.configure(text=f"Dados carregados: {filepath.split('/')[-1]}")
            except Exception as e:
                self.lbl_status.configure(text=f"Erro ao carregar dados: {e}", text_color="red")

    def toggle_infinite_loop(self):
        if self.chk_infinite.get():
            self.entry_loops.configure(state="disabled")
        else:
            self.entry_loops.configure(state="normal")

    def start_capture_thread(self):
        """Inicia a captura em uma thread separada para não travar a GUI."""
        self.lbl_status.configure(text="Capturando em 3 segundos...")
        threading.Thread(target=self._capture_position, daemon=True).start()

    def _capture_position(self):
        time.sleep(3)
        x, y = pyautogui.position()
        
        # Agenda a atualização da GUI para a thread principal
        self.after(0, lambda: self._update_capture_ui(x, y))

    def _update_capture_ui(self, x, y):
        self.entry_x.delete(0, "end")
        self.entry_x.insert(0, str(x))
        self.entry_y.delete(0, "end")
        self.entry_y.insert(0, str(y))
        self.lbl_status.configure(text=f"Capturado: {x}, {y}")

    def add_step(self):
        try:
            # Validação simples
            x_str = self.entry_x.get()
            y_str = self.entry_y.get()
            delay_str = self.entry_delay.get()

            if not x_str or not y_str or not delay_str:
                self.lbl_status.configure(text="Erro: Preencha todos os campos!", text_color="red")
                return

            x = int(x_str)
            y = int(y_str)
            delay = float(delay_str)
            action_choice = self.opt_action.get()
            
            # Mapeia gui choice para backend
            button = "left"
            action_type = "click"
            text_content = ""
            use_data_file = False
            clear_field = False
            
            if action_choice == "Click Left":
                button = "left"
            elif action_choice == "Click Right":
                button = "right"
            elif action_choice == "Digitar Texto":
                action_type = "type"
                text_content = self.entry_text.get()
                use_data_file = bool(self.chk_use_file.get())
                clear_field = bool(self.chk_clear_field.get())

            self.engine.add_step(x, y, delay, button, action_type, text_content, use_data_file, clear_field)
            self._refresh_list()
            self.lbl_status.configure(text="Passo adicionado.", text_color="white")
        except ValueError:
            self.lbl_status.configure(text="Erro: Valores inválidos (digite apenas números).", text_color="red")

    def _refresh_list(self):
        # Limpa markers antigos
        self._clear_markers()
        
        # Limpa o frame atual
        for widget in self.list_frame.winfo_children():
            widget.destroy()
            
        self.step_frames = [] # Armazena referências para highlight

        for i, step in enumerate(self.engine.steps):
            # Cria markers se checkbox ativo
            if self.markers_visible:
                # O master do marker pode ser o self (root)
                m = DraggableMarker(self, i, step.x, step.y, self.on_marker_move)
                self.markers.append(m)
            
            # Container do item
            item_frame = ctk.CTkFrame(self.list_frame, fg_color="transparent")
            item_frame.pack(fill="x", pady=2)
            self.step_frames.append(item_frame)
            
            # Label do passo
            # Se for type com clear, mostra o [LIMPAR]
            # Como atualizamos o __str__ no backend, isso deve aparecer automático
            lbl = ctk.CTkLabel(item_frame, text=f"{i+1}. {step}", anchor="w")
            lbl.pack(side="left", fill="x", expand=True, padx=5)
            
            # Botão de Remover (X)
            btn_remove = ctk.CTkButton(
                item_frame, 
                text="X", 
                width=30, 
                height=25, 
                fg_color="red", 
                command=lambda idx=i: self.remove_step_at(idx)
            )
            btn_remove.pack(side="right", padx=5)

    def _clear_markers(self):
        for m in self.markers:
            m.destroy()
        self.markers = []

    def toggle_markers(self):
        self.markers_visible = bool(self.chk_markers.get())
        self._refresh_list()

    def on_marker_move(self, index, new_x, new_y):
        """Callback chamado quando um marcador é solto."""
        if 0 <= index < len(self.engine.steps):
            step = self.engine.steps[index]
            step.x = new_x
            step.y = new_y
            print(f"Passo {index+1} atualizado para ({new_x}, {new_y})")
            # Recarrega a lista para mostrar novos valores
            self._refresh_list()

    def highlight_step(self, index):
        """Destaca o passo em execução."""
        # Reseta cor de todos
        for frame in self.step_frames:
            try:
                frame.configure(fg_color="transparent")
            except:
                pass # Widget pode ter sido destruído
        
        # Destaca o atual se índice válido
        if 0 <= index < len(self.step_frames):
            try:
                self.step_frames[index].configure(fg_color=("gray75", "gray25"))
            except:
                pass

    def remove_step_at(self, index):
        self.engine.remove_step(index)
        self._refresh_list()
        self.lbl_status.configure(text="Passo removido.")

    def start_execution_thread(self):
        if not self.engine.steps:
            self.lbl_status.configure(text="A lista de passos está vazia!", text_color="yellow")
            return
            
        # Pega configurações de loop
        try:
            loops = int(self.entry_loops.get())
        except ValueError:
            self.lbl_status.configure(text="Número de loops inválido!", text_color="red")
            return
            
        infinite = self.chk_infinite.get()
        confirm_loops = bool(self.chk_confirm.get())
            
        self.lbl_status.configure(text="Executando...", text_color="white")
        self.btn_execute.configure(state="disabled")
        threading.Thread(target=self._run_engine, args=(loops, infinite, confirm_loops), daemon=True).start()

    def _run_engine(self, loops, infinite, confirm_loops):
        def confirmation_callback(loop_num):
            # Esta função roda na thread da engine.
            # MessageBox no Python Tkinter no Windows geralmente bloqueia a thread chamadora
            # e exibe a GUI.
            return messagebox.askyesno("Confirmar Loop", f"Loop {loop_num-1} finalizado.\nIniciar Loop {loop_num}?")

        self.engine.execute_sequence(
            loops=loops, 
            infinite=infinite, 
            on_step_callback=lambda i: self.after(0, self.highlight_step, i),
            confirm_between_loops=confirm_loops,
            confirm_callback=confirmation_callback
        )
        # Restaura estado ao finalizar
        self.after(0, self._on_execution_finished)

    def _on_execution_finished(self):
        self.lbl_status.configure(text="Execução finalizada.")
        self.btn_execute.configure(state="normal")

    def stop_execution(self):
        if self.engine.is_running:
            self.engine.stop()
            self.lbl_status.configure(text="Parando...", text_color="yellow")

    def save_sequence(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                self.engine.save_to_file(filepath)
                self.lbl_status.configure(text=f"Salvo em {filepath.split('/')[-1]}")
            except Exception as e:
                self.lbl_status.configure(text=f"Erro ao salvar: {e}", text_color="red")


    def load_sequence(self):
        filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if filepath:
            try:
                self.engine.load_from_file(filepath)
                self._refresh_list()
                self.lbl_status.configure(text=f"Carregado de {filepath.split('/')[-1]}")
            except Exception as e:
                self.lbl_status.configure(text=f"Erro ao carregar: {e}", text_color="red")

    def clear_list(self):
        self.engine.clear_steps()
        self._refresh_list()
        self.lbl_status.configure(text="Lista limpa.")

if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
