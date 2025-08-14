// quantity.js
export function setupQuantityCounter(selector = ".payloxCard__quantity") {
    const containers = document.querySelectorAll(selector);
  
    containers.forEach(container => {
      const input = container.querySelector(".payloxCard__input");
      const decreaseBtn = container.querySelector('[data-action="decrease"]');
      const increaseBtn = container.querySelector('[data-action="increase"]');
  
      if (!input || !decreaseBtn || !increaseBtn) return;
  
      decreaseBtn.addEventListener("click", () => {
        const current = parseInt(input.value, 10) || 1;
        if (current > 1) input.value = current - 1;
      });
  
      increaseBtn.addEventListener("click", () => {
        const current = parseInt(input.value, 10) || 1;
        input.value = current + 1;
      });
    });
  }
  