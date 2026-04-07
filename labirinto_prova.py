import os
import sys
import math
import random
import time

os.environ["WAYLAND_DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "x11"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Configurações ---
LARGURA  = 800
ALTURA   = 800
HUD_H    = 40          # altura do HUD em pixels (topo)
COLS     = 21          # deve ser ímpar para o algoritmo de labirinto
LINHAS   = 21
AREA_H   = ALTURA - HUD_H          # altura disponível para o labirinto
TAM_CEL  = min(LARGURA // COLS, AREA_H // LINHAS)   # tamanho de cada célula
OFF_X    = (LARGURA - COLS * TAM_CEL) // 2           # margem horizontal
OFF_Y    = (AREA_H  - LINHAS * TAM_CEL) // 2         # margem vertical (base)

# --- Estado global ---
# paredes[lin][col] = conjunto com 'N','S','E','O' indicando paredes presentes
paredes     = []
visitado    = []
jogador     = (0, 0)          # (col, lin)
saida       = (COLS - 1, LINHAS - 1)
estado      = 'AGUARDANDO'    # 'AGUARDANDO', 'JOGANDO', 'VITORIA'
passos      = 0
tempo_ini   = 0.0
tempo_fim   = 0.0
caminho_sol = []              # solução BFS (lista de (col,lin))
mostrar_sol = False


# ── Geração do labirinto (backtracking recursivo iterativo) ──────────────────

def gerar_labirinto():
    global paredes, visitado, caminho_sol, mostrar_sol

    mostrar_sol = False
    caminho_sol = []

    # Inicializa todas as paredes fechadas
    paredes  = [[{'N', 'S', 'E', 'O'} for _ in range(COLS)] for _ in range(LINHAS)]
    visitado = [[False] * COLS for _ in range(LINHAS)]

    DIRECOES = [('N', 0, -1), ('S', 0, 1), ('E', 1, 0), ('O', -1, 0)]
    OPOSTA   = {'N': 'S', 'S': 'N', 'E': 'O', 'O': 'E'}

    pilha = [(0, 0)]
    visitado[0][0] = True

    while pilha:
        col, lin = pilha[-1]
        vizinhos = []
        for direcao, dc, dl in DIRECOES:
            nc, nl = col + dc, lin + dl
            if 0 <= nc < COLS and 0 <= nl < LINHAS and not visitado[nl][nc]:
                vizinhos.append((direcao, nc, nl))

        if vizinhos:
            direcao, nc, nl = random.choice(vizinhos)
            # Remove paredes entre (col,lin) e (nc,nl)
            paredes[lin][col].discard(direcao)
            paredes[nl][nc].discard(OPOSTA[direcao])
            visitado[nl][nc] = True
            pilha.append((nc, nl))
        else:
            pilha.pop()


def resolver_bfs():
    """Retorna lista de (col,lin) do início até a saída."""
    from collections import deque
    sc, sl = 0, 0
    ec, el = saida
    fila    = deque([(sc, sl, [(sc, sl)])])
    vistos  = {(sc, sl)}
    DIR     = {'N': (0, -1), 'S': (0, 1), 'E': (1, 0), 'O': (-1, 0)}

    while fila:
        col, lin, caminho = fila.popleft()
        if (col, lin) == (ec, el):
            return caminho
        for direcao, (dc, dl) in DIR.items():
            if direcao not in paredes[lin][col]:
                nc, nl = col + dc, lin + dl
                if (nc, nl) not in vistos:
                    vistos.add((nc, nl))
                    fila.append((nc, nl, caminho + [(nc, nl)]))
    return []


# ── Conversão de coordenadas ─────────────────────────────────────────────────

def cel_para_px(col, lin):
    """Retorna o pixel (x, y) do canto inferior esquerdo da célula."""
    x = OFF_X + col * TAM_CEL
    y = OFF_Y + lin * TAM_CEL
    return x, y


# ── Funções de desenho auxiliares ────────────────────────────────────────────

def retangulo(x, y, w, h):
    glBegin(GL_POLYGON)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def retangulo_borda(x, y, w, h):
    glBegin(GL_LINE_LOOP)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def circulo(cx, cy, r, segs=20):
    glBegin(GL_POLYGON)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def desenhar_texto(x, y, texto, escala=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(escala * 0.12, escala * 0.12, 1)
    for c in texto:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
    glPopMatrix()


# ── Renderização do labirinto ─────────────────────────────────────────────────

def desenhar_fundo():
    glColor3f(0.06, 0.06, 0.10)
    retangulo(0, 0, LARGURA, ALTURA)


def desenhar_labirinto():
    esp = 2          # espessura extra das paredes (px)
    glColor3f(0.55, 0.65, 0.85)
    glLineWidth(2.0)

    for lin in range(LINHAS):
        for col in range(COLS):
            x, y = cel_para_px(col, lin)
            ps = paredes[lin][col]

            if 'N' in ps:          # N = lin-1 = borda inferior da célula
                glBegin(GL_LINES)
                glVertex2f(x,           y)
                glVertex2f(x + TAM_CEL, y)
                glEnd()
            if 'S' in ps:          # S = lin+1 = borda superior da célula
                glBegin(GL_LINES)
                glVertex2f(x,           y + TAM_CEL)
                glVertex2f(x + TAM_CEL, y + TAM_CEL)
                glEnd()
            if 'O' in ps:          # parede oeste
                glBegin(GL_LINES)
                glVertex2f(x, y)
                glVertex2f(x, y + TAM_CEL)
                glEnd()
            if 'E' in ps:          # parede leste
                glBegin(GL_LINES)
                glVertex2f(x + TAM_CEL, y)
                glVertex2f(x + TAM_CEL, y + TAM_CEL)
                glEnd()

    glLineWidth(1.0)

    # Borda externa reforçada
    bx = OFF_X
    by = OFF_Y
    bw = COLS * TAM_CEL
    bh = LINHAS * TAM_CEL
    glColor3f(0.7, 0.8, 1.0)
    glLineWidth(3.0)
    retangulo_borda(bx, by, bw, bh)
    glLineWidth(1.0)


def desenhar_saida():
    ec, el = saida
    x, y = cel_para_px(ec, el)
    m = 3
    # Fundo amarelo-dourado
    glColor3f(1.0, 0.85, 0.1)
    retangulo(x + m, y + m, TAM_CEL - 2*m, TAM_CEL - 2*m)
    # Estrela simples (dois triângulos)
    cx = x + TAM_CEL / 2
    cy = y + TAM_CEL / 2
    r1 = TAM_CEL * 0.32
    r2 = TAM_CEL * 0.15
    glColor3f(1.0, 0.55, 0.0)
    glBegin(GL_POLYGON)
    for i in range(10):
        a = math.pi / 2 + i * 2 * math.pi / 10
        r = r1 if i % 2 == 0 else r2
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def desenhar_solucao():
    if not caminho_sol:
        return
    glColor3f(0.2, 0.9, 0.5)
    glLineWidth(2.5)
    glBegin(GL_LINE_STRIP)
    for (c, l) in caminho_sol:
        x, y = cel_para_px(c, l)
        glVertex2f(x + TAM_CEL / 2, y + TAM_CEL / 2)
    glEnd()
    glLineWidth(1.0)


def desenhar_jogador():
    col, lin = jogador
    x, y = cel_para_px(col, lin)
    cx = x + TAM_CEL / 2
    cy = y + TAM_CEL / 2
    r  = TAM_CEL * 0.38

    # Sombra
    glColor3f(0.0, 0.15, 0.35)
    circulo(cx + 1, cy - 1, r, 28)

    # Corpo azul
    glColor3f(0.2, 0.55, 1.0)
    circulo(cx, cy, r, 28)

    # Brilho
    glColor3f(0.6, 0.85, 1.0)
    circulo(cx - r * 0.28, cy + r * 0.32, r * 0.28, 16)


def desenhar_inicio():
    x, y = cel_para_px(0, 0)
    m = 4
    glColor3f(0.2, 0.8, 0.2)
    retangulo(x + m, y + m, TAM_CEL - 2*m, TAM_CEL - 2*m)


def desenhar_hud():
    # Fundo HUD
    glColor3f(0.08, 0.08, 0.16)
    retangulo(0, ALTURA - HUD_H, LARGURA, HUD_H)
    glColor3f(0.3, 0.35, 0.6)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0,       ALTURA - HUD_H)
    glVertex2f(LARGURA, ALTURA - HUD_H)
    glEnd()
    glLineWidth(1.0)

    # Tempo
    if estado == 'JOGANDO':
        t = time.time() - tempo_ini
    elif estado == 'VITORIA':
        t = tempo_fim - tempo_ini
    else:
        t = 0.0
    mins  = int(t) // 60
    segs  = int(t) % 60
    texto_tempo = f"Tempo: {mins:02d}:{segs:02d}"

    glColor3f(0.9, 0.9, 1.0)
    desenhar_texto(12, ALTURA - 28, texto_tempo, escala=0.9)

    # Passos
    glColor3f(0.5, 0.85, 1.0)
    desenhar_texto(220, ALTURA - 28, f"Passos: {passos}", escala=0.9)

    # Dica tecla H
    glColor3f(0.35, 0.35, 0.55)
    desenhar_texto(500, ALTURA - 28, "H: dica   R: novo   Q: sair", escala=0.65)


def desenhar_tela_inicial():
    CX = LARGURA // 2
    CY = (ALTURA - HUD_H) // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.08, 0.82)
    retangulo(CX - 230, CY - 110, 460, 220)
    glDisable(GL_BLEND)

    glColor3f(0.35, 0.45, 0.9)
    glLineWidth(2.0)
    retangulo_borda(CX - 230, CY - 110, 460, 220)
    glLineWidth(1.0)

    glColor3f(0.5, 0.75, 1.0)
    desenhar_texto(CX - 115, CY + 70, "LABIRINTO", escala=1.5)

    glColor3f(0.9, 0.9, 0.2)
    desenhar_texto(CX - 150, CY + 22, "Pressione qualquer tecla!", escala=0.9)

    glColor3f(0.45, 0.45, 0.55)
    desenhar_texto(CX - 158, CY - 18, "Setas ou WASD para mover", escala=0.7)
    desenhar_texto(CX - 120, CY - 48, "H: mostrar dica (solucao)", escala=0.65)
    desenhar_texto(CX - 95,  CY - 74, "R: novo labirinto  Q: sair", escala=0.65)


def desenhar_tela_vitoria():
    CX = LARGURA // 2
    CY = (ALTURA - HUD_H) // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.1, 0.0, 0.82)
    retangulo(CX - 220, CY - 100, 440, 200)
    glDisable(GL_BLEND)

    glColor3f(0.2, 0.9, 0.3)
    glLineWidth(2.0)
    retangulo_borda(CX - 220, CY - 100, 440, 200)
    glLineWidth(1.0)

    glColor3f(0.3, 1.0, 0.4)
    desenhar_texto(CX - 148, CY + 52, "VOCE SAIU!", escala=1.4)

    t = tempo_fim - tempo_ini
    mins = int(t) // 60
    segs = int(t) % 60
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - 115, CY + 8, f"Tempo:  {mins:02d}:{segs:02d}", escala=1.0)
    desenhar_texto(CX - 115, CY - 24, f"Passos: {passos}", escala=1.0)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 64, "R: novo labirinto   Q: sair", escala=0.7)


