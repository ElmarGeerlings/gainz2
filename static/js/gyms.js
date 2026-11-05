let gymPhotoIndex = 0;
let gymPhotoViewerOpen = false;
let gymEquipmentModalSlug = "";
let gymEquipmentModalStatus = "assumed";
let gymEquipmentModalQuantity = "";

function syncGymFooterTab(tabName) {
    const infoFooter = document.getElementById("gym-footer-info");
    const equipFooter = document.getElementById("gym-footer-equipment");
    if (infoFooter) {
        infoFooter.hidden = tabName === "equipment";
    }
    if (equipFooter) {
        equipFooter.hidden = tabName !== "equipment";
    }
}

function activateGymTab(tabName) {
    document.querySelectorAll(".gym-tab").forEach((tabEl) => {
        const isActive = tabEl.getAttribute("data-tab") === tabName;
        tabEl.classList.toggle("is-active", isActive);
        tabEl.setAttribute("aria-selected", isActive ? "true" : "false");
    });
    document.querySelectorAll(".gym-panel").forEach((panel) => {
        const panelTab = panel.id.replace("gym-panel-", "");
        const isActive = panelTab === tabName;
        panel.classList.toggle("hidden", !isActive);
        panel.hidden = !isActive;
    });
    syncGymFooterTab(tabName);
    const url = new URL(window.location.href);
    url.searchParams.set("tab", tabName);
    history.replaceState(null, "", url.toString());
}

function switchGymTab(event) {
    const tabName = event.currentTarget.getAttribute("data-tab");
    if (tabName) {
        activateGymTab(tabName);
    }
}

