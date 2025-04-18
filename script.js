// Global variable to track the current step
let currentStep = 1;

// Function to show a given step
function showStep(step) {
  document.querySelectorAll('.step').forEach(section => section.classList.remove('active'));
  document.getElementById(`step-${step}`).classList.add('active');
  currentStep = step;

  // If step 5 is active, start the camera
  if (step === 5) {
    startCamera();
  }
}

// --- Step 1: Sign In ---
document.getElementById('btn-signin').addEventListener('click', () => {
  showStep(2);
});

// --- Step 2: Name Entry ---
document.getElementById('btn-name-next').addEventListener('click', () => {
  const firstName = document.getElementById('first-name').value.trim();
  const lastName = document.getElementById('last-name').value.trim();
  if (!firstName || !lastName) {
    alert('Please enter both your first name and last name.');
  } else {
    showStep(3);
  }
});

// --- Step 3: Contact Info, Purpose & Meeting Person ---
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}
function isValidPhone(phone) {
  const re = /^\d{10}$/;
  return re.test(phone);
}
document.getElementById('btn-contact-next').addEventListener('click', () => {
  const email = document.getElementById('email').value.trim();
  const phone = document.getElementById('phone').value.trim();
  const purpose = document.getElementById('purpose').value;
  const finding = document.getElementById('finding').value.trim();
  if (!email || !phone || !purpose || !finding) {
    alert('Please complete all fields.');
  } else if (!isValidEmail(email)) {
    alert('Please enter a valid email address.');
  } else if (!isValidPhone(phone)) {
    alert('Please enter a valid 10-digit phone number.');
  } else {
    showStep(4);
  }
});

// --- Step 4: Agreement & Checkbox ---
document.getElementById('btn-agreement-next').addEventListener('click', () => {
  const agreeCheckbox = document.getElementById('agree-checkbox');
  if (!agreeCheckbox.checked) {
    alert('You must agree to the Visitor Agreement & Confidentiality Form to continue.');
  } else {
    showStep(5);
  }
});

// --- Step 5: Photo Capture ---
let videoStream = null;
const video = document.getElementById('video');
const photoCanvas = document.getElementById('photo-canvas');
const capturedPhoto = document.getElementById('captured-photo');
const countdownEl = document.getElementById('countdown');
const btnCapture = document.getElementById('btn-capture');
const btnRetake = document.getElementById('btn-retake');
const btnPhotoNext = document.getElementById('btn-photo-next');

async function startCamera() {
  try {
    videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = videoStream;
    // Hide captured photo if restarting camera
    capturedPhoto.style.display = 'none';
    video.style.display = 'block';
  } catch (err) {
    alert('Error accessing camera: ' + err);
  }
}

function stopCamera() {
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
  }
}

btnCapture.addEventListener('click', () => {
  let count = 3;
  countdownEl.style.display = 'block';
  countdownEl.innerText = count;
  const interval = setInterval(() => {
    count--;
    if (count > 0) {
      countdownEl.innerText = count;
    } else {
      clearInterval(interval);
      countdownEl.style.display = 'none';
      capturePhoto();
    }
  }, 1000);
});

function capturePhoto() {
  photoCanvas.width = video.videoWidth;
  photoCanvas.height = video.videoHeight;
  const context = photoCanvas.getContext('2d');
  context.drawImage(video, 0, 0, photoCanvas.width, photoCanvas.height);
  // Convert canvas to data URL and show it in the captured photo element
  const dataURL = photoCanvas.toDataURL();
  capturedPhoto.src = dataURL;
  capturedPhoto.style.display = 'block';
  video.style.display = 'none';
  photoCanvas.style.display = 'none';
  btnRetake.style.display = 'inline-block';
  btnPhotoNext.style.display = 'inline-block';
  stopCamera();
}

btnRetake.addEventListener('click', () => {
  capturedPhoto.style.display = 'none';
  btnRetake.style.display = 'none';
  btnPhotoNext.style.display = 'none';
  startCamera();
});

btnPhotoNext.addEventListener('click', () => {
  showStep(6);
});

// --- Step 6: Welcome & Data Submission ---
document.getElementById('btn-finish').addEventListener('click', () => {
  // Gather data from all steps
  const visitorData = {
    firstName: document.getElementById('first-name').value.trim(),
    lastName: document.getElementById('last-name').value.trim(),
    email: document.getElementById('email').value.trim(),
    phone: document.getElementById('phone').value.trim(),
    purpose: document.getElementById('purpose').value,
    finding: document.getElementById('finding').value.trim(),
    // Use the captured photo data URL as the photo
    photo: capturedPhoto.src,
    agreed: document.getElementById('agree-checkbox').checked
  };

  // Send data to backend API (update URL as necessary)
  fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(visitorData)
  })
  .then(response => response.json())
  .then(result => {
    if (result.success) {
      alert('Welcome to KAS!');
      window.location.reload();
    } else {
      alert('Error: ' + result.error);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Something went wrong!');
  });
});
