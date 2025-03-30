from turtle import st
from utils.fetcher import fetch_page
from parsers import ParserType, get_parser
from db.storage import Storage

def main():

    # url = "https://www.tatacliq.com"
    url = "https://www.virgio.com/"
    base_url = url
    html_content = fetch_page(url)

    simple_parser = get_parser(ParserType.SIMPLE)
    config_parser = get_parser(ParserType.CONFIG)
    ai_parser = get_parser(ParserType.AI)

    active_parser = simple_parser
    # active_parser = config_parser
    active_parser = ai_parser

    if html_content:
        product_urls = active_parser.parse(html_content, base_url)
        print("Extracted product URLs:")
        if not product_urls:
            print("No product URLs found.")
        else:
            for url in product_urls:
                print(url)
    else:
        print("Failed to fetch the webpage.")

    if product_urls:
        storage = Storage()
        for url in product_urls:
            storage.save(url)
        print("Product URLs saved to storage.")


if __name__ == "__main__":
    main()