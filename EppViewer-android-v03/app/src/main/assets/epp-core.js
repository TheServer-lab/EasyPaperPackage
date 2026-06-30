/* EPP parser + renderer — v0.3 */

const COLOR_MAP = {
  black:'#211c14', red:'#a23b2e', blue:'#2e5c8a', green:'#3c6b3f',
  gray:'#5b564a', grey:'#5b564a', white:'#faf6ec', amber:'#c98a3e',
  orange:'#c98a3e', purple:'#5b3a6b'
};
// Callout background/border/text colours keyed by color= value
const CALLOUT_COLORS = {
  yellow: { bg:'#fdf3dc', border:'#c98a3e', text:'#6b3e10', label:'Note'      },
  red:    { bg:'#fce8e6', border:'#a23b2e', text:'#6b1e16', label:'Danger'    },
  green:  { bg:'#dff0df', border:'#3c6b3f', text:'#1e3d20', label:'Success'   },
  blue:   { bg:'#ddeef7', border:'#2e5c8a', text:'#1a3d5c', label:'Info'      },
  gray:   { bg:'#f0eeea', border:'#5b564a', text:'#2e2a24', label:'Note'      },
  purple: { bg:'#ede8f7', border:'#5b3a6b', text:'#2e1a3d', label:'Note'      },
};
// highlight= colour map (paper-friendly tints)
const HIGHLIGHT_COLORS = {
  yellow: '#fff176',
  green:  '#c8f5c8',
  blue:   '#c2e3fc',
  pink:   '#fcd5e8',
  red:    '#fdd5d3',
  orange: '#ffe0b2',
};
const ALIGN_VALUES = ['left','center','right'];
const TEXT_TYPES = ['heading','text','bullet','code'];

