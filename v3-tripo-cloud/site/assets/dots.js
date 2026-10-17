/* Animated dot-grid background (vanilla re-creation of the Framer "Dots" asset).
   Fixed, pointer-reactive, tiny, and motion-safe. */
(function () {
  var c = document.getElementById("dots-bg");
  if (!c) return;
  var ctx = c.getContext("2d");
  var dpr = Math.min(window.devicePixelRatio || 1, 2);
  var reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var gap = 30, w = 0, h = 0, px = -9999, py = -9999, t = 0;

  function resize() {
    w = window.innerWidth; h = window.innerHeight;
    c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
    c.style.width = w + "px"; c.style.height = h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  window.addEventListener("resize", resize);
  window.addEventListener("pointermove", function (e) { px = e.clientX; py = e.clientY; });
  window.addEventListener("pointerleave", function () { px = py = -9999; });
  resize();

  function frame() {
    t += 0.006;
    ctx.clearRect(0, 0, w, h);
    for (var y = gap / 2; y < h; y += gap) {
      for (var x = gap / 2; x < w; x += gap) {
        var dx = x - px, dy = y - py;
        var near = Math.max(0, 1 - Math.sqrt(dx * dx + dy * dy) / 150);
        var r = 1.05 + near * 2.5 + (reduced ? 0 : 0.22 * Math.sin(t * 2 + (x + y) * 0.012));
        var a = 0.07 + near * 0.5;
        ctx.beginPath();
        ctx.fillStyle = near > 0.02
          ? "rgba(200,240,74," + a.toFixed(3) + ")"
          : "rgba(255,255,255," + a.toFixed(3) + ")";
        ctx.arc(x, y, Math.max(0.4, r), 0, 6.2832);
        ctx.fill();
      }
    }
    if (!reduced) requestAnimationFrame(frame);
  }
  frame();
})();
