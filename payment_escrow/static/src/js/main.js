import { setupAccordion } from "./accordion.js";
import { setupTabSwitcher } from "./tabSwitcher.js";
import { setupWizard } from "./wizard.js";
import { setupToggle } from "./toggle.js";
import { setupTogglePanel } from "./togglePanel.js";
import { setupTooltips } from "./tooltip.js";
import { setupToggleSummaryPanel } from "./toggleSummaryPanel.js";
import { setupFormSwitcher } from "./formSwitcher.js";
import { setupVinMask } from "./vinMask.js";



import { setupModal } from "./modal.js";

document.addEventListener("DOMContentLoaded", () => {
  setupFormSwitcher();
  setupVinMask();
//   setupAccordion(".paymentMethod");
//   setupTabSwitcher(
//     "paymentWithCreditCardBtn",
//     "paymentWithSavedCardBtn",
//     "creditCardWrapper",
//     "saveCardWrapper"
//   );
//   setupWizard({
//     step1Id: "shoppingCreditStep1",
//     step2Id: "shoppingCreditStep2",
//     nextBtnId: "shoppingCreditStep1Btn",
//     backBtnId: "shoppingCreditStep2Btn"
// });
// setupToggle({
//   buttonId: "save_card",
//   panelId: "saveCardPanel"
// });
setupTogglePanel({
  panelId: "slickSheet",
  backdropId: "slickSheetBackdrop",
  openBtnId: "togglePanelBtn",
  closeBtnId: "closePanelBtn"
});
// setupToggleSummaryPanel({
//   panelId: "summaryWrapper",
//   backdropId: "slickSheetSummaryBackdrop",
//   openBtnId: "showSummaryBtn",
//   closeBtnId: "closeSummaryPanelBtn"
// });
// setupToggle({
//   buttonId: "showBilling",
//   panelId: "billingPanel"
// });
setupTooltips();
//   setupModal({
//     modalId: "showAllInstallmentModal",
//     openBtnId: "showAllInstallmentBtn",
//     closeBtnId: "closeModalBtn",
//     closeOnEscape: true,
//     closeOnBackdropClick: true
// });
});
