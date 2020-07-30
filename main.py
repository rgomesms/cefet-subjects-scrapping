import requests
import tabula
import io
import pandas as pd
import json

from bs4 import BeautifulSoup
from unidecode import unidecode
from tqdm import tqdm

from constants import EMPTY_TABLES, ONE_LINE_TABLES, SUBJECTS_PER_SEMESTER


def fetch_table_from_area(pdf_link: str, top: float, left: float, width: float, height: float) -> pd.DataFrame:
    bottom = top + height
    right = left + width
    table = tabula.read_pdf(pdf_link, stream=True, pages=[1], area=[top, left, bottom, right])[0]
    return table


def main():
    url = 'http://www.decom.cefetmg.br/ensino/graduacao/engenharia-de-computacao/disciplinas/'
    response = requests.get(url)

    if response.status_code == 200:
        page_html = response.text
        soup = BeautifulSoup(page_html, 'html.parser')

        # fetch the name of every subject in ENG. COMP
        subject_names = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if isinstance(href, str) and href.endswith('.pdf'):
                subject_names.append(link.get('title'))

        # Extract info from pdf available on the site
        subjects_dict = {}
        for link in tqdm(soup.find_all('a'), disable=True):
            href = link.get('href')
            subject_name = link.text
            if isinstance(href, str) and href.endswith('.pdf') and not subject_name.startswith('Tópicos Especiais'):
                subject_name_key = unidecode(subject_name).lower().replace(' ', '_')
                subjects_dict[subject_name_key] = {}
                cur_subject_dict = subjects_dict[subject_name_key]

                # save the subject name.
                cur_subject_dict['nome'] = subject_name

                cur_subject_dict['periodo'] = None
                for key, value in SUBJECTS_PER_SEMESTER.items():
                    if subject_name in value:
                        cur_subject_dict['periodo'] = key

                if subject_name.startswith('Laboratório de Arquitetura'):
                    hours_table = fetch_table_from_area(href, top=101.45, left=36.5, width=263.16, height=36.34)
                else:
                    hours_table = fetch_table_from_area(href, top=87.89, left=33.24, width=269.26, height=42.14)

                table_line = hours_table.iloc[0]
                cur_subject_dict['horas'] = {
                    'teoria': int(table_line['Teoria']),
                    'pratica': int(table_line['Prática']),
                    'total': int(table_line['Total'])
                }

                credits_table = fetch_table_from_area(href, top=69.34, left=299.81, width=262.48, height=60.08)
                table_line = credits_table.iloc[0]
                cur_subject_dict['creditos'] = int(table_line['CRÉDITOS'])
                cur_subject_dict['natureza'] = table_line['NATUREZA']

                if subject_name in EMPTY_TABLES:
                    requisites_table = fetch_table_from_area(href, top=138.5, left=32.81, width=530.61, height=29.38)
                elif subject_name in ONE_LINE_TABLES:
                    requisites_table = fetch_table_from_area(href, top=132.02, left=32.55, width=530.87, height=43.19)
                else:
                    requisites_table = fetch_table_from_area(href, top=132.06, left=32.6, width=537.09, height=68.6)

                cur_subject_dict['pre-requisitos'] = requisites_table['PRÉ-REQUISITOS'].dropna().to_list()
                cur_subject_dict['co-requisitos'] = requisites_table['CO-REQUISITOS'].dropna().to_list()

        with io.open('eng_comp.json', 'w', encoding='utf8') as file:
            json.dump(subjects_dict, file, ensure_ascii=False)

    else:
        print(f'Error: status code {response.status_code}')


if __name__ == '__main__':
    main()
