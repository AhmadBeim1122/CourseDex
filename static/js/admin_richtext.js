(function () {
  var formatsRegistered = false;

  function registerDefinitionListFormats() {
    if (formatsRegistered || typeof Quill === 'undefined') return;
    var Block = Quill.import('blots/block');

    function makeBlot(tag, name) {
      function Blot(domNode, value) { return Block.call(this, domNode, value) || this; }
      Blot.prototype = Object.create(Block.prototype);
      Blot.prototype.constructor = Blot;
      Blot.blotName = name;
      Blot.tagName = tag;
      return Blot;
    }

    var DtBlot = makeBlot('DT', 'dt');
    var DdBlot = makeBlot('DD', 'dd');
    Quill.register(DtBlot, true);
    Quill.register(DdBlot, true);

    var icons = Quill.import('ui/icons');
    icons['dt'] = '<span style="font-weight:700;font-size:11px;">Term</span>';
    icons['dd'] = '<span style="font-size:11px;">Def</span>';

    formatsRegistered = true;
  }

  function initEditor(textarea) {
    if (!textarea || textarea.dataset.richInit) return;
    textarea.dataset.richInit = '1';

    registerDefinitionListFormats();

    var toolbarWrap = document.createElement('div');
    toolbarWrap.innerHTML =
      '<span class="ql-formats">' +
        '<select class="ql-header"><option value="3"></option><option value="4"></option><option selected></option></select>' +
      '</span>' +
      '<span class="ql-formats">' +
        '<button class="ql-bold"></button><button class="ql-italic"></button>' +
      '</span>' +
      '<span class="ql-formats">' +
        '<button class="ql-blockquote"></button>' +
        '<button class="ql-list" value="ordered"></button>' +
        '<button class="ql-list" value="bullet"></button>' +
      '</span>' +
      '<span class="ql-formats">' +
        '<button class="ql-dt" title="Definition term"></button>' +
        '<button class="ql-dd" title="Definition description"></button>' +
      '</span>' +
      '<span class="ql-formats">' +
        '<button class="ql-link"></button><button class="ql-clean"></button>' +
      '</span>';
    toolbarWrap.className = 'rich-text-toolbar';

    var editorDiv = document.createElement('div');

    var container = document.createElement('div');
    container.className = 'rich-text-container';
    container.appendChild(toolbarWrap);
    container.appendChild(editorDiv);
    textarea.insertAdjacentElement('beforebegin', container);

    var quill = new Quill(editorDiv, {
      theme: 'snow',
      modules: { toolbar: toolbarWrap },
    });

    var toolbarModule = quill.getModule('toolbar');
    toolbarModule.addHandler('dt', function () {
      var range = quill.getSelection(true);
      if (range) quill.formatLine(range.index, range.length || 1, 'dt', true);
    });
    toolbarModule.addHandler('dd', function () {
      var range = quill.getSelection(true);
      if (range) quill.formatLine(range.index, range.length || 1, 'dd', true);
    });

    if (textarea.value) {
      quill.clipboard.dangerouslyPasteHTML(textarea.value);
    }

    quill.on('text-change', function () {
      textarea.value = quill.root.innerHTML;
    });

    textarea._quillInstance = quill;

    var form = textarea.closest('form');
    if (form) {
      form.addEventListener('submit', function () {
        textarea.value = quill.root.innerHTML;
      });
    }
  }

  function scan(root) {
    root = root || document;
    root.querySelectorAll('textarea.rich-text-source').forEach(initEditor);
  }

  document.addEventListener('DOMContentLoaded', function () { scan(document); });
  document.addEventListener('formset:added', function (e) { scan(e.target); });
})();