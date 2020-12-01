### Call to OS
import os

### Scraping setup
from bs4 import BeautifulSoup
import requests
import json
import time
#print('Scraping')
## SMS notification setup

#os.system('pip install requests')
#os.system('pip install clx-sdk-xms')
import clx.xms
import requests

client = clx.xms.Client(service_plan_id='bbf28c598d0d435fa566cc11f44ab1be', token='b34b08f442a84bdc8523685b7b539258')

create = clx.xms.api.MtBatchTextSmsCreate()
create.sender = '447537404817'
create.recipients = {'5561991155786'}
#print('SMS')

### Write to gsheets setup
#os.system('pip install gspread')
#os.system('pip install oauth2client')
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name(
         'credentials.json', scope) # Your json file here

gc = gspread.authorize(credentials)

wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1DWm0sZUQXHQ8AY-x3KQpdzw9hkL6QLKVe0QTH68v8IU/edit#gid=0")
#print('GSPREAD')


### CODE

LIMIT = 2

VIEWED_FILE = "./viewed/cl"
REGION      = "minneapolis"
KEY_WORDS   = open('KEYWORDS.txt','r').read().split('\n')
#input()
for key_word in KEY_WORDS:
    print(key_word)
    # Read viewed itens in local file
    if os.path.exists(f'{VIEWED_FILE}/{key_word}.csv'):
        viewed = open(f'{VIEWED_FILE}/{key_word}.csv','r').read().split('\n')
    else:
        viewed = []

    # Create sheets online
    """
    try:
        wk = wks.add_worksheet(title=key_word.upper(), rows="10", cols="8")
        wk.insert_row(["Timestamp", "Item name" , "Price", "Description", "Location", "Category", "Product URL", "Image_url"],1)
    except:
        wk = wks.worksheet(key_word.upper())            
    """

    #There is only one sheet
    wk = wks.worksheet('DATA')

    url =f"http://{REGION}.craigslist.org/d/for-sale/search/sss?sort=date&query={key_word}"
    source = 'craigslist'
    r = requests.get(url)
    soup = BeautifulSoup(r.text,'html.parser')
    #print(soup)

    new=[]
    i=0
    for ele in soup.find_all(class_='result-row'):
        try:
            print(ele['data-pid'])
            if ele['data-pid'] not in viewed:
                viewed.append(ele['data-pid'])
                item_name = ele.find(id = 'postid_'+ele['data-pid']).text
                price     = ele.find(class_='result-price').text
                timestamp = ele.find(class_='result-date')['title']
                product_url = ele.find('a')['href']
                print('\nProduct url = ',product_url)
                r_product = requests.get(product_url)
                time.sleep(1)
                soup_product = BeautifulSoup(r_product.text,'html.parser')
                description = soup_product.find(id = 'postingbody').text.replace('\n\nQR Code Link to This Post\n\n','')
                print("Description =", description)
                json_product = soup_product.find(id = 'ld_posting_data')
                try:
                    zip_code = json.loads(str(json_product).split('\n')[1])['offers']['availableAtOrFrom']['address']['postalCode']
                except:
                    try:
                        zip_code = f"No ZIPCODE\nCoordinates\nLatitude:({soup_product.find(id='map')['data-latitude']})\nLongitude:({soup_product.find(id='map')['data-longitude']})"
                    except:
                        zip_code = 'No zipcode'

                print('Zip = ',zip_code)
                category = soup_product.find('ul',class_='breadcrumbs').text.replace('\n','').replace('>',' > ')
                try:
                    img_url = json.loads(str(json_product).split('\n')[1])['image'][0]
                except:
                    img_url = 'no image'
                print('Image URL = ',img_url)

                
                # SMS
                create.body =f"{item_name} (from CRAIGSLIST) just posted.\nHere’s the link {product_url}"
                
                try:
                    batch = client.create_batch(create)
                except (requests.exceptions.RequestException,
                    clx.xms.exceptions.ApiException) as ex:
                    print('Failed to communicate with XMS: %s' % str(ex))
                
                # GSPREAD
                wk.insert_row([source,key_word,timestamp, item_name, price+'.00', description[1:], zip_code, category, product_url, img_url],2)                        
                new.append(ele['data-pid'])
        except:
            pass
        i+=1
        if i==LIMIT:break
    #Store in file
    if not os.path.isdir(f'{VIEWED_FILE}'):
        os.mkdir(f'{VIEWED_FILE}')
    else:
        if not os.path.exists(f'{VIEWED_FILE}/{key_word}.csv'):
            viewed_file = open(f'{VIEWED_FILE}/{key_word}.csv','w')            
        else:
            viewed_file = open(f'{VIEWED_FILE}/{key_word}.csv','a')
        
        for ele in new:
            viewed_file.write(ele+'\n')

        viewed_file.close()
