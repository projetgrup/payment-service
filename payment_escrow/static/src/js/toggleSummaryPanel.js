export function setupToggleSummaryPanel({ panelId, backdropId, openBtnId, closeBtnId }) {
    const panel = document.getElementById(panelId);
    const backdrop = document.getElementById(backdropId);
    const openBtn = document.getElementById(openBtnId);
    const closeBtn = document.getElementById(closeBtnId);

    if (!panel || !backdrop || !openBtn || !closeBtn) {
        console.error("Panel elemanları bulunamadı.");
        return;
    }

    function openPanel() {
        panel.classList.add("active");
        backdrop.classList.add("active");
        document.querySelector(".summary__bottomPanel").classList.add("-open");
    }

    function closePanel() {
        panel.classList.remove("active");
        backdrop.classList.remove("active");
        document.querySelector(".summary__bottomPanel").classList.remove("-open");
    }

    function handleKeyDown(event) {
        if (event.key === "Escape") {
            closePanel();
        }
    }

    function handleBackdropClick(event) {
        if (event.target === backdrop) {
            closePanel();
        }
    }

    openBtn.addEventListener("click", openPanel);
    closeBtn.addEventListener("click", closePanel);
    backdrop.addEventListener("click", handleBackdropClick);
    window.addEventListener("keydown", handleKeyDown);
}
