(function() {
    function initCopyButtons(root) {
        var blocks = (root || document).querySelectorAll('.page-content pre, .preview-pane pre');
        blocks.forEach(function(pre) {
            if (pre.querySelector('.copy-btn')) return;
            var code = pre.querySelector('code');
            if (!code) return;
            var btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.type = 'button';
            btn.setAttribute('aria-label', 'Copy code');
            btn.textContent = 'Copy';
            pre.style.position = 'relative';
            pre.appendChild(btn);
            btn.addEventListener('click', function() {
                var text = code.innerText;
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(text).then(function() {
                        btn.textContent = 'Copied!';
                        setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
                    }).catch(function() {
                        fallbackCopy(text, btn);
                    });
                } else {
                    fallbackCopy(text, btn);
                }
            });
        });
    }

    function fallbackCopy(text, btn) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); }
        catch (e) {}
        document.body.removeChild(ta);
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Copy'; }, 1500);
    }

    initCopyButtons();
    document.body.addEventListener('htmx:afterSwap', function(e) {
        initCopyButtons(e.target);
    });
})();