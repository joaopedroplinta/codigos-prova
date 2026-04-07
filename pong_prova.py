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
estado     = 'MENU'      # 'MENU', 'AGUARDANDO', 'JOGANDO'
modo       = None        # '1P' ou '2P'
opcao_menu = 0           # 0 = 1 jogador, 1 = 2 jogadores
teclas     = set()

MARGEM_X_ESQ = 20
MARGEM_X_DIR = LARGURA - 20 - PADDLE_W
HUD_H        = 30


def resetar_bola(direcao=1):
    bola['x']  = float(LARGURA // 2)
    bola['y']  = float(ALTURA  // 2)
    bola['vx'] = VEL_INICIAL * direcao
    bola['vy'] = VEL_INICIAL * random.choice([-1.0, 1.0]) * 0.6


def inicializar_jogo(novo_modo):
    global estado, modo
    modo = novo_modo
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


def desenhar_retangulo_borda(x, y, w, h):
    glBegin(GL_LINE_LOOP)
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
    if modo == 'SOLO':
        desenhar_texto(LARGURA / 2 - 20, ALTURA - 23, str(paddle_esq['score']), escala=1.2)
    else:
        desenhar_texto(LARGURA / 2 - 110, ALTURA - 23, str(paddle_esq['score']), escala=1.2)
        desenhar_texto(LARGURA / 2 +  70, ALTURA - 23, str(paddle_dir['score']), escala=1.2)

    # Labels dos lados dependendo do modo
    if modo == 'SOLO':
        glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(10, ALTURA - 22, "W/S ou Setas", escala=0.7)
        glColor3f(0.4, 0.9, 0.7)
        desenhar_texto(LARGURA - 100, ALTURA - 22, "Parede", escala=0.7)
    elif modo == '1P':
        glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(10, ALTURA - 22, "W/S ou Setas", escala=0.7)
        glColor3f(0.9, 0.4, 0.4)
        desenhar_texto(LARGURA - 80, ALTURA - 22, "CPU", escala=0.7)
    else:
        glColor3f(0.5, 0.8, 0.5)
        desenhar_texto(10, ALTURA - 22, "J1: W/S", escala=0.7)
        glColor3f(0.5, 0.6, 0.9)
        desenhar_texto(LARGURA - 110, ALTURA - 22, "J2: Setas", escala=0.7)


def desenhar_menu():
    # Largura aproximada de cada char em pixels para GLUT_STROKE_ROMAN:
    # glutStrokeWidth(GLUT_STROKE_ROMAN, ord(c)) retorna ~104 unidades.
    # Com glScalef(escala*0.12, ...) → px_por_char ≈ 104 * escala * 0.12
    CX = LARGURA // 2   # centro horizontal = 400

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.04, 0.04, 0.04)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    # --- Título "PONG" ---
    # 4 chars × 104 × 0.12 × 2.5 ≈ 125 px  →  x = 400 - 62 = 338
    glColor3f(1.0, 1.0, 0.3)
    desenhar_texto(CX - 62, 450, "PONG", escala=2.5)

    # --- Caixa do menu (320 × 250, centrada) ---
    BOX_W, BOX_H = 320, 250
    BOX_X = CX - BOX_W // 2   # 240
    BOX_Y = 180
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.75)
    desenhar_retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)
    glColor3f(0.25, 0.25, 0.5)
    desenhar_retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)

    # --- Opções ---
    # escala=0.9 → px_por_char ≈ 104*0.108 ≈ 11.2 px
    # "1 Jogador  (vs CPU)" ≈ 19 chars × 11.2 ≈ 213 px  →  x = 400 - 106 = 294
    # "2 Jogadores"         ≈ 11 chars × 11.2 ≈ 123 px  →  x = 400 - 61  = 339
    # "Solo  (parede)"      ≈ 14 chars × 11.2 ≈ 157 px  →  x = 400 - 78  = 322
    LABEL_W  = [213, 123, 157]
    LABELS   = ["1 Jogador  (vs CPU)", "2 Jogadores", "Solo  (parede)"]
    OPT_Y    = [388, 323, 258]

    for i, label in enumerate(LABELS):
        y    = OPT_Y[i]
        lx   = CX - LABEL_W[i] // 2

        if i == opcao_menu:
            glColor3f(0.2, 0.2, 0.55)
            desenhar_retangulo(BOX_X + 8, y - 8, BOX_W - 16, 34)
            glColor3f(0.5, 0.7, 1.0)
            glLineWidth(1.5)
            desenhar_retangulo_borda(BOX_X + 8, y - 8, BOX_W - 16, 34)
            glLineWidth(1.0)
            glColor3f(1.0, 1.0, 0.3)
            desenhar_texto(BOX_X + 14, y + 4, ">", escala=0.9)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(0.55, 0.55, 0.55)

        desenhar_texto(lx, y + 4, label, escala=0.9)

    # --- Instruções ---
    glColor3f(0.38, 0.38, 0.38)
    desenhar_texto(CX - 91, 214, "W/S ou Setas: navegar", escala=0.72)
    desenhar_texto(CX - 74, 198, "ESPACO: confirmar",     escala=0.72)
    desenhar_texto(CX - 30, 183, "Q: sair",               escala=0.72)

    glFlush()


