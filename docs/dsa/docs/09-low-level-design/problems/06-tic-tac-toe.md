# Design Tic-Tac-Toe

> The simplest LLD warm-up. Tests whether you can decompose a tiny system *cleanly* — and extend it.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design a Tic-Tac-Toe game. Two players alternate; first to align 3 wins. Detect win / draw / invalid moves. Then extend: N×N board with K-in-a-row, multiple players, AI opponent."*

A 20-30 minute LLD round. Often paired as a warm-up before a harder problem. Interviewer expects:

1. **Class decomposition** even for a "trivial" game.
2. **O(1) win detection** if asked (n=3 is fine to do O(n) but show you know).
3. **Extensibility** — N×N is the obvious extension.

---

## ❓ Clarifying questions

1. **Board size?** 3×3 fixed or N×N?
2. **Players?** Always 2 or arbitrary?
3. **Win condition?** 3-in-a-row, or K-in-a-row?
4. **Symbols?** X / O / Unicode emojis?
5. **AI?** Human vs human, or AI opponent?
6. **Persistence?** Save / load games?
7. **Win detection?** O(n) per move OK, or O(1) required?

**Default assumptions**:

- N×N board (default 3); K-in-a-row (default 3 for 3×3, K=N otherwise).
- Arbitrary number of players (2 default).
- O(1) win detection (counters per row/col/diag).

---

## 🏛️ Class design

### Enums + value objects

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class GameStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    WON         = "WON"
    DRAW        = "DRAW"


@dataclass(frozen=True)
class Move:
    row: int
    col: int


@dataclass
class Player:
    id: str
    name: str
    symbol: str               # "X", "O", "△", …
```

### Board with O(1) win check

The trick: maintain **per-row, per-column, per-diagonal counters** keyed by player. Each move increments four counters; if any reaches K, that player wins.

```python
class Board:
    def __init__(self, size: int, k_in_a_row: int):
        self.n = size
        self.k = k_in_a_row
        self.grid: list[list[Player | None]] = [[None] * size for _ in range(size)]
        # Per-line counters: line → player → consecutive count from that player
        # For N×N with K=N (no shifting), simple sums suffice. For K<N, we
        # need streak tracking per cell, but the simple-sum version is what
        # interviewers grade on. Document the limitation explicitly.
        self.row_counts: list[dict[Player, int]] = [{} for _ in range(size)]
        self.col_counts: list[dict[Player, int]] = [{} for _ in range(size)]
        self.diag_counts: dict[Player, int] = {}        # main diagonal
        self.anti_counts: dict[Player, int] = {}        # anti-diagonal
        self.moves_made = 0

    def is_valid(self, m: Move) -> bool:
        return (
            0 <= m.row < self.n
            and 0 <= m.col < self.n
            and self.grid[m.row][m.col] is None
        )

    def place(self, m: Move, p: Player) -> bool:
        """Returns True iff p just won."""
        self.grid[m.row][m.col] = p
        self.moves_made += 1

        rc = self.row_counts[m.row]
        cc = self.col_counts[m.col]
        rc[p] = rc.get(p, 0) + 1
        cc[p] = cc.get(p, 0) + 1
        won = rc[p] == self.n or cc[p] == self.n

        if m.row == m.col:
            self.diag_counts[p] = self.diag_counts.get(p, 0) + 1
            won = won or self.diag_counts[p] == self.n
        if m.row + m.col == self.n - 1:
            self.anti_counts[p] = self.anti_counts.get(p, 0) + 1
            won = won or self.anti_counts[p] == self.n

        return won

    def is_full(self) -> bool:
        return self.moves_made == self.n * self.n

    def render(self) -> str:
        rows = []
        for r in self.grid:
            rows.append(" | ".join(p.symbol if p else "." for p in r))
        return ("\n" + "-" * (4 * self.n - 3) + "\n").join(rows)
```

??? note "K-in-a-row vs full-line: a clarification"

    The above is **O(1) full-line** (K=N). For arbitrary K (say 5-in-a-row on a 19×19 Gomoku board), maintain *streak counters* per (cell, direction) — increment based on neighbouring same-symbol streak, not just total per row. Mention this trade-off.

### Game (Context for state + turn rotation)

```python
class TicTacToe:
    def __init__(self, players: list[Player], size: int = 3, k: int | None = None):
        if len(players) < 2:
            raise ValueError("need ≥2 players")
        self.players = players
        self.board = Board(size, k or size)
        self.turn = 0
        self.status = GameStatus.IN_PROGRESS
        self.winner: Player | None = None

    @property
    def current_player(self) -> Player:
        return self.players[self.turn % len(self.players)]

    def play(self, m: Move) -> GameStatus:
        if self.status != GameStatus.IN_PROGRESS:
            raise InvalidOperation("game already finished")
        if not self.board.is_valid(m):
            raise InvalidMove(m)

        p = self.current_player
        if self.board.place(m, p):
            self.status = GameStatus.WON
            self.winner = p
        elif self.board.is_full():
            self.status = GameStatus.DRAW
        else:
            self.turn += 1

        return self.status
