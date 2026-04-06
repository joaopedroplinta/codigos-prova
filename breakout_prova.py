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

TIJOLO_COLS   = 10
TIJOLO_LINHAS = 6
TIJOLO_W      = LARGURA // TIJOLO_COLS
TIJOLO_H      = 24
TIJOLO_Y_INI  = ALTURA - 80 - TIJOLO_LINHAS * TIJOLO_H

HUD_H     = 30
VIDAS_MAX = 3

# Power-ups
CHANCE_POWERUP      = 0.28   # 28 % de chance ao quebrar tijolo
POWERUP_VEL         = 2.5
POWERUP_W           = 26
POWERUP_H           = 14
EFEITO_LARGO_FRAMES = 300    # ~5 s de paddle largo
PADDLE_LARGO_W      = 160

# Tipos de power-up
PU_MULTIBALL = 'MULTIBALL'   # lança 2 bolas extras
PU_VIDA      = 'VIDA'        # ganha 1 vida
PU_LARGO     = 'LARGO'       # paddle largo temporário

CORES_PU = {
    PU_MULTIBALL: (0.3, 1.0, 0.3),
    PU_VIDA:      (1.0, 0.3, 0.3),
    PU_LARGO:     (0.3, 0.7, 1.0),
}

# Cores por linha (RGB)
CORES_LINHAS = [
    (0.95, 0.25, 0.25),
    (0.95, 0.55, 0.15),
    (0.95, 0.90, 0.15),
    (0.25, 0.85, 0.25),
    (0.25, 0.55, 0.95),
    (0.75, 0.25, 0.95),
]

# --- Estado do jogo ---
paddle_x      = 0.0
paddle_w_atual = PADDLE_W   # largura corrente (pode ser aumentada por power-up)
bolas         = []          # lista de {'x','y','vx','vy','ativa'}
tijolos       = []          # lista de [col, lin, vivo]
powerups      = []          # lista de {'x','y','tipo'}
pontuacao     = 0
vidas         = VIDAS_MAX
estado        = 'AGUARDANDO'
teclas        = set()
efeito_largo  = 0           # frames restantes do paddle largo


def nova_bola(x, y, angulo_graus=None):
    if angulo_graus is None:
        angulo_graus = random.uniform(50, 130)
    rad = math.radians(angulo_graus)
    return {
        'x': float(x), 'y': float(y),
        'vx': VEL_BOLA * math.cos(rad),
        'vy': VEL_BOLA * math.sin(rad),
        'ativa': False,
    }


def inicializar_tijolos():
    global tijolos
    tijolos = [
        [c, l, True]
        for l in range(TIJOLO_LINHAS)
        for c in range(TIJOLO_COLS)
    ]


def posicao_tijolo(col, lin):
    return col * TIJOLO_W, TIJOLO_Y_INI + lin * TIJOLO_H


def resetar_bolas():
    global bolas
    bolas = [nova_bola(paddle_x + paddle_w_atual / 2,
                       PADDLE_Y + PADDLE_H + BOLA_R + 2)]


def inicializar_jogo():
    global paddle_x, paddle_w_atual, pontuacao, vidas, estado, powerups, efeito_largo
    paddle_x      = LARGURA / 2 - PADDLE_W / 2
    paddle_w_atual = PADDLE_W
    pontuacao     = 0
    vidas         = VIDAS_MAX
    estado        = 'AGUARDANDO'
    powerups      = []
    efeito_largo  = 0
    inicializar_tijolos()
    resetar_bolas()


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

        glColor3f(r, g, b)
        desenhar_retangulo(x + margem, y + margem,
                           TIJOLO_W - margem * 2, TIJOLO_H - margem * 2)
        glColor3f(min(r + 0.25, 1.0), min(g + 0.25, 1.0), min(b + 0.25, 1.0))
        desenhar_retangulo(x + margem, y + TIJOLO_H - margem * 2 - 4,
                           TIJOLO_W - margem * 2, 4)
        glColor3f(r * 0.4, g * 0.4, b * 0.4)
        desenhar_retangulo_borda(x + margem, y + margem,
                                  TIJOLO_W - margem * 2, TIJOLO_H - margem * 2)


def desenhar_paddle():
    x = paddle_x
    y = PADDLE_Y
    w = paddle_w_atual
    glColor3f(0.85, 0.85, 0.95)
    desenhar_retangulo(x, y, w, PADDLE_H)
    glColor3f(1.0, 1.0, 1.0)
    desenhar_retangulo(x + 4, y + PADDLE_H - 4, w - 8, 4)
    glColor3f(0.4, 0.4, 0.6)
    desenhar_retangulo_borda(x, y, w, PADDLE_H)


