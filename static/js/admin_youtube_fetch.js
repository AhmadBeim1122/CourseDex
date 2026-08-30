(function () {
  function csrfToken() {
    var el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function getObjectIdFromUrl() {
    var match = window.location.pathname.match(/\/(\d+)\/change\/?$/);
    return match ? match[1] : null;
  }

  function runFetch(url, btn, onSuccessReload) {
    btn.disabled = true;
    var original = btn.textContent;
    btn.textContent = "⏳ Searching…";
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
          btn.textContent = "✅ +" + data.added + " added";
          if (onSuccessReload) setTimeout(function () { window.location.reload(); }, 900);
        } else {
          alert("❌ " + data.error);
        }
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = original;
        alert("❌ " + String(err));
      });
  }

  // ---- Main "Auto-fetch" button on the Topic/SubTopic's own change page ----
  function initMainButton() {
    var isTopicPage = window.location.pathname.indexOf("/academics/topic/") !== -1;
    var isSubTopicPage = window.location.pathname.indexOf("/academics/subtopic/") !== -1;
    if (!isTopicPage && !isSubTopicPage) return;

    var objectId = getObjectIdFromUrl();
    if (!objectId) return;

    var titleField = document.getElementById("id_title");
    if (!titleField) return;

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "ai-btn";
    btn.style.marginTop = "8px";
    btn.textContent = "🎥 Auto-fetch YouTube Videos (2 EN + 2 HI)";

    var url = isTopicPage
      ? "/staff-ai/topic/" + objectId + "/fetch-videos/"
      : "/staff-ai/subtopic/" + objectId + "/fetch-videos/";

    btn.addEventListener("click", function () {
      runFetch(url, btn, true);
    });

    titleField.insertAdjacentElement("afterend", btn);
  }

  // ---- Small "Fetch Videos" shortcut on each existing Subtopic inline row (Topic page) ----
  function initInlineSubtopicButtons() {
    var group = document.getElementById("subtopics-group");
    if (!group) return;

    var rows = group.querySelectorAll("tr[id^='subtopics-']");
    rows.forEach(function (row) {
      if (row.id === "subtopics-empty" || row.dataset.ytAttached) return;

      var idInput = row.querySelector('input[name$="-id"]');
      var titleInput = row.querySelector('input[name$="-title"]');
      if (!idInput || !titleInput || !idInput.value) return; // unsaved new row — skip

      row.dataset.ytAttached = "1";
      var pk = idInput.value;
      var cell = titleInput.closest("td");
      if (!cell) return;

      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ai-btn ai-btn-inline";
      btn.textContent = "🎥 Fetch Videos";
      btn.title = "Auto-fetch 2 EN + 2 HI YouTube videos for this subtopic";
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        runFetch("/staff-ai/subtopic/" + pk + "/fetch-videos/", btn, false);
      });

      cell.appendChild(document.createElement("br"));
      cell.appendChild(btn);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initMainButton();
    initInlineSubtopicButtons();
  });
})();