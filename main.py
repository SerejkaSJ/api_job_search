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


def find_vacancies_develop_by_language_hh(language, count_days = 30, area_msk = 1):
    temp_page = 0
    pages_number =1 
    page_max = 50 
    vacancies = []
    while temp_page <= pages_number:
        url = 'https://api.hh.ru/vacancies'
        payload = {"text":"программист {}".format(language), "area":area_msk, "period":count_days, 'page':temp_page}
        response = requests.get(url,  params = payload)
        result = response.json()
        response.raise_for_status()
        pages_number = result['pages']
        if pages_number > page_max:
            pages_number = page_max
        temp_page +=1 
        for vacancy in result['items']:
            vacancies.append(vacancy)
    print("hh", len(vacancies))
    return vacancies
      
   
def predict_rub_salary_hh(vacancy):
    if vacancy['salary']:
        salary = vacancy['salary']
        if salary['currency'] != "RUR":
            return
        return predict_salary(salary['from'], salary['to'])
    else:
        return


def find_vacancies_develop_by_language_sj(language, token, catalogues = 48, town = 4):
    vacancies = []
    page = 0
    while True:
        url = 'https://api.superjob.ru/2.0/vacancies/'
        headers = {'X-Api-App-Id': token}
        payload = {"catalogues":catalogues, "town":town, "keyword":language, 'page':page}
        response = requests.get(url,  headers = headers, params = payload)
        response.raise_for_status()
        result = response.json()
        for vacancy in result['objects']:
            vacancies.append(vacancy)
        if result['more']:
            page += 1
        else:
            break
    print("sj", len(vacancies))
    return vacancies


def predict_salary(salary_from, salary_to):
    if not salary_from and not salary_to:
        return 
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if not salary_from:
        return salary_to * 0.8
    if not salary_to:
        return salary_from * 1.2


def predict_rub_salary_sj(vacancy):
    if vacancy['currency'] != "rub":
        return
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
    return info_from_sj       
     

if __name__ == "__main__":
    load_dotenv()
    token_sj = os.getenv("TOKEN_SJ")
    success_hh = True
    success_sj = True
    
    try:
        info_from_hh = get_info_hh(LANGUAGES)
    except  requests.exceptions.HTTPError as err:
        print("Error request from HeadHunter:", err)  
        success_hh = False  
        
    try:
        info_from_sj = get_info_sj(LANGUAGES, token_sj)
    except  requests.exceptions.HTTPError as err:
        print("Error request from SuperJob:", err)  
        success_sj = False

    if success_sj:
        print_table(info_from_sj, "SuperJob")
    if success_hh:
        print_table(info_from_hh, "HeadHunter")
