document.addEventListener('DOMContentLoaded', () => {
  const avatarBtn = document.getElementById('avatarBtn');
  const dropdownMenu = document.getElementById('dropdownMenu');
  const profileWidget = document.getElementById('profileWidget');

  if (avatarBtn && dropdownMenu) {
    avatarBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const expanded = avatarBtn.getAttribute('aria-expanded') === 'true' ? false : true;
      avatarBtn.setAttribute('aria-expanded', expanded);
      dropdownMenu.classList.toggle('show');
    });

    document.addEventListener('click', (event) => {
      if (!profileWidget.contains(event.target)) {
        dropdownMenu.classList.remove('show');
        avatarBtn.setAttribute('aria-expanded', 'false');
      }
    });

    dropdownMenu.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    const menuItems = dropdownMenu.querySelectorAll('.dropdown-item');
    menuItems.forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const text = item.innerText.trim();
        if (text.includes('Выйти')) {
          alert('Выход из аккаунта (демо-режим)');
        } else if (text.includes('Мой профиль')) {
          alert('Переход в профиль (демо)');
        } else if (text.includes('Настройки')) {
          alert('Открыть настройки (демо)');
        }
        dropdownMenu.classList.remove('show');
        avatarBtn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  const startBtn = document.getElementById('startFreeBtn');
  const learnBtn = document.getElementById('learnMoreBtn');

  if (startBtn) {
    startBtn.addEventListener('click', () => {
      window.location.href='/problem'
    });
  }
  if (learnBtn) {
    learnBtn.addEventListener('click', () => {
      window.location.href='/chat'
    });
  }

  const triggerCards = document.querySelectorAll('.option-card');
  const submitTrigger = document.getElementById('submitTrigger');

  if (triggerCards.length > 0 && submitTrigger) {
    function clearSelected() {
      triggerCards.forEach(card => {
        card.classList.remove('selected');
        const radio = card.querySelector('input[type="radio"]');
        if (radio) radio.checked = false;
      });
    }

    triggerCards.forEach(card => {
      card.addEventListener('click', (e) => {
        const radio = card.querySelector('input[type="radio"]');
        if (radio) {
          clearSelected();
          radio.checked = true;
          card.classList.add('selected');
        }
      });
    });

    submitTrigger.addEventListener('click', () => {
      const selected = document.querySelector('input[name="trigger"]:checked');
      if (!selected) {
        alert('Пожалуйста, выберите один из вариантов.');
        return;
      }
      const value = selected.value;
      window.location.href = `/chat?trigger=${value}`;
    });
  }
});