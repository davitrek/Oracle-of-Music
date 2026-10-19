// node tooltip: follows the cursor on hover, sits below the node on focus
const tooltip = document.createElement('div');
tooltip.className = 'path-tooltip';
tooltip.setAttribute('aria-hidden', 'true');
document.body.appendChild(tooltip);

function addTooltipLine(className, text, extraStyle) {
  const line = document.createElement('div');
  line.className = className;
  line.textContent = text;
  if (extraStyle) line.style.fontStyle = extraStyle;
  tooltip.appendChild(line);
}

function showTooltip(node) {
  tooltip.replaceChildren();
  addTooltipLine('tooltip-title', node.dataset.name);
  if (node.classList.contains('path-node-track')) {
    addTooltipLine('tooltip-subtext', node.dataset.artistCredit);
  }
  if (!node.querySelector('.node-image').dataset.spotify) {
    addTooltipLine('tooltip-subtext', '(Not on Spotify)', 'italic');
  }
  tooltip.style.opacity = '1';
}

document.querySelectorAll('.path-node').forEach(node => {
  node.addEventListener('mouseenter', () => showTooltip(node));
  node.addEventListener('mousemove', e => {
    tooltip.style.left = `${e.pageX + 12}px`;
    tooltip.style.top = `${e.pageY - 28}px`;
  });
  node.addEventListener('mouseleave', () => {
    tooltip.style.opacity = '0';
  });

  node.addEventListener('focusin', () => {
    // mouse clicks also focus; the cursor-following tooltip covers those
    if (!node.querySelector(':focus-visible')) return;
    showTooltip(node);
    const rect = node.getBoundingClientRect();
    tooltip.style.left = `${rect.left + window.scrollX}px`;
    tooltip.style.top = `${rect.bottom + window.scrollY + 8}px`;
  });
  node.addEventListener('focusout', () => {
    tooltip.style.opacity = '0';
  });
});

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

async function loadSpotifyInfo(kind) {
  const nodes = [...document.querySelectorAll(`.path-node-${kind}`)];
  await Promise.allSettled(nodes.map(async (node) => {
    const image = node.querySelector('.node-image');
    const anchor = node.querySelector('a');

    try {
      const res = await fetch(`/api/${kind}_spotify_info?mbid=${encodeURIComponent(image.dataset.mbid)}`);
      if (!res.ok) return;

      const data = await res.json();

      if (data.image_url) {
        image.src = data.image_url;
        image.dataset.spotify = 'true';
      }
      const url = data[`${kind}_url`];
      if (url) {
        anchor.href = url;
      }
    } catch (err) {
      // silently ignore failed fetch/parse
    } finally {
      // lets the vertical layout show "(Not on Spotify)" once the lookup is done
      if (!image.dataset.spotify) node.dataset.notOnSpotify = '';
    }
  }));
}

async function loadImages() {
  const spotifyFetchToast = document.getElementById('spotifyFetchToast')
  const toast = bootstrap.Toast.getOrCreateInstance(spotifyFetchToast)

  toast.show()
  await Promise.all([loadSpotifyInfo('track'), loadSpotifyInfo('artist')]);
  toast.hide()
}

loadImages();
  
if (error_message) {
  const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
  document.querySelector('#errorModal .modal-body').textContent = error_message;
  errorModal.show();
}
