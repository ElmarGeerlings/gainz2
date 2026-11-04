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
        btn.classList.remove("is-active", "is-confirmed", "is-assumed", "is-missing");
        if (status === gymEquipmentModalStatus) {
            btn.classList.add("is-active");
            btn.classList.add(`is-${status}`);
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
}

document.addEventListener("DOMContentLoaded", () => {
    initGymPhotoCarousel();
});
