import requests
import json
import re
import os

from terminaltables import AsciiTable
from dotenv import load_dotenv

LANGUAGES = [
    "C++",
    "C",
    "Lua",
    "Java",
    "Javacript",
    "Python",
    "Node.js",
    "PHP",
]


def find_vacancies_develop_by_language_hh(language):
    temp_page = 0
    pages_number =1 
    vacancies = []
    while temp_page <= pages_number:
        url = 'https://api.hh.ru/vacancies'
        payload = {"text":"программист {}".format(language), "area":"1", "period":'30', 'page':temp_page}
        response = requests.get(url,  params = payload)
        result = response.json()
        pages_number = result['pages']
        if pages_number > 50:
            pages_number = 50
        temp_page +=1 
        for vacancy in result['items']:
            vacancies.append(vacancy)
  

    return vacancies
      
   
def predict_rub_salary_hh(vacancy):
    if vacancy['salary']:
        salary = vacancy['salary']
        if salary['currency'] != "RUR":
            return None
        return predict_salary(salary['from'], salary['to'])
    else:
        return None


def find_vacancies_develop_by_language_sj(language, token):
    vacancies = []
    page = 0
    while True:
        url = 'https://api.superjob.ru/2.0/vacancies/'
        headers = {'X-Api-App-Id': token}
        payload = {"catalogues":48, "town":4, "keyword":language, 'page':page}
        response = requests.get(url,  headers = headers, params = payload)
        result = response.json()
        for vacancy in result['objects']:
            vacancies.append(vacancy)
        if result['more']:
            page += 1
        else:
            break

    return vacancies


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return None
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if not salary_from:
        return salary_to * 0.8
    if not salary_to:
        return salary_from * 1.2


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != "rub":
        return None
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])
 

def average_count(array):
    count = 0
    summa = 0
    for values in array:
        if values:
            count += 1
            summa = summa + values
    return int(summa / count), count


def print_table(stat, title):
    table = [("Язык программирования", "Найдено вакансий", "Обработано вакансий", "Средняя зарплата")]
    for language in stat.keys():
        table.append((language, stat[language]['vacancies_found'],stat[language]['vacancies_processed'],stat[language]['average_salary']))
    table_instance = AsciiTable(table, title)
    table_instance.justify_columns[2] = 'right'
    print(table_instance.table)
    
    
def get_info_hh(languages):
    info_from_hh = {}
    for language in languages:
        vacancies = find_vacancies_develop_by_language_hh(language)
        salary = []
        for vacancy in vacancies:
            salary.append(predict_rub_salary_hh(vacancy))
        average_salary, vacancies_processed = average_count(salary)
        info_from_hh[language] = {
            'vacancies_found' : len(vacancies),
            'average_salary' : average_salary,
            'vacancies_processed' : vacancies_processed,
        }
    return info_from_hh
        
        
def get_info_sj(languages, token):
    info_from_sj = {}
    for language in languages:
        vacancies = find_vacancies_develop_by_language_sj(language, token)
        salary = []
        for vacancy in vacancies:
            salary.append(predict_rub_salary_sj(vacancy))
        average_salary, vacancies_processed = average_count(salary)
        info_from_sj[language] = {
            'vacancies_found' : len(vacancies),
            'average_salary' : average_salary,
            'vacancies_processed' : vacancies_processed,
        }
    return info_from_hh        
     

if __name__ == "__main__":
    load_dotenv()
    token_sj = os.getenv("TOKEN_SJ")
    info_from_hh = get_info_hh(LANGUAGES)
    info_from_sj = get_info_sj(LANGUAGES, token_sj)

    print_table(info_from_sj, "SuperJob")
    print_table(info_from_hh, "HeadHunter")
