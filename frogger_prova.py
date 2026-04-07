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
AREA_H         = ALTURA - HUD_H   # 560
VELOCIDADE_MS  = 16               # ~60 fps
TAM_JOGADOR    = 25
TAM_CARRO      = 30
TAM_TRONCO     = 35

# Faixas (coordenadas dentro de AREA_H = 560)
FAIXAS = [
    {'y': 50,  'tipo': 'chao',    'y0': 30,  'y1': 70,  },
    {'y': 120, 'tipo': 'estrada', 'y0': 100, 'y1': 140, 'dir':  1},
    {'y': 190, 'tipo': 'estrada', 'y0': 170, 'y1': 210, 'dir': -1},
    {'y': 260, 'tipo': 'estrada', 'y0': 240, 'y1': 280, 'dir':  1},
    {'y': 330, 'tipo': 'rio',     'y0': 310, 'y1': 350, 'dir': -1},
    {'y': 400, 'tipo': 'rio',     'y0': 380, 'y1': 420, 'dir':  1},
    {'y': 470, 'tipo': 'rio',     'y0': 450, 'y1': 490, 'dir': -1},
    {'y': 530, 'tipo': 'chegada', 'y0': 515, 'y1': 545, },
]

# --- Estado do jogo ---
jogador_x  = LARGURA // 2
jogador_y  = 50
vidas      = 3
pontuacao  = 0
nivel      = 1
estado     = 'MENU'   # 'MENU', 'JOGANDO', 'GAME_OVER'
carros     = []
troncos    = []
chegadas   = []


def inicializar_jogo():
    global jogador_x, jogador_y, vidas, pontuacao, nivel, estado
    jogador_x = LARGURA // 2
    jogador_y = 50
    vidas     = 3
    pontuacao = 0
    nivel     = 1
    estado    = 'JOGANDO'
    inicializar_carros()
    inicializar_troncos()
    inicializar_chegadas()


def inicializar_carros():
    global carros
    carros = []
    for f in FAIXAS:
        if f['tipo'] != 'estrada':
            continue
        for _ in range(random.randint(3, 4)):
            x    = random.randint(-200, LARGURA + 200)
            larg = random.randint(25, 40)
            vel  = random.uniform(2, 5) * (1 + nivel * 0.2)
            cor  = random.choice([(1,0,0),(0,0,1),(1,1,0),(0.3,0.3,0.3)])
            carros.append([x, f['y'], larg, vel, cor, f['dir']])


def inicializar_troncos():
    global troncos
    troncos = []
    for f in FAIXAS:
        if f['tipo'] != 'rio':
            continue
        for _ in range(random.randint(2, 3)):
            x    = random.randint(-200, LARGURA + 200)
            larg = random.randint(40, 80)
            vel  = random.uniform(1.5, 3.5) * (1 + nivel * 0.1)
            troncos.append([x, f['y'], larg, vel, f['dir']])


def inicializar_chegadas():
    global chegadas
    chegadas = []
    esp = LARGURA // 6
    for i in range(5):
        chegadas.append({'x': esp * (i + 1), 'y': 530, 'ocupado': False})


def reiniciar_nivel():
    global jogador_x, jogador_y
    jogador_x = LARGURA // 2
    jogador_y = 50
    for c in chegadas:
        c['ocupado'] = False
    inicializar_carros()
    inicializar_troncos()


def perder_vida():
    global vidas, estado, jogador_x, jogador_y
    vidas -= 1
    if vidas <= 0:
        estado = 'GAME_OVER'
    else:
        jogador_x = LARGURA // 2
        jogador_y = 50


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

def mover_carros():
    for c in carros[:]:
        c[0] += c[3] * c[5]
        if c[0] > LARGURA + 200 or c[0] < -200:
            carros.remove(c)


def mover_troncos():
    for t in troncos[:]:
        t[0] += t[3] * t[4]
        if t[0] > LARGURA + 200 or t[0] < -200:
            troncos.remove(t)


def gerar_carro():
    if estado != 'JOGANDO':
        return
    faixas_e = [f for f in FAIXAS if f['tipo'] == 'estrada']
    f    = random.choice(faixas_e)
    x    = -TAM_CARRO if f['dir'] == 1 else LARGURA
    larg = random.randint(25, 40)
    vel  = random.uniform(2, 5) * (1 + nivel * 0.2)
    cor  = random.choice([(1,0,0),(0,0,1),(1,1,0),(0.3,0.3,0.3)])
    carros.append([x, f['y'], larg, vel, cor, f['dir']])


def gerar_tronco():
    if estado != 'JOGANDO':
        return
    faixas_r = [f for f in FAIXAS if f['tipo'] == 'rio']
    f    = random.choice(faixas_r)
    x    = -80 if f['dir'] == 1 else LARGURA
    larg = random.randint(40, 80)
    vel  = random.uniform(1.5, 3.5) * (1 + nivel * 0.1)
    troncos.append([x, f['y'], larg, vel, f['dir']])


