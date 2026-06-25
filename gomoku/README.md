# Gomoku next-move solver

Pure-Python five-in-a-row engine. Give it a board + whose turn it is, and it
returns the strongest next move (alpha-beta search + pattern evaluation, with
immediate win / block detection).

## Usage

```bash
cd gomoku
python3 solve.py --player black board.txt
# or pipe a board in:
cat board.txt | python3 solve.py --player white --depth 4
```

### Board format

One row per line. Cells (whitespace optional):

| symbol            | meaning        |
|-------------------|----------------|
| `.` `_` `+`       | empty          |
| `X` `B` `1` `*`   | black (player 1) |
| `O` `W` `2`       | white (player 2) |

Example:

```
. . . . .
. X X X .
. . . . .
```

### Output

- The board, with the recommended move marked `@`
- The move as `row N, col L` (1-indexed, like a real board) and 0-indexed `(r,c)`
- Why it was chosen: `win` / `block` / `search`

## Files
- `engine.py` — board logic, evaluation, alpha-beta search
- `solve.py`  — CLI: parse a text board, print the best move

## Typical workflow (from a photo)
1. Read the photographed board into the text format above.
2. Run `solve.py` with the side to move.
3. Play the `@` square.
