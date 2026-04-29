# Game Theory & Alpha-Beta

> The chapter where every "two players play optimally — who wins?" problem collapses to one of two universal frameworks. **Sprague-Grundy** turns any **impartial combinatorial game** (both players have the same moves; no chance; no hidden info) into Nim with a single XOR — `g(state) = mex({g(next) : next})`, and the position is losing iff `g = 0`. **Minimax with alpha-beta** does the rest: explore the game tree, propagate values up by min/max alternation, and prune branches whose result can't change the answer. Add iterative deepening, transposition tables, and move ordering, and you have the algorithmic core of every chess engine from Stockfish to AlphaZero's MCTS-augmented variant. Net: this chapter is "the answer to every game-theory interview question," and the bonus is you'll understand why classic chess AI works.

<span class="phase-status phase-done">Phase 7 — Ultra-Advanced topic 7 of 7 (chapter complete)</span>

---

## 📖 What is "game theory" in algorithms?

In an algorithmic context, "game theory" usually means **two-player, zero-sum, perfect-information, no-chance** games. Examples: chess, Go, Nim, tic-tac-toe, every "Stone Game" LC problem. Both players see the full state, alternate moves, and one wins ⇔ the other loses.

These games split into two camps:

1. **Impartial games** — both players have the **same available moves** from any position. The only thing that distinguishes the players is who moves next. Examples: Nim, "take stones from a pile," "remove a coin and split or not." **The Sprague-Grundy theorem makes these isomorphic to Nim** via the XOR of Grundy numbers.

2. **Partisan games** — players have **different available moves**. Chess (white moves white pieces, black moves black pieces), Go, checkers. No clean SG reduction; you fall back to **minimax** with the game tree.

The mental model:

- **Impartial → SG number → Nim equivalent.** Compute `g(state) = mex(g(reachable))` recursively. The root position is **losing** for the player about to move iff `g(root) = 0`. For sums of independent games, XOR the Grundy values.
- **Partisan → game tree → minimax.** Recurse to a terminal or a depth limit, evaluate, propagate min/max. Alpha-beta prunes irrelevant branches. Transposition tables memoize. Iterative deepening lets you stop anytime with the best move so far.

The third pillar — **Zermelo's theorem (1913)** — says every finite, no-chance, perfect-info, deterministic, terminating game is *determined*: one player has a winning strategy or both can force a draw. The *algorithmic* question is finding that strategy efficiently.

!!! tip "The signal — when to reach for game theory"
    Reach for it when:

    - "Two players take turns, both play optimally, who wins / what's the score difference?"
    - "Stones / coins / cards in piles, last move wins (or loses)" → likely **Nim / SG**.
    - "Game on a graph or grid with limited depth" → **minimax + alpha-beta**.
    - "Find the first / last losing position" → **DP on states** with `f(s) = OR(NOT f(s'))`.
    - "Optimal play with depth-limited evaluation" → **iterative deepening + heuristic**.
    - "Multiple independent sub-games combined" → **XOR of Grundy values**.

    Don't reach for it when:

    - The game has chance (dice, hidden info) — switch to **expectiminimax** or **POMDP**.
    - There are more than 2 players — Nash equilibria are PPAD-hard in general.
    - State space is too large for tabulation — try **MCTS** (Monte Carlo Tree Search).

---

## 🧩 The four flavors

### Flavor 1: Sprague-Grundy & Nim

Compute the Grundy number `g(s) = mex({g(s') : s' reachable from s})` where `mex` is the minimum non-negative integer not in the set.

```python
from functools import lru_cache

def mex(seen: set[int]) -> int:
    g = 0
    while g in seen: g += 1
    return g

@lru_cache(maxsize=None)
def grundy(state: tuple) -> int:
    """Generic SG number for any impartial game with hashable state."""
    moves = next_states(state)                                        # game-specific
    if not moves:
        return 0                                                      # (1) terminal = losing for mover
    return mex({grundy(m) for m in moves})

def is_winning(initial: tuple) -> bool:
    return grundy(initial) != 0                                       # (2)
```