function jumpToGymHours() {
    activateGymTab("info");
    const hoursPanel = document.getElementById("gym-hours-panel");
    if (hoursPanel) {
        hoursPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function gymPhotoSlideCount() {
    const track = document.getElementById("gym-photo-track");
    if (!track) {
        return 0;
    }
    return track.children.length;
}

function gymPhotoSlideImage(index) {
    const track = document.getElementById("gym-photo-track");
    if (!track) {
        return null;
    }
    const slide = track.children[index];
    if (!slide) {
        return null;
    }
    return slide.querySelector(".gym-hero-slide-img");
}

function syncGymPhotoViewerImage() {
    const viewerImg = document.getElementById("gym-photo-viewer-img");
    const heroImg = gymPhotoSlideImage(gymPhotoIndex);
    if (viewerImg && heroImg) {
        viewerImg.src = heroImg.src;
        viewerImg.alt = heroImg.alt;
    }
}

function setGymPhotoIndex(index) {
    const count = gymPhotoSlideCount();
    if (count === 0) {
        return;
    }
    gymPhotoIndex = ((index % count) + count) % count;
    const track = document.getElementById("gym-photo-track");
    track.style.transform = `translateX(-${gymPhotoIndex * 100}%)`;
    document.querySelectorAll(".gym-hero-dot").forEach((dot, dotIndex) => {
        dot.classList.toggle("is-active", dotIndex === gymPhotoIndex);
    });
    if (gymPhotoViewerOpen) {
        syncGymPhotoViewerImage();
    }
}

function bindGymPhotoSwipe(element) {
    let touchStartX = 0;
    element.addEventListener("touchstart", (event) => {
        touchStartX = event.changedTouches[0].screenX;
    }, { passive: true });
    element.addEventListener("touchend", (event) => {
        const delta = event.changedTouches[0].screenX - touchStartX;
        if (Math.abs(delta) < 40) {
            return;
        }
        if (delta < 0) {
            setGymPhotoIndex(gymPhotoIndex + 1);
        } else {
            setGymPhotoIndex(gymPhotoIndex - 1);
        }
    }, { passive: true });
}

function initGymPhotoCarousel() {
    const carousel = document.getElementById("gym-photo-carousel");
    if (carousel) {
        bindGymPhotoSwipe(carousel);
    }
    const viewerBody = document.getElementById("gym-photo-viewer-body");
    if (viewerBody) {
        bindGymPhotoSwipe(viewerBody);
    }
}

function openGymPhotoViewer(event) {
    if (event.target.closest(".gym-save-btn")) {
        return;
    }
    const slide = event.currentTarget;
    const indexAttr = slide.getAttribute("data-photo-index");
    if (indexAttr !== null) {
        setGymPhotoIndex(parseInt(indexAttr, 10));
    }
    syncGymPhotoViewerImage();
    const viewer = document.getElementById("gym-photo-viewer");
    if (!viewer) {
        return;
    }
    viewer.classList.remove("hidden");
    viewer.hidden = false;
    gymPhotoViewerOpen = true;
    history.pushState({ gymPhotoViewer: true }, "");
}

function closeGymPhotoViewer(event) {
    if (event) {
        const onCloseBtn = event.target.closest(".gym-photo-viewer-close");
        const onBackdrop = event.target.classList.contains("gym-photo-viewer");
        if (!onCloseBtn && !onBackdrop) {
            return;
        }
    }
    const viewer = document.getElementById("gym-photo-viewer");
    if (!viewer || viewer.hidden) {
        return;
    }
    viewer.classList.add("hidden");
    viewer.hidden = true;
    gymPhotoViewerOpen = false;
}

window.addEventListener("popstate", () => {
    if (gymPhotoViewerOpen) {
        closeGymPhotoViewer();
        gymPhotoViewerOpen = false;
    }
});

function equipmentStatusParts(status, quantity) {
    if (status === "confirmed") {
        if (quantity && quantity !== "?") {
            return { word: "Confirmed", qty: quantity };
        }
        return { word: "Confirmed", qty: "" };
    }
    if (status === "missing") {
        return { word: "Missing", qty: "" };
    }
    return { word: "Assumed", qty: "" };
}

function updateEquipmentStatusPill(labelEl, status, quantity) {
    const parts = equipmentStatusParts(status, quantity);
    labelEl.classList.remove("gym-equip-status--confirmed", "gym-equip-status--assumed", "gym-equip-status--missing");
    labelEl.classList.add(`gym-equip-status--${status}`);
    const wordEl = labelEl.querySelector(".gym-equip-status-word");
    const qtyEl = labelEl.querySelector(".gym-equip-status-qty");
    if (wordEl) {
        wordEl.textContent = parts.word;
    }
    if (qtyEl) {
        qtyEl.textContent = parts.qty ? parts.qty : "";
    }
}

function syncGymEquipmentQuantityField() {
    const wrap = document.getElementById("gym-equipment-quantity-wrap");
    const input = document.getElementById("gym-equipment-quantity-input");
    if (!wrap || !input) {
        return;
    }
    const showQty = gymEquipmentModalStatus === "confirmed";
    wrap.classList.toggle("hidden", !showQty);
    wrap.hidden = !showQty;
    if (showQty && gymEquipmentModalQuantity && gymEquipmentModalQuantity !== "?") {
        input.value = gymEquipmentModalQuantity;
    } else {
        input.value = "";
    }
}

function setGymEquipmentModalStatusButtons() {
    document.querySelectorAll("#gym-equipment-item-modal .gym-status-btn").forEach((btn) => {
        const status = btn.getAttribute("data-status");
        btn.classList.remove("is-active", "is-confirmed", "is-assumed", "is-missing", "is-stay");
        if (status === gymEquipmentModalStatus) {
            btn.classList.add("is-active");
            if (status === "confirmed") {
                btn.classList.add("is-confirmed");
            }
            if (status === "missing") {
                btn.classList.add("is-missing");
            }
            if (status === "assumed") {
                btn.classList.add("is-stay");
            }
        }
    });
    syncGymEquipmentQuantityField();
}

function openGymEquipmentItemModal(event) {
    const row = event.currentTarget;
    gymEquipmentModalSlug = row.getAttribute("data-equipment-slug");
    gymEquipmentModalStatus = row.getAttribute("data-equipment-status");
    gymEquipmentModalQuantity = row.getAttribute("data-equipment-quantity");
    const title = document.getElementById("gym-equipment-item-modal-title");
    const slugInput = document.getElementById("gym-equipment-item-slug");
    if (title) {
        title.textContent = row.getAttribute("data-equipment-name");
    }
    if (slugInput) {
        slugInput.value = gymEquipmentModalSlug;
    }
    setGymEquipmentModalStatusButtons();
    const modal = document.getElementById("gym-equipment-item-modal");
    if (modal) {
        modal.style.display = "flex";
    }
}

function pickGymEquipmentItemStatus(event) {
    gymEquipmentModalStatus = event.currentTarget.getAttribute("data-status");
    setGymEquipmentModalStatusButtons();
}

function applyGymEquipmentItemModal() {
    const row = document.querySelector(`[data-equipment-slug="${gymEquipmentModalSlug}"]`);
    if (!row) {
        return;
    }
    let quantity = gymEquipmentModalQuantity;
    if (gymEquipmentModalStatus === "confirmed") {
        const input = document.getElementById("gym-equipment-quantity-input");
        const raw = input ? input.value.trim() : "";
        quantity = raw === "" ? "?" : raw;
    }
    row.setAttribute("data-equipment-status", gymEquipmentModalStatus);
    row.setAttribute("data-equipment-quantity", quantity);
    const labelEl = row.querySelector("[data-equipment-status-label]");
    if (labelEl) {
        updateEquipmentStatusPill(labelEl, gymEquipmentModalStatus, quantity);
    }
    const modal = document.getElementById("gym-equipment-item-modal");
    if (modal) {
        modal.style.display = "none";
    }
    filterGymEquipment();
}

function toggleGymEquipmentStatusFilter(event) {
    const btn = event.currentTarget;
    const pressed = btn.getAttribute("aria-pressed") !== "true";
    btn.setAttribute("aria-pressed", pressed ? "true" : "false");
    btn.classList.toggle("is-active", pressed);
    filterGymEquipment();
}

function filterGymEquipment() {
    const searchInput = document.getElementById("gym-equipment-search");
    const bodypartSelect = document.getElementById("gym-equipment-bodypart-filter");
    const query = searchInput ? searchInput.value.trim().toLowerCase() : "";
    const bodypart = bodypartSelect ? bodypartSelect.value : "";
    const allowed = new Set();
    document.querySelectorAll("#gym-panel-equipment .gym-status-btns .gym-status-btn[data-status]").forEach((btn) => {
        if (btn.getAttribute("aria-pressed") === "true") {
            allowed.add(btn.getAttribute("data-status"));
        }
    });
    document.querySelectorAll("[data-equipment-group]").forEach((group) => {
        const groupMatch = bodypart === "" || group.getAttribute("data-equipment-group") === bodypart;
        let anyVisible = false;
        group.querySelectorAll("[data-equipment-row]").forEach((row) => {
            const name = (row.getAttribute("data-equipment-name") || "").toLowerCase();
            const status = row.getAttribute("data-equipment-status");
            const show = groupMatch && name.includes(query) && allowed.has(status);
            row.classList.toggle("hidden", !show);
            row.hidden = !show;
            if (show) {
                anyVisible = true;
            }
        });
        group.classList.toggle("hidden", !anyVisible);
        group.hidden = !anyVisible;
    });
}

let gymPricesPlans = [];
let gymPricesEditSnapshot = [];

const GYM_VIBE_LABELS = {
    unknown: "Unknown",
    serious: "Serious",
    casual: "Casual",
};

function showGymModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "flex";
    }
}

