import os
import sys
import math
import random

os.environ["WAYLAND_DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "x11"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Configurações ---
LARGURA        = 600
ALTURA         = 600
HUD_H          = 40
AREA_H         = ALTURA - HUD_H
VELOCIDADE_MS  = 16          # ~60 fps
TAM_JOGADOR    = 30
TAM_ITEM       = 20
VEL_JOGADOR    = 8
VEL_ITEM_BASE  = 3

# --- Estado do jogo ---
jogador_x        = LARGURA // 2
jogador_y        = 50
itens            = []
pontuacao        = 0
nivel            = 1
velocidade_atual = float(VEL_ITEM_BASE)
estado           = 'MENU'   # 'MENU', 'JOGANDO', 'GAME_OVER'
tecla_esq        = False
tecla_dir        = False

CORES_ITENS = [
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (1.0, 0.5, 0.0),
    (0.8, 0.0, 0.8),
]


def inicializar_jogo():
    global jogador_x, jogador_y, itens, pontuacao, nivel, velocidade_atual, estado
    jogador_x        = LARGURA // 2
    jogador_y        = 50
    itens            = []
    pontuacao        = 0
    nivel            = 1
    velocidade_atual = float(VEL_ITEM_BASE)
    estado           = 'JOGANDO'
    for _ in range(3):
        gerar_item()


# --- Helpers de desenho ---

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


def desenhar_texto(x, y, texto, escala=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(escala * 0.12, escala * 0.12, 1)
    for c in texto:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
    glPopMatrix()


# --- Lógica ---

def gerar_item():
    x   = random.randint(TAM_ITEM, LARGURA - TAM_ITEM)
    y   = AREA_H - TAM_ITEM
    cor = random.choice(CORES_ITENS)
    val = 10
    if random.random() < 0.2:
        cor = (0.0, 0.8, 0.0)
        val = 50
    itens.append([x, y, cor, val])


def mover_itens():
    global pontuacao, nivel, velocidade_atual

    r_j = TAM_JOGADOR // 2
    r_i = TAM_ITEM    // 2

    for item in itens[:]:
        item[1] -= velocidade_atual

        if (item[0] - r_i < jogador_x + r_j and
                item[0] + r_i > jogador_x - r_j and
                item[1] - r_i < jogador_y + r_j and
                item[1] + r_i > jogador_y - r_j):
            pontuacao += item[3]
            itens.remove(item)
            if pontuacao // 100 >= nivel:
                nivel            += 1
                velocidade_atual += 0.5
        elif item[1] + r_i < 0:
            itens.remove(item)


def mover_jogador():
    global jogador_x
    r = TAM_JOGADOR // 2
    if tecla_esq and jogador_x - r > 0:
        jogador_x -= VEL_JOGADOR
    if tecla_dir and jogador_x + r < LARGURA:
        jogador_x += VEL_JOGADOR


# --- Desenho ---

def desenhar_fundo():
    glColor3f(0.08, 0.08, 0.16)
    retangulo(0, 0, LARGURA, AREA_H)


def desenhar_chao():
    glColor3f(0.25, 0.25, 0.35)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(0,       jogador_y + TAM_JOGADOR // 2 + 2)
    glVertex2f(LARGURA, jogador_y + TAM_JOGADOR // 2 + 2)
    glEnd()
    glLineWidth(1.0)


def desenhar_jogador():
    r = TAM_JOGADOR // 2
    glColor3f(0.2, 0.4, 0.9)
    retangulo(jogador_x - r, jogador_y - r, TAM_JOGADOR, TAM_JOGADOR)
    glColor3f(0.6, 0.8, 1.0)
    glLineWidth(2.0)
    retangulo_borda(jogador_x - r, jogador_y - r, TAM_JOGADOR, TAM_JOGADOR)
    glLineWidth(1.0)


def desenhar_itens():
    r = TAM_ITEM // 2
    for item in itens:
        x, y, cor, val = item
        glColor3f(*cor)
        retangulo(x - r, y - r, TAM_ITEM, TAM_ITEM)
        if cor == (0.0, 0.8, 0.0):
            glColor3f(1.0, 1.0, 1.0)
            glPointSize(4)
            glBegin(GL_POINTS)
            glVertex2f(x, y)
            glEnd()


def desenhar_hud():
    glColor3f(0.05, 0.05, 0.10)
    retangulo(0, AREA_H, LARGURA, HUD_H)

    glColor3f(0.2, 0.25, 0.5)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0,       AREA_H)
    glVertex2f(LARGURA, AREA_H)
    glEnd()
    glLineWidth(1.0)

    CY = AREA_H + HUD_H // 2

    glColor3f(0.6, 0.8, 1.0)
    desenhar_texto(16, CY - 9, 'Pts:', escala=0.75)
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(72, CY - 9, str(pontuacao), escala=0.85)

    glColor3f(0.6, 0.8, 1.0)
    desenhar_texto(LARGURA // 2 - 50, CY - 9, f'Nivel: {nivel}', escala=0.75)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(LARGURA - 120, CY - 9, 'A/D mover', escala=0.55)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.08, 0.08, 0.16)
    retangulo(0, 0, LARGURA, ALTURA)

    glColor3f(0.2, 0.6, 1.0)
    desenhar_texto(CX - 110, 430, 'COLETOR', escala=1.6)

    BOX_W, BOX_H = 340, 180
    BOX_X = CX - BOX_W // 2
    BOX_Y = 220

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.1, 0.85)
    retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)

    glColor3f(0.2, 0.3, 0.6)
    glLineWidth(1.5)
    retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)
    glLineWidth(1.0)

    glColor3f(0.8, 0.8, 0.8)
    desenhar_texto(CX - 155, 356, 'Pegue os itens que caem!', escala=0.72)
    desenhar_texto(CX - 95,  330, 'Verdes valem 50 pts', escala=0.72)
    desenhar_texto(CX - 120, 304, 'A cada 100 pts o nivel sobe', escala=0.72)

    glColor3f(0.35, 0.35, 0.4)
    desenhar_texto(CX - 95, 258, 'A / D: mover', escala=0.72)
    desenhar_texto(CX - 92, 238, 'ESPACO: jogar', escala=0.72)
    desenhar_texto(CX - 30, 218, 'Q: sair', escala=0.72)

    glFlush()


def desenhar_game_over():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.78)
    retangulo(CX - 210, CY - 80, 420, 160)
    glDisable(GL_BLEND)

    glColor3f(1.0, 0.3, 0.3)
    glLineWidth(2.0)
    retangulo_borda(CX - 210, CY - 80, 420, 160)
    glLineWidth(1.0)

    glColor3f(1.0, 0.3, 0.3)
    desenhar_texto(CX - 120, CY + 36, 'GAME OVER', escala=1.2)

    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - 80, CY + 4, f'Pontos: {pontuacao}', escala=0.9)
    desenhar_texto(CX - 68, CY - 20, f'Nivel:  {nivel}', escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 52, 'ESPACO: menu    Q: sair', escala=0.72)


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    desenhar_fundo()
    desenhar_chao()
    desenhar_itens()
    desenhar_jogador()
    desenhar_hud()

    if estado == 'GAME_OVER':
        desenhar_game_over()

    glFlush()


