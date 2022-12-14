import csv
import re
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from os import path
from prettytable import PrettyTable
from jinja2 import Environment, FileSystemLoader
import pdfkit
import doctest
import datetime

experienceToRus = {
    "noExperience": "Нет опыта",
    "between1And3": "От 1 года до 3 лет",
    "between3And6": "От 3 до 6 лет",
    "moreThan6": "Более 6 лет"
}

experienceToPoints = {
    "noExperience": 0,
    "between1And3": 1,
    "between3And6": 2,
    "moreThan6": 3
}

grossToRus = {
    "true": "Без вычета налогов",
    "false": "С вычетом налогов",
    "True": "Без вычета налогов",
    "False": "С вычетом налогов",
}

currencyToRus = {
    "AZN": "Манаты",
    "BYR": "Белорусские рубли",
    "EUR": "Евро",
    "GEL": "Грузинский лари",
    "KGS": "Киргизский сом",
    "KZT": "Тенге",
    "RUR": "Рубли",
    "UAH": "Гривны",
    "USD": "Доллары",
    "UZS": "Узбекский сум"
}

currency_to_rub = {
    "AZN": 35.68,
    "BYR": 23.91,
    "EUR": 59.90,
    "GEL": 21.74,
    "KGS": 0.76,
    "KZT": 0.13,
    "RUR": 1,
    "UAH": 1.64,
    "USD": 60.66,
    "UZS": 0.0055
}

fieldToRus = {
    "name": "Название",
    "description": "Описание",
    "key_skills": "Навыки",
    "experience_id": "Опыт работы",
    "premium": "Премиум-вакансия",
    "employer_name": "Компания",
    "salary": "Оклад",
    "salary_gross": "Оклад указан до вычета налогов",
    "salary_currency": "Идентификатор валюты оклада",
    "area_name": "Название региона",
    "published_at": "Дата публикации вакансии"
}

def get_key(d, value):
    """Получает первый ключ по значению

    Args:
        d (dict): Словарь для поиска ключа
        value(object): Значение по которому искать
    >>> x = {1: 2, "3": "x", 4: "2"}
    >>> get_key(x, 2)
    1
    >>> x = {1: 2, "3": "x", 4: "2"}
    >>> get_key(x, "x")
    '3'
    >>> x = {1: 2, "3": "x", 4: "2"}
    >>> get_key(x, "2")
    4
    """
    for k, v in d.items():
        if v == value:
            return k

class Salary:
    """Класс для представления зарплаты.

    Attributes:
        salary_from (int): Нижняя граница вилки оклада
        salary_to (int): Верхняя граница вилки оклада
        salary_gross (str): Наличие включенного налога
        salary_currency (str): Валюта оклада
    """

    def __init__(self, salary_from: str, salary_to: str, salary_gross: str, salary_currency: str):
        """Инициализирует объект Salary, выполняет конвертацию для полей.

            Args:
                salary_from (str): Нижняя граница вилки оклада
                salary_to (str): Верхняя граница вилки оклада
                salary_gross (str): Наличие включенного налога
                salary_currency (str): Валюта оклада

        >>> Salary("100","2000", "true", "RUR").salary_to
        2000
        >>> Salary(100.0,"2000", "true", "RUR").salary_from
        100
        >>> Salary("100","2000", "true", "RUR").salary_currency
        'RUR'
        >>> type(Salary("100","2000", "true", "RUR"))
        <class '__main__.Salary'>
        """
        self.salary_from = int(float(salary_from))
        self.salary_to = int(float(salary_to))
        self.salary_gross = salary_gross
        self.salary_currency = salary_currency

    def to_string(self):
        """
            Переводит объект Salary в строчный вид для правильного вывода в таблицу.

            Returns:
                str: '{salary_from} - {salary_to} ({salary_currency}) ({salary_gross})'

            >>> Salary("100", "2000", "true", "RUR").to_string()
            '100 - 2 000 (Рубли) (Без вычета налогов)'
            >>> Salary(100.0, 200, "false", "KZT").to_string()
            '100 - 200 (Тенге) (С вычетом налогов)'
            >>> Salary(100.0, 2000000000, "false", "EUR").to_string()
            '100 - 2 000 000 000 (Евро) (С вычетом налогов)'
        """
        salary_string = '{0:,}'.format(self.salary_from).replace(',', ' ') + " - "
        salary_string += '{0:,}'.format(self.salary_to).replace(',', ' ') + " (" + currencyToRus[
            self.salary_currency] + ") ("
        salary_string += grossToRus[self.salary_gross] + ")"
        return salary_string