function hideGymModalById(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        hideGainzModal(modal);
    }
}

function commitFormDefaults(form) {
    if (!form) {
        return;
    }
    form.querySelectorAll("input, textarea, select").forEach((el) => {
        if (el.type === "checkbox") {
            el.defaultChecked = el.checked;
        } else {
            el.defaultValue = el.value;
        }
    });
}

function ruleBadgeHtml(state) {
    if (state === "yes") {
        return '<span class="gym-fact-badge gym-fact-badge--yes">Yes</span>';
    }
    if (state === "no") {
        return '<span class="gym-fact-badge gym-fact-badge--no">No</span>';
    }
    return '<span class="gym-fact-badge gym-fact-badge--unknown">Unknown</span>';
}

function stripGymPriceNumber(raw) {
    return raw.replace(/€/g, "").trim();
}

function formatGymPriceDisplay(raw) {
    const stripped = stripGymPriceNumber(raw);
    if (stripped === "") {
        return "";
    }
    return "€" + stripped;
}

function parseGymPricesFromTable() {
    const tbody = document.getElementById("gym-prices-table-body");
    if (!tbody) {
        return [];
    }
    const plans = [];
    tbody.querySelectorAll("tr").forEach((row) => {
        const nameEl = row.querySelector(".fw-700");
        const metaEl = row.querySelector(".gym-price-plan-meta");
        const priceEl = row.querySelector("td:last-child");
        if (!nameEl || !priceEl) {
            return;
        }
        let period = "";
        let note = "";
        if (metaEl) {
            const metaText = metaEl.textContent.trim();
            const parts = metaText.split(" · ");
            period = parts[0] || "";
            note = parts.slice(1).join(" · ");
        }
        plans.push({
            name: nameEl.textContent.trim(),
            period: period,
            note: note,
            price: stripGymPriceNumber(priceEl.textContent.trim()),
        });
    });
    return plans;
}

