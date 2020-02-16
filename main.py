import requests
import base64
import os
import argparse
import json
import pycurl
from flask import Flask, url_for, jsonify, request, render_template
from flask_cors import CORS, cross_origin
python3 = False
try:
    from StringIO import StringIO
except ImportError:
    python3 = True
    import io as bytesIOModule
from bs4 import BeautifulSoup
if python3:
    import certifi



app = Flask(__name__)
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILEPATH = os.path.join(APP_ROOT, 'static/imageToSave.png')
host = '192.168.0.101'
@app.route("/")
@app.route("/home")
def home():
    return render_template('index.html')






@app.route('/save', methods=['GET','POST'])
def save_base64_file():
    """
        Upload image with base64 format and get car make model and year
        response
    """

    data = request.get_data()
    print(data)
    img_data = str(data)
    img_data = img_data.replace('b\'data:image/png;base64,', "")

    print(img_data)
    if img_data is None:
        print("No valid request body, json missing!")
        return jsonify({'error': 'No valid request body, json missing!'})
    else:
        # this method convert and save the base64 string to image
        with open(IMAGE_FILEPATH, "wb") as fh:
            fh.write(base64.decodebytes(img_data.encode()))
        return ""

@app.route('/search_image',  methods=['GET','POST'])
def search_image():
    key_imgbb = "d27dd909ec0dfad809a352fee20ace11"

    with open(IMAGE_FILEPATH, "rb") as file:
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": key_imgbb,
            "image": base64.b64encode(file.read()),
        }

    res = requests.post(url, payload)
    # res_json = {'data': {'id': '31kCmfW', 'url_viewer': 'https://ibb.co/31kCmfW',
    #                      'url': 'https://i.ibb.co/sjtV95Q/mario.png',
    #                      'display_url': 'https://i.ibb.co/sjtV95Q/mario.png', 'title': 'mario',
    #                      'time': '1576404031',
    #                      'image': {'filename': 'mario.png', 'name': 'mario', 'mime': 'image/png',
    #                                'extension': 'png', 'url': 'https://i.ibb.co/sjtV95Q/mario.png',
    #                                'size': 233646},
    #                      'thumb': {'filename': 'mario.png', 'name': 'mario', 'mime': 'image/png',
    #                                'extension': 'png', 'url': 'https://i.ibb.co/sjtV95Q/mario.png',
    #                                'size': '57122'},
    #                      'delete_url': 'https://ibb.co/99wG6Sg/f3108ace81f7c82abdf6043fd1df136d'}, 'success': True,
    #             'status': 200}
    res_json = res.json()

    # print(res.json())
    # print(url_for('static', filename='imageToSave.png'))
    url = "https://192.168.0.101:5000/search"

    # "image_url": url_for('static', filename='imageToSave.png')
    data = {
        "image_url": res_json['data']['url'],
        "resized_images": False,  # Or True
        "cloud_api": False
    }

    headers = {'Content-type': 'application/json'}
    r = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

    # r.json to get the response as json
    print(r.json())

    return r.json()

    # r.text for no u'' characters



SEARCH_URL = 'https://www.google.com/searchbyimage?hl=en-US&image_url='


@app.route('/search', methods = ['POST'])
def search():
    if request.headers['Content-Type'] != 'application/json':
        return "Requests must be in JSON format. Please make sure the header is 'application/json' and the JSON is valid."
    client_json = json.dumps(request.json)
    client_data = json.loads(client_json)

    if 'cloud_api' in client_data and client_data['cloud_api'] == True:
        saveImage(client_data['image_url'])
        data = getCloudAPIDetails("./default.jpg")
        return jsonify(data)

    else:
        code = doImageSearch(SEARCH_URL + client_data['image_url'])

        if 'resized_images' in client_data and client_data['resized_images'] == True:
            return parseResults(code, resized=True)
        else:
            return parseResults(code)

