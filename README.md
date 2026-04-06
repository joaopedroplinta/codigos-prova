# Computação Gráfica — Códigos para Prova

Repositório com os códigos desenvolvidos para estudo e revisão da prova de Computação Gráfica.

## Conteúdo

| Arquivo | Descrição | Conceitos em destaque |
|---|---|---|
| `snake_prova.py` | Jogo Snake | Grid, GL_POLYGON, GL_LINE_LOOP, animação por timer |
| `pong_prova.py` | Pong (jogador vs CPU) | Colisão AABB, física de bola, `glutKeyboardUpFunc` |
| `breakout_prova.py` | Breakout | Colisão bola×tijolo, múltiplas vidas, cores por linha |
| `asteroids_prova.py` | Asteroids | `glRotatef`, `glTranslatef`, `glPushMatrix`/`glPopMatrix`, wrap-around |
| `velha_prova.py` | Jogo da Velha | `glutMouseFunc`, coordenadas mouse→grade, IA Minimax |

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

| Tópico | Onde ver |
|---|---|
| Primitivas (`GL_POLYGON`, `GL_LINES`, `GL_LINE_LOOP`, `GL_POINTS`) | todos os jogos |
| Projeção ortográfica (`gluOrtho2D`) | todos os jogos |
| Animação com timer (`glutTimerFunc`) | todos os jogos |
| Transparência (`GL_BLEND`, `glBlendFunc`) | todos (telas de overlay) |
| Texto com stroke font (`glutStrokeCharacter`) | todos os jogos |
| Transformações de modelo (`glTranslatef`, `glRotatef`, `glScalef`) | `asteroids_prova.py` |
| Push/Pop de matriz (`glPushMatrix`/`glPopMatrix`) | `asteroids_prova.py` |
| Colisão AABB | `pong_prova.py`, `breakout_prova.py` |
| Colisão circular (distância entre centros) | `asteroids_prova.py` |
| Teclado contínuo (`glutKeyboardUpFunc`, `glutSpecialUpFunc`) | `pong_prova.py`, `breakout_prova.py`, `asteroids_prova.py` |
| Entrada de mouse (`glutMouseFunc`, conversão pixel→jogo) | `velha_prova.py` |
| IA com Minimax | `velha_prova.py` |