def desenhar_bolas():
    for b in bolas:
        glColor3f(1.0, 0.85, 0.2)
        desenhar_circulo(b['x'], b['y'], BOLA_R)
        glColor3f(1.0, 1.0, 0.8)
        desenhar_circulo(b['x'] - BOLA_R * 0.3, b['y'] + BOLA_R * 0.35, BOLA_R * 0.3)


def desenhar_powerups():
    for pu in powerups:
        r, g, b = CORES_PU[pu['tipo']]
        # Cápsula colorida
        glColor3f(r, g, b)
        desenhar_retangulo(pu['x'] - POWERUP_W / 2, pu['y'] - POWERUP_H / 2,
                           POWERUP_W, POWERUP_H)
        glColor3f(r * 0.5, g * 0.5, b * 0.5)
        desenhar_retangulo_borda(pu['x'] - POWERUP_W / 2, pu['y'] - POWERUP_H / 2,
                                  POWERUP_W, POWERUP_H)
        # Label
        glColor3f(0.05, 0.05, 0.05)
        label = {'MULTIBALL': 'x3', 'VIDA': '+1', 'LARGO': '<==>'}[pu['tipo']]
        desenhar_texto(pu['x'] - POWERUP_W / 2 + 2, pu['y'] - 4, label, escala=0.55)


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

    # Indicador de bolas ativas
    n_bolas = len(bolas)
    if n_bolas > 1:
        glColor3f(0.3, 1.0, 0.3)
        desenhar_texto(200, ALTURA - 23, f"Bolas: {n_bolas}", escala=0.85)

    # Indicador de paddle largo com barra de tempo restante
    if efeito_largo > 0:
        bx, by, bw, bh = 310, ALTURA - 24, 110, 10
        t = efeito_largo / EFEITO_LARGO_FRAMES  # 1.0 → 0.0

        # Fundo da barra
        glColor3f(0.15, 0.15, 0.3)
        desenhar_retangulo(bx, by, bw, bh)

        # Preenchimento (azul → amarelo → vermelho conforme acaba)
        if t > 0.5:
            r, g, b = 0.3, 0.7, 1.0
        elif t > 0.25:
            r, g, b = 1.0, 0.8, 0.1
        else:
            r, g, b = 1.0, 0.25, 0.25
        glColor3f(r, g, b)
        desenhar_retangulo(bx, by, bw * t, bh)

        # Borda
        glColor3f(0.5, 0.5, 0.7)
        desenhar_retangulo_borda(bx, by, bw, bh)

        # Label
        glColor3f(0.8, 0.8, 1.0)
        desenhar_texto(bx, by + 13, "LARGO", escala=0.65)

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

    glColor3f(0.2, 0.2, 0.4)
    glLineWidth(2.0)
    desenhar_retangulo_borda(0, 0, LARGURA, ALTURA - HUD_H)
    glLineWidth(1.0)

    desenhar_tijolos()
    desenhar_powerups()
    desenhar_paddle()
    desenhar_bolas()
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

def sortear_powerup():
    """Retorna um tipo de power-up aleatório ou None."""
    if random.random() > CHANCE_POWERUP:
        return None
    return random.choice([PU_MULTIBALL, PU_MULTIBALL, PU_LARGO, PU_VIDA])


def verificar_colisao_tijolo(b):
    """Verifica colisão de uma bola com tijolos. Retorna True se houve colisão."""
    global pontuacao
    bx, by = b['x'], b['y']
    for tijolo in tijolos:
        if not tijolo[2]:
            continue
        col, lin, _ = tijolo
        tx, ty = posicao_tijolo(col, lin)
        tw, th = TIJOLO_W - 2, TIJOLO_H - 2

        px = max(tx, min(bx, tx + tw))
        py = max(ty, min(by, ty + th))

        if math.hypot(bx - px, by - py) <= BOLA_R:
            tijolo[2] = False
            pontuacao += 10

            # Spawna power-up no centro do tijolo
            tipo_pu = sortear_powerup()
            if tipo_pu:
                powerups.append({
                    'x': tx + TIJOLO_W / 2,
                    'y': ty + TIJOLO_H / 2,
                    'tipo': tipo_pu,
                })

            # Reflexão: px==bx → bateu no topo/base → inverte vy
            if px == bx:
                b['vy'] = -b['vy']
                if by < ty + th / 2:
                    b['y'] = ty - BOLA_R - 1
                else:
                    b['y'] = ty + th + BOLA_R + 1
            else:
                b['vx'] = -b['vx']
                if bx < tx + tw / 2:
                    b['x'] = tx - BOLA_R - 1
                else:
                    b['x'] = tx + tw + BOLA_R + 1
            return True
    return False


