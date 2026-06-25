"""
Gomoku (Five-in-a-Row) engine.

Pure-Python, no third-party deps. Given a board state and the player to move,
it returns the strongest next move using:
  - immediate win detection
  - immediate block of opponent win
  - pattern-based static evaluation (live/blocked four, live three, etc.)
  - alpha-beta search with iterative deepening and move ordering

Rules assumed: standard casual gomoku, any line of 5+ identical stones wins,
no forbidden (renju) moves. Board is square (default 15x15).

Cell encoding: 0 = empty, 1 = player-1 (black), 2 = player-2 (white).
"""

from functools import lru_cache

EMPTY, BLACK, WHITE = 0, 1, 2
WIN_SCORE = 10_000_000

# Pattern scores, evaluated on a line string where:
#   '1' = current player's stone, '2' = opponent, '0' = empty.
# Order matters: longer / stronger patterns first.
PATTERNS = [
    ("11111", 10_000_000),   # five (win)
    ("011110", 500_000),     # live four
    ("11110", 50_000),       # four (one side blocked)
    ("01111", 50_000),
    ("11011", 50_000),       # split four
    ("10111", 50_000),
    ("11101", 50_000),
    ("011100", 8_000),       # live three
    ("001110", 8_000),
    ("011010", 7_000),       # broken live three
    ("010110", 7_000),
    ("11100", 1_000),        # three (blocked)
    ("00111", 1_000),
    ("11010", 1_000),
    ("01011", 1_000),
    ("10110", 1_000),
    ("01101", 1_000),
    ("001100", 600),         # live two
    ("011000", 300),
    ("000110", 300),
    ("010100", 300),
    ("001010", 300),
]


def other(player):
    return WHITE if player == BLACK else BLACK


def in_bounds(board, r, c):
    n = len(board)
    return 0 <= r < n and 0 <= c < n


DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]


def is_win(board, r, c, player):
    """Did placing `player` at (r,c) complete 5+ in a row?"""
    n = len(board)
    for dr, dc in DIRECTIONS:
        count = 1
        for sign in (1, -1):
            rr, cc = r + dr * sign, c + dc * sign
            while 0 <= rr < n and 0 <= cc < n and board[rr][cc] == player:
                count += 1
                rr += dr * sign
                cc += dc * sign
        if count >= 5:
            return True
    return False


def line_strings(board, r, c, player):
    """Return the 4 line-windows through (r,c) as perspective strings."""
    n = len(board)
    opp = other(player)
    out = []
    for dr, dc in DIRECTIONS:
        s = []
        for k in range(-5, 6):
            rr, cc = r + dr * k, c + dc * k
            if not (0 <= rr < n and 0 <= cc < n):
                s.append("2")  # off-board acts like a block
            elif board[rr][cc] == player:
                s.append("1")
            elif board[rr][cc] == opp:
                s.append("2")
            else:
                s.append("0")
        out.append("".join(s))
    return out


def point_score(board, r, c, player):
    """Heuristic value of placing `player` at empty (r,c)."""
    board[r][c] = player
    total = 0
    for line in line_strings(board, r, c, player):
        for pat, sc in PATTERNS:
            if pat in line:
                total += sc
                break  # strongest pattern per line only
    board[r][c] = EMPTY
    return total


def get_candidates(board, radius=2):
    """Empty cells within `radius` of any stone. If empty board, center."""
    n = len(board)
    stones = [(r, c) for r in range(n) for c in range(n) if board[r][c] != EMPTY]
    if not stones:
        return [(n // 2, n // 2)]
    cands = set()
    for (r, c) in stones:
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < n and 0 <= cc < n and board[rr][cc] == EMPTY:
                    cands.add((rr, cc))
    return list(cands)


def evaluate(board, player):
    """Static eval of whole board from `player`'s perspective."""
    opp = other(player)
    my = _side_score(board, player)
    op = _side_score(board, opp)
    return my - int(op * 1.1)  # slight defensive bias


def _side_score(board, player):
    """Sum pattern scores over all lines for one side (counts each line once)."""
    n = len(board)
    opp = other(player)

    def cell(r, c):
        if not (0 <= r < n and 0 <= c < n):
            return "2"
        v = board[r][c]
        return "1" if v == player else ("2" if v == opp else "0")

    total = 0
    seen_patterns = PATTERNS
    # Iterate every line in 4 directions exactly once.
    lines = []
    # rows
    for r in range(n):
        lines.append("".join(cell(r, c) for c in range(n)))
    # cols
    for c in range(n):
        lines.append("".join(cell(r, c) for r in range(n)))
    # diagonals '\'
    for start in range(-(n - 1), n):
        diag = []
        for r in range(n):
            c = r - start
            if 0 <= c < n:
                diag.append(cell(r, c))
        if len(diag) >= 5:
            lines.append("".join(diag))
    # diagonals '/'
    for start in range(0, 2 * n - 1):
        diag = []
        for r in range(n):
            c = start - r
            if 0 <= c < n:
                diag.append(cell(r, c))
        if len(diag) >= 5:
            lines.append("".join(diag))

    for line in lines:
        for pat, sc in seen_patterns:
            cnt = line.count(pat)
            if cnt:
                total += sc * cnt
    return total


def find_immediate(board, player):
    """Return a winning move for `player` if one exists, else None."""
    for (r, c) in get_candidates(board, radius=1):
        if board[r][c] == EMPTY and is_win_at(board, r, c, player):
            return (r, c)
    return None


def is_win_at(board, r, c, player):
    board[r][c] = player
    w = is_win(board, r, c, player)
    board[r][c] = EMPTY
    return w


def alphabeta(board, depth, alpha, beta, player, root_player):
    maximizing = (player == root_player)
    # Terminal / leaf
    if depth == 0:
        return evaluate(board, root_player), None

    cands = get_candidates(board)
    # Move ordering by quick point score (offense for mover).
    cands.sort(key=lambda m: point_score(board, m[0], m[1], player), reverse=True)
    cands = cands[:14]  # branching cap for speed

    best_move = cands[0] if cands else None

    if maximizing:
        value = -float("inf")
        for (r, c) in cands:
            board[r][c] = player
            if is_win(board, r, c, player):
                board[r][c] = EMPTY
                return WIN_SCORE + depth, (r, c)
            score, _ = alphabeta(board, depth - 1, alpha, beta, other(player), root_player)
            board[r][c] = EMPTY
            if score > value:
                value, best_move = score, (r, c)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = float("inf")
        for (r, c) in cands:
            board[r][c] = player
            if is_win(board, r, c, player):
                board[r][c] = EMPTY
                return -(WIN_SCORE + depth), (r, c)
            score, _ = alphabeta(board, depth - 1, alpha, beta, other(player), root_player)
            board[r][c] = EMPTY
            if score < value:
                value, best_move = score, (r, c)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, best_move


def best_move(board, player, depth=4):
    """Top-level move selection."""
    # 1) Win now?
    win = find_immediate(board, player)
    if win:
        return win, "win", WIN_SCORE
    # 2) Block opponent's immediate win.
    block = find_immediate(board, other(player))
    if block:
        return block, "block", WIN_SCORE // 2
    # 3) Search.
    score, move = alphabeta(board, depth, -float("inf"), float("inf"), player, player)
    if move is None:
        # fallback: best static point
        cands = get_candidates(board)
        move = max(cands, key=lambda m: point_score(board, m[0], m[1], player))
        score = point_score(board, move[0], move[1], player)
    return move, "search", score