# ── Loop principal ────────────────────────────────────────────────────────────

def display():
    glClear(GL_COLOR_BUFFER_BIT)

    desenhar_fundo()
    desenhar_labirinto()
    desenhar_inicio()
    desenhar_saida()

    if mostrar_sol:
        desenhar_solucao()

    desenhar_jogador()
    desenhar_hud()

    if estado == 'AGUARDANDO':
        desenhar_tela_inicial()
    elif estado == 'VITORIA':
        desenhar_tela_vitoria()

    glFlush()


def timer(valor=0):
    if estado == 'JOGANDO':
        glutPostRedisplay()
    glutTimerFunc(100, timer, 0)


# ── Entradas ──────────────────────────────────────────────────────────────────

def mover(dc, dl):
    global jogador, passos, estado, tempo_fim

    if estado != 'JOGANDO':
        return

    col, lin = jogador
    DIR_MAP = {(0, 1): 'S', (0, -1): 'N', (1, 0): 'E', (-1, 0): 'O'}
    direcao = DIR_MAP.get((dc, dl))
    if direcao is None:
        return
    if direcao in paredes[lin][col]:
        return  # parede bloqueando

    nc, nl = col + dc, lin + dl
    if 0 <= nc < COLS and 0 <= nl < LINHAS:
        jogador = (nc, nl)
        passos += 1
        if jogador == saida:
            estado    = 'VITORIA'
            tempo_fim = time.time()
        glutPostRedisplay()


