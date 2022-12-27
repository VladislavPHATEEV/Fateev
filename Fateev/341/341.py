# from DataSet_class import DataSet
# from Report_class import Report
# from Table_statistics import TableStatistics
#
#
# if __name__ == "__main__":
#     userQuery = input("Введите команду: (Вакансии / Статистика)")
#     if userQuery == "Вакансии":
#         TableStatistics.start_table_programm()
#     elif userQuery == "Статистика":
#         folder_name = input("Введите название папки: ")
#         file_name = input("Введите название файла: ")
#         current_vacancy_name = input("Введите название профессии: ")
#
#         data_set = DataSet(current_vacancy_name)
#         print(data_set.currency_frequency_reader(file_name='vacancies_dif_currencies.csv'))
#         data_set.generate_currency('2005-09-16T17:26:39+0400', '2022-07-18T19:35:13+0300')
#         file_names = data.csv_split_generator(file_name, folder_name)
#         data.multi_proc_fill_dictionaries(file_names)
#         data.concurrent_futures_fill_dictionaries(file_names)
#         data.fill_dictionaries(DataSet.csv_reader(file_name), current_vacancy_name)
#         data.calculate_vacancies_count()
#         data.fill_statistics_dictionaries()
#
#         data.print_statistics_dictionaries()
#
#         sorted_salaries_by_town = dict(sorted(data.salaries_by_town.items(), key=lambda item: item[1], reverse=True)[0:10])
#         sorted_vacancies_by_rate = dict(sorted(data.vacancies_rate_by_town.items(),
#                                               key=lambda item: item[1], reverse=True)[0:10])
#
#         report = Report()
#         report.generate_excel(data, sorted_salaries_by_town, sorted_vacancies_by_rate, current_vacancy_name)
#         report.generate_image(data, sorted_salaries_by_town, sorted_vacancies_by_rate, current_vacancy_name)
#         report.generate_pdf(current_vacancy_name, "graph.png", "report.xlsx")
#     else:
#         print("Неизвестная команда. Введите 'Вакансии' или 'Статистика'")
# @staticmethod
#     def get_statistics_for_year(tuple_args):
#         """
#         Возвращает статистику расчитанную за 1 год
#         :param tuple_args: ([str], str)
#             Аргументы функции, содержат название файла с данными и наазвание интересующей нас профессии
#         :return: {}
#             Статистика за 1 год
#         """
#         full_file_name = tuple_args[0]
#         current_name = tuple_args[1]
#         year_statistics = {}
#         year_statistics["vacancies_count_by_town"] = {}
#         year_statistics["salaries_sum_by_town"] = {}
#         vacancies_salaries_sum = 0
#         current_salaries_sum = 0
#         with open(full_file_name, "r", encoding="UTF-8-sig") as file:
#             file_reader = csv.DictReader(file, delimiter=",")
#             headlines_list = list(file_reader.fieldnames)
#             for line in file_reader:
#                 vacancy = DataSet.parse_line_to_vacancy(line, headlines_list)
#                 if vacancy is not None:
#                     year_statistics["vacancies_count"] = year_statistics.setdefault("vacancies_count", 0) + 1
#                     vacancies_salaries_sum += vacancy.average_ru_salary
#                     year_statistics["vacancies_count_by_town"][vacancy.area_name] \
#                         = year_statistics["vacancies_count_by_town"].setdefault(vacancy.area_name, 0) + 1
#                     year_statistics["salaries_sum_by_town"][vacancy.area_name] \
#                         = year_statistics["salaries_sum_by_town"].setdefault(vacancy.area_name, 0) \
#                           + vacancy.average_ru_salary
#                     if current_name in vacancy.name:
#                         year_statistics["current_count"] = year_statistics.setdefault("current_count", 0) + 1
#                         current_salaries_sum += vacancy.average_ru_salary
#         year_statistics["salary"] = int(vacancies_salaries_sum / year_statistics["vacancies_count"])
#         year_statistics["current_salary"] = int(current_salaries_sum / year_statistics["current_count"])
#         return year_statistics