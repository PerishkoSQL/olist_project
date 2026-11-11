import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine

# Настройка стиля графиков
sns.set_theme(style="darkgrid")
engine = create_engine('postgresql://postgres:0987@localhost:5432/olist_db')

print("=== ЗАГРУЗКА ДАННЫХ ===")

# 1. Загрузка данных для RFM
query_rfm = """
select ocd.customer_unique_id,
       (select max(order_purchase_timestamp)::date from olist_orders_dataset) - max(ood.order_purchase_timestamp)::date as recency_days,
       count(distinct ood.order_id) as frequency,
       sum(oopd.payment_value) as monetary
from olist_orders_dataset ood
join olist_customers_dataset ocd using(customer_id)
join olist_order_payments_dataset oopd using(order_id)
group by 1
"""
df_rfm = pd.read_sql(query_rfm, engine)

# 2. Загрузка данных для анализа доставки
query_delivery = """
select ocd.customer_state,
       count(*) as total_orders,
       round(avg(ord.order_delivered_customer_date::date - ord.order_purchase_timestamp::date), 2) as avg_delivery_days,
       round(avg(oor.review_score), 2) as avg_review_score
from olist_orders_dataset ord
join olist_customers_dataset ocd using(customer_id)
join olist_order_reviews_dataset oor using(order_id)
where ord.order_status = 'delivered'
group by 1
"""
df_delivery = pd.read_sql(query_delivery, engine)

# 3. Загрузка данных для качества продукции
query_quality = """
select coalesce(p.product_category_name, 'no_category_name') as product_category_name,
       count(*) as orders_count,
       round(avg(r.review_score), 2) as avg_review,
       round(100.0 * count(*) filter (where r.review_score <= 2) / count(*), 2) as fraction_negative_reviews
from olist_order_items_dataset o
join olist_products_dataset p using(product_id)
join olist_order_reviews_dataset r using(order_id)
group by 1
having count(*) > 50
order by fraction_negative_reviews desc
limit 10
"""
df_quality = pd.read_sql(query_quality, engine)

print("Данные загружены!")


print("\n=== АНАЛИЗ 1: RFM-СЕГМЕНТАЦИЯ ===")
# Скоринг
df_rfm['R_score'] = pd.qcut(df_rfm['recency_days'], q=4, labels=[4, 3, 2, 1])
df_rfm['F_score'] = pd.qcut(df_rfm['frequency'].rank(method='first'), q=4, labels=[1, 2, 3, 4])
df_rfm['M_score'] = pd.qcut(df_rfm['monetary'], q=4, labels=[1, 2, 3, 4])

# Сегментация (Путь 2: по R и M)
conditions = [
    (df_rfm['R_score'].astype(int) >= 3) & (df_rfm['M_score'].astype(int) >= 3),
    (df_rfm['R_score'].astype(int) <= 2) & (df_rfm['M_score'].astype(int) >= 3),
    (df_rfm['R_score'].astype(int) >= 3) & (df_rfm['M_score'].astype(int) <= 2),
    (df_rfm['R_score'].astype(int) <= 2) & (df_rfm['M_score'].astype(int) <= 2)
]
choices = ['VIP', 'Золотые', 'Перспективные', 'Спящие']
df_rfm['segment_name'] = np.select(conditions, choices, default='Спящие')

# Вывод
rfm_revenue = df_rfm.groupby('segment_name')['monetary'].sum().sort_values(ascending=False)
print("Выручка по сегментам:\n", rfm_revenue)


print("\n=== АНАЛИЗ 2: ДОСТАВКА ===")
print(df_delivery.sort_values('avg_delivery_days', ascending=False).head())


print("\n=== АНАЛИЗ 3: КАЧЕСТВО ===")
print(df_quality)


print("\n=== ВИЗУАЛИЗАЦИЯ ===")
# Создаем фигуру с 3 графиками в ряд
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# 1. Выручка по сегментам
sns.barplot(x=rfm_revenue.index, y=rfm_revenue.values, palette='viridis', ax=axes[0])
axes[0].set_title('Выручка по сегментам (RFM)', fontsize=14)
axes[0].set_ylabel('Выручка (млн)')
axes[0].bar_label(axes[0].containers[0], fmt='%.0f') # Подписи данных

# 2. Зависимость оценки от доставки
sns.scatterplot(data=df_delivery, x='avg_delivery_days', y='avg_review_score', size='total_orders', sizes=(20, 200), ax=axes[1])
sns.regplot(data=df_delivery, x='avg_delivery_days', y='avg_review_score', scatter=False, color='red', ax=axes[1])
axes[1].set_title('Влияние доставки на оценку', fontsize=14)
axes[1].set_xlabel('Среднее время доставки (дни)')
axes[1].set_ylabel('Средняя оценка')

# 3. Топ плохих категорий
sns.barplot(data=df_quality, y='product_category_name', x='fraction_negative_reviews', palette='Reds_r', ax=axes[2])
axes[2].set_title('Топ-10 категорий с плохими отзывами', fontsize=14)
axes[2].set_xlabel('% плохих отзывов')
axes[2].set_ylabel('')

plt.tight_layout()
plt.show()
print("Скрипт завершен успешно!")