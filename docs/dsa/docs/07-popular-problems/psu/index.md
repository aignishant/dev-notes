# PSU Companies — consolidated prep guide

> One page covering Indian PSUs (Public Sector Undertakings) and government technical / financial roles: ISRO, DRDO, BARC, ECIL, BEL, HAL, BHEL, NTPC, ONGC, IOCL, GAIL, NHAI, RBI Grade B, SEBI Grade A.
>
> Most select via **GATE score + interview**, with some running their own written exam.

<span class="company-tag">ISRO</span> <span class="company-tag">DRDO</span> <span class="company-tag">BARC</span> <span class="company-tag">ECIL</span> <span class="company-tag">BEL</span> <span class="company-tag">HAL</span> <span class="company-tag">BHEL</span> <span class="company-tag">NTPC</span> <span class="company-tag">ONGC</span> <span class="company-tag">IOCL</span> <span class="company-tag">GAIL</span> <span class="company-tag">NHAI</span> <span class="company-tag">RBI Grade B</span> <span class="company-tag">SEBI Grade A</span>

<span class="phase-status phase-inprogress">Phase 8 — PSU consolidated</span>

---

## 🏢 What interviewing at PSUs is like

Two broad routes — pick whichever applies:

### Route A — GATE-based (most PSUs)

Used by: BHEL, NTPC, ONGC, IOCL, GAIL, NHAI, HPCL, BPCL, GSPL, NLC, Power Grid, NHPC, MDL …

| Stage | Detail |
|---|---|
| **GATE score** | Computed via your subject paper (CS / EC / EE / ME …). Cutoffs published per company. |
| **Document verification** | Originals — degree, GATE scorecard, caste / EWS certs, photo IDs. |
| **Group discussion** (some only) | 10-15 min on a current-affairs / technical topic. |
| **Personal interview** | 20-40 min. Subject + project + general awareness. |

### Route B — Own written exam + interview

Used by: ISRO (ICRB), DRDO (CEPTAM, RAC), BARC (OCES / DGFS), ECIL (GET), BEL (PE), HAL (MT), RBI Grade B, SEBI Grade A.

| Stage | Detail |
|---|---|
| **Written exam** | Subject + aptitude. Pattern varies. |
| **Interview** | Subject + project + situational. RBI / SEBI add finance + economics + English essay. |

**Key facts**:
- **No coding rounds**. PSUs hire on subject knowledge + personality.
- **Pay is moderate but stable**; perks (housing, medical, pension) are large.
- **Service bond** common: 2-5 years, ₹2-10L penalty.
- Selection is **strictly merit-based** but reservation rosters apply (UR / OBC / SC / ST / EWS / PwD).

---

## 🎯 What PSUs test

| Signal | Where | How to show |
|---|---|---|
| Subject mastery | Written + interview | Textbook-deep, not LeetCode. |
| Project depth | Interview | One project, 5 minutes deep, with diagrams ready. |
| General awareness | Interview | Current affairs, your home state, the company itself. |
| Composure + manners | Interview | Suit + tie. "Sir / madam". Don't sit until invited. |

---

## 🧩 What CS subjects to drill (for CS / IT branch PSUs)

Same coverage as **GATE CS**. Concise areas:

| Subject | What gets tested |
|---|---|
| **DSA + Algorithms** | Arrays, linked lists, trees, graphs, sorting, searching, recursion, DP basics. **No advanced** (no segment trees etc.) |
| **DBMS** | ER → relational, normalization (1NF–BCNF), SQL queries, transactions, ACID, joins. |
| **Operating Systems** | Process / thread, scheduling (FCFS, SJF, RR), deadlock 4 conditions, paging, page-replacement (LRU, FIFO), banker's algorithm. |
| **Computer Networks** | OSI 7 layers, TCP / UDP, 3-way handshake, sliding window, IP routing basics, DNS. |
| **TOC + Compilers** | Regex → DFA / NFA, CFG, parsing (LL, LR), three-address code. |
| **Computer Architecture** | Pipelining stages, hazards, cache, cache mapping, RISC vs CISC. |
| **Digital Logic** | K-map simplification, MUX / DEMUX, flip-flops, sequential vs combinational. |
| **Discrete Math + DM** | Sets, relations, graphs, propositional logic. |

---

## 📋 The 50 prep items

### DSA / Algorithms (15) — basics done well

