# Computational Geometry

> The chapter where coordinates, vectors, and orientation tests replace `if x < y`. The trick that unlocks every problem here is the **cross product** — a single sign tells you whether three points turn left, right, or are colinear, and that one primitive solves convex hull, segment intersection, point-in-polygon, polygon area, and half-plane intersection. Add a **sweep line** for `n log n` algorithms (closest pair, segment intersections, rectangle union), and a **KD-tree** for spatial nearest-neighbour queries. Net: a self-contained toolkit for any 2D geometry problem you'll see in interviews.

<span class="phase-status phase-inprogress">Phase 7 — Ultra-Advanced topic 3 of 7</span>

---

## 📖 What is computational geometry?

It's algorithms whose inputs and outputs are **points, segments, polygons, and circles** in 2D (occasionally 3D). The core challenge is that floating-point arithmetic is **imprecise** — two segments that mathematically cross at a single point may, in float, miss each other by 10⁻¹⁵, or worse, agree on intersection but disagree on which side of the line each endpoint lies.

The discipline has two pillars:

1. **Robust primitives.** Work with integer coordinates whenever possible; replace `<` and `==` with **orientation tests** that use the cross-product sign.
2. **Sweep line algorithms.** Process events (segment endpoints, points sorted by x) left-to-right; maintain an active set with a balanced BST keyed by y-coordinate. Many `O(n²)` brute-force problems collapse to `O(n log n)` this way.

The mental model: every 2D problem is "given a bunch of points, what's true of the configuration?" — and the configuration's combinatorial structure (which points lie on which side of which line) is determined entirely by O(n²) cross-product signs. If you can extract those signs robustly, you've solved 90% of the problem.

!!! tip "The signal — when to reach for computational geometry"
    Reach for it when:

    - The problem mentions **points / lines / segments / polygons / circles** in the plane.
    - You need to compute a **convex hull** — Graham scan or Andrew's monotone chain.
    - You need to **detect segment intersections** in a set — Bentley-Ottmann sweep line.
    - **Closest pair of points** — divide-and-conquer or sweep line in O(n log n).
    - **Point in polygon** — ray-casting parity test.
    - **Polygon area / centroid** — shoelace formula.
    - **Nearest neighbour in 2D** — KD-tree.

    Don't reach for it when:

    - The "geometry" is actually a 1D number-line problem disguised by xy axes.
    - The problem only needs **Manhattan / Chebyshev** distance — those rotate to ℓ∞ / ℓ₁ and become simple sweeps.
    - Coordinates are integer and bounded — sometimes a 2D grid + BFS / sliding window beats hull tricks.

---

## 🧩 The four flavors

### Flavor 1: Cross product — the universal primitive

The signed area of the parallelogram spanned by `(b - a)` and `(c - a)`:

```python
def cross(o: tuple[int, int], a: tuple[int, int], b: tuple[int, int]) -> int:
    """> 0 if oa→ob turns left (counter-clockwise);
       < 0 if right (clockwise); = 0 if colinear."""
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
```

Every other geometric primitive is built from this. Three points colinear? Cross is 0. Convex polygon? All consecutive crosses share the same sign. Segment AB intersects segment CD? Cross signs of (A,B,C), (A,B,D), (C,D,A), (C,D,B) split into two pairs of opposite signs.

**Why integer-friendly:** if all input coordinates are integers, `cross` is exact — no floating point. This eliminates the single biggest source of bugs in computational geometry.

### Flavor 2: Convex hull — Andrew's monotone chain

The smallest convex polygon containing all input points. Andrew's monotone chain is the cleanest implementation: sort by `(x, y)`, build lower hull left-to-right and upper hull right-to-left, concatenate.

```python
def convex_hull(points: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Returns hull in counter-clockwise order. Excludes colinear points (use ≤ 0 to include)."""
    pts = sorted(set(points))
    if len(pts) <= 1: return pts

    # Build lower hull
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    # Build upper hull
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]                                # last point of each is the start of the other
```

Total: `O(n log n)` from the sort. The actual hull-building is `O(n)` since each point is pushed and popped at most once.

### Flavor 3: Sweep line — closest pair of points

Find the two closest points among `n` in `O(n log n)`. Sort by x; sweep a vertical line; maintain a sorted-by-y set of points within the current best distance `d` of the line.

