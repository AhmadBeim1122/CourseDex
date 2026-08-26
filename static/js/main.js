// Minimal JS: mobile nav toggle only. Everything else is HTMX or plain links.
document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.getElementById("navToggle");
  var nav = document.getElementById("primaryNav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Outline sidebar toggle — only visually active on mobile/tablet via CSS,
  // harmless no-op on desktop where the media query doesn't collapse it.
  document.querySelectorAll(".outline-side").forEach(function (aside) {
    var heading = aside.querySelector("h4");
    if (!heading || heading.dataset.toggleInit) return;
    heading.dataset.toggleInit = "1";
    heading.classList.add("outline-toggle-heading");

    var arrow = document.createElement("span");
    arrow.className = "outline-toggle-arrow";
    arrow.textContent = "▾";
    heading.appendChild(arrow);

    heading.addEventListener("click", function () {
      var open = aside.classList.toggle("is-open");
      arrow.textContent = open ? "▴" : "▾";
    });
  });
  
  var themeToggle = document.getElementById("themeToggle");
  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme");
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("theme", next);
    });
  }
});


// ---------- Lazy YouTube embed: thumbnail -> click -> play ----------
let currentPlayingEmbed = null;

function loadLiteEmbed(thumbEl) {
  var wrapper = thumbEl.closest('.lite-embed');
  if (!wrapper) return;

  if (currentPlayingEmbed && currentPlayingEmbed !== wrapper) {
    resetLiteEmbed(currentPlayingEmbed);
  }

  var src = wrapper.getAttribute('data-embed-src');
  if (!wrapper.dataset.originalHtml) {
    wrapper.dataset.originalHtml = wrapper.innerHTML;
  }

  var origin = window.location.origin;
  var iframe = document.createElement('iframe');
  iframe.style.position = 'absolute';
  iframe.style.inset = '0';
  iframe.style.width = '100%';
  iframe.style.height = '100%';
  iframe.style.border = '0';
  iframe.setAttribute('allowfullscreen', '');
  iframe.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
  iframe.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
  iframe.setAttribute('title', 'YouTube video player');
  iframe.src = src
    + (src.indexOf('?') > -1 ? '&' : '?')
    + 'autoplay=1&rel=0&modestbranding=1&origin=' + encodeURIComponent(origin);

  wrapper.innerHTML = '';
  wrapper.appendChild(iframe);
  currentPlayingEmbed = wrapper;
}
function resetLiteEmbed(wrapper) {
  if (!wrapper) return;
  if (wrapper.dataset.originalHtml) {
    wrapper.innerHTML = wrapper.dataset.originalHtml;
  }
  if (currentPlayingEmbed === wrapper) currentPlayingEmbed = null;
}