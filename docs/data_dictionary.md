# Retail Sales Modern Data Lakehouse - Data Dictionary (Silver Layer)

## 1. Table: customers (Silver)

| Column Name     | Target Type (Polars) | Mandatory | Value Constraints                          | Standardization Rules |
|-----------------|----------------------|-----------|--------------------------------------------|-----------------------|
| customer_id     | pl.Utf8             | Yes       | Format: `CUST\d{5}`                        | Trim, Uppercase |
| customer_name   | pl.Utf8             | Yes       | Non-empty string                           | Trim, Title Case |
| email           | pl.Utf8             | Yes       | Valid email format                         | Trim, Lowercase |
| region          | pl.Utf8             | Yes       | `North`, `South`, `East`, `West`, `Central` | Trim, Title Case |
| created_at      | pl.Datetime         | Yes       | ISO 8601 format, past or current date      | Convert to UTC Datetime |

---

## 2. Table: products (Silver)

| Column Name    | Target Type (Polars) | Mandatory | Value Constraints                  | Standardization Rules |
|----------------|----------------------|-----------|------------------------------------|-----------------------|
| product_id     | pl.Utf8             | Yes       | Format: `PROD\d{4}`                | Trim, Uppercase |
| product_name   | pl.Utf8             | Yes       | Non-empty string                   | Trim |
| category       | pl.Utf8             | Yes       | `Electronics`, `Fashion`, `Home`, `Beauty`, `Sports`, `Food`, `Books` | Trim, Title Case |
| unit_cost      | pl.Float64          | Yes       | `> 0`                              | Round to 2 decimal places |

---

## 3. Table: sales (Silver)

| Column Name     | Target Type (Polars) | Mandatory | Value Constraints                          | Standardization Rules |
|-----------------|----------------------|-----------|--------------------------------------------|-----------------------|
| sale_id         | pl.Utf8             | Yes       | Format: `SALE\d{6}`                        | Trim, Uppercase |
| sale_date       | pl.Date             | Yes       | Valid date, range 2025-01-01 ~ 2026-12-31 | Convert to Date |
| customer_id     | pl.Utf8             | Yes       | Must exist in customers table              | Trim, Uppercase |
| product_id      | pl.Utf8             | Yes       | Must exist in products table               | Trim, Uppercase |
| store_id        | pl.Utf8             | Yes       | Format: `STORE0[1-9]`                      | Trim, Uppercase |
| quantity        | pl.Int32            | Yes       | `>= 1`                                     | Convert to Integer |
| unit_price      | pl.Float64          | Yes       | `> 0`                                      | Round to 2 decimal places |

---

**Ghi chú chung cho Silver Layer:**

- Tất cả các cột ID (Primary & Foreign Keys) là **Mandatory = Yes**.
- Các record vi phạm Mandatory hoặc Value Constraints sẽ được chuyển vào `silver_rejected`.
- Toàn bộ Standardization Rules sẽ được thực thi trước khi chạy Data Quality Validation (Great Expectations).