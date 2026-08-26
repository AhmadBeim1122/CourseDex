document.addEventListener("DOMContentLoaded", function () {
  var modalEl = document.getElementById("keywordModal");
  if (!modalEl || typeof bootstrap === "undefined") return;

  var modalTitle = document.getElementById("keywordModalLabel");
  var modalBody = document.getElementById("keywordModalBody");
  var modalLink = document.getElementById("keywordModalLink");
  var modal = new bootstrap.Modal(modalEl);

document.addEventListener("click", function (e) {
    var link = e.target.closest("[data-kind][data-id]");
    if (!link) return;
    e.preventDefault();

    var kind = link.getAttribute("data-kind");
    var id = link.getAttribute("data-id");

    modalTitle.textContent = "Loading…";
    modalBody.innerHTML = '<div class="empty-state"><p>Loading…</p></div>';
    modalLink.style.visibility = "hidden";
    modal.show();

    fetch("/api/content/" + kind + "/" + id + "/")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.ok) {
          modalTitle.textContent = data.title;
          modalBody.innerHTML = data.content
            ? '<div class="topic-body">' + data.content + '</div>'
            : '<div class="empty-state"><p>No content added for this yet.</p></div>';
          modalLink.href = data.url;
          modalLink.style.visibility = "visible";
        } else {
          modalTitle.textContent = "Not found";
          modalBody.innerHTML = '<div class="empty-state"><p>' + (data.error || "Could not load content.") + '</p></div>';
        }
      })
      .catch(function () {
        modalTitle.textContent = "Error";
        modalBody.innerHTML = '<div class="empty-state"><p>Something went wrong loading this content.</p></div>';
      });
  });
});