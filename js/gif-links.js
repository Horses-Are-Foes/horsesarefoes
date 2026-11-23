document.addEventListener("click", (event) => {
  const link = event.target.closest("a[data-random-hrefs]");
  if (!link) return;

  const urls = JSON.parse(link.dataset.randomHrefs);
  link.href = urls[Math.floor(Math.random() * urls.length)];
});