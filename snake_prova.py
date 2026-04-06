import os
import sys
import math
import random

os.environ["WAYLAND_DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "x11"

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# --- Configurações da janela e grade ---
LARGURA = 800
ALTURA = 800
TAMANHO_CELULA = 20
COLUNAS = LARGURA // TAMANHO_CELULA   # 25
LINHAS  = ALTURA  // TAMANHO_CELULA   # 25
VELOCIDADE_MS = 120  # intervalo entre frames (ms)

# --- Estado do jogo ---
cobra = []          # lista de (col, lin) — cabeça na posição 0
direcao = (1, 0)    # (dcol, dlin)
prox_direcao = (1, 0)
comida = (0, 0)
pontuacao = 0
estado = 'AGUARDANDO'  # 'AGUARDANDO', 'JOGANDO', 'GAME_OVER', 'VITORIA'


HUD_LINHAS = math.ceil(28 / TAMANHO_CELULA)  # linhas cobertas pelo HUD no topo

def nova_comida():
    """Gera posição aleatória para a comida, fora do corpo da cobra e do HUD.
    Retorna None se não houver espaço disponível."""
    livres = [
        (c, l)
        for c in range(COLUNAS)
        for l in range(LINHAS - HUD_LINHAS)
        if (c, l) not in cobra
    ]
    if not livres:
        return None
    return random.choice(livres)


def inicializar_jogo():
    global cobra, direcao, prox_direcao, comida, pontuacao, estado
    cx, cy = COLUNAS // 2, LINHAS // 2
    cobra = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
    direcao = (1, 0)
    prox_direcao = (1, 0)
    comida = nova_comida()
    pontuacao = 0
    estado = 'AGUARDANDO'


# --- Funções de desenho ---

def celula_para_pixel(col, lin):
    """Converte coordenada de grade para pixel (canto inferior esquerdo da célula)."""
    return col * TAMANHO_CELULA, lin * TAMANHO_CELULA


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


def desenhar_circulo(cx, cy, r, segmentos=20):
    glBegin(GL_POLYGON)
    for i in range(segmentos):
        angulo = 2 * math.pi * i / segmentos
        glVertex2f(cx + r * math.cos(angulo), cy + r * math.sin(angulo))
    glEnd()


def desenhar_cobra():
    tamanho = len(cobra)
    for i, (col, lin) in enumerate(cobra):
        px, py = celula_para_pixel(col, lin)
        margem = 2
        tam = TAMANHO_CELULA - margem * 2

        if i == 0:
            # Cabeça: verde vibrante
            glColor3f(0.15, 0.85, 0.15)
            desenhar_retangulo(px + margem, py + margem, tam, tam)

            # Olhos brancos
            glColor3f(1.0, 1.0, 1.0)
            cx_cel = px + TAMANHO_CELULA / 2
            cy_cel = py + TAMANHO_CELULA / 2
            dc, dl = direcao
            ox = dc * tam * 0.15
            oy = dl * tam * 0.15
            perp_x = -dl * tam * 0.2
            perp_y =  dc * tam * 0.2
            desenhar_circulo(cx_cel + ox + perp_x, cy_cel + oy + perp_y, 2.8)
            desenhar_circulo(cx_cel + ox - perp_x, cy_cel + oy - perp_y, 2.8)

            # Pupilas pretas
            glColor3f(0.0, 0.0, 0.0)
            desenhar_circulo(cx_cel + ox + perp_x, cy_cel + oy + perp_y, 1.4)
            desenhar_circulo(cx_cel + ox - perp_x, cy_cel + oy - perp_y, 1.4)
        else:
            # Corpo: gradiente de verde claro a verde escuro
            t = i / max(tamanho - 1, 1)
            g = 0.75 - 0.3 * t
            glColor3f(0.05, g, 0.05)
            desenhar_retangulo(px + margem, py + margem, tam, tam)

        # Borda mais escura para destacar os segmentos
        glColor3f(0.0, 0.25, 0.0)
        desenhar_retangulo_borda(px + margem, py + margem, tam, tam)


def desenhar_comida():
    col, lin = comida
    px, py = celula_para_pixel(col, lin)
    cx_cel = px + TAMANHO_CELULA / 2
    cy_cel = py + TAMANHO_CELULA / 2
    r = TAMANHO_CELULA / 2 - 1  # maior que antes

    # Halo brilhante ao redor
    glColor3f(0.5, 0.0, 0.0)
    desenhar_circulo(cx_cel, cy_cel, r + 2, segmentos=24)

    # Maçã vermelha
    glColor3f(0.95, 0.15, 0.15)
    desenhar_circulo(cx_cel, cy_cel, r, segmentos=24)

    # Brilho
    glColor3f(1.0, 0.6, 0.6)
    desenhar_circulo(cx_cel - r * 0.3, cy_cel + r * 0.35, r * 0.3)

    # Cabo
    glColor3f(0.3, 0.6, 0.1)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(cx_cel + 1, cy_cel + r)
    glVertex2f(cx_cel + 4, cy_cel + r + 5)
    glEnd()
    glLineWidth(1.0)


def desenhar_grade():
    # Linhas da grade bem sutis
    glColor3f(0.10, 0.10, 0.10)
    glBegin(GL_LINES)
    for c in range(COLUNAS + 1):
        x = c * TAMANHO_CELULA
        glVertex2f(x, 0)
        glVertex2f(x, ALTURA)
    for l in range(LINHAS + 1):
        y = l * TAMANHO_CELULA
        glVertex2f(0, y)
        glVertex2f(LARGURA, y)
    glEnd()

    # Borda da área de jogo
    glColor3f(0.2, 0.5, 0.2)
    glLineWidth(2.0)
    desenhar_retangulo_borda(0, 0, LARGURA, ALTURA)
    glLineWidth(1.0)


def desenhar_texto(x, y, texto, escala=1.0):
    glPushMatrix()
    glTranslatef(x, y, 0)
    glScalef(escala * 0.12, escala * 0.12, 1.0)
    for c in texto:
        glutStrokeCharacter(GLUT_STROKE_ROMAN, ord(c))
    glPopMatrix()


def desenhar_hud():
    # Fundo da barra do HUD
    glColor3f(0.05, 0.12, 0.05)
    desenhar_retangulo(0, ALTURA - 28, LARGURA, 28)

    # Linha separadora
    glColor3f(0.2, 0.5, 0.2)
    glLineWidth(1.5)
    glBegin(GL_LINES)
    glVertex2f(0, ALTURA - 28)
    glVertex2f(LARGURA, ALTURA - 28)
    glEnd()
    glLineWidth(1.0)

    # Pontuação
    glColor3f(0.3, 1.0, 0.3)
    desenhar_texto(8, ALTURA - 22, f"Pontos: {pontuacao}", escala=1.0)

    # Tamanho da cobra
    glColor3f(0.7, 0.9, 0.7)
    desenhar_texto(195, ALTURA - 22, f"Tamanho: {len(cobra)}", escala=0.9)


def desenhar_tela_final(titulo, cor_titulo):
    # Painel semitransparente
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.0, 0.0, 0.0, 0.7)
    desenhar_retangulo(80, 160, 340, 180)
    glDisable(GL_BLEND)

    # Título
    glColor3f(*cor_titulo)
    desenhar_texto(110, 290, titulo, escala=1.4)

    # Pontuação final
    glColor3f(1.0, 1.0, 1.0)
    desenhar_texto(145, 250, f"Pontos: {pontuacao}", escala=1.0)

    # Instrução de reinício
    glColor3f(0.7, 0.7, 0.7)
    desenhar_texto(120, 210, "Pressione R para reiniciar", escala=0.75)
    desenhar_texto(148, 185, "Pressione Q para sair", escala=0.75)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    # Fundo escuro
    glColor3f(0.08, 0.08, 0.08)
    desenhar_retangulo(0, 0, LARGURA, ALTURA)

    desenhar_grade()
    desenhar_comida()
    desenhar_cobra()
    desenhar_hud()

    if estado == 'AGUARDANDO':
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.0, 0.0, 0.0, 0.75)
        desenhar_retangulo(80, 195, 340, 110)
        glDisable(GL_BLEND)
        glColor3f(0.3, 1.0, 0.3)
        desenhar_texto(115, 275, "Jogo da Cobrinha", escala=1.3)
        glColor3f(0.9, 0.9, 0.2)
        desenhar_texto(105, 235, "Pressione uma tecla!", escala=1.0)
        glColor3f(0.5, 0.5, 0.5)
        desenhar_texto(128, 210, "WASD ou setas para mover", escala=0.7)
    elif estado == 'GAME_OVER':
        desenhar_tela_final("GAME OVER", (1.0, 0.2, 0.2))
    elif estado == 'VITORIA':
        desenhar_tela_final("VOCE VENCEU!", (0.2, 1.0, 0.4))

    glFlush()


