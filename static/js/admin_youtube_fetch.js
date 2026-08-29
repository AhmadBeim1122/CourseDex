(function () {
  function csrfToken() {
    var el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function getObjectIdFromUrl() {
    // Matches .../topic/123/change/  or  .../subtopic/123/change/
    var match = window.location.pathname.match(/\/(\d+)\/change\/?$/);
    return match ? match[1] : null;
  }

  function init() {
    var isTopicPage = window.location.pathname.indexOf("/academics/topic/") !== -1;
    var isSubTopicPage = window.location.pathname.indexOf("/academics/subtopic/") !== -1;
    if (!isTopicPage && !isSubTopicPage) return;

    var objectId = getObjectIdFromUrl();
    if (!objectId) return; // only on existing (change) pages, not "add"

    var titleField = document.getElementById("id_title");
    if (!titleField) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ai-btn";
    btn.style.marginTop = "8px";
    btn.textContent = "🎥 Auto-fetch YouTube Videos (2 EN + 2 HI)";

    var status = document.createElement("span");
    status.style.cssText = "margin-left:10px; font-size:12px; color:#9aa0ab;";

    btn.addEventListener("click", function () {
      btn.disabled = true;
      var original = btn.textContent;
      btn.textContent = "⏳ Searching YouTube…";
      status.textContent = "";

      var url = isTopicPage
        ? "/staff-ai/topic/" + objectId + "/fetch-videos/"
        : "/staff-ai/subtopic/" + objectId + "/fetch-videos/";

      fetch(url, {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken() },
      })
        .then(function (r) { return r.text(); })
        .then(function (text) {
          var data;
          try { data = JSON.parse(text); } catch (e) {
            data = { ok: false, error: "Non-JSON response: " + text.slice(0, 200) };
          }
          btn.disabled = false;
          btn.textContent = original;
          if (data.ok) {
            status.style.color = "#0F766E";
            status.textContent = "✅ Added " + data.added + " new video(s) (found " + data.found + "). Reloading…";
            setTimeout(function () { window.location.reload(); }, 900);
          } else {
            status.style.color = "#C2410C";
            status.textContent = "❌ " + data.error;
          }
        })
        .catch(function (err) {
          btn.disabled = false;
          btn.textContent = original;
          status.style.color = "#C2410C";
          status.textContent = "❌ " + String(err);
        });
    });

    titleField.insertAdjacentElement("afterend", btn);
    btn.insertAdjacentElement("afterend", status);
  }

  document.addEventListener("DOMContentLoaded", init);
})();