function gymPriceSubtitle(plan) {
    if (!plan.period && !plan.note) {
        return "";
    }
    if (plan.period && plan.note) {
        return `${plan.period} · ${plan.note}`;
    }
    return plan.period || plan.note;
}

function splitGymPriceSubtitle(raw) {
    if (!raw) {
        return { period: "", note: "" };
    }
    if (raw.includes(" · ")) {
        const parts = raw.split(" · ");
        return { period: parts[0], note: parts.slice(1).join(" · ") };
    }
    return { period: raw, note: "" };
}

function renderGymPricesTable(plans) {
    const tbody = document.getElementById("gym-prices-table-body");
    if (!tbody) {
        return;
    }
    tbody.innerHTML = "";
    plans.forEach((plan) => {
        const tr = document.createElement("tr");
        const meta = gymPriceSubtitle(plan);
        tr.innerHTML = `
            <td>
                <span class="fw-700">${plan.name}</span>
                <span class="text-sm text-muted gym-price-plan-meta">${meta}</span>
            </td>
            <td class="fw-700 gym-price-cell">${formatGymPriceDisplay(plan.price)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function renderGymPriceEditTable(plans) {
    const tbody = document.getElementById("gym-prices-table-body");
    if (!tbody) {
        return;
    }
    tbody.innerHTML = "";
    plans.forEach((plan) => appendGymPriceEditRow(plan));
}

function computeGymPriceHeadlines(plans) {
    let dayPass = "—";
    let subscription = "—";
    plans.forEach((plan) => {
        if (plan.name.toLowerCase() === "day pass") {
            dayPass = formatGymPriceDisplay(plan.price);
        }
    });
    let cheapestMonthly = null;
    plans.forEach((plan) => {
        const nameLower = plan.name.toLowerCase();
        if (nameLower === "day pass") {
            return;
        }
        const noteLower = (plan.note || "").toLowerCase();
        const periodLower = (plan.period || "").toLowerCase();
        if (noteLower.includes("/ month") || noteLower.includes("≈") || periodLower.includes("12 month") || periodLower.includes("year")) {
            const match = (plan.note || formatGymPriceDisplay(plan.price)).match(/€[\d.,]+/);
            if (match) {
                const val = match[0];
                if (!cheapestMonthly) {
                    cheapestMonthly = val + " / mo";
                }
            }
        }
        if (nameLower.includes("yearly") && plan.note) {
            const match = plan.note.match(/€[\d.,]+/);
            if (match && !cheapestMonthly) {
                cheapestMonthly = match[0] + " / mo";
            }
        }
    });
    if (!cheapestMonthly && plans.length > 1) {
        const fallback = plans.find((p) => p.name.toLowerCase() !== "day pass");
        if (fallback) {
            subscription = formatGymPriceDisplay(fallback.price);
        }
    } else if (cheapestMonthly) {
        subscription = cheapestMonthly;
    }
    return { dayPass, subscription };
}

function updateGymPriceHeadlineCards(plans) {
    const headlines = computeGymPriceHeadlines(plans);
    const dayEl = document.getElementById("gym-price-headline-day");
    const subEl = document.getElementById("gym-price-headline-subscription");
    if (dayEl) {
        dayEl.textContent = headlines.dayPass;
    }
    if (subEl) {
        subEl.textContent = headlines.subscription;
    }
}

function setGymPricesMode(editMode) {
    const editBtn = document.getElementById("gym-prices-edit-btn");
    const addBtn = document.getElementById("gym-prices-add-row");
    const actions = document.getElementById("gym-prices-edit-actions");
    const deleteHead = document.getElementById("gym-prices-delete-head");
    if (editBtn) {
        editBtn.classList.toggle("hidden", editMode);
        editBtn.hidden = editMode;
    }
    if (addBtn) {
        addBtn.classList.toggle("hidden", !editMode);
        addBtn.hidden = !editMode;
    }
    if (actions) {
        actions.classList.toggle("hidden", !editMode);
        actions.hidden = !editMode;
    }
    if (deleteHead) {
        deleteHead.classList.toggle("hidden", !editMode);
        deleteHead.hidden = !editMode;
    }
}

function appendGymPriceEditRow(plan) {
    const tbody = document.getElementById("gym-prices-table-body");
    if (!tbody) {
        return;
    }
    const tr = document.createElement("tr");
    tr.className = "gym-price-edit-row";
    const name = document.createElement("input");
    name.type = "text";
    name.className = "form-control gym-price-edit-name";
    name.value = plan.name || "";
    name.placeholder = "Title";
    name.setAttribute("aria-label", "Title");
    const subtitle = document.createElement("input");
    subtitle.type = "text";
    subtitle.className = "form-control gym-price-edit-period";
    subtitle.value = gymPriceSubtitle(plan);
    subtitle.placeholder = "Subtitle";
    subtitle.setAttribute("aria-label", "Subtitle");
    const price = document.createElement("input");
    price.type = "text";
    price.className = "form-control gym-price-edit-price";
    price.value = stripGymPriceNumber(plan.price || "");
    price.placeholder = "Price";
    price.setAttribute("aria-label", "Price");
    price.setAttribute("inputmode", "decimal");
    const planCell = document.createElement("td");
    planCell.className = "gym-price-edit-plan";
    planCell.appendChild(name);
    planCell.appendChild(subtitle);
    const priceCell = document.createElement("td");
    priceCell.className = "gym-price-cell";
    priceCell.appendChild(price);
    const deleteCell = document.createElement("td");
    deleteCell.className = "gym-price-edit-delete";
    const deleteBtn = document.createElement("button");
    deleteBtn.type = "button";
    deleteBtn.className = "icon-btn icon-btn-danger";
    deleteBtn.setAttribute("data-function", "click->removeGymPriceRow");
    deleteBtn.setAttribute("aria-label", "Delete price");
    deleteBtn.innerHTML = '<i class="fas fa-trash" aria-hidden="true"></i>';
    deleteCell.appendChild(deleteBtn);
    tr.appendChild(planCell);
    tr.appendChild(priceCell);
    tr.appendChild(deleteCell);
    tbody.appendChild(tr);
}

function readGymPriceEditRows() {
    const rows = document.querySelectorAll("#gym-prices-table-body .gym-price-edit-row");
    const plans = [];
    rows.forEach((row) => {
        const name = row.querySelector(".gym-price-edit-name").value.trim();
        const periodRaw = row.querySelector(".gym-price-edit-period").value.trim();
        const price = stripGymPriceNumber(row.querySelector(".gym-price-edit-price").value.trim());
        if (name === "" && price === "") {
            return;
        }
        const split = splitGymPriceSubtitle(periodRaw);
        plans.push({ name, period: split.period, note: split.note, price });
    });
    return plans;
}

function openGymPricesRead() {
    setGymPricesMode(false);
    showGymModal("gym-prices-modal");
}

function enterGymPricesEdit() {
    gymPricesEditSnapshot = JSON.parse(JSON.stringify(gymPricesPlans));
    setGymPricesMode(true);
    renderGymPriceEditTable(gymPricesPlans);
}

function cancelGymPricesEdit() {
    gymPricesPlans = JSON.parse(JSON.stringify(gymPricesEditSnapshot));
    renderGymPricesTable(gymPricesPlans);
    setGymPricesMode(false);
}

function resetGymPricesModal() {
    cancelGymPricesEdit();
}

function saveGymPricesEdit() {
    gymPricesPlans = readGymPriceEditRows();
    gymPricesEditSnapshot = JSON.parse(JSON.stringify(gymPricesPlans));
    renderGymPricesTable(gymPricesPlans);
    updateGymPriceHeadlineCards(gymPricesPlans);
    setGymPricesMode(false);
}

function addGymPriceRow() {
    appendGymPriceEditRow({ name: "", period: "", note: "", price: "" });
}

function removeGymPriceRow(event) {
    const row = event.currentTarget.closest(".gym-price-edit-row");
    if (row) {
        row.remove();
    }
}

function openGymDescriptionEdit() {
    const display = document.getElementById("gym-description-display");
    const input = document.getElementById("gym-edit-description");
    if (display && input) {
        input.value = display.textContent.trim();
        input.defaultValue = input.value;
    }
    showGymModal("gym-edit-description-modal");
}

function saveGymDescriptionEdit() {
    const form = document.getElementById("gym-edit-description-form");
    const input = document.getElementById("gym-edit-description");
    const display = document.getElementById("gym-description-display");
    if (input && display) {
        display.textContent = input.value.trim();
    }
    commitFormDefaults(form);
    hideGymModalById("gym-edit-description-modal");
}

function syncGymVibeEditButtons(vibe) {
    document.querySelectorAll("#gym-edit-vibe-form .gym-status-btn").forEach((btn) => {
        btn.classList.remove("is-active", "is-confirmed", "is-assumed", "is-unknown");
        if (btn.getAttribute("data-vibe") === vibe) {
            btn.classList.add("is-active");
        }
    });
    const hidden = document.getElementById("gym-edit-vibe-value");
    if (hidden) {
        hidden.value = vibe;
    }
}

function openGymVibeEdit() {
    const display = document.getElementById("gym-vibe-display");
    const vibe = display ? display.getAttribute("data-vibe") : "unknown";
    syncGymVibeEditButtons(vibe);
    const hidden = document.getElementById("gym-edit-vibe-value");
    if (hidden) {
        hidden.defaultValue = vibe;
    }
    showGymModal("gym-edit-vibe-modal");
}

function pickGymVibeEdit(event) {
    syncGymVibeEditButtons(event.currentTarget.getAttribute("data-vibe"));
}

function saveGymVibeEdit() {
    const hidden = document.getElementById("gym-edit-vibe-value");
    const display = document.getElementById("gym-vibe-display");
    const vibe = hidden ? hidden.value : "unknown";
    if (display) {
        display.setAttribute("data-vibe", vibe);
        display.textContent = GYM_VIBE_LABELS[vibe] || GYM_VIBE_LABELS.unknown;
    }
    hidden.defaultValue = vibe;
    hideGymModalById("gym-edit-vibe-modal");
}

function syncGymRuleEditRow(slug, state) {
    const row = document.querySelector(`.gym-rule-edit-row[data-rule-slug="${slug}"]`);
    if (!row) {
        return;
    }
    const hidden = row.querySelector(".gym-rule-edit-value");
    if (hidden) {
        hidden.value = state;
    }
    row.querySelectorAll(".gym-rule-state-btn").forEach((btn) => {
        btn.classList.remove("is-active", "is-confirmed", "is-missing", "is-assumed", "is-unknown", "is-stay");
        if (btn.getAttribute("data-state") === state) {
            btn.classList.add("is-active");
            if (state === "yes") {
                btn.classList.add("is-confirmed");
            }
            if (state === "no") {
                btn.classList.add("is-missing");
            }
            if (state === "unknown") {
                btn.classList.add("is-stay");
            }
        }
    });
}

function openGymRulesEdit() {
    document.querySelectorAll("#gym-rules-display .gym-fact-row").forEach((row) => {
        const slug = row.getAttribute("data-rule-slug");
        const state = row.getAttribute("data-rule-state");
        syncGymRuleEditRow(slug, state);
        const hidden = document.querySelector(`.gym-rule-edit-row[data-rule-slug="${slug}"] .gym-rule-edit-value`);
        if (hidden) {
            hidden.defaultValue = state;
        }
    });
    showGymModal("gym-edit-rules-modal");
}

function pickGymRuleEdit(event) {
    const slug = event.currentTarget.getAttribute("data-rule-slug");
    const state = event.currentTarget.getAttribute("data-state");
    syncGymRuleEditRow(slug, state);
}

function saveGymRulesEdit() {
    document.querySelectorAll(".gym-rule-edit-row").forEach((editRow) => {
        const slug = editRow.getAttribute("data-rule-slug");
        const state = editRow.querySelector(".gym-rule-edit-value").value;
        const displayRow = document.querySelector(`#gym-rules-display [data-rule-slug="${slug}"]`);
        if (displayRow) {
            displayRow.setAttribute("data-rule-state", state);
            const labelText = displayRow.querySelector(".text-sm").textContent;
            displayRow.innerHTML = `<span class="text-sm">${labelText}</span>${ruleBadgeHtml(state)}`;
        }
        const hidden = editRow.querySelector(".gym-rule-edit-value");
        hidden.defaultValue = state;
    });
    hideGymModalById("gym-edit-rules-modal");
}

