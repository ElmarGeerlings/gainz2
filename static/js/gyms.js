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

function equipmentToneClass(status) {
    if (status === "confirmed") {
        return "gym-tone-yes";
    }
    if (status === "missing") {
        return "gym-tone-no";
    }
    return "gym-tone-unknown";
}

function updateEquipmentStatusPill(labelEl, status, quantity) {
    const parts = equipmentStatusParts(status, quantity);
    labelEl.classList.remove("gym-tone-yes", "gym-tone-unknown", "gym-tone-no");
    labelEl.classList.add(equipmentToneClass(status));
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
    const statusRadio = document.querySelector(`#gym-equipment-item-modal input[name="equipment_status"][value="${value}"]`)(gymEquipmentModalStatus);
    if (statusRadio) {
        statusRadio.checked = true;
        statusRadio.defaultChecked = true;
        document.querySelectorAll('#gym-equipment-item-modal input[name="equipment_status"]').forEach((radio) => {
            if (radio !== statusRadio) {
                radio.defaultChecked = false;
            }
        });
    }
    syncGymEquipmentQuantityField();
    const modal = document.getElementById("gym-equipment-item-modal");
    if (modal) {
        modal.style.display = "flex";
    }
}

function pickGymEquipmentItemStatus(event) {
    gymEquipmentModalStatus = event.currentTarget.value;
    syncGymEquipmentQuantityField();
}

