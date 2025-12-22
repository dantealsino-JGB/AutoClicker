# Modular AutoClicker

Um automatizador de cliques modular e moderno, desenvolvido em Python. Permite criar sequências de cliques, definir delays, repetir ações em loop e salvar suas configurações.

## 🚀 Como Usar (Versão Executável)
A maneira mais fácil de usar, sem precisar instalar nada.

1.  Acesse a pasta `dist` dentro do projeto.
2.  Execute o arquivo **`ModularAutoClicker.exe`**.

---

## 🛠 Como Usar (Código Fonte)
Se preferir rodar pelo código ou fazer modificações:

### Pré-requisitos
- Python 3.10 ou superior instalado.

### Instalação
1.  Abra o terminal na pasta do projeto.
2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

### Execução
Rode o comando:
```bash
python main.py
```

---

## 📖 Manual de Instruções

### 1. Adicionando Passos
Existem duas formas de configurar onde o mouse deve clicar:

*   **Manual**: Digite as coordenadas X e Y e o tempo de Delay (espera após o clique) nos campos.
*   **Captura Automática (Recomendado)**:
    1.  Clique no botão laranja **`Capturar (3s)`**.
    2.  Você tem 3 segundos para posicionar o mouse no local desejado.
    3.  As coordenadas X e Y serão preenchidas automaticamente.
    4.  Defina o Delay.
    5.  Escolha a **Ação**:
        *   **Click Left/Right**: Clica com o botão do mouse.
        *   **Digitar Texto**: Abre uma caixa para escrever o texto que será digitado na automação.
    6.  Clique em **`Adicionar Passo`**.

### 2. Marcadores Visuais Interativos [NOVO]
*   Marque a caixa **`Marcadores Visuais`** para ver pequenos pontos vermelhos na tela indicando onde cada clique ocorrerá.
*   **Arrastar e Soltar**: Você pode clicar e arrastar esses pontos para ajustar a posição (X/Y) sem precisar digitar números. A lista atualiza automaticamente!

### 3. Gerenciando a Lista
*   **Visualizar**: Os passos aparecem na lista central.
*   **Remover**: Clique no botão vermelho **`X`** ao lado de um passo para apagá-lo.
*   **Limpar**: O botão `Limpar Lista` apaga tudo.

### 3. Executando a Sequência
*   **Loop Infinito**: Marque a caixa `Loop Infinito` para rodar sem parar.
*   **Contagem de Loops**: Se desmarcar o infinito, digite quantas vezes quer repetir no campo `Loops`.
*   **Iniciar**: Clique em **`Executar Sequência`** (Verde). O passo atual ficará destacado na lista.
*   **Parar**: Pressione a tecla **`F9`** a qualquer momento para abortar a automação imediatamente.

### 4. Salvar e Carregar
*   **Salvar JSON**: Salva sua sequência atual em um arquivo para uso futuro.
*   **Carregar JSON**: Recupera uma sequência salva anteriormente.
