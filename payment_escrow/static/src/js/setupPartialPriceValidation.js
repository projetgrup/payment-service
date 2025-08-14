import JustValidate from 'just-validate';

export function setupPartialPriceValidation() {
  const form = document.querySelector('#partialPriceForm');
  const input = form.querySelector('#paymentAmount');
  const button = form.querySelector('#payAllBtn');
  const balanceText = form.querySelector('#remainingBalance');

  // Formatlı değeri raw sayıya çeviren yardımcı fonksiyon
  const getRawValue = (val) => val.replace(/\D/g, '');

  // Formatlayan fonksiyon (boşsa boş dön, 0 ise "0 TL")
  const formatCurrency = (val) => {
    if (!val) return '';
    const num = parseInt(val, 10);
    if (isNaN(num)) return '';
    return new Intl.NumberFormat('tr-TR').format(num) + ' TL';
  };

  // Tümünü Öde Butonu
  button.addEventListener('click', () => {
    const raw = getRawValue(balanceText.textContent);
    input.value = formatCurrency(raw);
    input.dispatchEvent(new Event('input'));
     validator.revalidateField('#paymentAmount'); // 🔥 HOT VALIDATE
  });

  // Girişte sadece sayı yazılmasına ve bozmadan formatlamaya dikkat
  input.addEventListener('input', (e) => {
    const caretPos = input.selectionStart;
    const raw = getRawValue(input.value);
    const formatted = formatCurrency(raw);

    input.value = formatted;

    // caret pozisyonu en sona gitmesin diye güncelle
    requestAnimationFrame(() => {
      input.setSelectionRange(input.value.length - 3, input.value.length - 3); // ' TL' öncesi
    });
     // 🔥 HOT VALIDATE
    validator.revalidateField('#paymentAmount');
  });

  // Validasyon
  const validator = new JustValidate(form, {
    validateOnInput: true,
    errorLabelCssClass: 'form__error-label',
  });

  validator.addField('#paymentAmount', [
    { rule: 'required', errorMessage: 'Miktar zorunludur' },
    {
      validator: (val) => {
        const raw = parseInt(getRawValue(val), 10);
        return !isNaN(raw) && raw > 0;
      },
      errorMessage: '0’dan büyük bir miktar girin',
    }
  ]);

  validator.onSuccess((e) => {
    e.preventDefault();
    alert('Form gönderildi: ' + input.value);
  });
}
