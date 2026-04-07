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
LARGURA        = 800
ALTURA         = 600
HUD_H          = 40
AREA_H         = ALTURA - HUD_H
VELOCIDADE_MS  = 16          # ~60 fps
TAM_NAVE       = 30
TAM_TIRO       = 5
TAM_INIMIGO    = 30
VEL_NAVE       = 8
VEL_TIRO       = 8
VEL_INIMIGO    = 2

CORES_INIMIGOS = [
    (1.0, 0.0, 0.0),
    (1.0, 0.5, 0.0),
    (0.8, 0.0, 0.8),
    (0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0),
]

# Estrelas fixas para evitar cintilação
_ESTRELAS = [(random.randint(0, 800), random.randint(0, 560)) for _ in range(120)]

# --- Estado do jogo ---
nave_x                  = LARGURA // 2 - TAM_NAVE // 2
nave_y                  = 50
vidas                   = 3
pontuacao               = 0
nivel                   = 1
estado                  = 'MENU'   # 'MENU', 'JOGANDO', 'GAME_OVER'
tiros                   = []
inimigos                = []
direcao_inimigos        = 1
descida_inimigos        = 0
velocidade_inimigos_atual = VEL_INIMIGO
powerups                = []
powerup_ativo           = False
tempo_powerup           = 0
tecla_esq               = False
tecla_dir               = False
tempo_entre_tiros       = 0
tiro_rapido             = False


def inicializar_jogo():
    global nave_x, nave_y, vidas, pontuacao, nivel, estado
    global tiros, powerups, powerup_ativo, tiro_rapido
    global direcao_inimigos, descida_inimigos, velocidade_inimigos_atual
    nave_x                    = LARGURA // 2 - TAM_NAVE // 2
    nave_y                    = 50
    vidas                     = 3
    pontuacao                 = 0
    nivel                     = 1
    tiros                     = []
    powerups                  = []
    powerup_ativo             = False
    tiro_rapido               = False
    direcao_inimigos          = 1
    descida_inimigos          = 0
    velocidade_inimigos_atual = VEL_INIMIGO
    estado                    = 'JOGANDO'
    inicializar_inimigos()


def inicializar_inimigos():
    global inimigos
    inimigos   = []
    linhas     = 5
    colunas    = 8
    esp_x      = TAM_INIMIGO + 10
    esp_y      = TAM_INIMIGO + 10
    inicio_x   = (LARGURA - colunas * esp_x) // 2
    inicio_y   = AREA_H - 150
    for linha in range(linhas):
        for col in range(colunas):
            x   = inicio_x + col  * esp_x
            y   = inicio_y - linha * esp_y
            cor = CORES_INIMIGOS[linha % len(CORES_INIMIGOS)]
            inimigos.append([x, y, cor, True])


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


def desenhar_texto(x, y, texto, escala=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(escala * 0.12, escala * 0.12, 1)
    for c in texto:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
    glPopMatrix()


# --- Lógica ---

def verificar_colisao_aabb(x1, y1, w1, h1, x2, y2, w2, h2):
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)


def mover_inimigos():
    global direcao_inimigos, descida_inimigos, velocidade_inimigos_atual

    borda = False
    for inv in inimigos:
        if inv[3]:
            if inv[0] <= 0 or inv[0] + TAM_INIMIGO >= LARGURA:
                borda = True
                break

    if borda:
        direcao_inimigos *= -1
        descida_inimigos  = 20
    else:
        descida_inimigos  = 0

    for inv in inimigos:
        if inv[3]:
            inv[0] += velocidade_inimigos_atual * direcao_inimigos
            inv[1] -= descida_inimigos


def mover_tiros():
    global pontuacao, nivel, velocidade_inimigos_atual

    for tiro in tiros[:]:
        tiro[1] += VEL_TIRO
        if tiro[1] > AREA_H:
            tiros.remove(tiro)
            continue

        acertou = False
        for inv in inimigos:
            if inv[3] and verificar_colisao_aabb(
                    tiro[0], tiro[1], TAM_TIRO, TAM_TIRO,
                    inv[0],  inv[1],  TAM_INIMIGO, TAM_INIMIGO):
                inv[3]     = False
                acertou    = True
                pontuacao += 10

                if all(not i[3] for i in inimigos):
                    nivel                    += 1
                    velocidade_inimigos_atual += 0.5
                    inicializar_inimigos()

                if random.random() < 0.1:
                    powerups.append([inv[0], inv[1], True])
                break

        if acertou and tiro in tiros:
            tiros.remove(tiro)