# --- Lógica de atualização ---

def atualizar(valor=0):
    global cobra, direcao, comida, pontuacao, estado

    if estado != 'JOGANDO':
        return

    direcao = prox_direcao
    dc, dl = direcao
    cab_col, cab_lin = cobra[0]
    nova_cab = (cab_col + dc, cab_lin + dl)

    # Colisão com parede
    if not (0 <= nova_cab[0] < COLUNAS and 0 <= nova_cab[1] < LINHAS):
        estado = 'GAME_OVER'
        glutPostRedisplay()
        return

    # Colisão com o próprio corpo
    if nova_cab in cobra:
        estado = 'GAME_OVER'
        glutPostRedisplay()
        return

    cobra.insert(0, nova_cab)

    if nova_cab == comida:
        pontuacao += 10
        nova = nova_comida()
        if nova is None:
            estado = 'VITORIA'
            glutPostRedisplay()
            return
        comida = nova
    else:
        cobra.pop()

    glutPostRedisplay()
    glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Teclado ---

def teclado(tecla, x, y):
    global prox_direcao, estado

    if isinstance(tecla, bytes):
        tecla = tecla.decode('utf-8', errors='ignore').lower()

    if tecla == 'r':
        inicializar_jogo()
        glutPostRedisplay()
        return

    if tecla in ('q', '\x1b'):  # Q ou Esc
        os._exit(0)

    if estado not in ('JOGANDO', 'AGUARDANDO'):
        return

    dc, dl = direcao
    if tecla == 'w' and dl != -1:
        prox_direcao = (0, 1)
    elif tecla == 's' and dl != 1:
        prox_direcao = (0, -1)
    elif tecla == 'a' and dc != 1:
        prox_direcao = (-1, 0)
    elif tecla == 'd' and dc != -1:
        prox_direcao = (1, 0)
    else:
        return

    if estado == 'AGUARDANDO':
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