def doImageSearch(full_url):
    # Directly passing full_url
    """Return the HTML page response."""

    if python3:
        returned_code = bytesIOModule.BytesIO()
    else:
        returned_code = StringIO()
    # full_url = SEARCH_URL + image_url

    if app.debug:
        print('POST: ' + full_url)

    conn = pycurl.Curl()
    if python3:
        conn.setopt(conn.CAINFO, certifi.where())
    conn.setopt(conn.URL, str(full_url))
    conn.setopt(conn.FOLLOWLOCATION, 1)
    conn.setopt(conn.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
    conn.setopt(conn.WRITEFUNCTION, returned_code.write)
    conn.perform()
    conn.close()
    if python3:
        return returned_code.getvalue().decode('UTF-8')
    else:
        return returned_code.getvalue()

def parseResults(code, resized=False):
    """Parse/Scrape the HTML code for the info we want."""

    soup = BeautifulSoup(code, 'html.parser')

    results = {
        'links': [],
        'descriptions': [],
        # 'titles': [],
        # 'similar_images': [],
        'best_guess': ''
    }

    for div in soup.findAll('div', attrs={'class':'rc'}):
        sLink = div.find('a')
        results['links'].append(sLink['href'])

    for desc in soup.findAll('span', attrs={'class':'st'}):
        results['descriptions'].append(desc.get_text())

    # for title in soup.findAll('h3', attrs={'class':'r'}):
    #     results['titles'].append(title.get_text())

    # for similar_image in soup.findAll('div', attrs={'rg_meta'}):
    #     tmp = json.loads(similar_image.get_text())
    #     img_url = tmp['ou']
    #     results['similar_images'].append(img_url)
    #
    for best_guess in soup.findAll('a', attrs={'class':'fKDtNb'}):
      results['best_guess'] = best_guess.get_text()

    if resized:
        results['resized_images'] = getDifferentSizes(soup)

    print("Successful search")

    return json.dumps(results)

def getDifferentSizes(soup):
    """
    Takes html code ( souped ) as input

    Returns google's meta info on the different sizes of the same image from different websites

    Returns a list of JSON objects of form

    {
        'rh': 'resource_host',
        'ru': 'resource_url',
        'rid': 'SOME_ID_USED_BY_GOOGLE',
        'ou': 'original_url of image
        'oh': 'orginal_height',
        'ow': 'original_width',
        'ity': 'image type',
        'tu': 'thumbnail_url of image', # Generated by google
        'th': 'thumbnail_height',
        'tw': 'thumbnail_width',
        's': 'summary'
        'itg': 'SOME UNKNOWN TERM',
        'pt': 'pt', # some short description (UNKNOWN TERM)
        'sc': "SOME UNKNOWN TERM",
        'id': 'SOME_ID_USED_BY_GOOGLE',
        'st': 'Site', # UNKOWN TERM
        'rt': 'UNKNOWN TERM',
        'isu': 'resource_host', # (UNKNOWN TERM)
    }

    """

    region = soup.find('div',{"class":"O1id0e"})

    span = region.find('span',{"class":"gl"})

    allsizes = False

    try:

        if span.a.get_text() == "All sizes":
            allsizes = True
        else:
            print("not all sizes")
            print(span)
    except Exception as e:
        print(str(e))
        return [{'error':'500','details':'no_images_found'}]

    if allsizes:
        new_url = "https://google.com" + span.a['href']

    resized_images_page = doImageSearch(new_url)

    new_soup = BeautifulSoup(resized_images_page,"lxml")

    main_div = new_soup.find('div',{"id":"search"})

    rg_meta_divs = main_div.findAll('div',{"class":"rg_meta notranslate"})

    results = []

    for item in rg_meta_divs:
        results.append(json.loads(item.text))

    return results

def main():
    parser = argparse.ArgumentParser(description='Meta Reverse Image Search API')
    parser.add_argument('-p', '--port', type=int, default=5000, help='port number')
    parser.add_argument('-d','--debug', action='store_true', help='enable debug mode')
    parser.add_argument('-c','--cors', action='store_true', default=False, help="enable cross-origin requests")
    args = parser.parse_args()

    if args.debug:
        app.debug = True

    if args.cors:
        CORS(app, resources=r'/search/*')
        app.config['CORS_HEADERS'] = 'Content-Type'

        global search
        search = cross_origin(search)
        print(" * Running with CORS enabled")


    app.run(host= "0.0.0.0", port=args.port, ssl_context='adhoc', threaded=True)

if __name__ == '__main__':
    main()




