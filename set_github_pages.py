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
