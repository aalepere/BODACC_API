import requests
from bs4 import BeautifulSoup

r = requests.get("https://echanges.dila.gouv.fr/OPENDATA/BODACC/2020/")
soup = BeautifulSoup(r.text, 'html.parser')

list_bodacc_files = []
for link in soup.find_all('a'):
    list_bodacc_files.append(link.get('href'))

pcl_bodacc_files = [i for i in list_bodacc_files if "PCL" in i]
