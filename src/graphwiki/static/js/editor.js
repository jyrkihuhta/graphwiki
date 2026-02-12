(function () {
    "use strict";

    var textarea = document.getElementById("content");
    var toolbar = document.getElementById("editor-toolbar");
    var form = document.getElementById("edit-form");
    var dropdown = document.getElementById("autocomplete-dropdown");
    var dirty = false;

    if (!textarea || !toolbar) return;

    // ========== Dirty tracking ==========
    textarea.addEventListener("input", function () {
        dirty = true;
    });
    window.addEventListener("beforeunload", function (e) {
        if (dirty) {
            e.preventDefault();
            e.returnValue = "";
        }
    });
    if (form) {
        form.addEventListener("submit", function () {
            dirty = false;
        });
    }

    // ========== Toolbar actions ==========
    var wrappers = {
        bold: { before: "**", after: "**", placeholder: "bold text" },
        italic: { before: "*", after: "*", placeholder: "italic text" },
        strikethrough: { before: "~~", after: "~~", placeholder: "strikethrough text" },
        heading: { before: "## ", after: "", placeholder: "Heading" },
        code: { before: "`", after: "`", placeholder: "code" },
        link: { before: "[", after: "](url)", placeholder: "link text" },
        wikilink: { before: "[[", after: "]]", placeholder: "PageName" },
    };

    function wrapSelection(action) {
        var w = wrappers[action];
        if (!w) return;
        var start = textarea.selectionStart;
        var end = textarea.selectionEnd;
        var selected = textarea.value.substring(start, end) || w.placeholder;
        var replacement = w.before + selected + w.after;
        textarea.setRangeText(replacement, start, end, "select");
        textarea.focus();
        // Select the inserted text (not the wrapper chars)
        textarea.selectionStart = start + w.before.length;
        textarea.selectionEnd = start + w.before.length + selected.length;
        dirty = true;
        textarea.dispatchEvent(new Event("input", { bubbles: true }));
    }

    toolbar.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-action]");
        if (btn) {
            wrapSelection(btn.dataset.action);
        }
    });

    // ========== Keyboard shortcuts ==========
    textarea.addEventListener("keydown", function (e) {
        var mod = e.ctrlKey || e.metaKey;
        if (!mod) return;

        if (e.key === "b") {
            e.preventDefault();
            wrapSelection("bold");
        } else if (e.key === "i") {
            e.preventDefault();
            wrapSelection("italic");
        } else if (e.key === "k") {
            e.preventDefault();
            wrapSelection("link");
        } else if (e.key === "s") {
            e.preventDefault();
            if (form) {
                dirty = false;
                form.submit();
            }
        } else if (e.key === "p") {
            e.preventDefault();
            togglePreview();
        }
    });

    // ========== Wiki link autocomplete ==========
    var acVisible = false;
    var acItems = [];
    var acIndex = -1;

    function hideAutocomplete() {
        dropdown.innerHTML = "";
        acVisible = false;
        acItems = [];
        acIndex = -1;
    }

    function getWikiLinkPrefix() {
        var pos = textarea.selectionStart;
        var text = textarea.value.substring(0, pos);
        var match = text.match(/\[\[([^\]|]*)$/);
        return match ? match[1] : null;
    }

    function showAutocomplete(query) {
        if (!query && query !== "") {
            hideAutocomplete();
            return;
        }
        fetch("/api/autocomplete?q=" + encodeURIComponent(query))
            .then(function (r) { return r.text(); })
            .then(function (html) {
                if (!html) {
                    hideAutocomplete();
                    return;
                }
                dropdown.innerHTML = html;
                acItems = Array.from(dropdown.querySelectorAll(".autocomplete-item"));
                acIndex = -1;
                acVisible = acItems.length > 0;
            });
    }

    function insertAutocomplete(value) {
        var pos = textarea.selectionStart;
        var text = textarea.value.substring(0, pos);
        var match = text.match(/\[\[([^\]|]*)$/);
        if (match) {
            var start = pos - match[1].length;
            textarea.setRangeText(value + "]]", start, pos, "end");
            dirty = true;
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }
        hideAutocomplete();
        textarea.focus();
    }

    textarea.addEventListener("input", function () {
        var prefix = getWikiLinkPrefix();
        if (prefix !== null) {
            showAutocomplete(prefix);
        } else {
            hideAutocomplete();
        }
    });

    textarea.addEventListener("keydown", function (e) {
        if (!acVisible) return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            acIndex = Math.min(acIndex + 1, acItems.length - 1);
            acItems.forEach(function (el, i) {
                el.classList.toggle("active", i === acIndex);
            });
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            acIndex = Math.max(acIndex - 1, 0);
            acItems.forEach(function (el, i) {
                el.classList.toggle("active", i === acIndex);
            });
        } else if (e.key === "Enter" || e.key === "Tab") {
            if (acIndex >= 0 && acIndex < acItems.length) {
                e.preventDefault();
                insertAutocomplete(acItems[acIndex].dataset.value);
            }
        } else if (e.key === "Escape") {
            hideAutocomplete();
        }
    });

    dropdown.addEventListener("click", function (e) {
        var item = e.target.closest(".autocomplete-item");
        if (item) {
            insertAutocomplete(item.dataset.value);
        }
    });

    // Close dropdown on outside click
    document.addEventListener("click", function (e) {
        if (!dropdown.contains(e.target) && e.target !== textarea) {
            hideAutocomplete();
        }
    });

    // ========== Preview toggle ==========
    var previewPane = document.getElementById("preview-pane");
    var editorSplit = document.getElementById("editor-split");
    var toggleBtn = document.getElementById("toggle-preview");
    var previewEnabled = localStorage.getItem("graphwiki-preview") !== "false";

    function enablePreview() {
        previewEnabled = true;
        localStorage.setItem("graphwiki-preview", "true");
        editorSplit.classList.remove("editor-split--no-preview");
        textarea.setAttribute("hx-post", "/api/preview");
        textarea.setAttribute("hx-trigger", "keyup changed delay:300ms");
        textarea.setAttribute("hx-target", "#preview-pane");
        if (typeof htmx !== "undefined") {
            htmx.process(textarea);
            htmx.trigger(textarea, "keyup");
        }
        if (toggleBtn) toggleBtn.classList.add("active");
    }

    function disablePreview() {
        previewEnabled = false;
        localStorage.setItem("graphwiki-preview", "false");
        editorSplit.classList.add("editor-split--no-preview");
        textarea.removeAttribute("hx-post");
        textarea.removeAttribute("hx-trigger");
        textarea.removeAttribute("hx-target");
        if (typeof htmx !== "undefined") {
            htmx.process(textarea);
        }
        if (toggleBtn) toggleBtn.classList.remove("active");
    }

    function togglePreview() {
        if (previewEnabled) {
            disablePreview();
        } else {
            enablePreview();
        }
    }

    if (toggleBtn) {
        toggleBtn.addEventListener("click", togglePreview);
    }

    // Apply initial state
    if (previewEnabled) {
        enablePreview();
    } else {
        disablePreview();
    }
})();
