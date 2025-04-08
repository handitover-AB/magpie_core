"""Implement state functions for internet search test"""
import re
from app import Page, expect


LOCATOR_HTML_BODY = "xpath=//html/body"


def start(_):
    pass


def at_start_page(page: Page):
    """At the DuckDuckGo start page"""
    expect(page).to_have_url("https://start.duckduckgo.com/")


def at_search_page(page: Page):
    """The DuckDuckGo page contaning search results"""
    url_pattern = re.compile(r"https://duckduckgo.com/\?.*q=Magpie.*")
    search_hit_pattern = re.compile(r".*Magpie - Wikipedia.*")
    expect(page).to_have_url(url_pattern)
    expect(page.locator("body")).to_have_text(search_hit_pattern)