def mover_powerups():
    global powerup_ativo, tempo_powerup, tiro_rapido

    for pu in powerups[:]:
        pu[1] -= 3
        if pu[1] < 0:
            powerups.remove(pu)
            continue
        if verificar_colisao_aabb(pu[0], pu[1], 15, 15,
                                   nave_x, nave_y, TAM_NAVE, TAM_NAVE):
            powerups.remove(pu)
            powerup_ativo = True
            tempo_powerup = 300
            tiro_rapido   = True


def verificar_colisao_inimigos():
    global vidas, estado, nave_x, nave_y

    for inv in inimigos:
        if inv[3]:
            if verificar_colisao_aabb(inv[0], inv[1], TAM_INIMIGO, TAM_INIMIGO,
                                       nave_x, nave_y, TAM_NAVE, TAM_NAVE):
                vidas -= 1
                if vidas <= 0:
                    estado = 'GAME_OVER'
                else:
                    nave_x = LARGURA // 2 - TAM_NAVE // 2
                    nave_y = 50
                return

            if inv[1] < nave_y + TAM_NAVE:
                vidas -= 1
                if vidas <= 0:
                    estado = 'GAME_OVER'
                return


def atualizar_powerup():
    global powerup_ativo, tempo_powerup, tiro_rapido
    if powerup_ativo:
        tempo_powerup -= 1
        if tempo_powerup <= 0:
            powerup_ativo = False
            tiro_rapido   = False


def atirar():
    global tempo_entre_tiros
    if estado != 'JOGANDO':
        return
    if tempo_entre_tiros <= 0:
        tx = nave_x + TAM_NAVE // 2 - TAM_TIRO // 2
        ty = nave_y + TAM_NAVE
        tiros.append([tx, ty])
        tempo_entre_tiros = 5 if tiro_rapido else 15
    else:
        tempo_entre_tiros -= 1


def mover_nave():
    global nave_x
    if estado != 'JOGANDO':
        return
    if tecla_esq and nave_x > 0:
        nave_x -= VEL_NAVE
    if tecla_dir and nave_x < LARGURA - TAM_NAVE:
        nave_x += VEL_NAVE


# --- Desenho ---

def desenhar_fundo():
    glColor3f(0.05, 0.05, 0.10)
    retangulo(0, 0, LARGURA, AREA_H)
    glColor3f(1.0, 1.0, 1.0)
    glPointSize(1)
    glBegin(GL_POINTS)
    for sx, sy in _ESTRELAS:
        glVertex2f(sx, sy)
    glEnd()


