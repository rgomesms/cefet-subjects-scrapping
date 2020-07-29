import requests
import tabula
import pandas as pd
import json
from bs4 import BeautifulSoup
from tqdm import tqdm


def fetch_table_from_area(pdf_link: str, top: float, left: float, width: float, height: float) -> pd.DataFrame:
    bottom = top + height
    right = left + width
    table = tabula.read_pdf(pdf_link, stream=True, pages=[1], area=[top, left, bottom, right])[0]
    return table


def main():
    url = 'http://www.decom.cefetmg.br/ensino/graduacao/engenharia-de-computacao/disciplinas/'
    response = requests.get(url)

    subject_names = []
    if response.status_code == 200:
        page_html = response.text
        soup = BeautifulSoup(page_html, 'html.parser')

        # fetch the name of every subject in ENG. COMP
        for link in soup.find_all('a'):
            href = link.get('href')
            if isinstance(href, str) and href.endswith('.pdf'):
                subject_names.append(link.get('title'))

        # Extract info from pdf available on the site
        subjects_dict = {}
        for link in soup.find_all('a'):
            href = link.get('href')
            subject_name = link.text
            if isinstance(href, str) and href.endswith('.pdf') and not subject_name.startswith('Tópicos Especiais'):
                subjects_dict[subject_name] = {}
                cur_subject_dict = subjects_dict[subject_name]

                hours_table = None
                if subject_name.startswith('Laboratório de Arquitetura'):
                    hours_table = fetch_table_from_area(href, top=101.45, left=36.5, width=263.16, height=36.34)
                else:
                    hours_table = fetch_table_from_area(href, top=87.89, left=33.24, width=269.26, height=42.14)

                table_line = hours_table.iloc[0]
                print(subject_name)
                print(table_line)
                cur_subject_dict['horas'] = {
                    'teoria': int(table_line['Teoria']),
                    'pratica': int(table_line['Prática']),
                    'total': int(table_line['Total'])
                }

                credits_table = fetch_table_from_area(href, top=69.34, left=299.81, width=262.48, height=60.08)
                table_line = credits_table.iloc[0]
                cur_subject_dict['creditos'] = int(table_line['CRÉDITOS'])
                cur_subject_dict['natureza'] = table_line['NATUREZA']

                # requisites_table = fetch_table_from_area(href, top=132.06, left=32.6, width=537.09, height=68.6)
        json.dump(subjects_dict, open('./eng_comp.json', 'w'))

    else:
        print(f'Error: status code {response.status_code}')


if __name__ == '__main__':
    main()