| # | Topic | Most-asked variant |
|---|---|---|
| 1 | Reverse a linked list | iterative + recursive |
| 2 | Detect cycle in linked list | Floyd's |
| 3 | Binary tree traversals | inorder / preorder / postorder + level-order |
| 4 | BST insert + delete | three delete cases |
| 5 | Heap basics | heapify, build-heap |
| 6 | BFS / DFS on graph | adjacency list + matrix |
| 7 | Dijkstra | with min-heap |
| 8 | Prim's / Kruskal's MST | trade-offs |
| 9 | Topological sort | DFS + Kahn's |
| 10 | Quick sort / merge sort | partition + merge step |
| 11 | Binary search variants | first / last occurrence |
| 12 | 0/1 Knapsack | 2D DP table |
| 13 | LIS | O(N²) DP |
| 14 | Floyd-Warshall | 3-loop, when to use |
| 15 | Hash table | chaining + open addressing |

### DBMS (10)

| # | Topic | Most-asked |
|---|---|---|
| 1 | Normalization 1NF / 2NF / 3NF / BCNF | converting tables |
| 2 | ER → relational | weak entity, ISA |
| 3 | SQL joins | inner / left / right / cross |
| 4 | Aggregate + GROUP BY + HAVING | numeric examples |
| 5 | Transactions + ACID | examples |
| 6 | 2PL + serializability | conflict + view |
| 7 | Indexing | B+ tree, when index hurts |
| 8 | Functional dependency | closure, candidate keys |
| 9 | Lossless decomposition | with proof |
| 10 | Recovery | undo / redo, log-based |

### OS (8)

| # | Topic | Most-asked |
|---|---|---|
| 1 | Process vs thread | context switch cost |
| 2 | Scheduling: FCFS / SJF / RR / Priority | Gantt chart calc |
| 3 | Critical section | Peterson's / semaphores |
| 4 | Deadlock | 4 conditions; banker's algo |
| 5 | Paging | TLB + page table |
| 6 | Page replacement: LRU / FIFO / Optimal | trace through reference string |
| 7 | Disk scheduling: FCFS / SCAN / C-SCAN | head movement |
| 8 | File system | inode, FAT, journaling |

### Networks (7)

| # | Topic | Most-asked |
|---|---|---|
| 1 | OSI 7 layers + TCP/IP 4 layers | mapping |
| 2 | TCP 3-way handshake + termination | SYN / ACK / FIN |
| 3 | TCP vs UDP | when to choose |
| 4 | Sliding window | window size, sequence numbers |
| 5 | Stop-and-wait + Go-back-N + Selective Repeat | pipelining trade-offs |
| 6 | IP addressing + subnetting | CIDR, masks |
| 7 | Routing: distance vector vs link state | RIP vs OSPF |

### Architecture / Digital (5)

| # | Topic | Most-asked |
|---|---|---|
| 1 | Pipelining + hazards | data / control / structural |
| 2 | Cache mapping | direct / set-associative / fully |
| 3 | K-map | 3-var, 4-var |
| 4 | Flip-flops | D / JK / T |
| 5 | MUX / DEMUX | building larger MUX from smaller |

### Project + Personality (5)

| # | Question | Best-answer style |
|---|---|---|
| 1 | "Tell me about yourself." | Background → academic highlight → project → why this PSU |
| 2 | "Walk me through your project." | Slide-style: problem → architecture → tech → role → outcome |
| 3 | "Why this PSU?" | Cite mission, sector, location, scale. NOT just "stability". |
| 4 | "Why CSE / IT / EC / EE / ME?" | Genuine reason backed by an example |
| 5 | "What do you know about <our company>?" | Founded year, headquarters, latest news, key projects, scale |

---

## 🔬 Three deep-dives (most-asked technical concepts)

### Deep-dive 1 — Bankers Algorithm (deadlock avoidance)

??? question "Story: 5 processes, 3 resource types. Decide if a request is safe."

    Maintain `available`, `max[i]`, `allocation[i]`, `need[i] = max[i] - allocation[i]`. A state is **safe** if there's some sequence in which every process can finish given the current `available`.

```python
def is_safe(available: list[int], allocation: list[list[int]], maximum: list[list[int]]) -> bool:
    n = len(allocation)
    m = len(available)
    work = available[:]
    finish = [False] * n
    need = [[maximum[i][j] - allocation[i][j] for j in range(m)] for i in range(n)]

    while True:
        progressed = False
        for i in range(n):
            if not finish[i] and all(need[i][j] <= work[j] for j in range(m)):
                for j in range(m):
                    work[j] += allocation[i][j]
                finish[i] = True
                progressed = True
        if not progressed:
            break
    return all(finish)
```