def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.04, 0.04, 0.04)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    desenhar_linha_central()

    # Paddle esquerdo
    glColor3f(0.95, 0.95, 0.95)
    desenhar_retangulo(MARGEM_X_ESQ, paddle_esq['y'], PADDLE_W, PADDLE_H)

    # Paddle direito ou parede (SOLO)
    if modo == 'SOLO':
        glColor3f(0.3, 0.8, 0.6)
        glLineWidth(4.0)
        glBegin(GL_LINES)
        glVertex2f(LARGURA - 4, 0)
        glVertex2f(LARGURA - 4, ALTURA - HUD_H)
        glEnd()
        glLineWidth(1.0)
    else:
        if modo == '2P':
            glColor3f(0.4, 0.7, 1.0)
        else:
            glColor3f(0.9, 0.3, 0.3)
        desenhar_retangulo(MARGEM_X_DIR, paddle_dir['y'], PADDLE_W, PADDLE_H)

    # Bola
    glColor3f(1.0, 1.0, 0.2)
    desenhar_circulo(bola['x'], bola['y'], BOLA_R, segs=18)
    glColor3f(1.0, 1.0, 0.8)
    desenhar_circulo(bola['x'] - BOLA_R * 0.3, bola['y'] + BOLA_R * 0.3, BOLA_R * 0.3)

    desenhar_hud()

    if estado == 'AGUARDANDO':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.72)
        desenhar_retangulo(230, 255, 340, 100)
        glDisable(GL_BLEND)

        if modo == '2P':
            glColor3f(0.4, 0.9, 0.4)
            desenhar_texto(258, 320, "2 JOGADORES", escala=1.2)
            glColor3f(0.7, 0.7, 0.7)
            desenhar_texto(248, 280, "J1: W/S   J2: Setas", escala=0.78)
        elif modo == 'SOLO':
            glColor3f(0.3, 0.9, 0.7)
            desenhar_texto(290, 320, "SOLO", escala=1.2)
            glColor3f(0.7, 0.7, 0.7)
            desenhar_texto(248, 280, "W/S ou Setas para mover", escala=0.78)
        else:
            glColor3f(1.0, 1.0, 0.3)
            desenhar_texto(255, 320, "1 JOGADOR", escala=1.2)
            glColor3f(0.7, 0.7, 0.7)
            desenhar_texto(248, 280, "W/S ou Setas para mover", escala=0.78)

        glColor3f(0.85, 0.85, 0.85)
        desenhar_texto(263, 258, "ESPACO para comecar", escala=0.75)

    glFlush()


# --- Lógica de atualização ---

