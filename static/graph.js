// document.addEventListener('DOMContentLoaded', function () {
//     document.addEventListener('Form', () => {
//         fetch('/getpath', {
//             method: 'POST',
//             body: JSON.stringify({ start: "Kanye West", end: "Drake"}),
//         })
//         .then(response => response.json())
//         .then(json => {

//         })
//     })
// });

    // // to aviod having duplicate code in each page's html
    // // copies contents of navbar.html into <div> elements with id #navbar-container
    // fetch('navbar.html')
    // .then(response => response.text())
    // .then(text => {
    //     const container = document.querySelector('#navbar-container');
    //     container.innerHTML = text;
        
    //     setCurrentPageActive();
    // });
    
    // // to aviod having duplicate code in each page's html
    // // copies contents of navbar.html into <div> elements with id #favicon
    // fetch('favicon.html')
    // .then(response => response.text())
    // .then(text => {
    //     const container = document.querySelector('#favicon');
    //     container.innerHTML = text;
    // });
    
    // alert('Welcome to my page!\n\n-John Smith');

// function setCurrentPageActive() {
//     let tmp = window.location.href.split('/')

//     // should convert 'https:://... .com/index.html#etc' into 'index'
//     let currPage = tmp[tmp.length - 1].split('.')[0];

//     let navButtons = document.querySelectorAll('a.nav-link');
//     for (button of navButtons) {
//         if (button.id.toLowerCase() == currPage) {
//             button.classList.add('active')
//         }
//     }
// }
// 

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

// Wait for images to decode before starting animations
const images = Array.from(document.querySelectorAll('svg image'));
Promise.all(images.map(img => img.decode?.() ?? Promise.resolve()))
  .finally(() => startPathAnimation());

document.querySelectorAll('[data-path-index]').forEach(el => {
  const i = parseInt(el.dataset.pathIndex, 10);
  el.style.animationDelay = `${i * 0.15}s`;
});

const isFirefox = navigator.userAgent.toLowerCase().includes('firefox');

if (isFirefox) {
  document.querySelectorAll('.path-connector, .path-node-artist, .path-node-track').forEach(el => {
    el.classList.add('no-animation');
  });
}
