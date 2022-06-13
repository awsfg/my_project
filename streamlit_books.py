import os
import re
import folium
import isbnlib
import requests
import geopandas
import numpy as np 
import pandas as pd
import seaborn as sns
from time import sleep
import streamlit as st
from shapely import wkt
import plotly.express as px
from newspaper import Article
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.figure_factory as ff
import goodreads_api_client as gr
from progressbar import ProgressBar
import urllib.request as urllib2
from bs4 import BeautifulSoup
from shapely.geometry import Point
from streamlit_folium import st_folium, folium_static
from folium.plugins import HeatMap
plt.style.use('ggplot')

import warnings
warnings.filterwarnings('ignore')


with st.echo(code_location='below'):
    
    @st.cache
    def data_mos_ru_libraries():
        API_KEY = 'd0f03e3c87a66846239c2de7cc0e6294'
        dataset_id = 526

        response = requests.get(url=f'https://apidata.mos.ru/v1/datasets/{dataset_id}/count', params={'api_key': API_KEY})
        count = int(response.text)
        url = f'https://apidata.mos.ru/v1/datasets/{dataset_id}/rows'
        answer = []

        for i in range(0, count, 100):
            params = {
                'api_key': API_KEY,
                '$orderby': 'global_id',
                '$top': 100,
                '$skip': i
            }
            sleep(2)
            response = requests.get(url=url, params=params)
            if (response.status_code == 200):
                data = response.json()
                answer.extend(data)
                print(len(answer))
        return answer
    
    st.title("Анализ предметной области `Книги`")

    st.subheader('Описание набора данных')
    """
    Для анализа предметной области "книги" был взят набор данных [Goodreads-books](https://www.kaggle.com/jealousleopard/goodreadsbooks), который содержит подробную информацию о книгах. 
    Детальное описание полей:
    * **bookID** - уникальный ID книги;
    * **title** - название книги;
    * **authors** - автор;
    * **average_rating** - средняя оценка книги;
    * **ISBN ISBN(10)** - номер, в котором содержится информация о книге;
    * **ISBN 13** - новый формат ISBN, созданный в 2007 году. Состоит из 13 цифр;
    * **language_code** - язык книги;
    * **num_pages** - количество страниц в книге;
    * **ratings_count** - количество оценок, которые получила книга;
    * **text_reviews_count** - количество рецензий;
    * **publication_date** - дата публикации книги;
    * **publisher** - имя издательства;
    """

    st.subheader('Описание набора данных')
    df = pd.read_csv('books.csv', error_bad_lines = False)
    st.write('Датасет содержит {} строк и {} столбцов.'.format(df.shape[0], df.shape[1]))
    
    # уберем Mary и оставим только J.K. Rowling
    df.replace(to_replace='J.K. Rowling/Mary GrandPré', value = 'J.K. Rowling', inplace=True)
    st.write(df)

    st.subheader('При помощи различных визуализаций проанализируем имеющийся датасет.')
    
    st.write("Количество книг, встречающиеся чаще всего")
    fig1 = plt.figure(figsize=(8, 4))

    sns.set_context('paper')
    books = df['title'].value_counts()[:10]
    sns.barplot(x = books, y = books.index, palette='deep')
    plt.title('Наиболее часто встречающиеся книги')
    plt.xlabel('Количество')
    plt.ylabel('Книги')
    st.pyplot(fig1)

    st.write("Видно, что книга встречается 8 раз (8 раз переиздавалась в разные даты и разными c publisher + разное кол-во страниц)")
    st.write(df[df['title']=='The Brothers Karamazov'])
    st.write("Из графика видно, что полученные книги либо являются классикой, либо старые, либо они являются частью обязательной школьной программы. Несмотря ни на что, эти книги выдержали течение времени и до сих пор актуальны/")

    st.markdown("")
    st.write("Распределение книг по языкам")
    fig2 = plt.figure(figsize=(8, 4))
    sns.set_context('paper')
    ax = df.groupby('language_code')['title'].count().plot.bar()
    plt.xlabel('Код языка')
    plt.ylabel('Количество')
    plt.xticks(fontsize = 15)
    for p in ax.patches:
        ax.annotate(str(p.get_height()), (p.get_x()-0.3, p.get_height()+100))
    st.pyplot(fig2)

    st.markdown("")
    st.write("Топ 10 книг по количеству оценок")
    most_rated = df.sort_values('ratings_count', ascending=False).head(15).set_index('title')
    fig3 = plt.figure(figsize=(8, 4))
    fig3 = go.Figure(
       px.bar(most_rated, x=most_rated['ratings_count'], y = most_rated.index)
    )
    fig3.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                  marker_line_width=1.5, opacity=0.6)
    fig3.update_layout(xaxis_title='Количество оценок', yaxis_title='Название', title_text='Топ 10 книг по количеству оценок')

    #1e6 = 1000000 (примерно)
    st.plotly_chart(fig3, use_container_width=True)

    """
    Выводы:
    * Видно, что начало серии книг обычно оценивается больше всего (Twilinght№1, The Hobbit, Angels & Demons№1))
    * Количество оценок у серии книг Harry Potter довольно большое, из чего можно сделать вывод: если человек начал читать серию книг, то он, скорее всего, стремится завершить ее до конца
    """


    st.markdown("")
    st.write("Авторы с наибольшим кол-вом книг.")
    sns.set_context('paper')
    most_books = df.groupby('authors')['title'].count().reset_index().sort_values('title', ascending=False).head(10).set_index('authors')

    fig4 = plt.figure(figsize=(8,4))
    fig4 = go.Figure(
       px.bar(most_books, x=most_books['title'], y = most_books.index)
    )
    fig4.update_traces(marker_color='rgb(158,202,225)', marker_line_color='rgb(8,48,107)',
                  marker_line_width=1.5, opacity=0.6)
    fig4.update_layout(xaxis_title='Количество книг', yaxis_title='Авторы', title_text='Топ 10 авторов с наибольшим количеством книг')
    st.plotly_chart(fig4, use_container_width=True)

    """
    Выводы:
    * Видно, что больше всего книг у Стивен Кинга и Вудхауса. Стоит учесть, что многие из книг - различные издания одной и той же книги
    * Из полученного списка авторов можно заметить, что некоторые из них - "классики", другие - пишут книги десятилетиями третьи - время от времени 
    """


    # ==============================================================
    # 1) мета информация из isbnlib 
    # 2) API request to goodreads_api_client 
    # 3) парсинг isbndb.com
    client = gr.Client(developer_key= 'qI4Do63YsTPICTREpQuu0g')
    def html(isbn):
        url = 'https://isbndb.com/book/'+isbn
        article = Article(url)
        article.download()
        article.parse()
        ar = article.html
        ar = ar[9300:9900]
        return ar

    def html_all(isbn):
        url = 'https://isbndb.com/book/'+isbn
        article = Article(url)
        article.download()
        article.parse()
        ar = article.html
        return ar

    def reg(l):
        return re.search(r'(\b\d{4})\b',l).groups()[0]
        
    def reg_price(l):
        try:
            return re.search(r'(\$[0-9.]+(\.[0-9]{2})?)',l).groups()[0]
        except:
            return "Не нашли цену :("

    def bookdata(df):
        year=[]
        pbar = ProgressBar()
        for isbn in pbar(df.isbn13):
            try:
                details = isbnlib.meta(str(isbn))
                year.append(details['Year'])
            except:
                try: 
                    book_detail = client.Book.show_by_isbn(isbn)
                    keys_wanted = ['publication_year']
                    reduced_book = {k:v for k,v in book_detail.items() if k in keys_wanted}
                    year.append((reduced_book['publication_year']))
                except:
                    try:
                        y = html(isbn)
                        year_extracted = reg(y) 
                        year.append(y)
                    except:
                        year.append('0')
                    
        return year

    def bookdata_html(df):
        price=[]
        pbar = ProgressBar()
        for isbn in pbar(df.isbn13):
            y = html_all(str(isbn))
            print(y)
            get_price = reg_price(y) 
            price.append(get_price)
        return price

    def plot_author_chart(author_df, name):
        status = st.text('Считаю среднюю оценку..')
        year = bookdata(author_df)
        author_df = final_df(author_df, year)
        author_df.dropna(0, inplace=True)
        author_df = author_df[author_df['Year'].str.isnumeric()]
        author_df = author_df.set_index('title')
        author_df = author_df[author_df.Year !='0']
        fig5 = plt.figure(figsize=(8,8))
        sns.set_context('paper')
        plt.xticks(rotation=30)
        ax = sns.barplot(author_df['Year'], author_df['average_rating'], palette='deep')
        plt.ylabel('Средняя оценка')
        plt.title('Средняя оценка книг в течение времени, ' + name)
        plt.xticks(rotation=30)
        st.pyplot(fig5)
        status.text('Готово!')

    def final_df(df1, l):
        year_df = pd.DataFrame(l, columns=['Year'])
        df1 = df1.reset_index(drop=True)
        final = df1[['authors', 'average_rating', 'title']].join(year_df)
        return final
    # ==============================================================

    st.markdown("")
    st.write("Проанализируем среднюю оценку книг выбранного писателя в течение времени.")
    author_eng = df[df['language_code']=='eng']
    select1 = st.selectbox('Выберите зарубежного автора', options=[opt for opt in author_eng['authors'].unique()]) 

    if st.button("Посчитать оценку"):
        author_df = df[df['authors']==select1]
        plot_author_chart(author_df, select1)

    st.markdown("")
    st.write("Топ наиболее оцениваемых авторов (средняя оценка которых > 4.3)")
    author_num = st.slider('Какое количество авторов необходимо вывести?', 1, 20, 10)
    high_rated_author = df[df['average_rating']>=4.3]
    high_rated_author = high_rated_author.groupby('authors')['title'].count().reset_index().sort_values('title', ascending = False).head(author_num).set_index('authors')
    fig6 = plt.figure(figsize=(8,4))
    sns.set_context('paper')
    ax = sns.barplot(high_rated_author['title'], high_rated_author.index, palette='Set2')
    plt.xlabel('Количество книг')
    plt.ylabel('Авторы')
    plt.title('Топ 10 наиболее оцениваемых авторов')
    for i in ax.patches:
        ax.text(i.get_width()+.3, i.get_y()+0.5, str(round(i.get_width())), fontsize = 10, color = 'k')
    st.pyplot(fig6)


    st.markdown("")
    st.write("Распределение оценок книг")
    # Замена Null на 0 
    df.dropna(0, inplace=True) 
    fig7 = plt.figure(figsize=(8,8))
    rating= df.average_rating.astype(float)
    sns.distplot(rating, bins=20)
    st.pyplot(fig7)

    """
    Выводы:
    * Большинство книг имеет рейтинг 3.7-4.3
    * Очень мало книг с рейтингом 5 
    """

    st.markdown("")
    radio1 = st.radio(
        "Ограничить число рецензий до 5000",
        ('нет', 'да'))
    fig8 = plt.figure(figsize=(8,4))
    if radio1 == 'нет':
        fig8 = px.scatter(df, x="average_rating", y="text_reviews_count", marginal_x="histogram", marginal_y="histogram", title='Зависимость между рейтингом и количеством рецензий')
        fig8.update_layout(xaxis_title='Средняя оценка', yaxis_title='Количество рецензий')
        st.plotly_chart(fig8)
        st.write("Из графика видно, что большая часть рейтинга лежит в промежутке 3-4, при числе рецензий примерно 5000.")
    else:
        trial = df[~(df['text_reviews_count']>5000)]
        fig8 = px.scatter(trial, x="average_rating", y="text_reviews_count", marginal_x="histogram", marginal_y="histogram", title='Зависимость между рейтингом и количеством рецензий')
        fig8.update_layout(xaxis_title='Средняя оценка', yaxis_title='Количество рецензий')
        st.plotly_chart(fig8)
        st.write("Можно заметить, что большая часть рецензий находится ниже 1000. Возможно здесь и есть какая-либо зависимость, но кажется, что рецензии преобладают у книг с высоким рейтингом.")
    

    def bs_html(isbn):
        url = 'https://isbndb.com/book/'+str(isbn.iloc[0])
        html_page = urllib2.urlopen(url)
        soup = BeautifulSoup(html_page)
        return soup.find('object')['data']

    st.subheader('Выбор понравившейся книги.')
    select2 = st.selectbox('Выберите книгу, чтобы узнать ее стоимость', options=[opt for opt in author_eng['title'].unique()]) 
    if st.button("Найти"):
        author_df = df[df['title']==select2]
        price = bookdata_html(author_df)

        st.write(select2)
        col1, mid, col2 = st.columns([10,5,20])
        with col1:
            st.image(bs_html(author_df['isbn13']), width=100)
        with col2:
            st.write(price[0])

    st.subheader('А где библиотеки, чтобы взять книжку?')
    """
        Данные о библиотеках были получены с сайта data.mos.ru.
    """
    def response_to_dict(response_item):
        converter = {
            'Number': response_item['Number'],
            'CommonName': response_item['Cells']['CommonName'],
            'FullName': response_item['Cells']['FullName'],
            'ShortName': response_item['Cells']['ShortName'],
            'ChiefPhone': response_item['Cells']['OrgInfo'][0]['ChiefPhone'][0]['ChiefPhone'],
            'Address': response_item['Cells']['ObjectAddress'][0]['Address'],
            'ChiefName': response_item['Cells']['ChiefName'],
            'ChiefPosition': response_item['Cells']['ChiefPosition'],
            'AdmArea': response_item['Cells']['ObjectAddress'][0]['AdmArea'],
            'NumOfSeats': response_item['Cells']['NumOfSeats'],
            'Coordinates' : str(Point(response_item['Cells']['geoData']['coordinates'][0])),
        }                
        return converter

    library_dataset = []
    if library_dataset == []: 
        library_dataset = data_mos_ru_libraries()
        geo_dataset = []
        geo_dataset.extend([response_to_dict(i) for i in library_dataset])
        geo_pd_data_no_points = pd.DataFrame(geo_dataset)
        geo_pd_data = pd.DataFrame(geo_dataset)
        geo_pd_data['Coordinates'] = geopandas.GeoSeries.from_wkt(geo_pd_data['Coordinates'])
        geo_pd_data['NumOfSeats'] = geo_pd_data['NumOfSeats'].fillna(0)
        geo_pd_data['NumOfSeats'] = geo_pd_data['NumOfSeats'].astype(int)

        geo_pd_data_no_points['NumOfSeats'] = geo_pd_data_no_points['NumOfSeats'].fillna(0)
        geo_pd_data_no_points['NumOfSeats'] = geo_pd_data_no_points['NumOfSeats'].astype(int)
        
        st.write(geo_pd_data_no_points)
        

        lib_map = folium.Map(location=[55.75876, 37.62573], zoom_start=10)
        nl = '\n'
        for i in range(0, len(geo_pd_data)):
            folium.CircleMarker(
                location=list(geo_pd_data['Coordinates'].iloc[i].coords[0])[::-1],
                popup=f"Название: {geo_pd_data.iloc[i]['CommonName']} {nl} Адрес: {geo_pd_data.iloc[i]['Address']} {nl} Число посадочных мест: {geo_pd_data.iloc[i]['NumOfSeats']}",
                tooltip=geo_pd_data.iloc[i]['CommonName'],
                radius=1
            ).add_to(lib_map)

        folium_static(lib_map)