def atualizar(valor=0):
    if estado != 'JOGANDO':
        return

    area_max_y = ALTURA - HUD_H - PADDLE_H

    # Jogador 1: W/S (sempre) + setas quando não é 2P
    if 'w' in teclas and paddle_esq['y'] < area_max_y:
        paddle_esq['y'] = min(paddle_esq['y'] + PADDLE_VEL, area_max_y)
    if 's' in teclas and paddle_esq['y'] > 0:
        paddle_esq['y'] = max(paddle_esq['y'] - PADDLE_VEL, 0)
    if modo != '2P':
        if 'up' in teclas and paddle_esq['y'] < area_max_y:
            paddle_esq['y'] = min(paddle_esq['y'] + PADDLE_VEL, area_max_y)
        if 'down' in teclas and paddle_esq['y'] > 0:
            paddle_esq['y'] = max(paddle_esq['y'] - PADDLE_VEL, 0)

    if modo == '2P':
        # Jogador 2: setas
        if 'up' in teclas and paddle_dir['y'] < area_max_y:
            paddle_dir['y'] = min(paddle_dir['y'] + PADDLE_VEL, area_max_y)
        if 'down' in teclas and paddle_dir['y'] > 0:
            paddle_dir['y'] = max(paddle_dir['y'] - PADDLE_VEL, 0)
    else:
        # CPU
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

    # Colisão paddle direito ou parede (SOLO)
    if modo == 'SOLO':
        if bola['vx'] > 0 and bola['x'] + BOLA_R >= LARGURA - 4:
            bola['x'] = LARGURA - 4 - BOLA_R
            bola['vx'] = -abs(bola['vx'])
            paddle_esq['score'] += 1
    else:
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
        if modo == 'SOLO':
            paddle_esq['score'] = 0   # errou: zera o score
            resetar_bola(direcao=1)
        else:
            paddle_dir['score'] += 1
            resetar_bola(direcao=1)
    elif bola['x'] > LARGURA:
        if modo != 'SOLO':
            paddle_esq['score'] += 1
            resetar_bola(direcao=-1)

    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def teclado(tecla, x, y):
    global estado, opcao_menu
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.add(tecla)

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if estado == 'MENU':
        if tecla == ' ':
            escolha = ['1P', '2P', 'SOLO'][opcao_menu]
            inicializar_jogo(escolha)
            glutPostRedisplay()
        elif tecla == 'w':
            opcao_menu = (opcao_menu - 1) % 3
            glutPostRedisplay()
        elif tecla == 's':
            opcao_menu = (opcao_menu + 1) % 3
            glutPostRedisplay()
        return

    if tecla == 'r':
        global modo
        estado = 'MENU'
        opcao_menu = 0
        glutPostRedisplay()
        return

    if tecla == ' ' and estado == 'AGUARDANDO':
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


def teclado_up(tecla, x, y):
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.discard(tecla)


def teclado_especial(tecla, x, y):
    global opcao_menu
    if tecla == GLUT_KEY_UP:
        if estado == 'MENU':
            opcao_menu = (opcao_menu - 1) % 3
            glutPostRedisplay()
        else:
            teclas.add('up')
    elif tecla == GLUT_KEY_DOWN:
        if estado == 'MENU':
            opcao_menu = (opcao_menu + 1) % 3
            glutPostRedisplay()
        else:
            teclas.add('down')


def teclado_especial_up(tecla, x, y):
    if tecla == GLUT_KEY_UP:
        teclas.discard('up')
    elif tecla == GLUT_KEY_DOWN:
        teclas.discard('down')


def redimensionar(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, LARGURA, 0, ALTURA)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glutPostRedisplay()


# --- Inicialização OpenGL ---

def inicializar_opengl():
    glClearColor(0.04, 0.04, 0.04, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, LARGURA, 0, ALTURA)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def main():
    global estado
    estado = 'MENU'

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutInitWindowSize(LARGURA, ALTURA)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Pong - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutReshapeFunc(redimensionar)
    glutKeyboardFunc(teclado)
    glutKeyboardUpFunc(teclado_up)
    glutSpecialFunc(teclado_especial)
    glutSpecialUpFunc(teclado_especial_up)

    glutMainLoop()


if __name__ == "__main__":
    main()
