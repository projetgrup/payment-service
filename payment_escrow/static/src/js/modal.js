export function setupModal({ modalId, openBtnId, closeBtnId, closeOnEscape = true, closeOnBackdropClick = true }) {
    const modal = document.getElementById(modalId);
    const openBtn = document.getElementById(openBtnId);
    const closeBtn = document.getElementById(closeBtnId);
    const modalContainer = modal.querySelector(".modal__container");

    if (!modal || !openBtn || !closeBtn) {
        console.error("Modal elemanları eksik.");
        return;
    }

    function openModal() {
        modal.classList.remove("fade-out");
        modal.classList.add("fade-in");
        modalContainer.classList.remove("slide-out");
        modalContainer.classList.add("slide-in");
        document.body.classList.add("body-no-scroll");

        if (closeOnEscape) {
            window.addEventListener("keydown", handleKeyDown);
        }
    }

    function closeModal() {
        modal.classList.remove("fade-in");
        modal.classList.add("fade-out");
        modalContainer.classList.remove("slide-in");
        modalContainer.classList.add("slide-out");
        document.body.classList.remove("body-no-scroll");

        setTimeout(() => {
            modal.classList.remove("fade-in");
            modal.classList.add("fade-out");
        }, 300); // Animasyon süresi kadar beklet
        window.removeEventListener("keydown", handleKeyDown);
    }

    function handleKeyDown(event) {
        if (event.key === "Escape") {
            closeModal();
        }
    }

    function handleBackdropClick(event) {
        if (closeOnBackdropClick && event.target === modal) {
            closeModal();
        }
    }

    openBtn.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);
    modal.addEventListener("click", handleBackdropClick);
}
