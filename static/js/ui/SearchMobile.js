// Mainly used for accessibility on the search page
// On desktop resolution, some HTML attributes need to be removed
function SearchMobile(root) {
  if (!root) return

  const desktopRes = window.matchMedia('(width > 992px)')

  function callback(mediaMatching) {
    const tabsList = document.querySelector('.fr-tabs__list')
    const tabs = document.querySelectorAll('.fr-tabs__list .fr-tabs__tab')
    const tabsPanel = document.querySelectorAll('.fr-tabs__panel')

    if (!tabsList || !tabs || !tabsPanel) return

    if (mediaMatching) {
      tabsList.removeAttribute('role')
      tabs.forEach((tab) => {
        tab.removeAttribute('role')
      })

      tabsPanel.forEach((tabPanel) => {
        tabPanel.removeAttribute('aria-labelledby')
        tabPanel.removeAttribute('role')
      })
    } else {
      tabsList.setAttribute('role', 'tablist')
      tabs.forEach((tab) => {
        tab.setAttribute('role', 'tab')
      })

      tabsPanel.forEach((tabPanel, index) => {
        tabPanel.setAttribute('aria-labelledby', `tabpanel-${index + 1}-panel`)
        tabPanel.setAttribute('role', 'tabpanel')
      })
    }
  }

  desktopRes.addEventListener('change', (event) => callback(event.matches))

  callback(desktopRes.matches)
}

export default SearchMobile