function openGymAmenitiesEdit() {
    const selected = new Set();
    document.querySelectorAll("#gym-amenities-display .gym-amenity-bubble").forEach((bubble) => {
        selected.add(bubble.textContent.trim());
    });
    document.querySelectorAll(".gym-amenity-edit-bubble").forEach((btn) => {
        const label = btn.getAttribute("data-amenity-label");
        const isSelected = selected.has(label);
        btn.classList.toggle("is-selected", isSelected);
        btn.setAttribute("aria-pressed", isSelected ? "true" : "false");
    });
    showGymModal("gym-edit-amenities-modal");
}

function toggleGymAmenityEdit(event) {
    const btn = event.currentTarget;
    const isSelected = btn.classList.toggle("is-selected");
    btn.setAttribute("aria-pressed", isSelected ? "true" : "false");
}

function saveGymAmenitiesEdit() {
    const container = document.getElementById("gym-amenities-display");
    if (!container) {
        return;
    }
    const labels = [];
    document.querySelectorAll(".gym-amenity-edit-bubble.is-selected").forEach((btn) => {
        labels.push(btn.getAttribute("data-amenity-label"));
    });
    labels.sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
    if (labels.length === 0) {
        container.innerHTML = '<p class="text-sm text-muted m-0">No amenity information yet</p>';
    } else {
        container.innerHTML = '<div class="gym-amenity-bubbles"></div>';
        const wrap = container.querySelector(".gym-amenity-bubbles");
        labels.forEach((label) => {
            const span = document.createElement("span");
            span.className = "gym-amenity-bubble";
            span.textContent = label;
            wrap.appendChild(span);
        });
    }
    hideGymModalById("gym-edit-amenities-modal");
}

