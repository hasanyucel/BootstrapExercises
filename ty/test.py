import requests, json, regex, os,re,cloudscraper,sqlite3
from lxml import html
from bs4 import BeautifulSoup
from rich import print
import time

db = 'trendyol.db'

def get_seller_id(url): #Verilen URL'den satıcının idsini döner.
    start_index = url.rfind("m-") + 2
    end_index = url.find("?", start_index)
    if end_index == -1: # eğer '&' işareti yoksa end_index -1 olacaktır
        seller_id = url[start_index:]
    else:
        seller_id = url[start_index:end_index]
    return seller_id

def create_seller_product_reviews_summary_table(): #Satıcıya ait ürün değerlendirmeleri özetlerinin girilmesi için tablo oluşturur.
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS seller_product_reviews_summary (
                  id INTEGER PRIMARY KEY,
                  sellerId TEXT UNIQUE,
                  averageRating FLOAT,
                  totalRatingCount INTEGER,
                  totalCommentCount INTEGER,
                  rate1Count INTEGER,
                  rate1CommentCount INTEGER,
                  rate2Count INTEGER,
                  rate2CommentCount INTEGER,
                  rate3Count INTEGER,
                  rate3CommentCount INTEGER,
                  rate4Count INTEGER,
                  rate4CommentCount INTEGER,
                  rate5Count INTEGER,
                  rate5CommentCount INTEGER
                  )''')
    conn.close()

def create_seller_products_table():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS seller_products (
                        id INTEGER PRIMARY KEY,
                        product_id INTEGER UNIQUE,
                        name TEXT,
                        image1 TEXT,
                        brand_id INTEGER,
                        brand_name TEXT,
                        business_unit TEXT,
                        average_rating REAL,
                        total_rating_count INTEGER,
                        category_hierarchy TEXT,
                        category_id INTEGER,
                        category_name TEXT,
                        url TEXT,
                        merchant_id INTEGER,
                        campaign_id INTEGER,
                        selling_price REAL,
                        original_price REAL,
                        discounted_price REAL,
                        buying_price REAL,
                        listing_id TEXT,
                        item_number INTEGER
                    )''')
    conn.close()

def create_seller_product_reviews_table():
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS seller_product_reviews
                (reviewId INTEGER PRIMARY KEY, userId INTEGER, contentId TEXT,
                reviewStatusName TEXT, rate INTEGER, commentTitle TEXT, comment TEXT,
                userFullName TEXT, showUserName INTEGER, trusted INTEGER, platform TEXT,
                createdDate INTEGER, lastModifiedDate INTEGER, sellerId INTEGER,
                userType TEXT, orderNumber TEXT)''')
    conn.close()

def insert_seller_product(product):
    conn = sqlite3.connect(db)
    print(product)
    query = '''INSERT OR REPLACE INTO seller_products (product_id, name, image1, brand_id, brand_name, business_unit,
                                               average_rating, total_rating_count, category_hierarchy, category_id,
                                               category_name, url, merchant_id, campaign_id, selling_price,
                                               original_price, discounted_price, buying_price, listing_id, item_number)
               VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    rating_score = product.get('ratingScore', None)
    if rating_score is None:
        averageRating = 0
        totalCount = 0
    else:
        averageRating = product['ratingScore']['averageRating']
        totalCount = product['ratingScore']['totalCount']
    params = (product['id'],product['name'], 'https://cdn.dsmcdn.com'+product['images'][0], product['brand']['id'], product['brand']['name'], 
              product['businessUnit'], averageRating, totalCount, 
              product['categoryHierarchy'], product['categoryId'], product['categoryName'], 'https://www.trendyol.com'+product['url'], product['merchantId'], 
              product['campaignId'], product['price']['sellingPrice'], product['price']['originalPrice'], product['price']['discountedPrice'], 
              product['price']['buyingPrice'], product['listingId'], product['itemNumber'])
    conn.execute(query, params)
    conn.commit()
    conn.close()

