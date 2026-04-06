"""
Asteroids — Computação Gráfica
Conceitos cobertos:
  - glPushMatrix / glPopMatrix
  - glTranslatef / glRotatef  (rotação da nave e dos asteroides)
  - Wrap-around de coordenadas
  - Desenho com GL_LINE_LOOP e GL_LINES
  - Detecção de colisão por distância (círculos)
  - glutTimerFunc para animação
"""
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
VELOCIDADE_MS = 20   # 50 fps

HUD_H         = 30
ACEL_NAVE     = 0.25
FRICCAO       = 0.98
VEL_MAX_NAVE  = 8.0
VEL_ROTACAO   = 4.5  # graus por frame
VEL_PROJÉTIL  = 10.0
VIDA_PROJ     = 55   # frames que o projétil vive
VIDAS_MAX     = 3

RAIO_AST_GRANDE = 40
RAIO_AST_MEDIO  = 22
RAIO_AST_PEQUENO = 12

PONTOS_GRANDE  = 20
PONTOS_MEDIO   = 50
PONTOS_PEQUENO = 100

# --- Estado do jogo ---
nave       = {}
projeteis  = []
asteroides = []
particulas = []  # efeito de explosão
pontuacao  = 0
vidas      = VIDAS_MAX
estado     = 'AGUARDANDO'   # 'AGUARDANDO', 'JOGANDO', 'GAME_OVER', 'VITORIA'
teclas     = set()


# ---- Utilitários ----

def angulo_para_vetor(graus):
    rad = math.radians(graus)
    return math.cos(rad), math.sin(rad)


def wrap(val, maximo):
    """Mantém o valor dentro do intervalo [0, maximo] com wrap-around."""
    return val % maximo


def distancia(a, b):
    return math.hypot(a['x'] - b['x'], a['y'] - b['y'])


# ---- Inicialização ----

def pontos_asteroide(n=10):
    """Polígono irregular para dar aparência rochosa."""
    pts = []
    for i in range(n):
        ang = 2 * math.pi * i / n
        r = random.uniform(0.7, 1.0)
        pts.append((math.cos(ang) * r, math.sin(ang) * r))
    return pts


def criar_asteroide(x, y, raio, vel_x=None, vel_y=None):
    ang = random.uniform(0, 360)
    speed = random.uniform(1.2, 2.5)
    vx = vel_x if vel_x is not None else math.cos(math.radians(ang)) * speed
    vy = vel_y if vel_y is not None else math.sin(math.radians(ang)) * speed
    return {
        'x': x, 'y': y,
        'vx': vx, 'vy': vy,
        'raio': raio,
        'rotacao': random.uniform(0, 360),
        'vel_rot': random.uniform(-1.5, 1.5),
        'forma': pontos_asteroide(random.randint(8, 12)),
    }


