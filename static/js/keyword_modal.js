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

document.addEventListener("DOMContentLoaded", function () {
  var driveModalEl = document.getElementById("drivePreviewModal");
  if (!driveModalEl || typeof bootstrap === "undefined") return;

  var driveModal = new bootstrap.Modal(driveModalEl);
  var titleEl = document.getElementById("drivePreviewModalLabel");
  var iframeEl = document.getElementById("drivePreviewIframe");
  var openLinkEl = document.getElementById("drivePreviewOpenLink");

  function toPreviewUrl(url) {
    var match = url.match(/\/file\/d\/([a-zA-Z0-9_-]+)/) || url.match(/[?&]id=([a-zA-Z0-9_-]+)/);
    if (match) return "https://drive.google.com/file/d/" + match[1] + "/preview";
    return url;
  }

  document.addEventListener("click", function (e) {
    var trigger = e.target.closest("[data-drive-preview]");
    if (!trigger) return;
    e.preventDefault();

    var link = trigger.getAttribute("data-drive-preview");
    var title = trigger.getAttribute("data-drive-title") || "Preview";

    titleEl.textContent = title;
    iframeEl.src = toPreviewUrl(link);
    openLinkEl.href = link;
    driveModal.show();
  });

  driveModalEl.addEventListener("hidden.bs.modal", function () {
    iframeEl.src = ""; // stop the embedded viewer when the modal closes
  });
});