from flask import *
import requests
import pickle
from datetime import datetime
import city
import pandas as pd
import os
from sklearn import preprocessing
import smtplib

constant = int(1e3)
format_data = "%d/%m/%y"

app = Flask(__name__)


# để chạy được code nhớ pip install flask !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# index
@app.route('/')
@app.route('/index')
@app.route('/index.html')
def index():
    return render_template('index.html')


# 404 not found page
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


api_key = "f978c96591a433fbbada0ef7e7d323b1"


def time_from_utc_with_timezone(utc_with_tz):
    local_time = datetime.utcfromtimestamp(utc_with_tz)
    return local_time.time()


c = []
for x in city.city:
    c.append(x)

data = []
label = ['Temp', 'Feel temp', 'Pressure', 'Humidity', 'Wind speed', 'Sunrise time', 'Sunset time', 'Cloud',
         'Description']


def get_weather(lat, lon):
    # url = f"http://history.openweathermap.org/data/2.5/history/city?lat=41.85&lon=-87&type=hour&start=1643720400&end=1643806800&appid={api_key}"
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
    print(url)
    response = requests.get(url).json()
    kelvin = 273.15
    temp = int(response['main']['temp'] - kelvin)
    feel_temp = int(response['main']['feels_like'] - kelvin)
    pressure = response['main']['pressure']
    humidity = response['main']['humidity']
    wind_speed = response['wind']['speed'] * 3.6
    sunrise = response['sys']['sunrise']
    sunset = response['sys']['sunset']
    timezone = response['timezone']
    cloud = response['clouds']['all']
    description = response['weather'][0]['description']
    sunrise_time = time_from_utc_with_timezone(sunrise + timezone)
    sunset_time = time_from_utc_with_timezone(sunset + timezone)
    city = response['name']
    print(f"Weather infomation of {city}")
    print(f"Temp (Celsius): {temp}")
    print(f"Feel likes in (Celcius): {feel_temp}")
    print(f"Pressure: {pressure} hPa")
    print(f"Humidity: {humidity}%")
    print("Wind speed: {0:.2f} km/hr".format(wind_speed))
    print(f"Sunrise at {sunrise_time} ans Sunset at {sunset_time}")
    print(f"Cloud: {cloud}%")
    print(f"Info: {description}")
    data.clear()
    data.extend([str(temp) + "°C", str(feel_temp) + "°C", str(pressure) + "hPa", str(humidity) + "%",
                 str(round(wind_speed)) + "km/hr", sunrise_time, sunset_time, str(cloud) + "%", description])


@app.route('/test')
def performweather_1():
    return render_template('test.html')


@app.route('/weather_perform', methods=['POST', 'GET'])
def performweather():
    c = []
    for x in city.city:
        c.append(x)
    loc = request.form.get('comp_select')
    location = "Weather information of " + loc
    a = []
    for value in city.city[loc]:
        a.append(value)
    lat = a[0]
    long = a[1]
    a.clear()
    get_weather(lat, long)
    return render_template('weather.html', lat=lat, long=long, city=c, location=location, label=label, data=data,
                           loc=loc)


# weather draf mode
@app.route('/weather')
@app.route('/weather.html')
def weather():
    return render_template('weather.html', city=c)


# Gogo solar ranger
@app.route('/solar')
@app.route('/solar.html')
def solar():
    return render_template('solarpredict.html')


