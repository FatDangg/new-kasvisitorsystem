// admin.js
let visitors = [];

async function loadVisitors() {
  try {
    const response = await fetch("/api/visitors");
    if (!response.ok) {
      alert("Error loading visitors. Are you logged in?");
      return;
    }
    visitors = await response.json();
    displayVisitors(visitors);
  } catch (error) {
    console.error("Failed to load visitors:", error);
    alert("Error loading visitors");
  }
}

function displayVisitors(list) {
  const tbody = document.getElementById("visitorTbody");
  tbody.innerHTML = "";
  list.forEach((visitor) => {
    const row = document.createElement("tr");

    // Name
    const nameCell = document.createElement("td");
    nameCell.textContent = visitor.full_name;
    nameCell.style.cursor = "pointer";
    nameCell.addEventListener("click", () => {
      openVisitorModal(visitor);
      console.log("i got you")
    });
    row.appendChild(nameCell);

    // Purpose
    const purposeCell = document.createElement("td");
    purposeCell.textContent = visitor.purpose;
    row.appendChild(purposeCell);

    // Date/Time
    const dateCell = document.createElement("td");
    const dt = new Date(visitor.created_at);
    dateCell.textContent = dt.toLocaleString();
    row.appendChild(dateCell);

    // Meeting
    const meetingCell = document.createElement("td");
    meetingCell.textContent = visitor.finding;
    row.appendChild(meetingCell);

    // Photo
    const photoCell = document.createElement("td");
    if (visitor.photo_download) {
      const img = document.createElement("img");
      img.src = visitor.photo_download;
      img.alt = "Visitor Photo";
      photoCell.appendChild(img);
    } else {
      photoCell.textContent = "No photo";
    }
    row.appendChild(photoCell);

    // Badge Download
    const badgeCell = document.createElement("td");
    if (visitor.pdf_download) {
      const badgeLink = document.createElement("a");
      badgeLink.href = visitor.pdf_download;
      badgeLink.textContent = "Download Badge";
      badgeLink.className = "badge-btn";
      badgeLink.target = "_blank";
      badgeCell.appendChild(badgeLink);
    } else {
      badgeCell.textContent = "No badge";
    }
    row.appendChild(badgeCell);

    tbody.appendChild(row);
  });
}
document.addEventListener("DOMContentLoaded", () => {

    // Function to display visitors in the table
    function displayVisitors(list) {
      const tbody = document.getElementById("visitorTbody");
      tbody.innerHTML = "";
      list.forEach((visitor) => {
        const row = document.createElement("tr");
  
        // Name cell with modal trigger
        const nameCell = document.createElement("td");
        nameCell.textContent = visitor.full_name;
        nameCell.style.cursor = "pointer";
        nameCell.addEventListener("click", () => {
          openVisitorModal(visitor);
        });
        row.appendChild(nameCell);
  
        // Purpose
        const purposeCell = document.createElement("td");
        purposeCell.textContent = visitor.purpose;
        row.appendChild(purposeCell);
  
        // Date/Time
        const dateCell = document.createElement("td");
        const dt = new Date(visitor.created_at);
        dateCell.textContent = dt.toLocaleString();
        row.appendChild(dateCell);
  
        // Meeting
        const meetingCell = document.createElement("td");
        meetingCell.textContent = visitor.finding;
        row.appendChild(meetingCell);
  
        // Photo
        const photoCell = document.createElement("td");
        if (visitor.photo_download) {
          const img = document.createElement("img");
          img.src = visitor.photo_download;
          img.alt = "Visitor Photo";
          photoCell.appendChild(img);
        } else {
          photoCell.textContent = "No photo";
        }
        row.appendChild(photoCell);
  
        // Badge Download / View Link
        const badgeCell = document.createElement("td");
        if (visitor.pdf_download) {
          const badgeLink = document.createElement("a");
          badgeLink.href = visitor.pdf_download;
          badgeLink.textContent = "View Badge";
          badgeLink.className = "badge-btn";
          badgeLink.target = "_blank"; // Open in a new tab
          badgeCell.appendChild(badgeLink);
        } else {
          badgeCell.textContent = "No badge";
        }
        row.appendChild(badgeCell);
  
        tbody.appendChild(row);
      });
    }
  
    // Function to open the visitor details modal
    function openVisitorModal(visitor) {
      const modal = document.getElementById("visitorModal");
      if (!modal) {
        console.error("Modal element not found. Ensure your admin.html includes a div with id 'visitorModal'.");
        return;
      }
    
      document.getElementById("modalName").textContent = visitor.full_name;
      document.getElementById("modalEmail").textContent = visitor.email || "N/A";
      document.getElementById("modalPhone").textContent = visitor.phone || "N/A";
      document.getElementById("modalPurpose").textContent = visitor.purpose;
      document.getElementById("modalFinding").textContent = visitor.finding;
      const dt = new Date(visitor.created_at);
      document.getElementById("modalCreatedAt").textContent = dt.toLocaleString();
    
      modal.style.display = "block";
    }
  
    // Attach event listener for the modal close button
    document.getElementById("modalClose").addEventListener("click", () => {
      document.getElementById("visitorModal").style.display = "none";
    });
  
    // Attach event listener to close the modal when clicking on the dimmed background
    window.addEventListener("click", (e) => {
      const modal = document.getElementById("visitorModal");
      if (e.target === modal) {
        modal.style.display = "none";
      }
    });
  
    // Optionally, expose displayVisitors globally if you call it from elsewhere
    window.displayVisitors = displayVisitors;
  });
  
function filterVisitors() {
  const searchTerm = document.getElementById("searchInput").value.toLowerCase();
  const dateFilter = document.getElementById("dateFilter").value;
  const filtered = visitors.filter((v) => {
    const matchSearch =
      v.full_name.toLowerCase().includes(searchTerm) ||
      v.purpose.toLowerCase().includes(searchTerm);
    let matchDate = true;
    if (dateFilter === "today") {
      const dt = new Date(v.created_at);
      const now = new Date();
      matchDate = dt.toDateString() === now.toDateString();
    } else if (dateFilter === "thisweek") {
      const dt = new Date(v.created_at);
      const now = new Date();
      const weekAgo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 7);
      matchDate = dt >= weekAgo && dt <= now;
    }
    return matchSearch && matchDate;
  });
  displayVisitors(filtered);
}

function setupFilters() {
  document.getElementById("searchInput").addEventListener("input", filterVisitors);
  document.getElementById("dateFilter").addEventListener("change", filterVisitors);
}

function setupLogout() {
  const logoutBtn = document.getElementById("logoutBtn");
  if (!logoutBtn) return;
  logoutBtn.addEventListener("click", () => {
    window.location.href = "/logout";
  });
}

window.addEventListener("DOMContentLoaded", () => {
  loadVisitors();
  setupFilters();
  setupLogout();
});
