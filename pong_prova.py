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
LARGURA = 800
ALTURA  = 600
VELOCIDADE_MS = 16  # ~60 fps

PADDLE_W   = 14
PADDLE_H   = 80
PADDLE_VEL = 5
BOLA_R     = 8
VEL_INICIAL = 5.0

# --- Estado do jogo ---
paddle_esq = {'y': 0, 'score': 0}
paddle_dir = {'y': 0, 'score': 0}
bola       = {'x': 0.0, 'y': 0.0, 'vx': 0.0, 'vy': 0.0}
estado     = 'AGUARDANDO'
teclas     = set()

MARGEM_X_ESQ = 20
MARGEM_X_DIR = LARGURA - 20 - PADDLE_W
HUD_H        = 30  # barra no topo


def resetar_bola(direcao=1):
    bola['x']  = float(LARGURA // 2)
    bola['y']  = float(ALTURA  // 2)
    bola['vx'] = VEL_INICIAL * direcao
    bola['vy'] = VEL_INICIAL * random.choice([-1.0, 1.0]) * 0.6


def inicializar_jogo():
    global estado
    paddle_esq['y']     = ALTURA // 2 - PADDLE_H // 2
    paddle_dir['y']     = ALTURA // 2 - PADDLE_H // 2
    paddle_esq['score'] = 0
    paddle_dir['score'] = 0
    resetar_bola()
    estado = 'AGUARDANDO'


# --- Funções de desenho ---

def desenhar_retangulo(x, y, w, h):
    glBegin(GL_POLYGON)
    glVertex2f(x,     y)
    glVertex2f(x + w, y)
    glVertex2f(x + w, y + h)
    glVertex2f(x,     y + h)
    glEnd()


def desenhar_circulo(cx, cy, r, segs=20):
    glBegin(GL_POLYGON)
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


def desenhar_linha_central():
    """Linha tracejada no meio da tela."""
    glColor3f(0.25, 0.25, 0.25)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    y = 0
    while y < ALTURA - HUD_H:
        glVertex2f(LARGURA / 2, y)
        glVertex2f(LARGURA / 2, y + 15)
        y += 25
    glEnd()
    glLineWidth(1.0)


def desenhar_hud():
    # Fundo do HUD
    glColor3f(0.05, 0.05, 0.15)
    desenhar_retangulo(0, ALTURA - HUD_H, LARGURA, HUD_H)

    glColor3f(0.3, 0.3, 0.6)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, ALTURA - HUD_H)
    glVertex2f(LARGURA, ALTURA - HUD_H)
    glEnd()
    glLineWidth(1.0)

    # Placar
    glColor3f(0.9, 0.9, 0.9)
    desenhar_texto(LARGURA / 2 - 110, ALTURA - 23, str(paddle_esq['score']), escala=1.2)
    desenhar_texto(LARGURA / 2 +  70, ALTURA - 23, str(paddle_dir['score']), escala=1.2)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(10, ALTURA - 22, "W/S: mover", escala=0.7)
    glColor3f(0.9, 0.4, 0.4)
    desenhar_texto(LARGURA - 95, ALTURA - 22, "CPU", escala=0.7)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    glColor3f(0.04, 0.04, 0.04)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    desenhar_linha_central()

    # Paddle do jogador (esquerda — branco)
    glColor3f(0.95, 0.95, 0.95)
    desenhar_retangulo(MARGEM_X_ESQ, paddle_esq['y'], PADDLE_W, PADDLE_H)

    # Paddle da CPU (direita — vermelho)
    glColor3f(0.9, 0.3, 0.3)
    desenhar_retangulo(MARGEM_X_DIR, paddle_dir['y'], PADDLE_W, PADDLE_H)

    # Bola
    glColor3f(1.0, 1.0, 0.2)
    desenhar_circulo(bola['x'], bola['y'], BOLA_R, segs=18)
    # Brilho
    glColor3f(1.0, 1.0, 0.8)
    desenhar_circulo(bola['x'] - BOLA_R * 0.3, bola['y'] + BOLA_R * 0.3, BOLA_R * 0.3)

    desenhar_hud()

    if estado == 'AGUARDANDO':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.72)
        desenhar_retangulo(230, 240, 340, 130)
        glDisable(GL_BLEND)
        glColor3f(1.0, 1.0, 0.3)
        desenhar_texto(285, 330, "PONG", escala=1.8)
        glColor3f(0.85, 0.85, 0.85)
        desenhar_texto(245, 285, "Pressione ESPACO para jogar", escala=0.75)
        glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(278, 258, "R: reiniciar  Q: sair", escala=0.7)

    glFlush()


