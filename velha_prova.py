import os
import sys
import math

os.environ["WAYLAND_DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "x11"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Configurações ---
LARGURA  = 600
ALTURA   = 660     # 600 de grade + 60 de HUD no topo
HUD_H    = 60
CELL     = 200     # tamanho de cada célula (600 / 3)
PAD      = 30      # margem interna para X e O

COR_X       = (0.95, 0.35, 0.35)
COR_O       = (0.35, 0.65, 0.95)
COR_GRADE   = (0.55, 0.55, 0.55)
COR_VITORIA = (0.95, 0.85, 0.2)

# --- Estado ---
tabuleiro  = [[None] * 3 for _ in range(3)]   # None | 'X' | 'O'
vez        = 'X'        # quem joga agora
estado     = 'MENU'     # 'MENU' | 'JOGANDO' | 'FIM'
modo       = None       # '1P' | '2P'
opcao_menu = 0
vencedor   = None       # None | 'X' | 'O' | 'EMPATE'
linha_vit  = None       # [(lin,col),(lin,col),(lin,col)] da linha vencedora


# ---- Lógica do jogo ----

def reiniciar():
    global tabuleiro, vez, estado, vencedor, linha_vit
    tabuleiro = [[None] * 3 for _ in range(3)]
    vez       = 'X'
    estado    = 'JOGANDO'
    vencedor  = None
    linha_vit = None


def checar_vencedor(tab):
    """Retorna ('X'|'O', linha) ou (None, None) ou ('EMPATE', None)."""
    linhas = (
        # linhas
        [(0,0),(0,1),(0,2)], [(1,0),(1,1),(1,2)], [(2,0),(2,1),(2,2)],
        # colunas
        [(0,0),(1,0),(2,0)], [(0,1),(1,1),(2,1)], [(0,2),(1,2),(2,2)],
        # diagonais
        [(0,0),(1,1),(2,2)], [(0,2),(1,1),(2,0)],
    )
    for linha in linhas:
        vals = [tab[l][c] for l, c in linha]
        if vals[0] and vals[0] == vals[1] == vals[2]:
            return vals[0], linha

    # Empate?
    if all(tab[l][c] for l in range(3) for c in range(3)):
        return 'EMPATE', None

    return None, None


# ---- Minimax ----

def minimax(tab, is_max):
    """Retorna score: +1 (O vence), -1 (X vence), 0 (empate/em andamento)."""
    v, _ = checar_vencedor(tab)
    if v == 'O':  return 1
    if v == 'X':  return -1
    if v == 'EMPATE': return 0

    scores = []
    for l in range(3):
        for c in range(3):
            if tab[l][c] is None:
                tab[l][c] = 'O' if is_max else 'X'
                scores.append(minimax(tab, not is_max))
                tab[l][c] = None

    return max(scores) if is_max else min(scores)


def melhor_jogada():
    """Retorna (lin, col) da melhor jogada para a CPU (joga com 'O')."""
    melhor_score = -2
    melhor = None
    for l in range(3):
        for c in range(3):
            if tabuleiro[l][c] is None:
                tabuleiro[l][c] = 'O'
                score = minimax(tabuleiro, False)
                tabuleiro[l][c] = None
                if score > melhor_score:
                    melhor_score = score
                    melhor = (l, c)
    return melhor


def jogar(lin, col):
    """Executa a jogada na célula (lin, col). Atualiza estado."""
    global vez, estado, vencedor, linha_vit

    if tabuleiro[lin][col] is not None or estado != 'JOGANDO':
        return

    tabuleiro[lin][col] = vez
    v, lv = checar_vencedor(tabuleiro)
    if v:
        vencedor  = v
        linha_vit = lv
        estado    = 'FIM'
        glutPostRedisplay()
        return

    vez = 'O' if vez == 'X' else 'X'

    # CPU joga automaticamente no modo 1P
    if modo == '1P' and vez == 'O' and estado == 'JOGANDO':
        l, c = melhor_jogada()
        tabuleiro[l][c] = 'O'
        v, lv = checar_vencedor(tabuleiro)
        if v:
            vencedor  = v
            linha_vit = lv
            estado    = 'FIM'
        else:
            vez = 'X'

    glutPostRedisplay()


# ---- Coordenadas ----

def pixel_para_celula(px, py):
    """Converte coordenada de pixel (GLUT: y invertido) para (lin, col)."""
    # GLUT reporta y=0 no topo; gluOrtho2D tem y=0 em baixo
    gy = ALTURA - py          # converte para sistema OpenGL
    if gy < 0 or gy >= ALTURA - HUD_H:
        return None, None     # clique no HUD
    col = px // CELL
    lin = gy // CELL
    if 0 <= lin < 3 and 0 <= col < 3:
        return lin, col
    return None, None


# ---- Funções de desenho ----

def desenhar_retangulo(x, y, w, h):
    glBegin(GL_POLYGON)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def desenhar_retangulo_borda(x, y, w, h):
    glBegin(GL_LINE_LOOP)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def desenhar_circulo_borda(cx, cy, r, segs=40):
    glBegin(GL_LINE_LOOP)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def desenhar_texto(x, y, texto, escala=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(escala * 0.12, escala * 0.12, 1.0)
    for c in texto:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
    glPopMatrix()


def desenhar_grade():
    glColor3f(*COR_GRADE)
    glLineWidth(3.0)
    glBegin(GL_LINES)
    # Linhas verticais
    for c in range(1, 3):
        x = c * CELL
        glVertex2f(x, 0)
        glVertex2f(x, ALTURA - HUD_H)
    # Linhas horizontais
    for l in range(1, 3):
        y = l * CELL
        glVertex2f(0,      y)
        glVertex2f(LARGURA, y)
    glEnd()
    glLineWidth(1.0)


def desenhar_x(lin, col, cor):
    x0 = col * CELL + PAD
    y0 = lin * CELL + PAD
    x1 = (col + 1) * CELL - PAD
    y1 = (lin + 1) * CELL - PAD
    glColor3f(*cor)
    glLineWidth(8.0)
    glBegin(GL_LINES)
    glVertex2f(x0, y0);  glVertex2f(x1, y1)
    glVertex2f(x1, y0);  glVertex2f(x0, y1)
    glEnd()
    glLineWidth(1.0)


def desenhar_o(lin, col, cor):
    cx = col * CELL + CELL / 2
    cy = lin * CELL + CELL / 2
    r  = CELL / 2 - PAD
    glColor3f(*cor)
    glLineWidth(8.0)
    desenhar_circulo_borda(cx, cy, r, segs=48)
    glLineWidth(1.0)


def desenhar_peca(lin, col):
    v = tabuleiro[lin][col]
    if v == 'X':
        # Destaca se faz parte da linha vencedora
        if linha_vit and (lin, col) in linha_vit:
            desenhar_x(lin, col, COR_VITORIA)
        else:
            desenhar_x(lin, col, COR_X)
    elif v == 'O':
        if linha_vit and (lin, col) in linha_vit:
            desenhar_o(lin, col, COR_VITORIA)
        else:
            desenhar_o(lin, col, COR_O)


def desenhar_hud():
    CX = LARGURA // 2
    BASE_Y = ALTURA - HUD_H

    glColor3f(0.08, 0.08, 0.12)
    desenhar_retangulo(0, BASE_Y, LARGURA, HUD_H)
    glColor3f(0.25, 0.25, 0.4)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, BASE_Y);  glVertex2f(LARGURA, BASE_Y)
    glEnd()
    glLineWidth(1.0)

    if estado == 'JOGANDO':
        if vez == 'X':
            glColor3f(*COR_X)
            msg = "Vez do X"
        else:
            glColor3f(*COR_O)
            msg = "CPU (O)" if modo == '1P' else "Vez do O"
        larg = len(msg) * 104 * 0.12 * 1.1 / 2
        desenhar_texto(CX - larg, BASE_Y + 18, msg, escala=1.1)

    elif estado == 'FIM':
        if vencedor == 'EMPATE':
            glColor3f(0.85, 0.85, 0.85)
            msg = "Empate!"
        elif vencedor == 'X':
            glColor3f(*COR_X)
            msg = "X venceu!"
        else:
            glColor3f(*COR_O)
            msg = ("CPU venceu!" if modo == '1P' else "O venceu!")
        larg = len(msg) * 104 * 0.12 * 1.1 / 2
        desenhar_texto(CX - larg, BASE_Y + 18, msg, escala=1.1)

    glColor3f(0.35, 0.35, 0.35)
    desenhar_texto(10, BASE_Y + 14, "R: reiniciar", escala=0.65)
    desenhar_texto(LARGURA - 115, BASE_Y + 14, "M: menu", escala=0.65)


def desenhar_menu():
    CX = LARGURA // 2
    CY = ALTURA  // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.06, 0.06, 0.09)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    # Título
    glColor3f(0.85, 0.85, 0.85)
    desenhar_texto(CX - 158, CY + 155, "JOGO DA VELHA", escala=1.6)

    # X e O decorativos
    glColor3f(*COR_X)
    glLineWidth(5.0)
    glBegin(GL_LINES)
    glVertex2f(CX - 220, CY + 90);  glVertex2f(CX - 170, CY + 140)
    glVertex2f(CX - 170, CY + 90);  glVertex2f(CX - 220, CY + 140)
    glEnd()
    glColor3f(*COR_O)
    desenhar_circulo_borda(CX + 195, CY + 115, 28, segs=36)
    glLineWidth(1.0)

    # Caixa do menu
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.72)
    desenhar_retangulo(CX - 170, CY - 100, 340, 180)
    glDisable(GL_BLEND)
    glColor3f(0.22, 0.22, 0.38)
    desenhar_retangulo_borda(CX - 170, CY - 100, 340, 180)

    opcoes  = ["1 Jogador  (vs CPU)", "2 Jogadores"]
    largs   = [205, 120]
    ys      = [CY + 40, CY - 20]

    for i, label in enumerate(opcoes):
        y = ys[i]
        if i == opcao_menu:
            glColor3f(0.18, 0.18, 0.42)
            desenhar_retangulo(CX - 162, y - 8, 324, 34)
            glColor3f(0.45, 0.55, 1.0)
            glLineWidth(1.5)
            desenhar_retangulo_borda(CX - 162, y - 8, 324, 34)
            glLineWidth(1.0)
            glColor3f(1.0, 1.0, 0.4)
            desenhar_texto(CX - 158, y + 4, ">", escala=0.9)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(0.52, 0.52, 0.52)
        desenhar_texto(CX - largs[i] // 2, y + 4, label, escala=0.9)

    glColor3f(0.35, 0.35, 0.35)
    desenhar_texto(CX - 95, CY - 62, "W/S ou Setas: navegar", escala=0.65)
    desenhar_texto(CX - 75, CY - 80, "ESPACO: confirmar", escala=0.65)

    glFlush()


def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)

    # Fundo
    glColor3f(0.06, 0.06, 0.09)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    # Fundo suave alternado nas células
    for l in range(3):
        for c in range(3):
            if (l + c) % 2 == 0:
                glColor3f(0.09, 0.09, 0.13)
            else:
                glColor3f(0.07, 0.07, 0.10)
            desenhar_retangulo(c * CELL, l * CELL, CELL, CELL)

    desenhar_grade()

    for l in range(3):
        for c in range(3):
            desenhar_peca(l, c)

    desenhar_hud()

    # Overlay de fim de jogo
    if estado == 'FIM':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.45)
        desenhar_retangulo(0, 0, LARGURA, ALTURA - HUD_H)
        glDisable(GL_BLEND)

        glColor3f(0.85, 0.85, 0.85)
        CX = LARGURA // 2
        CY = (ALTURA - HUD_H) // 2
        desenhar_texto(CX - 140, CY - 5, "ESPACO para jogar de novo", escala=0.85)

    glFlush()