function parseEPP(source){
  let i = 0;
  const n = source.length;
  let title = null;
  let version = null;
  let header = null;  // @header text
  let footer = null;  // @footer text (may contain [page])
  const meta = {};
  const pages = [];
  let current = { number:null, blocks:[], pageAttrs:{} };
  const isWS = c => c === ' ' || c === '\t' || c === '\n' || c === '\r';

  function skipWsAndComments(){
    while (i < n){
      const c = source[i];
      if (isWS(c)){ i++; continue; }
      if (c === ';'){ while (i < n && source[i] !== '\n') i++; continue; }
      break;
    }
  }
  function readWord(){
    const start = i;
    while (i < n && !isWS(source[i]) && source[i] !== '{' && source[i] !== ';') i++;
    return source.slice(start, i);
  }
  function readQuotedString(){
    i++; // consume opening "
    let out = '';
    while (i < n){
      const c = source[i];
      if (c === '\\'){
        const next = source[i+1];
        if (next === '"' || next === '[' || next === ']' || next === '\\'){ out += next; i += 2; continue; }
        out += c; i++; continue;
      }
      if (c === '"'){ i++; break; }
      if (c === '\n'){ out += ' '; i++; continue; }
      out += c; i++;
    }
    return out;
  }
  function readAttrBlock(){
    i++; // consume {
    const start = i;
    while (i < n && source[i] !== '}') i++;
    const inner = source.slice(start, i);
    if (i < n) i++;
    const attrs = {};
    inner.split(',').forEach(part => {
      const p = part.trim();
      if (!p) return;
      if (p.includes('=')){
        let [k, v] = p.split('=');
        k = k.trim().toLowerCase(); v = v.trim().toLowerCase();
        if (k === 'aling') k = 'align';
        attrs[k] = v;
      } else { attrs[p.toLowerCase()] = true; }
    });
    return attrs;
  }
  // Read a key=value token that is NOT inside braces (used by @meta)
  function readInlineKV(){
    skipWsAndComments();
    const start = i;
    while (i < n && !isWS(source[i]) && source[i] !== ';') i++;
    const token = source.slice(start, i);
    if (token.includes('=')){
      let [k, ...rest] = token.split('=');
      let v = rest.join('=');
      // strip surrounding quotes from value
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1);
      return [k.trim().toLowerCase(), v.trim()];
    }
    return [token.trim().toLowerCase(), ''];
  }

  skipWsAndComments();
  if (source[i] === '%'){
    const start = i; i++;
    while (i < n && source[i] !== '%') i++;
    const raw = source.slice(start+1, i);
    if (i < n) i++;
    const m = raw.match(/epp=(.+)/);
    version = m ? m[1] : raw;
  }

  while (true){
    skipWsAndComments();
    if (i >= n) break;
    if (source[i] !== '@'){ i++; continue; }
    i++;
    const cmd = readWord().toLowerCase();

    if (cmd === 'newpage'){ pages.push(current); current = { number:null, blocks:[], pageAttrs:{} }; continue; }
    if (cmd === 'page'){
      skipWsAndComments();
      current.number = readWord();
      skipWsAndComments();
      // v0.3: @page N {lined} {color=blue} {rotate=90}
      if (source[i] === '{'){
        current.pageAttrs = readAttrBlock();
      }
      continue;
    }
    if (cmd === 'title'){ skipWsAndComments(); if (source[i] === '"') title = readQuotedString(); continue; }
    if (cmd === 'label'){ skipWsAndComments(); const name = readWord(); current.blocks.push({ type:'label', name }); continue; }
    if (cmd === 'space'){ current.blocks.push({ type:'space' }); continue; }
    if (cmd === 'line'){ current.blocks.push({ type:'line' }); continue; }

    // v0.2: @meta key="value"
    if (cmd === 'meta'){
      const [k, v] = readInlineKV();
      meta[k] = v;
      if (k === 'title' && !title) title = v;
      continue;
    }
    // v0.2: @header "text"
    if (cmd === 'header'){
      skipWsAndComments();
      if (source[i] === '"') header = readQuotedString();
      continue;
    }
    // v0.2: @footer "text"
    if (cmd === 'footer'){
      skipWsAndComments();
      if (source[i] === '"') footer = readQuotedString();
      continue;
    }
    // v0.2: @quote "text"
    if (cmd === 'quote'){
      skipWsAndComments();
      let text = '';
      if (source[i] === '"') text = readQuotedString();
      current.blocks.push({ type:'quote', text });
      continue;
    }
    // v0.3: @callout "text" {color=yellow}
    if (cmd === 'callout'){
      skipWsAndComments();
      let text = '';
      if (source[i] === '"') text = readQuotedString();
      skipWsAndComments();
      let attrs = {};
      if (source[i] === '{') attrs = readAttrBlock();
      current.blocks.push({ type:'callout', text, attrs });
      continue;
    }
    // v0.2: @table "col1|col2|col3"
    if (cmd === 'table'){
      skipWsAndComments();
      let headers = [];
      if (source[i] === '"') headers = readQuotedString().split('|');
      current.blocks.push({ type:'table', headers, rows:[] });
      continue;
    }
    // v0.2: @row "val1|val2|val3"
    if (cmd === 'row'){
      skipWsAndComments();
      let cells = [];
      if (source[i] === '"') cells = readQuotedString().split('|');
      // Attach to last table block on this page
      const lastTable = [...current.blocks].reverse().find(b => b.type === 'table');
      if (lastTable) lastTable.rows.push(cells);
      continue;
    }

    if (TEXT_TYPES.includes(cmd)){
      skipWsAndComments();
      let text = '';
      if (source[i] === '"') text = readQuotedString();
      skipWsAndComments();
      let attrs = {};
      if (source[i] === '{') attrs = readAttrBlock();
      current.blocks.push({ type:cmd, text, attrs });
      continue;
    }
    // unknown command — skip rest of line tokens
    skipWsAndComments();
    if (source[i] === '"') readQuotedString();
    skipWsAndComments();
    if (source[i] === '{') readAttrBlock();
  }
  pages.push(current);
  return { version, title, meta, header, footer, pages };
}

/* ---- rendering helpers ---- */

