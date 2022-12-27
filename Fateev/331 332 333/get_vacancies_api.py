import requests
import json
import csv
import datetime
from time import sleep
def request_vacancies(date_from : datetime, date_to : datetime, page : int):
    """ Возвращает запрос c https://api.hh.ru
        Args: 
            date_from(datetime): дата начала
            date_to(datetime): дата конца
            page(int): страница
        Returns:
            request: Ответ сервера
    """
    hour_from = str(date_from.hour).zfill(2)
    hour_to = str(date_to.hour).zfill(2)
    day_from = str(date_from.day).zfill(2)
    day_to = str(date_to.day).zfill(2)
    minute_from = str(date_from.minute).zfill(2)
    minute_to = str(date_to.minute).zfill(2)
    second_from = str(date_from.second).zfill(2)
    second_to = str(date_to.second).zfill(2)
    request = requests.get('https://api.hh.ru/vacancies', 
    params={'specialization': 1, 
            "per_page": 100,
            "page" : page,
            'date_from': f"2022-12-{day_from}T{hour_from}:{minute_from}:{second_from}",
            'date_to': f"2022-12-{day_to}T{hour_to}:{minute_to}:{second_to}"})
    return request

def form_vacancy(item):
    """ Возвращает вакансию в виде массива
        Args:
            item(dict): Вакансия
        Returns:
            list: Вакансия в обработанном виде
    """
    try:
        salary_from = item["salary"]["from"]
    except:
        salary_from = ""

    try:
        salary_to = item["salary"]["to"]
    except:
        salary_to = ""
        
    try:
        salary_currency = item["salary"]["currency"]
    except:
        salary_currency = ""  
    
    try:
        area_name = item["address"]["city"]
    except:
        area_name = "" 

    return [item["name"], salary_from, salary_to, salary_currency, area_name,item["published_at"]]

def input_datetime():
    """Получаем нужный день
        Returns:
            datetime: Нужный день
    """
    print("Press <enter> for default")
    year = 2022
    month = 12
    day = input("Введите день (default=22): ")
    day = 22 if day == "" else int(day)
    return datetime.datetime(year, month, day)

def get_day_range(date : datetime):
    """Получаем список нужных дат
        Args:
            date(datetime): Требуемый день
        Returns:
            [datetime, datetime]: Временной промежуток
    """
    day_range = []
    for hour in range(1,25):
        if hour == 24:
            day_range.append([datetime.datetime(date.year, date.month, date.day, 23, 0, 0),
                            datetime.datetime(date.year, date.month, date.day, 23, 59, 59)])
            continue
        day_range.append([datetime.datetime(date.year, date.month, date.day, hour - 1, 0, 0),
                        datetime.datetime(date.year, date.month, date.day, hour, 0, 0)])
    return day_range
    
def make_requests(day_range):
    """Возвращает все вакансии за определенный день
        Args:
            day_range(list): Список параметров для запроса
        Return:
            list: Все вакансии
    """
    items = []
    for request_params in day_range:
        for page in range(0, 20):
            print(f"Request with params: Datetimes: {request_params} Page: {page}")
            request = request_vacancies(*request_params, page)  
            if "captcha_url" in request.text:
                print("Пройдите капчу чтобы продолжить: ")
                print(json.loads(request.text)["errors"][0]["captcha_url"])
                input("Нажмите после ввода капчи")
            if request.status_code == 200:
                items += json.loads(request.text)["items"]
            else:
                print("Request rejected, retrying")
                request = request_vacancies(*request_params, page)
                if request.status_code == 200:
                    items += json.loads(request.text)["items"]
                else:
                    print(f"Request rejected with params: {request_params} {page}")
    return items

def write_vacancies(items):
    """Записывает все вакансии в файл
        Args:
            items(list): Список вакансий
    """
    if len(items) == 0:
        print("Нет данных")
        return
    myFile = open('vacancies_from_api.csv', 'w', encoding="UTF-8")
    writer = csv.writer(myFile, lineterminator='\n')
    writer.writerow(['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at'])
    for item in items:
        writer.writerow(form_vacancy(item))
    myFile.close()
 
date = input_datetime()
day_range = get_day_range(date)
items = make_requests(day_range)
write_vacancies(items)