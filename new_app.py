import os
import numpy as np
import pandas as pd
import streamlit as st


def data_preprocess(data):
    #data clearing
    if data["Lost profit"].dtype == "object":
        data["Lost profit"] = data["Lost profit"].str.replace(",",".")
    data["Lost profit"] = data["Lost profit"].astype(float)
    
    #division by subcategoeies
    data["Category"] = data["Category"].str.split("/").str[2]
    data = data[data["Category"].notnull()] #delete empty ones
    return data
    
def top_niches_rps(data):
    df = data
    
    #calculate revenue and RPS for niches
    proxy_data = df.groupby("Category", as_index = False).agg({"Revenue": "sum", "SKU": "count"}).sort_values(by = "Revenue", ascending = False)
    proxy_data = proxy_data[proxy_data["Revenue"]>0]
    proxy_data["Revenue Per SKU"] = proxy_data["Revenue"]/proxy_data["SKU"]
    proxy_data = proxy_data[["Category", "Revenue", "Revenue Per SKU"]]
    
    #normalising for analysis
    r_m = proxy_data["Revenue"].mean()
    r_std = proxy_data["Revenue"].std()
    
    rps_m = proxy_data["Revenue Per SKU"].mean()
    rps_std = proxy_data["Revenue Per SKU"].std()
    
    
    proxy_data["Revenue"] = (proxy_data["Revenue"]-r_m)/r_std
    proxy_data["Revenue Per SKU"] = (proxy_data["Revenue Per SKU"]-rps_m)/rps_std

    proxy_data["Score"] = proxy_data["Revenue"]+proxy_data["Revenue Per SKU"]
    proxy_data = proxy_data.sort_values(by = "Score", ascending = False).head(10)
    
    return proxy_data

def data_category_preprocess(data):
    #data clearing
    if data["Lost profit"].dtype == "object":
        data["Lost profit"] = data["Lost profit"].str.replace(",",".")
    
    data["Lost profit"] = data["Lost profit"].astype(float)

    #create new columns

    #вспомогательные столбцы
    data["Price rank"] = data["Final price"].rank(ascending = 1)/data.shape[0]
    data["Cumulative revenue"] = np.cumsum(data["Revenue"])

    #добавляем столбцы
    data["Group A"] = data["Cumulative revenue"].apply(lambda x: 1 if x/data["Revenue"].sum()<0.8 else 0)
    data["Price range"] = data["Price rank"].apply(lambda x: "Эконом" if x < 0.11 else ("Эконом+" if x<0.22 else("Средний-" if x < 0.33 else("Средний" if x < 0.44 else("Средний+" if x < 0.55 else("Бизнес-" if x < 0.66 else("Бизнес" if x < 0.77 else("Бизнес+" if x < 0.88 else "Люкс"))))))))

    return data

def price_segmentation(data):
  #ranges list
  ranges = ["Эконом", "Эконом+","Средний-","Средний","Средний+","Бизнес-","Бизнес","Бизнес+","Люкс"]

  #lists
  diapazon = []
  mean_price = []
  overall_share = []
  sku = []
  revenue_per_sku = []
  sku_with_sales = []
  percent_sku_with_sales = []
  sku_over1m = []
  percent_sku_over1m = []
  sales = []
  sales_over1m = []
  share_sales_over1m = []
  revenue = []
  revenue_over1m = []
  share_revenue_over1m = []
  lost_profit = []
  share_lost_profit = []
  group_a = []
  share_group_a = []

  #append information to lists
  for Range in ranges:
      df = data[data["Price range"] == Range]
      diapazon.append(str(df["Final price"].min())+'-'+str(df["Final price"].max()))
      mean_price.append(round(np.median(df["Final price"])))
      overall_share.append(round(df["Revenue"].sum()/data["Revenue"].sum()*100))
      sku.append(df.shape[0])
      revenue_per_sku.append(round(df["Revenue"].sum()/df.shape[0]))
      sku_with_sales.append(df[df["Sales"]>1].shape[0])
      percent_sku_with_sales.append(round(df[df["Sales"]>1].shape[0]/df.shape[0]*100))
      sku_over1m.append(df[df["Revenue"]>1000000].shape[0])
      sales.append(df["Sales"].sum())
      sales_over1m.append(df[df["Revenue"]>1000000]["Sales"].sum())
      share_sales_over1m.append(round(df[df["Revenue"]>1000000]["Sales"].sum()*100/df["Sales"].sum()))
      revenue.append(df["Revenue"].sum())
      revenue_over1m.append(df[df["Revenue"]>1000000]["Revenue"].sum())
      share_revenue_over1m.append(round(df[df["Revenue"]>1000000]["Revenue"].sum()*100/df["Revenue"].sum()))
      lost_profit.append(round(df["Lost profit"].sum()))
      share_lost_profit.append(round(df["Lost profit"].sum()/df["Revenue"].sum()*100))
      group_a.append(df["Group A"].sum())
      share_group_a.append(df["Group A"].sum()/df.shape[0]*100)

  #create df
  final_ps = pd.DataFrame({"Диапазон": diapazon,"Ценовой сегмент": ranges, "Средняя цена": mean_price, "Доля в ТО": overall_share, "SKU всего": sku, "SKU с продажами >1млн" : sku_over1m,
                                 "Выручка на SKU": revenue_per_sku, "SKU с продажами": sku_with_sales, "% SKU с продажами": percent_sku_with_sales,
                                "Продажи": sales, "Продажи SKU >1млн": sales_over1m, "Доля продаж SKU >1млн": share_sales_over1m,
                                "Выручка": revenue, "Выручка SKU >1млн": revenue_over1m, "Доля выручки SKU >1млн": share_revenue_over1m,
                                "Упущенная выручка": lost_profit, "Доля упущенной выручки": share_lost_profit, "Товаров группы А": group_a,
                                "Доля товаров группы А": share_group_a})
  final_ps["Коэффициент"] = final_ps["Доля товаров группы А"]*final_ps["Выручка"]*final_ps["% SKU с продажами"]*final_ps["Упущенная выручка"]*final_ps["SKU с продажами >1млн"]*final_ps["Доля продаж SKU >1млн"]/1000000000000000000

  #return df
  return final_ps