class Vacancy:
    """Класс для представления вакансии.

    Attributes:
        name (str): Название вакансии
        description (str): Описание вакансии
        key_skills (list): Ключевые навыки
        experience_id (str): Требуемый опыт работы
        premium (str): Премиум-вакансия
        employer_name (str): Название работодателя
        salary (Salary): Зарплата
        area_name (str): Город работы
        published_at (str): Дата публикации вакансии
    """

    def __init__(self, name: str, description: str, key_skills: str, experience_id: str,
                 premium: str, employer_name: str, salary: Salary, area_name: str, published_at: str):
        """Инициализирует объект Vacancy, выполняет конвертацию дляполей.

            Args:
                name (str): Название вакансии
                description (str): Описание вакансии
                key_skills (str): Ключевые навыки
                experience_id (str): Требуемый опыт работы
                premium (str): Премиум-вакансия
                employer_name (str): Название работодателя
                salary (Salary): Зарплата
                area_name (str): Город работы
                published_at (str): Дата публикации вакансии

        >>> Vacancy("x", "y", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").key_skills
        ['z']
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").description
        'xyz'
        """
        self.name = name
        self.description = TextEditor.beautifulStr(description)
        self.key_skills = list(key_skills.split("\n"))
        self.experience_id = experience_id
        self.premium = premium
        self.employer_name = employer_name
        self.salary = salary
        self.area_name = area_name
        self.published_at = published_at

    def date_to_string(self):
        """Переводит аттрибут published_at класса Vacancy в формат dd.mm.yyyy

            Returns:
                str: Дата в формате dd.mm.yyyy

        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").date_to_string()
        '03.12.2007'
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2012-10-03T17:12:09+0300").date_to_string()
        '03.10.2012'
        """
        splitted_date = self.published_at.split("T")[0].split("-")
        date_string = splitted_date[2] + "." + splitted_date[1] + "." + splitted_date[0]
        return date_string

    def date_get_year(self):
        """Получить год публикации вакансии

            Returns:
                int: Год публикации вакансии

        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").date_get_year()
        2007
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2012-10-03T17:12:09+0300").date_get_year()
        2012
        """
        return int(self.date_to_string().split(".")[-1])

    def premium_to_string(self):
        """Переводит аттрибут premium класса Vacancy в строку на Русском языке

            Returns:
                str: Значение premium перведенное на Русский язык

        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").premium_to_string()
        'Да'
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "False", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").premium_to_string()
        'Нет'
        """
        return self.premium.lower().replace("true", "Да").replace("false", "Нет")

    def description_to_string(self):
        """Обрезает description класса Vacancy до 100 символов

            Returns:
                str: Значение description после обрезки

        >>> Vacancy("x", 'x'*1000, 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").description_to_string()
        'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...'
        >>> Vacancy("x", 'xxxx', 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").description_to_string()
        'xxxx'
        """

        return TextEditor.line_trim(self.description)

    def skills_to_string(self):
        """Переводит key_skills класса Vacancy в str склеивая их

            Returns:
                str: Значение key_skills склееной в строку
        """
        return TextEditor.line_trim("\n".join(self.key_skills))

    def experience_to_string(self):
        """Переводит аттрибут experience_id класса Vacancy в строку на Русском языке

            Returns:
                str: Значение experience_id перведенное на Русский язык

        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "noExperience", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").experience_to_string()
        'Нет опыта'
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "between1And3", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").experience_to_string()
        'От 1 года до 3 лет'
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "between3And6", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").experience_to_string()
        'От 3 до 6 лет'
        """
        return experienceToRus[self.experience_id]

    def to_list(self):
        """Возвращает вакансию в виде list для добавление в таблицу

            Returns:
                list: Массив со всеми нужными аттрибутами вакансии
        >>> Vacancy("x", "<br><b>x</b>yz</br>", 'z', "between3And6", "true", "x", Salary("100", "2000", "true", "RUR"), "x", "2007-12-03T17:40:09+0300").to_list()
        ['x', 'xyz', 'z', 'От 3 до 6 лет', 'Да', 'x', '100 - 2 000 (Рубли) (Без вычета налогов)', 'x', '03.12.2007']
        """
        return [TextEditor.beautifulStr(self.name), self.description_to_string(), self.skills_to_string(),
                self.experience_to_string(), self.premium_to_string(),
                self.employer_name, self.salary.to_string(), self.area_name, self.date_to_string()]


