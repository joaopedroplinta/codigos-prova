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
LARGURA      = 800
ALTURA       = 600
HUD_H        = 40
AREA_H       = ALTURA - HUD_H
VELOCIDADE_MS = 16          # ~60 fps
TAM_CARTA    = 80
ESPACAMENTO  = 20
LINHAS       = 4
COLUNAS      = 4
MARGEM_X     = (LARGURA - (COLUNAS * (TAM_CARTA + ESPACAMENTO))) // 2
MARGEM_Y     = (AREA_H  - (LINHAS  * (TAM_CARTA + ESPACAMENTO))) // 2

CORES_CARTAS_BASE = [
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0, 0.0),
    (1.0, 0.5, 0.0), (0.8, 0.0, 0.8), (0.0, 1.0, 1.0), (1.0, 0.5, 0.8),
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 1.0, 0.0),
    (1.0, 0.5, 0.0), (0.8, 0.0, 0.8), (0.0, 1.0, 1.0), (1.0, 0.5, 0.8),
]

# --- Estado do jogo ---
cores_cartas     = list(CORES_CARTAS_BASE)
cartas_viradas   = [False] * (LINHAS * COLUNAS)
cartas_combinadas = [False] * (LINHAS * COLUNAS)
primeira_carta   = None
segunda_carta    = None
aguardando       = False
movimentos       = 0
pares_encontrados = 0
estado           = 'MENU'   # 'MENU', 'JOGANDO', 'VITORIA'
tempo_inicio     = 0.0
tempo_atual      = 0.0

random.shuffle(cores_cartas)


def inicializar_jogo():
    global cores_cartas, cartas_viradas, cartas_combinadas
    global primeira_carta, segunda_carta, aguardando, movimentos
    global pares_encontrados, estado, tempo_inicio, tempo_atual
    cores_cartas      = list(CORES_CARTAS_BASE)
    random.shuffle(cores_cartas)
    cartas_viradas    = [False] * (LINHAS * COLUNAS)
    cartas_combinadas = [False] * (LINHAS * COLUNAS)
    primeira_carta    = None
    segunda_carta     = None
    aguardando        = False
    movimentos        = 0
    pares_encontrados = 0
    tempo_inicio      = time.time()
    tempo_atual       = 0.0
    estado            = 'JOGANDO'


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

def obter_indice_carta(mx, my):
    for i in range(LINHAS):
        for j in range(COLUNAS):
            cx = MARGEM_X + j * (TAM_CARTA + ESPACAMENTO)
            cy = MARGEM_Y + i * (TAM_CARTA + ESPACAMENTO)
            if cx <= mx <= cx + TAM_CARTA and cy <= my <= cy + TAM_CARTA:
                return i * COLUNAS + j
    return -1


def processar_clique(indice):
    global primeira_carta, segunda_carta, aguardando, movimentos
    global pares_encontrados, estado

    if estado != 'JOGANDO' or aguardando:
        return
    if cartas_combinadas[indice] or cartas_viradas[indice]:
        return

    if primeira_carta is None:
        primeira_carta = indice
        cartas_viradas[indice] = True
        glutPostRedisplay()
    elif segunda_carta is None and indice != primeira_carta:
        segunda_carta = indice
        cartas_viradas[indice] = True
        movimentos += 1
        glutPostRedisplay()

        if cores_cartas[primeira_carta] == cores_cartas[segunda_carta]:
            cartas_combinadas[primeira_carta] = True
            cartas_combinadas[segunda_carta]  = True
            pares_encontrados += 1
            primeira_carta = None
            segunda_carta  = None
            if all(cartas_combinadas):
                estado = 'VITORIA'
        else:
            aguardando = True
            glutTimerFunc(1000, virar_cartas, 0)


def virar_cartas(valor):
    global primeira_carta, segunda_carta, aguardando
    if primeira_carta is not None:
        cartas_viradas[primeira_carta] = False
    if segunda_carta is not None:
        cartas_viradas[segunda_carta] = False
    primeira_carta = None
    segunda_carta  = None
    aguardando     = False
    glutPostRedisplay()


# --- Desenho ---

