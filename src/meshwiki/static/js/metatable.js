/* MetaTable inline cell editing — Shift+Click to edit */
(function () {
    "use strict";

    document.addEventListener("click", function (e) {
        if (!e.shiftKey) return;

        var cell = e.target.closest("td[data-editable]");
        if (!cell) return;

        e.preventDefault();
        e.stopPropagation();

        // Don't re-enter editing if already editing
        if (cell.querySelector(".metatable-edit-input")) return;

        startEditing(cell);
    });

    function startEditing(cell) {
        var page = cell.getAttribute("data-page");
        var field = cell.getAttribute("data-field");
        var currentValue = cell.textContent.trim();

        // Store original value for cancel/comparison
        cell._originalValue = currentValue;

        var input = document.createElement("input");
        input.type = "text";
        input.className = "metatable-edit-input";
        input.value = currentValue;

        // Clear cell safely and add input
        while (cell.firstChild) cell.removeChild(cell.firstChild);
        cell.classList.add("metatable-editing");
        cell.appendChild(input);
        input.focus();
        input.select();

        input.addEventListener("keydown", function (e) {
            if (e.key === "Enter") {
                e.preventDefault();
                commitEdit(cell, page, field, input.value);
            } else if (e.key === "Escape") {
                e.preventDefault();
                cancelEdit(cell);
            } else if (e.key === "Tab") {
                e.preventDefault();
                commitEdit(cell, page, field, input.value);
                var next = findNextEditableCell(cell, e.shiftKey);
                if (next) startEditing(next);
            }
        });

        input.addEventListener("blur", function () {
            setTimeout(function () {
                if (cell.querySelector(".metatable-edit-input")) {
                    commitEdit(cell, page, field, input.value);
                }
            }, 150);
        });
    }

    function commitEdit(cell, page, field, newValue) {
        newValue = newValue.trim();
        cell.classList.remove("metatable-editing");

        if (newValue === cell._originalValue) {
            cancelEdit(cell);
            return;
        }

        // Optimistic update using safe textContent
        while (cell.firstChild) cell.removeChild(cell.firstChild);
        cell.textContent = newValue;

        var urlName = page.replace(/ /g, "_");
        var formData = new FormData();
        formData.append("field", field);
        formData.append("value", newValue);

        fetch("/api/page/" + encodeURIComponent(urlName) + "/metadata", {
            method: "PATCH",
            body: formData,
        })
            .then(function (resp) {
                if (!resp.ok) {
                    return resp.json().then(function (data) {
                        throw new Error(data.detail || "Save failed");
                    });
                }
                return resp.json();
            })
            .then(function () {
                showToast("Updated " + field + " on " + page, "success");
            })
            .catch(function (err) {
                // Revert to original value on error
                cell.textContent = cell._originalValue;
                showToast("Error: " + err.message, "error");
            });
    }

    function cancelEdit(cell) {
        cell.classList.remove("metatable-editing");
        cell.textContent = cell._originalValue;
    }

    function findNextEditableCell(current, reverse) {
        var all = Array.from(document.querySelectorAll("td[data-editable]"));
        var idx = all.indexOf(current);
        if (idx === -1) return null;
        var next = reverse ? idx - 1 : idx + 1;
        return next >= 0 && next < all.length ? all[next] : null;
    }
})();
