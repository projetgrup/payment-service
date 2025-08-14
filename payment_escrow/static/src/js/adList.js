
import { setupTogglePanel } from "./togglePanel.js";



document.addEventListener("DOMContentLoaded", () => {
    setupTogglePanel({
        panelId: "slickSheet",
        backdropId: "slickSheetBackdrop",
        openBtnId: "togglePanelBtn",
        closeBtnId: "closePanelBtn"
    });
    setupTogglePanel({
      panelId: "adDetail",
      backdropId: "slickSheetAdDetailBackdrop",
      openBtnId: "toggleAdDetailPanelBtn-1", // buraya butonları dinamik açacağımız için null bırakıyoruz
      closeBtnId: "closeAdDetailPanelBtn"
  });

    document.querySelectorAll('.ad-list-type .add-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            // Butonlarda aktifliği güncelle
            document.querySelectorAll('.ad-list-type .add-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            // Görünümü güncelle
            const view = this.dataset.view;
            const table = document.querySelector('.ad-list-table');
            table.classList.remove('list-view', 'grid-view');
            table.classList.add(view === 'list' ? 'list-view' : 'grid-view');
        });
    });
});
