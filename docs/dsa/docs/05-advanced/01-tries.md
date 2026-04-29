# Tries (Prefix Trees)

> The first advanced data structure most engineers reach for in interviews. A trie is **a tree whose paths spell strings** — every edge is labelled with a character, and every node corresponds to a *prefix* of some inserted string. Insert and query are both O(L) in the length of the string, **independent of the dictionary size**. The whole "autocomplete, prefix search, dictionary, word-game, XOR-pair" interview category lives here.

<span class="phase-status phase-done">Phase 6 — Advanced</span>

---

## 📖 What is a trie?

A **trie** (pronounced "try", from re*trie*val) is a tree where:

- Each **node** represents a string prefix — the empty prefix at the root.
- Each **edge** is labelled with a character.
- Each node optionally marks whether the prefix it represents is a **complete word** (`is_end = True`).

The path from root to any node spells out the prefix that node represents. Inserting `"cat"`, `"car"`, `"care"` into an empty trie produces:

```
root
 └── c
     └── a
         ├── t  [end]
         └── r  [end]
             └── e  [end]
```

The two key properties:

1. **All strings sharing a prefix share the same path** until they diverge. The branch point is exactly where they first differ.
2. **Lookup is O(L)**, length of the query string. The dictionary size never enters the cost — searching among 1M words is the same speed as searching among 10.

The mental model: imagine a **filing cabinet indexed by character at each level**. To file `"cat"`, walk to the `c` drawer, then the `a` sub-drawer, then the `t` sub-sub-drawer, and stamp it. To check if any word starts with `"ca"`, walk to `c` then `a` and see if anything's filed below.

!!! tip "The signal — when to reach for a trie"
    Reach for it when:

    - "**Prefix** queries" — autocomplete, "does any word start with X", longest common prefix.
    - "**Insert and search** a dictionary" with O(L) lookup independent of size.
    - "**Word game** on a board" (LC 79 Word Search II uses a trie to prune DFS).
    - "**Replace words** with their root" (LC 648).
    - "**Maximum / minimum XOR**" of pairs — bitwise trie variant (LC 421).
    - "Stream of words / prefixes / suffixes" with continuous insert + query.

    Don't reach for it when:

    - You only need exact-match lookup with no prefixes — a hash set is simpler and faster constant-factor.
    - The strings are very long with little prefix overlap — trie space blows up, suffix-array / hash beats it.
    - You only have a handful of words — sorted array + binary search is fine and zero ceremony.

---

## 🧩 The three implementations

### Implementation 1: Dict-of-dicts (Pythonic, fastest to write)

```python
class Trie:
    def __init__(self) -> None:
        self.root: dict = {}
        self._END = "$"                                            # (1) sentinel; can be any non-letter

    def insert(self, word: str) -> None:
        node = self.root
        for c in word:
            node = node.setdefault(c, {})                          # (2) walk-or-create
        node[self._END] = True                                     # (3) mark end-of-word

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and self._END in node

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> dict | None:
        node = self.root
        for c in s:
            if c not in node:
                return None
            node = node[c]
        return node
```

1. The end-of-word marker is a non-letter key — using `$` or `True` keyed by a sentinel string avoids colliding with any real character.
2. `setdefault(c, {})` is the "walk into child, create if missing" idiom. One method call per level.
3. Marking `is_end` as a key in the node itself, rather than a wrapper object, keeps the node a plain `dict`.

**Why this is the interview default:** writes in 15 lines, no class hierarchy, no array sizing. Acceptable for any LC trie problem.

### Implementation 2: TrieNode class (cleaner for problems with extra metadata)

```python
class TrieNode:
    __slots__ = ("children", "is_end", "word")
    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_end: bool = False
        self.word: str | None = None                              # (1) optional — useful for Word Search II


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for c in word:
            if c not in node.children:
                node.children[c] = TrieNode()
            node = node.children[c]
        node.is_end = True
        node.word = word                                          # (2) store the full word at the leaf

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_end

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> TrieNode | None:
        node = self.root
        for c in s:
            child = node.children.get(c)
            if child is None:
                return None
            node = child
        return node
```

1. `__slots__` keeps each node lean. Storing `word` at the end-node is a useful trick for Word Search II — when DFS hits a node with `node.word`, you've found a match without rebuilding the path.
2. Setting `node.word` at the leaf makes the eventual extraction one step.

### Implementation 3: Array-backed (lowercase a–z, fastest at runtime)

