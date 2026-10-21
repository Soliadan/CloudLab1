"use strict";

const $ = (id) => document.getElementById(id);
const API = "/orders";
let orders = [];
let editingId = null;
let queryText = "";

function showPage(name) {
  for (const page of ["main_page", "create_page", "edit_page"]) {
    $(page).hidden = page !== name;
  }
  window.scrollTo({ top: 0, behavior: "smooth" });
}

window.toggleMainPage = function () {
  showPage("main_page");
  void loadOrders();
};

window.toggleCreatePage = function () {
  $("add_form").reset();
  $("order_date_input").value = new Date().toLocaleDateString("en-CA");
  showPage("create_page");
};

function alertUser(message, isError = false) {
  const box = $("feedback");
  box.textContent = message;
  box.hidden = false;
  box.classList.toggle("feedback--error", isError);
}

async function apiRequest(path, options = {}) {
  let response;
  try {
    response = await fetch(path, { cache: "no-store", ...options });
  } catch (_) {
    throw new Error("Cannot connect to the server. Check your connection.");
  }
  let data = null;
  if (response.status !== 204) {
    data = await response.json().catch(() => null);
  }
  if (!response.ok) {
    throw new Error(data?.error || `Request failed (HTTP ${response.status}).`);
  }
  return data;
}

const currency = new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
});

function renderOrders() {
  const needle = queryText.toLocaleLowerCase().trim();
  let visible = orders.filter((order) =>
    `${order.parfume_name} ${order.brand} ${order.Volume}`.toLocaleLowerCase().includes(needle)
  );
  if ($("sort_objects").checked) {
    visible = [...visible].sort((a, b) => a.price - b.price);
  }

  const list = $("orders_list");
  list.replaceChildren();
  $("catalog_count").textContent = `${visible.length} ${visible.length === 1 ? "perfume" : "perfumes"}${needle ? " found" : " in your collection"}`;
  $("empty_state").hidden = visible.length > 0;
  $("empty_state").textContent = needle ? "No matching perfumes found." : "No perfumes yet. Add your first fragrance to get started.";

  visible.forEach((order) => {
    const card = document.createElement("li");
    card.className = "perfume-card";
    const visual = document.createElement("div");
    visual.className = "perfume-card__visual";
    const mark = document.createElement("span");
    mark.textContent = "✦";
    visual.append(mark);

    const body = document.createElement("div");
    body.className = "perfume-card__body";
    const brand = document.createElement("div");
    brand.className = "perfume-card__brand";
    brand.textContent = order.brand;
    const name = document.createElement("h3");
    name.className = "perfume-card__name";
    name.textContent = order.parfume_name;
    const meta = document.createElement("div");
    meta.className = "perfume-card__meta";
    meta.textContent = `${order.Volume} · ${order.order_date}`;

    const bottom = document.createElement("div");
    bottom.className = "perfume-card__bottom";
    const price = document.createElement("span");
    price.className = "perfume-card__price";
    price.textContent = currency.format(order.price);
    const actions = document.createElement("div");
    actions.className = "perfume-card__actions";
    for (const [label, type] of [["Edit", "edit"], ["Delete", "delete"]]) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "card-btn" + (type === "delete" ? " card-btn--delete" : "");
      button.textContent = label;
      button.setAttribute("aria-label", `${label} ${order.parfume_name}`);
      button.addEventListener("click", () => type === "edit" ? startEdit(order) : deleteOrder(order, button));
      actions.append(button);
    }
    bottom.append(price, actions);
    body.append(brand, name, meta, bottom);
    card.append(visual, body);
    list.append(card);
  });
}

async function loadOrders() {
  try {
    orders = await apiRequest(API);
    if (!Array.isArray(orders)) throw new Error("The server returned an unexpected response.");
    $("feedback").hidden = true;
    renderOrders();
  } catch (error) {
    orders = [];
    renderOrders();
    alertUser(`Unable to load perfumes: ${error.message}`, true);
  }
}

function payload(prefix = "") {
  return {
    parfume_name: $(`${prefix}parfume_name_input`).value.trim(),
    Volume: $(`${prefix}Volume_input`).value.trim(),
    brand: $(`${prefix}brand_input`).value.trim(),
    order_date: $(`${prefix}order_date_input`).value,
    price: Number($(`${prefix}price_input`).value),
  };
}

function checkPayload(value) {
  if (!value.parfume_name || !value.Volume || !value.brand || !value.order_date || !Number.isSafeInteger(value.price) || value.price < 0 || value.price > 2147483647) {
    throw new Error("Complete all fields and enter a valid whole-number price.");
  }
}

$("add_form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("submit_btn");
  try {
    const data = payload();
    checkPayload(data);
    button.disabled = true;
    await apiRequest(API, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    showPage("main_page");
    await loadOrders();
    if ($("feedback").hidden) alertUser("Perfume added successfully.");
  } catch (error) {
    window.alert(error.message);
  } finally {
    button.disabled = false;
  }
});

function startEdit(order) {
  editingId = order.id;
  $("edit_parfume_name_input").value = order.parfume_name;
  $("edit_Volume_input").value = order.Volume;
  $("edit_brand_input").value = order.brand;
  $("edit_order_date_input").value = order.order_date;
  $("edit_price_input").value = order.price;
  showPage("edit_page");
}

$("edit_form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (editingId === null) return;
  const button = $("edit_btn");
  try {
    const data = payload("edit_");
    checkPayload(data);
    button.disabled = true;
    await apiRequest(`${API}/${encodeURIComponent(editingId)}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    editingId = null;
    showPage("main_page");
    await loadOrders();
    if ($("feedback").hidden) alertUser("Changes saved successfully.");
  } catch (error) {
    window.alert(error.message);
  } finally {
    button.disabled = false;
  }
});

async function deleteOrder(order, button) {
  if (!window.confirm(`Delete “${order.parfume_name}”? This cannot be undone.`)) return;
  button.disabled = true;
  try {
    await apiRequest(`${API}/${encodeURIComponent(order.id)}`, { method: "DELETE" });
    await loadOrders();
    if ($("feedback").hidden) alertUser("Perfume deleted successfully.");
  } catch (error) {
    window.alert(error.message);
    button.disabled = false;
  }
}

$("sort_objects").addEventListener("change", renderOrders);
$("search_btn").addEventListener("click", () => { queryText = $("input_search").value; showPage("main_page"); renderOrders(); });
$("input_search").addEventListener("keydown", (event) => {
  if (event.key === "Enter") { event.preventDefault(); $("search_btn").click(); }
});
$("cancel_search_btn").addEventListener("click", () => {
  $("input_search").value = "";
  queryText = "";
  showPage("main_page");
  renderOrders();
});

void loadOrders();
