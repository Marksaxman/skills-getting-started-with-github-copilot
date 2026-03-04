document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      // avoid serving a cached response so clients always see updates
      const response = await fetch("/activities", { cache: "no-store" });
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      // reset dropdown options each time to avoid duplicates
      activitySelect.innerHTML = `<option value="">-- Select an activity --</option>`;

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // build participants section if any have signed up
        let participantsSection = "";
        if (details.participants && details.participants.length > 0) {
          participantsSection = `
            <p><strong>Participants:</strong></p>
            <ul>
              ${details.participants.map(
                p => `<li>${p} <button class="remove-btn" data-activity="${name}" data-email="${p}">&times;</button></li>`
              ).join("")}
            </ul>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsSection}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // refresh activities so the new participant appears immediately
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // remove handler for delete buttons using event delegation
  activitiesList.addEventListener("click", async (e) => {
    if (e.target.matches(".remove-btn")) {
      const activity = e.target.dataset.activity;
      const email = e.target.dataset.email;

      try {
        const resp = await fetch(
          `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
          { method: "DELETE", cache: "no-store" }
        );
        const data = await resp.json();
        if (resp.ok) {
          messageDiv.textContent = data.message;
          messageDiv.className = "info";
          messageDiv.classList.remove("hidden");
          setTimeout(() => messageDiv.classList.add("hidden"), 5000);
          fetchActivities();
        } else {
          messageDiv.textContent = data.detail || "Failed to remove";
          messageDiv.className = "error";
          messageDiv.classList.remove("hidden");
        }
      } catch (err) {
        messageDiv.textContent = "Error removing participant.";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
        console.error(err);
      }
    }
  });

  // Initialize app
  fetchActivities();
});