class TextEditor:
    """Класс для работы с текстом и его форматирования
    """

    def beautifulStr(string: str):
        """Возвращает str из которой удалены все HTML теги

            Args:
                string (str): Строка для очистки от тегов

            Returns:
                str: Текст с удаленными HTML тегами
        """
        return ' '.join(re.sub(r"<[^>]+>", '', string).split()).replace("  ", " ").replace(" ", " ")

    def line_trim(string: str):
        """Обрезает str до 100 символов

            Args:
                string (str): Строка для обрезки

            Returns:
                str: Текст обрезанный до 100 символов
        """
        if len(string) > 100:
            string = string[:100] + "..."
        return string

    def formatter(field: str, string: str):
        """Переводит str на Русский язык в зависимости от выбранного поля

            Args:
                field (str): Название поля для перевода на Русский язык
                string (str): Строка для перевода на Русский язык

            Returns:
                str: Строка переведенная на Русский язык
        """
        if (field == "premium"):
            string = string.replace("FALSE", "Нет").replace("TRUE", "Да").replace("False", "Нет").replace("True", "Да")
        elif (field == "salary_gross"):
            string = grossToRus[string.lower()]
        elif (field == "salary_currency"):
            string = currencyToRus[string]
        elif (field == "experience_id"):
            string = experienceToRus[string]
        return [fieldToRus[field], string]


class InputConect:
    """Класс для проверки правильности введеных данных.

    Attributes:
        filter_parameter (list): Параметр фильтрации
        sort_field (list): Параметр сортировки
        range (list): Диапазон вывода
        columns (list): Требуемые столбцы
    """

    def __init__(self, filter_parameter_input: str, sort_field_input: str, reverse_input: str, range_input: str,
                 columns_input: str):
        """Инициализирует объект InputConect, выполняет проверку полей, конвертирует их.

        Attributes:
            filter_parameter_input (str): Параметр фильтрации
            sort_field_input (str): Параметр сортировки
            reverse_input (str): Обратный порядок фильтрации
            range_input (str): Диапазон вывода
            columns_input (str): Требуемые столбцы
        """
        self.filter_parameter = self.__init_filter_parametr(filter_parameter_input)
        self.sort_field = self.__init_sort_field(sort_field_input.rstrip().lstrip(), reverse_input.rstrip().lstrip())
        self.range = list(map(int, self.__init_range(range_input)))
        self.columns = self.__init_columns(columns_input)

    def check_input(self):
        """Выводит сообщение о неправильном вводе данных и возвращает результат проверки на корректность

            Returns:
                bool: False если не прошла проверка, иначе True
        """
        if not (self.filter_parameter[0] == "Нет" or self.filter_parameter[0] == "Ок"):
            print(self.filter_parameter[0])
            return False
        elif not (self.sort_field[0] == "Нет" or self.sort_field[0] == "Ок"):
            print(self.sort_field[0])
            return False
        return True

    def __init_filter_parametr(self, filter_parameter_input: str):
        """Проверяет правильность введеных данных для параметра фильтрации и преобразует их в нужный вид

            Args:
                filter_parameter_input (str): Параметр фильтрации для проверки

            Returns:
                list: Массив размером 1 с ошибкой, иначе массив размером 3 с преобразованными параметрами
        """
        if filter_parameter_input == "":
            return ["Нет"]
        elif ":" not in filter_parameter_input:
            return ["Формат ввода некорректен"]
        else:
            field = filter_parameter_input.split(":")[0]
            param = filter_parameter_input.split(":")[1]
            field = get_key(fieldToRus, field)
            if field == None:
                return ["Параметр поиска некорректен"]
            return ["Ок", field, param]

    def __init_sort_field(self, sort_field_input: str, reverse_input: str):
        """Проверяет правильность введеных данных для параметра сортировки и преобразует их в нужный вид

            Args:
                sort_field_input (str): Параметр фильтрации для проверки
                reverse_input (str): Порядок сортировки для проверки

            Returns:
                list: Массив размером 1 с ошибкой, иначе массив размером 3 с преобразованными параметрами
        """
        if (sort_field_input != "" and sort_field_input not in list(fieldToRus.values())):
            return ["Параметр сортировки некорректен"]
        elif (sort_field_input == ""):
            return ["Нет"]
        elif not (reverse_input == "Да" or reverse_input == "Нет" or reverse_input == ""):
            return ["Порядок сортировки задан некорректно"]
        else:
            if (reverse_input == "Да"):
                reverse_input = True
            else:
                reverse_input = False
            return ["Ок", sort_field_input, reverse_input]

    def __init_range(self, range_input: str):
        """Проверяет правильность введеных данных для диапазон вывода и преобразует их в нужный вид

            Args:
                range_input (str): Диапазон вывода для проверки

            Returns:
                list: Массив размером 2, с границами сортировки
        """
        range_input = range_input.split(" ")
        if (range_input == ['']):
            filterFrom, filterTo = 1, 99999999
        elif (len(range_input) == 1):
            filterFrom, filterTo = range_input[0], 99999999
        else:
            filterFrom, filterTo = range_input[0], range_input[1]
        return [filterFrom, filterTo]

    def __init_columns(self, columns_input: str):
        """Проверяет правильность введеных данных для требуемых столбцов

            Args:
                columns_input (str): Требуемые столбцы для проверки

            Returns:
                list: Требуемые колонки
        """
        columns_input = columns_input.split(", ")
        columns = []
        if len(columns_input) >= 1 and not "" in columns_input:
            columns = list(columns_input)
            columns.append("№")
        return columns

