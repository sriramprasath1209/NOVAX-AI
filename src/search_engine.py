import json
import ssl
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class SearchEngine:

    def __init__(self):
        self.ssl_context = ssl._create_unverified_context()

    def fetch_live_news(self, query="India"):
        """
        Fetches live real-time news headlines from Google News RSS feeds.
        """
        try:
            clean_query = query.lower()
            for kw in ["can you say about the", "can you tell me", "what is the", "show me", "tell me about", "latest", "news", "updates", "update", "today", "current", "say about"]:
                clean_query = clean_query.replace(kw, "").strip()

            clean_query = clean_query or "India"

            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(clean_query)}&hl=en-IN&gl=IN&ceid=IN:en"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            )
            raw = urllib.request.urlopen(req, context=self.ssl_context, timeout=5).read()
            root = ET.fromstring(raw)
            items = root.findall(".//item")

            headlines = []
            for item in items[:6]:
                title = item.find("title").text if item.find("title") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                if title:
                    headlines.append(f"- {title} ({pub_date})")

            if headlines:
                return "\n".join(headlines)
        except Exception:
            return None

        return None

    def search_wikipedia(self, query):
        """
        Performs a live Wikipedia search for accurate facts.
        """
        try:
            clean_query = query.strip()
            url = (
                "https://en.wikipedia.org/w/api.php?"
                "action=query&generator=search&gsrsearch="
                + urllib.parse.quote(clean_query)
                + "&prop=pageimages|extracts&exintro=1&explaintext=1&pithumbsize=800&format=json"
            )
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "NOVAX-AI/1.0 (https://novax.ai; contact@novax.ai)"}
            )
            raw_response = urllib.request.urlopen(req, context=self.ssl_context, timeout=5).read().decode("utf-8")
            data = json.loads(raw_response)

            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None

            sorted_pages = sorted(pages.values(), key=lambda p: p.get("index", 999))
            
            results = []
            for page in sorted_pages[:2]:
                title = page.get("title")
                extract = page.get("extract", "").strip()

                if extract and title:
                    results.append({
                        "title": title,
                        "extract": extract[:500]
                    })

            if results:
                return results
        except Exception:
            return None

        return None
