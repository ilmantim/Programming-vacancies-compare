import os
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from:
        return salary_from * 1.2
    elif salary_to:
        return salary_to * 0.8


def predict_rub_salary_hh(vacancy):
    salary = vacancy['salary']
    if not salary:
        return None
    salary_from = salary['from']
    salary_to = salary['to']
    currency = salary['currency']
    if currency == 'RUR':
        return predict_salary(salary_from, salary_to)
    else:
        return None


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    currency = vacancy['currency']

    if currency == 'rub':
        return predict_salary(salary_from, salary_to)
    else:
        return None
    

def get_hh_statistics(programming_languages):
    url = 'https://api.hh.ru/vacancies'
    one_month_ago = datetime.now() - timedelta(days=30)
    date_from = one_month_ago.strftime('%Y-%m-%d')

    language_statistics = {}

    for language in programming_languages:
        page = 0
        pages_number = 1

        estimated_salaries = []

        while page < pages_number:
            params = {
                'text': language,
                'area': '1',
                'date_from': date_from,
                'page': page
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            # Parse the JSON response
            vacancies = response.json()

            print(f"Downloading {language} - Page {page + 1}")

            pages_number = vacancies['pages']

            page += 1

            for vacancy in vacancies['items']:
                estimated_salary = predict_rub_salary_hh(vacancy)
                if estimated_salary:
                    estimated_salaries.append(estimated_salary)

        if estimated_salaries:
            average_salary = int(sum(estimated_salaries) / len(estimated_salaries))

        language_statistics[language] = {
            "vacancies_found": vacancies['found'],
            "vacancies_processed": len(estimated_salaries),
            "average_salary": average_salary
        }

    return language_statistics


def get_sj_statistics(programming_languages, superjob_api_key):  
    url = 'https://api.superjob.ru/2.0/vacancies'
    one_month_ago = datetime.now() - timedelta(days=30)
    date_from_unix = int(one_month_ago.timestamp())

    language_statistics = {}

    for language in programming_languages:
        page = 0

        estimated_salaries = []

        while page < 5:
            headers = {
                'X-Api-App-Id': superjob_api_key
            }

            params = {
                'town': 4,
                'catalogues': 48,
                'keyword': language,
                'date_published_from': date_from_unix,
                'page': page,
                'count': 100
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            vacancies_data = response.json()

            print(f"Downloading {language} - Page {page + 1}")

            page += 1

            vacancies = vacancies_data['objects']

            for vacancy in vacancies:
                estimated_salary = predict_rub_salary_sj(vacancy)
                if estimated_salary:
                    estimated_salaries.append(estimated_salary)

        if estimated_salaries:
            average_salary = int(sum(estimated_salaries) / len(estimated_salaries))

        else:
            average_salary = 0 

        language_statistics[language] = {
            "vacancies_found": vacancies_data['total'],
            "vacancies_processed": len(estimated_salaries),
            "average_salary": average_salary
        }

    return language_statistics


def display_statistics_table(statistics, title):
   
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']
    ]

    for language, stats in statistics.items():
        row = [language, stats['vacancies_found'], stats['vacancies_processed'], stats['average_salary']]
        table_data.append(row)

    table = AsciiTable(table_data, title)

    print(table.table)


def main():
    load_dotenv()
    superjob_api_key = os.getenv('SUPERJOB_API_KEY')

    programming_languages = ['Python', 'Java', 'JavaScript', 'Ruby', 'PHP', 'C++', 'C#', 'C', 'Go']

    language_statistics_hh = get_hh_statistics(programming_languages)
    language_statistics_sj = get_sj_statistics(programming_languages, superjob_api_key)

    display_statistics_table(language_statistics_hh, 'HeadHunter Moscow')
    display_statistics_table(language_statistics_sj, 'SuperJob Moscow')


if __name__ == '__main__':
    main()