def desenhar_nave():
    x, y = nave_x, nave_y
    glColor3f(0.0, 0.85, 0.0)
    retangulo(x, y, TAM_NAVE, TAM_NAVE)
    glColor3f(1.0, 1.0, 1.0)
    glBegin(GL_TRIANGLES)
    glVertex2f(x + TAM_NAVE // 2,     y + TAM_NAVE)
    glVertex2f(x + TAM_NAVE // 2 - 8, y + TAM_NAVE - 10)
    glVertex2f(x + TAM_NAVE // 2 + 8, y + TAM_NAVE - 10)
    glEnd()
    glColor3f(0.0, 1.0, 1.0)
    retangulo(x + TAM_NAVE // 2 - 3, y + TAM_NAVE, 6, 10)


def desenhar_inimigos():
    for inv in inimigos:
        if not inv[3]:
            continue
        x, y, cor, _ = inv
        glColor3f(*cor)
        retangulo(x, y, TAM_INIMIGO, TAM_INIMIGO)
        glColor3f(1.0, 1.0, 1.0)
        glPointSize(4)
        glBegin(GL_POINTS)
        glVertex2f(x + 8,  y + 15)
        glVertex2f(x + 22, y + 15)
        glEnd()
        glColor3f(0.0, 0.0, 0.0)
        glPointSize(2)
        glBegin(GL_POINTS)
        glVertex2f(x + 8,  y + 15)
        glVertex2f(x + 22, y + 15)
        glEnd()


def desenhar_tiros():
    glColor3f(1.0, 1.0, 0.0)
    for tiro in tiros:
        retangulo(tiro[0], tiro[1], TAM_TIRO, TAM_TIRO)


def desenhar_powerups():
    for pu in powerups:
        x, y, _ = pu
        glColor3f(1.0, 0.5, 0.8)
        circulo(x + 7, y + 7, 8)
        glColor3f(1.0, 1.0, 1.0)
        glPointSize(3)
        glBegin(GL_POINTS)
        glVertex2f(x + 7, y + 7)
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
    desenhar_texto(16, CY - 9, f'Pts: {pontuacao}', escala=0.75)

    glColor3f(0.9, 0.9, 0.2)
    desenhar_texto(LARGURA // 2 - 60, CY - 9, f'Nivel: {nivel}', escala=0.75)

    for i in range(vidas):
        glColor3f(0.0, 0.85, 0.0)
        retangulo(LARGURA - 30 - i * 22, CY - 8, 16, 16)

    if powerup_ativo:
        glColor3f(1.0, 0.5, 0.8)
        desenhar_texto(LARGURA - 200, CY - 9, 'POWER-UP!', escala=0.72)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.05, 0.05, 0.10)
    retangulo(0, 0, LARGURA, ALTURA)

    glColor3f(1.0, 1.0, 1.0)
    glPointSize(1)
    glBegin(GL_POINTS)
    for sx, sy in _ESTRELAS:
        glVertex2f(sx, sy)
    glEnd()

    glColor3f(0.3, 1.0, 0.3)
    desenhar_texto(CX - 215, 460, 'SPACE INVADERS', escala=1.4)

    BOX_W, BOX_H = 400, 180
    BOX_X = CX - BOX_W // 2
    BOX_Y = 240

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.05, 0.85)
    retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)

    glColor3f(0.1, 0.4, 0.1)
    glLineWidth(1.5)
    retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)
    glLineWidth(1.0)

    glColor3f(0.8, 0.8, 0.8)
    desenhar_texto(CX - 155, 380, 'Destrua todos os invasores!', escala=0.72)
    desenhar_texto(CX - 155, 354, 'A/D ou setas: mover a nave', escala=0.72)
    desenhar_texto(CX - 165, 328, 'ESPACO ou seta cima: atirar', escala=0.72)
    desenhar_texto(CX - 155, 302, 'Power-ups rosas: tiro rapido', escala=0.72)

    glColor3f(0.35, 0.35, 0.4)
    desenhar_texto(CX - 80, 268, 'ESPACO: jogar', escala=0.72)
    desenhar_texto(CX - 30, 250, 'Q: sair',       escala=0.72)

    glFlush()


def desenhar_game_over():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.78)
    retangulo(CX - 220, CY - 80, 440, 160)
    glDisable(GL_BLEND)

    glColor3f(1.0, 0.3, 0.3)
    glLineWidth(2.0)
    retangulo_borda(CX - 220, CY - 80, 440, 160)
    glLineWidth(1.0)

    glColor3f(1.0, 0.3, 0.3)
    desenhar_texto(CX - 120, CY + 44, 'GAME OVER', escala=1.2)

    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - 90, CY + 10, f'Pontuacao: {pontuacao}', escala=0.9)
    desenhar_texto(CX - 65, CY - 16, f'Nivel: {nivel}', escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 52, 'ESPACO: menu    Q: sair', escala=0.72)


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    desenhar_fundo()
    desenhar_inimigos()
    desenhar_tiros()
    desenhar_powerups()
    desenhar_nave()
    desenhar_hud()

    if estado == 'GAME_OVER':
        desenhar_game_over()

    glFlush()


def atualizar(valor=0):
    global tempo_entre_tiros

    if estado == 'JOGANDO':
        mover_nave()
        mover_inimigos()
        mover_tiros()
        mover_powerups()
        verificar_colisao_inimigos()
        atualizar_powerup()
        if tempo_entre_tiros > 0:
            tempo_entre_tiros -= 1

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
        elif estado == 'JOGANDO':
            atirar()
        glutPostRedisplay()
        return

    if estado == 'JOGANDO':
        if tecla == 'a':   tecla_esq = True
        elif tecla == 'd': tecla_dir = True


def tecla_normal_up(tecla, x, y):
    global tecla_esq, tecla_dir
    tecla = tecla.decode('utf-8', errors='ignore').lower()
    if tecla == 'a':   tecla_esq = False
    elif tecla == 'd': tecla_dir = False


def tecla_especial(tecla, x, y):
    global tecla_esq, tecla_dir
    if estado != 'JOGANDO':
        return
    if tecla == GLUT_KEY_LEFT:   tecla_esq = True
    elif tecla == GLUT_KEY_RIGHT: tecla_dir = True
    elif tecla == GLUT_KEY_UP:    atirar()


def tecla_especial_up(tecla, x, y):
    global tecla_esq, tecla_dir
    if tecla == GLUT_KEY_LEFT:   tecla_esq = False
    elif tecla == GLUT_KEY_RIGHT: tecla_dir = False


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
    glutCreateWindow(b'Space Invaders')

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
