(function () {
  function parseJsonSafe(response) {
    return response.text().then(function (text) {
      try {
        return JSON.parse(text);
      } catch (e) {
        return {
          ok: false,
          error: 'Server returned a non-JSON response (HTTP ' + response.status + '): ' + text.slice(0, 300),
        };
      }
    });
  }
  function csrfToken() {
    var el = document.querySelector('input[name=csrfmiddlewaretoken]');
    return el ? el.value : '';
  }

  function refreshUsage(wrap) {
    fetch('/admin/academics/topic/ai/usage/', { credentials: 'same-origin' })
      .then(parseJsonSafe)
      .then(function (data) {
        var note = wrap.querySelector('.ai-usage-note');
        if (note) {
          note.textContent = data.summary.map(function (s) {
            return s.label + ': ' + s.remaining + '/' + s.limit + ' left today';
          }).join('   ·   ');
        }
      }).catch(function () {});
  }

  function showCopyAlert(message) {
    var modal = document.createElement('div');
    modal.innerHTML =
      '<div style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:99999;">' +
        '<div style="background:#3a3a3a;color:#fff;padding:20px;border-radius:10px;width:420px;max-width:90%;box-shadow:0 10px 30px rgba(0,0,0,.3);">' +
          '<div style="white-space:pre-wrap;margin-bottom:15px;word-break:break-word;">' + message + '</div>' +
          '<button id="copyAlertBtn" type="button" class="ai-popup-btn ai-popup-confirm">📋 Copy</button>' +
          '<button id="closeAlertBtn" type="button" class="ai-popup-btn ai-popup-cancel">Close</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    document.getElementById('copyAlertBtn').onclick = function () {
      navigator.clipboard.writeText(message).then(function () {
        document.getElementById('copyAlertBtn').textContent = '✅ Copied!';
      });
    };
    document.getElementById('closeAlertBtn').onclick = function () { modal.remove(); };
  }

  function requestGeneration(provider, title, onDone) {
    fetch('/admin/academics/topic/ai/generate/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken() },
      body: 'provider=' + encodeURIComponent(provider) + '&title=' + encodeURIComponent(title),
    })
      .then(parseJsonSafe)
      .then(function (data) { onDone(data); })
      .catch(function (err) { onDone({ ok: false, error: String(err) }); });
  }

  function showGenerationPopup(provider, title, initialData, contentField, wrap) {
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;z-index:99999;padding:20px;';

    var box = document.createElement('div');
    box.style.cssText = 'background:#20242b;color:#e8e8e8;padding:20px;border-radius:10px;width:600px;max-width:95%;max-height:80vh;display:flex;flex-direction:column;box-shadow:0 10px 30px rgba(0,0,0,.4);';

    var heading = document.createElement('div');
    heading.style.cssText = 'font-weight:700;margin-bottom:10px;';
    heading.textContent = '🤖 Generated content for: ' + title;

    var body = document.createElement('div');
    body.style.cssText = 'overflow-y:auto;background:#14171c;border-radius:6px;padding:14px 16px;margin-bottom:14px;flex:1;font-size:14px;line-height:1.65;';
    body.className = 'ai-preview-body';

    var actions = document.createElement('div');
    actions.style.cssText = 'display:flex;gap:8px;justify-content:flex-end;';

    var confirmBtn = document.createElement('button');
    confirmBtn.type = 'button';
    confirmBtn.className = 'ai-popup-btn ai-popup-confirm';
    confirmBtn.textContent = '✅ Confirm & Add';

    var regenBtn = document.createElement('button');
    regenBtn.type = 'button';
    regenBtn.className = 'ai-popup-btn ai-popup-regen';
    regenBtn.textContent = '🔄 Regenerate';

    var cancelBtn = document.createElement('button');
    cancelBtn.type = 'button';
    cancelBtn.className = 'ai-popup-btn ai-popup-cancel';
    cancelBtn.textContent = '✖ Cancel';

    actions.appendChild(regenBtn);
    actions.appendChild(cancelBtn);
    actions.appendChild(confirmBtn);
    box.appendChild(heading);
    box.appendChild(body);
    box.appendChild(actions);
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    var currentText = '';

    function renderState(data) {
      if (data.ok) {
        currentText = data.text;
        body.innerHTML = data.text;
        confirmBtn.disabled = false;
        regenBtn.disabled = false;
      } else {
        currentText = '';
        body.textContent = '❌ Error: ' + data.error;
        confirmBtn.disabled = true;
        regenBtn.disabled = false;
      }
    }

    renderState(initialData);

    confirmBtn.addEventListener('click', function () {
      if (!currentText) return;
      if (contentField._quillInstance) {
        contentField._quillInstance.setContents([]);
        contentField._quillInstance.clipboard.dangerouslyPasteHTML(currentText);
      } else {
        contentField.value = currentText;
      }
      refreshUsage(wrap);
      overlay.remove();
    });

    regenBtn.addEventListener('click', function () {
      body.textContent = '⏳ Regenerating…';
      confirmBtn.disabled = true;
      regenBtn.disabled = true;
      requestGeneration(provider, title, function (data) {
        renderState(data);
      });
    });

    cancelBtn.addEventListener('click', function () {
      overlay.remove();
    });
  }

  function runGenerate(provider, titleField, contentField, btn, wrap) {
    var title = (titleField.value || '').trim();
    if (!title) { showCopyAlert('Pehle Title field fill karein.'); return; }
    var original = btn.textContent;
    btn.disabled = true;
    btn.textContent = '⏳ Generating…';
    requestGeneration(provider, title, function (data) {
      btn.disabled = false;
      btn.textContent = original;
      showGenerationPopup(provider, title, data, contentField, wrap);
    });
  }

  function attach(contentField, titleField) {
    if (!contentField || !titleField || contentField.dataset.aiAttached) return;
    contentField.dataset.aiAttached = '1';

    var wrap = document.createElement('div');
    wrap.className = 'ai-btn-group';

        [['groq', 'API 1'], ['gemini', 'API 2'], ['openrouter', 'API 3'], ['ollama', 'API 4']].forEach(function (p) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ai-btn';
      btn.textContent = '🤖 ' + p[1] + ' — Get Data';
      btn.addEventListener('click', function () {
        runGenerate(p[0], titleField, contentField, btn, wrap);
      });
      wrap.appendChild(btn);
    });

    var usage = document.createElement('div');
    usage.className = 'ai-usage-note';
    wrap.appendChild(usage);

    contentField.insertAdjacentElement('afterend', wrap);
    refreshUsage(wrap);
  }

  function scan(root) {
    root = root || document;
    attach(root.querySelector('#id_content'), root.querySelector('#id_title'));
    root.querySelectorAll('tr.form-row, tr').forEach(function (row) {
      var content = row.querySelector('textarea[id$="-content"]');
      var title = row.querySelector('input[id$="-title"]');
      if (content && title) attach(content, title);
    });
  }

  document.addEventListener('DOMContentLoaded', function () { scan(document); });
  document.addEventListener('formset:added', function (e) { scan(e.target); });
})();