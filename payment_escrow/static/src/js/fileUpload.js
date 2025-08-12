export function setupFileUpload({
  inputId = "file-input",
  listId = "files-list",
  counterId = "num-of-files"
} = {}) {
  const fileInput = document.getElementById(inputId);
  const fileList = document.getElementById(listId);
  const numOfFiles = document.getElementById(counterId);

  if (!fileInput || !fileList || !numOfFiles) return;

  fileInput.addEventListener("change", () => {
    fileList.innerHTML = "";

    const files = fileInput.files;
    numOfFiles.textContent = `${files.length} dosya seçildi`;

    Array.from(files).forEach((file) => {
      const fileName = file.name;
      let fileSize = (file.size / 1024).toFixed(1);
      let fileSizeStr = `${fileSize} KB`;

      if (fileSize >= 1024) {
        fileSize = (fileSize / 1024).toFixed(1);
        fileSizeStr = `${fileSize} MB`;
      }

      const listItem = document.createElement("li");
      listItem.innerHTML = `<p>${fileName}</p><p>${fileSizeStr}</p>`;
      fileList.appendChild(listItem);
    });
  });
}