def get_all_product_comments_summary(seller_id): #Verilen satıcı idsine ait ürün değerlendirmeleri özetlerinin olduğu JSON verisini döner.
    url = f"https://public-mdc.trendyol.com/discovery-sellerstore-webgw-service/v1/ugc/product-reviews/reviews/{seller_id}?page=0&size=1&isMarketplaceMember=true"
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False},delay=10)
    data = scraper.get(url).text
    data = json.loads(data)
    return data

def save_product_reviews_summary_to_db(seller_id): #Verilen satıcı idsine ait ürün değerlendirme özetlerini dbye yazar.
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    json_data = get_all_product_comments_summary(seller_id)
    content_summary = json_data['contentSummaryDTO']
    average_rating = content_summary['averageRating']
    total_rating_count = content_summary['totalRatingCount']
    total_comment_count = content_summary['totalCommentCount']
    rating_counts = content_summary['ratingCounts']
    rate1_count = 0
    rate1_comment_count = 0
    rate2_count = 0
    rate2_comment_count = 0
    rate3_count = 0
    rate3_comment_count = 0
    rate4_count = 0
    rate4_comment_count = 0
    rate5_count = 0
    rate5_comment_count = 0
    for rating in rating_counts:
        if rating['rate'] == 1:
            rate1_count = rating['count']
            rate1_comment_count = rating['commentCount']
        elif rating['rate'] == 2:
            rate2_count = rating['count']
            rate2_comment_count = rating['commentCount']
        elif rating['rate'] == 3:
            rate3_count = rating['count']
            rate3_comment_count = rating['commentCount']
        elif rating['rate'] == 4:
            rate4_count = rating['count']
            rate4_comment_count = rating['commentCount']
        elif rating['rate'] == 5:
            rate5_count = rating['count']
            rate5_comment_count = rating['commentCount']

    cursor.execute('''INSERT OR REPLACE INTO seller_product_reviews_summary(
                          sellerId,
                          averageRating,
                          totalRatingCount,
                          totalCommentCount,
                          rate1Count,
                          rate1CommentCount,
                          rate2Count,
                          rate2CommentCount,
                          rate3Count,
                          rate3CommentCount,
                          rate4Count,
                          rate4CommentCount,
                          rate5Count,
                          rate5CommentCount
                          )
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (seller_id,
                          average_rating,
                          total_rating_count,
                          total_comment_count,
                          rate1_count,
                          rate1_comment_count,
                          rate2_count,
                          rate2_comment_count,
                          rate3_count,
                          rate3_comment_count,
                          rate4_count,
                          rate4_comment_count,
                          rate5_count,
                          rate5_comment_count)
                      )
    conn.commit()
    conn.close()

def get_all_product_comments_count(seller_id): #Verilen satıcı idsine ait ürün yorumları sayısını döner.
    url = f"https://public-mdc.trendyol.com/discovery-sellerstore-webgw-service/v1/ugc/product-reviews/reviews/{seller_id}?page=0&size=1&isMarketplaceMember=true"
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False},delay=10)
    data = scraper.get(url).text
    data = json.loads(data)
    return data["productReviews"]["totalElements"]

def get_seller_products_data(seller_id,pi=1): #Verilen satıcıya ait ürün bilgilerini JSON olarak döner.
    url = f'https://www.trendyol.com/sr?mid={seller_id}&pi={pi}'
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False},delay=200)
    data = scraper.get(url).content
    soup = BeautifulSoup(data, 'html.parser')
    products = soup.findAll('script', text = re.compile('__SEARCH_APP_INITIAL_STATE__'))
    pattern = '\{(?:[^{}]|(?R))*\}'
    result = regex.search(pattern, str(products[0]))[0]
    data = json.loads(result)
    #with open('data.json', 'w') as f:
    #    json.dump(data, f)
    return data

def get_seller_product_pages_count(seller_id): #Verilen satıcı idye ait tüm ürünlerin bulunduğu sayfa sayısını döner. Her sayfada 24 ürün bulunur.
    data = get_seller_products_data(seller_id)
    totalProductCount = data["totalCount"] #Satıcıda bulunan toplam ürün adedi
    productPageCount = int((totalProductCount / 24) + 1) #Maksimum sayfa
    return productPageCount

def save_seller_product_review_to_db(data):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    #print(data)
    for review in data['productReviews']['content']:
        review_id = review['id']
        user_id = review['userId']
        content_id = review['contentId']
        review_status_name = review['reviewStatus']['reviewStatusName']
        rate = review['rate']
        comment_title = review['commentTitle']
        comment = review['comment']
        if 'userFullName' not in review:
            user_full_name = '-'
        else:
            user_full_name = review['userFullName']
        if review['showUserName'] is None:
            show_user_name = '-'
        else:
            show_user_name = review['showUserName']
        trusted = review['trusted']
        platform = review['platform']
        created_date = review['createdDate']
        last_modified_date = review['lastModifiedDate']
        seller_id = review['sellerId']
        user_type = review['userType']
        order_number = review['orderNumber']
        cursor.execute('''INSERT OR REPLACE INTO seller_product_reviews
                    (reviewId, userId, contentId, reviewStatusName, rate, commentTitle, comment,
                    userFullName, showUserName, trusted, platform, createdDate, lastModifiedDate,
                    sellerId, userType, orderNumber)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (review_id, user_id, content_id, review_status_name, rate, comment_title, comment,
                user_full_name, show_user_name, trusted, platform, created_date, last_modified_date,
                seller_id, user_type, order_number))
        conn.commit()
    conn.close()

