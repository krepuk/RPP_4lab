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
      <title>Project Site</title>
    </head>
    <body>
      <h1>Project Site</h1>
      
      <div class="version-list">
        <h2>Все версии:</h2>
        <ul>
          <li class="latest"><a href="./v1.0.0/">Version 1.0.0 (LATEST)</a></li>
          <!-- Новые версии будут добавляться автоматически при каждом релизе -->
        </ul>
      </div>

      <h2>Navigation:</h2>
      <ul>
        <li><a href="./ru/index.html">Русская версия</a></li>
        <li><a href="./en/index.html">English version</a></li>
      </ul>

      <script>
        console.log('Site version: 1.0.0');
      </script>
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

    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout repository
            uses: actions/checkout@v4

          - name: Setup Git config
            run: |
              git config --global user.name "github-actions[bot]"
              git config --global user.email "41898282+github-actions[bot]@users.noreply.github.com"

          - name: Create versioned copy
            run: |
              # Создаем папку для текущей версии
              mkdir -p v${{ github.event.release.tag_name }}
              cp -r ru en v${{ github.event.release.tag_name }}/
              
              # Создаем временный index.html для версионной папки
              cat > v${{ github.event.release.tag_name }}/index.html << 'EOF'
              <!doctype html>
              <html lang="en">
              <head>
                <meta charset="utf-8">
                <title>Project Site - Version ${{ github.event.release.tag_name }}</title>
              </head>
              <body>
                <h1>Project Site - ${{ github.event.release.tag_name }}</h1>
                <p>This is version ${{ github.event.release.tag_name }} of the site.</p>
                
                <h2>Navigation:</h2>
                <ul>
                  <li><a href="./ru/index.html">Russian version</a></li>
                  <li><a href="./en/index.html">English version</a></li>
                </ul>
                
                <p><a href="../index.html">← Back to all versions</a></p>
              </body>
              </html>
              EOF

          - name: Generate main index with all versions
            run: |
              # Создаем главную страницу со списком всех версий
              cat > index.html << 'EOF'
              <!doctype html>
              <html lang="en">
              <head>
                <meta charset="utf-8">
                <title>Project Site</title>
              </head>
              <body>
                <h1>Project Site</h1>
                
                <div class="version-list">
                  <h2>Все версии:</h2>
                  <ul>
              EOF
              
              # Добавляем все существующие версии в список
              # Сортируем по имени в обратном порядке (новые версии первыми)
              for dir in $(ls -d v*/ 2>/dev/null | sort -Vr); do
                version=${dir%/}
                version_num=${version#v}
                if [ "$version" = "v${{ github.event.release.tag_name }}" ]; then
                  echo "                <li class=\"latest\"><a href=\"./$version/\">Version $version_num (LATEST)</a></li>" >> index.html
                else
                  echo "                <li><a href=\"./$version/\">Version $version_num</a></li>" >> index.html
                fi
              done
              
              cat >> index.html << 'EOF'
                  </ul>
                </div>

                <h2>Navigation:</h2>
                <ul>
                  <li><a href="./ru/index.html">Русская версия</a></li>
                  <li><a href="./en/index.html">English version</a></li>
                </ul>

                <script>
                  console.log('Site version: ${{ github.event.release.tag_name }}');
                </script>
              </body>
              </html>
              EOF

          - name: Deploy to GitHub Pages
            uses: peaceiris/actions-gh-pages@v3
            with:
              github_token: ${{ secrets.GITHUB_TOKEN }}
              publish_dir: ./
              force_orphan: false
              keep_files: true
""")

readme_deploy = textwrap.dedent("""\
    # GitHub Pages / CI/CD deployment

    Что сделано этим генератором:
    - созданы: `ru/index.html`, `en/index.html`, `index.html`
    - создан GitHub Actions workflow: `.github/workflows/deploy_on_release.yml`

    Как это работает:
    1. Когда вы в GitHub создаёте и публикуете *релиз* (Release → publish),
       workflow `Deploy site on release` запускается.
    2. Workflow создает папку `v<tag>/` с копией сайта для этой версии
    3. Workflow автоматически генерирует главную страницу со списком ВСЕХ версий
    4. Все версии сохраняются в папках `v1/`, `v2/`, `v3/` и т.д.
    5. При каждом новом релизе список на главной странице автоматически обновляется
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
print("3) Создайте релиз — workflow автоматически создаст папку v<tag> в ветке gh-pages и добавит ссылки в релиз.")