```python
class TrieNode:
    __slots__ = ("children", "is_end")
    def __init__(self) -> None:
        self.children: list[TrieNode | None] = [None] * 26        # (1) fixed alphabet
        self.is_end: bool = False


class Trie:
    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for c in word:
            i = ord(c) - ord("a")
            if node.children[i] is None:
                node.children[i] = TrieNode()
            node = node.children[i]
        node.is_end = True
```

1. Fixed-size 26-slot array per node. Cache-friendly and a few times faster than a hash; uses 26 × pointer-size bytes per node even when most are unused. Worth it when you know the alphabet is small and fixed (lowercase a–z, digits 0–9, ATCG, etc.).

**Use the array form** for performance-sensitive contests / huge dictionaries. **Use the dict form** in interviews unless asked for the optimised version.

---

## 🎒 The seven sub-patterns

| # | Sub-pattern | Plain English | Canonical problem | Trick |
|---|-------------|---------------|-------------------|-------|
| 1 | Insert + Search + StartsWith | Basic dictionary trie | LC 208 | Walk-or-create on insert; walk-or-fail on search |
| 2 | Wildcard search (`.` matches any) | Regex-lite | LC 211 | DFS into all children when `c == '.'` |
| 3 | Trie + DFS over a board | Word search with dictionary | LC 212 | Build trie from words; DFS the board pruned by trie |
| 4 | Replace-with-shortest-root | Greedy prefix replacement | LC 648 | Walk both word and trie; replace at first end-marker |
| 5 | Bitwise trie | Max/min XOR over pairs | LC 421 | Indexed by bits MSB-first; greedy opposite-bit walk |
| 6 | Word lookup + score | Stream + ranked autocomplete | LC 642 | Trie + heap or sorted list at each node |
| 7 | Suffix trie / Aho–Corasick (Ultra-advanced cousin) | Multi-pattern matching | — | Add fail links for O(n + matches) text scanning |

---

## 📋 Twenty problems on tries

| # | Problem | LC # | Difficulty | Sub-pattern | Status |
|---|---------|------|------------|-------------|--------|
| 1 | Implement Trie (Prefix Tree) | 208 | <span class="diff-medium">Medium</span> | Basic | 📝 |
| 2 | Design Add and Search Words Data Structure | 211 | <span class="diff-medium">Medium</span> | Wildcard search | 📝 |
| 3 | Word Search II | 212 | <span class="diff-hard">Hard</span> | Trie + DFS | 📝 |
| 4 | Replace Words | 648 | <span class="diff-medium">Medium</span> | Replace-with-root | 📝 |
| 5 | Maximum XOR of Two Numbers in Array | 421 | <span class="diff-medium">Medium</span> | Bitwise trie | ✅ |
| 6 | Longest Word in Dictionary | 720 | <span class="diff-medium">Medium</span> | Trie BFS for longest word | 📝 |
| 7 | Map Sum Pairs | 677 | <span class="diff-medium">Medium</span> | Trie with subtree sum | 📝 |
| 8 | Design Search Autocomplete System | 642 | <span class="diff-hard">Hard</span> | Trie + ranked queries | 📝 |
| 9 | Stream of Characters | 1032 | <span class="diff-hard">Hard</span> | Reverse-trie of patterns | 📝 |
| 10 | Concatenated Words | 472 | <span class="diff-hard">Hard</span> | Trie + DP over prefixes | 📝 |
| 11 | Short Encoding of Words | 820 | <span class="diff-medium">Medium</span> | Suffix trie (insert reversed) | 📝 |
| 12 | Index Pairs of a String | 1065 | <span class="diff-easy">Easy</span> | Trie scan over text | 📝 |
| 13 | Implement Magic Dictionary | 676 | <span class="diff-medium">Medium</span> | Trie + 1-edit DFS | 📝 |
| 14 | Maximum XOR With an Element From Array | 1707 | <span class="diff-hard">Hard</span> | Offline bitwise trie | 📝 |
| 15 | Count Pairs With XOR in Range | 1803 | <span class="diff-hard">Hard</span> | Bitwise trie + count | 📝 |
| 16 | Top K Frequent Words | 692 | <span class="diff-medium">Medium</span> | Trie alternative to heap | 📝 |
| 17 | Camelcase Matching | 1023 | <span class="diff-medium">Medium</span> | Trie + two-pointer match | 📝 |
| 18 | Sum of Prefix Scores of Strings | 2416 | <span class="diff-hard">Hard</span> | Trie node with visit-count | 📝 |
| 19 | Palindrome Pairs | 336 | <span class="diff-hard">Hard</span> | Trie + palindrome check | 📝 |
| 20 | Lexicographical Numbers | 386 | <span class="diff-medium">Medium</span> | Implicit trie DFS over digits | 📝 |

