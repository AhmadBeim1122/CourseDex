document.addEventListener("DOMContentLoaded", function () {
  var fab = document.getElementById("chatFabBtn");
  var popup = document.getElementById("chatPopup");
  var body = document.getElementById("chat-modal-body");
  if (!fab || !popup || !body) return;

  var isOpen = false;

  fab.addEventListener("click", function () {
    isOpen = !isOpen;
    popup.classList.toggle("is-open", isOpen);
    fab.classList.toggle("is-open", isOpen);
    fab.setAttribute("aria-expanded", isOpen ? "true" : "false");
    popup.setAttribute("aria-hidden", isOpen ? "false" : "true");

    if (isOpen && typeof htmx !== "undefined") {
      htmx.ajax("GET", body.dataset.loadUrl, { target: "#chat-modal-body", swap: "innerHTML" });
    }
  });

  document.body.addEventListener("htmx:afterSwap", function (e) {
    if (e.target && e.target.id === "chat-modal-body") {
      var thread = document.getElementById("chat-thread-scroll");
      if (thread) thread.scrollTop = thread.scrollHeight;
    }
  });
});