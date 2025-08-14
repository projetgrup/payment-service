import { setupPartialPriceValidation } from './setupPartialPriceValidation.js';
import { setupFileUpload } from './fileUpload.js';

document.addEventListener('DOMContentLoaded', () => {
  setupPartialPriceValidation();
    setupFileUpload({
      inputId: "file-input",
      listId: "files-list",
      counterId: "num-of-files"
    });
});