1. A terminal position (no moves available) has Grundy 0 — the current player can't move and loses (under normal play convention).
2. **The fundamental theorem:** in normal play, a position is winning for the player about to move iff `g(state) ≠ 0`.

**For sums of independent games** (e.g., multiple piles in Nim): `g(s₁ + s₂ + ... + s_k) = g(s₁) XOR g(s₂) XOR ... XOR g(s_k)`. The position is losing iff the XOR is 0.

```python
def nim_winner(piles: list[int]) -> str:
    """Classic Nim: remove any number from one pile. g(pile of n) = n."""
    return "first" if (xor := 0) ^ (xor := __import__("functools").reduce(lambda a, b: a ^ b, piles, 0)) else "second"
```

For Nim specifically, `g(pile of n) = n`. Whoever faces an XOR-zero state loses.

### Flavor 2: Minimax (recursive)

```python
def minimax(state, depth: int, maximizing: bool) -> int:
    if terminal(state) or depth == 0:
        return evaluate(state)                                        # (1)
    if maximizing:
        best = float("-inf")
        for child in next_states(state):
            best = max(best, minimax(child, depth - 1, False))
        return best
    else:
        best = float("inf")
        for child in next_states(state):
            best = min(best, minimax(child, depth - 1, True))
        return best
```

1. Static evaluation function `evaluate(state)` returns a heuristic score from the maximizer's perspective. For terminal states, return ±∞ for win/loss; for cutoff at `depth = 0`, use a heuristic (material balance in chess, etc.).

Time: `O(b^d)` where `b` is branching factor, `d` is depth. For chess, `b ≈ 35`, `d ≈ 6` gives `~10⁹` nodes — already at compute limit.

### Flavor 3: Alpha-Beta pruning

The optimisation that makes minimax practical. Maintain `α` (best so far for the maximizer) and `β` (best so far for the minimizer). Prune any subtree where the maximizer's lower bound exceeds the minimizer's upper bound.

```python
def alphabeta(state, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
    if terminal(state) or depth == 0:
        return evaluate(state)
    if maximizing:
        v = float("-inf")
        for child in next_states(state):
            v = max(v, alphabeta(child, depth - 1, alpha, beta, False))
            alpha = max(alpha, v)
            if alpha >= beta:                                         # (1) β-cutoff
                break
        return v
    else:
        v = float("inf")
        for child in next_states(state):
            v = min(v, alphabeta(child, depth - 1, alpha, beta, True))
            beta = min(beta, v)
            if alpha >= beta:                                         # (2) α-cutoff
                break
        return v
```

1. **β-cutoff:** if the maximizer has already found a move worth `≥ β`, the minimizer (parent) won't pick this branch — prune.
2. **α-cutoff:** dual case — minimizer found a move `≤ α` so the maximizer won't pick this branch.

**With perfect move ordering**, alpha-beta visits `O(b^(d/2))` nodes — the **square root** of plain minimax. That's why "search depth 12" is plausible only with alpha-beta + good ordering. With random ordering, the speedup is `O(b^(3d/4))` — still significant.

### Flavor 4: DP on game states

When the state space is small enough to tabulate, recursive minimax with memoization (`@lru_cache`) is often cleanest. This is the canonical LC pattern:

```python
@lru_cache(maxsize=None)
def stone_game(l: int, r: int, turn: int) -> int:
    """LC 486: turn ∈ {+1, -1}; return score difference (current_player − opponent)."""
    if l == r:
        return turn * piles[l]
    take_left = turn * piles[l] + stone_game(l + 1, r, -turn)
    take_right = turn * piles[r] + stone_game(l, r - 1, -turn)
    return turn * max(turn * take_left, turn * take_right)            # (1)
```