def criar_nave():
    return {
        'x': float(LARGURA // 2),
        'y': float(ALTURA  // 2),
        'vx': 0.0, 'vy': 0.0,
        'angulo': 90.0,  # aponta para cima
        'acelerando': False,
        'invencivel': 120,  # frames de invencibilidade ao iniciar/morrer
    }


def inicializar_jogo():
    global nave, projeteis, asteroides, particulas, pontuacao, vidas, estado
    nave       = criar_nave()
    projeteis  = []
    particulas = []
    pontuacao  = 0
    vidas      = VIDAS_MAX
    estado     = 'AGUARDANDO'
    asteroides = []
    # 4 asteroides grandes em posições longe da nave
    for _ in range(4):
        while True:
            x = random.uniform(0, LARGURA)
            y = random.uniform(0, ALTURA - HUD_H)
            if math.hypot(x - nave['x'], y - nave['y']) > 150:
                break
        asteroides.append(criar_asteroide(x, y, RAIO_AST_GRANDE))


def explodir_asteroide(ast):
    """Substitui asteroide por dois menores (se possível) e cria partículas."""
    asteroides.remove(ast)

    # Partículas de debris
    for _ in range(10):
        ang = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.0, 3.5)
        particulas.append({
            'x': ast['x'], 'y': ast['y'],
            'vx': math.cos(ang) * speed,
            'vy': math.sin(ang) * speed,
            'vida': random.randint(15, 35),
        })

    if ast['raio'] == RAIO_AST_GRANDE:
        raio_filho = RAIO_AST_MEDIO
    elif ast['raio'] == RAIO_AST_MEDIO:
        raio_filho = RAIO_AST_PEQUENO
    else:
        return  # pequeno: some

    for _ in range(2):
        asteroides.append(criar_asteroide(ast['x'], ast['y'], raio_filho))


# ---- Funções de desenho ----

def desenhar_retangulo(x, y, w, h):
    glBegin(GL_POLYGON)
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


def desenhar_nave():
    """
    Desenha a nave usando transformações de modelo:
      glTranslatef → posiciona na tela
      glRotatef    → orienta conforme o ângulo
    A nave é desenhada no referencial local (centrada na origem).
    """
    alpha = 1.0
    if nave['invencivel'] > 0 and nave['invencivel'] % 10 < 5:
        return  # pisca durante invencibilidade

    glPushMatrix()
    glTranslatef(nave['x'], nave['y'], 0)
    glRotatef(nave['angulo'], 0, 0, 1)

    # Corpo da nave (triângulo)
    glColor3f(0.8, 0.9, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINE_LOOP)
    glVertex2f( 14,  0)   # proa (aponta para direita no ref. local)
    glVertex2f(-10,  8)   # asa esquerda
    glVertex2f( -6,  0)   # centro traseiro
    glVertex2f(-10, -8)   # asa direita
    glEnd()
    glLineWidth(1.0)

    # Chama de aceleração
    if nave['acelerando']:
        glColor3f(1.0, 0.6, 0.1)
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glVertex2f(-6,  4)
        glVertex2f(-18, random.uniform(-2, 2))
        glVertex2f(-6, -4)
        glVertex2f(-18, random.uniform(-2, 2))
        glEnd()
        glLineWidth(1.0)

    glPopMatrix()


def desenhar_asteroides():
    for ast in asteroides:
        glPushMatrix()
        glTranslatef(ast['x'], ast['y'], 0)
        glRotatef(ast['rotacao'], 0, 0, 1)

        r = ast['raio']
        glColor3f(0.65, 0.55, 0.45)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        for fx, fy in ast['forma']:
            glVertex2f(fx * r, fy * r)
        glEnd()
        glLineWidth(1.0)

        glPopMatrix()


def desenhar_projeteis():
    glColor3f(1.0, 0.95, 0.5)
    for p in projeteis:
        desenhar_circulo(p['x'], p['y'], 3, segs=8)


def desenhar_particulas():
    for part in particulas:
        t = part['vida'] / 35.0
        glColor3f(1.0, max(0.0, t), 0.0)
        desenhar_circulo(part['x'], part['y'], max(1, t * 3), segs=6)


def desenhar_hud():
    glColor3f(0.04, 0.04, 0.10)
    desenhar_retangulo(0, ALTURA - HUD_H, LARGURA, HUD_H)
    glColor3f(0.2, 0.2, 0.5)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, ALTURA - HUD_H)
    glVertex2f(LARGURA, ALTURA - HUD_H)
    glEnd()
    glLineWidth(1.0)

    glColor3f(0.9, 0.9, 0.3)
    desenhar_texto(8, ALTURA - 23, f"Pontos: {pontuacao}", escala=1.0)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(LARGURA - 120, ALTURA - 23, "Vidas:", escala=0.8)
    for i in range(vidas):
        cx = LARGURA - 28 - i * 22
        cy = ALTURA - HUD_H // 2
        # Miniaturas de naves como triângulos
        glColor3f(0.7, 0.85, 1.0)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(cx + 7,  cy)
        glVertex2f(cx - 5,  cy + 5)
        glVertex2f(cx - 3,  cy)
        glVertex2f(cx - 5,  cy - 5)
        glEnd()
        glLineWidth(1.0)