function syncGymHoursEditRowDisabled(row) {
    const closed = row.querySelector(".gym-hours-edit-closed").checked;
    row.querySelector(".gym-hours-edit-open").disabled = closed;
    row.querySelector(".gym-hours-edit-close").disabled = closed;
}

function openGymHoursEdit() {
    document.querySelectorAll("#gym-hours-display .gym-fact-row").forEach((displayRow) => {
        const day = displayRow.getAttribute("data-day");
        const editRow = document.querySelector(`.gym-hours-edit-row[data-day="${day}"]`);
        if (!editRow) {
            return;
        }
        const closed = displayRow.getAttribute("data-closed") === "true";
        const openSelect = editRow.querySelector(".gym-hours-edit-open");
        const closeSelect = editRow.querySelector(".gym-hours-edit-close");
        const closedInput = editRow.querySelector(".gym-hours-edit-closed");
        openSelect.value = displayRow.getAttribute("data-open");
        closeSelect.value = displayRow.getAttribute("data-close");
        closedInput.checked = closed;
        openSelect.defaultValue = openSelect.value;
        closeSelect.defaultValue = closeSelect.value;
        closedInput.defaultChecked = closed;
        syncGymHoursEditRowDisabled(editRow);
    });
    showGymModal("gym-edit-hours-modal");
}