1. The trick — instead of two separate functions, encode "whose turn" via `turn = ±1` and **maximise** `turn × score`. Both players maximise their own score, which means maximising `turn × score_diff`. This collapses minimax into a single recursion.

For most LC game problems with `n ≤ 10⁴`, a 2D or 3D DP table beats explicit minimax.

---

## 🔍 Sub-pattern at-a-glance

| # | Pattern                          | Trigger                                          | Approach                              | Complexity                       |
|---|----------------------------------|--------------------------------------------------|---------------------------------------|----------------------------------|
| 1 | Pure Nim                         | k piles, take any from one pile                  | XOR of pile sizes                     | O(k)                             |
| 2 | Misère Nim                       | Last move loses (not wins)                       | Special-case for piles all = 1        | O(k)                             |
| 3 | Subtraction game                 | Take from {a₁, …, aₘ} per move                   | g(n) = mex of g(n − aᵢ); often periodic | O(n · m) precompute            |
| 4 | Sum of games                     | Multiple independent boards                      | XOR Grundy values                     | O(per-game)                      |
| 5 | Stone-game DP                    | LC: range/score game on array                    | `dp[l][r]` with turn parity            | O(n²)                            |
| 6 | Minimax with depth limit         | Game tree, eval function                          | Recursive min/max                     | O(b^d)                           |
| 7 | Alpha-beta pruning               | Same, but want speed                              | α/β bounds + pruning                  | O(b^(d/2)) with good ordering    |
| 8 | Iterative deepening + TT         | "Stop anytime" search                             | DFS at depths 1, 2, 3 ... + memo      | O(b^d) + cache hits              |
| 9 | MCTS (Monte Carlo Tree Search)   | Branching too high for minimax (Go, large board) | UCB1-guided random rollouts           | O(N · simulation_length)         |
| 10| Expectiminimax                   | Game with chance nodes (dice)                    | Add weighted-average level            | O((b · c)^d)                     |

---

## 📚 20 problems where game theory is the canonical answer

| #  | Source        | Problem                                              | Difficulty | Pattern                  | Key insight                                                            |
|----|---------------|------------------------------------------------------|------------|--------------------------|------------------------------------------------------------------------|
| 1  | LC 292        | Nim Game                                             | Easy       | Direct Nim               | Lose iff `n % 4 == 0`.                                                 |
| 2  | LC 877        | Stone Game                                           | Medium     | DP / parity argument     | First player always wins on even-length array; or 2D DP for the score.|
| 3  | LC 486        | Predict the Winner                                   | Medium     | Stone-game DP            | `dp[l][r]` = max score diff current player can achieve.                |
| 4  | LC 1140       | Stone Game II                                        | Medium     | Stone-game DP w/ M       | State = `(i, M)`; recursion picks 1..2M piles.                         |
| 5  | LC 1406       | Stone Game III                                       | Hard       | DP forward               | `dp[i]` = best score diff from position i; pick 1, 2, or 3.            |
| 6  | LC 1510       | Stone Game IV                                        | Hard       | DP win/lose              | `win[n] = ∃ k: ¬win[n − k²]`.                                          |
| 7  | LC 1690       | Stone Game VII                                       | Medium     | Stone-game DP            | Subtract-the-endpoint variant.                                         |
| 8  | LC 1872       | Stone Game VIII                                      | Hard       | DP suffix sum            | Reduce to "max suffix-sum delta from position i."                      |
| 9  | LC 464        | Can I Win                                            | Medium     | Bitmask DP on used set    | `dp[mask]`; n ≤ 20 fits the bitmask budget.                            |
| 10 | LC 913        | Cat and Mouse                                        | Hard       | BFS on (mouse, cat, turn)| Topological coloring of game graph; O(V³) states.                      |
| 11 | LC 1561       | Maximum Number of Coins You Can Get                  | Medium     | Sorting greedy           | Sort desc; you take every odd-indexed (0-based) of top 2/3.            |
| 12 | CSES 1730     | Stick Game                                           | Easy       | SG / subtraction game    | Compute `g(0..n)` with allowed moves; check `g(n) ≠ 0`.                |
| 13 | CSES 1729     | Nim Game I                                           | Easy       | XOR of piles             | First wins iff XOR ≠ 0.                                                |
| 14 | CSES 2207     | Nim Game II (Misère)                                 | Easy       | Misère adjustment        | Special case when all piles ≤ 1.                                       |
| 15 | LC 489        | Robot Room Cleaner (interactive)                     | Hard       | Game-flavoured DFS        | Not strictly game theory but uses similar reasoning over moves.        |
| 16 | LC 1908       | Game of Nim                                          | Medium     | Direct XOR               | Trivial application of Nim's theorem.                                  |
| 17 | Codeforces    | Mock Tournament (impartial games)                    | Hard       | SG-table precompute       | Compute g table up to N; XOR for sum of games.                         |
| 18 | Tic-tac-toe   | Optimal play                                         | Easy       | Minimax with depth ≤ 9   | Always draws with perfect play.                                        |
| 19 | Connect-4     | 7×6 board                                            | Hard       | Alpha-beta + bitboards   | Solved (first player wins with perfect play).                          |
| 20 | Chess engine  | Stockfish-class search                               | Industry   | All of the above         | iterative deepening + alpha-beta + TT + killer moves + null move + LMR + quiescence search. |

