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

PADDLE_W   = 100
PADDLE_H   = 14
PADDLE_Y   = 30
PADDLE_VEL = 7

BOLA_R   = 8
VEL_BOLA = 5.5

TIJOLO_COLS  = 10
TIJOLO_LINHAS = 6
TIJOLO_W = LARGURA // TIJOLO_COLS
TIJOLO_H = 24
TIJOLO_Y_INI = ALTURA - 80 - TIJOLO_LINHAS * TIJOLO_H  # começa abaixo do HUD

HUD_H = 30
VIDAS_MAX = 3

# Cores por linha (RGB)
CORES_LINHAS = [
    (0.95, 0.25, 0.25),  # vermelho
    (0.95, 0.55, 0.15),  # laranja
    (0.95, 0.90, 0.15),  # amarelo
    (0.25, 0.85, 0.25),  # verde
    (0.25, 0.55, 0.95),  # azul
    (0.75, 0.25, 0.95),  # roxo
]

# --- Estado do jogo ---
paddle_x = 0.0
bola     = {'x': 0.0, 'y': 0.0, 'vx': 0.0, 'vy': 0.0, 'ativa': False}
tijolos  = []   # lista de [col, lin, vivo]
pontuacao = 0
vidas    = VIDAS_MAX
estado   = 'AGUARDANDO'
teclas   = set()


def inicializar_tijolos():
    global tijolos
    tijolos = [
        [c, l, True]
        for l in range(TIJOLO_LINHAS)
        for c in range(TIJOLO_COLS)
    ]


def posicao_tijolo(col, lin):
    """Retorna (x, y) do canto inferior esquerdo do tijolo."""
    x = col * TIJOLO_W
    y = TIJOLO_Y_INI + lin * TIJOLO_H
    return x, y


def resetar_bola():
    bola['x']    = paddle_x + PADDLE_W / 2
    bola['y']    = PADDLE_Y + PADDLE_H + BOLA_R + 2
    angle = math.radians(random.uniform(50, 130))
    bola['vx']   = VEL_BOLA * math.cos(angle)
    bola['vy']   = VEL_BOLA * math.sin(angle)
    bola['ativa'] = False


def inicializar_jogo():
    global paddle_x, pontuacao, vidas, estado
    paddle_x  = LARGURA / 2 - PADDLE_W / 2
    pontuacao = 0
    vidas     = VIDAS_MAX
    estado    = 'AGUARDANDO'
    inicializar_tijolos()
    resetar_bola()


def tijolos_vivos():
    return sum(1 for t in tijolos if t[2])


# --- Funções de desenho ---

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


def desenhar_circulo(cx, cy, r, segs=18):
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


def desenhar_tijolos():
    margem = 2
    for col, lin, vivo in tijolos:
        if not vivo:
            continue
        x, y = posicao_tijolo(col, lin)
        r, g, b = CORES_LINHAS[lin % len(CORES_LINHAS)]

        # Corpo do tijolo
        glColor3f(r, g, b)
        desenhar_retangulo(x + margem, y + margem,
                           TIJOLO_W - margem * 2, TIJOLO_H - margem * 2)

        # Brilho no topo
        glColor3f(min(r + 0.25, 1.0), min(g + 0.25, 1.0), min(b + 0.25, 1.0))
        desenhar_retangulo(x + margem, y + TIJOLO_H - margem * 2 - 4,
                           TIJOLO_W - margem * 2, 4)

        # Borda escura
        glColor3f(r * 0.4, g * 0.4, b * 0.4)
        desenhar_retangulo_borda(x + margem, y + margem,
                                  TIJOLO_W - margem * 2, TIJOLO_H - margem * 2)


def desenhar_paddle():
    x = paddle_x
    y = PADDLE_Y
    # Corpo
    glColor3f(0.85, 0.85, 0.95)
    desenhar_retangulo(x, y, PADDLE_W, PADDLE_H)
    # Brilho
    glColor3f(1.0, 1.0, 1.0)
    desenhar_retangulo(x + 4, y + PADDLE_H - 4, PADDLE_W - 8, 4)
    # Borda
    glColor3f(0.4, 0.4, 0.6)
    desenhar_retangulo_borda(x, y, PADDLE_W, PADDLE_H)


