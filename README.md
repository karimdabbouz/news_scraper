# news-scraper

This is a python package to scrape news articles in structured format from any news outlet. It takes XPATH selectors and lambda functions as arguments to access headlines, teaser, body text, etc. Example:

After having collected a list of URLs with the ArticleLinkScraper you can then instantiate the ArticleContentScraper with the necessary selectors like this:

```
article_content_scraper = ArticleContentScraper(
    scraping_mode='FRONTEND',
    selenium_headed=True,
    link_list=['https://www.faz.net/aktuell/sport/mehr-sport/marathon-chepkirui-und-nageeye-gewinnen-in-new-york-110087882.html'],
    medium='faz',
    hooks=[lambda driver: close_modal(driver)],
    datetime_published_selector=('//article/header//time', False, lambda element: datetime.datetime.strptime(element.get_attribute('datetime'), '%Y-%m-%dT%H:%M:%SZ')),
    paywall_selector=('//div[@class="wall paywall"]', True, lambda element: True if element else False),
    author_selector=('//article/header//div[@class="header-detail"]', False, lambda element: element.text.replace('Von ', '') if 'Von' in element.text else None),
    category_selector=('//span[contains(@class, "breadcrumbs__item")]', True, lambda element: element[0].text),
    image_url_selector=('//picture/img', False, lambda element: element.get_attribute('src')),
    kicker_selector=('//span[@class="header-label__content"]', False, lambda element: element.text.replace('\n', '')),
    headline_selector=('//div[contains(@class, "header-title")]', False, lambda element: element.text),
    teaser_selector=('//div[@class="header-teaser flex items-start"]', False, lambda element: element.text),
    body_selector=('//p[@class="body-elements__paragraph"]', True, lambda element: [x.text for x in element])
)
```

WIP...