# Computação Gráfica — Códigos para Prova

Repositório com os códigos desenvolvidos para estudo e revisão da prova de Computação Gráfica.

## Conteúdo

| Arquivo | Descrição | Conceitos em destaque |
|---|---|---|
| `snake_prova.py` | Jogo Snake | Grid, GL_POLYGON, GL_LINE_LOOP, animação por timer |
| `pong_prova.py` | Pong (1P vs CPU, 2P local, Solo contra a parede) | Colisão AABB, física de bola, `glutKeyboardUpFunc`, menu com 3 modos |
| `breakout_prova.py` | Breakout | Colisão bola×tijolo, múltiplas vidas, cores por linha |
| `asteroids_prova.py` | Asteroids | `glRotatef`, `glTranslatef`, `glPushMatrix`/`glPopMatrix`, wrap-around |
| `velha_prova.py` | Jogo da Velha | `glutMouseFunc`, coordenadas mouse→grade, IA Minimax |
| `labirinto_prova.py` | Labirinto | Geração por backtracking recursivo, BFS para solução, `GL_LINES` |
| `futebol_prova.py` | Futebol (1P vs CPU ou 2P) | Colisão circular jogador×bola, IA defensiva/ofensiva, `glutSpecialFunc`, menu interativo |
| `coletor_prova.py` | Coletor | Colisão AABB item×jogador, spawn aleatório, progressão de nível |
| `dodge_prova.py` | Dodge | Obstáculos das 4 bordas, colisão AABB, `circulo`/`circulo_borda` |
| `frogger_prova.py` | Frogger | Faixas de estrada/rio, movimento em troncos, múltiplas vidas, `glutSpecialFunc` |
| `memoria_prova.py` | Jogo da Memória | `glutMouseFunc`, coordenadas mouse→grade, timer para virar cartas |
| `space-invaders_prova.py` | Space Invaders | Frota de inimigos, power-ups, `GL_TRIANGLES`, estrelas fixas |

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

#Configurando para rodar no meu note (BigLinux)
alias pygl='env WAYLAND_DISPLAY="" PYOPENGL_PLATFORM=x11 python'

# Execute um dos scripts
python snake_prova.py

pygl snake_prova.py
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
| Geração procedural de labirinto (backtracking recursivo) | `labirinto_prova.py` |
| Busca em largura (BFS) | `labirinto_prova.py` |
| IA com comportamento defensivo/ofensivo | `futebol_prova.py` |
| Modo 1P vs CPU e 2P local | `futebol_prova.py`, `pong_prova.py` |
| Modo solo (pontuação por rebatida) | `pong_prova.py` |
| Spawn aleatório e progressão de nível | `coletor_prova.py`, `dodge_prova.py` |
| Movimento em plataformas (troncos) | `frogger_prova.py` |
| Timer para revelar/ocultar cartas | `memoria_prova.py` |
| Power-ups e `GL_TRIANGLES` | `space-invaders_prova.py` |
