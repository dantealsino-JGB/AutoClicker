import time
import pyautogui
import dataclasses
import json
import logging
from typing import List, Literal

@dataclasses.dataclass
class ClickStep:
    """Representa um único passo de automação."""
    x: int
    y: int
    delay: float  # Tempo de espera APÓS a ação
    button: Literal['left', 'right', 'middle'] = 'left'
    action_type: Literal['click', 'type'] = 'click'
    text_content: str = ""

    def __str__(self):
        if self.action_type == 'type':
            return f"DIGITAR em ({self.x}, {self.y}): '{self.text_content}' - Delay: {self.delay}s"
        return f"CLIQUE {self.button.upper()} em ({self.x}, {self.y}) - Delay: {self.delay}s"

class AutomationEngine:
    """Gerencia a sequência de passos e a execução."""
    def __init__(self):
        self.steps: List[ClickStep] = []
        self.is_running = False
        self.logger = logging.getLogger(__name__)

    def add_step(self, x: int, y: int, delay: float, button: str = 'left', action_type: str = 'click', text_content: str = ""):
        """Adiciona um novo passo à sequência."""
        step = ClickStep(x, y, delay, button, action_type, text_content) # type: ignore
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

    def execute_sequence(self, loops: int = 1, infinite: bool = False, on_step_callback=None):
        """
        Executa a lista de passos.
        :param loops: Número de repetições (se infinite=False)
        :param infinite: Se True, repete indefinidamente até parar.
        :param on_step_callback: Função callback(index) para notificar progresso.
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
                    
                    print(f"Executando passo {i+1}: {step}")
                    
                    # Move o mouse para a posição
                    try:
                        pyautogui.click(x=step.x, y=step.y, button=step.button if step.action_type == 'click' else 'left')
                        
                        # Se for ação de digitar, escreve o texto
                        if step.action_type == 'type' and step.text_content:
                            time.sleep(0.1)
                            pyautogui.write(step.text_content, interval=0.05)
                            
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
                
                self.add_step(
                    x=int(item['x']),
                    y=int(item['y']),
                    delay=float(item['delay']),
                    button=str(item['button']),
                    action_type=str(action),
                    text_content=str(text)
                )
            self.logger.info(f"Sequência carregada de {filepath}")
            print(f"Sequência carregada de {filepath}")
        except Exception as e:
            self.logger.error(f"Erro ao carregar arquivo: {e}")
            raise e
