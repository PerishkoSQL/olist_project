import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
sns.set_theme(style='darkgrid')

engine = create_engine('postgresql://postgres:0987@localhost:5432/olist_db')
query = '''
select ocd.customer_unique_id,
	   (select max(order_purchase_timestamp)::date from olist_orders_dataset) - max(ood.order_purchase_timestamp)::date as recency_days,
	   count(distinct ood.order_id) as frequency,
	   sum(oopd.payment_value) as monetary
from olist_orders_dataset ood
join olist_customers_dataset ocd using(customer_id)
join olist_order_payments_dataset oopd using(order_id)
group by 1
'''

df = pd.read_sql(query, engine)

df['R_score'] = pd.qcut(df['recency_days'], q=4, labels=[4, 3, 2, 1])
df['F_score'] = pd.qcut(df['frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4])
df['M_score'] = pd.qcut(df['monetary'], q=4, labels=[1, 2, 3, 4])

conditions = [
    (df['R_score'].astype(int) >= 3) & (df['M_score'].astype(int) >= 3),
    (df['R_score'].astype(int) <= 2) & (df['M_score'].astype(int) >= 3),
    (df['R_score'].astype(int) >= 3) & (df['M_score'].astype(int) <= 2),
    (df['R_score'].astype(int) <= 2) & (df['M_score'].astype(int) <= 2)
]

choices = ['VIP', 'Дорогие', 'Перспективные', 'Спящие']

df['segment_name'] = np.select(conditions, choices,  default='Спящие')

revenue = df.groupby('segment_name')['monetary'].sum().sort_values(ascending=False)
plt.figure(figsize=(10,6))
sns.barplot(x=revenue.index, y=revenue.values, palette='viridis')
plt.title('Выручка по сегментам (в реалах)', fontsize=16)
plt.xlabel('Сегмент', fontsize=12)
plt.ylabel('Сумма', fontsize=12)

for i, v in enumerate(revenue.values):
    plt.text(i, v + 100000, f'{v/1000000:.1f} млн', ha='center', fontsize=11)

plt.figure(figsize=(8, 8))

color_map = {
    'VIP': "#4873e9b5",
    'Дорогие': "#94cdeeda",
    'Перспективные': "#95f395ee",
    'Спящие': '#dfedf7'
}
counts = df['segment_name'].value_counts()
color_list = [color_map[segment] for segment in counts.index]
plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%', counterclock=False, startangle=90, colors=color_list)
plt.title('Распределение клиентов по сегментам', fontsize=14)

plt.tight_layout()
plt.show()