---

## 🔬 Deep-dive 1 — Why XOR is the right answer for Nim

**Nim:** k piles with sizes `n₁, …, n_k`. Each move: pick a pile and remove ≥ 1 stones. Last move wins.

**Theorem (Bouton, 1901):** the first player wins iff `n₁ XOR n₂ XOR … XOR n_k ≠ 0`.

**Why XOR works:**

Define a position to be a **P-position** (previous player wins, current player loses) iff XOR = 0. We show this set is closed correctly:

1. **From XOR = 0, every move leads to XOR ≠ 0.** If you remove from pile `i`, the new pile `n'_i < n_i`. The new XOR is `XOR ⊕ n_i ⊕ n'_i = 0 ⊕ n_i ⊕ n'_i ≠ 0` (since `n_i ≠ n'_i`).

2. **From XOR ≠ 0, there's a move to XOR = 0.** Let `S = XOR(n₁, …, n_k)`. The leftmost set bit of `S` is set in *some* pile `n_i` (else its XOR contribution would be 0). Compute `n'_i = n_i ⊕ S`. Then `n'_i < n_i` (because the leftmost bit of `S` flips a 1 in `n_i` to a 0 → strictly smaller). The new XOR is `S ⊕ n_i ⊕ n'_i = S ⊕ S = 0`. ✓

Together: a player at XOR ≠ 0 can always move to XOR = 0 (forcing opponent into the losing class), and a player at XOR = 0 must move to XOR ≠ 0 (giving opponent the winning move). Inductive base: terminal `(0, 0, …, 0)` has XOR = 0 — the player to move loses (no moves). ✓

**Sprague-Grundy generalises this**: every impartial game's Grundy number is the size of an "equivalent" Nim pile. Sums of games XOR their Grundy values.

---

## 🔬 Deep-dive 2 — Alpha-beta cutoffs traced on a tiny tree

Game tree, maximizer at root, depth 2, branching 3:

```
                   MAX
                /   |   \
               A    B    C            ← MIN level (depth 1)
              /|\  /|\  /|\
             3 5 6 6 7 4 5 ...         ← MAX level (depth 2, terminal evals)
