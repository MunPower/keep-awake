"""urls.txt에 적힌 Streamlit 앱들을 실제 브라우저로 열어서 잠들지 않게 합니다.
잠든 앱이면 'Yes, get this app back up!' 버튼을 눌러 깨웁니다."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WAKE_BUTTON = re.compile(r"get this app back up", re.I)


def load_urls():
    lines = Path(__file__).with_name("urls.txt").read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in lines if s.strip() and not s.strip().startswith("#")]


def visit(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(8_000)  # 화면이 뜰 시간
    button = page.get_by_role("button", name=WAKE_BUTTON)
    if button.count() > 0:
        button.first.click()
        print(f"[깨움] {url} - 잠들어 있어서 깨우기 버튼을 눌렀어요")
        page.wait_for_timeout(45_000)  # 서버가 올라올 시간
    else:
        print(f"[정상] {url} - 깨어 있어요")


def main():
    urls = load_urls()
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for url in urls:
            try:
                visit(page, url)
            except Exception as e:  # 한 앱이 실패해도 나머지는 계속
                print(f"[실패] {url} - {e}")
                failed.append(url)
        browser.close()
    if failed:
        sys.exit(1)  # 실패가 있으면 Actions에 빨간 X로 표시


if __name__ == "__main__":
    main()
