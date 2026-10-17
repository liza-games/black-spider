#!/usr/bin/env python3
"""Собирает игру из src/game.html.

src/game.html — русский исходник без обёртки <html>/<head>/<body>.
Английские тексты лежат в src/i18n/en.json: ключ — русская строка ровно как в коде
(для JS — вместе с кавычками), значение — замена. tools/i18n.mjs (нужен node) подставляет
их и проверяет, что английский JS разбирается без ошибок.

Результат:
  build/game.html — страница для чата Claude (без обёртки), в ней обе версии;
  index.html      — она же с обёрткой, для GitHub Pages.
При запуске страница берёт язык из localStorage 'spider-lang', а если его не выбирали — язык телефона
и вставляет разметку и скрипт нужной версии. Переключатель — в главном меню.
"""
import json, subprocess, sys
from pathlib import Path

root = Path(__file__).parent
data = json.loads(subprocess.run(["node", str(root / "tools" / "i18n.mjs"), "build"],
                                 check=True, capture_output=True, text=True, encoding="utf-8").stdout)
if data["missing"]:
    print(f"нет перевода для {len(data['missing'])} строк (останутся по-русски):", file=sys.stderr)
    for m in data["missing"][:40]:
        print(f"  {m['where']}:{m['line']}  {m['key'][:90]!r}", file=sys.stderr)

def pack(v):
    # JSON внутри <script>: «</» нельзя оставлять как есть
    return json.dumps(v, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")

titles = {"ru": "Чёрный паук", "en": "Black Spider"}
boot = f"""<script>
/* обе версии игры; выбирается одна по сохранённому языку */
(function(){{
  var P={{ru:{pack(data['ru'])},en:{pack(data['en'])}}}, T={pack(titles)};
  // язык: выбранный вручную, иначе язык телефона (русский, украинский, белорусский, казахский → русский, остальные → английский)
  var saved=null; try{{ saved=localStorage.getItem('spider-lang') }}catch(e){{}}
  var dev=((navigator.languages&&navigator.languages[0])||navigator.language||'ru').toLowerCase();
  var L=saved==='en'||saved==='ru'?saved:(/^(ru|uk|be|kk)([-_]|$)/.test(dev)?'ru':'en');
  window.SPIDER_LANG=L; document.documentElement.lang=L; document.title=T[L];
  var me=document.currentScript;
  me.insertAdjacentHTML('beforebegin',P[L].html);
  var s=document.createElement('script'); s.textContent=P[L].js; me.parentNode.insertBefore(s,me);
}})();
</script>"""
head = data["head"].strip()
(root / "build").mkdir(exist_ok=True)
artifact = head + "\n" + boot + "\n"
(root / "build" / "game.html").write_text(artifact, encoding="utf-8")

page = f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<style>
:root{{color-scheme:light;padding:env(safe-area-inset-top,0px) 0 env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px system-ui,sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
{head}
</head>
<body>
{boot}
</body>
</html>
"""
(root / "index.html").write_text(page, encoding="utf-8")
print("index.html:", len(page.encode("utf-8")), "bytes;", "build/game.html:", len(artifact.encode("utf-8")), "bytes;",
      "без перевода:", len(data["missing"]))
