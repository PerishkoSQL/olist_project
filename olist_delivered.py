import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

engine = create_engine('postgresql://postgres:0987@localhost:5432/olist_db')
query = '''select ocd.customer_state,
	   count(*) as total_orders,
	   round(avg(ord.order_delivered_customer_date::date - ord.order_purchase_timestamp::date), 2) as avg_delivery_days,
	   avg(oord.review_score) as avg_review_score
from olist_orders_dataset ord
join olist_customers_dataset ocd using(customer_id)
join olist_order_reviews_dataset oord using(order_id)
where ord.order_status = 'delivered'
group by 1
order by 3 desc'''

df = pd.read_sql(query, engine)

plt.figure(figsize=(10,6))
sns.scatterplot(data=df, x='avg_delivery_days', y='avg_review_score', size='total_orders', sizes=(20, 200))
sns.regplot(data=df, x='avg_delivery_days', y='avg_review_score', scatter=False, color='red')

plt.title('Зависимость оценки от времени доставки по штатам')
plt.xlabel('Среднее время доставки (дни)')
plt.ylabel('Средняя оценка')
plt.tight_layout()
plt.show()