def desenhar_bola():
    glColor3f(1.0, 0.85, 0.2)
    desenhar_circulo(bola['x'], bola['y'], BOLA_R)
    glColor3f(1.0, 1.0, 0.8)
    desenhar_circulo(bola['x'] - BOLA_R * 0.3, bola['y'] + BOLA_R * 0.35, BOLA_R * 0.3)


def desenhar_hud():
    glColor3f(0.05, 0.05, 0.12)
    desenhar_retangulo(0, ALTURA - HUD_H, LARGURA, HUD_H)
    glColor3f(0.3, 0.3, 0.6)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, ALTURA - HUD_H)
    glVertex2f(LARGURA, ALTURA - HUD_H)
    glEnd()
    glLineWidth(1.0)

    glColor3f(0.9, 0.9, 0.3)
    desenhar_texto(8, ALTURA - 23, f"Pontos: {pontuacao}", escala=1.0)

    # Vidas como círculos coloridos
    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(LARGURA - 120, ALTURA - 23, "Vidas:", escala=0.8)
    for i in range(vidas):
        cx = LARGURA - 30 - i * 20
        glColor3f(0.95, 0.3, 0.3)
        desenhar_circulo(cx, ALTURA - HUD_H // 2, 6)


def desenhar_tela_overlay(titulo, cor, subtitulo=""):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.72)
    desenhar_retangulo(170, 220, 460, 140)
    glDisable(GL_BLEND)

    glColor3f(*cor)
    desenhar_texto(200, 320, titulo, escala=1.5)

    glColor3f(0.9, 0.9, 0.9)
    desenhar_texto(215, 278, f"Pontos: {pontuacao}", escala=1.0)

    if subtitulo:
        glColor3f(0.7, 0.7, 0.7)
        desenhar_texto(220, 245, subtitulo, escala=0.75)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(235, 228, "R: reiniciar  Q: sair", escala=0.7)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    glColor3f(0.05, 0.05, 0.08)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    # Borda lateral da arena
    glColor3f(0.2, 0.2, 0.4)
    glLineWidth(2.0)
    desenhar_retangulo_borda(0, 0, LARGURA, ALTURA - HUD_H)
    glLineWidth(1.0)

    desenhar_tijolos()
    desenhar_paddle()
    desenhar_bola()
    desenhar_hud()

    if estado == 'AGUARDANDO':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.72)
        desenhar_retangulo(170, 220, 460, 150)
        glDisable(GL_BLEND)
        glColor3f(0.3, 0.7, 1.0)
        desenhar_texto(220, 335, "BREAKOUT", escala=1.8)
        glColor3f(0.85, 0.85, 0.85)
        desenhar_texto(210, 288, "A/D ou setas para mover", escala=0.78)
        glColor3f(0.9, 0.9, 0.3)
        desenhar_texto(228, 258, "ESPACO para lancar a bola", escala=0.78)
        glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(248, 232, "R: reiniciar  Q: sair", escala=0.7)
    elif estado == 'GAME_OVER':
        desenhar_tela_overlay("GAME OVER", (1.0, 0.25, 0.25),
                              "Pressione R para reiniciar")
    elif estado == 'VITORIA':
        desenhar_tela_overlay("VOCE VENCEU!", (0.25, 1.0, 0.45),
                              "Pressione R para jogar de novo")

    glFlush()


# --- Lógica de atualização ---

def verificar_colisao_tijolo():
    """AABB: verifica colisão da bola com cada tijolo vivo."""
    global pontuacao
    bx, by = bola['x'], bola['y']
    for tijolo in tijolos:
        if not tijolo[2]:
            continue
        col, lin, _ = tijolo
        tx, ty = posicao_tijolo(col, lin)
        tw, th = TIJOLO_W - 2, TIJOLO_H - 2  # margem 2

        # Ponto mais próximo do centro da bola dentro do tijolo
        px = max(tx, min(bx, tx + tw))
        py = max(ty, min(by, ty + th))

        if math.hypot(bx - px, by - py) <= BOLA_R:
            tijolo[2] = False
            pontuacao += 10

            # px == bx → centro da bola dentro da faixa X do tijolo → bateu no topo/base
            # py == by → centro da bola dentro da faixa Y do tijolo → bateu na lateral
            if px == bx:
                bola['vy'] = -bola['vy']
                # Empurra a bola para fora para evitar colisão dupla no próximo frame
                if by < ty + th / 2:
                    bola['y'] = ty - BOLA_R - 1
                else:
                    bola['y'] = ty + th + BOLA_R + 1
            else:
                bola['vx'] = -bola['vx']
                if bx < tx + tw / 2:
                    bola['x'] = tx - BOLA_R - 1
                else:
                    bola['x'] = tx + tw + BOLA_R + 1
            return