function saveGymHoursEdit() {
    const displayList = document.getElementById("gym-hours-display");
    let todayHours = "";
    document.querySelectorAll(".gym-hours-edit-row").forEach((editRow) => {
        const day = editRow.getAttribute("data-day");
        const closed = editRow.querySelector(".gym-hours-edit-closed").checked;
        const openVal = editRow.querySelector(".gym-hours-edit-open").value;
        const closeVal = editRow.querySelector(".gym-hours-edit-close").value;
        const displayRow = displayList.querySelector(`[data-day="${day}"]`);
        if (!displayRow) {
            return;
        }
        displayRow.setAttribute("data-open", openVal);
        displayRow.setAttribute("data-close", closeVal);
        displayRow.setAttribute("data-closed", closed ? "true" : "false");
        const timeEl = displayRow.querySelector(".gym-hours-display-time");
        if (closed) {
            timeEl.textContent = "Closed";
        } else {
            timeEl.textContent = `${openVal} – ${closeVal}`;
        }
        if (displayRow.getAttribute("data-is-today") === "true" && !closed) {
            todayHours = `${openVal} – ${closeVal}`;
        }
        if (displayRow.getAttribute("data-is-today") === "true" && closed) {
            todayHours = "Closed";
        }
        const openSelect = editRow.querySelector(".gym-hours-edit-open");
        const closeSelect = editRow.querySelector(".gym-hours-edit-close");
        const closedInput = editRow.querySelector(".gym-hours-edit-closed");
        openSelect.defaultValue = openVal;
        closeSelect.defaultValue = closeVal;
        closedInput.defaultChecked = closed;
    });
    const openNowEl = document.getElementById("gym-open-now-hours");
    if (openNowEl && todayHours) {
        openNowEl.textContent = todayHours;
    }
    hideGymModalById("gym-edit-hours-modal");
}

function openGymContactEdit() {
    const form = document.getElementById("gym-edit-contact-form");
    const fields = [
        { kind: "phone", id: "gym-edit-phone" },
        { kind: "email", id: "gym-edit-email" },
        { kind: "website", id: "gym-edit-website" },
        { kind: "instagram", id: "gym-edit-instagram" },
    ];
    fields.forEach(({ kind, id }) => {
        const input = document.getElementById(id);
        const row = document.querySelector(`#gym-contact-display [data-contact-kind="${kind}"]`);
        if (input && row) {
            input.value = row.querySelector("span").textContent.trim();
        } else if (input && !row) {
            input.value = "";
        }
        if (input) {
            input.defaultValue = input.value;
        }
    });
    showGymModal("gym-edit-contact-modal");
}

