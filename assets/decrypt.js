// One load-time moment: the status line resolves from hex "ciphertext" to plain text.
(function () {
  var el = document.querySelector("[data-decrypt]");
  if (!el) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var plain = el.textContent;
  var hex = "0123456789abcdef";
  var duration = 1300;   // ms until the last character settles
  var lead = 250;        // ms of pure noise before the first character settles

  // Wrap each letter in a span; spaces and the full stop stay as they are.
  el.textContent = "";
  var chars = [];
  for (var i = 0; i < plain.length; i++) {
    var c = plain.charAt(i);
    if (c === " " || c === ".") {
      el.appendChild(document.createTextNode(c));
      continue;
    }
    var s = document.createElement("span");
    s.className = "ch scr";
    s.textContent = c;
    el.appendChild(s);
    chars.push({ node: s, at: lead + (i / plain.length) * (duration - lead) + Math.random() * 120 });
  }

  var start = null;
  var last = -1000;
  function frame(t) {
    if (start === null) start = t;
    var elapsed = t - start;
    var pending = 0;
    if (t - last > 45) {
      last = t;
      for (var j = 0; j < chars.length; j++) {
        var ch = chars[j];
        if (elapsed >= ch.at) {
          if (ch.node.classList.contains("scr")) ch.node.classList.remove("scr");
        } else {
          pending++;
          ch.node.setAttribute("data-n", hex.charAt((Math.random() * 16) | 0));
        }
      }
    } else {
      pending = 1;
    }
    if (pending > 0) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