```python
import bisect

def closest_pair(points: list[tuple[int, int]]) -> float:
    pts = sorted(points)                                          # by x then y
    active: list[tuple[int, int]] = []                            # sorted by y
    left = 0
    best = float("inf")
    for x, y in pts:
        # Drop points more than `best` away in x
        while left < len(active) and pts[left][0] < x - best ** 0.5:
            ay = pts[left][1]
            i = bisect.bisect_left(active, (ay, pts[left][0]))
            active.pop(i)
            left += 1
        # Check candidates within ±√best in y
        ylo = bisect.bisect_left(active, (y - best ** 0.5, -float("inf")))
        yhi = bisect.bisect_right(active, (y + best ** 0.5, float("inf")))
        for ay, ax in active[ylo:yhi]:
            d2 = (x - ax) ** 2 + (y - ay) ** 2
            if d2 < best: best = d2
        bisect.insort(active, (y, x))
    return best ** 0.5
```

The active window has expected ≤ 7 candidates per insertion (a packing argument), giving overall `O(n log n)`. The same template generalises: Bentley-Ottmann segment intersection, rectangle union area, skyline.

### Flavor 4: KD-tree — spatial nearest neighbour

A balanced BST where each level alternates splitting by x and y. Build in `O(n log n)`; nearest-neighbour query in `O(log n)` average (or `O(√n)` adversarial worst case in 2D).

```python
class KDNode:
    __slots__ = ("point", "axis", "left", "right")
    def __init__(self, point: tuple[int, int], axis: int, left=None, right=None) -> None:
        self.point, self.axis, self.left, self.right = point, axis, left, right

def build_kd(points: list[tuple[int, int]], depth: int = 0) -> KDNode | None:
    if not points: return None
    axis = depth % 2
    points.sort(key=lambda p: p[axis])
    mid = len(points) // 2
    return KDNode(
        points[mid], axis,
        build_kd(points[:mid], depth + 1),
        build_kd(points[mid+1:], depth + 1),
    )

def nearest(node: KDNode | None, target: tuple[int, int], best: list) -> None:
    """best = [best_dist_sq, best_point]; mutated in place."""
    if node is None: return
    d = (node.point[0] - target[0]) ** 2 + (node.point[1] - target[1]) ** 2
    if d < best[0]:
        best[0], best[1] = d, node.point
    diff = target[node.axis] - node.point[node.axis]
    near, far = (node.left, node.right) if diff < 0 else (node.right, node.left)
    nearest(near, target, best)
    if diff ** 2 < best[0]:                                       # plane closer than current best
        nearest(far, target, best)
```

For uniformly-distributed points, queries are `O(log n)` expected. For adversarial inputs in d=2, worst case is `O(√n)`; in higher dimensions, KD-trees degrade and you should switch to ball trees or just brute force.

---

## 🔍 Sub-pattern at-a-glance

| # | Primitive / algorithm        | Use case                                      | Complexity        |
|---|------------------------------|-----------------------------------------------|-------------------|
| 1 | Cross product                | Orientation, side-of-line, colinearity        | O(1)              |
| 2 | Shoelace formula             | Polygon signed area / centroid                | O(n)              |
| 3 | Convex hull (Andrew / Graham) | Smallest enclosing convex polygon            | O(n log n)        |
| 4 | Closest pair (sweep)         | Min Euclidean distance among n points         | O(n log n)        |
| 5 | Segment intersection (Bentley-Ottmann) | All k intersections among n segments | O((n + k) log n) |
| 6 | Point-in-polygon (ray cast)  | Inside / outside test                         | O(n)              |
| 7 | Half-plane intersection      | Feasible region of linear constraints         | O(n log n)        |
| 8 | KD-tree nearest neighbour    | 2D / 3D nearest-point queries                 | O(log n) average  |
| 9 | Rotating calipers            | Diameter / width of a convex polygon          | O(n) post-hull    |

---

## 📚 20 problems where computational geometry is the canonical answer