class DataSet:
    """Класс для хранения названия файла и всех вакансий

        Attributes:
            file_name (str): Имя файла
            vacancies_objects (list): Вакансии
    """

    def __init__(self, ﬁle_name: str, vacancies_objects: list):
        """Инициализирует объект DataSet

        Args:
            ﬁle_name (str): Имя файла
            vacancies_objects (list): Вакансии
        """
        self.file_name = file_name
        self.vacancies_objects = vacancies_objects

class Table:
    """Класс для работы с таблицей.

    Attributes:
        vacancies_objects (list): Вакансии
        input_connect (InputConect): Проверка ввода
        fields (list): Поля таблицы
        table (PrettyTable): Таблица
    """

    def __init__(self, vacancies_objects: list, fields: list, input_connect: InputConect):
        """Инициализирует объект Table

        Args:
            vacancies_objects (list): Вакансии
            fields (list): Поля таблицы
            input_connect (InputConect): Проверка ввода
        """
        self.vacancies_objects = vacancies_objects
        self.input_connect = input_connect
        self.fields = fields
        self.table = PrettyTable()

    def filter(self):
        """Вызывает функции фильтра и сортировки вакансий
        """
        vacancies = self.vacancies_objects
        if input_connect.filter_parameter[0] == "Ок":
            vacancies = self.filter_vacancies(vacancies)
        if input_connect.sort_field[0] == "Ок":
            vacancies = self.sort_vacancies(vacancies)
        self.vacancies_objects = vacancies

    def fill_table(self):
        """Полностью заполняет таблицу
        """
        self.table.hrules = 1
        self.table.align = "l"
        self.table.field_names = ['№', 'Название', 'Описание', 'Навыки', 'Опыт работы', 'Премиум-вакансия',
                                  'Компания', 'Оклад', 'Название региона', 'Дата публикации вакансии']
        for i in range(len(self.vacancies_objects)):
            self.table.add_row([i + 1] + self.vacancies_objects[i].to_list())
        self.table._max_width = {'Название': 20, 'Описание': 20, 'Навыки': 20, 'Опыт работы': 20,
                                 'Премиум-вакансия': 20,
                                 'Компания': 20, 'Оклад': 20, 'Название региона': 20, 'Дата публикации вакансии': 20}

    def print_table(self):
        """Выводит таблицу в консоль
        """
        columns = self.input_connect.columns
        start = self.input_connect.range[0]
        end = self.input_connect.range[1]
        print(self.table.get_string(start=start - 1, end=end - 1, fields=columns))

    def filter_vacancies(self, vacancies):
        """Фильтрует вакансии

            Args:
                vacancies (list): Вакансии

            Returns:
                list: Отфильтрованные вакансии
        """
        filterField = self.input_connect.filter_parameter[1].rstrip().lstrip()
        filterParam = self.input_connect.filter_parameter[2].rstrip().lstrip()
        if filterField == "salary_currency":
            filterParam = get_key(currencyToRus, filterParam)
            return list(filter(lambda vacancy: filterParam in vacancy.salary.salary_currency, vacancies))
        elif filterField == "premium":
            return list(filter(
                lambda vacancy: filterParam in vacancy.premium.lower().replace("true", "Да").replace("false", "Нет"),
                vacancies))
        elif filterField == "experience_id":
            filterParam = get_key(experienceToRus, filterParam)
            return list(filter(lambda vacancy: filterParam in vacancy.experience_id, vacancies))
        elif filterField == "salary":
            return list(filter(lambda vacancy: float(vacancy.salary.salary_from) <= float(filterParam) <= float(
                vacancy.salary.salary_to), vacancies))
        elif filterField == "key_skills":
            skills = filterParam.split(", ")
            return list(filter(lambda vacancy: self.check_skills(vacancy.key_skills, skills), vacancies))
        elif filterField == "published_at":
            return list(filter(lambda vacancy: vacancy.date_to_string() == filterParam, vacancies))
        return list(filter(lambda vacancy: filterParam == getattr(vacancy, filterField), vacancies))

    def sort_vacancies(self, vacancies):
        """Сортирует вакансии

            Args:
                vacancies (list): Вакансии

            Returns:
                list: Отсортированные вакансии
        """
        sort_field = self.input_connect.sort_field[1].rstrip().lstrip()
        reverse_sort = self.input_connect.sort_field[2]
        if sort_field == "Оклад":
            vacancies = sorted(vacancies, key=lambda vacancy: (float(vacancy.salary.salary_from) * currency_to_rub[
                vacancy.salary.salary_currency] + float(vacancy.salary.salary_to) * currency_to_rub[
                                                                   vacancy.salary.salary_currency]) // 2,
                               reverse=reverse_sort)
        elif sort_field == "Опыт работы":
            vacancies = sorted(vacancies, key=lambda vacancy: experienceToPoints[vacancy.experience_id],
                               reverse=reverse_sort)
        else:
            sortIndex = fields.index(get_key(fieldToRus, sort_field))
            if sort_field == "Навыки":
                vacancies = sorted(vacancies, key=lambda vacancy: len(vacancy.key_skills), reverse=reverse_sort)
            else:
                vacancies = sorted(vacancies, key=lambda vacancy: getattr(vacancy, get_key(fieldToRus, sort_field)),
                                   reverse=reverse_sort)
        return vacancies

    def check_skills(self, vacancy_skills, skills):
        """Проверяет наличие всех требуемых навыков в вакансии

            Args:
                vacancy_skills (list): Список навыков вакансии
                skills (list): Навыки для проверки

            Returns:
                bool: Наличие всех требуемых навыков в вакансии
        """
        for skill in skills:
            if skill not in vacancy_skills:
                return False
        return True

