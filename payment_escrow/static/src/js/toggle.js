export function setupToggle({ buttonId, panelId }) {
    const toggleBtn = document.getElementById(buttonId);
    const togglePanel = document.getElementById(panelId);

    if (!toggleBtn || !togglePanel) {
        console.error("Toggle elemanları bulunamadı.");
        return;
    }

    function togglePanelVisibility() {
        const isActive = togglePanel.classList.contains("-active");

        if (isActive) {
            togglePanel.classList.remove("-active");
        } else {
            togglePanel.classList.add("-active");
        }
    }

    toggleBtn.addEventListener("click", togglePanelVisibility);
}
