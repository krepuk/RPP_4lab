#!/usr/bin/env python3
# generate_site_and_ci.py
"""
Генерирует:
 - ru/index.html
 - en/index.html
 - index.html (в корне) с навигацией
 - .github/workflows/deploy_on_release.yml (GitHub Actions workflow)
 - README_DEPLOY.md с инструкциями
"""

from pathlib import Path
import textwrap
import os

ROOT = Path.cwd()
GH_WORKFLOWS = ROOT / ".github" / "workflows"
RU_DIR = ROOT / "ru"
EN_DIR = ROOT / "en"

def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Создан: {path.relative_to(ROOT)}")

# Templates
ru_index = textwrap.dedent("""\
    <!doctype html>
    <html lang="ru">
    <head>
      <meta charset="utf-8">
      <title>Мой сайт — Русская версия</title>
    </head>
    <body>
      <h1>Добро пожаловать — Русская версия</h1>
      <p>Это русскоязычная версия сайта.</p>
      <nav>
        <a href="../index.html">Главная</a> |
        <a href="../en/index.html">English</a>
      </nav>
    </body>
    </html>
""")

en_index = textwrap.dedent("""\
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>My site — English version</title>
    </head>
    <body>
      <h1>Welcome — English version</h1>
      <p>This is the English version of the site.</p>
      <nav>
        <a href="../index.html">Home</a> |
        <a href="../ru/index.html">Русский</a>
      </nav>
    </body>
    </html>
""")

root_index = textwrap.dedent("""\
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Site root — navigation</title>
    </head>
    <body>
      <h1>Project site</h1>
      <p>Navigation:</p>
      <ul>
        <li><a href="./ru/index.html">Русская версия</a></li>
        <li><a href="./en/index.html">English version</a></li>
      </ul>

      <h2>Версии (history)</h2>
      <p>При публикации релиза GitHub Actions автоматически положит сборку в папку <code>/v&lt;tag&gt;/</code> ветки <code>gh-pages</code>.
         Список доступных версий будет показываться здесь (в gh-pages branch).</p>

      <p>После первой публикации релиза откроется ссылка вида:
         <code>https://&lt;your-github-login&gt;.github.io/&lt;your-repo&gt;/v&lt;tag&gt;/</code>
      </p>

      <hr>
      <p>Инструкции по деплою и настройке смотрите в <code>README_DEPLOY.md</code>.</p>
    </body>
    </html>
""")

deploy_workflow = textwrap.dedent("""\
    name: Deploy site on release

    on:
      release:
        types: [published]

    permissions:
      contents: write
      pages: write

    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository
            uses: actions/checkout@v4
            with:
              fetch-depth: 0

          - name: Setup git for pushing
            run: |
              git config user.name "github-actions[bot]"
              git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          - name: Fetch gh-pages branch if exists
            run: |
              git fetch origin gh-pages:gh-pages || true

          - name: Switch to gh-pages branch (or create it)
            run: |
              if git rev-parse --verify gh-pages >/dev/null 2>&1; then
                git checkout gh-pages
                # Clean any untracked files that might interfere
                git clean -fd
              else
                git checkout --orphan gh-pages
                git rm -rf .
                git commit --allow-empty -m "Initialize gh-pages"
                git push origin gh-pages
              fi

          - name: Prepare deploy folder
            run: |
              # create temporary folder with site files
              mkdir -p site_to_deploy
              cp -a ../ru site_to_deploy/ || true
              cp -a ../en site_to_deploy/ || true
              cp -a ../index.html site_to_deploy/ || true
              echo "Release: ${{ github.event.release.tag_name }}" > site_to_deploy/RELEASE.txt

          - name: Copy files into versioned folder
            run: |
              TAG="${{ github.event.release.tag_name }}"
              mkdir -p "v${TAG}"
              # Copy content of site_to_deploy into v<TAG> directory (overwrite)
              cp -a site_to_deploy/. "v${TAG}/"
              
              # Generate versions index with links to all releases
              echo "<!doctype html><html><head><meta charset='utf-8'><title>Available Versions</title></head><body><h1>Available Versions</h1><ul>" > versions_index.html
              
              # Get all version directories and list them (simple approach)
              for d in v*/ ; do
                if [ -d "$d" ]; then
                  # strip trailing slash
                  name="${d%/}"
                  version="${name#v}"
                  echo "<li><a href='./$name/'>Version $version</a> ($name)</li>" >> versions_index.html
                fi
              done
              
              echo "</ul>" >> versions_index.html
              
              # Add link to latest version if current tag exists
              if [ -d "v${TAG}" ]; then
                echo "<p><strong><a href='./v${TAG}/'>Latest version (${TAG})</a></strong></p>" >> versions_index.html
              fi
              
              echo "</body></html>" >> versions_index.html
              mv versions_index.html index.html

              # Clean up temporary folder
              rm -rf site_to_deploy

          - name: Commit and push changes to gh-pages
            env:
              GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            run: |
              git add -A
              git commit -m "Deploy site for release ${{ github.event.release.tag_name }}" || echo "No changes to commit"
              # Push to gh-pages branch using token auth
              git push "https://x-access-token:${GH_TOKEN}@github.com/${{ github.repository }}.git" gh-pages

          - name: Create GitHub Pages build (if needed)
            uses: actions/github-script@v7
            with:
              script: |
                // optional: nothing here, pages will serve from gh-pages branch once set in repo settings
                core.info("Deployed files to gh-pages branch.")
""")

readme_deploy = textwrap.dedent("""\
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
    4. На главной странице автоматически генерируется список всех доступных версий.
""")

set_pages_py = textwrap.dedent("""\
    # set_github_pages.py
    # Скрипт использует PyGithub для установки источника GitHub Pages на ветку gh-pages (root).
    # Usage:
    #   pip install PyGithub
    #   python set_github_pages.py <GITHUB_TOKEN> <owner> <repo>
    #
    import sys
    from github import Github

    def main():
        if len(sys.argv) != 4:
            print("Usage: python set_github_pages.py <GITHUB_TOKEN> <owner> <repo>")
            return
        token, owner, repo_name = sys.argv[1], sys.argv[2], sys.argv[3]
        g = Github(token)
        repo = g.get_repo(f"{owner}/{repo_name}")
        # Set pages source to gh-pages branch, root folder
        try:
            repo.create_pages_source(branch='gh-pages', path='/')
            print("Pages source set to gh-pages (root).")
        except Exception as e:
            # fallback for older PyGithub or insufficient permissions: use repo.edit
            try:
                repo.edit_pages(source={'branch': 'gh-pages', 'path': '/'})
                print("Pages source set (fallback).")
            except Exception as e2:
                print("Не удалось установить Pages через API:", e, e2)

    if __name__ == '__main__':
        main()
""")

# write files
write_file(RU_DIR / "index.html", ru_index)
write_file(EN_DIR / "index.html", en_index)
write_file(ROOT / "index.html", root_index)
write_file(GH_WORKFLOWS / "deploy_on_release.yml", deploy_workflow)
write_file(ROOT / "README_DEPLOY.md", readme_deploy)
write_file(ROOT / "set_github_pages.py", set_pages_py)

print("\nГенерация завершена.")
print("Дальше: инициализируйте репозиторий, закоммитьте и запушьте изменения, если ещё не сделали этого.")
print("1) git add . && git commit -m 'Add site + CI' && git push origin main")
print("2) В GitHub: Settings → Pages → выберите ветку gh-pages (или запустите set_github_pages.py с токеном)")
print("3) Создайте релиз — workflow автоматически создаст папку v<tag> в ветке gh-pages.")