function applyGymEquipmentItemModal() {
    const row = document.querySelector(`[data-equipment-slug="${gymEquipmentModalSlug}"]`);
    if (!row) {
        return;
    }
    const checked = document.querySelector('#gym-equipment-item-modal input[name="equipment_status"]:checked');
    if (checked) {
        gymEquipmentModalStatus = checked.value;
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
    document.querySelectorAll("#gym-panel-equipment .gym-status-btns .gym-status-btn[data-value]").forEach((btn) => {
        if (btn.getAttribute("aria-pressed") === "true") {
            allowed.add(btn.getAttribute("data-value"));
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

let gymPricesEditKind = "membership";

const gymPriceKinds = [
    { kind: "membership", readBodyId: "gym-prices-membership-body", editBodyId: "gym-prices-edit-membership-body", editWrapId: "gym-prices-edit-membership-wrap", isMembership: true },
    { kind: "other", readBodyId: "gym-prices-other-body", editBodyId: "gym-prices-edit-other-body", editWrapId: "gym-prices-edit-other-wrap", isMembership: false },
];

function gymPriceKindConfig(kind) {
    return gymPriceKinds.find((entry) => entry.kind === kind);
}

function cloneGymPriceEditRow(isMembership) {
    const templateId = isMembership ? "gym-price-edit-row-template" : "gym-price-edit-extra-row-template";
    const template = document.getElementById(templateId);
    return template.content.firstElementChild.cloneNode(true);
}

function fillGymPriceEditRow(row, readTr) {
    row.querySelector(".gym-price-edit-name").value = readTr.getAttribute("data-title") || "";
    row.querySelector(".gym-price-edit-note").value = readTr.getAttribute("data-subtitle") || "";
    row.querySelector(".gym-price-edit-price").value = readTr.getAttribute("data-amount") || "";
    const countInput = row.querySelector(".gym-price-edit-count");
    const unitInput = row.querySelector(".gym-price-edit-unit");
    if (countInput) {
        countInput.value = readTr.getAttribute("data-billing-count") || "1";
    }
    if (unitInput) {
        unitInput.value = readTr.getAttribute("data-billing-unit") || "month";
    }
}

function setGymPricesMode(editMode) {
    const readWrap = document.getElementById("gym-prices-read");
    const editWrap = document.getElementById("gym-prices-edit");
    const readHeader = document.getElementById("gym-prices-read-header");
    const editHeader = document.getElementById("gym-prices-edit-header");
    const editBtn = document.getElementById("gym-prices-edit-btn");
    const addBtn = document.getElementById("gym-prices-add-row");
    const actions = document.getElementById("gym-prices-edit-actions");
    if (readWrap) {
        readWrap.classList.toggle("hidden", editMode);
        readWrap.hidden = editMode;
    }
    if (editWrap) {
        editWrap.classList.toggle("hidden", !editMode);
        editWrap.hidden = !editMode;
    }
    if (readHeader) {
        readHeader.classList.toggle("hidden", editMode);
        readHeader.hidden = editMode;
    }
    if (editHeader) {
        editHeader.classList.toggle("hidden", !editMode);
        editHeader.hidden = !editMode;
    }
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
}

function switchGymPricesKind(event) {
    const kind = event.currentTarget.getAttribute("data-kind");
    if (!kind || kind === gymPricesEditKind) {
        return;
    }
    gymPricesEditKind = kind;
    document.querySelectorAll(".gym-prices-kind-btn").forEach((btn) => {
        btn.classList.remove("btn-primary");
        btn.classList.add("btn-outline");
    });
    event.currentTarget.classList.remove("btn-outline");
    event.currentTarget.classList.add("btn-primary");
    gymPriceKinds.forEach((entry) => {
        const wrap = document.getElementById(entry.editWrapId);
        const show = entry.kind === kind;
        wrap.classList.toggle("hidden", !show);
        wrap.hidden = !show;
    });
    const active = gymPriceKindConfig(kind);
    syncGymPriceRowMoveButtons(document.getElementById(active.editBodyId));
}

function readGymPriceEditRows() {
    const plans = [];
    gymPriceKinds.forEach((entry) => {
        const tbody = document.getElementById(entry.editBodyId);
        if (!tbody) {
            return;
        }
        tbody.querySelectorAll(".gym-price-edit-row").forEach((row) => {
            const title = row.querySelector(".gym-price-edit-name").value.trim();
            const subtitle = row.querySelector(".gym-price-edit-note").value.trim();
            const amount = row.querySelector(".gym-price-edit-price").value.trim();
            if (title === "" && amount === "") {
                return;
            }
            const plan = { title, subtitle, amount, is_membership: entry.isMembership };
            if (entry.isMembership) {
                const billing_count = row.querySelector(".gym-price-edit-count").value.trim() || "1";
                const billing_unit = row.querySelector(".gym-price-edit-unit").value;
                plan.billing_count = billing_count;
                plan.billing_unit = billing_unit;
            }
            plans.push(plan);
        });
    });
    return plans;
}

function resetGymPricesEditKind() {
    gymPricesEditKind = "membership";
    document.querySelectorAll(".gym-prices-kind-btn").forEach((btn) => {
        const isMember = btn.getAttribute("data-kind") === "membership";
        btn.classList.toggle("btn-primary", isMember);
        btn.classList.toggle("btn-outline", !isMember);
    });
    gymPriceKinds.forEach((entry) => {
        const wrap = document.getElementById(entry.editWrapId);
        const show = entry.kind === "membership";
        wrap.classList.toggle("hidden", !show);
        wrap.hidden = !show;
    });
}

function enterGymPricesEdit() {
    gymPriceKinds.forEach((entry) => {
        const readBody = document.getElementById(entry.readBodyId);
        const editBody = document.getElementById(entry.editBodyId);
        editBody.innerHTML = "";
        if (!readBody) {
            return;
        }
        readBody.querySelectorAll("tr").forEach((readTr) => {
            const row = cloneGymPriceEditRow(entry.isMembership);
            fillGymPriceEditRow(row, readTr);
            editBody.appendChild(row);
        });
        syncGymPriceRowMoveButtons(editBody);
    });
    resetGymPricesEditKind();
    setGymPricesMode(true);
}

function cancelGymPricesEdit() {
    gymPriceKinds.forEach((entry) => {
        const editBody = document.getElementById(entry.editBodyId);
        if (editBody) {
            editBody.innerHTML = "";
        }
    });
    resetGymPricesEditKind();
    setGymPricesMode(false);
}

function saveGymPricesEdit(event) {
    const trigger = event.currentTarget;
    trigger.setAttribute("prices", JSON.stringify(readGymPriceEditRows()));
    sendWsRequest("gyms/update_prices", trigger).then((response) => {
        if (response.json_content?.morphs) {
            for (const morph of response.json_content.morphs) {
                const target = document.querySelector(morph.target);
                if (target) {
                    target.innerHTML = morph.html;
                }
            }
        }
        if (response.status === 200) {
            cancelGymPricesEdit();
        }
    });
}

function addGymPriceRow() {
    const entry = gymPriceKindConfig(gymPricesEditKind);
    const tbody = document.getElementById(entry.editBodyId);
    const row = cloneGymPriceEditRow(entry.isMembership);
    tbody.appendChild(row);
    syncGymPriceRowMoveButtons(tbody);
}

function removeGymPriceRow(event) {
    const row = event.currentTarget.closest(".gym-price-edit-row");
    const tbody = row ? row.closest("tbody") : null;
    if (row) {
        row.remove();
        syncGymPriceRowMoveButtons(tbody);
    }
}

function moveGymPriceRow(event) {
    const row = event.currentTarget.closest(".gym-price-edit-row");
    const tbody = row ? row.closest("tbody") : null;
    if (!row || !tbody) {
        return;
    }
    if (event.currentTarget.getAttribute("data-direction") === "up") {
        const previous = row.previousElementSibling;
        if (previous) {
            tbody.insertBefore(row, previous);
        }
    } else {
        const next = row.nextElementSibling;
        if (next) {
            tbody.insertBefore(next, row);
        }
    }
    syncGymPriceRowMoveButtons(tbody);
}

function syncGymPriceRowMoveButtons(tbody) {
    if (!tbody) {
        return;
    }
    const rows = tbody.querySelectorAll(".gym-price-edit-row");
    rows.forEach((row, index) => {
        const upBtn = row.querySelector(".gym-price-move-up");
        const downBtn = row.querySelector(".gym-price-move-down");
        if (upBtn) {
            upBtn.classList.toggle("is-hidden", index === 0);
        }
        if (downBtn) {
            downBtn.classList.toggle("is-hidden", index === rows.length - 1);
        }
    });
}

function syncGymHoursEditRowDisabled(row) {
    const closed = row.querySelector(".gym-hours-edit-closed").checked;
    row.querySelector(".gym-hours-edit-open").disabled = closed;
    row.querySelector(".gym-hours-edit-close").disabled = closed;
}

function onGymHoursClosedChange(event) {
    const row = event.currentTarget.closest(".gym-hours-edit-row");
    if (row) {
        syncGymHoursEditRowDisabled(row);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    initGymPhotoCarousel();
    document.querySelectorAll(".gym-hours-edit-row").forEach((row) => {
        syncGymHoursEditRowDisabled(row);
    });
});