```

Plain minimax: visits all 9 leaves.

Alpha-beta with default `(α=−∞, β=+∞)`:

- Visit A (MIN). `α=−∞, β=+∞`.
  - Leaf 3: A's value ≤ 3. Set `β=3`.
  - Leaf 5: 5 > 3, MIN won't pick it. `β` stays 3.
  - Leaf 6: 6 > 3, same. A's final value = 3.
- Back at root. MAX has lower bound 3, so `α = 3`.
- Visit B (MIN). `α=3, β=+∞`.
  - Leaf 6: B's value ≤ 6. `β = 6`.
  - Leaf 7: skip (7 > 6, doesn't change MIN).
  - Hmm but wait — the prune fires: `α ≥ β` becomes `3 ≥ 6`? No. **Prune fires when α ≥ β**, here `3 < 6` — no prune.
  - Leaf 4: B's value ≤ 4. `β = 4`. Now `α(3) < β(4)`, no prune.
  - B's final value = 4.
  - Wait — actually let me redo: at the MIN node, after evaluating each leaf, we update β. After leaf 6: β=6. After leaf 7: β=min(6,7)=6, no change. After leaf 4: β=4. The check `α ≥ β` fires *after* updating β. So `α=3, β=4`: still no prune.
  - B = 4.
- Back at root: max(3, 4) = 4. `α = 4`.
- Visit C (MIN). `α=4, β=+∞`.
  - Leaf 5: C's value ≤ 5. `β = 5`. Check: `α(4) ≥ β(5)`? No — keep going.
  - Leaf X: ... etc.

**Key point:** every time MIN's `β` drops to `≤ α`, all remaining children are pruned because MAX has already found a strictly better alternative elsewhere. **The pruning power depends entirely on move ordering** — if the best move is searched first, `α` rises quickly and β-cutoffs fire often. With perfect ordering, alpha-beta visits ~`b^(d/2)` nodes. With reverse-perfect ordering, no cutoffs fire and you're back to `b^d`.

This is why chess engines spend so much code on **move ordering heuristics**: principal variation, killer moves, history heuristic, MVV-LVA, SEE.

---

## 🔬 Deep-dive 3 — Iterative deepening + transposition table architecture

A real engine doesn't run `alphabeta(depth=12)` directly. Instead:

```python
def search(state, max_time_ms: int) -> Move:
    deadline = now_ms() + max_time_ms
    best_move = None
    for d in range(1, MAX_DEPTH):
        if now_ms() >= deadline: break
        score, move = alphabeta_with_tt(state, d, -INF, +INF, True)
        best_move = move                                              # (1) update on each completed depth
    return best_move
```

1. **Iterative deepening** — search depth 1, then 2, then 3, etc. Each completed iteration produces a usable best move. **Why not just go to depth `d` directly?** Because (a) you might exceed the time budget; (b) the previous depth's result *seeds* this depth's move ordering, making alpha-beta dramatically faster.

**Transposition table (TT)** — a hash map from `zobrist_hash(state)` to `(depth, score, flag, best_move)` where `flag ∈ {EXACT, LOWER, UPPER}`. Every time you re-enter the same position (different move sequences leading to the same board), you can reuse the cached result if the cached depth ≥ current depth. The `best_move` field also serves as the **first move tried** at this position next time — feeding into move ordering.

```python
def alphabeta_with_tt(state, depth, alpha, beta, maximizing):
    h = zobrist(state)
    entry = TT.get(h)
    if entry and entry.depth >= depth:                                # (1) reuse
        if entry.flag == EXACT: return entry.score
        if entry.flag == LOWER: alpha = max(alpha, entry.score)
        if entry.flag == UPPER: beta = min(beta, entry.score)
        if alpha >= beta: return entry.score
    # ... normal alpha-beta, but try entry.best_move first
    # ... store result in TT with appropriate flag
