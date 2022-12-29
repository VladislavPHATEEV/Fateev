import itertools
import concurrent.futures as pool
from Vacancy_class import Vacancy
from multiprocessing import Pool
import csv
import pandas as pd
import numpy as np
import requests
from xml.etree import ElementTree
import sqlite3 as sl


class DataSet:
    """
    DataSet - класс, который хранит все данные из CSV файлов в виде словарей
    Атрибуты (все атрибуты имеют сеттеры)
    ------------------------------------------------------------------------
    __vacancies_count_by_year: pandas.Dataframe
        Количество вакансий по годам
    __sum_salaries_by_year: {int: float}
        Сумма всех зарплат по годам
    __current_count_by_year: {int: int}
        Количество факансий для интересующей нас профессии по годам
    __current_sum_salary_by_year: {int: float}
        Сумма всех зарплат для интересующей нас професси по годам
    __vacancies_count_by_town: pandas.Dataframe
        Количество вакансий по городам
    __vacancies_count: int (default=0)
        Общее число вакансий
    __current: str
        Название интересующей нас профессии
    __salaries_by_year: pandas.Dataframe
        Зарплаты по годам
    __current_salaries_by_year: pandas.Dataframe
        Зарплаты по годам для интересующей нас профессии
    __salaries_by_town: pandas.Dataframe
        Зарплаты по городам
    __vacancies_rate_by_town: pandas.Dataframe
        Доля вакансий в каждом городе
    __available_currencies: [str]
        Вакансии с частотностью более 5000
    __currencies_data: pandas.DataFrame
        Данные о курсах валют за все время
    __data: pandas.DataFrame
        Данные о вакансиях из CSV файла
    __region: str
        Название интересующего нас региона
    __salaries_by_year_for_town: {str: int}
        Словарь сопоставляющий средюю зарплату для интересующией нас профессии, интересующего нас региона каждому году
    __count_by_year_for_town: {str: int}
        Словарь сопоставляющий количество вакансий для интересующией
        нас профессии, интересующего нас региона каждому году
    """
    def __init__(self, profession_name: str):
        """
        Инициализирует объект
        :param profession_name: str
            задает название искомой профессии
        :param region_name: str
            задает название скомого региона
        :return: void
        """
        self.__vacancies_count_by_year = {}
        self.__sum_salaries_by_year = {}
        self.__current_count_by_year = {}
        self.__current_sum_salary_by_year = {}
        self.__vacancies_count_by_town = {}
        self.__sum_salaries_by_town = {}

        self.__vacancies_count = 0
        self.__current = profession_name

        self.__salaries_by_year = {}
        self.__current_salaries_by_year = {}
        self.__salaries_by_town = {}
        self.__vacancies_rate_by_town = {}
        self.__salaries_by_year_for_town = {}
        self.__count_by_year_for_town = {}

        self.__available_currencies = None
        self.__currencies_data = None
        self.__line_data = None

    @property
    def vacancies_count(self):
        return self.__vacancies_count

    @property
    def salaries_by_year(self):
        return self.__salaries_by_year

    @property
    def vacancies_count_by_year(self):
        return self.__vacancies_count_by_year

    @property
    def current_salaries_by_year(self):
        return self.__current_salaries_by_year

    @property
    def current_count_by_year(self):
        return self.__current_count_by_year

    @property
    def salaries_by_town(self):
        return self.__salaries_by_town

    @property
    def vacancies_rate_by_town(self):
        return self.__vacancies_rate_by_town

    @property
    def available_currencies(self):
        return self.__available_currencies

    @property
    def current(self):
        return self.__current

    @property
    def salaries_by_year_for_town(self):
        return self.__salaries_by_year_for_town
    @property
    def count_by_year_for_town(self):
        return self.__count_by_year_for_town

    def load_data_from_hh(self):
        """
        Загружает информацию о вакансиях с сайта hh.ru и сохраняет их в CSV файл
        :return: void
        """
        df = pd.DataFrame(columns=['name', 'salary_from', 'salary_to', 'salary_currency', 'area_name', 'published_at'])
        for hour in range(0, 24, 6):
            url = f'https://api.hh.ru/vacancies?specialization=1&date_from=2022-12-01T{("0" + str(hour))[-2:]}:00:00' \
                  f'&date_to=2022-12-' \
                  f'{("0" + str(1 + ((hour + 6) // 24)))[-2:]}T{("0" + str((hour + 6) % 24))[-2:]}:00:00'
            response = requests.get(url)
            if response.status_code != 200:
                print('Error')
                response = requests.get(url)
            result = response.json()
            for page_num in range(result['pages']):
                url = url + f'&page={page_num}'
                page_response = requests.get(url)
                if page_response.status_code != 200:
                    print('Error')
                    page_response = requests.get(url)
                for vacancy in page_response.json()['items']:
                    df.loc[len(df.index)] = self.__parse_json(vacancy)
        df.to_csv('hh_unloading.csv')

    def __parse_json(self, json) -> [str]:
        """
        Метод отбирает информацию из json формата и переводит в список значений
        :param json: {}
            Вакансия в виде словаря, json формате
        :return: [str]
            Все необходимые для вакансии данные
        """
        salary_from = None
        salary_to = None
        salary_currency = None
        area_name = None
        if json['salary'] is not None:
            salary_from = json['salary']['from']
            salary_to = json['salary']['to']
            salary_currency = json['salary']['currency']
        if json['area'] is not None:
            area_name = json['area']['name']

        return [json['name'], str(salary_from), str(salary_to), salary_currency, area_name, json['published_at']]


    def currency_frequency_reader(self, file_name: str) -> (str, str):
        """
        Считывает CSV файл, а также берет всю нужную информацию
        (крайние даты вакансий, валюты с нужной частотностью, вакансии с допустимыми валютами)
        :param file_name: str
            Название CSV файла
        :return: (str, str)
            Кортеж состоящий из крайних дат
        """
        oldest_date = None
        youngest_date = None
        currency_frequency = {}
        data = pd.read_csv(file_name)
        oldest_date = max(data['published_at'])
        youngest_date = min(data['published_at'])
        currency_frequency = data['salary_currency'].value_counts()
        self.__available_currencies = list(currency_frequency[currency_frequency > 5000].keys())
        self.__line_data = data[data['salary_currency'].isin(self.__available_currencies)]

        return (oldest_date, youngest_date)

    def generate_currency(self, oldest_date: str, youngest_date: str):
        """
        Генерирует dataframe с курсами всех валют за указанный период, а также сохраняет полученный датафрейм в БД
        в формате sqlite
        :param oldest_date: str
            Дата начала периода
        :param youngest_date: str
            Дата окончания периода
        :return: Void
        """
        first_year = int(oldest_date[0:4])
        first_month = int(oldest_date[5:7])
        last_year = int(youngest_date[0:4])
        last_month = int(youngest_date[5:7])
        df = pd.DataFrame(columns=['date'] + self.__available_currencies)
        for year in range(first_year, last_year + 1):
            for month in range(1, 13):
                if (year == first_year and month < first_month) or (year == last_year and month > last_month):
                    continue
                row = self.__get_row(month, year)
                if row is None:
                    continue
                df.loc[len(df.index)] = row
        self.__currencies_data = df

        con = sl.connect('bd.sqlite')
        df.to_sql(name='currency', con=con, if_exists='replace')

    def __get_row(self, month: str, year: str):
        """
        Возвращает список с курсами валют за указанный отрезок времени
        :param month: str
            Интересующий месяц
        :param year: str
            Интересующий год
        :return: [str/None]/None
            Список с курсами валют или None если информация недоступна
        """
        try:
            format_month = ('0' + str(month))[-2:]
            url = f'http://www.cbr.ru/scripts/XML_daily.asp?date_req=02/{format_month}/{year}'
            res = requests.get(url)
            tree = ElementTree.fromstring(res.content)
            row = [f'{year}-{format_month}']
            for val in self.__available_currencies:
                if val == "RUR":
                    row.append(1)
                    continue
                founded = False
                for valute in tree:
                    if valute[1].text == val:
                        row.append(round(float(valute[4].text.replace(',', '.'))
                                         /float(valute[2].text.replace(',', '.')), 6))
                        founded = True
                        break
                if not founded:
                    row.append(None)
            return row
        except Exception:
            return None

    def get_vacancies_data(self):
        """
        Фильтрует все данные из line_data, загружает все данные в БД и вычисляет поле 'salary'
        :return: Void
        """
        self.__line_data['date'] = self.__line_data["published_at"].str[0:4] + '-'\
                                   + self.__line_data["published_at"].str[5:7]

        con = sl.connect('bd.sqlite')
        self.__line_data.to_sql(name='raw_vacancies', con=con, if_exists='replace')

        cur = con.cursor()

        cur.execute(f"""ALTER TABLE raw_vacancies ADD rate DECIMAL(10, 4)""")
        for currency in self.__available_currencies:
            cur.execute(f"""UPDATE raw_vacancies
                        SET rate = (SELECT {currency} from currency where currency.date = raw_vacancies.date)
                        where salary_currency = '{currency}'
                        """)

        cur.execute(f"""ALTER TABLE raw_vacancies ADD salary MONEY""")
        cur.execute(f"""UPDATE raw_vacancies
                        SET salary = salary_from * rate
                        where salary_from is not NULL and salary_to is NULL
                    """)
        cur.execute(f"""UPDATE raw_vacancies
                        SET salary = salary_to * rate
                        where salary_from is NULL and salary_to is not NULL
                    """)
        cur.execute(f"""UPDATE raw_vacancies
                                SET salary = (salary_to + salary_from) / 2 * rate
                                where salary_from is not NULL and salary_to is not NULL
                            """)
        cur.execute("""DELETE from raw_vacancies
                        where salary is Null
                     """)
        cur.execute("""CREATE TABLE IF NOT EXISTS vacancies(
                        name varchar(100),
                        area_name varchar(50),
                        published_at datetime,
                        salary money)
                    """)
        cur.execute("""DELETE FROM vacancies""")
        cur.execute("""INSERT INTO vacancies SELECT name, area_name, published_at, salary 
                        from raw_vacancies
                    """)
        cur.execute("""DROP TABLE raw_vacancies""")
        con.commit()
        con.close()

    def fill_dataframes_by_sql(self):
        """
        Заполняет все dataframe-ы со статистикой используя SQL-запросы
        :return:
        """

        con = sl.connect('bd.sqlite')

        # strftime не работает
        self.__salaries_by_year = pd.read_sql("""SELECT SUBSTR(published_at, 1, 4) as 'Год', 
                                                        ROUND(AVG(salary), 2) as 'Средняя з\п'
                                                    from vacancies
                                                    group by SUBSTR(published_at, 1, 4)      
                                              """, con)
        self.__vacancies_count_by_year = pd.read_sql("""SELECT SUBSTR(published_at, 1, 4) as 'Год',
                                                                COUNT(*) as 'Кол-во вакансий'
                                                            from vacancies
                                                            group by SUBSTR(published_at, 1, 4)
                                                      """, con)
        self.__current_salaries_by_year = pd.read_sql(f"""SELECT SUBSTR(published_at, 1, 4) as 'Год',
                                                            ROUND(AVG(salary), 2) as 'Средняя з\п {self.__current}'
                                                            from vacancies 
                                                            where lower(name) LIKE '%{self.__current.lower()}%'
                                                            group by SUBSTR(published_at, 1, 4)      
                                                       """, con)
        self.__current_count_by_year = pd.read_sql(f"""SELECT SUBSTR(published_at, 1, 4) as 'Год',
                                                            COUNT(*) as 'Кол-во вакансий {self.__current}'
                                                            from vacancies 
                                                            where lower(name) LIKE '%{self.__current.lower()}%'
                                                            group by SUBSTR(published_at, 1, 4)      
                                                       """, con)
        self.__salaries_by_town = pd.read_sql("""SELECT area_name as 'Город',  ROUND(AVG(salary), 2) as 'Средняя з\п'
                                                 from vacancies 
                                                 group by area_name
                                                 having COUNT(*) >= (SELECT COUNT(*) FROM vacancies) / 100
                                                 ORDER BY ROUND(AVG(salary), 2) DESC 
                                                 LIMIT 10
                                              """, con)
        self.__vacancies_rate_by_town = pd.read_sql("""SELECT area_name as 'Город',
                                                        100 * COUNT(*)/(select COUNT(*) from vacancies)  as 'Доля(%)'
                                                        from vacancies
                                                        group by area_name
                                                        having COUNT(*) >= (SELECT COUNT(*) FROM vacancies) / 100
                                                        ORDER BY COUNT(*) DESC 
                                                        LIMIT 10
                                                    """, con)
        con.close()

    @staticmethod
    def csv_reader(file_name: str) -> []:
        """
        Считывает данные из CSV файла, преоразует их в объекты Vacancy и возвращает список этих объектов
        :param file_name: str
            Имя файла с данными
        :return: [Vacancy]
            Список объектов Vacancy
        """
        data = []
        with open(file_name, "r", encoding="UTF-8-sig") as file:
            file_reader = csv.DictReader(file, delimiter=",")
            headlines_list = list(file_reader.fieldnames)
            for line in file_reader:
                vacancy = DataSet.parse_line_to_vacancy(line, headlines_list)
                if vacancy is not None:
                    data.append(vacancy)
        return data

    @staticmethod
    def csv_split_generator(file_name: str, folder_name: str):
        """
        Генерирует разделенный по годам CSV файлы с даннымии из исходного CSV файла
        :param file_name: str
            Название искодного CSV файла
        :param folder_name: str
            Название название папки куда сохраняются сгенерированные файлы
        :return: [str]
            Названия сгенерированых файлов
        """
        lines_by_year = {}
        with open(file_name, "r", encoding="UTF-8-sig") as file:
            file_reader = csv.DictReader(file, delimiter=",")
            headlines_list = list(file_reader.fieldnames)
            for line in file_reader:
                key = line["published_at"][0:4]
                if key not in lines_by_year.keys():
                    lines_by_year[key] = []
                lines_by_year[key].append(line.values())
        file_names = []
        for key in lines_by_year.keys():
            new_file_name = folder_name + "/" + key + ".csv"
            file_names.append(new_file_name)
            with open(new_file_name, 'w', newline='', encoding="UTF8") as new_file:
                file_writer = csv.writer(new_file, delimiter=",")
                file_writer.writerow(headlines_list)
                file_writer.writerows(lines_by_year[key])
        return file_names

    def multi_proc_fill_dictionaries(self, file_names: [str]):
        """
        Заполняет словари данными используя multiprocessing
        :param file_names: [str]
            Названия файлов, из которых нужно брать данные
        :return: void
        """
        args_multiproc = zip(file_names, itertools.repeat(self.__current))
        with Pool() as p:
            for file_name, year_statistics in zip(file_names, p.map(DataSet.get_statistics_for_year, args_multiproc)):
                key = file_name.split('/')[1][0:4]
                self.__vacancies_count += year_statistics["vacancies_count"]
                self.__vacancies_count_by_year[key] = year_statistics["vacancies_count"]
                self.__current_count_by_year[key] = year_statistics["current_count"]
                self.__salaries_by_year[key] = year_statistics["salary"]
                self.__current_salaries_by_year[key] = year_statistics["current_salary"]
                for item in year_statistics["vacancies_count_by_town"].items():
                    self.__vacancies_count_by_town[item[0]] = self.__vacancies_count_by_town.setdefault(item[0], 0) \
                                                              + item[1]
                for item in year_statistics["salaries_sum_by_town"].items():
                    self.__sum_salaries_by_town[item[0]] = self.__sum_salaries_by_town.setdefault(item[0], 0) + item[1]
        for key in self.__sum_salaries_by_town.keys():
            if int(self.__vacancies_count_by_town[key] / self.__vacancies_count * 100) >= 1:
                self.__salaries_by_town[key] = int(self.__sum_salaries_by_town[key] /
                                                   self.__vacancies_count_by_town[key])
        for key in self.__salaries_by_town:
            self.__vacancies_rate_by_town[key] = round(self.__vacancies_count_by_town[key] / self.__vacancies_count, 4)

    def concurrent_futures_fill_dictionaries(self, file_names: [str]):
        """
        Заполняет словари данными используя concurrent.futures
        :param file_names: [str]
            Названия файлов, из которых нужно брать данные
        :return: void
        """
        args_multiproc = zip(file_names, itertools.repeat(self.__current))
        with pool.ProcessPoolExecutor() as ex:
            for file_name, year_statistics in zip(file_names, ex.map(DataSet.get_statistics_for_year, args_multiproc)):
                key = file_name.split('/')[1][0:4]
                self.__vacancies_count += year_statistics["vacancies_count"]
                self.__vacancies_count_by_year[key] = year_statistics["vacancies_count"]
                self.__current_count_by_year[key] = year_statistics["current_count"]
                self.__salaries_by_year[key] = year_statistics["salary"]
                self.__current_salaries_by_year[key] = year_statistics["current_salary"]
                for item in year_statistics["vacancies_count_by_town"].items():
                    self.__vacancies_count_by_town[item[0]] = self.__vacancies_count_by_town.setdefault(item[0], 0) \
                                                              + item[1]
                for item in year_statistics["salaries_sum_by_town"].items():
                    self.__sum_salaries_by_town[item[0]] = self.__sum_salaries_by_town.setdefault(item[0], 0) + item[1]
        for key in self.__sum_salaries_by_town.keys():
            if int(self.__vacancies_count_by_town[key] / self.__vacancies_count * 100) >= 1:
                self.__salaries_by_town[key] = int(self.__sum_salaries_by_town[key] /
                                                   self.__vacancies_count_by_town[key])
        for key in self.__salaries_by_town:
            self.__vacancies_rate_by_town[key] = round(self.__vacancies_count_by_town[key] / self.__vacancies_count, 4)

    def get_statistics_for_year(self, tuple_args):
        """
        Возвращает статистику расчитанную за 1 год
        :param tuple_args: ([str], str)
            Аргументы функции, содержат название файла с данными и наазвание интересующей нас профессии
        :return: {}
            Статистика за 1 год
        """
        year = tuple_args[0]
        current_name = tuple_args[1]
        year_statistics = {}
        year_statistics["vacancies_count_by_town"] = {}
        year_statistics["salaries_sum_by_town"] = {}
        vacancies_salaries_sum = 0
        current_salaries_sum = 0

        data = self.__data_by_year[year]
        data['salary'] = [self.get_salary(row) for row in self.__line_data.itertuples()]

        #with open(full_file_name, "r", encoding="UTF-8-sig") as file:
        #    file_reader = csv.DictReader(file, delimiter=",")
        #    headlines_list = list(file_reader.fieldnames)
        #    for line in file_reader:
        #        vacancy = DataSet.parse_line_to_vacancy(line, headlines_list)
        #        if vacancy is not None:
        #            year_statistics["vacancies_count"] = year_statistics.setdefault("vacancies_count", 0) + 1
        #            vacancies_salaries_sum += vacancy.average_ru_salary
        #            year_statistics["vacancies_count_by_town"][vacancy.area_name] \
        #                = year_statistics["vacancies_count_by_town"].setdefault(vacancy.area_name, 0) + 1
        #            year_statistics["salaries_sum_by_town"][vacancy.area_name] \
        #                = year_statistics["salaries_sum_by_town"].setdefault(vacancy.area_name, 0) \
        #                  + vacancy.average_ru_salary
        #            if current_name in vacancy.name:
        #                year_statistics["current_count"] = year_statistics.setdefault("current_count", 0) + 1
        #                current_salaries_sum += vacancy.average_ru_salary
        #year_statistics["salary"] = int(vacancies_salaries_sum / year_statistics["vacancies_count"])
        #year_statistics["current_salary"] = int(current_salaries_sum / year_statistics["current_count"])
        #return year_statistics

    @staticmethod
    def parse_line_to_vacancy(line, headlines_list):
        """
        Преобразует строку из CSV файла в объект Vacancy
        :param line: {}
            Строка из CSV файла
        :param headlines_list: [str]
            Список заголовков столбцов в CSV файле
        :return: Vacancy/None
            Объект Vacancy, при удачном преобразовании, иначе None
        """
        vacancy_dict = {}
        for headline in headlines_list:
            vacancy_dict[headline] = line[headline]
        if "" not in vacancy_dict.values():
            return Vacancy(vacancy_dict)
        return None

    def fill_dictionaries(self, data: [Vacancy]):
        """
        Заполняет словари с данными
        :param data: [Vacancy]
            Данные в виде списка с объектами Vacancy
        :param current_vacancy_name: str
            Название интересующей нам профессии
        :return: void
        """
        for vacancy in data:
            key = int(vacancy.year)
            self.__vacancies_count_by_year[key] = self.__vacancies_count_by_year.setdefault(key, 0) + 1
            self.__sum_salaries_by_year[key] = self.__sum_salaries_by_year.setdefault(key, 0) \
                                               + vacancy.average_ru_salary
            self.__vacancies_count_by_town[vacancy.area_name] = \
                self.__vacancies_count_by_town.setdefault(vacancy.area_name, 0) + 1
            self.__sum_salaries_by_town[vacancy.area_name] = \
                self.__sum_salaries_by_town.setdefault(vacancy.area_name, 0) + vacancy.average_ru_salary
            if self.__current in vacancy.name:
                self.__current_count_by_year[key] = self.__current_count_by_year.setdefault(key, 0) + 1
                self.__current_sum_salary_by_year[key] = \
                    self.__current_sum_salary_by_year.setdefault(key, 0) + vacancy.average_ru_salary

    def calculate_vacancies_count(self):
        """
        Считает общее количество вакансий в данных
        :return: void
        """
        self.__vacancies_count = sum(self.__vacancies_count_by_town.values())

    def fill_statistics_dictionaries(self):
        """
        Заполняет словари со статистикой используя словари с данными
        :return: void
        """
        for key in self.__sum_salaries_by_year.keys():
            self.__salaries_by_year[key] = int(self.__sum_salaries_by_year[key] / (self.__vacancies_count_by_year[key]))
            if key in self.__current_count_by_year:
                self.__current_salaries_by_year[key] = int(self.__current_sum_salary_by_year[key]
                                                           / self.__current_count_by_year[key])
            else:
                self.__current_salaries_by_year[key] = 0
                self.__current_count_by_year[key] = 0
        for key in self.__sum_salaries_by_town.keys():
            if int(self.__vacancies_count_by_town[key] / self.__vacancies_count * 100) >= 1:
                self.__salaries_by_town[key] = int(self.__sum_salaries_by_town[key] /
                                                   self.__vacancies_count_by_town[key])
        for key in self.__salaries_by_town:
            self.__vacancies_rate_by_town[key] = round(self.__vacancies_count_by_town[key] / self.__vacancies_count, 4)

    def print_statistics_dictionaries(self):
        """
        Выводит все словари со статистикой
        :return: void
        """
        sorted_salaries_by_town = dict(
            sorted(self.salaries_by_town.items(), key=lambda item: item[1], reverse=True)[0:10])
        sorted_vacancies_by_rate = dict(sorted(self.vacancies_rate_by_town.items(),
                                               key=lambda item: item[1], reverse=True)[0:10])
        print("Динамика уровня зарплат по годам: ", self.__salaries_by_year)
        print("Динамика количества вакансий по годам: ", self.__vacancies_count_by_year)
        print("Динамика уровня зарплат по годам для выбранной профессии: ", self.__current_salaries_by_year)
        print("Динамика количества вакансий по годам для выбранной профессии: ", self.__current_count_by_year)
        print("Уровень зарплат по городам (в порядке убывания): ", sorted_salaries_by_town)
        print("Доля вакансий по городам (в порядке убывания): ", sorted_vacancies_by_rate)

    def print_statistics_dataframes(self):
        """
        Выводит всю статистику в консоль
        :return: Void
        """
        print("Динамика уровня зарплат по годам: \n", self.__salaries_by_year)
        print("Динамика количества вакансий по годам: \n", self.__vacancies_count_by_year)
        print("Динамика уровня зарплат по годам для выбранной профессии: \n", self.__current_salaries_by_year)
        print("Динамика количества вакансий по годам для выбранной профессии: \n", self.__current_count_by_year)
        print("Уровень зарплат по городам (в порядке убывания): \n", self.__salaries_by_town)
        print("Доля вакансий по городам (в порядке убывания): \n", self.__vacancies_rate_by_town)
