document.addEventListener('DOMContentLoaded', () => {
  if (!document.querySelector('link[href="/assets/css/phase1.css"]')) {
    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = '/assets/css/phase1.css';
    document.head.append(stylesheet);
  }
  const data = window.UNAGITANI_DATA;
  const currentPath = location.pathname;
  const navItems = [
    ['/company/', 'Company'], ['/business/', 'Business'], ['/message/', 'Message'], ['/compliance/', 'Compliance'],
    ['/history/', 'History'], ['/brands/', 'Brands'], ['/news/', 'News'], ['/contact/', 'Contact']
  ];
  const header = document.querySelector('.site-header');
  if (header) {
    header.innerHTML = `<div class="wrap header-inner"><a class="logo" href="/"><i></i>UNAGITANI</a><button class="menu" type="button" aria-expanded="false" aria-controls="nav">メニュー</button><nav id="nav" aria-label="メインナビゲーション"><ul class="nav-list">${navItems.map(([href, label]) => `<li><a ${currentPath === href ? 'aria-current="page" ' : ''}class="${href === '/contact/' ? 'nav-cta' : ''}" href="${href}">${label}</a></li>`).join('')}</ul></nav></div>`;
  }
  const footer = document.querySelector('.site-footer');
  if (footer) {
    footer.innerHTML = '<div class="wrap"><div class="footer-top"><div><a class="logo" href="/"><i></i>UNAGITANI</a><p>株式会社UNAGITANI</p></div><nav class="footer-nav" aria-label="フッターナビ"><a href="/company/">Company</a><a href="/business/">Business</a><a href="/message/">Message</a><a href="/compliance/">Compliance</a><a href="/privacy/">Privacy</a><a href="/contact/">Contact</a></nav></div><p class="copyright">© UNAGITANI Co., Ltd.</p></div>';
  }
  const button = document.querySelector('.menu');
  const nav = document.querySelector('.nav-list');
  if (button && nav) {
    button.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
      button.textContent = open ? '閉じる' : 'メニュー';
    });
  }

  document.querySelectorAll('[data-company-field]').forEach((element) => {
    const value = data?.company?.[element.dataset.companyField];
    if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) {
      element.closest('[data-company-row]')?.remove();
      return;
    }
    element.textContent = Array.isArray(value) ? value.join('、') : value;
  });

  const profile = document.querySelector('[data-company-profile]');
  if (profile && data) {
    const fields = [
      ['商号', 'name'], ['英文商号', 'nameEn'], ['代表者', 'representative'], ['所在地', 'address'],
      ['創業', 'founded'], ['法人設立', 'incorporated'], ['資本金', 'capital'], ['法人番号', 'corporateNumber'],
      ['事業内容', 'business'], ['決算期', 'fiscalYearEnd'], ['従業員数', 'employees'], ['主要取引銀行', 'banks'],
      ['古物商許可', 'license'], ['適格請求書発行事業者登録番号', 'invoiceRegistrationNumber'],
      ['主要販売チャネル', 'channels'], ['主な取扱メーカー', 'manufacturers'], ['公式サイト', 'website']
    ];
    fields.forEach(([label, key]) => {
      const value = data.company[key];
      if (value === null || value === undefined || (Array.isArray(value) && value.length === 0)) return;
      const dt = document.createElement('dt');
      const dd = document.createElement('dd');
      dt.textContent = label;
      dd.textContent = Array.isArray(value) ? value.join('、') : value;
      profile.append(dt, dd);
    });
  }

  document.querySelectorAll('[data-financial-highlights]').forEach((container) => {
    data?.financialHighlights?.forEach((item) => {
      const article = document.createElement('article');
      article.className = `financial-card financial-card--${item.type}`;
      article.innerHTML = `<p>${item.fiscalYear}</p><strong>${item.revenue}</strong><span>${item.label}</span>`;
      container.append(article);
    });
  });

  const history = document.querySelector('[data-history]');
  data?.history?.forEach((item) => {
    if (!history) return;
    const article = document.createElement('article');
    article.className = 'history-item';
    article.innerHTML = `<time>${item.year}</time><ul>${item.events.map((event) => `<li>${event}</li>`).join('')}</ul>`;
    history.append(article);
  });

});
