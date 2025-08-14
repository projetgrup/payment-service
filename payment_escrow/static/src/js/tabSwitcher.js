export function setupTabSwitcher(creditCardBtnId, saveCardBtnId, creditCardWrapperId, saveCardWrapperId) {
    const creditCardBtn = document.getElementById(creditCardBtnId);
    const saveCardBtn = document.getElementById(saveCardBtnId);
    const creditCardWrapper = document.getElementById(creditCardWrapperId);
    const saveCardWrapper = document.getElementById(saveCardWrapperId);

    if (!creditCardBtn || !saveCardBtn || !creditCardWrapper || !saveCardWrapper) {
        console.error("TabSwitcher: Elemanlar bulunamadı.");
        return;
    }

    function showCreditCard() {
        creditCardWrapper.classList.remove("hidden");
        saveCardWrapper.classList.add("hidden");
    }

    function showSavedCard() {
        saveCardWrapper.classList.remove("hidden");
        creditCardWrapper.classList.add("hidden");
    }

    creditCardBtn.addEventListener("click", showCreditCard);
    saveCardBtn.addEventListener("click", showSavedCard);
}
