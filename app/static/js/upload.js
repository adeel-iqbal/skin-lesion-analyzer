const zone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('imagePreview');
const previewContainer = document.getElementById('previewContainer');
const uploadPrompt = document.getElementById('uploadPrompt');
const fileName = document.getElementById('fileName');
const form = document.getElementById('analyzeForm');
const loadingState = document.getElementById('loadingState');

zone.addEventListener('click', (e) => {
  if (!e.target.closest('#previewContainer')) fileInput.click();
});

zone.addEventListener('dragover', (e) => {
  e.preventDefault();
  zone.classList.add('drag-over');
});

zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));

zone.addEventListener('drop', (e) => {
  e.preventDefault();
  zone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) showPreview(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) showPreview(fileInput.files[0]);
});

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    preview.src = e.target.result;
    fileName.textContent = file.name;
    uploadPrompt.classList.add('hidden');
    previewContainer.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  fileInput.value = '';
  preview.src = '';
  uploadPrompt.classList.remove('hidden');
  previewContainer.classList.add('hidden');
}

let locationSet = false;

function setBtn(state) {
  const btn = document.getElementById('locationBtn');
  const status = document.getElementById('locationStatus');

  if (state === 'default') {
    btn.innerHTML = `
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 2C8.686 2 6 4.686 6 8c0 4.418 6 12 6 12s6-7.582 6-12c0-3.314-2.686-6-6-6z"/>
        <circle cx="12" cy="8" r="2" stroke="currentColor" stroke-width="2"/>
      </svg>
      <span>Allow location</span>`;
    btn.className = 'w-full flex items-center justify-center gap-2 bg-stone-800 hover:bg-stone-700 border border-stone-700 text-stone-300 text-sm px-3 py-2.5 rounded-xl transition-colors';
    btn.disabled = false;
    status.className = 'text-xs text-stone-500 mt-1.5 hidden';
    status.textContent = '';

  } else if (state === 'loading') {
    btn.innerHTML = `<span>Getting location...</span>`;
    btn.disabled = true;

  } else if (state === 'set') {
    btn.innerHTML = `
      <svg class="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/>
      </svg>
      <span>Location set</span>`;
    btn.className = 'w-full flex items-center justify-center gap-2 bg-green-800 border border-green-700 text-green-100 text-sm px-3 py-2.5 rounded-xl transition-colors';
    btn.disabled = false;
    status.textContent = 'Click to remove location';
    status.className = 'text-xs text-stone-500 mt-1.5';

  } else if (state === 'denied') {
    btn.disabled = false;
    setBtn('default');
    status.textContent = 'Location access denied. Dermatologist search skipped.';
    status.className = 'text-xs text-stone-500 mt-1.5';
  }
}

function getLocation() {
  if (locationSet) {
    locationSet = false;
    document.getElementById('latInput').value = '';
    document.getElementById('lngInput').value = '';
    setBtn('default');
    return;
  }

  setBtn('loading');

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      locationSet = true;
      document.getElementById('latInput').value = pos.coords.latitude;
      document.getElementById('lngInput').value = pos.coords.longitude;
      setBtn('set');
    },
    () => setBtn('denied')
  );
}

form.addEventListener('submit', () => {
  loadingState.classList.remove('hidden');
  document.getElementById('submitBtn').disabled = true;
});
