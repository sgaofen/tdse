"""
CLI: read a board from a text file (or stdin) and print the best move.

Board text format (one row per line):
  .  = empty
  X / B / 1 / *  = black  (player 1)
  O / W / 2      = white  (player 2)
Whitespace between cells is optional.

Usage:
  python3 solve.py --player black --depth 4 board.txt
  cat board.txt | python3 solve.py --player white

Output: 0-indexed (row, col), plus a 1-indexed human label and column letter.
"""

import sys
import argparse

from engine import best_move, BLACK, WHITE, EMPTY

CHAR_MAP = {
    ".": EMPTY, "_": EMPTY, "+": EMPTY, "-": EMPTY, "0": EMPTY,
    "x": BLACK, "X": BLACK, "b": BLACK, "B": BLACK, "1": BLACK, "*": BLACK, "#": BLACK,
    "o": WHITE, "O": WHITE, "w": WHITE, "W": WHITE, "2": WHITE,
}


def parse_board(text):
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        cells = []
        for ch in line:
            if ch.isspace():
                continue
            if ch in CHAR_MAP:
                cells.append(CHAR_MAP[ch])
        if cells:
            rows.append(cells)
    # pad to square / consistent width
    width = max(len(r) for r in rows)
    for r in rows:
        while len(r) < width:
            r.append(EMPTY)
    return rows


def col_letter(c):
    # A, B, ... skipping nothing; supports >26 with AA etc.
    s = ""
    c += 1
    while c > 0:
        c, rem = divmod(c - 1, 26)
        s = chr(65 + rem) + s
    return s


def render(board, move=None):
    n = len(board)
    sym = {EMPTY: ".", BLACK: "X", WHITE: "O"}
    lines = []
    header = "   " + " ".join(col_letter(c) for c in range(n))
    lines.append(header)
    for r in range(n):
        row = []
        for c in range(n):
            if move and (r, c) == move:
                row.append("@")  # recommended move
            else:
                row.append(sym[board[r][c]])
        lines.append(f"{r+1:2d} " + " ".join(row))
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", help="board text file; stdin if omitted")
    ap.add_argument("--player", default="black", help="black/white/1/2 — side to move")
    ap.add_argument("--depth", type=int, default=4)
    args = ap.parse_args()

    text = open(args.file).read() if args.file else sys.stdin.read()
    board = parse_board(text)

    p = args.player.lower()
    player = BLACK if p in ("black", "b", "x", "1") else WHITE

    move, reason, score = best_move(board, player, depth=args.depth)
    r, c = move

    print("Board (X=black, O=white):")
    print(render(board, move))
    print()
    side = "BLACK (X)" if player == BLACK else "WHITE (O)"
    print(f"Side to move : {side}")
    print(f"Best move    : row {r+1}, col {col_letter(c)}  "
          f"(0-indexed: r={r}, c={c})")
    print(f"Reason       : {reason}   score={score}")


if __name__ == "__main__":
    main()
