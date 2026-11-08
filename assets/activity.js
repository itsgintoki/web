const REQUIRED_METRICS = ["Commits", "Pull requests", "Code review", "Issues"];
const SVG_NS = "http://www.w3.org/2000/svg";

function renderMix(metrics) {
  REQUIRED_METRICS.forEach((metric) => {
    const value = Math.round(Number(metrics[metric]));
    const label = document.querySelector(`.mix-value[data-metric="${metric}"]`);
    const bar = document.querySelector(`.mix-bar b[data-bar="${metric}"]`);
    if (label) label.textContent = value + "%";
    if (bar) bar.style.width = Math.max(0, Math.min(100, value)) + "%";
  });

  const breakdown = document.getElementById("activity-breakdown");
  if (breakdown) {
    breakdown.setAttribute(
      "aria-label",
      `Activity mix over the last year: ${metrics.Commits}% commits, ${metrics["Pull requests"]}% pull requests, ${metrics["Code review"]}% code review, and ${metrics.Issues}% issues.`,
    );
  }
}

function renderRadar(metrics) {
  const radar = document.getElementById("radar");
  const radarArea = document.getElementById("radar-area");
  const radarPoints = document.querySelectorAll(".radar-points circle");
  if (!radar || !radarArea || radarPoints.length === 0) return;

  const centerX = 150;
  const centerY = 115;
  const radiusX = 90;
  const radiusY = 70;
  const directions = {
    Commits: [-1, 0],
    Issues: [1, 0],
    "Code review": [0, -1],
    "Pull requests": [0, 1],
  };
  const coordinates = {};

  REQUIRED_METRICS.forEach((metric) => {
    const [dx, dy] = directions[metric];
    const value = Math.min(100, Math.max(0, Number(metrics[metric])));
    coordinates[metric] = [
      centerX + dx * (value / 100) * radiusX,
      centerY + dy * (value / 100) * radiusY,
    ];
  });

  const order = ["Code review", "Issues", "Pull requests", "Commits"];
  radarArea.setAttribute("points", order.map((metric) => coordinates[metric].join(",")).join(" "));

  radarPoints.forEach((circle) => {
    const point = coordinates[circle.dataset.metric];
    if (!point) return;
    circle.setAttribute("cx", point[0]);
    circle.setAttribute("cy", point[1]);
  });

  radar.querySelectorAll(".radar-label[data-metric]").forEach((label) => {
    const percent = label.querySelector("span");
    if (percent) percent.textContent = Math.round(Number(metrics[label.dataset.metric])) + "%";
  });

  radar.setAttribute(
    "aria-label",
    `Activity breakdown over the last year: ${metrics.Commits}% commits, ${metrics["Pull requests"]}% pull requests, ${metrics["Code review"]}% code review, and ${metrics.Issues}% issues.`,
  );
}

function renderContributions(days, total) {
  const chart = document.getElementById("contrib-chart");
  const totalElement = document.getElementById("activity-total");
  if (!chart || !totalElement) return;

  const firstDay = new Date(days[0].date + "T00:00:00Z").getUTCDay();
  const weeks = Math.ceil((days.length + firstDay) / 7);

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("viewBox", `0 0 ${weeks} 7`);
  svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
  svg.setAttribute("aria-hidden", "true");

  days.forEach((day, index) => {
    const position = index + firstDay;
    const level = Math.min(4, Math.max(0, Number(day.level) || 0));

    const rect = document.createElementNS(SVG_NS, "rect");
    rect.setAttribute("x", String(Math.floor(position / 7) + 0.08));
    rect.setAttribute("y", String((position % 7) + 0.08));
    rect.setAttribute("width", "0.84");
    rect.setAttribute("height", "0.84");
    rect.setAttribute("rx", "0.16");
    rect.setAttribute("class", "l" + level);

    const title = document.createElementNS(SVG_NS, "title");
    title.textContent = `${day.date}: ${day.count} contribution${day.count === 1 ? "" : "s"}`;
    rect.appendChild(title);
    svg.appendChild(rect);
  });

  chart.replaceChildren(svg);
  chart.setAttribute(
    "aria-label",
    `GitHub contribution graph for the last 12 months: ${total} contributions.`,
  );
  totalElement.textContent = String(total);
}

function renderRepositories(data) {
  const repos = Array.isArray(data.contributedTo)
    ? data.contributedTo.filter((repo) => /^[\w.-]+\/[\w.-]+$/.test(repo))
    : [];
  const other = Number.isInteger(data.otherRepositories) ? data.otherRepositories : null;
  const summary = document.getElementById("activity-contrib-text");
  if (!summary || repos.length === 0 || other === null) return;

  const fragment = document.createDocumentFragment();
  fragment.append("Contributed to ");

  repos.forEach((repo, index) => {
    if (index > 0) fragment.append(", ");
    const link = document.createElement("a");
    link.href = "https://github.com/" + repo;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = repo;
    fragment.append(link);
  });

  if (other > 0) {
    fragment.append(" and ");
    const otherLink = document.createElement("a");
    otherLink.href = "https://github.com/itsgintoki?tab=repositories";
    otherLink.target = "_blank";
    otherLink.rel = "noopener";
    otherLink.textContent = `${other} other repositor${other === 1 ? "y" : "ies"}`;
    fragment.append(otherLink);
  }

  summary.replaceChildren(fragment);
}

function renderOrganizations(organizations) {
  const orgs = Array.isArray(organizations)
    ? organizations.filter(
        (org) => org && /^[\w.-]+$/.test(org.login) && typeof org.avatar === "string",
      )
    : [];
  const orgChips = document.getElementById("org-chips");
  if (!orgChips || orgs.length === 0) return;

  const fragment = document.createDocumentFragment();
  orgs.slice(0, 3).forEach((org) => {
    const link = document.createElement("a");
    link.className = "org";
    link.href = "https://github.com/" + org.login;
    link.target = "_blank";
    link.rel = "noopener";

    const avatar = document.createElement("img");
    avatar.src = org.avatar;
    avatar.alt = "";
    avatar.width = 18;
    avatar.height = 18;
    avatar.loading = "lazy";
    avatar.decoding = "async";

    link.append(avatar, document.createTextNode("@" + org.login));
    fragment.append(link);
  });

  const more = document.createElement("a");
  more.className = "org org-more";
  more.href = "https://github.com/itsgintoki?tab=overview";
  more.target = "_blank";
  more.rel = "noopener";
  more.textContent = "More";
  fragment.append(more);
  orgChips.replaceChildren(fragment);
}

async function main() {
  let data;
  try {
    const response = await fetch("activity.json", { cache: "no-store" });
    if (!response.ok) return;
    data = await response.json();
  } catch {
    return;
  }

  const metrics = data?.percentages;
  if (metrics && REQUIRED_METRICS.every((key) => Number.isFinite(metrics[key]))) {
    renderMix(metrics);
    renderRadar(metrics);
  }

  if (
    Array.isArray(data?.contributions) &&
    data.contributions.length > 0 &&
    Number.isFinite(data.totalContributions) &&
    data.totalContributions >= 0
  ) {
    renderContributions(data.contributions, data.totalContributions);
  }

  renderRepositories(data ?? {});
  renderOrganizations(data?.organizations);
}

void main();