class CsvWorker:
    """Класс для работы с CSV файлом

        Attributes:
            file_name (str): Имя файла
    """

    def __init__(self, file_name: str):
        """Инициализирует объект CsvWorker

            Args:
                file_name (str): Имя файла
        """
        self.file_name = file_name

    def check_file(self):
        """Проверяет файл на пустоту

            Returns:
                bool: Пустой ли файл
        """
        if os.stat(file_name).st_size == 0:
            print("Пустой файл")
            return False
        return True

    def сsv_reader(self):
        """Читает файл, создает list Вакансий и list Полей

            Returns:
                list, list: Вакансии, Поля
        """
        fields = []
        vacancies = []
        with open(ﬁle_name, encoding="UTF-8-sig") as File:
            reader = csv.reader(File, delimiter=',')
            for row in reader:
                if (fields == []):
                    fields = row
                elif (len(fields) == len(row) and not ("" in row)):
                    vacancies.append(self.csv_ﬁler(row, fields))
        return vacancies, fields

    def csv_ﬁler(self, vacancy_in, fields):
        """Создает вакансию, находя необходимые аттрибуты для нее

            Args:
                vacancy_in (list): Вакансия в виде list

            Returns:
                Vacancy: Вакансия
        """
        name = vacancy_in[fields.index("name")] if "name" in fields else ""
        description = vacancy_in[fields.index("description")] if "description" in fields else ""
        key_skills = vacancy_in[fields.index("key_skills")] if "key_skills" in fields else ""
        experience_id = vacancy_in[fields.index("experience_id")] if "experience_id" in fields else ""
        premium = vacancy_in[fields.index("premium")] if "premium" in fields else ""
        employer_name = vacancy_in[fields.index("employer_name")] if "employer_name" in fields else ""
        area_name = vacancy_in[fields.index("area_name")] if "area_name" in fields else ""
        salary_from = vacancy_in[fields.index("salary_from")] if "salary_from" in fields else ""
        salary_to = vacancy_in[fields.index("salary_to")] if "salary_to" in fields else ""
        salary_gross = vacancy_in[fields.index("salary_gross")] if "salary_gross" in fields else ""
        salary_currency = vacancy_in[fields.index("salary_currency")] if "salary_currency" in fields else "RUR"
        published_at = vacancy_in[fields.index("published_at")] if "published_at" in fields else ""
        salary = Salary(salary_from, salary_to, salary_gross, salary_currency)
        vacancy = Vacancy(name, description, key_skills, experience_id, premium, employer_name, salary, area_name,
                          published_at)
        return vacancy


