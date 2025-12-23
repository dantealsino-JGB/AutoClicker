import time
import pyautogui
import dataclasses
import json
import logging
import os
from typing import List, Literal, Optional

@dataclasses.dataclass
class ClickStep:
    """Representa um único passo de automação."""
    x: int
    y: int
    delay: float  # Tempo de espera APÓS a ação
    button: Literal['left', 'right', 'middle'] = 'left'
    action_type: Literal['click', 'type'] = 'click'
    text_content: str = ""
    use_data_file: bool = False # Se True, usa linha do arquivo carregado
    clear_field: bool = False # Se True, envia Ctrl+A + Del antes de digitar

    def __str__(self):
        if self.action_type == 'type':
            src = " (ARQUIVO)" if self.use_data_file else f" '{self.text_content}'"
            clear = " [LIMPAR]" if self.clear_field else ""
            return f"DIGITAR em ({self.x}, {self.y}):{src}{clear} - Delay: {self.delay}s"
        return f"CLIQUE {self.button.upper()} em ({self.x}, {self.y}) - Delay: {self.delay}s"

class AutomationEngine:
    """Gerencia a sequência de passos e a execução."""
    def __init__(self):
        self.steps: List[ClickStep] = []
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        self.data_lines: List[str] = []

    def load_data_file(self, filepath: str) -> int:
        """Carrega linhas de dados de um arquivo txt. Retorna qtd linhas."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.data_lines = [line.strip() for line in f.readlines() if line.strip()]
            self.logger.info(f"Dados carregados: {len(self.data_lines)} linhas.")
            return len(self.data_lines)
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo de dados: {e}")
            raise e

    def add_step(self, x: int, y: int, delay: float, button: str = 'left', action_type: str = 'click', text_content: str = "", use_data_file: bool = False, clear_field: bool = False):
        """Adiciona um novo passo à sequência."""
        step = ClickStep(x, y, delay, button, action_type, text_content, use_data_file, clear_field) # type: ignore
        self.steps.append(step)
        self.logger.info(f"Passo adicionado: {step}")
        print(f"Passo adicionado: {step}")

    def clear_steps(self):
        """Limpa toda a sequência."""
        self.steps.clear()
        self.logger.info("Sequência limpa.")
        print("Sequência limpa.")
    
    def get_steps(self) -> List[ClickStep]:
        return self.steps

    def remove_step(self, index: int):
        """Remove o passo no índice especificado."""
        if 0 <= index < len(self.steps):
            removed = self.steps.pop(index)
            self.logger.info(f"Passo removido: {removed}")
            print(f"Passo removido: {removed}")
        else:
            self.logger.warning(f"Tentativa de remover índice inválido: {index}")
            print(f"Índice inválido para remoção: {index}")

    def execute_sequence(self, loops: int = 1, infinite: bool = False, on_step_callback=None, confirm_between_loops: bool = False, confirm_callback=None):
        """
        Executa a lista de passos.
        :param confirm_between_loops: Se True, pede confirmação antes do próximo loop.
        :param confirm_callback: Função que retorna Bool (True=Continua, False=Para).
        """
        if not self.steps:
            self.logger.warning("Tentativa de executar lista vazia.")
            print("Nenhum passo para executar.")
            return

        loop_type = 'Infinito' if infinite else loops
        self.logger.info(f"Iniciando execução. Loops: {loop_type}, Total Passos: {len(self.steps)}")
        print(f"Iniciando execução. Loops: {loop_type}")
        
        self.is_running = True
        
        current_loop = 0
        
        try:
            while self.is_running:
                if not infinite and current_loop >= loops:
                    break
                
                # Confirmação entre loops (exceto o primeiro)
                if current_loop > 0 and confirm_between_loops and confirm_callback:
                    self.logger.info("Aguardando confirmação do usuário para próximo loop...")
                    should_continue = confirm_callback(current_loop + 1)
                    if not should_continue:
                        self.logger.info("Usuário cancelou no diálogo de confirmação.")
                        break

                current_loop += 1
                print(f"--- Loop {current_loop} ---")
                self.logger.info(f"Iniciando Loop {current_loop}")

                for i, step in enumerate(self.steps):
                    if not self.is_running:
                        self.logger.info("Execução interrompida pelo usuário (loop interno).")
                        break
                    
                    # Notifica a interface sobre o passo atual
                    if on_step_callback:
                        on_step_callback(i)
                    
                    # Resolve texto a ser digitado (Fixo ou do Arquivo)
                    text_to_type = step.text_content
                    if step.action_type == 'type' and step.use_data_file:
                        if self.data_lines:
                            # Usa índice do loop (0-based) mod len(lines) para ciclar se acabar
                            data_idx = (current_loop - 1) % len(self.data_lines)
                            text_to_type = self.data_lines[data_idx]
                            self.logger.info(f"Usando dados da linha {data_idx+1}: '{text_to_type}'")
                        else:
                            self.logger.warning("Passo configurado para usar arquivo, mas lista de dados está vazia!")
                            text_to_type = "SEM DADOS"

                    print(f"Executando passo {i+1}: {step}")
                    
                    # Move e Clica
                    try:
                        btn = step.button if step.action_type == 'click' else 'left'
                        self.logger.info(f"Executando ação no ponto ({step.x}, {step.y}) com botão: {btn.upper()}")
                        
                        # Garante movimento antes do clique
                        pyautogui.moveTo(step.x, step.y)
                        
                        # Pequeno delay para garantir que o mouse "assentou"
                        time.sleep(0.1)
                        
                        # Usa duration para segurar o clique por alguns milissegundos (simula humano)
                        if btn == 'right':
                            pyautogui.rightClick(duration=0.1)
                        elif btn == 'middle':
                            pyautogui.middleClick(duration=0.1)
                        else:
                            pyautogui.click(duration=0.1)
                        
                        # Se for ação de digitar, escreve o texto
                        if step.action_type == 'type':
                            # Limpar campo antes de digitar?
                            if step.clear_field:
                                self.logger.info("Limpando campo (Ctrl+A + Del)...")
                                time.sleep(0.1)
                                pyautogui.hotkey('ctrl', 'a')
                                time.sleep(0.1)
                                pyautogui.press('del')
                                time.sleep(0.1)

                            if text_to_type:
                                time.sleep(0.2) # Aumentado delay antes de digitar
                                pyautogui.write(text_to_type, interval=0.1) # Digitação mais lenta
                            
                    except Exception as e:
                        self.logger.error(f"Erro ao executar ação PyAutoGUI no passo {i+1}: {e}")
                        raise e
                    
                    # Aguarda o delay definido
                    time.sleep(step.delay)
            
            # Limpa destaque ao final
            if on_step_callback:
                on_step_callback(-1)
                
        except Exception as e:
            self.logger.error(f"Erro crítico durante a execução: {e}", exc_info=True)
            print(f"Erro durante a execução: {e}")
            if on_step_callback: on_step_callback(-1)
        finally:
            self.is_running = False
            self.logger.info("Execução finalizada.")
            print("Execução finalizada.")

    def stop(self):
        """Sinaliza para parar a execução."""
        self.is_running = False
        self.logger.info("Sinal de parada recebido.")
        print("Parando execução...")

    def save_to_file(self, filepath: str):
        """Salva a sequência atual em um arquivo JSON."""
        data = [dataclasses.asdict(step) for step in self.steps]
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            self.logger.info(f"Sequência salva em {filepath}")
            print(f"Sequência salva em {filepath}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar arquivo: {e}")
            raise e

    def load_from_file(self, filepath: str):
        """Carrega uma sequência de um arquivo JSON."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.steps.clear()
            for item in data:
                # Garante que os tipos estão corretos ao carregar
                # Compatibilidade com versões antigas (sem action_type)
                action = item.get('action_type', 'click')
                text = item.get('text_content', '')
                use_file = item.get('use_data_file', False) # Default False para retrocompatibilidade
                clear = item.get('clear_field', False)
                
                self.add_step(
                    x=int(item['x']),
                    y=int(item['y']),
                    delay=float(item['delay']),
                    button=str(item['button']),
                    action_type=str(action),
                    text_content=str(text),
                    use_data_file=bool(use_file),
                    clear_field=bool(clear)
                )
            self.logger.info(f"Sequência carregada de {filepath}")
            print(f"Sequência carregada de {filepath}")
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo: {e}")
            raise e
