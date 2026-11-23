"""urls.txt에 적힌 Streamlit 앱들을 실제 브라우저로 열어서 잠들지 않게 합니다.
- 잠든 앱이면 'Yes, get this app back up!' 버튼을 찾아 누릅니다(페이지 안쪽 프레임까지 모두 찾음).
- 앱 화면이 실제로 뜰 때까지 기다린 뒤 잠깐 머물러서, Streamlit이 '방문'으로 인정하게 합니다."""
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

WAKE_BUTTON = re.compile(r"get this app back up", re.I)
APP_READY = '[data-testid="stApp"], .stApp'
CHECK_EVERY_MS = 5_000
MAX_CHECKS = 24          # 5초 x 24 = 최대 2분 기다림
STAY_MS = 15_000         # 앱이 뜬 뒤 머무는 시간


def load_urls():
    lines = Path(__file__).with_name("urls.txt").read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in lines if s.strip() and not s.strip().startswith("#")]


def find_wake_button(page):
    for frame in page.frames:
        try:
            btn = frame.get_by_role("button", name=WAKE_BUTTON)
            if btn.count() > 0:
                return btn.first
        except Exception:
            pass
    return None


def app_is_ready(page):
    for frame in page.frames:
        try:
            if frame.locator(APP_READY).count() > 0:
                return True
        except Exception:
            pass
    return False


def visit(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    woke = False
    for _ in range(MAX_CHECKS):
        page.wait_for_timeout(CHECK_EVERY_MS)
        if not woke:
            btn = find_wake_button(page)
            if btn is not None:
                btn.click()
                woke = True
                print(f"[깨우는 중] {url} - 잠들어 있어서 깨우기 버튼을 눌렀어요")
                continue
        if app_is_ready(page):
            page.wait_for_timeout(STAY_MS)
            print(f"[{'깨움 완료' if woke else '정상'}] {url}")
            return
    raise RuntimeError("2분 안에 앱 화면이 뜨지 않았어요")


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
