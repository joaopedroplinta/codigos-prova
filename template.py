from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

# ========== CONFIGURAÇÕES ==========
LARGURA, ALTURA = 600, 600
VELOCIDADE = 10

# ========== ESTADO DO JOGO ==========
jogador_x, jogador_y = LARGURA // 2, ALTURA // 2
pontuacao = 0
jogo_ativo = True

# ========== FUNÇÕES OBRIGATÓRIAS ==========
def inicializar():
    """Configuração inicial (projeção ortogonal)"""
    glClearColor(0, 0, 0, 1)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, LARGURA, 0, ALTURA)  # PROJEÇÃO ORTOGONAL

def desenhar():
    """Desenha todos os elementos"""
    glClear(GL_COLOR_BUFFER_BIT)
    
    # Desenhar jogador (ponto ou quadrado)
    glColor3f(0, 0, 1)  # CORES
    glPointSize(20)
    glBegin(GL_POINTS)  # PONTOS
    glVertex2f(jogador_x, jogador_y)
    glEnd()
    
    glFlush()

def teclado(tecla, x, y):
    """CONTROLE PELO TECLADO"""
    global jogador_x, jogador_y
    
    if tecla == b'a':
        jogador_x -= VELOCIDADE
    elif tecla == b'd':
        jogador_x += VELOCIDADE
    
    # Limites
    jogador_x = max(0, min(LARGURA, jogador_x))

def verificar_colisao():
    """LÓGICA DE COLISÃO (obrigatória)"""
    pass

def timer(valor):
    """Atualização do jogo"""
    verificar_colisao()
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

# ========== MAIN ==========
glutInit()
glutInitWindowSize(LARGURA, ALTURA)
glutCreateWindow(b'Meu Jogo')
inicializar()
glutDisplayFunc(desenhar)
glutKeyboardFunc(teclado)
glutTimerFunc(16, timer, 0)
glutMainLoop()
