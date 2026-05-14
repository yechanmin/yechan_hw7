"""
체스 게임 (Pygame)
실행 방법:
    pip install pygame
    python chess.py
"""

import pygame
import sys
from copy import deepcopy

# ──────────────────────────────────────────
# 상수
# ──────────────────────────────────────────
WIDTH, HEIGHT = 720, 720
ROWS, COLS = 8, 8
SQ = WIDTH // COLS          # 칸 크기 = 90

# 색상
LIGHT   = (240, 217, 181)
DARK    = (181, 136,  99)
HL_SEL  = (106, 176,  76, 180)   # 선택된 칸 (green, alpha)
HL_MOV  = (106, 176,  76, 100)   # 이동 가능 칸
HL_CHK  = (220,  50,  50, 160)   # 체크
BG_SIDE = (30,  30,  30)
TEXT_W  = (255, 255, 255)
TEXT_B  = ( 30,  30,  30)
PROMO_BG= ( 50,  50,  50, 220)

PIECES = ['K','Q','R','B','N','P']   # King Queen Rook Bishop Knight Pawn

# ──────────────────────────────────────────
# 기물 유니코드 (폰트 렌더링용)
# ──────────────────────────────────────────
UNICODE = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟',
}

# ──────────────────────────────────────────
# 보드 초기 상태
# ──────────────────────────────────────────
def init_board():
    b = [[None]*8 for _ in range(8)]
    order = ['R','N','B','Q','K','B','N','R']
    for c in range(8):
        b[0][c] = ('b', order[c])
        b[7][c] = ('w', order[c])
        b[1][c] = ('b', 'P')
        b[6][c] = ('w', 'P')
    return b

