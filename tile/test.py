import requests,time,cloudscraper,sqlite3,concurrent.futures
from bs4 import BeautifulSoup
from rich import print 

MAX_THREADS = 30
products = []

def createDbAndTables():
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS 'SiteMapLinks' ('Url' TEXT NOT NULL,PRIMARY KEY('Url'));")
    conn.commit()
    cur.execute("CREATE TABLE IF NOT EXISTS 'StockPrice' ('SKU' TEXT NOT NULL,'Date' DATE NOT NULL,'Stock'	REAL NOT NULL,'Price' REAL NOT NULL);")
    conn.commit()
    cur.execute("CREATE TABLE IF NOT EXISTS 'Products' ('SKU' TEXT,'Name' TEXT,'Categories' TEXT,'Size' REAL,'Meas' TEXT,'Material' TEXT,'Finish' TEXT,'Url' TEXT,PRIMARY KEY('SKU'));")
    conn.commit()
    conn.close()

def insertAllLinks():
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    xml = 'https://www.tilemountain.co.uk/sitemap/sitemap.xml'
    r = requests.get(xml)
    soup = BeautifulSoup(r.text, 'lxml')
    urls = [loc.string for loc in soup.find_all('loc')]
    for url in urls:
        if url.startswith("https://www.tilemountain.co.uk/p/"):
            cur.execute("INSERT OR IGNORE INTO SiteMapLinks (URL) VALUES (?)",(url,))
    conn.commit()
    conn.close()

def product_info(url):
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False},delay=10)
    html = scraper.get(url).content
    soup = BeautifulSoup(html, 'lxml')
    print(url)
    sku = soup.find('span',attrs={"class":"sku-value"}).text.strip()
    title = soup.find('h1',attrs={"class":"mb20 mt0 cl-mine-shaft product-name"}).text.strip()
    size = soup.find('span',attrs={"class":"size-value"})
    if size is not None:
        size = size.text
    else:
        size = None
    stock = soup.find('span',attrs={"class":"sqm"}).text
    price = soup.find('span',attrs={"class":"h2 cl-mine-shaft weight-700"}).text.strip()
    material = soup.select("#viewport > div.product-page-detail > section.container.px15.pt20.pb35.cl-accent.details.product-desc > div > div > div.col-xs-12.col-sm-12.col-md-12.col-lg-6.infoprod-col > div > div.tabs-content-box > div > div > ul > li:nth-child(8) > span.detail")
    if material:
        material = Material[0].text
    else:
        material = "-"
    category = soup.find('div',attrs={"class":"breadcrumbs h5 cl-gray pt40 pb20 hidden-xs breadcrumb"})
    category = category.findAll('a')
    categories = []
    for x in category:
        categories.append(x.text.strip())
    categories = '/'.join(categories)
    #Product bilgilerini product tablosuna yaz
    #Price ve stock bilgilerini pricestock tablosuna yaz.
    product = (sku,title,categories,size,material,stock,price,url)
    print(product)
    products.append(product)
    
    time.sleep(0.25)
    
def insertProductInfos(sku,name,categories,size,meas,material,finish,url):
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO Products (sku,name,categories,size,meas,material,finish,url) VALUES (?,?,?,?,?,?,?,?)",(sku,name,categories,size,meas,material,finish,url))
    conn.commit()
    conn.close()

def PoolExecutor(urls):
    threads = min(MAX_THREADS, len(urls))
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(product_info, urls)

def getSiteMapLinks():
    conn = sqlite3.connect('db.sqlite')
    cur = conn.cursor()
    cur.execute('SELECT Url FROM SiteMapLinks')
    links = cur.fetchall()
    links = [f[0] for f in links]
    conn.close()
    return links

createDbAndTables()
insertAllLinks()
#urls = getSiteMapLinks()

insertProductInfos("234", "hasan", "ahmet", "600x600","ad", "porcelain", "cilal2ı", "www.google.com")
"""urls = []
f = open("links.txt",'r') 
for line in f:
    line = line.replace("\n", "")
    urls.append(line)
    #product_info(line)"""

"""t0 = time.time()
PoolExecutor(urls)
t1 = time.time()
print(len(urls),len(products))
print(f"{t1-t0} seconds.")"""