# model testing heere
@app.route('/runmodel', methods=['GET', 'POST'])
def runmodel():
    try:
        if request.method == 'POST':
            file = request.files['csvfile']
            if not os.path.isdir('static'):
                os.mkdir('static')
            filepath = os.path.join('static', file.filename)
            file.save(filepath)

            df = pd.read_csv(filepath)
            start = str(df['datetime'][0])
            end = str(df['datetime'][df['datetime'].count() - 1])
            # df.drop(
            # ['name', 'datetime', 'preciptype', 'precip', 'snow', 'snowdepth', 'solarenergy', 'severerisk', 'conditions',
            # 'icon', 'stations', 'visibility'], axis=1, inplace=True)
            df = df[
                ['datetime', 'temp', 'feelslike', 'dew', 'humidity', 'windgust', 'windspeed', 'winddir', 'cloudcover',
                 'solarradiation',
                 'precipprob', 'sealevelpressure', 'uvindex']]

            # dropping missing values
            df.dropna(inplace=True)
            table = pd.DataFrame()

            # get datetime
            table['datetime'] = df['datetime']
            df = df[
                ['temp', 'feelslike', 'dew', 'humidity', 'windgust', 'windspeed', 'winddir', 'cloudcover',
                 'solarradiation',
                 'precipprob', 'sealevelpressure', 'uvindex']]

            X = df.values
            X = preprocessing.scale(X)
            X = X.tolist()

            path = 'model/'
            with open(path + 'main_RFmodel3.pkl', 'rb') as f:
                model = pickle.load(f)

            pred = model.predict(X)
            # return render_template('prediction.html', predictions = pred['predictions'][0]['values'])

            # get prediction
            table['pred'] = pred

            # convert str to timestamps
            table['datetime'] = pd.to_datetime(table['datetime'])

            # group by month
            table_month = table.resample('M', on='datetime').pred.sum()

            # group by day
            table = table.resample('D', on='datetime').pred.sum()

            # create dictionary for day
            d = {}
            i = 0
            for key in table.index:
                d[str(key)[0:10]] = table[i]
                i = i + 1

            sum_predict = 0
            day_predict = []
            value_predict = []
            maximum = ~(1 << 31)
            minimum = 1 << 31
            for key, value in d.items():
                day_predict.append(datetime.strptime(key, '%Y-%m-%d').strftime('%d-%m-%Y'))
                maximum = max(maximum, value / constant)
                minimum = min(minimum, value / constant)
                value_predict.append(value / constant)
                sum_predict += (value / constant)
            # create dictionary for month
            d_month = {}
            i = 0
            for key in table_month.index:
                d_month[str(key)[0:7]] = table_month[i]
                i = i + 1
            avg = sum_predict / len(d)
            month_predict = []
            value_month_predict = []
            for key, value in d_month.items():
                month_predict.append(datetime.strptime(key, '%Y-%m').strftime('%m-%Y'))
                value_month_predict.append(value / constant)

        return render_template('results.html', s=datetime.strptime(start[0:10], '%Y-%m-%d').strftime('%d-%m-%Y'),
                               e=datetime.strptime(end[0:10], '%Y-%m-%d').strftime('%d-%m-%Y'),
                               a=value_predict, b=day_predict, c=value_month_predict, d=month_predict, sum=sum_predict,
                               maximum=maximum, minimum=minimum, avg=avg)
    except:
        return render_template('404.html')


@app.route('/contact.html')
@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/formContact', methods=['POST'])
def sendContactForm():
    name = request.form['fullname']
    email = request.form['email']
    message = request.form['msg']
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        # region Login
        smtp.login('kimlong101020@gmail.com', 'arbzgnhgtnoiisqu')
        # endregion
        subject = name + " " + "question"
        body = "Guess name: " + name + "\nEmail: " + email + "\n" + "Message: " + message
        # body = u' '.join((name, email, message)).encode('utf-8').strip()
        # body = r.join((name, '\n', email, '\n', message)).encode('utf-8').strip()
        msg = f'Subject: {subject}\n\n{body}'.encode('utf-8').strip()
        smtp.sendmail('kimlong101020@gmail.com', 'huytd218@uef.edu.vn', msg)
    return redirect(url_for('contact'))


if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(debug=True, threaded=True)