def desenhar_tela_overlay(titulo, cor):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.75)
    desenhar_retangulo(200, 230, 400, 150)
    glDisable(GL_BLEND)

    glColor3f(*cor)
    desenhar_texto(230, 340, titulo, escala=1.4)

    glColor3f(0.9, 0.9, 0.9)
    desenhar_texto(255, 296, f"Pontos: {pontuacao}", escala=1.0)

    glColor3f(0.5, 0.5, 0.5)
    desenhar_texto(240, 258, "R: reiniciar  Q: sair", escala=0.75)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    glColor3f(0.02, 0.02, 0.05)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    # Estrelas de fundo (posições fixas semeadas)
    random.seed(42)
    glColor3f(0.6, 0.6, 0.7)
    glPointSize(1.5)
    glBegin(GL_POINTS)
    for _ in range(80):
        glVertex2f(random.uniform(0, LARGURA), random.uniform(0, ALTURA - HUD_H))
    glEnd()
    glPointSize(1.0)
    random.seed()  # restaura aleatoriedade

    desenhar_particulas()
    desenhar_asteroides()
    desenhar_projeteis()
    desenhar_nave()
    desenhar_hud()

    if estado == 'AGUARDANDO':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.75)
        desenhar_retangulo(185, 225, 430, 170)
        glDisable(GL_BLEND)
        glColor3f(0.5, 0.8, 1.0)
        desenhar_texto(215, 355, "ASTEROIDS", escala=1.6)
        glColor3f(0.85, 0.85, 0.85)
        desenhar_texto(200, 310, "Setas: rotacionar / acelerar", escala=0.78)
        glColor3f(0.85, 0.85, 0.85)
        desenhar_texto(222, 283, "ESPACO: atirar", escala=0.78)
        glColor3f(0.9, 0.9, 0.3)
        desenhar_texto(228, 255, "Pressione qualquer tecla!", escala=0.78)
        glColor3f(0.45, 0.45, 0.45)
        desenhar_texto(240, 233, "R: reiniciar  Q: sair", escala=0.7)
    elif estado == 'GAME_OVER':
        desenhar_tela_overlay("GAME OVER", (1.0, 0.25, 0.25))
    elif estado == 'VITORIA':
        desenhar_tela_overlay("VOCE VENCEU!", (0.25, 1.0, 0.5))

    glFlush()


# ---- Lógica de atualização ----

def atirar():
    dx, dy = angulo_para_vetor(nave['angulo'])
    projeteis.append({
        'x': nave['x'] + dx * 16,
        'y': nave['y'] + dy * 16,
        'vx': nave['vx'] + dx * VEL_PROJÉTIL,
        'vy': nave['vy'] + dy * VEL_PROJÉTIL,
        'vida': VIDA_PROJ,
    })