def atualizar(valor=0):
    global paddle_x, vidas, estado

    if estado != 'JOGANDO':
        return

    # Movimento do paddle
    if ('a' in teclas or 'left' in teclas) and paddle_x > 0:
        paddle_x = max(paddle_x - PADDLE_VEL, 0)
    if ('d' in teclas or 'right' in teclas) and paddle_x + PADDLE_W < LARGURA:
        paddle_x = min(paddle_x + PADDLE_VEL, LARGURA - PADDLE_W)

    # Se a bola ainda não foi lançada, fica presa na paddle
    if not bola['ativa']:
        bola['x'] = paddle_x + PADDLE_W / 2
        glutPostRedisplay()
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)
        return

    # Move bola
    bola['x'] += bola['vx']
    bola['y'] += bola['vy']

    # Paredes laterais
    if bola['x'] - BOLA_R <= 0:
        bola['x'] = BOLA_R
        bola['vx'] = abs(bola['vx'])
    if bola['x'] + BOLA_R >= LARGURA:
        bola['x'] = LARGURA - BOLA_R
        bola['vx'] = -abs(bola['vx'])

    # Teto
    if bola['y'] + BOLA_R >= ALTURA - HUD_H:
        bola['y'] = ALTURA - HUD_H - BOLA_R
        bola['vy'] = -abs(bola['vy'])

    # Paddle: AABB simples
    if (bola['vy'] < 0
            and paddle_x <= bola['x'] <= paddle_x + PADDLE_W
            and PADDLE_Y <= bola['y'] - BOLA_R <= PADDLE_Y + PADDLE_H):
        bola['y'] = PADDLE_Y + PADDLE_H + BOLA_R
        bola['vy'] = abs(bola['vy'])
        # Angulo baseado em onde bateu no paddle
        offset = (bola['x'] - (paddle_x + PADDLE_W / 2)) / (PADDLE_W / 2)
        bola['vx'] = offset * VEL_BOLA
        speed = math.hypot(bola['vx'], bola['vy'])
        bola['vx'] = bola['vx'] / speed * VEL_BOLA
        bola['vy'] = bola['vy'] / speed * VEL_BOLA

    # Colisão tijolos
    verificar_colisao_tijolo()

    # Bola saiu pelo fundo
    if bola['y'] < 0:
        vidas -= 1
        if vidas <= 0:
            estado = 'GAME_OVER'
        else:
            resetar_bola()

    # Vitória
    if tijolos_vivos() == 0:
        estado = 'VITORIA'

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
    if tecla == ' ':
        if estado == 'AGUARDANDO':
            estado = 'JOGANDO'
            bola['ativa'] = True
            glutTimerFunc(VELOCIDADE_MS, atualizar, 0)
        elif estado == 'JOGANDO' and not bola['ativa']:
            bola['ativa'] = True


def teclado_up(tecla, x, y):
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.discard(tecla)


def teclado_especial(tecla, x, y):
    if tecla == GLUT_KEY_LEFT:
        teclas.add('left')
    elif tecla == GLUT_KEY_RIGHT:
        teclas.add('right')


def teclado_especial_up(tecla, x, y):
    if tecla == GLUT_KEY_LEFT:
        teclas.discard('left')
    elif tecla == GLUT_KEY_RIGHT:
        teclas.discard('right')


# --- Inicialização OpenGL ---

def inicializar_opengl():
    glClearColor(0.05, 0.05, 0.08, 1.0)
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
    glutCreateWindow(b"Breakout - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutKeyboardUpFunc(teclado_up)
    glutSpecialFunc(teclado_especial)
    glutSpecialUpFunc(teclado_especial_up)

    glutMainLoop()


if __name__ == "__main__":
    main()