# ---- Entrada ----

def mouse(botao, acao, px, py):
    """glutMouseFunc: (botao, GLUT_DOWN/UP, x_pixel, y_pixel)."""
    if botao != GLUT_LEFT_BUTTON or acao != GLUT_DOWN:
        return
    if estado != 'JOGANDO':
        return
    if modo == '1P' and vez == 'O':
        return  # bloqueia clique enquanto CPU "pensa"
    lin, col = pixel_para_celula(px, py)
    if lin is not None:
        jogar(lin, col)


def teclado(tecla, x, y):
    global estado, modo, opcao_menu
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if estado == 'MENU':
        if tecla == ' ':
            modo = ['1P', '2P'][opcao_menu]
            reiniciar()
            glutPostRedisplay()
        elif tecla == 'w':
            opcao_menu = (opcao_menu - 1) % 2
            glutPostRedisplay()
        elif tecla == 's':
            opcao_menu = (opcao_menu + 1) % 2
            glutPostRedisplay()
        return

    if tecla == 'm':
        estado    = 'MENU'
        opcao_menu = 0
        glutPostRedisplay()
        return
    if tecla == 'r':
        reiniciar()
        glutPostRedisplay()
        return
    if tecla == ' ' and estado == 'FIM':
        reiniciar()
        glutPostRedisplay()


def teclado_especial(tecla, x, y):
    global opcao_menu
    if estado == 'MENU':
        if tecla == GLUT_KEY_UP:
            opcao_menu = (opcao_menu - 1) % 2
            glutPostRedisplay()
        elif tecla == GLUT_KEY_DOWN:
            opcao_menu = (opcao_menu + 1) % 2
            glutPostRedisplay()


# ---- Inicialização OpenGL ----

def inicializar_opengl():
    glClearColor(0.06, 0.06, 0.09, 1.0)
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
    glutCreateWindow(b"Jogo da Velha - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclado_especial)
    glutMouseFunc(mouse)        # entrada de mouse

    glutMainLoop()


if __name__ == "__main__":
    main()
