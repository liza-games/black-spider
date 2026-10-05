#!/usr/bin/env python3
"""Собирает index.html для GitHub Pages из src/game.html.

src/game.html хранится без обёртки <html>/<head>/<body>: в таком виде страница
публикуется в чате Claude. Для обычного хостинга обёртку добавляет этот скрипт.
"""
from pathlib import Path

root = Path(__file__).parent
src = (root / "src" / "game.html").read_text(encoding="utf-8")
# Всё до этой метки (<title>, шрифты, стили) уходит в <head>, остальное в <body>.
marker = '<svg id="web"'
if src.count(marker) != 1:
    raise SystemExit(f"метка {marker!r} должна встречаться в src/game.html ровно один раз")
head, body = src.split(marker, 1)
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
{head.strip()}
</head>
<body>
{marker}{body.rstrip()}
</body>
</html>
"""
(root / "index.html").write_text(page, encoding="utf-8")
print("index.html:", len(page.encode("utf-8")), "bytes")
