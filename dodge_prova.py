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
TAM_JOGADOR    = 20
TAM_OBSTACULO  = 25
VEL_JOGADOR    = 7
VEL_OBS_BASE   = 4

# --- Estado do jogo ---
jogador_x          = LARGURA // 2
jogador_y          = AREA_H  // 2
obstaculos         = []
pontuacao          = 0
tempo_sobrevivencia = 0.0
dificuldade        = 1
velocidade_atual   = float(VEL_OBS_BASE)
estado             = 'MENU'   # 'MENU', 'JOGANDO', 'GAME_OVER'
tecla_cima         = False
tecla_baixo        = False
tecla_esq          = False
tecla_dir          = False

CORES_OBS = [
    (1.0, 0.0, 0.0),
    (1.0, 1.0, 0.0),
    (1.0, 0.5, 0.0),
    (0.8, 0.0, 0.8),
]


def inicializar_jogo():
    global jogador_x, jogador_y, obstaculos, pontuacao
    global tempo_sobrevivencia, dificuldade, velocidade_atual, estado
    jogador_x           = LARGURA // 2
    jogador_y           = AREA_H  // 2
    obstaculos          = []
    pontuacao           = 0
    tempo_sobrevivencia = 0.0
    dificuldade         = 1
    velocidade_atual    = float(VEL_OBS_BASE)
    estado              = 'JOGANDO'
    for _ in range(3):
        gerar_obstaculo()


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


def circulo(cx, cy, r, segs=24):
    glBegin(GL_POLYGON)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        glVertex2f(cx + r * math.cos(a), cy + r * math.sin(a))
    glEnd()


def circulo_borda(cx, cy, r, segs=48):
    glBegin(GL_LINE_LOOP)
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


# --- Lógica ---

def gerar_obstaculo():
    lado = random.randint(0, 3)
    r    = TAM_OBSTACULO // 2

    if lado == 0:   # cima
        x  = random.randint(r, LARGURA - r)
        y  = AREA_H - r
        dx = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        dy = -random.uniform(0.5, 1.5)
    elif lado == 1: # baixo
        x  = random.randint(r, LARGURA - r)
        y  = r
        dx = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        dy = random.uniform(0.5, 1.5)
    elif lado == 2: # esquerda
        x  = r
        y  = random.randint(r, AREA_H - r)
        dx = random.uniform(0.5, 1.5)
        dy = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
    else:           # direita
        x  = LARGURA - r
        y  = random.randint(r, AREA_H - r)
        dx = -random.uniform(0.5, 1.5)
        dy = random.choice([-1, 1]) * random.uniform(0.5, 1.5)

    cor = random.choice(CORES_OBS)
    obstaculos.append([x, y, cor, dx, dy])


def mover_obstaculos():
    global estado
    r_o = TAM_OBSTACULO // 2
    r_j = TAM_JOGADOR   // 2

    for obs in obstaculos[:]:
        obs[0] += obs[3] * (velocidade_atual / 2)
        obs[1] += obs[4] * (velocidade_atual / 2)

        if (obs[0] - r_o < jogador_x + r_j and
                obs[0] + r_o > jogador_x - r_j and
                obs[1] - r_o < jogador_y + r_j and
                obs[1] + r_o > jogador_y - r_j):
            estado = 'GAME_OVER'
            return

        if (obs[0] + r_o < 0 or obs[0] - r_o > LARGURA or
                obs[1] + r_o < 0 or obs[1] - r_o > AREA_H):
            obstaculos.remove(obs)


def mover_jogador():
    global jogador_x, jogador_y
    r = TAM_JOGADOR // 2
    if tecla_cima  and jogador_y + r < AREA_H:   jogador_y += VEL_JOGADOR
    if tecla_baixo and jogador_y - r > 0:         jogador_y -= VEL_JOGADOR
    if tecla_esq   and jogador_x - r > 0:         jogador_x -= VEL_JOGADOR
    if tecla_dir   and jogador_x + r < LARGURA:   jogador_x += VEL_JOGADOR


def atualizar_dificuldade():
    global dificuldade, velocidade_atual
    if pontuacao // 100 >= dificuldade:
        dificuldade      += 1
        velocidade_atual += 0.3


# --- Desenho ---

def desenhar_fundo():
    glColor3f(0.05, 0.05, 0.10)
    retangulo(0, 0, LARGURA, AREA_H)


def desenhar_jogador():
    r = TAM_JOGADOR // 2
    glColor3f(0.2, 0.4, 0.9)
    circulo(jogador_x, jogador_y, r)
    glColor3f(0.6, 0.8, 1.0)
    circulo_borda(jogador_x, jogador_y, r)
    glColor3f(1.0, 1.0, 1.0)
    glPointSize(3)
    glBegin(GL_POINTS)
    glVertex2f(jogador_x - 5, jogador_y + 4)
    glVertex2f(jogador_x + 5, jogador_y + 4)
    glEnd()