??? abstract "Complexity"

    O(N² · M). Used at decision time, not in production schedulers.

??? tip "Interview follow-up: 'why is this rarely used in real OSes?'"

    Requires processes to declare maximum resource needs in advance — almost no app does this. In practice, OSes use deadlock **detection + recovery** (kill a victim) instead of avoidance.

---

### Deep-dive 2 — TCP 3-Way Handshake

??? question "Story: explain how a TCP connection is established and what each flag carries."

    1. **Client → Server**: `SYN`, seq = X
    2. **Server → Client**: `SYN, ACK`, seq = Y, ack = X+1
    3. **Client → Server**: `ACK`, seq = X+1, ack = Y+1

    Both sides have proof the other can send AND receive (each direction's seq has been ACKed). Connection is now **ESTABLISHED**.

??? abstract "Why three messages?"

    Two messages can confirm one direction. Three confirm both. Without the final `ACK`, the server doesn't know its `SYN-ACK` was received.

??? tip "Interview follow-up: 'four-way close, why?'"

    `FIN` from each side is independent — A might still want to send data after B has finished. Hence: A→B `FIN`, B→A `ACK`, B→A `FIN` (when B is done), A→B `ACK`.

---

### Deep-dive 3 — LRU Page Replacement

??? question "Story: trace through a reference string with LRU, page frames = 3."

    Reference: `1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5`. Frames: 3.

| Step | Ref | Frames | Hit / Miss |
|---|---|---|---|
| 1 | 1 | [1] | Miss |
| 2 | 2 | [1, 2] | Miss |
| 3 | 3 | [1, 2, 3] | Miss |
| 4 | 4 | [2, 3, 4] (evict 1) | Miss |
| 5 | 1 | [3, 4, 1] (evict 2) | Miss |
| 6 | 2 | [4, 1, 2] (evict 3) | Miss |
| 7 | 5 | [1, 2, 5] (evict 4) | Miss |
| 8 | 1 | [2, 5, 1] | Hit |
| 9 | 2 | [5, 1, 2] | Hit |
| 10 | 3 | [1, 2, 3] (evict 5) | Miss |
| 11 | 4 | [2, 3, 4] (evict 1) | Miss |
| 12 | 5 | [3, 4, 5] (evict 2) | Miss |

**Misses = 10, hits = 2**.

??? tip "Interview follow-up: 'implement LRU in O(1)'"

    Hash map + doubly-linked list. Hash maps key → DLL node. On access, unlink + push to head. On miss with full cache, pop tail. (Same pattern as the LRU Cache LeetCode problem.)

---

## 🛡️ Day-of tips

- **Dress code**: formal. Suit / blazer + tie for men; saree or formal salwar / business suit for women. Nervousness aside, attire alone improves first impression.
- **Address etiquette**: "Sir" / "Madam" — yes, every time. Don't first-name interviewers.
- **Project depth, not breadth**: pick ONE project; know it cold; have a one-page diagram you can mentally redraw.
- **Current affairs**: skim *The Hindu* or PIB for two weeks. Be ready for "tell me about a recent technology in your field".
- **Know the org**: founding year, headquarters, current chairman / CMD, recent flagship project. 5 minutes on Wikipedia is enough.
- **GATE-based slot**: do NOT skip document verification — missing a single document cancels candidacy.

---

## 📦 PSU-specific notes

| PSU | Distinguishing feature |
|---|---|
| **ISRO (ICRB)** | Own subject-only written exam. No GATE. Engineering-discipline strong. |
| **DRDO (CEPTAM / RAC)** | Multi-tier; tier-2 subject-specific. RAC is for scientists. |
| **BARC (OCES / DGFS)** | OCES = own selection test → 1-year training. Highly competitive. |
| **ECIL** | GATE-based for GET; sometimes own written. Defence electronics. |
| **BEL** | Probationary engineer via GATE. Defence + civil avionics. |
| **HAL** | Management Trainee via GATE. Aerospace. |
| **BHEL / NTPC / ONGC / IOCL / GAIL / NHAI** | All standard GATE-based; cutoffs vary year to year. |
| **RBI Grade B** | Three-phase: prelims → mains (essay + finance + economics + management) → interview. Distinct prep. |
| **SEBI Grade A** | Similar to RBI Grade B, with securities-law focus. |
| **NHAI** | GATE-based; civil engineering bias. |
