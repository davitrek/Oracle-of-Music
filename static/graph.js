// node hover tooltip
const tooltip = document.createElement('div');
tooltip.className = 'svg-tooltip';
document.body.appendChild(tooltip);

document.querySelectorAll('.path-node-artist, .path-node-track').forEach(node => {
  node.addEventListener('mouseenter', () => {
    if (node.classList.contains('path-node-track')) {
      tooltip.innerHTML = `<span class="tooltip-title">${node.dataset.name}</span><br><span class="tooltip-subtext">${node.dataset.artists}</span>`;
    } else {
      tooltip.innerHTML = `<span class="tooltip-title">${node.dataset.name}</span>`;
    }
    tooltip.style.opacity = '1';
  });
  node.addEventListener('mousemove', e => {
    tooltip.style.left = `${e.pageX + 12}px`;
    tooltip.style.top = `${e.pageY - 28}px`;
  });
  node.addEventListener('mouseleave', () => {
    tooltip.style.opacity = '0';
  });
});


// graph animation offset per node
document.querySelectorAll('[data-path-index]').forEach(el => {
  const i = parseInt(el.dataset.pathIndex, 10);
  el.style.animationDelay = `${i * 0.15}s`;
});


// disable animations for firefox, which seems to perform poorly with them
const isFirefox = navigator.userAgent.toLowerCase().includes('firefox');

if (isFirefox) {
  document.querySelectorAll('.path-connector, .path-node-artist, .path-node-track').forEach(el => {
    el.classList.add('no-animation');
  });
}

// typeahead
function debounce(fn, delay) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

function setupArtistTypeahead(inputId, datalistId) {
  const input = document.getElementById(inputId);
  const datalist = document.getElementById(datalistId);

  const runSearch = debounce(async (query) => {
    try {
      const res = await fetch(`/api/artist_search?q=${encodeURIComponent(query)}`);
      if (!res.ok) return;
      const results = await res.json();

      datalist.innerHTML = '';

      results.forEach((item) => {
        const label = item.name;

        const option = document.createElement('option');
        option.value = label;
        datalist.appendChild(option);
      });
    } catch (err) {
      console.error('Artist search failed:', err);
    }
  }, 300);

  input.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (query.length > 1) {
      runSearch(query);
    } else {
      datalist.innerHTML = '';
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  setupArtistTypeahead('start', 'start-artists');
  setupArtistTypeahead('end', 'end-artists');
});