def verificar_colisao_carro():
    for c in carros:
        if abs(jogador_y - c[1]) <= 15:
            if (jogador_x + TAM_JOGADOR // 2 > c[0] - c[2] // 2 and
                    jogador_x - TAM_JOGADOR // 2 < c[0] + c[2] // 2):
                return True
    return False


def verificar_tronco():
    global jogador_x
    for t in troncos:
        if abs(jogador_y - t[1]) <= 15:
            if (jogador_x + TAM_JOGADOR // 2 > t[0] - t[2] // 2 and
                    jogador_x - TAM_JOGADOR // 2 < t[0] + t[2] // 2):
                jogador_x += t[3] * t[4]
                return True
    return False


def verificar_agua():
    for f in FAIXAS:
        if f['tipo'] == 'rio' and f['y'] - 20 <= jogador_y <= f['y'] + 20:
            if not verificar_tronco():
                return True
    return False


def mover_sapo_no_tronco():
    for f in FAIXAS:
        if f['tipo'] == 'rio' and f['y'] - 20 <= jogador_y <= f['y'] + 20:
            if not verificar_tronco():
                perder_vida()
            return


def verificar_chegada():
    global pontuacao, nivel, jogador_x, jogador_y
    for c in chegadas:
        if (abs(jogador_x - c['x']) < TAM_JOGADOR // 2 and
                abs(jogador_y - c['y']) < TAM_JOGADOR // 2 and
                not c['ocupado']):
            c['ocupado'] = True
            pontuacao   += 100
            if all(ch['ocupado'] for ch in chegadas):
                nivel += 1
                reiniciar_nivel()
            else:
                jogador_x = LARGURA // 2
                jogador_y = 50
            return True
    return False


def mover_jogador_pulo(dx, dy):
    global jogador_x, jogador_y
    if estado != 'JOGANDO':
        return
    novo_x = jogador_x + dx * 40
    novo_y = jogador_y + dy * 70
    novo_x = max(TAM_JOGADOR // 2, min(LARGURA - TAM_JOGADOR // 2, novo_x))
    novo_y = max(30, min(AREA_H - 30, novo_y))
    jogador_x = novo_x
    jogador_y = novo_y
    if verificar_colisao_carro():
        perder_vida()
        return
    if verificar_agua():
        perder_vida()
        return
    verificar_chegada()


# --- Desenho ---

def desenhar_faixas():
    for f in FAIXAS:
        if f['tipo'] == 'chao':
            glColor3f(0.3, 0.8, 0.3)
        elif f['tipo'] == 'estrada':
            glColor3f(0.2, 0.2, 0.2)
        elif f['tipo'] == 'rio':
            glColor3f(0.1, 0.3, 0.5)
        elif f['tipo'] == 'chegada':
            glColor3f(0.0, 0.6, 0.0)

        retangulo(0, f['y0'], LARGURA, f['y1'] - f['y0'])

        if f['tipo'] == 'estrada':
            glColor3f(1.0, 1.0, 0.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for x in range(0, LARGURA, 40):
                glVertex2f(x,      f['y'] - 5)
                glVertex2f(x + 20, f['y'] - 5)
            glEnd()
            glLineWidth(1.0)

    # fundo entre faixas
    glColor3f(0.12, 0.12, 0.12)
    retangulo(0, 0, LARGURA, AREA_H)
    for f in FAIXAS:
        if f['tipo'] == 'chao':
            glColor3f(0.3, 0.8, 0.3)
        elif f['tipo'] == 'estrada':
            glColor3f(0.2, 0.2, 0.2)
        elif f['tipo'] == 'rio':
            glColor3f(0.1, 0.3, 0.5)
        elif f['tipo'] == 'chegada':
            glColor3f(0.0, 0.6, 0.0)
        retangulo(0, f['y0'], LARGURA, f['y1'] - f['y0'])

        if f['tipo'] == 'estrada':
            glColor3f(1.0, 1.0, 0.0)
            glLineWidth(2.0)
            glBegin(GL_LINES)
            for x in range(0, LARGURA, 40):
                glVertex2f(x,      f['y'] - 5)
                glVertex2f(x + 20, f['y'] - 5)
            glEnd()
            glLineWidth(1.0)


def desenhar_carros():
    for c in carros:
        x, y, larg, vel, cor, d = c
        glColor3f(*cor)
        retangulo(x - larg // 2, y - 15, larg, 30)
        glColor3f(1.0, 1.0, 1.0)
        retangulo(x - larg // 4, y - 8, larg // 2, 10)


def desenhar_troncos():
    for t in troncos:
        x, y, larg, vel, d = t
        glColor3f(0.5, 0.35, 0.2)
        retangulo(x - larg // 2, y - 12, larg, 24)
        glColor3f(0.6, 0.4, 0.2)
        glLineWidth(1.0)
        for offset in range(-larg // 2 + 10, larg // 2, 15):
            glBegin(GL_LINES)
            glVertex2f(x + offset, y - 8)
            glVertex2f(x + offset, y + 8)
            glEnd()


def desenhar_chegadas():
    for c in chegadas:
        glColor3f(0.3, 0.5, 0.8) if c['ocupado'] else glColor3f(0.0, 0.6, 0.0)
        retangulo(c['x'] - 20, c['y'] - 10, 40, 20)


def desenhar_jogador():
    r = TAM_JOGADOR // 2
    glColor3f(0.0, 0.8, 0.0)
    retangulo(jogador_x - r, jogador_y - r, TAM_JOGADOR, TAM_JOGADOR)
    glColor3f(1.0, 1.0, 1.0)
    retangulo(jogador_x - 8, jogador_y + 5, 5, 5)
    retangulo(jogador_x + 3, jogador_y + 5, 5, 5)
    glColor3f(0.0, 0.0, 0.0)
    glPointSize(3)
    glBegin(GL_POINTS)
    glVertex2f(jogador_x - 5, jogador_y + 7)
    glVertex2f(jogador_x + 5, jogador_y + 7)
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
        glColor3f(0.2, 0.9, 0.2)
        retangulo(LARGURA - 30 - i * 22, CY - 8, 16, 16)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.08, 0.14, 0.08)
    retangulo(0, 0, LARGURA, ALTURA)

    glColor3f(0.2, 0.2, 0.2)
    retangulo(0, 0, LARGURA, AREA_H // 3)
    glColor3f(0.1, 0.3, 0.5)
    retangulo(0, AREA_H // 3, LARGURA, AREA_H // 3)
    glColor3f(0.3, 0.8, 0.3)
    retangulo(0, 2 * AREA_H // 3, LARGURA, AREA_H // 3)

    glColor3f(0.9, 1.0, 0.3)
    desenhar_texto(CX - 130, 460, 'FROGGER', escala=1.6)

    BOX_W, BOX_H = 380, 180
    BOX_X = CX - BOX_W // 2
    BOX_Y = 230

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.82)
    retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)

    glColor3f(0.3, 0.5, 0.3)
    glLineWidth(1.5)
    retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)
    glLineWidth(1.0)

    glColor3f(0.8, 0.8, 0.8)
    desenhar_texto(CX - 170, 376, 'Atravesse a rua e o rio!', escala=0.72)
    desenhar_texto(CX - 160, 350, 'Desvie dos carros na estrada', escala=0.72)
    desenhar_texto(CX - 150, 324, 'Use troncos para o rio', escala=0.72)
    desenhar_texto(CX - 165, 298, 'Chegue nas 5 areas verdes!', escala=0.72)

    glColor3f(0.35, 0.35, 0.4)
    desenhar_texto(CX - 110, 258, 'WASD ou setas: pular', escala=0.72)
    desenhar_texto(CX - 80,  240, 'ESPACO: jogar',        escala=0.72)
    desenhar_texto(CX - 30,  222, 'Q: sair',              escala=0.72)

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
    desenhar_texto(CX - 120, CY + 40, 'GAME OVER', escala=1.2)

    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - 90, CY + 6, f'Pontuacao: {pontuacao}', escala=0.9)
    desenhar_texto(CX - 65, CY - 20, f'Nivel: {nivel}', escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 130, CY - 54, 'ESPACO: menu    Q: sair', escala=0.72)


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    desenhar_faixas()
    desenhar_carros()
    desenhar_troncos()
    desenhar_chegadas()
    desenhar_jogador()
    desenhar_hud()

    if estado == 'GAME_OVER':
        desenhar_game_over()

    glFlush()


def atualizar(valor=0):
    if estado == 'JOGANDO':
        mover_carros()
        mover_troncos()
        mover_sapo_no_tronco()
        if random.random() < 0.02:
            gerar_carro()
        if random.random() < 0.015:
            gerar_tronco()
    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def tecla_normal(tecla, x, y):
    global estado
    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if tecla == ' ':
        if estado in ('MENU', 'GAME_OVER'):
            inicializar_jogo()
        glutPostRedisplay()
        return

    if estado == 'JOGANDO':
        if tecla == 'w':   mover_jogador_pulo( 0,  1)
        elif tecla == 's': mover_jogador_pulo( 0, -1)
        elif tecla == 'a': mover_jogador_pulo(-1,  0)
        elif tecla == 'd': mover_jogador_pulo( 1,  0)
        glutPostRedisplay()


def tecla_especial(tecla, x, y):
    if estado != 'JOGANDO':
        return
    if tecla == GLUT_KEY_UP:    mover_jogador_pulo( 0,  1)
    elif tecla == GLUT_KEY_DOWN:  mover_jogador_pulo( 0, -1)
    elif tecla == GLUT_KEY_LEFT:  mover_jogador_pulo(-1,  0)
    elif tecla == GLUT_KEY_RIGHT: mover_jogador_pulo( 1,  0)
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
    glutCreateWindow(b'Frogger')

    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_LINE_SMOOTH)
    glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

    reshape(LARGURA, ALTURA)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(tecla_normal)
    glutSpecialFunc(tecla_especial)
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)

    glutMainLoop()


if __name__ == '__main__':
    main()
