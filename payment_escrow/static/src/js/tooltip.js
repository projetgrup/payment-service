export function setupTooltips() {
    const tooltipTriggers = document.querySelectorAll(".tooltip-trigger");
    let activeTooltip = null;
    let activeTrigger = null;

    tooltipTriggers.forEach(trigger => {
        trigger.addEventListener("mouseenter", function () {
            removeAllTooltips(); // Önce var olan tooltip'leri temizle

            activeTrigger = trigger;
            activeTooltip = document.createElement("div");
            activeTooltip.classList.add("tooltip");
            activeTooltip.innerText = trigger.getAttribute("data-tooltip-content");

            document.body.appendChild(activeTooltip);
            updateTooltipPosition(trigger, activeTooltip); // Konumu hesapla

            setTimeout(() => activeTooltip.classList.add("show"), 10);
        });

        trigger.addEventListener("mouseleave", function () {
            removeAllTooltips();
        });

        // Scroll olunca tooltip konumunu güncelle
        window.addEventListener("scroll", function () {
            if (activeTooltip && activeTrigger) {
                updateTooltipPosition(activeTrigger, activeTooltip);
            }
        });
    });
}

// Tooltip Konumunu Dinamik Olarak Hesaplayan Fonksiyon
function updateTooltipPosition(trigger, tooltip) {
    const triggerRect = trigger.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    // Sayfanın scroll durumunu hesaba katarak mutlak konumu al
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;

    let left = triggerRect.left + scrollX + (triggerRect.width / 2) - (tooltipRect.width / 2);
    let top = triggerRect.top + scrollY - tooltipRect.height - 8; // Yukarıda başlasın

    // Eğer yukarıda yeterli alan yoksa, tooltip'i aşağıda göster ve arrow yönünü değiştir
    if (top < window.scrollY) {
        top = triggerRect.bottom + scrollY + 8;
        tooltip.classList.add("tooltip-bottom");
    } else {
        tooltip.classList.remove("tooltip-bottom");
    }

    // Eğer sol tarafa taşıyorsa sağa kaydır
    if (left < scrollX + 5) {
        left = scrollX + 5;
    }

    // Eğer sağ tarafa taşıyorsa sola kaydır
    if (left + tooltipRect.width > window.innerWidth + scrollX - 5) {
        left = window.innerWidth + scrollX - tooltipRect.width - 5;
    }

    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
}

// Tüm tooltip'leri kaldır
function removeAllTooltips() {
    document.querySelectorAll(".tooltip").forEach(t => t.remove());
}