class HtmlGenerator:
    """Класс для генерации HTML страницы
    """
    def generate_table(self, titles, content):
        """Возвращает HTML код таблицы

            Args:
                titles (list): Заголовки столбцов
                content (list): Строки таблицы

            Returns:
                str: HTML код таблицы
        """
        table = "<table>"
        table += self.generate_titles(titles)
        for row in content:
            table += self.generate_row(row)
        table += "</table>"
        return table

    def generate_titles(self, titles):
        """Возвращает HTML код для заголовков таблицы

            Args:
                titles (list): Заголовки столбцов

            Returns:
                str: HTML код заголовков
        """
        string = "<tr>"
        for title in titles:
            string += "<th>" + title + "</th>"
        string += "</tr>"
        return string

    def generate_html(self, dicts, image_path, prof_name):
        """Возвращает HTML код страницы с графиками и 3-мя таблицами

            Args:
                dicts (list): Словари со строками и заголовками для таблиц
                image_path (str): Путь до графика
                prof_name (str): Имя выбранной профессии

            Returns:
                str: HTML код страницы
        """
        html = """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>Report</title>
                    </head>
                    <style>
                    body{
                        font-family: Verdana;
                    }
                    table{
                        text-align: center;
                        border-collapse: collapse;
                    }
                    th, td{
                        border: 1px solid;
                        padding: 5px;
                    }
                    </style>
                    <body>
                    <h1 style="text-align: center; font-size: 60px;">Аналитика по зарплатам и городам для профессии """ + prof_name + """</h1>
                    <img src=\"""" + image_path + """\">"""
        # 1
        titles = ["Год", "Средняя зарплата", "Средняя зарплата - " + prof_name, "Количество вакансий",
                  "Количество вакансий - " + prof_name]
        html += "<h1 style='text-align:center;'>Статистика по годам</h1>"
        html += "<table style='width: 100%;'>" + self.generate_titles(titles)
        dict = dicts[0]
        for i in range(len(dict[0])):
            year = dict[0][i]
            avgSalary = list(dict[1].values())[i]
            avgSalaryProf = list(dict[3].values())[i]
            vacAmount = list(dict[2].values())[i]
            vacAmountProf = list(dict[4].values())[i]
            row = [year, avgSalary, avgSalaryProf, vacAmount, vacAmountProf]
            html += self.generate_row(row)
        html += """</table> <br>"""
        # 2
        titles = ["Город", "Уровень зарплат"]
        html += "<h1 style='text-align:center;'>Статистика по городам</h1>"
        html += "<table style='float: left; width: 45%;'>" + self.generate_titles(titles)
        dict = dicts[1][0]
        values = list(dict.values())
        keys = list(dict.keys())
        for i in range(len(values)):
            city = keys[i]
            avgSalary = values[i]
            row = [city, avgSalary]
            html += self.generate_row(row)
        html += "</table>"
        # 3
        titles = ["Город", "Доля вакансий"]
        html += "<table style='float: right; width: 45%;'>" + self.generate_titles(titles)
        dict = dicts[1][1]
        values = list(dict.values())
        keys = list(dict.keys())
        for i in range(len(values)):
            city = keys[i]
            percent = str(values[i] * 100).replace(".", ",") + "%"
            row = [city, percent]
            html += self.generate_row(row)
        html += "</table></body></html>"
        return html

    def generate_row(self, row):
        """Возвращает HTML код для строки таблицы

            Args:
                row (list): Строка таблицы

            Returns:
                str: HTML код для строки
        """
        string = "<tr>"
        for row_item in row:
            string += "<td>" + str(row_item) + "</td>"
        string += "</tr>"
        return string


