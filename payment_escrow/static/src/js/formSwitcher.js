export function setupFormSwitcher(individualId = "individual", corporateId = "corporate") {
  const individualForm = document.getElementById(individualId);
  const corporateForm = document.getElementById(corporateId);
  const radioInputs = document.querySelectorAll('input[name="userType"]');

  if (!individualForm || !corporateForm || !radioInputs.length) return;

  const toggleForms = (value) => {
    if (value === "individual") {
      individualForm.style.display = "block";
      corporateForm.style.display = "none";
    } else if (value === "corporate") {
      individualForm.style.display = "none";
      corporateForm.style.display = "block";
    }
  };

  // İlk yüklemede doğru formu göster
  const checkedRadio = document.querySelector('input[name="userType"]:checked');
  toggleForms(checkedRadio.value);

  // Değişiklik dinleme
  radioInputs.forEach((input) => {
    input.addEventListener("change", (e) => {
      toggleForms(e.target.value);
    });
  });
}