function escapeHtml(str){
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function renderInlineText(text, highlightColor){
  let out = escapeHtml(text).split('[newline]').join('<br>');
  if (highlightColor && HIGHLIGHT_COLORS[highlightColor]){
    const bg = HIGHLIGHT_COLORS[highlightColor];
    out = '<mark style="background:' + bg + ';padding:1px 3px;border-radius:2px">' + out + '</mark>';
  }
  return out;
}

const BULLET_GLYPHS = {
  disc:   '•',
  number: null,   // handled separately
  check:  '✓',
  arrow:  '→',
  star:   '★',
};


const PAGE_COLORS = {
  cream:  { bg:'#faf6ec', ink:'#211c14' },
  blue:   { bg:'#edf3fc', ink:'#1c3358' },
  pink:   { bg:'#fce8f0', ink:'#5a1c33' },
  green:  { bg:'#ecf6ec', ink:'#1c3d1c' },
  yellow: { bg:'#fefadf', ink:'#4a3a00' },
  gray:   { bg:'#f0eeea', ink:'#2e2a24' },
};
function renderPageInner(page, pageNumber, totalPages, header, footer){
  let html = '';
  let openList = false;
  let listCounter = 0;
  const total = page.blocks.length;

  // header band
  if (header){
    html += `<div class="epp-header-band">${renderInlineText(header)}</div>`;
  }

  const blocksHtml = (() => {
    let out = '';
    page.blocks.forEach((block, idx) => {
      // close open list if this block isn't a bullet
      if (block.type !== 'bullet' && openList){ out += '</ol></ul>'; openList = false; listCounter = 0; }

      const color = (block.attrs && COLOR_MAP[block.attrs.color]) || '';
      const align = (block.attrs && ALIGN_VALUES.includes(block.attrs.align)) ? block.attrs.align : 'left';
      const bold  = block.attrs && block.attrs.bold;
      const italic= block.attrs && block.attrs.italic;
      const under = block.attrs && block.attrs.underline;

      function styleStr(){ return `${color ? `color:${color};` : ''}text-align:${align};${bold?'font-weight:700;':''}${italic?'font-style:italic;':''}${under?'text-decoration:underline;':''}`; }

      if (block.type === 'heading'){
        out += `<h2 class="epp-heading" style="${styleStr()}">${renderInlineText(block.text, block.attrs && block.attrs.highlight)}</h2>`;
      } else if (block.type === 'text'){
        out += `<p class="epp-text" style="${styleStr()}">${renderInlineText(block.text, block.attrs && block.attrs.highlight)}</p>`;
      } else if (block.type === 'callout'){
        const ckey = (block.attrs && block.attrs.color) || 'yellow';
        const cs = CALLOUT_COLORS[ckey] || CALLOUT_COLORS.yellow;
        out += `<div class="epp-callout" style="background:${cs.bg};border-left:3px solid ${cs.border};color:${cs.text}"><span class="epp-callout-label" style="color:${cs.border}">${cs.label}</span>${escapeHtml(block.text)}</div>`;
      } else if (block.type === 'bullet'){
        const btype = (block.attrs && block.attrs.type) || 'disc';
        if (!openList){
          out += '<ul class="epp-bullets">';
          openList = true; listCounter = 0;
        }
        listCounter++;
        if (btype === 'number'){
          out += `<li class="epp-bullet-number" style="${color?`color:${color};`:''}"><span class="epp-bullet-glyph">${listCounter}.</span>${renderInlineText(block.text)}</li>`;
        } else {
          const glyph = BULLET_GLYPHS[btype] || '•';
          out += `<li class="epp-bullet-custom" style="${color?`color:${color};`:''}"><span class="epp-bullet-glyph">${glyph}</span>${renderInlineText(block.text)}</li>`;
        }
      } else if (block.type === 'code'){
        out += `<pre class="epp-code">${escapeHtml(block.text).split('[newline]').join('\n')}</pre>`;
      } else if (block.type === 'space'){
        out += '<div class="epp-space"></div>';
      } else if (block.type === 'line'){
        out += '<hr class="epp-line">';
      } else if (block.type === 'quote'){
        out += `<blockquote class="epp-quote">${renderInlineText(block.text)}</blockquote>`;
      } else if (block.type === 'table'){
        out += '<table class="epp-table"><thead><tr>';
        block.headers.forEach(h => { out += `<th>${escapeHtml(h.trim())}</th>`; });
        out += '</tr></thead><tbody>';
        block.rows.forEach(row => {
          out += '<tr>';
          row.forEach(cell => { out += `<td>${escapeHtml(cell.trim())}</td>`; });
          out += '</tr>';
        });
        out += '</tbody></table>';
      } else if (block.type === 'label'){
        const tp = total <= 1 ? 50 : (idx / (total - 1)) * 86 + 6;
        out += `<div class="label-tab" style="top:${tp}%" title="label: ${escapeHtml(block.name)}">${escapeHtml(block.name)}</div>`;
      }
    });
    if (openList) out += '</ul>';
    return out || '<p class="empty-hint">This page is empty.</p>';
  })();

  html += `<div class="epp-page-body">${blocksHtml}</div>`;

  // footer band
  if (footer){
    const footerText = footer.replace('[page]', pageNumber);
    html += `<div class="epp-footer-band">${renderInlineText(footerText)}</div>`;
  } else {
    // default page number
    html += `<div class="epp-page-footer">${escapeHtml(String(pageNumber))}</div>`;
  }

  return html;
}

function renderDocumentHTML(doc){
  const total = doc.pages.length;
  return doc.pages.map((page, pIdx) => {
    const number = page.number || String(pIdx + 1);
    const pa = page.pageAttrs || {};

    // Color
    const colorKey = pa.color && PAGE_COLORS[pa.color] ? pa.color : 'cream';
    const { bg, ink } = PAGE_COLORS[colorKey];

    // Lined
    const linedStyle = pa.lined
      ? `background-image:repeating-linear-gradient(transparent,transparent 23px,rgba(185,175,152,.4) 24px);background-size:100% 24px;background-position:0 63px;`
      : '';

    // Rotation
    const validRots = { '90':true, '180':true, '270':true };
    const rot = pa.rotate && validRots[String(pa.rotate)] ? pa.rotate : null;
    const rotClass = rot ? ` epp-page-rotate-${rot}` : '';
    const linedClass = pa.lined ? ' epp-page-lined' : '';

    const pageStyle = `background:${bg};color:${ink};${linedStyle}`;

    return `<div class="epp-page${rotClass}${linedClass}" data-index="${pIdx}" style="${pageStyle}">` +
      `<div class="epp-page-inner">${renderPageInner(page, number, total, doc.header, doc.footer)}</div>` +
    `</div>`;
  }).join('');
}

function mountViewer(container, initialDoc, opts){
  opts = opts || {};
  let doc = initialDoc;
  let currentIndex = 0;

  // Build source-URL chip if a remote URL was provided
  const srcUrlChip = opts.sourceUrl
    ? '<a class="epp-src-url no-print" href="' + opts.sourceUrl.replace(/"/g, '%22') + '" target="_blank" title="Source: ' + opts.sourceUrl.replace(/"/g, '&quot;') + '">' +
        '\u{1F517} ' + (() => { try { const u = new URL(opts.sourceUrl); return u.hostname + (u.pathname.length > 30 ? u.pathname.slice(-28) : u.pathname); } catch(e){ return opts.sourceUrl.slice(0,50); } })() +
      '</a>'
    : '';

  container.innerHTML =
    '<div class="epp-toolbar no-print">' +
      '<div class="epp-brand"></div>' +
      srcUrlChip +
      '<div class="epp-nav">' +
        '<button class="epp-btn" data-action="prev">\u2039</button>' +
        '<span class="epp-indicator"></span>' +
        '<button class="epp-btn" data-action="next">\u203A</button>' +
      '</div>' +
      '<div class="epp-actions">' +
        (opts.showOpenButton ? '<button class="epp-btn" data-action="open">Open file\u2026</button><input type="file" class="epp-file-input" accept=".epp,.txt" hidden />' : '') +
        '<button class="epp-btn primary" data-action="print">Print</button>' +
      '</div>' +
    '</div>' +
    '<div class="epp-pages"></div>';

  const pagesEl   = container.querySelector('.epp-pages');
  const brandEl   = container.querySelector('.epp-brand');
  const indicatorEl = container.querySelector('.epp-indicator');

  function renderPages(){ pagesEl.innerHTML = renderDocumentHTML(doc); }
  function updateNav(){
    const total = doc.pages.length;
    currentIndex = Math.max(0, Math.min(currentIndex, total - 1));
    const page = doc.pages[currentIndex];
    const label = page && page.number ? page.number : String(currentIndex + 1);
    indicatorEl.textContent = `${label} / ${total}`;
    [...pagesEl.children].forEach((el, i) => { el.style.display = (i === currentIndex) ? 'block' : 'none'; });
  }
  function setDoc(newDoc){
    doc = newDoc;
    currentIndex = 0;
    brandEl.textContent = doc.title || 'EPP document';
    renderPages();
    updateNav();
  }

  setDoc(doc);

  container.querySelector('[data-action="prev"]').addEventListener('click', () => { currentIndex--; updateNav(); });
  container.querySelector('[data-action="next"]').addEventListener('click', () => { currentIndex++; updateNav(); });
  container.querySelector('[data-action="print"]').addEventListener('click', () => window.print());

  if (opts.showOpenButton){
    const openBtn   = container.querySelector('[data-action="open"]');
    const fileInput = container.querySelector('.epp-file-input');
    openBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => setDoc(parseEPP(reader.result));
      reader.readAsText(file);
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown'){ currentIndex++; updateNav(); }
    else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp'){ currentIndex--; updateNav(); }
  });

  return { setDoc };
}
