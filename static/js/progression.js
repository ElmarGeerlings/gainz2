let lastProgressionWeightDelta = "0";
let lastProgressionRepsDelta = "0";

function openProgressionStepModal(req_event) {
    if (req_event.target.closest(".icon-btn")) {
        return;
    }
    const trigger = req_event.currentTarget;
    const modalName = trigger.getAttribute("data-modal-name");
    const endpoint = trigger.getAttribute("data-routing");
    if (!trigger.getAttribute("data-step-id")) {
        trigger.setAttribute("data-weight-delta", lastProgressionWeightDelta);
        trigger.setAttribute("data-reps-delta", lastProgressionRepsDelta);
    }
    sendWsRequest(endpoint, trigger).then((response) => {
        const contentEl = document.getElementById(`${modalName}-content`);
        contentEl.innerHTML = response.json_content.html;
        const modal = document.getElementById(modalName);
        if (modal) {
            modal.style.display = "flex";
        }
        const form = contentEl.querySelector("form");
        requestAnimationFrame(() => {
            initValuePickers(contentEl);
            syncPickersFromHidden(form);
            const confirmBtn = form.querySelector(".set-modal-confirm");
            confirmBtn.addEventListener("click", () => {
                lastProgressionWeightDelta = form.querySelector("#progression-step-weight-delta").value;
                lastProgressionRepsDelta = form.querySelector("#progression-step-reps-delta").value;
            });
        });
    });
}

function openProgressionEditModal() {
    const header = document.getElementById("progression-header");
    const section = header.querySelector("section");
    document.getElementById("progression-edit-id").value = section.dataset.templateId;
    document.getElementById("progression-edit-name").value = document.getElementById("progression-name").textContent;
    document.getElementById("progression-edit-notes").value = document.getElementById("progression-notes-text").textContent;
    document.getElementById("progression-modal").style.display = "flex";
}
