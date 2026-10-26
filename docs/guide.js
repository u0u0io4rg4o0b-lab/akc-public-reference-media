'use strict';
(() => {
  const status = document.getElementById('guide-system');
  const dataNode = document.getElementById('guide-data');
  if (!status || !dataNode) return;
  let data;
  try {
    data = JSON.parse(dataNode.textContent);
    if (data.schema_version !== 1 || data.active !== true || data.samples.length !== 3 || data.questions.length !== 5) throw new Error('unsupported');
  } catch (_) {
    status.textContent = '互動暫時無法使用。下方三份說明與原件連結仍可直接閱讀；沒有進行真假判定。';
    return;
  }
  const cards = Array.from(document.querySelectorAll('[data-sample]'));
  const panels = Array.from(document.querySelectorAll('.sample-panel'));
  const all = document.getElementById('show-all');
  let currentMessage = '';
  function announce(message) {
    currentMessage = message;
    const failed = Array.from(document.querySelectorAll('.sample-card img')).some(img => img.complete && img.naturalWidth === 0);
    status.textContent = message + (failed ? ' 有圖片暫時無法顯示；文字和原件連結仍可用，這不表示圖片是假。' : '');
  }
  function choose(key) {
    if (!data.samples.some(s => s.key === key)) return;
    cards.forEach(card => {
      const selected = card.dataset.sample === key;
      card.classList.toggle('is-active', selected);
      if (selected) card.setAttribute('aria-current', 'true'); else card.removeAttribute('aria-current');
      card.querySelector('.sample-picked').hidden = !selected;
    });
    panels.forEach(panel => { panel.hidden = panel.id !== 'record-' + key; });
    announce('正在看「' + data.samples.find(s => s.key === key).label + '」。下方列出查到的與不能推論的事；不是對事件的真假裁決。');
  }
  cards.forEach(card => card.addEventListener('click', event => { event.preventDefault(); choose(card.dataset.sample); }));
  all.hidden = false;
  all.addEventListener('click', () => {
    panels.forEach(panel => { panel.hidden = false; });
    cards.forEach(card => { card.classList.remove('is-active'); card.removeAttribute('aria-current'); card.querySelector('.sample-picked').hidden = true; });
    announce('現在一次顯示三份說明。你可以直接閱讀或離開，不必完成任何關卡。');
  });
  document.querySelectorAll('.sample-card img').forEach(img => img.addEventListener('error', () => {
    announce(currentMessage);
  }));
  choose('original');
})();