# --- Lógica de atualização ---

def atualizar(valor=0):
    if estado != 'JOGANDO':
        return

    area_max_y = ALTURA - HUD_H - PADDLE_H

    # Movimento do jogador
    if 'w' in teclas and paddle_esq['y'] < area_max_y:
        paddle_esq['y'] = min(paddle_esq['y'] + PADDLE_VEL, area_max_y)
    if 's' in teclas and paddle_esq['y'] > 0:
        paddle_esq['y'] = max(paddle_esq['y'] - PADDLE_VEL, 0)

    # CPU: acompanha a bola com velocidade limitada
    centro_cpu = paddle_dir['y'] + PADDLE_H / 2
    cpu_vel = PADDLE_VEL * 0.78
    if centro_cpu < bola['y'] - 4:
        paddle_dir['y'] = min(paddle_dir['y'] + cpu_vel, area_max_y)
    elif centro_cpu > bola['y'] + 4:
        paddle_dir['y'] = max(paddle_dir['y'] - cpu_vel, 0)

    # Move bola
    bola['x'] += bola['vx']
    bola['y'] += bola['vy']

    # Bounce teto e chão
    if bola['y'] - BOLA_R <= 0:
        bola['y'] = BOLA_R
        bola['vy'] = abs(bola['vy'])
    if bola['y'] + BOLA_R >= ALTURA - HUD_H:
        bola['y'] = ALTURA - HUD_H - BOLA_R
        bola['vy'] = -abs(bola['vy'])

    # Colisão paddle esquerdo
    if (bola['vx'] < 0
            and MARGEM_X_ESQ <= bola['x'] - BOLA_R <= MARGEM_X_ESQ + PADDLE_W
            and paddle_esq['y'] <= bola['y'] <= paddle_esq['y'] + PADDLE_H):
        bola['vx'] = abs(bola['vx']) * 1.04
        offset = (bola['y'] - (paddle_esq['y'] + PADDLE_H / 2)) / (PADDLE_H / 2)
        bola['vy'] = offset * 6.0

    # Colisão paddle direito
    if (bola['vx'] > 0
            and MARGEM_X_DIR <= bola['x'] + BOLA_R <= MARGEM_X_DIR + PADDLE_W
            and paddle_dir['y'] <= bola['y'] <= paddle_dir['y'] + PADDLE_H):
        bola['vx'] = -abs(bola['vx']) * 1.04
        offset = (bola['y'] - (paddle_dir['y'] + PADDLE_H / 2)) / (PADDLE_H / 2)
        bola['vy'] = offset * 6.0

    # Limitar velocidade máxima
    speed = math.hypot(bola['vx'], bola['vy'])
    if speed > 14.0:
        fator = 14.0 / speed
        bola['vx'] *= fator
        bola['vy'] *= fator

    # Ponto
    if bola['x'] < 0:
        paddle_dir['score'] += 1
        resetar_bola(direcao=1)
    elif bola['x'] > LARGURA:
        paddle_esq['score'] += 1
        resetar_bola(direcao=-1)

    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def teclado(tecla, x, y):
    global estado
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.add(tecla)

    if tecla in ('q', '\x1b'):
        os._exit(0)
    if tecla == 'r':
        inicializar_jogo()
        glutPostRedisplay()
        return
    if tecla == ' ' and estado == 'AGUARDANDO':
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


def teclado_up(tecla, x, y):
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.discard(tecla)


# --- Inicialização OpenGL ---

def inicializar_opengl():
    glClearColor(0.04, 0.04, 0.04, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, LARGURA, 0, ALTURA)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def main():
    inicializar_jogo()

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(LARGURA, ALTURA)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Pong - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutKeyboardUpFunc(teclado_up)

    glutMainLoop()


if __name__ == "__main__":
    main()
