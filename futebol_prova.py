import os
import sys
import math

os.environ["WAYLAND_DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "x11"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Configurações ---
LARGURA       = 800
ALTURA        = 600
HUD_H         = 40
AREA_H        = ALTURA - HUD_H
VELOCIDADE_MS = 16          # ~60 fps
TAM_JOGADOR   = 20
TAM_BOLA      = 12
VELOCIDADE    = 5
CPU_VEL       = 3.8         # velocidade da CPU (menor que o jogador)
GOLS_VITORIA  = 3

# Gols
GOL_ESQ = {'x': 20,           'y1': AREA_H // 2 - 80, 'y2': AREA_H // 2 + 80}
GOL_DIR = {'x': LARGURA - 40, 'y1': AREA_H // 2 - 80, 'y2': AREA_H // 2 + 80}

# --- Estado do jogo ---
jogador1   = {}
jogador2   = {}
bola       = {}
teclas1    = set()   # 'w','a','s','d'
teclas2    = set()   # 'up','down','left','right'
estado     = 'MENU'  # 'MENU','AGUARDANDO','JOGANDO','VITORIA'
modo       = None    # '1P' ou '2P'
opcao_menu = 0       # 0 = 1P, 1 = 2P
vencedor   = 0
tempo_msg  = 0
msg_gol    = ''


def inicializar_jogo(novo_modo):
    global jogador1, jogador2, bola, teclas1, teclas2
    global estado, modo, vencedor, tempo_msg, msg_gol
    modo      = novo_modo
    jogador1  = {'x': LARGURA // 4,     'y': AREA_H // 2, 'gols': 0}
    jogador2  = {'x': 3 * LARGURA // 4, 'y': AREA_H // 2, 'gols': 0}
    bola      = {'x': float(LARGURA // 2), 'y': float(AREA_H // 2), 'vx': 0.0, 'vy': 0.0}
    teclas1   = set()
    teclas2   = set()
    vencedor  = 0
    tempo_msg = 0
    msg_gol   = ''
    estado    = 'AGUARDANDO'


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


# --- Desenho ---

def desenhar_campo():
    glColor3f(0.13, 0.50, 0.13)
    retangulo(0, 0, LARGURA, AREA_H)

    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)

    glBegin(GL_LINES)
    glVertex2f(LARGURA // 2, 0)
    glVertex2f(LARGURA // 2, AREA_H)
    glEnd()

    circulo_borda(LARGURA // 2, AREA_H // 2, 60)
    glColor3f(1.0, 1.0, 1.0)
    circulo(LARGURA // 2, AREA_H // 2, 4)

    glColor3f(1.0, 1.0, 1.0)
    retangulo_borda(0,             AREA_H // 2 - 80, 100, 160)
    retangulo_borda(LARGURA - 100, AREA_H // 2 - 80, 100, 160)

    glLineWidth(1.0)


def desenhar_gols():
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(4.0)

    glBegin(GL_LINE_STRIP)
    glVertex2f(GOL_ESQ['x'] - 20, GOL_ESQ['y1'])
    glVertex2f(GOL_ESQ['x'],      GOL_ESQ['y1'])
    glVertex2f(GOL_ESQ['x'],      GOL_ESQ['y2'])
    glVertex2f(GOL_ESQ['x'] - 20, GOL_ESQ['y2'])
    glEnd()

    glBegin(GL_LINE_STRIP)
    glVertex2f(GOL_DIR['x'] + 20, GOL_DIR['y1'])
    glVertex2f(GOL_DIR['x'],      GOL_DIR['y1'])
    glVertex2f(GOL_DIR['x'],      GOL_DIR['y2'])
    glVertex2f(GOL_DIR['x'] + 20, GOL_DIR['y2'])
    glEnd()

    glLineWidth(1.0)


def desenhar_jogadores():
    r = TAM_JOGADOR // 2

    glColor3f(0.15, 0.35, 1.0)
    circulo(jogador1['x'], jogador1['y'], r)
    glColor3f(0.7, 0.85, 1.0)
    circulo_borda(jogador1['x'], jogador1['y'], r)
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(jogador1['x'] - 4, jogador1['y'] - 5, '1', escala=0.55)

    glColor3f(1.0, 0.15, 0.15)
    circulo(jogador2['x'], jogador2['y'], r)
    glColor3f(1.0, 0.75, 0.75)
    circulo_borda(jogador2['x'], jogador2['y'], r)
    glColor3f(1.0, 1.0, 1.0)
    label2 = 'C' if modo == '1P' else '2'
    desenhar_texto(jogador2['x'] - 4, jogador2['y'] - 5, label2, escala=0.55)


def desenhar_bola():
    x, y = bola['x'], bola['y']
    r = TAM_BOLA // 2
    glColor3f(0.95, 0.95, 0.95)
    circulo(x, y, r)
    glColor3f(0.1, 0.1, 0.1)
    circulo(x, y, r * 0.38, segs=5)
    glColor3f(0.4, 0.4, 0.4)
    circulo_borda(x, y, r)


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

    glColor3f(0.4, 0.6, 1.0)
    desenhar_texto(16, CY - 9, 'J1 (WASD):', escala=0.75)
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(155, CY - 9, str(jogador1['gols']), escala=0.85)

    glColor3f(0.9, 0.9, 0.2)
    placar = f'{jogador1["gols"]}  x  {jogador2["gols"]}'
    desenhar_texto(LARGURA // 2 - 52, CY - 10, placar, escala=1.1)

    if modo == '2P':
        glColor3f(1.0, 0.4, 0.4)
        desenhar_texto(LARGURA - 185, CY - 9, 'J2 (Setas):', escala=0.75)
    else:
        glColor3f(1.0, 0.5, 0.5)
        desenhar_texto(LARGURA - 120, CY - 9, 'CPU:', escala=0.75)
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(LARGURA - 30, CY - 9, str(jogador2['gols']), escala=0.85)


def desenhar_msg_gol():
    if tempo_msg <= 0:
        return
    CX = LARGURA // 2
    CY = AREA_H  // 2 + 30

    alpha = min(1.0, tempo_msg / 30.0)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.6 * alpha)
    retangulo(CX - 170, CY - 22, 340, 44)
    glDisable(GL_BLEND)

    larg = len(msg_gol) * 104 * 0.12 * 1.1 / 2
    glColor3f(1.0, 1.0, 0.2)
    desenhar_texto(CX - larg, CY - 9, msg_gol, escala=1.1)


def desenhar_menu():
    CX = LARGURA // 2

    glClear(GL_COLOR_BUFFER_BIT)
    glColor3f(0.04, 0.08, 0.04)
    retangulo(0, 0, LARGURA, ALTURA)

    # Gramado decorativo no fundo
    glColor3f(0.10, 0.38, 0.10)
    retangulo(0, 0, LARGURA, AREA_H // 2)
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    circulo_borda(CX, AREA_H // 2, 80)
    glBegin(GL_LINES)
    glVertex2f(CX, 0)
    glVertex2f(CX, AREA_H // 2)
    glEnd()
    glLineWidth(1.0)

    # Título
    glColor3f(0.3, 1.0, 0.3)
    desenhar_texto(CX - 115, 430, 'FUTEBOL', escala=1.5)

    # Caixa do menu
    BOX_W, BOX_H = 360, 200
    BOX_X = CX - BOX_W // 2
    BOX_Y = 230
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.05, 0.0, 0.85)
    retangulo(BOX_X, BOX_Y, BOX_W, BOX_H)
    glDisable(GL_BLEND)
    glColor3f(0.2, 0.5, 0.2)
    glLineWidth(1.5)
    retangulo_borda(BOX_X, BOX_Y, BOX_W, BOX_H)
    glLineWidth(1.0)

    OPCOES  = ['1 Jogador  (vs CPU)', '2 Jogadores']
    LARGURAS = [213, 123]
    OPT_Y   = [388, 318]

    for i, label in enumerate(OPCOES):
        y  = OPT_Y[i]
        lx = CX - LARGURAS[i] // 2
        if i == opcao_menu:
            glColor3f(0.1, 0.25, 0.1)
            retangulo(BOX_X + 8, y - 8, BOX_W - 16, 34)
            glColor3f(0.3, 0.8, 0.3)
            glLineWidth(1.5)
            retangulo_borda(BOX_X + 8, y - 8, BOX_W - 16, 34)
            glLineWidth(1.0)
            glColor3f(0.9, 1.0, 0.3)
            desenhar_texto(BOX_X + 14, y + 4, '>', escala=0.9)
            glColor3f(1.0, 1.0, 1.0)
        else:
            glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(lx, y + 4, label, escala=0.9)

    glColor3f(0.35, 0.35, 0.35)
    desenhar_texto(CX - 91, 268, 'W/S ou Setas: navegar', escala=0.72)
    desenhar_texto(CX - 74, 250, 'ESPACO: confirmar',     escala=0.72)
    desenhar_texto(CX - 30, 232, 'Q: sair',               escala=0.72)

    glFlush()


def desenhar_tela_aguardando():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.72)
    retangulo(CX - 210, CY - 55, 420, 110)
    glDisable(GL_BLEND)

    if modo == '2P':
        glColor3f(0.4, 0.9, 0.4)
        desenhar_texto(CX - 148, CY + 30, '2 JOGADORES', escala=1.2)
        glColor3f(0.65, 0.65, 0.65)
        desenhar_texto(CX - 185, CY - 8,  'J1: WASD   J2: Setas do teclado', escala=0.72)
    else:
        glColor3f(1.0, 1.0, 0.3)
        desenhar_texto(CX - 122, CY + 30, '1 JOGADOR', escala=1.2)
        glColor3f(0.65, 0.65, 0.65)
        desenhar_texto(CX - 118, CY - 8,  'J1: WASD   vs   CPU', escala=0.72)

    glColor3f(0.85, 0.85, 0.85)
    desenhar_texto(CX - 152, CY - 36, 'Pressione qualquer tecla!', escala=0.75)


def desenhar_tela_vitoria():
    CX = LARGURA // 2
    CY = AREA_H  // 2

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.78)
    retangulo(CX - 230, CY - 100, 460, 200)
    glDisable(GL_BLEND)

    if vencedor == 1:
        cor    = (0.3, 0.6, 1.0)
        titulo = 'JOGADOR 1 VENCEU!'
    elif modo == '1P':
        cor    = (1.0, 0.4, 0.2)
        titulo = 'CPU VENCEU!'
    else:
        cor    = (1.0, 0.3, 0.3)
        titulo = 'JOGADOR 2 VENCEU!'

    glColor3f(*cor)
    glLineWidth(2.0)
    retangulo_borda(CX - 230, CY - 100, 460, 200)
    glLineWidth(1.0)

    larg = len(titulo) * 104 * 0.12 * 1.3 / 2
    glColor3f(*cor)
    desenhar_texto(CX - larg, CY + 44, titulo, escala=1.3)

    placar = f'Placar final:  {jogador1["gols"]} x {jogador2["gols"]}'
    larg2  = len(placar) * 104 * 0.12 * 0.9 / 2
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(CX - larg2, CY + 2, placar, escala=0.9)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(CX - 145, CY - 40, 'R: menu principal    Q: sair', escala=0.72)


# --- Lógica ---

def mover_jogadores():
    r = TAM_JOGADOR // 2

    if 'w' in teclas1 and jogador1['y'] + r < AREA_H:  jogador1['y'] += VELOCIDADE
    if 's' in teclas1 and jogador1['y'] - r > 0:        jogador1['y'] -= VELOCIDADE
    if 'a' in teclas1 and jogador1['x'] - r > 0:        jogador1['x'] -= VELOCIDADE
    if 'd' in teclas1 and jogador1['x'] + r < LARGURA:  jogador1['x'] += VELOCIDADE

    if modo == '2P':
        if 'up'    in teclas2 and jogador2['y'] + r < AREA_H:  jogador2['y'] += VELOCIDADE
        if 'down'  in teclas2 and jogador2['y'] - r > 0:        jogador2['y'] -= VELOCIDADE
        if 'left'  in teclas2 and jogador2['x'] - r > 0:        jogador2['x'] -= VELOCIDADE
        if 'right' in teclas2 and jogador2['x'] + r < LARGURA:  jogador2['x'] += VELOCIDADE
    else:
        mover_cpu()


def mover_cpu():
    r   = TAM_JOGADOR // 2
    bx  = bola['x']
    by  = bola['y']
    cx2 = jogador2['x']
    cy2 = jogador2['y']

    # Alvo: bola quando ela está no lado da CPU, senão posição defensiva
    if bx > LARGURA // 2:
        alvo_x = bx
        alvo_y = by
    else:
        alvo_x = 3 * LARGURA // 4
        alvo_y = AREA_H // 2

    dx = alvo_x - cx2
    dy = alvo_y - cy2
    dist = math.sqrt(dx * dx + dy * dy)

    if dist > 2:
        nx = dx / dist
        ny = dy / dist
        novo_x = cx2 + nx * CPU_VEL
        novo_y = cy2 + ny * CPU_VEL
        jogador2['x'] = max(r, min(LARGURA - r, novo_x))
        jogador2['y'] = max(r, min(AREA_H  - r, novo_y))


def colisao_jogador_bola(jogador):
    dx   = bola['x'] - jogador['x']
    dy   = bola['y'] - jogador['y']
    dist = math.sqrt(dx * dx + dy * dy)
    raio = (TAM_JOGADOR + TAM_BOLA) / 2
    if dist < raio:
        if dist > 0:
            dx /= dist
            dy /= dist
        bola['vx'] = dx * 8
        bola['vy'] = dy * 8


def mover_bola():
    global tempo_msg, msg_gol, estado, vencedor

    bola['vx'] *= 0.98
    bola['vy'] *= 0.98
    bola['x']  += bola['vx']
    bola['y']  += bola['vy']

    r = TAM_BOLA / 2

    if bola['y'] - r <= 0:
        bola['y'] = r
        bola['vy'] = abs(bola['vy']) * 0.8
    elif bola['y'] + r >= AREA_H:
        bola['y'] = AREA_H - r
        bola['vy'] = -abs(bola['vy']) * 0.8

    # Gol esquerdo → J2/CPU marca
    if (bola['x'] - r <= GOL_ESQ['x']
            and GOL_ESQ['y1'] <= bola['y'] <= GOL_ESQ['y2']):
        jogador2['gols'] += 1
        msg_gol   = 'GOL DA CPU!' if modo == '1P' else 'GOL DO JOGADOR 2!'
        tempo_msg = 120
        reposicionar_bola()
        if jogador2['gols'] >= GOLS_VITORIA:
            estado   = 'VITORIA'
            vencedor = 2

    # Gol direito → J1 marca
    elif (bola['x'] + r >= GOL_DIR['x']
            and GOL_DIR['y1'] <= bola['y'] <= GOL_DIR['y2']):
        jogador1['gols'] += 1
        msg_gol   = 'GOL DO JOGADOR 1!'
        tempo_msg = 120
        reposicionar_bola()
        if jogador1['gols'] >= GOLS_VITORIA:
            estado   = 'VITORIA'
            vencedor = 1

    bola['x'] = max(r, min(LARGURA - r, bola['x']))


def reposicionar_bola():
    bola['x']  = float(LARGURA // 2)
    bola['y']  = float(AREA_H  // 2)
    bola['vx'] = 0.0
    bola['vy'] = 0.0


def verificar_colisoes():
    colisao_jogador_bola(jogador1)
    colisao_jogador_bola(jogador2)

    dx   = jogador1['x'] - jogador2['x']
    dy   = jogador1['y'] - jogador2['y']
    dist = math.sqrt(dx * dx + dy * dy)
    if 0 < dist < TAM_JOGADOR:
        dx /= dist
        dy /= dist
        jogador1['x'] += dx * 5
        jogador1['y'] += dy * 5
        jogador2['x'] -= dx * 5
        jogador2['y'] -= dy * 5


# --- Loop principal ---

def display():
    if estado == 'MENU':
        desenhar_menu()
        return

    glClear(GL_COLOR_BUFFER_BIT)
    desenhar_campo()
    desenhar_gols()
    desenhar_jogadores()
    desenhar_bola()
    desenhar_hud()
    desenhar_msg_gol()

    if estado == 'AGUARDANDO':
        desenhar_tela_aguardando()
    elif estado == 'VITORIA':
        desenhar_tela_vitoria()

    glFlush()


def atualizar(valor=0):
    global tempo_msg
    if estado == 'JOGANDO':
        mover_jogadores()
        mover_bola()
        verificar_colisoes()
        if tempo_msg > 0:
            tempo_msg -= 1
    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def tecla_normal(tecla, x, y):
    global estado, opcao_menu
    tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)

    if tecla == 'r':
        estado = 'MENU'
        opcao_menu = 0
        glutPostRedisplay()
        return

    if estado == 'MENU':
        if tecla == ' ':
            inicializar_jogo(['1P', '2P'][opcao_menu])
            glutPostRedisplay()
        elif tecla == 'w':
            opcao_menu = (opcao_menu - 1) % 2
            glutPostRedisplay()
        elif tecla == 's':
            opcao_menu = (opcao_menu + 1) % 2
            glutPostRedisplay()
        return

    if estado == 'VITORIA':
        return

    if estado == 'AGUARDANDO':
        estado = 'JOGANDO'

    teclas1.add(tecla)


def tecla_normal_up(tecla, x, y):
    tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas1.discard(tecla)


def tecla_especial(tecla, x, y):
    global estado, opcao_menu

    if estado == 'MENU':
        if tecla == GLUT_KEY_UP:
            opcao_menu = (opcao_menu - 1) % 2
            glutPostRedisplay()
        elif tecla == GLUT_KEY_DOWN:
            opcao_menu = (opcao_menu + 1) % 2
            glutPostRedisplay()
        return

    if estado == 'VITORIA':
        return

    if estado == 'AGUARDANDO':
        estado = 'JOGANDO'

    if tecla == GLUT_KEY_UP:    teclas2.add('up')
    elif tecla == GLUT_KEY_DOWN:  teclas2.add('down')
    elif tecla == GLUT_KEY_LEFT:  teclas2.add('left')
    elif tecla == GLUT_KEY_RIGHT: teclas2.add('right')


def tecla_especial_up(tecla, x, y):
    if tecla == GLUT_KEY_UP:    teclas2.discard('up')
    elif tecla == GLUT_KEY_DOWN:  teclas2.discard('down')
    elif tecla == GLUT_KEY_LEFT:  teclas2.discard('left')
    elif tecla == GLUT_KEY_RIGHT: teclas2.discard('right')


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
    glutCreateWindow(b'Futebol')

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