class Report:
    """Класс для создания графиков

        Attributes:
            filename (str): Имя файла
            html (str): HTML код страницы
    """
    def __init__(self, name, dicts, prof_name):
        """Инициализирует объект Report, генерирует граф и создает HTML код страницы
            Args:
                name (str): Имя файла
                dicts (list): Данные для графиков и таблиц
                prof_name (str): Имя выбранной профессии
        """
        generator = HtmlGenerator()
        parent_dir = path.dirname(path.abspath(__file__))
        self.filename = name
        self.generate_graph(dicts, prof_name)
        self.html = generator.generate_html(dicts, parent_dir + '/temp.png', prof_name)

    def generate_graph(self, dicts, prof_name):
        """Создает и сохраняет в виде файла графики

            Args:
                dicts (list): Данные для графиков
                prof_name (str): Имя выбранной профессии
        """
        dictsSalary = dicts[0]
        dictsCities = dicts[1]
        years = dictsSalary[0]
        plt.grid(axis='y')
        plt.style.use('ggplot')
        plt.rcParams.update({'font.size': 8})
        x = np.arange(len(years))
        width = 0.35
        ax = plt.subplot(2, 2, 1)
        ax.bar(x - width / 2, dictsSalary[1].values(), width, label='средняя з/п')
        ax.bar(x + width / 2, dictsSalary[3].values(), width, label='з/п ' + prof_name)
        ax.legend()
        ax.set_xticks(x, years, rotation=90)
        plt.title("Уровень зарплат по годам")
        ax = plt.subplot(2, 2, 2)
        ax.bar(x - width / 2, dictsSalary[2].values(), width, label='Количество вакансий')
        ax.bar(x + width / 2, dictsSalary[4].values(), width, label='Количество вакансий\n' + prof_name)
        ax.legend()
        ax.set_xticks(x, years, rotation=90)
        plt.title("Количество вакансий по годам")
        plt.subplot(2, 2, 3)
        plt.barh(list(reversed(list(dictsCities[0].keys()))), list(reversed(dictsCities[0].values())), alpha=0.8, )
        plt.title("Уровень зарплат по городам")
        plt.subplot(2, 2, 4)
        plt.pie(list(dictsCities[1].values()) + [1 - sum(list(dictsCities[1].values()))],
                labels=list(dictsCities[1].keys()) + ["Другие"])
        plt.title("Доля вакансий по городам")
        plt.subplots_adjust(wspace=0.5, hspace=0.5)
        plt.savefig("temp.png", dpi=200, bbox_inches='tight')


