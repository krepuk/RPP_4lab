# GitHub Pages / CI/CD deployment

Что сделано этим генератором:
- созданы: `ru/index.html`, `en/index.html`, `index.html`
- создан GitHub Actions workflow: `.github/workflows/deploy_on_release.yml`

Как это работает:
1. Когда вы в GitHub создаёте и публикуете *релиз* (Release → publish),
   workflow `Deploy site on release` запускается.
2. Workflow копирует файлы сайта в ветку `gh-pages` в подпапку `v<tag>`,
   где `<tag>` — это `tag_name` релиза (например `v1.0.0`).
3. Все прошлые версии остаются в ветке `gh-pages` в своих папках `v.../`.
