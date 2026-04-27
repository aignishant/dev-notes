/* dev-notes — interactive layer
 *   - three.js wireframe icosahedron in the home hero
 *   - smooth-scroll for in-page anchors
 *   - copy-to-clipboard toast (uses Material's existing button; we only flash a hint)
 *
 * three.js is loaded as an external <script> in mkdocs.yml's extra_javascript.
 * If THREE is not present (e.g. on offline / pages without internet), we no-op.
 */
(function () {
  "use strict";

  // ── 1. three.js hero ──────────────────────────────────────────────────────
  function mountHero() {
    const mount = document.querySelector(".dn-hero-3d");
    if (!mount || typeof window.THREE === "undefined") return;
    if (mount.dataset.mounted === "1") return;
    mount.dataset.mounted = "1";

    const T = window.THREE;
    const w = mount.clientWidth || 360;
    const h = mount.clientHeight || 360;

    const scene = new T.Scene();
    const camera = new T.PerspectiveCamera(50, w / h, 0.1, 1000);
    camera.position.z = 3.4;

    const renderer = new T.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    renderer.setSize(w, h);
    mount.appendChild(renderer.domElement);

    // Wireframe icosahedron with a soft glow inner sphere.
    const geo = new T.IcosahedronGeometry(1.25, 1);
    const wire = new T.LineSegments(
      new T.WireframeGeometry(geo),
      new T.LineBasicMaterial({ color: 0xc7d2fe, transparent: true, opacity: 0.95 })
    );
    scene.add(wire);

    const inner = new T.Mesh(
      new T.IcosahedronGeometry(0.9, 0),
      new T.MeshBasicMaterial({ color: 0x8b5cf6, transparent: true, opacity: 0.18 })
    );
    scene.add(inner);

    // Floating particle dust
    const dustCount = 120;
    const dustGeo = new T.BufferGeometry();
    const positions = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount; i++) {
      const r = 1.7 + Math.random() * 0.9;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      positions[i * 3 + 0] = r * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = r * Math.cos(phi);
    }
    dustGeo.setAttribute("position", new T.BufferAttribute(positions, 3));
    const dust = new T.Points(
      dustGeo,
      new T.PointsMaterial({ color: 0xec4899, size: 0.035, transparent: true, opacity: 0.85 })
    );
    scene.add(dust);

    let raf = 0;
    const loop = (t) => {
      const k = t * 0.0006;
      wire.rotation.x = k * 0.7;
      wire.rotation.y = k;
      inner.rotation.x = -k * 0.5;
      inner.rotation.y = -k * 0.8;
      dust.rotation.y = k * 0.4;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);

    // Resize
    const resize = () => {
      const W = mount.clientWidth || 360;
      const H = mount.clientHeight || 360;
      camera.aspect = W / H;
      camera.updateProjectionMatrix();
      renderer.setSize(W, H);
    };
    window.addEventListener("resize", resize);

    // Pause when offscreen / tab hidden
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) cancelAnimationFrame(raf);
      else raf = requestAnimationFrame(loop);
    });
  }

  // ── 2. Smooth scroll for in-page anchors ──────────────────────────────────
  function smoothAnchors() {
    document.querySelectorAll('a[href^="#"]').forEach((a) => {
      a.addEventListener("click", (e) => {
        const id = a.getAttribute("href");
        if (!id || id.length < 2) return;
        const target = document.querySelector(id);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        history.pushState(null, "", id);
      });
    });
  }

  // ── 3. Tilt effect on grid cards (light, no library) ──────────────────────
  function tiltCards() {
    const cards = document.querySelectorAll(".md-typeset .grid.cards > ul > li");
    cards.forEach((card) => {
      card.addEventListener("mousemove", (e) => {
        const r = card.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width - 0.5;
        const py = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform =
          `translateY(-6px) rotateX(${(-py * 4).toFixed(2)}deg) rotateY(${(px * 4).toFixed(2)}deg) scale(1.012)`;
      });
      card.addEventListener("mouseleave", () => {
        card.style.transform = "";
      });
    });
  }

  // Material's instant-navigation rebinds on every page swap.
  // document$ is provided by mkdocs-material when navigation.instant is on.
  const init = () => {
    mountHero();
    smoothAnchors();
    tiltCards();
  };

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
