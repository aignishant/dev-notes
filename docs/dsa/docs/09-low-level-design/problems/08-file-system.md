# Design an In-Memory File System

> The Composite-pattern interview. A tree of files and folders that supports `mkdir`, `ls`, `cat`, `addContent`. Asked at Google, Meta, Amazon — and LeetCode 588 / 1166.

<span class="phase-status phase-done">Phase 13 — classic LLD</span>

---

## 🎤 Problem

> *"Design an in-memory file system. Support: `mkdir(path)`, `ls(path)` (lists if dir, returns filename if file), `addContentToFile(path, content)`, `readContentFromFile(path)`. Then extend: `rm`, `mv`, search, permissions, snapshots."*

A 30-45 minute LLD round. Interviewer expects:

1. **Tree representation** — files and folders sharing a parent type.
2. **Path parsing** as a separate concern.
3. **Composite pattern** explicitly named.
4. **Extensions**: permissions, soft links, COW snapshots.

---

## ❓ Clarifying questions

1. **Path format?** Unix-style `/foo/bar` or Windows `C:\\…`?
2. **Symlinks?** In v1?
3. **Permissions?** rwx? Owners?
4. **File metadata?** Created/modified timestamps? Size?
5. **Concurrency?** Multi-threaded access?
6. **Persistence?** Pure in-memory or eventual disk write-through?
7. **Search?** By name? Content? Glob?

**Default assumptions**:

- Unix-style `/`-separated paths.
- v1: `mkdir`, `ls`, `addContent`, `readContent`. v2 extensions later.
- No symlinks / permissions in v1.
- Single-threaded core; mention thread-safety strategy.

---

## 🏛️ Class design — the Composite pattern

A **`Node`** abstract base. **`File`** and **`Directory`** both extend it; `Directory` holds a `dict[name, Node]`. Same interface, recursive structure → Composite.

### Base + concrete types

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import threading


class Node(ABC):
    """Common base for File and Directory."""

    def __init__(self, name: str, parent: "Directory | None" = None):
        self.name = name
        self.parent = parent
        self.created_at = datetime.utcnow()
        self.modified_at = self.created_at

    @property
    def path(self) -> str:
        if self.parent is None:               # root
            return "/"
        parent_path = self.parent.path
        return parent_path + ("" if parent_path == "/" else "/") + self.name

    @abstractmethod
    def is_dir(self) -> bool: ...


class File(Node):
    def __init__(self, name: str, parent: "Directory"):
        super().__init__(name, parent)
        self.content: str = ""

    def is_dir(self) -> bool:
        return False

    def append(self, text: str):
        self.content += text
        self.modified_at = datetime.utcnow()

    def read(self) -> str:
        return self.content


class Directory(Node):
    def __init__(self, name: str, parent: "Directory | None" = None):
        super().__init__(name, parent)
        self.children: dict[str, Node] = {}

    def is_dir(self) -> bool:
        return True

    def add(self, node: Node):
        if node.name in self.children:
            raise FileExistsError(node.path)
        self.children[node.name] = node
        node.parent = self
        self.modified_at = datetime.utcnow()

    def remove(self, name: str) -> Node:
        node = self.children.pop(name)
        self.modified_at = datetime.utcnow()
        return node

    def list_names(self) -> list[str]:
        return sorted(self.children)
```

### Path parser (single responsibility)

```python
class PathParser:
    @staticmethod
    def split(path: str) -> list[str]:
        """'/a/b/c' → ['a', 'b', 'c']; '/' → []."""
        if not path.startswith("/"):
            raise ValueError("paths must start with /")
        parts = [p for p in path.split("/") if p]
        for p in parts:
            if p in ("", ".", ".."):
                raise ValueError(f"invalid path component: {p}")
        return parts
```

### The file system (Facade)

```python
class FileSystem:
    def __init__(self):
        self.root = Directory("/")
        self._lock = threading.RLock()

    # --- public API ---

    def mkdir(self, path: str):
        with self._lock:
            parts = PathParser.split(path)
            cur = self.root
            for p in parts:
                if p not in cur.children:
                    new = Directory(p, parent=cur)
                    cur.add(new)
                cur = cur.children[p]
                if not cur.is_dir():
                    raise NotADirectoryError(cur.path)

    def ls(self, path: str) -> list[str]:
        with self._lock:
            node = self._resolve(path)
            if node.is_dir():
                return node.list_names()
            return [node.name]

    def add_content(self, path: str, content: str):
        with self._lock:
            parts = PathParser.split(path)
            if not parts:
                raise IsADirectoryError("/")
            *dir_parts, fname = parts
            parent = self._resolve("/" + "/".join(dir_parts)) if dir_parts else self.root
            if not parent.is_dir():
                raise NotADirectoryError(parent.path)
            assert isinstance(parent, Directory)
            existing = parent.children.get(fname)
            if existing is None:
                f = File(fname, parent=parent)
                parent.add(f)
                f.append(content)
            elif isinstance(existing, File):
                existing.append(content)
            else:
                raise IsADirectoryError(existing.path)

    def read(self, path: str) -> str:
        with self._lock:
            node = self._resolve(path)
            if node.is_dir():
                raise IsADirectoryError(path)
            assert isinstance(node, File)
            return node.read()

    # --- helpers ---

    def _resolve(self, path: str) -> Node:
        cur: Node = self.root
        for p in PathParser.split(path):
            if not isinstance(cur, Directory) or p not in cur.children:
                raise FileNotFoundError(path)
            cur = cur.children[p]
        return cur