def goods_list(Range_name, data):
  #фильтр
  #t = t.sort_values(by = "Коэффициент", ascending = False)
  #df = data[data["Price range"] == t.iloc[0]["Ценовой сегмент"]]
  df = data[data["Price range"] == Range_name]
  proxy_df = df[["Name", "SKU", "Category", "Brand", "Seller", "Median price", "Sales", "Revenue", "Price range", "Lost profit", "Days with sales", "First Date"]]
  proxy_df["URL"] = proxy_df["SKU"].apply(lambda x: "https://www.wildberries.ru/catalog/"+str(x)+"/detail.aspx?targetUrl=SP")
  return proxy_df[:10]
    
def quantity_estimate(Range_name, data):
    sales, revenue, sku_count, sales_per_sku, revenue_per_sku, quantity = [], [], [], [], [], []
    #t = t.sort_values(by = "Коэффициент", ascending = False)
    #df = data[data["Price range"] == t.iloc[0]["Ценовой сегмент"]]
    df = data[data["Price range"] == Range_name]
    df["Cumulative revenue"] = np.cumsum(df["Revenue"])
    df["Group A"] = df["Cumulative revenue"].apply(lambda x: 1 if x/df["Revenue"].sum()<0.8 else 0)
    sales.append(df[df["Group A"] == 1]["Sales"].sum())
    revenue.append(df[df["Group A"] == 1]["Revenue"].sum())
    sku_count.append(df[df["Group A"] == 1].shape[0])
    qe_df = pd.DataFrame({"Количество продаж конкурентов": sales, "Выручка конкурентов": revenue, "Количество SKU": sku_count})
    qe_df["Продажи на SKU/шт."] = qe_df["Количество продаж конкурентов"]/qe_df["Количество SKU"]
    qe_df["Выручка на SKU"] = qe_df["Выручка конкурентов"]/qe_df["Количество SKU"]
    qe_df["Количество к закупке"] = round(qe_df["Количество продаж конкурентов"]/qe_df["Количество SKU"], -2)
    return qe_df
    
def analisys(data, Range_name, Category_name):
  t = price_segmentation(data_category_preprocess(data[data["Category"] == Category_name"]))
  csv_file1 = t
  g = goods_list(Range_name, data)
  csv_file2 = g
  qe = quantity_estimate(Range_name, data)
  csv_file3 = qe  
  return csv_file1, csv_file2, csv_file3


st.title("Аналитический отчет")
# Create a file uploader  
uploaded_file = st.file_uploader("Select a CSV file", type=["csv"])
if uploaded_file is not None:
    df_from_file = pd.read_csv(uploaded_file, sep = ";")
    df_from_file = data_preprocess(df_from_file)
    
    z = top_niches_rps(df_from_file)
    st.write(z)
    
    st.scatter_chart(z.head(6), x = "Revenue Per SKU", y = "Revenue", color = "Category", size = "Score")
    niche = sorted(list(df_from_file.Category.unique()))   
    category_filter = niche[0]
    category_filter = st.selectbox('Select a category', niche)
    
    #df_from_file = df_from_file[df_from_file["Category"] == category_filter]
    
    
    #Niche Analysis
    Range_name = "Эконом"
    Range_name = st.selectbox(
    "Выберите ценовой сегмент",
    ("Эконом", "Эконом+", "Средний-", "Средний", "Средний+", "Бизнес-", "Бизнес","Бизнес+","Люкс"))
  #file_contents = uploaded_file.read()
  #Range_name = st.selectbox(
  #"Выберите ценовой сегмент",
  #("Эконом", "Эконом+", "Средний-", "Средний", "Средний+", "Бизнес-", "Бизнес","Бизнес+","Люкс"))  
    
  # Process the uploaded file
    csv_file1, csv_file2, csv_file3 = analisys(df_from_file, Range_name, category_filter)
    
  # Display the output CSV files
    st.write("Ниже можно скачать крутые таблички :wolf: ")
    st.write("Анализ ценовых сегментов:")
    st.write(csv_file1)  
    st.write("Список топовых товаров в лучшем ценовом сегменте:")
    st.write(csv_file2)
    st.write("Примерный расчет закупки партии на WB на рассматриваемый период")
    st.write(csv_file3)
if uploaded_file is None:
    st.write("Загрузи файл, проверь, чтобы в нем были следующие столбцы :wolf:")
    st.write("Name, SKU, Category, Brand, Seller, Median price, Sales, Revenue, Lost profit, Days with sales, First Date, Final price")
    st.write("Без них скрипт работать не будет")
    
