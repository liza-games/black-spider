// Перевод игры: находит в src/game.html все русские тексты (в разметке и в строках JS)
// и подставляет английские из src/i18n/en.json. Ключ — исходный текст строки ровно как в коде
// (для JS — вместе с кавычками), значение — замена в том же виде.
//
//   node tools/i18n.mjs extract   → список всех русских текстов с номерами строк (для перевода)
//   node tools/i18n.mjs build     → JSON {ru:{head,html,js}, en:{...}, missing:[...]} для build.py
import {readFileSync} from 'node:fs';
import {parse} from './vendor/acorn.mjs';

const root = new URL('..', import.meta.url);
const src = readFileSync(new URL('src/game.html', root), 'utf8');
const CYR = /[А-Яа-яЁё]/;

const marker = '<svg id="web"';
const s0 = src.indexOf('<script>'), s1 = src.indexOf('</script>');
const mi = src.indexOf(marker);
if (mi < 0 || s0 < mi || s1 < s0) throw new Error('unexpected layout of src/game.html');
const head = src.slice(0, mi), html = src.slice(mi, s0), js = src.slice(s0 + 8, s1), tail = src.slice(s1 + 9);
if (tail.trim()) throw new Error('content after </script> is not supported');

const lineOf = (text, pos) => text.slice(0, pos).split('\n').length;

// --- разметка: текст между тегами и значения атрибутов
function htmlUnits(text) {
  const out = [];
  const reText = />([^<>]*[А-Яа-яЁё][^<>]*)</g;
  for (const m of text.matchAll(reText)) { const t = m[1].trim(); const at = m.index + 1 + m[1].indexOf(t); out.push({start: at, end: at + t.length, key: t}); }
  const reAttr = /\s(?:aria-label|title|alt|placeholder)="([^"]*[А-Яа-яЁё][^"]*)"/g;
  for (const m of text.matchAll(reAttr)) { const at = m.index + m[0].indexOf('"') + 1; out.push({start: at, end: at + m[1].length, key: m[1]}); }
  return out.sort((a, b) => a.start - b.start);
}

// --- JS: строки и шаблоны с кириллицей (только самые внешние)
function jsUnits(code) {
  const ast = parse(code, {ecmaVersion: 'latest', sourceType: 'script'});
  const found = [];
  (function walk(n) {
    if (!n || typeof n.type !== 'string') return;
    if ((n.type === 'Literal' && typeof n.value === 'string') || n.type === 'TemplateLiteral') {
      const raw = code.slice(n.start, n.end);
      if (CYR.test(raw)) { found.push({start: n.start, end: n.end, key: raw}); return; }   // внутрь не идём
    }
    for (const k in n) { const v = n[k]; if (Array.isArray(v)) v.forEach(walk); else if (v && typeof v.type === 'string') walk(v); }
  })(ast);
  return found.sort((a, b) => a.start - b.start);
}

function apply(text, units, map, missing, where) {
  let out = '', pos = 0;
  for (const u of units) {
    out += text.slice(pos, u.start);
    if (Object.prototype.hasOwnProperty.call(map, u.key)) out += map[u.key];
    else { out += u.key; missing.push({where, line: lineOf(text, u.start), key: u.key}); }
    pos = u.end;
  }
  return out + text.slice(pos);
}

const hU = htmlUnits(html), jU = jsUnits(js);
const mode = process.argv[2] || 'build';
if (mode === 'extract') {
  const seen = new Set(), list = [];
  for (const [w, t, us] of [['html', html, hU], ['js', js, jU]])
    for (const u of us) { const id = w + '\u0000' + u.key; if (seen.has(id)) continue; seen.add(id); list.push({where: w, line: lineOf(t, u.start), key: u.key}); }
  process.stdout.write(JSON.stringify(list, null, 1));
} else {
  const en = JSON.parse(readFileSync(new URL('src/i18n/en.json', root), 'utf8'));
  const missing = [];
  const out = {
    ru: {html, js},
    en: {html: apply(html, hU, en.html || {}, missing, 'html'), js: apply(js, jU, en.js || {}, missing, 'js')},
    head, missing
  };
  // английская сборка должна разбираться без ошибок
  parse(out.en.js, {ecmaVersion: 'latest', sourceType: 'script'});
  process.stdout.write(JSON.stringify(out));
}
