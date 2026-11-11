import pandas as pd
import os
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:0987@localhost:5432/olist_db')
folder_path = 'D:/my_dataset/olist'

for filename in os.listdir(folder_path):
    if filename.endswith('.csv'):
        file_path = os.path.join(folder_path, filename)

        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='latin1')

        table_name = filename.replace('.csv', '')

        print(f"Загрузка {filename} в таблицу {table_name}...")
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        print(f"Готово. Строк: {len(df)}")

print('Файлы загружены')
