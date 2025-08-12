import { setupToggle } from "./toggle.js";
import { setupTogglePanel } from "./togglePanel.js";
import { setupTooltips } from "./tooltip.js";
import { setupToggleSummaryPanel } from "./toggleSummaryPanel.js";

import { setupModal } from "./modal.js";

document.addEventListener("DOMContentLoaded", () => {
setupToggle({
  buttonId: "showBilling",
  panelId: "billingPanel"
});
setupTogglePanel({
  panelId: "slickSheet",
  backdropId: "slickSheetBackdrop",
  openBtnId: "togglePanelBtn",
  closeBtnId: "closePanelBtn"
});
setupTogglePanel({
  panelId: "addAddress",
  backdropId: "slickSheetAddAddressBackdrop",
  openBtnId: "toggleAddAddressPanelBtn",
  closeBtnId: "closeAddAddressPanelBtn"
});
setupToggleSummaryPanel({
  panelId: "summaryWrapper",
  backdropId: "slickSheetSummaryBackdrop",
  openBtnId: "showSummaryBtn",
  closeBtnId: "closeSummaryPanelBtn"
});

setupTooltips();
//   setupModal({
//     modalId: "showAllInstallmentModal",
//     openBtnId: "showAllInstallmentBtn",
//     closeBtnId: "closeModalBtn",
//     closeOnEscape: true,
//     closeOnBackdropClick: true
// });
});
