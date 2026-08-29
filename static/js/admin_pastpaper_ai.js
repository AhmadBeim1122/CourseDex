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

  function showAlert(message) {
    var modal = document.createElement('div');
    modal.innerHTML =
      '<div style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:99999;">' +
        '<div style="background:#3a3a3a;color:#fff;padding:20px;border-radius:10px;width:420px;max-width:90%;box-shadow:0 10px 30px rgba(0,0,0,.3);">' +
          '<div style="white-space:pre-wrap;margin-bottom:15px;word-break:break-word;">' + message + '</div>' +
          '<button id="closePastpaperAlertBtn" type="button" class="ai-popup-btn ai-popup-cancel">Close</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(modal);
    document.getElementById('closePastpaperAlertBtn').onclick = function () { modal.remove(); };
  }

  function requestJSON(url, params, onDone) {
    fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-CSRFToken': csrfToken() },
      body: params,
    })
      .then(parseJsonSafe)
      .then(onDone)
      .catch(function (err) { onDone({ ok: false, error: String(err) }); });
  }

  function showSolutionPopup(provider, extractedText, initialData, solutionField, wrap) {
    var overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;z-index:99999;padding:20px;';

    var box = document.createElement('div');
    box.style.cssText = 'background:#20242b;color:#e8e8e8;padding:20px;border-radius:10px;width:680px;max-width:96%;max-height:82vh;display:flex;flex-direction:column;box-shadow:0 10px 30px rgba(0,0,0,.4);';

    var heading = document.createElement('div');
    heading.style.cssText = 'font-weight:700;margin-bottom:10px;';
    heading.textContent = '🤖 Generated solution (' + provider + ')';

    var body = document.createElement('div');
    body.className = 'ai-preview-body';
    body.style.cssText = 'overflow-y:auto;background:#14171c;border-radius:6px;padding:14px 16px;margin-bottom:14px;flex:1;font-size:14px;line-height:1.65;';

    var actions = document.createElement('div');
    actions.style.cssText = 'display:flex;gap:8px;justify-content:flex-end;';

    var confirmBtn = document.createElement('button');
    confirmBtn.type = 'button';
    confirmBtn.className = 'ai-popup-btn ai-popup-confirm';
    confirmBtn.textContent = '✅ Confirm & Add to Solution';

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
      if (solutionField._quillInstance) {
        solutionField._quillInstance.setContents([]);
        solutionField._quillInstance.clipboard.dangerouslyPasteHTML(currentText);
      } else {
        solutionField.value = currentText;
      }
      var typeSelect = document.getElementById('id_solution_type');
      if (typeSelect) typeSelect.value = 'text';
      overlay.remove();
    });

    regenBtn.addEventListener('click', function () {
      body.textContent = '⏳ Regenerating…';
      confirmBtn.disabled = true;
      regenBtn.disabled = true;
      requestJSON(
        '/staff-ai/pastpaper/solve/',
        'provider=' + encodeURIComponent(provider) + '&paper_text=' + encodeURIComponent(extractedText),
        renderState
      );
    });

    cancelBtn.addEventListener('click', function () { overlay.remove(); });
  }

  function init() {
    var linkField = document.getElementById('id_paper_drive_link');
    var solutionField = document.getElementById('id_solution_text');
    if (!linkField || !solutionField || linkField.dataset.ocrAttached) return;
    linkField.dataset.ocrAttached = '1';

    var wrap = document.createElement('div');
    wrap.className = 'pastpaper-ai-wrap';

    var ocrRow = document.createElement('div');
    ocrRow.className = 'ai-btn-group';
    wrap.appendChild(ocrRow);

    var ocrBtnGemini = document.createElement('button');
    ocrBtnGemini.type = 'button';
    ocrBtnGemini.className = 'ai-btn';
    ocrBtnGemini.textContent = '📄 OCR via Gemini Vision';
    ocrRow.appendChild(ocrBtnGemini);

    var ocrBtnTesseract = document.createElement('button');
    ocrBtnTesseract.type = 'button';
    ocrBtnTesseract.className = 'ai-btn';
    ocrBtnTesseract.textContent = '📄 OCR via Tesseract (Local)';
    ocrRow.appendChild(ocrBtnTesseract);

    var extractedBox = document.createElement('div');
    extractedBox.className = 'ocr-extracted-box';
    extractedBox.style.display = 'none';
    wrap.appendChild(extractedBox);

    var extractedLabel = document.createElement('div');
    extractedLabel.className = 'ocr-extracted-label';
    extractedLabel.textContent = 'Extracted question paper text:';
    extractedBox.appendChild(extractedLabel);

    var extractedText = document.createElement('div');
    extractedText.className = 'ocr-extracted-text';
    extractedBox.appendChild(extractedText);

    var solveWrap = document.createElement('div');
    solveWrap.className = 'ai-btn-group';
    solveWrap.style.marginTop = '8px';
    extractedBox.appendChild(solveWrap);

    var currentExtracted = '';

    [['groq', 'API 1'], ['gemini', 'API 2'], ['openrouter', 'API 3'], ['ollama', 'API 4']].forEach(function (p) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'ai-btn';
      btn.textContent = '🤖 ' + p[1] + ' — Get Solution';
      btn.addEventListener('click', function () {
        if (!currentExtracted) { showAlert('Pehle OCR se text extract karein.'); return; }
        var original = btn.textContent;
        btn.disabled = true;
        btn.textContent = '⏳ Solving…';
        requestJSON(
          '/staff-ai/pastpaper/solve/',
          'provider=' + encodeURIComponent(p[0]) + '&paper_text=' + encodeURIComponent(currentExtracted),
          function (data) {
            btn.disabled = false;
            btn.textContent = original;
            showSolutionPopup(p[0], currentExtracted, data, solutionField, wrap);
          }
        );
      });
      solveWrap.appendChild(btn);
    });

    function runOcr(method, btn, loadingLabel) {
      var link = (linkField.value || '').trim();
      if (!link) { showAlert('Pehle Question paper ka Drive link field mein daalein.'); return; }
      var original = btn.textContent;
      ocrBtnGemini.disabled = true;
      ocrBtnTesseract.disabled = true;
      btn.textContent = loadingLabel;
      requestJSON(
        '/staff-ai/pastpaper/ocr/',
        'drive_link=' + encodeURIComponent(link) + '&method=' + encodeURIComponent(method),
        function (data) {
          ocrBtnGemini.disabled = false;
          ocrBtnTesseract.disabled = false;
          btn.textContent = original;
          extractedBox.style.display = 'block';
            if (data.ok) {
            currentExtracted = data.text;
            extractedLabel.textContent = 'Extracted question paper text (' + method + '):';
            extractedText.textContent = data.text;
            var storedField = document.getElementById('id_extracted_text');
            if (storedField) storedField.value = data.text;
          } else {
            currentExtracted = '';
            extractedLabel.textContent = 'Extracted question paper text (' + method + '):';
            extractedText.textContent = '❌ Error: ' + data.error;
          }
        }
      );
    }

    ocrBtnGemini.addEventListener('click', function () {
      runOcr('gemini', ocrBtnGemini, '⏳ Extracting via Gemini…');
    });

    ocrBtnTesseract.addEventListener('click', function () {
      runOcr('tesseract', ocrBtnTesseract, '⏳ Extracting via Tesseract…');
    });

    linkField.insertAdjacentElement('afterend', wrap);
  }

  document.addEventListener('DOMContentLoaded', init);
})();