# ......................................................................................................................................................
# ......................................................................................................................................................
# ......................................................................................................................................................
# ......................................................................................................................................................
# ......................................................................................................................................................
# ......................................................................................................................................................
# ..................................................................:^~!!77777777!~^::..................................................................
# ...............................................................:!?YYY5555555555555YJ7^................................................................
# ...............................................................7557^:~JYYYYYYYYY555555!...............................................................
# ...............................................................JYY!:.:J5YYYYY555555555?...............................................................
# ...............................................................J555YYY5555555555555555?...............................................................
# ...............................................................~!!!!!!!!!!!Y5555555555?...............................................................
# .....................................................:^7??JJJJJ???????????JY5555555555?.^^^^^^^::.....................................................
# ....................................................~JY5YYYY55555555555555555555555555?.^~~~~~~~~:....................................................
# ...................................................~YYYYYYYYYYYYYYY5555555555555555555?.^~~~~~~~~~:...................................................
# ..................................................:JYYYYYYYYYYYYY555555555555555555555~.^~~~~~~~~~~:..................................................
# ..................................................~YYYYYYYYYYYY5555555555555555555YY7^.^~~~~~~~~~~~:..................................................
# ..................................................~5YYYYYYYYY55Y?!~~~~~~~~~~~~~~~^^::^~~~~~~~~~~~~~:..................................................
# ..................................................~5YYYYYY5555?^.:^^^^^^^^^^^^^^^^~~~~~~~~~~~~~~~~~:..................................................
# ..................................................:YYYYY55Y55J::^~~~^^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~:..................................................
# ...................................................75555Y5555?.^~^^^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^...................................................
# ....................................................755555555?.^~^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^....................................................
# .....................................................^?JYYYY5?.^~~~~~~~~~~~^^^^~~~~~~~~~~~~~~~^^:.....................................................
# .......................................................::^^^^:.^~~~~~~~~~~~::::::::::::...............................................................
# ...............................................................^~~~~~~~~~~~~~~~~~~~~~~^...............................................................
# ...............................................................^~~~~~~~~~~~~~~~~:::^~~^...............................................................
# ...............................................................^~~~~~~~~~~~~~~~^:..^~~^...............................................................
# ................................................................:^~~~~~~~~~~~~~~~~~~~^:...............................................................
# ..................................................................:::^^^^^^^^^^^^^::..................................................................
# ......................................................................................................................................................
# ......................................................:...................::..........................................................................
# ....................................................^~^^^^:.........:~:..:~:..........................................................................
# ....................................................^~...^~.^^...^^:^!^^.:~^^^^^..:^^^^^:.:~^^^^^.....................................................
# ....................................................^~^^^~^.:~^.^~:.:~:..:~^..:~:.~^...^~.:~^..:~:....................................................
# ....................................................^~::::...:~^~:..:~:..:~:..:~:.~^...^~.:~:..:~:....................................................
# ....................................................^^........^!:....^^^::~:..:~:.:^^^^^:.:~:..:~:....................................................
# ...........................................................::^~:.....................:................................................................
# ............................................................::........................................................................................
# ......................................................................................................................................................

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&&##BBGGPP55YY5PGPPPGPGGBB#&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&#BPPYYY555YJP5P5JYJYGGPBG5P???7???JY5PGB#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&BP5JJ55?5YYPG555YG5G5Y5PG#G5#5YP5YPY55YJPJYP5!7JPB#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&GYJYPPPY?YGBGPPGY?55JGPGYYP5GBG5#Y?YPPYPBGYYP7JBG?J55?!7JPB&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@&#P775JYGGPGGGP5BBBGY?YY5YPPGPYP5PBB5GJJJ5PYYYGJY57YB5?P557!!75J?YG#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@GJ?JY77P55P5JYGGP5GBGPYY5?GGP5BG5P5Y#B5PYJJY5Y7J5?PYJPG?55JPY??GYY5G5YYP#@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@&BJ^~!~!!JJPY!7YP7JP5Y5P5555J?GPPGPP5PJYGP5P5!?J5J?!JYG5YGP55J5PY?557YGGPGPJ?JP&@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@#J:  .::.~^7JJPJ~!PPPP5PY5PPPPJ!57YPY5PPYG5555J!5P5Y7~J5PJ!5BG55P55PGY5GBPPPYJJPY?5B@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@B7.    ..:::.~^^YJY?YJ7YPGP5GJ?5G5Y!JYJP5GYPP5YJ??5B5J77YPJ7?5BYJ55YYGPPP5PPP55YPB5YY?JP@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@G!       .:^^::.^~YYJ5JJ~:!5P5P5?!!5Y!JJJP5P55P55YYYGBG5Y?YPJ?YPP5?YY55GGPY55PPP5Y5GYJYYYYYG@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@&J.     . ..^!~^..:^J5!?Y?J!!JPYPPY7!?YJY55YYPPPPPPGGBB##BBPGBG5YYPYYYJYGGP5PP5PP5YYY5YYPPPBBYJG@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@P~...   .^^:.~?7~.:..~Y~.!?J?~7555P5Y5PPGGGGGGGGGBBBBBBB####&&&&&BGBP5YJ5GGG5PP5P55YY55YYGGGGBGG5Y#@@@@@@@@@@@@@
# @@@@@@@@@@@#!.....  .:::..~!~!^..^!?!  ^?5Y?75YPGBBBB####BBBBBB######&&&@@@@@@@&&#GP5PPG55GG5PY555PYY5YPYPGGG#B5P@@@@@@@@@@@@
# @@@@@@@@@@P^^^:.:.    .. .::^^^:.~7J7. .75GJ~YPGGBBBB###&#BGPPPPPP55555PGB##&&&@@@&#GGP55GPP55JY5PYJ5GGGPPG#BGBBPY&@@@@@@@@@@
# @@@@@@@@@Y^~~~~:..   .   .:^~^^~~7!7J:^^^5P5YPGGGGBBBBBGY7!!~~~~~~^^^^^~7?JYPGB#@@@&BBGPGG55PGJY55JJY5PGBPGBBGGGGPJB@@@@@@@@@
# @@@@@@@&77777!~:::.:::.::^7!!~::!?~!5!!7~J5JPGGGGGGGPY?!~^^^^^^^^^^^^^^^^~~!7?J5G&@@&BGGGP55PGJY55JJP55PGGGGGGGPPPP?P@@@@@@@@
# @@@@@@&!~7!~~~^^^::^~^^~^~~!!!^~?7~~5J!77?5YPGGGGP5J7!~~~^^^^^^^^^^^^^^^^^~~~!!7JG&&&#BGGGP5PPYY?YG55GGPPPPPPPPY5PPP?5@@@@@@@
# @@@@@&!~7!~^:::~^^^^^^~~!?!!!~~7?!~^YY!!!?YYPGGB5?7!~~~~^^^^^^^^^^^^^^^^^^^^~~~!!?P#&##BGGPY5BPJ75#G5PPP5PP55PP55P555?P@@@@@@
# @@@@&7^~^^^::~?~^^^~~~~!!77777?J?!!!?577!7J5GGGP!!~~~^^^^^^^^^^^^^~~~~~~~^^^^^~!77JG###GP5PY5GP555PGP555JYYJYYYJ??5YJ57G@@@@@
# @@@@7.^^^^^::J55?!!~~^~JYYY5555PJJYJJPJ??77Y5Y5?^^^^^^^^^^^^^~7?JJJ?77!!~~^^^^^!!7?PBGGGG55YY555555PJJ7~!7?7?JJ?7755?YY!#@@@@
# @@@5.:!!~~!!^?55JJYYYYYPPPPPP55P55P5YP5J?7?Y5JJ?^:^^^^^^^~~!?YYJ?7!!!!~~~~~~~~~~!77?77?YGY5YY5Y55P5Y7!!~~~~!777?J??5#YYJ?@@@@
# @@&^:^777JYJ77YYJYY5P55PPPPPGPP5PGPP55GYJ??JPYY?!7JJ?7!!~!7?????JY55YJ?7!~~~~~~~~!~~~~!!?JY5J5YJJ5YYJJ?!!!~^^~7???YBG?J?7P@@@
# @@5:^~77?J555J5JJJYPPP5PPPPPGP5555Y555GP5Y?75YJYJJJJJJJ7~~~!777J??J?7!~~~~~~~~~~~~~7?!~!~?55YYY77YY5JJ?!^~!!!77?7YB#Y!!7?7@@@
# @&^:^!777?JJJJY?7~!J55Y5PYPPB5JJ!J5555GGGPGPY57J!!?J55J7~^^~~~~~~~~^^^^^^^^^^^~~~~~!77!~~JGPJ7Y5Y5J55JY~~77?JY555PBGPBPJ?^P@@
# @B:::^^^~!!7?!^^~^~!7??55J5PPYYJ7?JY5JPPPP5Y?5?Y!?J?J?!~^^^^^^~~^^^^^^^^^^^^^^~~~~~!!~~~^?5YY?JJJ5?YGYJP?~!~~YYJYYYYJY5PPJ?@@
# @J:^^^:^^^^~^^!77??~^^^~~~~~~~^^^^^^^^7J^^^^~JJY?^~!~~^^^^^^^^^~!!~^^^^^^^^^^~~~~~~~!~~!?Y5YJ55?7YP5P?!PGJJJJY5BY??5G#GGGP?@@
# @?^^^^:::....:?JJJ?...................~?^...:J??7:^^^^~^^^~~!77!7?777!!~~~~~~~~~~~!!!77?BPG5YP577YYJ5J5PBYGBBGPGGGB##&###BY@@
# @J!~~^^:::::::~!!^^::::::.::.:.:......^?~....7J?7^^^~!!7J??JJJ??7!~!7??7!!~~~~~~~!!!!77755PYYP5JJYJ?YJPG#YPGGP5Y5PG5GPY5BGY&@
# @J!~!~~~^:::::..:~::::::::::::::::::::^YY::::7YJ?^~!!7777777!!~~~~~!7?J?!!!!~~~~!!!!!7!!7JY?YJ5YYJJJYJPG#5PBBGBBB##GGGY5PGJ5@
# @YJ7!~~!~^^^^:::^!:::::::::::::::::::::?5^::^~JYJ~~7?JJ7~~~!7??7?7?J55J7!!!!!!!!!77777!777J?5Y5J?JY?JJ7Y#JYGPPYJYY5PPGBBB#JJ@
# @J7!J~~^^^^^^^^^^~^:^^^^^^^^^::::::::::~Y!::::7YJ~~!7JJJ?JP5J??77?JJJ7!!7777!!!7777777!777!^~!777?Y?JJ?Y#GPGPG5555YYYYYYJJ!B@
# @5?Y?^^^^^^^^^^:^~:^^^^^^^^::^^::::^:^^^YJ::::!J57~7?77???J?7777777!!!!!!77777????77777?7~^^^^:^~~~!?J?7#YJYPGYPG55PBGPPGG!#@
# @G7P?:::^^:^^:^:~~:^:^::^^:^:::::::^^^:^7Y^:::^Y57!JP5?7!!~!7???77!!~~~!!7????J??????7?7~~~^~^^^^^^^^~~^PBGGGGY75Y~~75!:^^!@@
# @&75!:^^^^^^:^^^~~^^^:^:^^:^:::::::^^:::~J!::::J5Y5P5GP5J7~~~~~~~~~~~~~!7?JJJJJJJ?????7!~~^~~^^^^^^^^^^^^~?J5PP5YP5YYPGYJ~5@@
# @@5~^^^^^^^^~JJYJ?!~^^^^^^^::::::::^::::^??:::^YG?YPPGBGGGY~~~~!!!!!!7?JJYYYJYYJJJJ??7!~^^~~~^^^^^^^^^^^^^:^~7YY7?P~~!5PJ7&@@
# @@&^:::^^^^^~77!~^^^^:::::::::::::::::::^?Y^:^~JP775GGGPBBG!!???JJYYY55YYYYYYYYJJJ??77~~^^~~~^^^^^^^^^^^^^^^^^^!?YBYJ?JP^Y@@@
# @@@5.::::::::::::::::::::::::::::::::::::!J~^~.7Y!75GYG#BBB7!?GGBG5555YYYY555YYJ???!7!~~~~~!~~~^^^^^^^^^^^^^^^^^^~77Y5YY?&@@@
# @@@@!.:::::::::::::::::::::::::::::::::::~J7^::7J~75PPY#BGG?!75BBGPYJYYY555YYYJJ??!!~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^:^^~~~#@@@@
# @@@@#^.:::::::::::::::::::::::::::::::::::7?:::~7~755PPPBP57!7YGGG5PP5JY555YYJJJ?!!~!!~~^^~^^^^^^^^^^^^^^^^^^^^^^^^^^^~5@@@@@
# @@@@@B^:::::::::::::::::::::::::::::::::::7J~::^!~?G5PBGGPY?77?5BPPPBGJ?JY5YJJJ?!!~!!~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^:?@@@@@@
# @@@@@@G:::::::::::::::::::::::::::::::::::7Y7:.~?J5G5PGB5PG5?YJ?J555PG57?5YJ??7~~~~!!!!!!~~~~^^^~~~~~!~~~^^^^^^^^^^^:7@@@@@@@
# @@@@@@@G^.:::::::::::..:...:::::..:::::::.~J7::!?YPPG5GBPPGPJGG55555YGG?JPY77!^~~~!!!!~~^^^^^^^^^~~^~~~!!!~^^^~~~~^:J@@@@@@@@
# @@@@@@@@#!.::::::.........::::::.:::::::..^?J~^?7JPGBPPGGPG5!5BGBGPP5Y5?YGJ!~^^~~~~~~^^^^^^^^~^~~~~~~~~~~~!!!~~~~~^Y@@@@@@@@@
# @@@@@@@@@@J...:..........::::::::::..:::.:~?Y!^?!?5GGGPGG5BP!JPGG5#BG5Y??J7~~^^~~~^^^^^^^^^^~~~~~~~~~~~~~~~~!7!~^~G@@@@@@@@@@
# @@@@@@@@@@@P^.::::...::::::::::.......::::~?Y7!?!75BBGPPGBB57JGB5B&#BG55!^~~^^~~^^^^^^^^^^^~~~~~~~~~~~~~~~~~~!!~?&@@@@@@@@@@@
# @@@@@@@@@@@@&?:.:....:.......::::::::::::::~?7JY!7PGBGPPPPP57?GG5###BGBG~:^^^^^^^^^^^~~^^^~~~~~~~~~~~~~~~~~~~^!G@@@@@@@@@@@@@
# @@@@@@@@@@@@@@B!.......:..::::::::::.:::::^~~!5J!?PGPGPGGGPP7J5GPGB#GBBB!:^:^~^^~~~^^^^~~~~~~~~~~~~~~~~~~~~~~Y&@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@G!..:::::::::::::::::::^~!?77?5J7YPPGPGB#BPGJ7JPBGGBGBBG~:^!!~~~^^^^^^~~~~~~~~~~~~~~~!!!!~~J#@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@G!:::::::::::^^~~:::^~?JYJJJPY?YPPG55PGBPP555GGBBBGP#B~:!!!~^:^^^^~^~~~~~~~!~~!!!!!!~~!Y#@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@B?^::^^:::::^^~~!!?7JYYYY55JJYPGPP5GPP5PBBGGG##GBG#G~^!!^^^~~~~~~~~~~!!!!!!!!!!!!~75&@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@#5!::^^^^^~~7?JJYJJJY5Y5PYJ55P555GGPPPBGPGBGPB#GBG!~~~~~~^^~^~!777!!!!!!!!!~~!JB@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@#Y7!77???JJYYJYYYY5Y5555P5PPPPGPPGGPPPPP5PBGPGB?~!~^^~~!7777!~~~!!!!!!!!JP&@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@B5J7??JYYYYY5555P55P555GGGGGPPPGGGGPPGGGBB#B?!~!7777!!~~~~~~~!~~!7YG&@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&G5J?JJYJ55PP55PPPGGBGGGGGGGGGGGGGBBBGGB5!!~~~~~~~~~!!~~~!7JP#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&BP5JJJ5555PPPPGPPBGGGGGGPGGBBGBBBBB5^^^^^^^~~~~!7?5G#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&BBGYYY5P5555PGPPPPPGGPPPPGBBBG!:::^^!!?YPB#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@&&#BGPPPP5555555Y55555PP5Y5PGB#&@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