def aplicar_powerup(tipo):
    """Ativa o efeito do power-up coletado."""
    global vidas, efeito_largo, paddle_w_atual

    if tipo == PU_MULTIBALL:
        # Cada bola ativa gera mais uma clone com ângulo levemente diferente
        novas = []
        for b in bolas:
            if b['ativa']:
                angulo_base = math.degrees(math.atan2(b['vy'], b['vx']))
                for delta in (-35, 35):
                    nb = nova_bola(b['x'], b['y'], angulo_base + delta)
                    nb['ativa'] = True
                    novas.append(nb)
        bolas.extend(novas)

    elif tipo == PU_VIDA:
        vidas = min(vidas + 1, VIDAS_MAX + 2)  # pode passar do máximo original

    elif tipo == PU_LARGO:
        efeito_largo  = EFEITO_LARGO_FRAMES
        paddle_w_atual = PADDLE_LARGO_W
        # Garante que o paddle não saia da tela
        global paddle_x
        if paddle_x + paddle_w_atual > LARGURA:
            paddle_x = LARGURA - paddle_w_atual


def mover_bola(b):
    """Move uma bola e trata colisões com paredes, paddle e tijolos."""
    b['x'] += b['vx']
    b['y'] += b['vy']

    # Paredes laterais
    if b['x'] - BOLA_R <= 0:
        b['x'] = BOLA_R
        b['vx'] = abs(b['vx'])
    if b['x'] + BOLA_R >= LARGURA:
        b['x'] = LARGURA - BOLA_R
        b['vx'] = -abs(b['vx'])

    # Teto
    if b['y'] + BOLA_R >= ALTURA - HUD_H:
        b['y'] = ALTURA - HUD_H - BOLA_R
        b['vy'] = -abs(b['vy'])

    # Paddle
    if (b['vy'] < 0
            and paddle_x <= b['x'] <= paddle_x + paddle_w_atual
            and PADDLE_Y <= b['y'] - BOLA_R <= PADDLE_Y + PADDLE_H):
        b['y'] = PADDLE_Y + PADDLE_H + BOLA_R
        b['vy'] = abs(b['vy'])
        offset = (b['x'] - (paddle_x + paddle_w_atual / 2)) / (paddle_w_atual / 2)
        b['vx'] = offset * VEL_BOLA
        speed = math.hypot(b['vx'], b['vy'])
        if speed > 0:
            b['vx'] = b['vx'] / speed * VEL_BOLA
            b['vy'] = b['vy'] / speed * VEL_BOLA

    verificar_colisao_tijolo(b)


def atualizar(valor=0):
    global paddle_x, vidas, estado, efeito_largo, paddle_w_atual

    if estado != 'JOGANDO':
        return

    # Movimento do paddle
    if ('a' in teclas or 'left' in teclas) and paddle_x > 0:
        paddle_x = max(paddle_x - PADDLE_VEL, 0)
    if ('d' in teclas or 'right' in teclas) and paddle_x + paddle_w_atual < LARGURA:
        paddle_x = min(paddle_x + PADDLE_VEL, LARGURA - paddle_w_atual)

    # Timer do efeito largo
    if efeito_largo > 0:
        efeito_largo -= 1
        if efeito_largo == 0:
            paddle_w_atual = PADDLE_W

    # Bola(s) não lançadas ficam presas no paddle
    for b in bolas:
        if not b['ativa']:
            b['x'] = paddle_x + paddle_w_atual / 2

    # Move bolas ativas
    for b in bolas:
        if b['ativa']:
            mover_bola(b)

    # Remove bolas que caíram
    bolas[:] = [b for b in bolas if b['ativa'] and b['y'] > 0 or not b['ativa']]

    # Se todas as bolas sumiram (inclusive inativas) → perde vida
    if not bolas:
        vidas -= 1
        if vidas <= 0:
            estado = 'GAME_OVER'
        else:
            resetar_bolas()

    # Move power-ups e verifica coleta pelo paddle
    for pu in powerups[:]:
        pu['y'] -= POWERUP_VEL
        if pu['y'] < 0:
            powerups.remove(pu)
            continue
        # Paddle coletou?
        if (PADDLE_Y <= pu['y'] <= PADDLE_Y + PADDLE_H
                and paddle_x - POWERUP_W / 2 <= pu['x'] <= paddle_x + paddle_w_atual + POWERUP_W / 2):
            aplicar_powerup(pu['tipo'])
            powerups.remove(pu)

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
            for b in bolas:
                b['ativa'] = True
            glutTimerFunc(VELOCIDADE_MS, atualizar, 0)
        elif estado == 'JOGANDO':
            for b in bolas:
                if not b['ativa']:
                    b['ativa'] = True


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
    glutReshapeFunc(redimensionar)
    glutKeyboardFunc(teclado)
    glutKeyboardUpFunc(teclado_up)
    glutSpecialFunc(teclado_especial)
    glutSpecialUpFunc(teclado_especial_up)

    glutMainLoop()


if __name__ == "__main__":
    main()