def insert_seller_product_infos(seller_id,productPageCount):
    #products = []
    for i in range(1,productPageCount+1): #Satıcının tüm ürün sayfalarını döner
        data = get_seller_products_data(seller_id,i) #Sayfalardaki ürün bilgilerini alır.
        for i in range (len(data["products"])): 
            #products.append('https://www.trendyol.com'+ data["products"][i]["url"])
            #print(i,str(data["products"][i]["id"]),'https://www.trendyol.com'+ data["products"][i]["url"],data["products"][i]["name"])
            insert_seller_product(data["products"][i])
            
        time.sleep(1)
    #return products

def get_all_product_comments(seller_id,size,page): #Verilen satıcı idsine ait ürün değerlendirmeleri özetlerinin olduğu JSON verisini döner.
    url = f"https://public-mdc.trendyol.com/discovery-sellerstore-webgw-service/v1/ugc/product-reviews/reviews/{seller_id}?page={page}&size={size}&isMarketplaceMember=true"
    scraper = cloudscraper.create_scraper(browser={'browser': 'firefox','platform': 'windows','mobile': False},delay=10)
    data = scraper.get(url).text
    data = json.loads(data)
    return data


seller_id = get_seller_id("https://www.trendyol.com/magaza/nevresim-dunyasi-m-107700?sst=0")
create_seller_product_reviews_summary_table()
create_seller_products_table()
create_seller_product_reviews_table()
save_product_reviews_summary_to_db(seller_id) # Değerlendirme Özetleri
productPageCount = get_seller_product_pages_count(seller_id) # Ürün sayısı / 24 = sayfa sayısı 
insert_seller_product_infos(seller_id,productPageCount)
seller_comments_count = get_all_product_comments_count(seller_id)
size = 100
seller_comment_page_count = (seller_comments_count / size) + 1 
for i in range(int(seller_comment_page_count)):
    review_data = get_all_product_comments(seller_id,size,i)
    save_seller_product_review_to_db(review_data)

#seller_info adında tablo oluşturulacak. Satıcının bilgilerini içericek. 
#Önce yorumlar çekilecek. Tek tek dbde product_reviews tablosuna eklenecek. Var olan veya güncellenmemiş yorumlar eklenmeyecek. id ve lastModifiedDate sütununa göre tekillik sağlanabilir.
#Mağazaki tüm ürünler ve linkleri toplanacak. seller_product_links tablosuna eklenecek. burada insert or replace kullanılabilir. product_reviews tablosunda contentId buradaki productId ile eşleşecek.
#seller_products tablosu oluşturulacak.


#import datetime
#
#unix_timestamp = 1676703842621 / 1000  # milisaniyeleri saniyelere çeviriyoruz
#date = datetime.datetime.fromtimestamp(unix_timestamp)
#
#print(date.strftime('%d/%m/%Y %H:%M:%S'))
