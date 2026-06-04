Retail Sales Modern Data Lakehouse
📝 Giới thiệu Dự án
Dự án Retail Sales Modern Data Lakehouse là một giải pháp xử lý dữ liệu hiện đại, mô phỏng quy trình xử lý dữ liệu bán lẻ thực tế (Retail Sales) tại doanh nghiệp. Dự án tập trung vào việc xây dựng một pipeline dữ liệu bền vững, tự động hóa và có khả năng mở rộng, tuân thủ kiến trúc Medallion Architecture (Bronze -> Silver -> Gold).

🏗️ Kiến trúc Hệ thống (Architecture)
Hệ thống kết hợp sự linh hoạt của Python (Polars) với sức mạnh phân tích của SQL (dbt + DuckDB):

Bronze Layer (Ingestion): Nhận dữ liệu thô (Raw CSV), lưu trữ dưới dạng Parquet partitioned theo thời gian.

Silver Layer (Cleaning & Quality): Làm sạch, chuẩn hóa kiểu dữ liệu, xóa trùng lặp và chặn dữ liệu "rác" bằng cơ chế rejected_records.

Gold Layer (Dimensional Modeling): Xây dựng mô hình Star Schema (Fact & Dimensions) hỗ trợ BI hiệu quả.

🛠️ Công nghệ sử dụng (Tech Stack)
Pipeline Engine: Python (Polars - High performance processing).

Data Warehouse: DuckDB (OLAP analytical engine).

Transformation: dbt (data build tool) để quản lý mô hình dữ liệu SQL.

Orchestration: Custom Python Orchestrator kết hợp Typer CLI.

Quality Control: Great Expectations & dbt Tests.

Dependency Management: uv (Modern Python package manager).

🚀 Tính năng nổi bật
Sandbox Isolation: Pipeline hỗ trợ chạy song song môi trường sample (để test nhanh) và production (để chạy dữ liệu lớn) mà không làm rác ổ cứng.

Data Contract: Thiết lập chặt chẽ các luật Unique, Not Null và Relationships thông qua schema.yml.

Observability: Tích hợp structlog xuất log định dạng JSON phục vụ hệ thống giám sát.

Idempotency: Pipeline được thiết kế để có thể chạy lại bất kỳ lúc nào mà không gây trùng lặp dữ liệu.

💻 Hướng dẫn sử dụng nhanh

### 1) Cài đặt (local)
```bash
uv sync
```

### 2) Khởi tạo cấu trúc thư mục
```bash
uv run python CLI.py init
```

### 3) Chạy pipeline
- **Sample (nhanh để test):**
```bash
uv run python CLI.py run --env sample
```
- **Production (full):**
```bash
uv run python CLI.py run --env production
```

### 4) Chạy riêng từng bước
```bash
# Bronze
uv run python CLI.py bronze --mode sample --env sample

# Silver
uv run python CLI.py transform --env sample

# Gold (dbt) được chạy trong pipeline.run
```

### 5) Docker (khuyến nghị)
```bash
docker compose --profile sample up --build
```

## Tích hợp dbt Snapshot cho Gold Layer
Gold (`marts`) phụ thuộc vào các snapshot `snp_*`. Pipeline đã được nâng cấp để chạy trước khi build marts:
1) `dbt snapshot --select snp_*`
2) `dbt run --select +marts`

đảm bảo relation snapshot tồn tại trước khi tạo dim/fact.

📊 Mô hình Star Schema
(Tại đây, sau khi bạn sinh file sơ đồ ER, hãy chèn hình ảnh sơ đồ tại đây)

📈 Kết quả Kiểm định (Quality Assurance)
- **Data Coverage:** đảm bảo toàn vẹn tham chiếu giữa Fact và Dimensions.
- **Testing:** sử dụng `pytest` (Unit/Integration) và `dbt test` (data quality).
- **Logs:** ghi nhận mọi biến động qua `logs/pipeline.log`.

Dự án này được phát triển như một ví dụ thực chiến về Modern Data Stack trong ngành bán lẻ.

