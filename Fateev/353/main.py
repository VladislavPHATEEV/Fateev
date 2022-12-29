from DataSet_class import DataSet
from Report_class import Report
from Table_statistics import TableStatistics

if __name__ == "__main__":
    file_name = input("Введите название файла: ")
    current_vacancy_name = input("Введите название профессии: ")

    data_set = DataSet(current_vacancy_name)
    dates = data_set.currency_frequency_reader(file_name)
    data_set.generate_currency(dates[1], dates[0])
    data_set.get_vacancies_data()
    data_set.fill_dataframes_by_sql()
    data_set.print_statistics_dataframes()