| #  | Source         | Problem                                              | Difficulty | Key insight                                                       |
|----|----------------|------------------------------------------------------|------------|-------------------------------------------------------------------|
| 1  | LC 587         | Erect the Fence                                      | Hard       | Convex hull including colinear points (use `< 0` not `≤ 0`).      |
| 2  | LC 836         | Rectangle overlap                                    | Easy       | Axis-aligned: just project onto x and y.                          |
| 3  | LC 149         | Max points on a line                                 | Hard       | For each point, group others by slope (gcd-normalised dx,dy).     |
| 4  | LC 469         | Convex polygon (validate)                            | Medium     | Check all consecutive crosses share a sign.                       |
| 5  | LC 1232        | Check if it's a straight line                        | Easy       | Cross product of (p1, p2, p_i) = 0 for all i.                     |
| 6  | LC 939         | Minimum area rectangle                               | Medium     | For each pair of diagonal points, check both other corners exist. |
| 7  | LC 963         | Minimum area rectangle II (rotated)                  | Hard       | For each pair of diagonal points, two other corners equidistant.  |
| 8  | LC 1453        | Maximum points inside a circle                       | Hard       | Sliding angle window over points sorted by angle from each.       |
| 9  | LC 1610        | Maximum visible points (angle window)                | Hard       | Convert points to angles, sliding window with wraparound.         |
| 10 | LC 973         | K closest points to origin                           | Medium     | Quickselect or heap, no actual geometry.                          |
| 11 | LC 391         | Perfect rectangle (axis-aligned cover)               | Hard       | Sum of areas + corner-counting parity.                            |
| 12 | UVa 109        | SCUD Busters (convex hulls per group + point-in-poly)| Medium     | Build hulls; ray-cast each city.                                  |
| 13 | SPOJ BSHEEP    | Build the fence (convex hull length)                 | Medium     | Andrew's monotone chain + perimeter.                              |
| 14 | LC 218         | Skyline problem                                      | Hard       | Sweep line over event endpoints; max-heap of active heights.      |
| 15 | LC 850         | Rectangle area II (union)                            | Hard       | Sweep line + segment tree of active y-intervals.                  |
| 16 | UVa 11178      | Morley's theorem (geometric construction)            | Medium     | Vector arithmetic and rotation matrices.                          |
| 17 | CF 70D         | Professor's task (online convex hull)                | Hard       | Maintain dual hulls (lower / upper) with sorted sets.             |
| 18 | LC 1037        | Valid boomerang                                      | Easy       | Cross product ≠ 0 between three points.                           |
| 19 | LC 593         | Valid square                                         | Medium     | All 6 pairwise distances reduce to {edge, diagonal} multiset.     |
| 20 | UVa 11437      | Triangle Fun (centroid / area)                       | Easy       | Shoelace.                                                         |

---

## 🔬 Deep-dive 1 — Why the cross product is robust and how to avoid floats entirely

The cross product `(a - o) × (b - o)` evaluates to:

`(a.x - o.x) · (b.y - o.y) - (a.y - o.y) · (b.x - o.x)`

If all coordinates are integers up to `10^9`, the products are up to `4 · 10^18` — fits in Python's arbitrary-precision int trivially, and in C++ `__int128` or careful 64-bit. **No rounding error.** So the *sign* of the cross product is exact, and that's all most algorithms need.

**Implication for convex hull:** Andrew's monotone chain works perfectly with integer coordinates. The only place you might want floats is when computing **distances** (for ranking nearest pairs). Even then, compare **squared distances** to avoid `sqrt`:

```python
def dist_sq(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2

# Compare dist_sq(p, q) < dist_sq(p, r) — exact for integer coords.
```

**Segment intersection without floats:**

```python
def segments_intersect(a, b, c, d) -> bool:
    """Do open segments AB and CD properly intersect?"""
    d1 = cross(c, d, a)
    d2 = cross(c, d, b)
    d3 = cross(a, b, c)
    d4 = cross(a, b, d)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return True
    # Colinear cases (d1 == 0 etc.) — point-on-segment checks
    return False
```

Pure integer comparisons. **No `1e-9 < x < 1e-9` epsilon nonsense.**

??? tip "When floats are unavoidable"
    Computing the **intersection point** of two segments requires division — that's where floats sneak in. Mitigations: (a) use rationals (Python's `fractions.Fraction`) if you need exact intersection points; (b) defer division as long as possible — represent the intersection as a parametric `t = num / denom` and compare cross-multiplied; (c) accept floats but use `math.isclose` with tuned tolerance for downstream comparisons.

