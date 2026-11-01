// Glossary page: render formulas with the local KaTeX copy, and filter entries by search.

renderMathInElement(document.body, {
  delimiters: [{ left: "\\[", right: "\\]", display: true }, { left: "\\(", right: "\\)", display: false }],
  throwOnError: false,
});

// Searchable units: glossary entries and the rows of the abbreviations table.
const entries = [...document.querySelectorAll(".entry")];
const rows = [...document.querySelectorAll(".tbl tbody tr")];
const units = [...entries, ...rows];
const q = document.getElementById("q");
const count = document.getElementById("count");
const empty = document.getElementById("empty");
const fa = n => n.toLocaleString("fa-IR");

// Normalize Arabic/Persian letter variants and remove zero-width joiners so "الگوریتمها" matches "الگوریتم‌ها".
const norm = s => s.toLowerCase().replace(/[‌‍]/g, "").replace(/ي/g, "ی").replace(/ك/g, "ک");
const texts = units.map(u => norm(u.textContent));

function filter() {
  const term = norm(q.value.trim());
  let shown = 0;
  units.forEach((u, i) => {
    const hit = !term || texts[i].includes(term);
    u.hidden = !hit;
    if (hit && u.classList.contains("entry")) shown++;
    if (hit && !u.classList.contains("entry") && term) shown++;
  });
  // While searching, hide headings and prose; keep the table only if one of its rows matches.
  document.querySelectorAll(".doc > :not(.entry):not(h1):not(#empty)").forEach(el => {
    el.hidden = !!term && !(el.classList.contains("tbl") && el.querySelector("tbody tr:not([hidden])"));
  });
  count.textContent = term ? fa(shown) + " نتیجه" : fa(entries.length) + " مدخل";
  empty.hidden = !term || shown > 0;
}
q.addEventListener("input", filter);
addEventListener("keydown", e => {
  if (e.key === "/" && document.activeElement !== q) { e.preventDefault(); q.focus(); }
  if (e.key === "Escape") { q.value = ""; filter(); }
});
count.textContent = fa(entries.length) + " مدخل";
