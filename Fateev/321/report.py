import csv

def save_as_csv(file_name, fields, lines):
    """Сохраняет файл в виде csv файла 

        Args:
            file_name (str): Название файла
            fields (str): Поля csv файла
            lines (str): Вакансии через \n
    """
    print("Saving", file_name)
    with open("csv/"+file_name, 'w', encoding="utf-8-sig") as f_out:
        f_out.write(','.join(fields)+ "\n")
        f_out.writelines(lines[:-1])
        f_out.close()

def сsv_chuncker(file_name):
    """Разделяет вакансии по годам и сохраняет их

        Args:
            file_name (str): Название файла для разделения
    """
    fields = []
    csvs = {}
    with open(ﬁle_name, encoding="UTF-8-sig") as File:
        reader = csv.reader(File, delimiter=',')
        for row in reader:
            if (fields == []):
                fields = row
            elif (len(fields) == len(row) and not ("" in row)):
                year = row[fields.index('published_at')].split("-")[0]
                if year not in csvs:
                    csvs[year] = []
                csvs[year].append(row)
    for year in csvs:
        year_str = ""
        for row in csvs[year]:
            year_str += ','.join(row) + "\n"
        save_as_csv("vacancies_" + year + ".csv", fields, year_str)

file_name = input("Введите название файла: ")
сsv_chuncker(file_name)