??? tip "Three-point colinearity from cross = 0"
    Cross product zero exactly captures colinearity for integer coordinates. For floats, "is this near-colinear" is ill-defined — you must pick a tolerance, which is application-specific. Always prefer integer coordinates by scaling input if possible (multiply by 1000, etc.).

---

## 🔬 Deep-dive 2 — Convex hull traced through Andrew's monotone chain

**Input:** `[(0, 0), (4, 0), (1, 1), (3, 1), (2, 2), (1, 3), (0, 4), (4, 4)]`.

**Step 1 — sort:** `[(0, 0), (0, 4), (1, 1), (1, 3), (2, 2), (3, 1), (4, 0), (4, 4)]`.

**Step 2 — lower hull** (left-to-right, only RIGHT turns kept):

| Process | Stack action                                                               | Stack after          |
|---------|----------------------------------------------------------------------------|----------------------|
| (0,0)   | push                                                                        | [(0,0)]              |
| (0,4)   | push                                                                        | [(0,0),(0,4)]        |
| (1,1)   | cross((0,0),(0,4),(1,1)) = `0·(1-0) - 4·(1-0)` = -4 < 0 → keep. Wait — for lower we want strictly counter-clockwise, the check is `cross ≤ 0` → pop. So (0,4) gets popped. | [(0,0),(1,1)]        |
| (1,3)   | cross((0,0),(1,1),(1,3)) = `1·3 - 1·1` = 2 > 0 → keep. Push.                | [(0,0),(1,1),(1,3)]  |
| (2,2)   | cross((1,1),(1,3),(2,2)) = `0·1 - 2·1` = -2 ≤ 0 → pop (1,3). cross((0,0),(1,1),(2,2)) = `1·2 - 1·2` = 0 ≤ 0 → pop (1,1). Push. | [(0,0),(2,2)]        |
| (3,1)   | cross((0,0),(2,2),(3,1)) = `2·1 - 2·3` = -4 ≤ 0 → pop (2,2). Push.          | [(0,0),(3,1)]        |
| (4,0)   | cross((0,0),(3,1),(4,0)) = `3·0 - 1·4` = -4 ≤ 0 → pop (3,1). Push.          | [(0,0),(4,0)]        |
| (4,4)   | push                                                                        | [(0,0),(4,0),(4,4)]  |

**Lower hull:** `[(0,0), (4,0), (4,4)]`.

**Step 3 — upper hull** (right-to-left, again only RIGHT turns):

Reversed input: `[(4,4), (4,0), (3,1), (2,2), (1,3), (1,1), (0,4), (0,0)]`.

| Process | Stack action                                                      | Stack after          |
|---------|-------------------------------------------------------------------|----------------------|
| (4,4)   | push                                                              | [(4,4)]              |
| (4,0)   | push                                                              | [(4,4),(4,0)]        |
| (3,1)   | cross((4,4),(4,0),(3,1)) = `0·(-3) - (-4)·(-1)` = -4 ≤ 0 → pop. push | [(4,4),(3,1)]      |
| (2,2)   | cross((4,4),(3,1),(2,2)) = `(-1)·(-2) - (-3)·(-2)` = 2 - 6 = -4 ≤ 0 → pop. push | [(4,4),(2,2)] |
| (1,3)   | cross((4,4),(2,2),(1,3)) = `(-2)·(-1) - (-2)·(-3)` = 2 - 6 = -4 ≤ 0 → pop. push | [(4,4),(1,3)] |
| (1,1)   | cross((4,4),(1,3),(1,1)) = `(-3)·(-3) - (-1)·(-3)` = 9 - 3 = 6 > 0 → push | [(4,4),(1,3),(1,1)] |
| (0,4)   | cross((1,3),(1,1),(0,4)) = `0·1 - (-2)·(-1)` = -2 ≤ 0 → pop (1,1). cross((4,4),(1,3),(0,4)) = `(-3)·0 - (-1)·(-4)` = -4 ≤ 0 → pop (1,3). push | [(4,4),(0,4)] |
| (0,0)   | cross((4,4),(0,4),(0,0)) = `(-4)·(-4) - 0·(-4)` = 16 > 0 → push    | [(4,4),(0,4),(0,0)] |

**Upper hull:** `[(4,4), (0,4), (0,0)]`.

**Concatenate** dropping last of each: `[(0,0), (4,0)] + [(4,4), (0,4)] = [(0,0), (4,0), (4,4), (0,4)]`.