> **Status legend:** ✅ done elsewhere · 📝 to be added · 🚧 in progress.

---

## 🔬 Three deep-dives

### Deep-dive 1 — Implement Trie (LC 208)

> Implement `insert(word)`, `search(word)`, `startsWith(prefix)` with O(L) per operation.

#### Code (re-stated, dict form)

```python
class Trie:
    def __init__(self) -> None:
        self.root: dict = {}
        self._END = "$"

    def insert(self, word: str) -> None:
        node = self.root
        for c in word:
            node = node.setdefault(c, {})
        node[self._END] = True

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and self._END in node

    def startsWith(self, prefix: str) -> bool:
        return self._walk(prefix) is not None

    def _walk(self, s: str) -> dict | None:
        node = self.root
        for c in s:
            if c not in node:
                return None
            node = node[c]
        return node
```

#### Dry run — insert `"apple"`, `"app"`, then various queries

After inserting `"apple"`:

```
root → a → p → p → l → e [end]
```

After inserting `"app"`:

```
root → a → p → p [end] → l → e [end]
```

Notice the second `p` now has *both* an `is_end` marker (for `"app"`) and a child `l` (continuing toward `"apple"`).

| Query | Walk path | End marker at last? | Result |
|-------|-----------|---------------------|--------|
| `search("apple")` | a → p → p → l → e ✓ | yes | `True` |
| `search("app")` | a → p → p ✓ | yes | `True` |
| `search("ap")` | a → p ✓ | no | `False` |
| `startsWith("app")` | a → p → p ✓ | — | `True` |
| `search("apricot")` | a → p ≠ r | — | `False` |

#### The crucial distinction: `search` vs `startsWith`

`startsWith` succeeds if the walk completes — we don't care if the prefix is itself a stored word. `search` requires the walk to complete **and** the final node to have the end marker.

The most common bug here is collapsing the two into one method that "checks if the walk reaches the end and returns true." That breaks `search` for partial-prefix words.

#### Complexity

- **Time:** O(L) per operation, where L = length of the word/prefix.
- **Space:** O(total characters across all inserted words). Each inserted character contributes at most one node.

---

### Deep-dive 2 — Word Search II (LC 212)

> Given a `m × n` board of characters and a list of words, return all words that appear on the board (4-connected). DFS per word would be O(W · m · n · 4^L). With a trie, drop a factor of W.

The single most important advanced trie problem. The trick: **build a trie from all the words, then DFS the board once and let the trie prune.**

#### Code

```python
def find_words(board: list[list[str]], words: list[str]) -> list[str]:
    """LC 212."""
    # build trie
    root: dict = {}
    for w in words:
        node = root
        for c in w:
            node = node.setdefault(c, {})
        node["$"] = w                                              # (1) store the word at end node

    rows, cols = len(board), len(board[0])
    found: list[str] = []

    def dfs(r: int, c: int, node: dict) -> None:
        ch = board[r][c]
        nxt = node.get(ch)
        if nxt is None:
            return                                                  # (2) trie pruning — no word continues here
        if "$" in nxt:                                              # (3) reached end of a word
            found.append(nxt.pop("$"))                              # (4) avoid duplicate matches by removing
        board[r][c] = "#"                                           # (5) mark visited (in-place to save memory)
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != "#":
                dfs(nr, nc, nxt)
        board[r][c] = ch                                            # (6) restore — backtracking

        if not nxt:                                                 # (7) prune trie of dead branches as we go
            node.pop(ch, None)

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)

    return found
```

1. Storing the word string itself at the end node lets us emit it on hit without reconstructing.
2. The early return on `nxt is None` is the **trie's pruning power**: if no word continues with this character, the entire DFS subtree is skipped. This is the speedup over per-word DFS.
3. End-of-word reached. Add to results.
4. Pop the `$` marker so the same word isn't reported twice if it has multiple paths on the board.
5. In-place visited marking (saves a separate `visited` set; common LC trick).
6. Backtrack — restore the cell so other paths can use it.
7. **Pruning the trie itself** as DFS unwinds. If `nxt` is empty (all words through this branch are found and removed), drop it from the parent. Subsequent DFS at the same character will short-circuit.

#### Why the trie matters

Per-word DFS on each starting cell is O(W · m · n · 4^L). With a trie:

- One DFS from each cell.
- Each step extends the trie path — cost is **per-cell**, not per-word.
- Pruning means dead trie branches are removed; the search shrinks as words are found.

In practice, runtime is dominated by the structure of the words and the board, not by `W` directly. For `W = 10^4` words, the speedup is several orders of magnitude.

#### Common pitfall: forgetting to backtrack

Setting `board[r][c] = "#"` and not restoring breaks the search for any word that crosses cells in a different order. Always pair the in-place mark with a restore.

#### Complexity

- **Time:** O(m · n · 4^L_max) where L_max is the longest word. Without trie: O(W · m · n · 4^L_max).
- **Space:** O(total characters in dictionary) for the trie + O(L_max) recursion.

---

### Deep-dive 3 — Bitwise Trie for Maximum XOR (LC 421)

> Given an integer array, return the maximum XOR over all pairs `nums[i] ^ nums[j]`.

Already covered in [Pattern 20: Bitwise XOR](../04-patterns/20-bitwise-xor.md). Restated here from the trie angle: **a bitwise trie is just a regular trie with alphabet `{0, 1}`** indexing by bits MSB-first.

#### Code (re-stated)

```python
def find_maximum_xor(nums: list[int]) -> int:
    BITS = max(nums).bit_length() if nums else 0
    root: dict = {}

    for x in nums:                                                 # build trie
        node = root
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            node = node.setdefault(b, {})

    best = 0
    for x in nums:                                                 # query
        node = root
        cur = 0
        for i in range(BITS - 1, -1, -1):
            b = (x >> i) & 1
            opp = 1 - b
            if opp in node:                                        # prefer the opposite bit (XOR contributes 1)
                cur |= 1 << i
                node = node[opp]
            else:
                node = node[b]
        best = max(best, cur)

    return best
```

#### The trie shape on `nums = [3, 10, 5, 25, 2, 8]`

5-bit binary:

| x | bits |
|----|------|
| 3 | 00011 |
| 10 | 01010 |
| 5 | 00101 |
| 25 | 11001 |
| 2 | 00010 |
| 8 | 01000 |

Building MSB-first creates a binary tree of depth 5. The MSB level partitions into `0` (everyone except 25) and `1` (just 25). At each subsequent level, the split is by the next bit.