def tecla_especial(tecla, x, y):
    global estado, tempo_ini
    if estado == 'VITORIA':
        return
    if estado == 'AGUARDANDO':
        estado    = 'JOGANDO'
        tempo_ini = time.time()
    if tecla == GLUT_KEY_UP:    mover( 0,  1)
    elif tecla == GLUT_KEY_DOWN:  mover( 0, -1)
    elif tecla == GLUT_KEY_LEFT:  mover(-1,  0)
    elif tecla == GLUT_KEY_RIGHT: mover( 1,  0)


def tecla_normal(tecla, x, y):
    global estado, mostrar_sol, caminho_sol, tempo_ini

    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):   # Q ou Esc
        os._exit(0)

    if tecla == 'r':
        inicializar()
        return

    if estado == 'VITORIA':
        return

    if estado == 'AGUARDANDO':
        estado    = 'JOGANDO'
        tempo_ini = time.time()

    if tecla == 'h':
        if not mostrar_sol:
            caminho_sol = resolver_bfs()
        mostrar_sol = not mostrar_sol
        glutPostRedisplay()
        return

    if tecla == 'w': mover( 0,  1)
    elif tecla == 's': mover( 0, -1)
    elif tecla == 'a': mover(-1,  0)
    elif tecla == 'd': mover( 1,  0)


# ── Inicialização ─────────────────────────────────────────────────────────────

def inicializar():
    global jogador, passos, estado, tempo_ini, tempo_fim, mostrar_sol, caminho_sol
    gerar_labirinto()
    jogador     = (0, 0)
    passos      = 0
    tempo_ini   = time.time()
    tempo_fim   = 0.0
    mostrar_sol = False
    caminho_sol = []
    estado      = 'AGUARDANDO'
    glutPostRedisplay()


def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, LARGURA, 0, ALTURA)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(LARGURA, ALTURA)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Labirinto")

    glClearColor(0.06, 0.06, 0.10, 1.0)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    reshape(LARGURA, ALTURA)
    inicializar()

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutSpecialFunc(tecla_especial)
    glutKeyboardFunc(tecla_normal)
    glutTimerFunc(100, timer, 0)

    glutMainLoop()


if __name__ == '__main__':
    main()