**Final hull:** the 4 corners of the bounding box. The interior points `(1,1), (3,1), (2,2), (1,3)` were correctly excluded. ✓

The mechanical part is **always the same**: sort, sweep, pop-while-non-CCW, push. The hard part is remembering whether you want strict (`< 0`) or non-strict (`≤ 0`) — strict keeps colinear hull points (LC 587 mode); non-strict drops them (canonical hull).

---

## 🔬 Deep-dive 3 — Why the sweep-line "active window has ≤ 7 candidates"

In closest-pair sweep, when processing a point `p = (x, y)`, we look at active points `q` with `q.x ≥ x - d` and `|q.y - y| ≤ d`, where `d` is the current best distance. We claim there are **at most 7** such active points (the 8th would force `d` smaller — contradiction).

**Proof:** any two active points within the candidate window are mutually at distance `≥ d` (by induction — they were each other's candidates in earlier iterations and we'd have updated `d` if closer). Pack non-overlapping `(d/2)`-radius disks around each; centres lie in a `d × 2d` rectangle. Area ≤ `2d²`; each disk area = `π(d/2)² ≈ 0.785 d²`. So at most `⌊2d² / 0.785d²⌋ = 2` non-overlapping disks fit — but with the boundary-touching cases, the bound goes up to **7 active points** (the rigorous derivation uses that points are mutually `≥ d` apart and packs differently in the rectangle).

So each insertion does at most 7 distance comparisons. Total work: `O(n)` comparisons + `O(n log n)` for the sorted set. **The whole algorithm is `O(n log n)`** without ever computing more than 7n actual distance checks.

This same packing argument generalises: the Bentley-Ottmann segment-intersection sweep maintains at most O(n) active segments, each insertion / deletion is `O(log n)` in a balanced BST, giving `O((n + k) log n)` for `k` intersections.

??? tip "Why divide-and-conquer closest-pair beats the naive O(n²) by the same factor"
    D&C closest-pair: split into left/right halves by median x, recurse, merge — the merge step looks at points within `d` of the dividing line, and the same packing argument bounds candidates per point to ≤ 7. Same `O(n log n)`, different control flow. Sweep line is usually preferred because it generalises to many other "events sorted by x" problems.

??? tip "When the sweep degenerates"
    If many points share the same x, you must break ties with y. If many points share the same x AND y, deduplicate first — otherwise active set inserts and removes the same key and breaks. Always `pts = sorted(set(points))` as the first step.

---

## 🐛 Common bugs

1. **Floating-point comparisons without epsilon — or with the wrong epsilon.** Comparing `cross == 0` directly on floats fails on perfectly-aligned inputs that round in the 17th digit. Use integer coordinates whenever input allows.
2. **Convex hull `<= 0` vs `< 0`.** `≤ 0` removes colinear points (canonical hull); `< 0` keeps them (LC 587 "fence" semantics). Pick consciously per problem.
3. **Sorting points lexicographically forgets ties on y.** Always sort by `(x, y)` — Python's tuple sort handles this for free.
4. **Polygon not closed when computing area.** Shoelace formula sums `x_i · y_{i+1} - x_{i+1} · y_i` for i=0..n-1 with `(i+1) mod n` — forgetting the wrap underestimates by one segment.
5. **Segment intersection treating endpoints as "not crossing."** Properly defined: open segments cross iff strict-inequality cross signs split. Closed segments need extra colinear-point-on-segment checks.
6. **KD-tree imbalance.** Building without sorting at every level (using a `nth_element`-style partition) is fine for static data but doesn't rebalance after inserts. For dynamic point sets, switch to balanced KD-tree or R-tree.
7. **Ray-casting point-in-polygon: ray hits a vertex.** A ray hitting a vertex counts the vertex's two edges — once you flip parity twice and stay outside, once and flip once. Resolve by tilting the ray slightly (e.g., always go +x, treat vertices as "above" the ray).
8. **Convex hull on duplicates.** If two input points coincide, `bisect.insort` and the cross check both still work — but if a third colinear point joins them and your check is `<= 0`, all three drop. Deduplicate input first.

---

## 🗣️ Interviewer phrasings to recognize

