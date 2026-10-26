/* ==========================================================================
   DevChecks - index.js
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initCounters();
  initPasswordStrength();
  initRegisterValidation();
  initChatbot();
});

/* ---------- Remaining-characters counters inside inputs ---------- */
function initCounters() {
  document.querySelectorAll("input[data-counter]").forEach((input) => {
    const counter = input.parentElement.querySelector(".counter");
    if (!counter) return;
    const max = parseInt(input.getAttribute("maxlength"), 10);
    const update = () => { counter.textContent = max - input.value.length; };
    input.addEventListener("input", update);
    update();
  });
}

/* ---------- Password strength meter (0-4) ---------- */
function scorePassword(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
  if (/\d/.test(pw) && /[^A-Za-z0-9]/.test(pw)) score++;
  return Math.min(score, 4);
}

function initPasswordStrength() {
  const pw = document.getElementById("password");
  const meter = document.getElementById("strength");
  if (!pw || !meter) return;
  pw.addEventListener("input", () => {
    meter.dataset.score = scorePassword(pw.value);
  });
}

/* ---------- Client-side register checks (server re-validates) ---------- */
function initRegisterValidation() {
  const form = document.getElementById("registerForm");
  if (!form) return;
  const errorBox = document.getElementById("clientError");

  form.addEventListener("submit", (e) => {
    const errors = [];
    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const pw = form.password.value;
    const confirm = form.confirm_password.value;

    if (!/^[A-Za-z0-9_-]{1,30}$/.test(username)) {
      errors.push("Username must be 1-30 characters: letters, numbers, _ or -.");
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
      errors.push("Enter a valid email address.");
    }
    if (pw.length < 8) errors.push("Password must be at least 8 characters.");
    if (pw !== confirm) errors.push("Passwords do not match.");

    if (errors.length) {
      e.preventDefault();
      errorBox.textContent = errors.join(" ");
      errorBox.hidden = false;
      errorBox.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
}

/* ---------- Chatbot ---------- */
function initChatbot() {
  const root = document.getElementById("chatbot");
  if (!root) return;

  const panel = document.getElementById("chatbotPanel");
  const toggle = document.getElementById("chatbotToggle");
  const closeBtn = document.getElementById("chatbotClose");
  const form = document.getElementById("chatbotForm");
  const input = document.getElementById("chatbotInput");
  const messages = document.getElementById("chatbotMessages");
  const chips = document.getElementById("chatbotChips");
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  function setOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
    if (open) input.focus();
  }

  function addMessage(text, who, extraClass = "") {
    const el = document.createElement("div");
    el.className = `msg msg--${who} ${extraClass}`.trim();
    el.textContent = text; // textContent keeps user input from being parsed as HTML
    messages.appendChild(el);
    messages.scrollTop = messages.scrollHeight;
    return el;
  }

  async function send(text) {
    text = text.trim();
    if (!text) return;
    chips.hidden = true;
    addMessage(text, "user");
    input.value = "";

    const typing = addMessage("Typing...", "bot", "msg--typing");
    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ message: text }),
      });
      if (res.status === 401) { window.location.href = "/login"; return; }
      const data = await res.json();
      typing.remove();
      addMessage(data.reply || data.error || "Something went wrong.", "bot");
    } catch (err) {
      typing.remove();
      addMessage("Can't reach the server. Try again in a moment.", "bot");
    }
  }

  toggle.addEventListener("click", () => setOpen(panel.hidden));
  closeBtn.addEventListener("click", () => { setOpen(false); toggle.focus(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !panel.hidden) setOpen(false);
  });

  form.addEventListener("submit", (e) => { e.preventDefault(); send(input.value); });
  chips.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) send(chip.dataset.prompt);
  });
}

/* ==========================================================================
   Add new JavaScript below this line
   ========================================================================== */