class DataWorker:
    """Класс для статистической обработки вакансий
    """
    def print_data(self, data, total_vacancies):
        """Обрабатывает вакансии и возвращает словари для создания таблиц, графиков и выводит данные этих словарей

            Args:
                data (list): Статистические данные
                total_vacancies (int): Общеее число вакансий

            Returns:
                [dict, dict]: Данные для создания таблиц и графиков
        """
        temp = {}
        salaryDict = []
        cityDict = []
        for x in data["salary"].keys():
            temp[x] = int(sum(data["salary"][x]) / len(data["salary"][x]))
        print("Динамика уровня зарплат по годам:", temp)
        salaryDict.append(list(list(data["salary"].keys())[i] for i in range(len(data["salary"].keys()))))
        salaryDict.append(temp)
        print("Динамика количества вакансий по годам:", data["amount"])
        salaryDict.append(data["amount"])
        temp = {list(data["salary"].keys())[i]: 0 for i in range(len(data["salary"].keys()))}
        for x in data["salary_prof"].keys():
            temp[x] = int(sum(data["salary_prof"][x]) / len(data["salary_prof"][x]))
        print("Динамика уровня зарплат по годам для выбранной профессии:", temp)
        salaryDict.append(temp)
        if len(data["amount_prof"]) != 0:
            print("Динамика количества вакансий по годам для выбранной профессии:", data["amount_prof"])
            salaryDict.append(data["amount_prof"])
        else:
            temp = {list(data["salary"].keys())[i]: 0 for i in range(len(data["salary"].keys()))}
            print("Динамика количества вакансий по годам для выбранной профессии:", temp)
            salaryDict.append(temp)
        temp = {}
        if "Россия" in data["salary_city"]:
            data["salary_city"].pop("Россия")
        for x in data["salary_city"].keys():
            percent = len(data["salary_city"][x]) / total_vacancies
            if (percent >= 0.01):
                temp[x] = int(sum(data["salary_city"][x]) / len(data["salary_city"][x]))
        temp = dict(sorted(temp.items(), key=lambda x: x[1], reverse=True)[:10])
        print("Уровень зарплат по городам (в порядке убывания):", temp)
        cityDict.append(temp)
        temp = {}
        if "Россия" in data["amount_city"]:
            data["amount_city"].pop("Россия")
        for x in data["amount_city"].keys():
            percent = data["amount_city"][x] / total_vacancies
            if (percent >= 0.01):
                temp[x] = round(percent, 4)
        temp = dict(sorted(temp.items(), key=lambda x: x[1], reverse=True)[:10])
        print("Доля вакансий по городам (в порядке убывания):", temp)
        cityDict.append(temp)
        return [salaryDict, cityDict]

    def get_data(self, vacancies_objects, prof_name):
        """Обрабатывает вакансии и возвращает статистические данные

            Args:
                vacancies_objects (list): Список вакансий
                prof_name (str): Имя выбранной профессии

            Returns:
                dict: Статистические данные
        """
        dict = {"salary": {},
                "amount": {},
                "salary_prof": {},
                "amount_prof": {},
                "salary_city": {},
                "amount_city": {}}
        for vacancy in vacancies_objects:
            avg_salary = (vacancy.salary.salary_from + vacancy.salary.salary_to) / 2 * currency_to_rub[
                vacancy.salary.salary_currency]
            year = vacancy.date_get_year()
            # Динамика уровня зарплат по годам
            if year not in dict["salary"]:
                dict["salary"][year] = [avg_salary]
            else:
                dict["salary"][year] += [avg_salary]
            # Динамика количества вакансий по годам
            if year not in dict["amount"]:
                dict["amount"][year] = 1
            else:
                dict["amount"][year] += 1
            if prof_name in vacancy.name:
                # Динамика уровня зарплат по годам для выбранной профессии
                if year not in dict["salary_prof"].keys():
                    dict["salary_prof"][year] = [avg_salary]
                else:
                    dict["salary_prof"][year] += [avg_salary]
                # Динамика количества вакансий по годам для выбранной профессии
                if year not in dict["amount_prof"].keys():
                    dict["amount_prof"][year] = 1
                else:
                    dict["amount_prof"][year] += 1
            # Уровень зарплат по городам (в порядке убывания)
            if vacancy.area_name not in dict["salary_city"]:
                dict["salary_city"][vacancy.area_name] = [avg_salary]
            else:
                dict["salary_city"][vacancy.area_name] += [avg_salary]
            # Доля вакансий по городам (в порядке убывания)
            if vacancy.area_name not in dict["amount_city"]:
                dict["amount_city"][vacancy.area_name] = 1
            else:
                dict["amount_city"][vacancy.area_name] += 1
        return dict

if __name__ == "__main__":
    doctest.testmod()
    if input("Выберите программу:\n1-Ваканссии \n2-Статистикa\nВаш выбор: ") == "2":
        file_name = input("Введите название file: ")
        options = {'enable-local-file-access': None}
        config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
        prof_name = input("Введите название профессии: ")

        csv_worker = CsvWorker(file_name)
        vacancies_objects, _ = csv_worker.сsv_reader()
        data_set = DataSet(file_name, vacancies_objects)
        dataWorker = DataWorker()
        data = dataWorker.get_data(vacancies_objects, prof_name)

        generator = HtmlGenerator()

        report = Report("graph.jpg", dataWorker.print_data(data, len(vacancies_objects)), prof_name)
        pdfkit.from_string(report.html, 'report.pdf', configuration=config, options=options)
    else:
        file_name = input("Введите название файла: ")
        filter_parametr_input = input("Введите параметр фильтрации: ")
        sort_input = input("Введите параметр сортировки: ")
        reverse_input = input("Обратный порядок сортировки (Да / Нет): ")
        range_input = input("Введите диапазон вывода: ")
        columns_input = input("Введите требуемые столбцы: ")
        input_connect = InputConect(filter_parametr_input, sort_input, reverse_input, range_input, columns_input)
        csv_worker = CsvWorker(file_name)

        if (input_connect.check_input() and csv_worker.check_file()):
            vacancies_objects, fields = csv_worker.сsv_reader()
            data_set = DataSet(file_name, vacancies_objects)
            if len(data_set.vacancies_objects) != 0:
                table = Table(vacancies_objects, fields, input_connect)
                table.filter()
                if len(table.vacancies_objects) == 0:
                    print("Ничего не найдено")
                else:
                    table.fill_table()
                    table.print_table()
            else:
                print("Нет данных")
