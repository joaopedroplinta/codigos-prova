# Computação Gráfica — Códigos para Prova

Repositório com os códigos desenvolvidos para estudo e revisão da prova de Computação Gráfica.

## Conteúdo

| Arquivo | Descrição |
|---|---|
| `snake_prova.py` | Jogo Snake implementado com OpenGL (PyOpenGL + GLUT) |

## Tecnologias

- Python 3
- PyOpenGL (OpenGL, GLUT, GLU)

## Como executar

```bash
# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate

# Instale as dependências
pip install PyOpenGL PyOpenGL_accelerate

# Execute um dos scripts
python snake_prova.py
```

## Tópicos de Estudo

- Primitivas OpenGL
- Pipeline de renderização
- Transformações geométricas (translação, rotação, escala)
- Projeção ortográfica e perspectiva
- Animação com GLUT (`glutTimerFunc`)
- HUD e renderização de texto com bitmap fonts