```

1. The flags handle the case where the cached score was a bound (returned via cutoff) rather than exact — you can still tighten α/β.

**Killer moves** — at each ply, remember the last 2 moves that caused β-cutoffs. Try them first at sibling nodes (often the same tactic works). Cheap; ~30% speedup typical.

**Null move heuristic** — let opponent move twice; if you're still winning at reduced depth, prune. Risky (zugzwang), but used in every engine since the 90s.

**Late move reductions (LMR)** — search the first few moves to full depth; reduce depth for later moves; re-search if they exceed α. Saves enormous time on bad-move-rich positions.

The whole stack — minimax → alpha-beta → iterative deepening → TT → killer + history → null move → LMR → quiescence search — is what gets you from "tic-tac-toe" to "Stockfish 14". Each layer is a 1.5–3× constant-factor speedup, multiplying together to make the difference between "depth 6" and "depth 30."

---

## 🐛 Common bugs

1. **Alpha-beta with `α > β` initial.** `α` must start at `−∞` and `β` at `+∞`; reversing them prunes everything immediately and returns nonsense.
2. **Misère Nim handled like normal Nim.** When the *last* move *loses*, the strategy differs only when all piles are size 1. Special-case it: with all piles = 1, the player to move wants to leave an *odd* number of piles for the opponent.
3. **Grundy number computed without `mex`.** A common mistake is `g(s) = max(g(reachable)) + 1` — that's wrong. `mex` returns the *minimum* non-negative integer not present.
4. **Stone-game DP with the wrong base case.** When `l == r`, return `turn * piles[l]`, not `0` or `piles[l]`.
5. **Zobrist hashing — XORing twice when undoing.** Zobrist is its own inverse: XOR a piece in, XOR it out — same key. Forgetting this leaves stale state in the hash and corrupts the TT.
6. **Transposition table reusing scores from shallower depths.** A score from `depth = 3` is not reusable when you need `depth = 5`. Always check `entry.depth ≥ current_depth`.
7. **Iterative deepening saving the best move from an *interrupted* iteration.** If iteration `d` was cut short by time, its "best move" is unreliable — use the last *completed* iteration's move.
8. **Memoization in minimax without including "whose turn" in the key.** `dp[state]` is wrong if the same state can occur on different players' turns — needs `dp[state][turn]` or the symmetric trick from Flavor 4.
9. **Sum-of-games XOR computed game-by-game with state.** If two sub-games share state (one move affects both), they're not independent — Sprague-Grundy fails.
10. **Quiescence search not implemented in chess.** Without it, the search stops mid-capture, giving wildly wrong evaluations. Quiescence extends the search through "noisy" positions until they settle.

---

## 🗣️ Interviewer phrasings to recognize

- "Two players take turns, both play optimally, who wins?" → impartial game → **Sprague-Grundy / Nim**.
- "Stones in piles, take from one pile per move" → literally **Nim**.
- "Range / endpoint game on an array" → **stone-game DP** (`dp[l][r]`).
- "Game on a graph, find optimal play" → **DP on states / minimax**.
- "Search the game tree to depth d" → **alpha-beta**.
- "How would you write a chess engine?" → **iterative deepening + alpha-beta + TT + move ordering**.
- "Two independent games combined" → **XOR Grundy**.
- "Game with random elements (dice)" → **expectiminimax** or **MCTS**.

---

## 🧭 Connections to other patterns

- **[Advanced DP](04-advanced-dp.md)** — game DP is just DP with two-player optimisation; bitmask DP for "Can I Win" (LC 464) is the canonical crossover.
- **[Randomised Algorithms](06-randomised-algorithms.md)** — **MCTS** uses random rollouts + UCB1 to handle game trees with branching too high for alpha-beta (Go, general game playing).
- **[Topological Sort](../04-patterns/14-topological-sort.md)** — game-graph coloring (LC 913 Cat and Mouse) computes win/lose values via reverse topo from terminal positions.
- **[Tries](../05-advanced/01-tries.md)** — **Zobrist hashing** is the trie-of-bits idea applied to board positions: each piece-square gets a random key, and XOR composes.
- **Reinforcement learning** — DP-on-game-states is the value-iteration view of optimal policies. **Q-learning** generalises to unknown transition models; **AlphaZero** combines it with MCTS + neural-network value/policy heads.
- **Combinatorial optimisation** — many "is there an assignment?" problems reduce to game-graph reachability with the SG framework.

---

## ✅ Self-check — 8 questions

??? question "1. State Sprague-Grundy and explain `mex` in one sentence."
    Every impartial game is equivalent (in the sum-of-games sense) to a Nim pile of size `g(state)`, where `g(s) = mex({g(s') : s' reachable from s})`. `mex` (minimum excludant) of a set `S` is the smallest non-negative integer not in `S`.

??? question "2. Why does Nim's XOR rule work — outline both directions."
    From XOR = 0: any move changes one pile, flipping its bits and shifting the XOR to non-zero. From XOR ≠ 0: locate the leftmost set bit of XOR `S`; some pile has that bit set; reduce that pile by XORing it with `S` (gives a strictly smaller pile and flips XOR to 0). Together, P-positions ↔ XOR=0 is closed correctly.

??? question "3. Why does alpha-beta achieve `O(b^(d/2))` with perfect move ordering?"
    With perfect ordering, the first child explored at every node is the best one (best response of opponent). At each internal node, this best child's score immediately raises α (or lowers β) to the optimal value, allowing all sibling subtrees to be pruned in one comparison. The tree alternates between fully-expanded levels and one-child-explored levels — total nodes = `b^⌈d/2⌉ + b^⌊d/2⌋ − 1 ≈ 2 b^(d/2)`.

??? question "4. Walk through the LC 486 (Predict the Winner) DP recurrence."
    Define `dp[l][r]` = max score difference (current player minus opponent) the player to move can achieve on subarray `[l, r]`. Base: `dp[i][i] = piles[i]`. Recurrence: `dp[l][r] = max(piles[l] − dp[l+1][r], piles[r] − dp[l][r-1])` — pick a side, subtract opponent's optimal future diff. First player wins iff `dp[0][n-1] ≥ 0`.

??? question "5. What's a transposition table and why does it matter for chess engines?"
    A hash map keyed by Zobrist hash of board states, storing `(depth, score, flag, best_move)`. It exploits the fact that many move sequences reach the same board (transpositions) — caching avoids re-searching. Modern engines see TT hit rates of 30–60% even at deep search; without it, depth 8 chess search is ~5× slower.

??? question "6. When does Sprague-Grundy NOT apply?"
    Three cases: (a) **partisan games** where players have different moves (chess, Go); (b) games with **chance** (dice, cards); (c) games where sub-games **share state** (so they're not independent). For (a), use minimax; for (b), expectiminimax or MCTS; for (c), tabulate the joint state.

??? question "7. Compare iterative deepening + alpha-beta vs. plain alpha-beta at fixed depth — when is iterative deepening worth the cost?"
    Iterative deepening searches depths 1, 2, ..., d before reaching the target. Naively, this *adds* work — but each iteration's TT and move-ordering data make the next iteration much faster (the depth-d search has near-perfect move ordering, getting it close to `b^(d/2)` instead of `b^(3d/4)`). Net: iterative deepening is typically 1.5–3× *faster* than direct depth-d search, plus you can stop anytime.

??? question "8. Why is MCTS preferred over alpha-beta for Go?"
    Go has branching factor ~250 and reasonable game length 100+, giving alpha-beta tree size ~`250^50 ≈ 10¹²⁰` — utterly infeasible even with perfect pruning. MCTS uses **selective sampling** via UCB1: exploit promising branches, occasionally explore unexplored ones, simulate to terminal via random rollouts, back-propagate win rates. Combined with deep neural-network policy/value heads (AlphaZero), MCTS solved superhuman Go without any explicit eval function — something alpha-beta couldn't do for 30 years of trying.

---

> **Chapter complete.** Phase 7 — Ultra-Advanced — is now seven topics deep: Persistent Data Structures, Max-Flow / Min-Cut, Computational Geometry, Advanced DP, Online Algorithms & Sketches, Randomised Algorithms, and Game Theory & Alpha-Beta. The chapter is meant to be read once front-to-back as a *capstone tour* and then revisited topic-by-topic as interview prep demands.
