import { setupTogglePanel } from "./togglePanel.js";
import { setupTooltips } from "./tooltip.js";
import { setupFormSwitcher } from "./formSwitcher.js";
import { setupOTPValidation } from './otpInput.js';

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
  setupOTPValidation({
  formId: '#otpBox',
  fieldName: 'otp',
  duration: 120,
  onSubmit: (code) => {
    console.log("Doğrulama kodu:", code);
    // Burada sunucuya doğrulama isteği atabilirsiniz
  }
});
  const form = document.querySelector('#recipientInfo');
  if (!form) return;
  const getUserType = () =>
    document.querySelector('input[name="userType"]:checked')?.value;

  const validator = new JustValidate(form, {
    validateOnInput: true,
    errorLabelCssClass: 'form__error-label',
  });

// ✅ Hot validate tetikleyici (JustValidate 4.x uyumlu)
const registeredSelectors = [
  '#email_individual',
  '#email_corporate',
  '#phone_individual',
  '#phone_corporate',
  '#address_corporate',
  '#address_individual',
  '[name="namesurname"]',
  '[name="taxoffice"]',
  '[name="idendity"]',
  '[name="birthdate"]',
  '[name="corporatetitle"]',
  '[name="taxnumber"]',
  '[name="person"]',
];

form.querySelectorAll('input, select').forEach((el) => {
  const selector = el.id ? `#${el.id}` : `[name="${el.name}"]`;

  if (registeredSelectors.includes(selector)) {
    el.addEventListener('input', () => {
      if (!el.hasAttribute('data-validate-ignore')) {
        validator.revalidateField(selector);
      }
    });
  }
});




  // ✅ Ortak alanlar (id bazlı)
  validator
    .addField('#email_individual', [
      { rule: 'required', errorMessage: 'E-posta zorunludur' },
      { rule: 'email', errorMessage: 'Geçerli bir e-posta giriniz' },
    ])
    .addField('#email_corporate', [
      { rule: 'required', errorMessage: 'E-posta zorunludur' },
      { rule: 'email', errorMessage: 'Geçerli bir e-posta giriniz' },
    ])
    .addField('#phone_individual', [
      { rule: 'required', errorMessage: 'Telefon zorunludur' },
      {
        rule: 'customRegexp',
        value: /^[0-9\s]{10,15}$/,
        errorMessage: 'Geçerli bir telefon giriniz',
      },
    ])
    .addField('#phone_corporate', [
      { rule: 'required', errorMessage: 'Telefon zorunludur' },
      {
        rule: 'customRegexp',
        value: /^[0-9\s]{10,15}$/,
        errorMessage: 'Geçerli bir telefon giriniz',
      },
    ]);

  // ✅ Bireysel alanlar
  validator
    .addField('[name="namesurname"]', [
      { rule: 'required', errorMessage: 'Ad Soyad zorunludur' },
    ])
    .addField('[name="idendity"]', [
      { rule: 'required', errorMessage: 'T.C. Kimlik No zorunludur' },
      {
        validator: (val) => /^[1-9][0-9]{10}$/.test(val),
        errorMessage: '11 haneli geçerli T.C. No girin',
      },
    ])
    .addField('[name="birthdate"]', [
      { rule: 'required', errorMessage: 'Doğum tarihi zorunludur' },
      {
        validator: (val) => /^\d{2}\/\d{2}\/\d{4}$/.test(val),
        errorMessage: 'GG/AA/YYYY formatında girin',
      },
    ])
    .addField('#address_individual', [
      { rule: 'required', errorMessage: 'Adres alanı zorunludur' },
      {
        rule: 'minLength',
        value: 10,
        errorMessage: 'Adres çok kısa (en az 10 karakter)'
      }
    ]);
    

  // ✅ Kurumsal alanlar
  validator
    .addField('[name="corporatetitle"]', [
      { rule: 'required', errorMessage: 'Firma unvanı zorunludur' },
    ])
    .addField('[name="taxnumber"]', [
      { rule: 'required', errorMessage: 'Vergi numarası zorunludur' },
      {
        validator: (val) => /^[0-9]{10}$/.test(val),
        errorMessage: '10 haneli geçerli vergi no girin',
      },
    ])
    .addField('[name="person"]', [
      { rule: 'required', errorMessage: 'Yetkili kişi adı zorunludur' },
    ])
    .addField('#taxoffice', [
    { rule: 'required', errorMessage: 'Vergi dairesi zorunludur' },
    {
      rule: 'minLength',
      value: 2,
      errorMessage: 'En az 2 karakter girin'
    }
  ])
  .addField('#address_corporate', [
    { rule: 'required', errorMessage: 'Adres alanı zorunludur' },
    {
      rule: 'minLength',
      value: 10,
      errorMessage: 'Adres çok kısa (en az 10 karakter)'
    }
  ]);

  // ✅ Sadece görünür alanlarda validasyon çalıştır
  validator.onValidate(() => {
    const type = getUserType();
    form.querySelectorAll('#individual input, #corporate input').forEach((el) => {
      const visible = el.closest(`#${type}`);
      if (visible) {
        el.removeAttribute('data-validate-ignore');
      } else {
        el.setAttribute('data-validate-ignore', 'true');
      }
    });
  });

  // ✅ IBAN & ünvan otomatik büyük harf
  form.querySelectorAll('#iban_individual, #iban_corporate, #corporatetitle').forEach((input) => {
    input.addEventListener('input', () => {
      input.value = input.value.toUpperCase();
    });
  });

  // ✅ Geçerli form submiti
  validator.onSuccess((e) => {
    console.log('Form geçerli, gönderiliyor...');
    e.target.submit();
  });
});
