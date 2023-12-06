function ProgressBar(root) {
  var bar = root.querySelector('.bar')
  var percentage = parseInt(root.querySelector('span').textContent)

  bar.animate([{ transform: 'rotate(45deg)' }, { transform: `rotate(${45 + percentage * 1.8}deg)` }], {
    duration: 1200,
    easing: 'ease-out',
    fill: 'forwards',
  })
}

export default ProgressBar