def teclado_especial(tecla, x, y):
    global prox_direcao, estado

    if estado not in ('JOGANDO', 'AGUARDANDO'):
        return

    dc, dl = direcao
    if tecla == GLUT_KEY_UP    and dl != -1:
        prox_direcao = (0, 1)
    elif tecla == GLUT_KEY_DOWN  and dl != 1:
        prox_direcao = (0, -1)
    elif tecla == GLUT_KEY_LEFT  and dc != 1:
        prox_direcao = (-1, 0)
    elif tecla == GLUT_KEY_RIGHT and dc != -1:
        prox_direcao = (1, 0)
    else:
        return

    if estado == 'AGUARDANDO':
        estado = 'JOGANDO'
        glutTimerFunc(VELOCIDADE_MS, atualizar, 0)


# --- Inicialização OpenGL ---

def inicializar_opengl():
    glClearColor(0.08, 0.08, 0.08, 1.0)
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
    glutCreateWindow(b"Jogo da Cobrinha - Computacao Grafica")

    inicializar_opengl()

    glutDisplayFunc(display)
    glutKeyboardFunc(teclado)
    glutSpecialFunc(teclado_especial)
    # O timer só inicia quando o usuário pressionar a primeira tecla

    glutMainLoop()


if __name__ == "__main__":
    main()
