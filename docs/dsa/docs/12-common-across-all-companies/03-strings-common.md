# Strings — common across all companies

> The interview-prep canon: every shop, from FAANG to a 2-year-old startup, asks at least three of these.

<span class="company-tag">Google</span> &nbsp; <span class="company-tag">Meta</span> &nbsp; <span class="company-tag">Amazon</span> &nbsp; <span class="company-tag">TCS</span> &nbsp; <span class="company-tag">ISRO</span> &nbsp; <span class="phase-status phase-done">Phase 14 — Common Across</span>

---

Strings are the most "universal" interview topic — they need no framework, no extra data structure, and they map cleanly onto patterns (two pointers, sliding window, hashing). The problems on this page show up in **phone screens, online assessments, and onsites at virtually every company**. Master them and you can confidently knock down ~30% of any generic interview loop.

## Patterns that drive these problems

| Pattern | Frequency | Where it shows up |
|---|---|---|
| Two pointers (palindromes, reversal) | ★★★★★ | Valid Palindrome, Reverse String/Words |
| Sliding window + hash | ★★★★★ | Longest Substring W/O Repeating, Find Anagrams |
| Hash map / counter | ★★★★★ | Anagram, Group Anagrams, Roman to Int |
| Stack | ★★★★☆ | Valid Parentheses, decode-style problems |
| Expand-around-center / DP | ★★★☆☆ | Longest Palindromic Substring |
| Simulation / parsing | ★★★☆☆ | atoi, ZigZag, Multiply Strings |

## The list (15 problems)

| # | Problem | Difficulty | Pattern | LC# |
|---|---|---|---|---|
| 1 | Valid Anagram | Easy | Counter | 242 |
| 2 | Valid Palindrome | Easy | Two pointers | 125 |
| 3 | Reverse String | Easy | Two pointers | 344 |
| 4 | Reverse Words in a String | Medium | Split + reverse | 151 |
| 5 | Longest Common Prefix | Easy | Vertical scan | 14 |
| 6 | Longest Substring Without Repeating Chars | Medium | Sliding window | 3 |
| 7 | Group Anagrams | Medium | Hash by signature | 49 |
| 8 | Valid Parentheses | Easy | Stack | 20 |
| 9 | String to Integer (atoi) | Medium | Simulation | 8 |
| 10 | Implement strStr / Find Needle | Easy | KMP / sliding | 28 |
| 11 | Encode and Decode Strings | Medium | Length-prefix | 271 |
| 12 | Longest Palindromic Substring | Medium | Expand around center | 5 |
| 13 | Roman to Integer | Easy | Lookup + sweep | 13 |
| 14 | Multiply Strings | Medium | Digit-by-digit | 43 |
| 15 | ZigZag Conversion | Medium | Bucket simulation | 6 |

---

## Deep-dive 1 — Longest Substring Without Repeating Characters

The single most-asked sliding-window problem. Maintain a window `[l, r]` of unique characters; whenever a duplicate enters at `r`, slide `l` past its previous index.

??? question "Why is the `last_seen[c] >= l` check critical?"
    Because we never physically erase characters from `last_seen`. A character may have been seen long before the current window started. We only advance `l` if the duplicate is **inside** the window.

```python linenums="1"
from __future__ import annotations


def length_of_longest_substring(s: str) -> int:
    """Return the length of the longest substring with all-unique characters.

    Sliding window: expand `r`, contract `l` only when a repeat falls
    inside the current window.

    Time:  O(n) — each index visited at most twice.
    Space: O(min(n, alphabet)).
    """
    last_seen: dict[str, int] = {}
    l = 0
    best = 0
    for r, c in enumerate(s):
        if c in last_seen and last_seen[c] >= l:
            l = last_seen[c] + 1
        last_seen[c] = r
        best = max(best, r - l + 1)
    return best


# Trace: "abcabcbb"
# r=0 a -> window "a"        best=1
# r=1 b -> window "ab"       best=2
# r=2 c -> window "abc"      best=3
# r=3 a -> dup, l=1 -> "bca" best=3
# r=4 b -> dup, l=2 -> "cab" best=3
# r=5 c -> dup, l=3 -> "abc" best=3
# r=6 b -> dup, l=5 -> "cb"
# r=7 b -> dup, l=7 -> "b"
# answer = 3
```

!!! tip "Interview talking points"
    - Mention the alphabet trick: if the alphabet is fixed (ASCII), `last_seen` can be a fixed array `int[128]` for cache-friendliness.
    - The window is **monotonic in `l`** — `l` never decreases. That's what gives the O(n) bound.

---

## Deep-dive 2 — Group Anagrams

The canonical "hash by signature" problem. Two strings are anagrams iff they share a canonical key. Picking the right key is the whole game.

??? question "Sorted-string key vs character-count tuple — which to use?"
    - **Sorted key** (`"".join(sorted(s))`): O(k log k) per word, simple, correct.
    - **Count tuple** (`tuple(count[26])`): O(k) per word, faster when many long words. Use when k is large or words are very long.
    Most interviewers accept either; mention both and pick the count-tuple if asked to optimise.

```python linenums="1"
from __future__ import annotations
from collections import defaultdict


def group_anagrams(strs: list[str]) -> list[list[str]]:
    """Group strings that are anagrams of each other.

    Approach: hash each word to a canonical signature (sorted form, or
    a 26-int count tuple) and bucket by signature.

    Time:  O(n * k)   with count-tuple key (k = avg word length)
           O(n * k log k) with sorted key
    Space: O(n * k)
    """
    buckets: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for word in strs:
        counts = [0] * 26
        for ch in word:
            counts[ord(ch) - ord('a')] += 1
        buckets[tuple(counts)].append(word)
    return list(buckets.values())


# Example
# strs = ["eat","tea","tan","ate","nat","bat"]
# -> [["eat","tea","ate"], ["tan","nat"], ["bat"]]
```

!!! warning "Don't pick a hash that collides"
    Tempting bug: hashing by `sum(ord(c) for c in word)`. `"abc"` and `"bda"` collide. Always use a **unique** signature (sorted or full count vector).

---

## 🃏 Cheatsheet

- **Two pointers** for palindromes, reversal, "compare from both ends".
- **Sliding window + hash/counter** the moment you see "longest/shortest substring with property X".
- **Stack** for matching parentheses, decoding nested strings, any LIFO structure.
- **Hash by canonical key** for anagrams — sorted string OR count tuple, never sum of char codes.
- **Expand around center** beats DP for longest palindrome on most inputs (O(n²) time, O(1) space).
- **Length-prefix encoding** (`"5#hello"`) for serialising lists of strings — robust against any payload character.
- **`int(s, base)` is banned** in atoi-style problems; do it digit-by-digit and clamp to `INT_MAX/INT_MIN`.
- **String concatenation in a loop is O(n²)** in Python — accumulate in a list and `"".join()` at the end.
- **`ord(c) - ord('a')`** gives a 0–25 index for lowercase ASCII; the fastest "char hash" you can write.
- **KMP / Z-function** only if the interviewer asks for sub-O(nm) `strStr`. Otherwise the built-in `str.find` is fine.