```

---

## 🧪 Walkthrough

```python
fs = FileSystem()

fs.mkdir("/home/alice")
fs.mkdir("/home/bob")

fs.add_content("/home/alice/notes.txt", "buy milk\n")
fs.add_content("/home/alice/notes.txt", "buy bread\n")    # appends

print(fs.ls("/home"))                  # ['alice', 'bob']
print(fs.ls("/home/alice/notes.txt"))  # ['notes.txt'] — single name
print(fs.read("/home/alice/notes.txt"))
# buy milk
# buy bread
```

---

## 🎯 Patterns + SOLID applied

| Decision | Pattern / principle |
|---|---|
| `Node` ABC + `File` / `Directory` | **Composite** — uniform tree |
| `PathParser` separate from FS | **SRP** + testable |
| `FileSystem` is the public surface | **Facade** |
| `add_content` is idempotent on missing file | Convenience matches POSIX |
| `mkdir -p` semantics | Materialise full path (matches LeetCode 588) |

---

## 🚀 Extensions

??? question "`rm` and `rmdir`?"

    `rm`: locate + remove from parent. `rmdir`: only if empty. `rm -r`: recursive — depth-first delete to free child references explicitly (helps GC in long-lived processes).

??? question "`mv` (rename / move)?"

    Resolve src + dest's parent. Detach from src parent (`remove`), update name, attach to dest parent (`add`). Reject mv-into-descendant (cycle prevention).

??? question "Symbolic links?"

    `Symlink(Node)` with `target_path: str`. Resolution dereferences on access; track depth to prevent infinite loops (POSIX caps at 40).

??? question "Permissions (rwx)?"

    Each `Node` carries `(owner, group, mode_int)`. On every op, check current user's effective permissions. **Never trust the caller** — wrap with auth middleware.

??? question "Snapshots / copy-on-write?"

    Each modification clones the path from leaf to root. Old root remains valid → constant-time snapshot, lazy copying. Same trick as Git's tree objects.

??? question "Concurrent access?"

    Coarse `RLock` (shown above) is fine for v1. For high concurrency: per-directory locks + sorted lock acquisition order (lock parent before child) to prevent deadlock.

??? question "Search by name / content?"

    BFS/DFS the tree. For content search, read each `File.content`. For scale: maintain an inverted index — `word → set[file_id]` updated on every `add_content`.

??? question "Persistence?"

    Serialise the tree as JSON / msgpack on `flush()`. Or add a write-through layer that mirrors operations to disk. For crash safety: WAL (write-ahead log).

---

## ⏱️ Pacing

| Minute | What |
|---|---|
| 0–3   | Clarifying questions. |
| 3–10  | Class diagram: Node / File / Directory + Composite. |
| 10–30 | Code: nodes, FS facade, path parser. |
| 30–40 | Extension: `rm`, snapshots, or permissions. |
| 40–45 | Q&A; concurrency strategy. |

---

## 🪤 Common mistakes

??? warning "One Node class with `is_directory: bool` flag"

    Every method becomes `if self.is_directory: …`. The whole point of Composite is dispatch via type. Use ABC.

??? warning "Path parsing inline in every method"

    DRY: `PathParser.split` once, reuse. Bonus: handles edge cases (`//`, trailing slash) in one place.

??? warning "Storing parent path as a string on every node"

    Forces O(n) updates on `mv`. Store `parent: Node` reference; compute path on demand.

??? warning "`os.path.join` everywhere"

    The interviewer is checking decomposition, not stdlib knowledge. Build it yourself.

??? warning "Forgetting modified_at updates"

    Real file systems track this; interviewers notice when you mention it but skip it on `add_content`.

---

## ➡️ Where this connects

- [Tree basics](../../02-data-structures/trees/01-tree-basics.md) — the tree the FS is.
- [Design patterns](../03-design-patterns.md) — Composite, Facade.
- [Tries](../../05-advanced/01-tries.md) — alternative path-prefix structure for autocomplete on filenames.
- Other LLD: [Parking Lot](01-parking-lot.md) (Composite for lot→floor→spot), [LRU Cache](03-lru-cache.md).