```

### Bot (Strategy pattern, for AI opponent extension)

```python
class BotStrategy(ABC):
    @abstractmethod
    def pick(self, board: Board, me: Player) -> Move: ...


class RandomBot(BotStrategy):
    def pick(self, board, me):
        import random
        empty = [
            Move(r, c)
            for r in range(board.n) for c in range(board.n)
            if board.grid[r][c] is None
        ]
        return random.choice(empty)


class MinimaxBot(BotStrategy):
    """Optimal for 3×3 — runs in microseconds. Don't run on N≥5."""

    def pick(self, board, me):
        _, best_move = self._minimax(board, me, me, depth=0)
        return best_move

    def _minimax(self, board: Board, me: Player, current: Player, depth: int):
        # Trimmed for brevity; standard minimax with +1/-1/0 leaves
        # and recursive tree with alternating maximiser/minimiser.
        ...
```

---

## 🧪 Walkthrough

```python
alice = Player("a", "Alice", "X")
bob   = Player("b", "Bob",   "O")
g = TicTacToe([alice, bob])

g.play(Move(0, 0))            # X
g.play(Move(1, 1))            # O
g.play(Move(0, 1))            # X
g.play(Move(2, 2))            # O
g.play(Move(0, 2))            # X — wins on row 0
print(g.status, g.winner)     # GameStatus.WON, alice
print(g.board.render())
# X | X | X
# - - - - -
# . | O | .
# - - - - -
# . | . | O
```

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `Board` separate from `TicTacToe` | **SRP** — Board owns geometry, Game owns flow |
| Per-line counters | O(1) win detection trick |
| `BotStrategy` ABC | **Strategy** for swappable AI |
| `GameStatus` enum | Type-safe outcomes |
| `Move` is `frozen=True` | Hashable; can be dict-keyed for replay |
| Game accepts arbitrary players | Generalises to N-player misère / Othello |

---

## 🚀 Extensions

??? question "K-in-a-row on a 19×19 board (Gomoku)?"

    Replace per-line *totals* with per-cell *streak counters in 4 directions*. On placing at (r,c): for each of 8 neighbour directions, look up streak; new streak = neighbour's same-direction streak + 1. If any direction's streak ≥ K, win.

??? question "AI opponent?"

    See `MinimaxBot` above. Optimal for 3×3 in < 1ms. For larger boards, use **alpha-beta pruning** + iterative deepening + transposition table.

??? question "Multiplayer (≥3 players)?"

    Already supported — `players` list rotates. Win still triggers when one player aligns N. Adjust UI to colour-code players.

??? question "Persistent / online play?"

    Serialise `(grid, turn, status)` as JSON. Real-time sync via WebSocket. `move_id` for idempotency on retries.

??? question "Undo / redo?"

    Stack of `Move` records. Undo = pop last move, decrement counters (mirror of `place`). Memento pattern for full snapshots if state grows.

??? question "Detect impending wins (suggest blocks)?"

    Scan: for each empty cell, simulate placing opponent there; if it creates a line of K-1, that's a forced threat — flag it.

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–2   | Clarifying questions. |
| 2–5   | Class list: Board, Player, Move, Game. |
| 5–15  | Code: O(1) win detection, turn rotation. |
| 15–25 | Extension: pick AI or N×N or undo. |
| 25–30 | Q&A. |

---

## 🪤 Common mistakes

??? warning "Naive O(n²) win check after every move"

    Works for 3×3 but signals weak DS thinking. The interviewer wants O(n) per move at worst — and ideally O(1).

??? warning "`current_player` as a string `\"X\"` / `\"O\"`"

    Player should be a real object with id + symbol. Otherwise extension to N players is awkward.

??? warning "God class — game owns grid, render, input parsing, AI"

    Decompose. Board owns geometry. Game owns flow. Bot owns strategy. Renderer (if you have one) owns I/O.

??? warning "Forgetting draw detection"

    Many candidates only check WIN; a board fills up without a winner. Track `moves_made` and compare to `n²`.

??? warning "Mutating the board after game-over"

    Guard `play()` with status check. Otherwise tests that play one move past the win pass silently.

---

## ➡️ Where this connects

- [OOP fundamentals](../01-oop-fundamentals.md) — clean decomposition under pressure.
- [Design patterns](../03-design-patterns.md) — Strategy (Bot), Memento (undo).
- Other LLD: [Vending Machine](04-vending-machine.md), [Snake & Ladder](#) (coming).
