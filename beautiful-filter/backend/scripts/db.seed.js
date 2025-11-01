// NOTE :  Some requests may error out - Just rerun the script to fill in more data

const ENDPOINT = "http://localhost:3000/api/data";

const names = [
  "John Doe",
  "Alice Smith",
  "Bob Lee",
  "Nina Brown",
  "Eve Adams",
  "Tom Chen",
  "Lara Patel",
];
const domains = [
  "gmail.com",
  "yahoo.com",
  "outlook.com",
  "protonmail.com",
  "iiits.in",
];

function randomDate(
  start = new Date(1980, 0, 1),
  end = new Date(2010, 11, 31)
) {
  return new Date(
    start.getTime() + Math.random() * (end.getTime() - start.getTime())
  );
}

function randomEmail(name) {
  const domain = domains[Math.floor(Math.random() * domains.length)];
  return name.toLowerCase().replace(/\s+/g, ".") + "@" + domain;
}

function randomData() {
  const data = {};
  if (Math.random() > 0.1) {
    data.name = names[Math.floor(Math.random() * names.length)];
    data.email = randomEmail(data.name);
  }
  if (Math.random() > 0.3)
    data.dateOfBirth = randomDate().toISOString().split("T")[0];
  if (Math.random() > 0.2) data.score = Math.floor(Math.random() * 100);
  if (Math.random() > 0.5) data.isPriority = Math.random() > 0.5;
  return data;
}

async function seed(n = 50) {
  for (let i = 0; i < n; i++) {
    const body = randomData();
    try {
      const res = await fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      console.log(`[${i + 1}] Sent`, body, "→", res.status);
    } catch (err) {
      console.error(`[${i + 1}] Failed`, err.message);
    }
  }
}

seed(50);
