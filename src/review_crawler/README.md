# ShopeeFood/Foody Review Crawler

Tool này crawl review cho một shop cụ thể từ danh sách link ShopeeFood.

1. Chọn shop từ `link_food_hcm.txt` bằng `--shop`, `--url` hoặc `--index`.
2. Chuyển ShopeeFood URL sang Foody review URL: `https://www.foody.vn/<city>/<shop>/binh-luan`.
3. Parse payload `initDataReviews` trong HTML.
4. Gọi thêm `/__get/Review/ResLoadMore` nếu cần nhiều review hơn.
5. Ghi output JSON và CSV vào `output/`.

## Run

```bash
python crawl_shop_reviews.py --shop "bun bo dat thanh" --limit 20
```

Test bằng link đầu tiên trong `link_food_hcm.txt`:

```bash
python crawl_shop_reviews.py --index 0 --limit 10
```

Hoặc truyền URL trực tiếp:

```bash
python crawl_shop_reviews.py --url "https://shopeefood.vn/ho-chi-minh/bun-bo-dat-thanh-shop-online" --limit 10
```

## Output

Script tạo 2 file:

- `output/reviews_<shop_slug>.json`
- `output/reviews_<shop_slug>.csv`

JSON gồm metadata shop, thông tin crawl và danh sách review đã normalize.