# ──────────────────────────────────────────
# 이동 생성 (pseudo-legal)
# ──────────────────────────────────────────
def raw_moves(board, r, c, state):
    """state = {turn, en_passant, castling}"""
    piece = board[r][c]
    if piece is None:
        return []
    color, kind = piece
    moves = []

    def in_board(rr, cc):
        return 0 <= rr < 8 and 0 <= cc < 8

    def enemy(rr, cc):
        return board[rr][cc] is not None and board[rr][cc][0] != color

    def empty(rr, cc):
        return board[rr][cc] is None

    def slide(dirs):
        for dr, dc in dirs:
            rr, cc = r+dr, c+dc
            while in_board(rr, cc):
                if empty(rr, cc):
                    moves.append((rr, cc))
                elif enemy(rr, cc):
                    moves.append((rr, cc))
                    break
                else:
                    break
                rr += dr; cc += dc

    if kind == 'P':
        d = -1 if color == 'w' else 1
        start_r = 6 if color == 'w' else 1
        if in_board(r+d, c) and empty(r+d, c):
            moves.append((r+d, c))
            if r == start_r and empty(r+2*d, c):
                moves.append((r+2*d, c))
        for dc in [-1, 1]:
            if in_board(r+d, c+dc):
                if enemy(r+d, c+dc):
                    moves.append((r+d, c+dc))
                # 앙파상
                ep = state.get('en_passant')
                if ep and (r+d, c+dc) == ep:
                    moves.append((r+d, c+dc))

    elif kind == 'N':
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            rr, cc = r+dr, c+dc
            if in_board(rr, cc) and (empty(rr,cc) or enemy(rr,cc)):
                moves.append((rr, cc))

    elif kind == 'B':
        slide([(-1,-1),(-1,1),(1,-1),(1,1)])

    elif kind == 'R':
        slide([(-1,0),(1,0),(0,-1),(0,1)])

    elif kind == 'Q':
        slide([(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])

    elif kind == 'K':
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                rr, cc = r+dr, c+dc
                if in_board(rr, cc) and (empty(rr,cc) or enemy(rr,cc)):
                    moves.append((rr, cc))
        # 캐슬링
        cast = state.get('castling', {})
        back_r = 7 if color=='w' else 0
        if r == back_r and c == 4:
            # 킹사이드
            if cast.get(color+'K') and empty(back_r,5) and empty(back_r,6):
                moves.append((back_r, 6))
            # 퀸사이드
            if cast.get(color+'Q') and empty(back_r,3) and empty(back_r,2) and empty(back_r,1):
                moves.append((back_r, 2))

    return moves

# ──────────────────────────────────────────
# 체크 감지
# ──────────────────────────────────────────
def king_pos(board, color):
    for r in range(8):
        for c in range(8):
            if board[r][c] == (color, 'K'):
                return r, c
    return None

def is_attacked(board, r, c, by_color, state):
    """(r,c) 칸이 by_color에게 공격받는지"""
    dummy_state = {'turn': by_color, 'en_passant': None, 'castling': {}}
    for rr in range(8):
        for cc in range(8):
            if board[rr][cc] and board[rr][cc][0] == by_color:
                if (r, c) in raw_moves(board, rr, cc, dummy_state):
                    return True
    return False

def in_check(board, color, state):
    kp = king_pos(board, color)
    if kp is None:
        return False
    opp = 'b' if color == 'w' else 'w'
    return is_attacked(board, kp[0], kp[1], opp, state)

# ──────────────────────────────────────────
# 이동 적용 (보드 복사본 반환)
# ──────────────────────────────────────────
def apply_move(board, fr, fc, tr, tc, state, promo='Q'):
    b = deepcopy(board)
    piece = b[fr][fc]
    color, kind = piece
    opp = 'b' if color=='w' else 'w'
    new_state = deepcopy(state)
    new_state['en_passant'] = None

    # 앙파상 캡처
    ep = state.get('en_passant')
    if kind == 'P' and ep and (tr, tc) == ep:
        ep_cap_r = fr   # 잡히는 폰의 행
        b[ep_cap_r][tc] = None

    # 캐슬링 이동
    back_r = 7 if color=='w' else 0
    if kind == 'K' and abs(tc - fc) == 2:
        if tc == 6:   # 킹사이드
            b[back_r][5] = b[back_r][7]
            b[back_r][7] = None
        elif tc == 2: # 퀸사이드
            b[back_r][3] = b[back_r][0]
            b[back_r][0] = None

    b[tr][tc] = piece
    b[fr][fc] = None

    # 프로모션
    promo_r = 0 if color=='w' else 7
    if kind == 'P' and tr == promo_r:
        b[tr][tc] = (color, promo)

    # 앙파상 플래그
    if kind == 'P' and abs(tr - fr) == 2:
        new_state['en_passant'] = ((fr+tr)//2, tc)

    # 캐슬링 권리 갱신
    cast = new_state.setdefault('castling', {})
    if kind == 'K':
        cast[color+'K'] = False
        cast[color+'Q'] = False
    if kind == 'R':
        if fc == 0: cast[color+'Q'] = False
        if fc == 7: cast[color+'K'] = False

    new_state['turn'] = opp
    return b, new_state

# ──────────────────────────────────────────
# 합법 이동 (체크 거르기)
# ──────────────────────────────────────────
def legal_moves(board, r, c, state):
    color = board[r][c][0] if board[r][c] else None
    if color is None or color != state['turn']:
        return []
    moves = []
    for tr, tc in raw_moves(board, r, c, state):
        # 캐슬링 통과 칸 공격 여부 확인
        piece_kind = board[r][c][1]
        back_r = 7 if color=='w' else 0
        if piece_kind == 'K' and abs(tc - c) == 2:
            mid_c = (c + tc) // 2
            opp = 'b' if color=='w' else 'w'
            if is_attacked(board, r, c, opp, state): continue
            if is_attacked(board, r, mid_c, opp, state): continue
        nb, ns = apply_move(board, r, c, tr, tc, state)
        if not in_check(nb, color, ns):
            moves.append((tr, tc))
    return moves

def all_legal_moves(board, color, state):
    result = []
    for r in range(8):
        for c in range(8):
            if board[r][c] and board[r][c][0] == color:
                for m in legal_moves(board, r, c, state):
                    result.append((r, c, m[0], m[1]))
    return result

# ──────────────────────────────────────────
# Pygame 렌더링
# ──────────────────────────────────────────
def draw_board(screen, sel, highlights, check_king, flip):
    for r in range(8):
        for c in range(8):
            dr = 7-r if flip else r
            dc = c
            color = LIGHT if (r+c)%2==0 else DARK
            pygame.draw.rect(screen, color, (dc*SQ, dr*SQ, SQ, SQ))

    # 체크 킹 하이라이트
    if check_king:
        kr, kc = check_king
        dr = 7-kr if flip else kr
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        s.fill(HL_CHK)
        screen.blit(s, (kc*SQ, dr*SQ))

    # 선택 및 이동 가능 하이라이트
    if sel:
        sr, sc = sel
        dr = 7-sr if flip else sr
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        s.fill(HL_SEL)
        screen.blit(s, (sc*SQ, dr*SQ))

    for hr, hc in highlights:
        dr = 7-hr if flip else hr
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        s.fill(HL_MOV)
        screen.blit(s, (hc*SQ, dr*SQ))
        pygame.draw.circle(screen, (50, 130, 50),
                           (hc*SQ + SQ//2, dr*SQ + SQ//2), SQ//8)

def draw_pieces(screen, board, piece_font, flip):
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p is None: continue
            color, kind = p
            key = color + kind
            glyph = UNICODE[key]
            dr = 7-r if flip else r

            # 그림자
            shadow = piece_font.render(glyph, True, (0,0,0,80))
            screen.blit(shadow, (c*SQ + SQ//2 - shadow.get_width()//2 + 2,
                                  dr*SQ + SQ//2 - shadow.get_height()//2 + 2))
            # 기물
            txt_color = (255,255,255) if color=='w' else (20,20,20)
            surf = piece_font.render(glyph, True, txt_color)
            screen.blit(surf, (c*SQ + SQ//2 - surf.get_width()//2,
                                dr*SQ + SQ//2 - surf.get_height()//2))

def draw_coords(screen, coord_font, flip):
    files = 'abcdefgh'
    ranks = '87654321' if not flip else '12345678'
    for i in range(8):
        # 파일 (a-h)
        col = DARK if i%2==0 else LIGHT
        s = coord_font.render(files[i], True, col)
        screen.blit(s, (i*SQ + 4, HEIGHT - 18))
        # 랭크 (1-8)
        col = DARK if i%2==1 else LIGHT
        s = coord_font.render(ranks[i], True, col)
        screen.blit(s, (4, i*SQ + 4))

def draw_promo_menu(screen, color, piece_font, small_font):
    """프로모션 선택 UI"""
    choices = ['Q','R','B','N']
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,150))
    screen.blit(overlay, (0,0))

    panel_w, panel_h = 380, 110
    px = (WIDTH - panel_w)//2
    py = (HEIGHT - panel_h)//2
    pygame.draw.rect(screen, (50,50,50), (px, py, panel_w, panel_h), border_radius=12)
    pygame.draw.rect(screen, (200,200,200), (px, py, panel_w, panel_h), 2, border_radius=12)

    title = small_font.render("프로모션 기물 선택", True, (220,220,220))
    screen.blit(title, (px + panel_w//2 - title.get_width()//2, py + 8))

    rects = []
    for i, kind in enumerate(choices):
        bx = px + 10 + i*92
        by = py + 45
        bw, bh = 82, 55
        pygame.draw.rect(screen, (80,80,80), (bx,by,bw,bh), border_radius=8)
        glyph = UNICODE[color+kind]
        gs = piece_font.render(glyph, True, (255,255,255) if color=='w' else (30,30,30))
        screen.blit(gs, (bx + bw//2 - gs.get_width()//2, by + bh//2 - gs.get_height()//2))
        rects.append((bx, by, bw, bh, kind))
    return rects

def draw_status(screen, board, state, fonts, game_over, winner, flip):
    small, = fonts
    turn = state['turn']
    opp  = 'b' if turn=='w' else 'w'

    if game_over:
        if winner == 'draw':
            msg = "스테일메이트 — 무승부!"
        else:
            who = "백" if winner=='w' else "흑"
            msg = f"{who} 승리!  🎉"
        # 중앙 배너
        overlay = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
        overlay.fill((0,0,0,180))
        screen.blit(overlay, (0, HEIGHT//2 - 30))
        s = small.render(msg, True, (255,220,50))
        screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT//2 - s.get_height()//2))
        hint = small.render("R: 재시작   Q: 종료", True, (200,200,200))
        screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 18))
        return

    # 체크 표시
    if in_check(board, turn, state):
        s = small.render("체크!", True, (255,80,80))
        screen.blit(s, (8, HEIGHT - 48))

    who = "백(White)" if turn=='w' else "흑(Black)"
    s = small.render(f"{who} 차례", True, (230,230,230))
    screen.blit(s, (WIDTH - s.get_width() - 8, HEIGHT - 48))

    hint = small.render("R:재시작  F:보드반전  Q:종료", True, (150,150,150))
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 22))

# ──────────────────────────────────────────
# 메인
# ──────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("체스 ♟")
    clock = pygame.time.Clock()

    # 폰트 — 유니코드 체스 기물 지원 폰트 탐색
    candidate_fonts = [
        "seguisym.ttf", "NotoSans-Regular.ttf", "FreeSans.ttf",
        "DejaVuSans.ttf", "Arial Unicode.ttf", "unifont.ttf"
    ]
    piece_font = None
    for fname in candidate_fonts:
        try:
            f = pygame.font.Font(fname, 64)
            # 테스트
            f.render('♔', True, (0,0,0))
            piece_font = f
            break
        except Exception:
            pass
    if piece_font is None:
        piece_font = pygame.font.SysFont("segoeuisymbol,notosans,freesans,dejavusans", 64)

    coord_font  = pygame.font.SysFont("consolas,monospace", 14)
    small_font  = pygame.font.SysFont("malgun gothic,nanum gothic,arial", 20)
    promo_small = pygame.font.SysFont("malgun gothic,nanum gothic,arial", 16)

    def new_game():
        board = init_board()
        state = {
            'turn': 'w',
            'en_passant': None,
            'castling': {'wK':True,'wQ':True,'bK':True,'bQ':True}
        }
        return board, state

    board, state = new_game()
    sel       = None       # 선택된 칸 (r,c)
    highlights= []         # 이동 가능 칸
    game_over = False
    winner    = None
    flip      = False      # 보드 반전
    promo_pending = None   # (fr,fc,tr,tc,color) 프로모션 대기
    promo_rects   = []

    running = True
    while running:
        clock.tick(60)
        screen.fill((30,30,30))

        # ── 체크 킹 위치
        turn = state['turn']
        check_king = None
        if not game_over and in_check(board, turn, state):
            check_king = king_pos(board, turn)

        # ── 그리기
        draw_board(screen, sel, highlights, check_king, flip)
        draw_pieces(screen, board, piece_font, flip)
        draw_coords(screen, coord_font, flip)
        draw_status(screen, board, state, [small_font], game_over, winner, flip)

        if promo_pending:
            promo_rects = draw_promo_menu(screen, promo_pending[4], piece_font, promo_small)

        pygame.display.flip()

        # ── 이벤트
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    board, state = new_game()
                    sel=None; highlights=[]; game_over=False; winner=None; promo_pending=None
                elif event.key == pygame.K_f:
                    flip = not flip

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # 프로모션 선택
                if promo_pending:
                    for bx,by,bw,bh,kind in promo_rects:
                        if bx<=mx<bx+bw and by<=my<by+bh:
                            fr,fc,tr,tc,color = promo_pending
                            board, state = apply_move(board, fr, fc, tr, tc, state, promo=kind)
                            promo_pending = None
                            # 게임 종료 체크
                            nt = state['turn']
                            if not all_legal_moves(board, nt, state):
                                game_over = True
                                winner = ('w' if nt=='b' else 'b') if in_check(board,nt,state) else 'draw'
                    continue

                if game_over:
                    continue

                # 클릭 → 보드 좌표
                cc = mx // SQ
                rr_raw = my // SQ
                rr = 7 - rr_raw if flip else rr_raw
                if not (0<=rr<8 and 0<=cc<8):
                    sel=None; highlights=[]; continue

                if sel is None:
                    # 기물 선택
                    if board[rr][cc] and board[rr][cc][0] == state['turn']:
                        sel = (rr, cc)
                        highlights = legal_moves(board, rr, cc, state)
                else:
                    if (rr, cc) in highlights:
                        fr, fc = sel
                        tr, tc = rr, cc
                        color  = board[fr][fc][0]
                        kind   = board[fr][fc][1]
                        # 프로모션?
                        promo_r = 0 if color=='w' else 7
                        if kind=='P' and tr==promo_r:
                            promo_pending = (fr,fc,tr,tc,color)
                            sel=None; highlights=[]
                        else:
                            board, state = apply_move(board, fr, fc, tr, tc, state)
                            sel=None; highlights=[]
                            # 게임 종료 체크
                            nt = state['turn']
                            if not all_legal_moves(board, nt, state):
                                game_over = True
                                winner = ('w' if nt=='b' else 'b') if in_check(board,nt,state) else 'draw'
                    elif board[rr][cc] and board[rr][cc][0] == state['turn']:
                        sel = (rr, cc)
                        highlights = legal_moves(board, rr, cc, state)
                    else:
                        sel=None; highlights=[]

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()