def atualizar(valor=0):
    if estado == 'JOGANDO':
        mover_jogador()
        mover_itens()
        if random.random() < 0.05:
            gerar_item()
    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def tecla_normal(tecla, x, y):
    global tecla_esq, tecla_dir, estado
    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if tecla == ' ':
        if estado in ('MENU', 'GAME_OVER'):
            inicializar_jogo()
        glutPostRedisplay()
        return

    if estado == 'JOGANDO':
        if tecla == 'a':
            tecla_esq = True
        elif tecla == 'd':
            tecla_dir = True


def tecla_normal_up(tecla, x, y):
    global tecla_esq, tecla_dir
    tecla = tecla.decode('utf-8', errors='ignore').lower()
    if tecla == 'a':
        tecla_esq = False
    elif tecla == 'd':
        tecla_dir = False


def tecla_especial(tecla, x, y):
    global tecla_esq, tecla_dir
    if estado != 'JOGANDO':
        return
    if tecla == GLUT_KEY_LEFT:
        tecla_esq = True
    elif tecla == GLUT_KEY_RIGHT:
        tecla_dir = True


def tecla_especial_up(tecla, x, y):
    global tecla_esq, tecla_dir
    if tecla == GLUT_KEY_LEFT:
        tecla_esq = False
    elif tecla == GLUT_KEY_RIGHT:
        tecla_dir = False


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
    glutCreateWindow(b'Coletor')

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    reshape(LARGURA, ALTURA)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(tecla_normal)
    glutKeyboardUpFunc(tecla_normal_up)
    glutSpecialFunc(tecla_especial)
    glutSpecialUpFunc(tecla_especial_up)
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)

    glutMainLoop()


if __name__ == '__main__':
    main()