def desenhar_carta(x, y, cor, virada, combinada):
    if combinada:
        glColor3f(0.7, 0.7, 0.7)
        retangulo(x, y, TAM_CARTA, TAM_CARTA)
        glColor3f(0.0, 0.85, 0.0)
        glLineWidth(3.0)
        glBegin(GL_LINES)
        glVertex2f(x + 20,           y + TAM_CARTA // 2)
        glVertex2f(x + TAM_CARTA // 2, y + TAM_CARTA - 20)
        glVertex2f(x + TAM_CARTA // 2, y + TAM_CARTA - 20)
        glVertex2f(x + TAM_CARTA - 20, y + 20)
        glEnd()
        glLineWidth(1.0)

    elif virada:
        glColor3f(*cor)
        retangulo(x, y, TAM_CARTA, TAM_CARTA)
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(2.0)
        retangulo_borda(x, y, TAM_CARTA, TAM_CARTA)
        glLineWidth(1.0)

    else:
        glColor3f(0.35, 0.35, 0.45)
        retangulo(x, y, TAM_CARTA, TAM_CARTA)
        glColor3f(0.6, 0.6, 0.75)
        glLineWidth(2.0)
        retangulo_borda(x, y, TAM_CARTA, TAM_CARTA)
        glLineWidth(1.0)
        glColor3f(0.6, 0.6, 0.75)
        glPointSize(8)
        glBegin(GL_POINTS)
        glVertex2f(x + TAM_CARTA // 2, y + TAM_CARTA // 2)
        glEnd()


def desenhar_tabuleiro():
    for i in range(LINHAS):
        for j in range(COLUNAS):
            idx = i * COLUNAS + j
            cx  = MARGEM_X + j * (TAM_CARTA + ESPACAMENTO)
            cy  = MARGEM_Y + i * (TAM_CARTA + ESPACAMENTO)
            desenhar_carta(cx, cy, cores_cartas[idx],
                           cartas_viradas[idx], cartas_combinadas[idx])


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
    total_pares = LINHAS * COLUNAS // 2

    glColor3f(0.6, 0.8, 1.0)
    desenhar_texto(16, CY - 9,
                   f'Pares: {pares_encontrados}/{total_pares}', escala=0.75)

    glColor3f(0.9, 0.9, 0.2)
    desenhar_texto(LARGURA // 2 - 70, CY - 9,
                   f'Moves: {movimentos}', escala=0.75)

    glColor3f(0.6, 0.8, 1.0)
    desenhar_texto(LARGURA - 135, CY - 9,
                   f'Tempo: {tempo_atual:.0f}s', escala=0.75)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.08, 0.08, 0.16)
    retangulo(0, 0, LARGURA, ALTURA)

    glColor3f(0.4, 0.5, 1.0)
    desenhar_texto(CX - 200, 460, 'JOGO DA MEMORIA', escala=1.4)

    BOX_W, BOX_H = 380, 170
    BOX_X = CX - BOX_W // 2
    BOX_Y = 248

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
    desenhar_texto(CX - 165, 378, 'Clique nas cartas para vira-las', escala=0.72)
    desenhar_texto(CX - 170, 352, 'Encontre todos os pares de cores', escala=0.72)
    total_pares = LINHAS * COLUNAS // 2
    desenhar_texto(CX - 85,  326, f'Total de pares: {total_pares}', escala=0.72)

    glColor3f(0.35, 0.35, 0.4)
    desenhar_texto(CX - 80, 282, 'ESPACO: jogar', escala=0.72)
    desenhar_texto(CX - 30, 262, 'Q: sair',       escala=0.72)

    glFlush()


def desenhar_vitoria():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.78)
    retangulo(CX - 230, CY - 90, 460, 180)
    glDisable(GL_BLEND)

    glColor3f(0.3, 0.9, 0.3)
    glLineWidth(2.0)
    retangulo_borda(CX - 230, CY - 90, 460, 180)
    glLineWidth(1.0)

    glColor3f(0.3, 1.0, 0.3)
    desenhar_texto(CX - 115, CY + 46, 'PARABENS!', escala=1.2)

    glColor3f(1.0, 1.0, 1.0)
    total_pares = LINHAS * COLUNAS // 2
    desenhar_texto(CX - 105, CY + 12,
                   f'Pares: {pares_encontrados}/{total_pares}', escala=0.9)
    desenhar_texto(CX - 95,  CY - 14,
                   f'Movimentos: {movimentos}', escala=0.9)
    desenhar_texto(CX - 85,  CY - 40,
                   f'Tempo: {tempo_atual:.1f}s', escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 70, 'ESPACO: novo jogo    Q: sair', escala=0.72)


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)

    glColor3f(0.08, 0.08, 0.16)
    retangulo(0, 0, LARGURA, AREA_H)

    desenhar_tabuleiro()
    desenhar_hud()

    if estado == 'VITORIA':
        desenhar_vitoria()

    glFlush()


def atualizar(valor=0):
    global tempo_atual
    if estado == 'JOGANDO':
        tempo_atual = time.time() - tempo_inicio
    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado e mouse ---

def tecla_normal(tecla, x, y):
    global estado
    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if tecla == ' ':
        if estado in ('MENU', 'VITORIA'):
            inicializar_jogo()
        glutPostRedisplay()


def mouse_clique(button, state, mx, my):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        my    = ALTURA - my
        indice = obter_indice_carta(mx, my)
        if indice != -1:
            processar_clique(indice)


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
    glutCreateWindow(b'Jogo da Memoria')

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    reshape(LARGURA, ALTURA)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(tecla_normal)
    glutMouseFunc(mouse_clique)
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)

    glutMainLoop()


if __name__ == '__main__':
    main()