def atualizar(valor=0):
    global estado, vidas, pontuacao

    if estado != 'JOGANDO':
        return

    # Entradas
    if 'left' in teclas:
        nave['angulo'] = (nave['angulo'] + VEL_ROTACAO) % 360
    if 'right' in teclas:
        nave['angulo'] = (nave['angulo'] - VEL_ROTACAO) % 360

    nave['acelerando'] = 'up' in teclas
    if nave['acelerando']:
        dx, dy = angulo_para_vetor(nave['angulo'])
        nave['vx'] += dx * ACEL_NAVE
        nave['vy'] += dy * ACEL_NAVE

    # Limitar velocidade
    speed = math.hypot(nave['vx'], nave['vy'])
    if speed > VEL_MAX_NAVE:
        nave['vx'] = nave['vx'] / speed * VEL_MAX_NAVE
        nave['vy'] = nave['vy'] / speed * VEL_MAX_NAVE

    # Fricção (espaço tem pouca resistência)
    nave['vx'] *= FRICCAO
    nave['vy'] *= FRICCAO

    # Move nave com wrap-around
    nave['x'] = wrap(nave['x'] + nave['vx'], LARGURA)
    nave['y'] = wrap(nave['y'] + nave['vy'], ALTURA - HUD_H)

    if nave['invencivel'] > 0:
        nave['invencivel'] -= 1

    # Move e envelhece projéteis
    for p in projeteis[:]:
        p['x'] = wrap(p['x'] + p['vx'], LARGURA)
        p['y'] = wrap(p['y'] + p['vy'], ALTURA - HUD_H)
        p['vida'] -= 1
        if p['vida'] <= 0:
            projeteis.remove(p)

    # Move e rotaciona asteroides
    for ast in asteroides:
        ast['x'] = wrap(ast['x'] + ast['vx'], LARGURA)
        ast['y'] = wrap(ast['y'] + ast['vy'], ALTURA - HUD_H)
        ast['rotacao'] = (ast['rotacao'] + ast['vel_rot']) % 360

    # Partículas
    for part in particulas[:]:
        part['x'] += part['vx']
        part['y'] += part['vy']
        part['vida'] -= 1
        if part['vida'] <= 0:
            particulas.remove(part)

    # Colisão projétil × asteroide
    for p in projeteis[:]:
        for ast in asteroides[:]:
            if distancia(p, ast) < ast['raio']:
                if p in projeteis:
                    projeteis.remove(p)
                if ast['raio'] == RAIO_AST_GRANDE:
                    pontuacao += PONTOS_GRANDE
                elif ast['raio'] == RAIO_AST_MEDIO:
                    pontuacao += PONTOS_MEDIO
                else:
                    pontuacao += PONTOS_PEQUENO
                explodir_asteroide(ast)
                break

    # Colisão nave × asteroide
    if nave['invencivel'] == 0:
        for ast in asteroides:
            if distancia(nave, ast) < ast['raio'] + 10:
                vidas -= 1
                if vidas <= 0:
                    estado = 'GAME_OVER'
                    glutPostRedisplay()
                    return
                # Reposiciona a nave no centro
                nave['x']         = float(LARGURA // 2)
                nave['y']         = float(ALTURA  // 2)
                nave['vx']        = 0.0
                nave['vy']        = 0.0
                nave['angulo']    = 90.0
                nave['invencivel'] = 120
                break

    # Vitória: todos os asteroides destruídos
    if not asteroides:
        estado = 'VITORIA'

    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# ---- Teclado ----

def teclado(tecla, x, y):
    global estado
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla in ('q', '\x1b'):
        os._exit(0)
    if tecla == 'r':
        inicializar_jogo()
        glutPostRedisplay()
        return

    teclas.add(tecla)

    if tecla == ' ' and estado == 'JOGANDO':
        atirar()

    if estado == 'AGUARDANDO' and tecla not in ('q', 'r'):
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


def teclado_up(tecla, x, y):
    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()
    teclas.discard(tecla)


def teclado_especial(tecla, x, y):
    global estado
    if tecla == GLUT_KEY_LEFT:
        teclas.add('left')
    elif tecla == GLUT_KEY_RIGHT:
        teclas.add('right')
    elif tecla == GLUT_KEY_UP:
        teclas.add('up')

    if estado == 'AGUARDANDO':
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


def teclado_especial_up(tecla, x, y):
    if tecla == GLUT_KEY_LEFT:
        teclas.discard('left')
    elif tecla == GLUT_KEY_RIGHT:
        teclas.discard('right')
    elif tecla == GLUT_KEY_UP:
        teclas.discard('up')


# ---- Inicialização OpenGL ----

def inicializar_opengl():
    glClearColor(0.02, 0.02, 0.05, 1.0)
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
    glutCreateWindow(b"Asteroids - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutKeyboardUpFunc(teclado_up)
    glutSpecialFunc(teclado_especial)
    glutSpecialUpFunc(teclado_especial_up)

    glutMainLoop()


if __name__ == "__main__":
    main()