function saveGymContactEdit() {
    const phone = document.getElementById("gym-edit-phone").value.trim();
    const email = document.getElementById("gym-edit-email").value.trim();
    const website = document.getElementById("gym-edit-website").value.trim();
    let instagramHandle = document.getElementById("gym-edit-instagram").value.trim();
    instagramHandle = instagramHandle.replace(/^@/, "");
    const container = document.getElementById("gym-contact-display");
    const items = [];
    if (phone) {
        items.push({ kind: "phone", href: `tel:${phone}`, icon: "fas fa-phone", text: phone });
    }
    if (email) {
        items.push({ kind: "email", href: `mailto:${email}`, icon: "fas fa-envelope", text: email });
    }
    if (website) {
        items.push({ kind: "website", href: website, icon: "fas fa-globe", text: website });
    }
    if (instagramHandle) {
        items.push({
            kind: "instagram",
            href: `https://instagram.com/${instagramHandle}`,
            icon: "fab fa-instagram",
            text: instagramHandle,
        });
    }
    if (items.length === 0) {
        container.innerHTML = '<p class="text-sm text-muted m-0">No contact information yet</p>';
    } else {
        container.innerHTML = '<ul class="gym-contact-list"></ul>';
        const list = container.querySelector(".gym-contact-list");
        items.forEach((item) => {
            const li = document.createElement("li");
            li.className = "gym-contact-row";
            li.setAttribute("data-contact-kind", item.kind);
            li.innerHTML = `
                <a class="gym-contact-link row-center gap-sm text-sm" href="${item.href}" rel="noopener noreferrer">
                    <i class="${item.icon}" aria-hidden="true"></i>
                    <span>${item.text}</span>
                </a>
            `;
            list.appendChild(li);
        });
    }
    commitFormDefaults(document.getElementById("gym-edit-contact-form"));
    hideGymModalById("gym-edit-contact-modal");
}

function formatGymAddress(street, postalCode, city, country) {
    const locality = [postalCode, city].filter(Boolean).join(" ");
    return [street, locality, country].filter(Boolean).join(", ");
}

function openGymLocationEdit() {
    const display = document.getElementById("gym-address-display");
    const street = document.getElementById("gym-edit-street");
    const postalCode = document.getElementById("gym-edit-postal-code");
    const city = document.getElementById("gym-edit-address-city");
    const country = document.getElementById("gym-edit-country");
    if (display && street && postalCode && city && country) {
        street.value = display.getAttribute("data-street") || "";
        postalCode.value = display.getAttribute("data-postal-code") || "";
        city.value = display.getAttribute("data-city") || "";
        country.value = display.getAttribute("data-country") || "";
        street.defaultValue = street.value;
        postalCode.defaultValue = postalCode.value;
        city.defaultValue = city.value;
        country.defaultValue = country.value;
    }
    showGymModal("gym-edit-location-modal");
}

function saveGymLocationEdit() {
    const street = document.getElementById("gym-edit-street").value.trim();
    const postalCode = document.getElementById("gym-edit-postal-code").value.trim();
    const city = document.getElementById("gym-edit-address-city").value.trim();
    const country = document.getElementById("gym-edit-country").value.trim();
    const display = document.getElementById("gym-address-display");
    const address = formatGymAddress(street, postalCode, city, country);
    if (display) {
        display.textContent = address;
        display.href = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(address)}`;
        display.setAttribute("data-street", street);
        display.setAttribute("data-postal-code", postalCode);
        display.setAttribute("data-city", city);
        display.setAttribute("data-country", country);
    }
    commitFormDefaults(document.getElementById("gym-edit-location-form"));
    hideGymModalById("gym-edit-location-modal");
}

document.addEventListener("DOMContentLoaded", () => {
    initGymPhotoCarousel();
    gymPricesPlans = parseGymPricesFromTable();
    gymPricesEditSnapshot = JSON.parse(JSON.stringify(gymPricesPlans));
    document.querySelectorAll(".gym-hours-edit-row").forEach((row) => {
        const closedInput = row.querySelector(".gym-hours-edit-closed");
        closedInput.addEventListener("change", () => syncGymHoursEditRowDisabled(row));
        syncGymHoursEditRowDisabled(row);
    });
});
