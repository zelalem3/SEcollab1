document.getElementById('toggle-dark-mode').addEventListener('click', toggleDarkMode);
 const darkModeEnabled = localStorage.getItem('darkMode') === 'enabled';

    // Add the dark-mode class to the body if dark mode is enabled
    if (document.body.classList.contains('dark-mode')) {
      document.body.classList.add('dark-mode');
    }
function toggleDarkMode() {
  document.body.classList.toggle('dark-mode');

  // Save the user's preference in local storage
  if (document.body.classList.contains('dark-mode')) {
    localStorage.setItem('darkMode', 'enabled');
  } else {
    localStorage.setItem('darkMode', 'disabled');
  }
}
if (localStorage.getItem('darkMode') === 'enabled') {
  document.body.classList.add('dark-mode');
}