export function setupWizard({ step1Id, step2Id, nextBtnId, backBtnId }) {
    const step1 = document.getElementById(step1Id);
    const step2 = document.getElementById(step2Id);
    const nextBtn = document.getElementById(nextBtnId);
    const backBtn = document.getElementById(backBtnId);

    if (!step1 || !step2 || !nextBtn || !backBtn) {
        console.error("Wizard elemanları eksik.");
        return;
    }

    function goToStep2() {
        step1.classList.add("hidden");
        step2.classList.remove("hidden");
    }

    function goToStep1() {
        step2.classList.add("hidden");
        step1.classList.remove("hidden");
    }

    nextBtn.addEventListener("click", goToStep2);
    backBtn.addEventListener("click", goToStep1);
}
