# Schémas lus par Spark

Types et nullabilité Parquet réellement observés. La nullabilité du schéma ne mesure pas le nombre de nulls ; voir qualite.json.

## store_sales

| Colonne | Type |
| --- | --- |
| ss_sold_date_sk | long |
| ss_sold_time_sk | long |
| ss_item_sk | long |
| ss_customer_sk | long |
| ss_cdemo_sk | long |
| ss_hdemo_sk | long |
| ss_addr_sk | long |
| ss_store_sk | long |
| ss_promo_sk | long |
| ss_ticket_number | long |
| ss_quantity | integer |
| ss_wholesale_cost | decimal(7,2) |
| ss_list_price | decimal(7,2) |
| ss_sales_price | decimal(7,2) |
| ss_ext_discount_amt | decimal(7,2) |
| ss_ext_sales_price | decimal(7,2) |
| ss_ext_wholesale_cost | decimal(7,2) |
| ss_ext_list_price | decimal(7,2) |
| ss_ext_tax | decimal(7,2) |
| ss_coupon_amt | decimal(7,2) |
| ss_net_paid | decimal(7,2) |
| ss_net_paid_inc_tax | decimal(7,2) |
| ss_net_profit | decimal(7,2) |
| _source_uri | string |
| _source_sha256 | string |
| _source_batch | string |
| _run_id | string |

## item

| Colonne | Type |
| --- | --- |
| i_item_sk | long |
| i_item_id | string |
| i_rec_start_date | date |
| i_rec_end_date | date |
| i_item_desc | string |
| i_current_price | decimal(7,2) |
| i_wholesale_cost | decimal(7,2) |
| i_brand_id | integer |
| i_brand | string |
| i_class_id | integer |
| i_class | string |
| i_category_id | integer |
| i_category | string |
| i_manufact_id | integer |
| i_manufact | string |
| i_size | string |
| i_formulation | string |
| i_color | string |
| i_units | string |
| i_container | string |
| i_manager_id | integer |
| i_product_name | string |
| _source_uri | string |
| _source_sha256 | string |
| _source_batch | string |
| _run_id | string |

## ventes_par_produit

| Colonne | Type |
| --- | --- |
| ss_item_sk | long |
| i_product_name | string |
| i_category | string |
| i_brand | string |
| quantity_sold | long |
| net_paid | decimal(17,2) |
| sales_line_count | long |
| _run_id | string |
| _source_sales_sha256 | string |
| _source_item_sha256 | string |
