const statusDot = document.querySelector("#statusDot");
const healthStatus = document.querySelector("#healthStatus");
const apiInfo = document.querySelector("#apiInfo");
const taskForm = document.querySelector("#taskForm");
const taskTitle = document.querySelector("#taskTitle");
const taskList = document.querySelector("#taskList");
const cacheButton = document.querySelector("#cacheButton");
const cacheInfo = document.querySelector("#cacheInfo");
const refreshHealth = document.querySelector("#refreshHealth");

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

function setHealthUi(status, message) {
  statusDot.className = `dot ${status}`;
  healthStatus.textContent = message;
}

async function loadHealth() {
  try {
    const health = await requestJson("/health");
    const checks = Object.entries(health.checks)
      .map(([name, value]) => `${name}: ${value}`)
      .join(", ");
    setHealthUi("dot-ok", `${health.status.toUpperCase()} (${checks})`);
  } catch (error) {
    setHealthUi("dot-error", error.message);
  }
}

async function loadInfo() {
  try {
    const info = await requestJson("/api/info");
    apiInfo.textContent = `${info.service} is running in ${info.environment} mode. ${info.message}`;
  } catch (error) {
    apiInfo.textContent = error.message;
  }
}

async function loadTasks() {
  try {
    const tasks = await requestJson("/api/tasks");
    taskList.innerHTML = "";

    if (tasks.length === 0) {
      const emptyItem = document.createElement("li");
      emptyItem.textContent = "No tasks yet. Add one above.";
      taskList.appendChild(emptyItem);
      return;
    }

    tasks.forEach((task) => {
      const item = document.createElement("li");
      item.textContent = `${task.title} - ${new Date(task.created_at).toLocaleString()}`;
      taskList.appendChild(item);
    });
  } catch (error) {
    taskList.innerHTML = `<li>${error.message}</li>`;
  }
}

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    await requestJson("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ title: taskTitle.value }),
    });
    taskTitle.value = "";
    await loadTasks();
    await loadHealth();
  } catch (error) {
    alert(error.message);
  }
});

cacheButton.addEventListener("click", async () => {
  try {
    const data = await requestJson("/api/cache");
    cacheInfo.textContent = `${data.message} Current hits: ${data.hits}`;
    await loadHealth();
  } catch (error) {
    cacheInfo.textContent = error.message;
  }
});

refreshHealth.addEventListener("click", loadHealth);

loadHealth();
loadInfo();
loadTasks();