def desenhar_obstaculos():
    r = TAM_OBSTACULO // 2
    for obs in obstaculos:
        x, y, cor, dx, dy = obs
        glColor3f(*cor)
        retangulo(x - r, y - r, TAM_OBSTACULO, TAM_OBSTACULO)
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.0)
        retangulo_borda(x - r, y - r, TAM_OBSTACULO, TAM_OBSTACULO)


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
    desenhar_texto(16, CY - 9, f'Pts: {pontuacao}', escala=0.75)

    glColor3f(0.9, 0.9, 0.2)
    desenhar_texto(LARGURA // 2 - 80, CY - 9,
                   f'Tempo: {tempo_sobrevivencia:.1f}s', escala=0.75)

    glColor3f(0.6, 0.8, 1.0)
    desenhar_texto(LARGURA - 120, CY - 9, f'Dif: {dificuldade}', escala=0.75)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.05, 0.05, 0.10)
    retangulo(0, 0, LARGURA, ALTURA)

    glColor3f(0.8, 0.3, 0.3)
    desenhar_texto(CX - 90, 430, 'DODGE', escala=1.6)

    BOX_W, BOX_H = 340, 160
    BOX_X = CX - BOX_W // 2
    BOX_Y = 240

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.05, 0.0, 0.0, 0.85)
    retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)

    glColor3f(0.4, 0.1, 0.1)
    glLineWidth(1.5)
    retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)
    glLineWidth(1.0)

    glColor3f(0.8, 0.8, 0.8)
    desenhar_texto(CX - 145, 366, 'Desvie dos obstaculos!', escala=0.72)
    desenhar_texto(CX - 130, 340, 'WASD ou setas: mover', escala=0.72)
    desenhar_texto(CX - 95,  314, 'A cada 100 pts: +dif', escala=0.72)

    glColor3f(0.35, 0.35, 0.4)
    desenhar_texto(CX - 92, 268, 'ESPACO: jogar', escala=0.72)
    desenhar_texto(CX - 30, 248, 'Q: sair',       escala=0.72)

    glFlush()


def desenhar_game_over():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.78)
    retangulo(CX - 210, CY - 90, 420, 180)
    glDisable(GL_BLEND)

    glColor3f(1.0, 0.3, 0.3)
    glLineWidth(2.0)
    retangulo_borda(CX - 210, CY - 90, 420, 180)
    glLineWidth(1.0)

    glColor3f(1.0, 0.3, 0.3)
    desenhar_texto(CX - 120, CY + 48, 'GAME OVER', escala=1.2)

    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - 80, CY + 14, f'Pontos: {pontuacao}', escala=0.9)
    desenhar_texto(CX - 105, CY - 12,
                   f'Tempo:  {tempo_sobrevivencia:.1f}s', escala=0.9)
    desenhar_texto(CX - 80, CY - 38, f'Dif:    {dificuldade}', escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 68, 'ESPACO: menu    Q: sair', escala=0.72)


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    desenhar_fundo()
    desenhar_obstaculos()
    desenhar_jogador()
    desenhar_hud()

    if estado == 'GAME_OVER':
        desenhar_game_over()

    glFlush()


def atualizar(valor=0):
    global tempo_sobrevivencia, pontuacao

    if estado == 'JOGANDO':
        mover_jogador()
        mover_obstaculos()
        tempo_sobrevivencia += VELOCIDADE_MS / 1000.0
        pontuacao = int(tempo_sobrevivencia * 10)
        atualizar_dificuldade()

        if random.random() < 0.03 + dificuldade * 0.005:
            gerar_obstaculo()

    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def tecla_normal(tecla, x, y):
    global tecla_cima, tecla_baixo, tecla_esq, tecla_dir, estado
    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if tecla == ' ':
        if estado in ('MENU', 'GAME_OVER'):
            inicializar_jogo()
        glutPostRedisplay()
        return

    if estado == 'JOGANDO':
        if tecla == 'w':   tecla_cima  = True
        elif tecla == 's': tecla_baixo = True
        elif tecla == 'a': tecla_esq   = True
        elif tecla == 'd': tecla_dir   = True


def tecla_normal_up(tecla, x, y):
    global tecla_cima, tecla_baixo, tecla_esq, tecla_dir
    tecla = tecla.decode('utf-8', errors='ignore').lower()
    if tecla == 'w':   tecla_cima  = False
    elif tecla == 's': tecla_baixo = False
    elif tecla == 'a': tecla_esq   = False
    elif tecla == 'd': tecla_dir   = False


def tecla_especial(tecla, x, y):
    global tecla_cima, tecla_baixo, tecla_esq, tecla_dir
    if estado != 'JOGANDO':
        return
    if tecla == GLUT_KEY_UP:    tecla_cima  = True
    elif tecla == GLUT_KEY_DOWN:  tecla_baixo = True
    elif tecla == GLUT_KEY_LEFT:  tecla_esq   = True
    elif tecla == GLUT_KEY_RIGHT: tecla_dir   = True


def tecla_especial_up(tecla, x, y):
    global tecla_cima, tecla_baixo, tecla_esq, tecla_dir
    if tecla == GLUT_KEY_UP:    tecla_cima  = False
    elif tecla == GLUT_KEY_DOWN:  tecla_baixo = False
    elif tecla == GLUT_KEY_LEFT:  tecla_esq   = False
    elif tecla == GLUT_KEY_RIGHT: tecla_dir   = False


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
    glutCreateWindow(b'Dodge')

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