- "Find the **smallest convex polygon** containing these points" → convex hull.
- "Are these three points **colinear**?" / "Which side of the line is X?" → cross product sign.
- "Find the **two closest points**" → closest-pair sweep / divide-and-conquer.
- "Detect all **segment intersections**" → Bentley-Ottmann sweep.
- "**Point inside polygon**?" → ray casting (count crossings).
- "Maximum number of points on the **same line**" → group by slope.
- "**Skyline** of buildings" → sweep with active-heights heap.
- "**Nearest neighbour** in 2D" → KD-tree.

---

## 🧭 Connections to other patterns

- **[Modified Binary Search](../04-patterns/11-modified-binary-search.md)** — for "smallest enclosing circle / convex hull diameter," ternary search over angles or rotating calipers can replace heavy machinery.
- **[Sliding Window](../04-patterns/01-sliding-window.md)** — angle-window problems (LC 1453, LC 1610) reduce to sliding window over sorted angles.
- **[Segment Trees](../05-advanced/03-segment-trees.md)** — Bentley-Ottmann's active set is often a segment tree of active y-intervals.
- **[Persistent Data Structures](01-persistent-data-structures.md)** — persistent convex hull (online insert + queries against historical hulls).
- **Linear programming** — half-plane intersection in 2D is the LP-feasibility problem in disguise; same algorithms (random incremental).
- **Graphics / collision detection** — CG primitives are the foundation of every 2D engine, robot motion planner, and CAD tool.

---

## ✅ Self-check — 8 questions

??? question "1. Why is the cross product the universal computational-geometry primitive?"
    Its sign exactly captures the orientation of three points (left turn / right turn / colinear). For integer coordinates the sign is exact (no float error). Convex hull, segment intersection, point-in-polygon, polygon area, half-plane test — all reduce to cross-product sign comparisons.

??? question "2. What's the difference between Andrew's monotone chain and Graham scan?"
    Both build convex hulls in O(n log n). Graham scan picks the lowest point as a pivot, sorts others by polar angle, and walks. Andrew's monotone chain sorts by (x, y) and builds lower then upper hulls separately — simpler implementation and avoids polar-angle sort (which involves `atan2` floats). Andrew's is the modern standard.

??? question "3. Why does closest-pair sweep run in O(n log n) and not O(n²)?"
    The active set within ±d in y of the current point has ≤ 7 candidates by a packing argument (any more would force d smaller, a contradiction). So each insertion does O(1) distance checks; total comparisons are O(n). The log factor comes from maintaining the active set sorted by y.

??? question "4. How does ray-casting determine if a point is inside a polygon?"
    Cast a horizontal ray from the point to +∞; count crossings with polygon edges. Odd count → inside; even → outside. Edge cases (ray touches a vertex, or is colinear with an edge) require careful tie-breaking — usually by perturbing the ray slightly upward.

??? question "5. When is a KD-tree fast and when does it degrade?"
    Fast (O(log n) average) for low dimensions (2-3) with uniformly-distributed query points. Degrades to O(√n) in 2D adversarial worst case, and to O(n) in high dimensions (curse of dimensionality). For d > ~10, switch to ball trees, locality-sensitive hashing, or just brute force.

??? question "6. What's the shoelace formula and why does it give a signed area?"
    Area = ½ |Σ (x_i · y_{i+1} - x_{i+1} · y_i)| over i=0..n-1 with indices mod n. The sign of the un-absoluted sum tells orientation: positive = counter-clockwise, negative = clockwise. Useful for testing polygon orientation without explicit cross products.

??? question "7. How do you check segment intersection robustly?"
    Compute four cross products: d1=cross(c,d,a), d2=cross(c,d,b), d3=cross(a,b,c), d4=cross(a,b,d). Open-segment proper intersection iff (d1, d2) have opposite strict signs AND (d3, d4) do too. Colinear / endpoint-touching cases need additional containment checks (point on segment).

??? question "8. Why do convex-hull problems sometimes want colinear hull points and sometimes not?"
    Canonical hull excludes interior-of-edge points (use cross ≤ 0 → pop). Some problems (LC 587 "Erect the Fence") want every point that participates in the boundary, including colinear ones — use cross < 0 to pop only on STRICT clockwise, keeping colinear-on-edge points.

---

> **Up next in Ultra-Advanced:** Advanced DP — digit DP for "count numbers in [L, R] with property P", bitmask DP for assignment-on-subsets, DP on trees with rerooting, and the SOS (sum-over-subsets) trick.