The query for `x = 5 = 00101` walks: prefer 1 (find 25's branch), prefer 1 (forced 1, 25 is the only one), prefer 0 (25 has 0 here, take it), prefer 1 (25 has 0, fall back to 0), prefer 0 (25 has 1, fall back to 1). Path's bits when XORed with `x`'s bits: `1^0=1, 1^0=1, 0^1=1, 0^0=0, 1^1=0` → `0b11100 = 28`. ✓

#### Why MSB-first is greedy-optimal

The MSB contributes more to the XOR than every lower bit combined (`2^(BITS-1) > 2^(BITS-1) - 1`). If you can flip the MSB, that strictly beats any combination of flips below it. So at each level, take the opposite-bit branch if available; only fall back when forced.

#### Complexity

- **Time:** O(n · BITS). Build is O(n · BITS); query is O(n · BITS).
- **Space:** O(n · BITS) for the trie nodes.

---

## 🐛 Common bugs

1. **Forgetting the `is_end` marker.** Without it, `search("app")` and `startsWith("app")` are indistinguishable. Always store an end marker — a sentinel key, a boolean field, or a stored word string.
2. **Sentinel key collision.** Using `"end"` or another letter combination as the end marker risks colliding with real input. Use a non-letter character (`"$"`, `"#"`) or a non-string sentinel.
3. **Not backtracking in trie + DFS combos.** Word Search II marks cells visited in-place to save memory. Forgetting to restore the cell breaks all subsequent paths.
4. **Inserting one word twice and double-counting.** If the dictionary has duplicates and your code emits results from the trie, dedupe before insert or after collect.
5. **Querying a partial word with `startsWith` instead of `search`.** They look similar but differ at the final step. `startsWith` always returns true if the walk completes; `search` additionally checks `is_end`.
6. **Array-trie sized too small.** If you size `children` to 26 and the input includes uppercase or digits, you get index errors. Always verify the alphabet before choosing array vs dict.
7. **Bitwise trie forgetting to fall back to same-bit on opposite-not-available.** A naive greedy that *only* takes the opposite-bit branch walks off the trie. Always `if opp in node: take opp; else: take same`.
8. **Memory blow-up on long, low-overlap strings.** A trie of `n` strings of length `L` with little prefix overlap is O(n · L) nodes. For long DNA / log-line data, suffix arrays or hashing beat tries on memory.
9. **Returning the trie node instead of a boolean from `_walk`.** Internal helpers should return the node (so multiple methods can share); public methods translate that into bool/end-check before returning.

---

## 🗣️ Interviewer phrasings to recognize

- "**Implement** insert, search, startsWith." → LC 208, the textbook trie.
- "Add `.` as a wildcard matching any character." → LC 211, DFS into all children at `.`.
- "Find all **words** on a board." → LC 212, trie + DFS with pruning.
- "Replace each word with the shortest **root** in a dictionary." → LC 648, trie walk until first end-marker.
- "**Maximum / minimum XOR** of any two numbers." → LC 421, bitwise trie MSB-first.
- "Stream of characters; report when any of K patterns appears as a suffix." → LC 1032, build a reversed-pattern trie.
- "Autocomplete / suggest next words." → LC 642, trie + score per node.
- "**Concatenated** words / **palindrome pairs**." → LC 472 / LC 336, trie + per-node logic.

---

## 🧭 Connections to other patterns

- **[Bitwise XOR](../04-patterns/20-bitwise-xor.md)** — the bitwise trie is the same data structure indexed on bits; max-XOR pairing is its canonical use.
- **[Subsets & Backtracking](../04-patterns/10-subsets-backtracking.md)** — Word Search II is DFS + trie pruning; the backtracking shape is identical to LC 79 (single word).
- **Hash maps** — the everyman alternative for exact lookup. Tries beat hashes whenever queries are *prefix-based* or you need to enumerate by prefix.
- **Suffix arrays / suffix automata (Ultra-advanced)** — the natural extension when you need to query *all suffixes* of a long string efficiently. Tries on suffixes are quadratic in space; suffix arrays are linear.
- **Aho–Corasick (Ultra-advanced)** — a trie augmented with **failure links** for multi-pattern matching in O(n + matches). Used in grep-like tools and intrusion detection.

---

## ✅ Self-check — 8 questions

??? question "1. What's the cost of insert and search in a trie of N words of average length L?"
    Insert: O(L) per word, O(N · L) total. Search: O(L) per query — independent of N. The dictionary size factor that hash maps share is absent.

??? question "2. Why does the trie need an `is_end` marker even though we already terminate the walk at the right node?"
    Because a word may be a prefix of another word. Inserting `"app"` and then `"apple"` puts both in the same path. Without an `is_end` at `app`'s last node, you can't distinguish "stored word" from "internal prefix".

??? question "3. Is `startsWith(prefix)` the same as `search(prefix)`?"
    No. `startsWith` only requires the walk to complete; `search` additionally requires the final node's `is_end` to be true. `startsWith("app")` is true after inserting only `"apple"`; `search("app")` is false in the same case.

??? question "4. How does Word Search II (LC 212) gain a speedup over running LC 79 W times?"
    LC 79 runs DFS per word: O(W · m · n · 4^L). LC 212 builds a trie from all words and DFS-es the board once, with the trie pruning impossible branches early. Cost becomes O(m · n · 4^L_max), a factor of W faster.

??? question "5. Why store the *word string itself* at the trie's end node in LC 212?"
    When DFS hits an end node, you need to emit the matched word. Storing the string at the leaf saves rebuilding the path, and lets you `pop` it to dedupe results.

??? question "6. Why prefer a dict-of-dicts over an array-trie in interviews?"
    Faster to write, no alphabet-size mistakes, and asymptotic cost is the same. Array tries are cache-friendlier and a few times faster in tight loops, but only worth pulling out for performance-critical contests.

??? question "7. Why is MSB-first the right order for the bitwise trie in LC 421?"
    The MSB contributes `2^(BITS-1)` to the XOR — strictly more than every lower bit combined. The greedy "prefer opposite bit at each level" works iff higher bits are decided first; any lower-bit ordering can be beaten.

??? question "8. When would you reach for a suffix trie / suffix array / Aho–Corasick instead of a plain trie?"
    Plain trie: independent words, prefix queries. Suffix trie / suffix array: many substrings of one long text, substring queries. Aho–Corasick: multiple patterns matched against streaming text in linear time. The choice is driven by what you're querying, not by the data structure's "advancedness."

---

> **Up next in Advanced:** Union-Find / DSU — connectivity, cycle detection, and Kruskal's MST. Then Segment Trees, Fenwick (BIT), Suffix Arrays, Heavy-Light Decomposition, and Mo's Algorithm.
