import { setupTogglePanel } from "./togglePanel.js";
import { setupTooltips } from "./tooltip.js";
import { setupFormSwitcher } from "./formSwitcher.js";
import { isValidVinChecksum } from "./validateVinChecksum.js";
import { setupFileUpload } from './fileUpload.js';

import JustValidate from 'just-validate';

document.addEventListener("DOMContentLoaded", () => {
  setupFormSwitcher();
  setupTogglePanel({
    panelId: "slickSheet",
    backdropId: "slickSheetBackdrop",
    openBtnId: "togglePanelBtn",
    closeBtnId: "closePanelBtn"
  });
  setupTooltips();
    setupFileUpload({
    inputId: "file-input",
    listId: "files-list",
    counterId: "num-of-files"
  });
  
const validator = new JustValidate('#productInfo', {
  validateOnInput: true,
  errorLabelCssClass: 'form__error-label',
});

document.querySelectorAll('#productInfo input, #productInfo select').forEach((el) => {
  el.addEventListener('input', () => {
    const selector = el.id ? `#${el.id}` : `[name="${el.name}"]`;
    validator.revalidateField(selector);
  });
});



  validator
    // Satış Kategorisi
    .addField('#town', [
      {
        rule: 'customRegexp',
        value: /^(?!0$)/,
        errorMessage: 'Lütfen satış kategorisi seçin',
      },
    ])

    // Satış Fiyatı
    .addField('[name="price"]', [
      {
        rule: 'required',
        errorMessage: 'Satış fiyatı zorunludur',
      },
      {
        rule: 'number',
        errorMessage: 'Geçerli bir sayı girin',
      },
    ])

    // Şase No
    .addField('#vinInput', [
        {
        rule: 'required',
        errorMessage: 'Şase numarası zorunludur',
        },
        {
        rule: 'customRegexp',
        value: /^[A-HJ-NPR-Z0-9]{17}$/,
        errorMessage: 'Geçerli bir 17 karakterlik VIN girin',
        },
        {
        validator: (value) => isValidVinChecksum(value.toUpperCase()),
        errorMessage: 'Geçersiz VIN numarası (kontrol hanesi yanlış)',
        }
    ])

    // Plaka
    .addField('[name="numberplate"]', [
    {
        rule: 'required',
        errorMessage: 'Plaka zorunludur',
    },
    {
        rule: 'customRegexp',
        value: /^(0[1-9]|[1-7][0-9]|8[01])\s?[A-Z]{1,3}\s?[0-9]{1,4}$/,
        errorMessage: 'Geçerli bir plaka girin (örn: 34 ABC 123)',
    },
    ])

    // Marka
    .addField('#brand', [
      {
        rule: 'customRegexp',
        value: /^(?!0$)/,
        errorMessage: 'Marka seçin',
      },
    ])

    // Model
    .addField('#model', [
      {
        rule: 'customRegexp',
        value: /^(?!0$)/,
        errorMessage: 'Model seçin',
      },
    ])

    // Yıl
    .addField('[name="year"]', [
      {
        rule: 'required',
        errorMessage: 'Yıl zorunludur',
      },
      {
        rule: 'number',
        errorMessage: 'Yıl sadece sayı olmalıdır',
      },
      {
        rule: 'minNumber',
        value: 1950,
        errorMessage: 'Geçerli bir yıl girin',
      },
      {
        rule: 'maxNumber',
        value: new Date().getFullYear(),
        errorMessage: 'Gelecek yıl girilemez',
      },
    ])

    // Ruhsat Fotoğrafı (file input)
    .addField('#file-input', [
      {
        validator: () => {
          const input = document.querySelector('#file-input');
          return input && input.files && input.files.length > 0;
        },
        errorMessage: 'En az bir dosya seçmelisiniz',
      },
    ])

    // Submit başarılıysa
    .onSuccess((event) => {
      console.log('Form geçerli, gönderiliyor...');
      event.target.submit();
    })

    // Hata varsa konsola logla (debug için)
    .onFail((fields) => {
      console.warn('Geçersiz alanlar:', fields);
    });

    document.querySelector('[name="numberplate"]').addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
    });

});
