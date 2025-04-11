import json

input_file_path = "temp/gamedata/promotions.json"
output_file_path = "temp/upload/promotions_data.json"

with open(input_file_path, "r", encoding="utf-8") as input_file:
    data = json.load(input_file)

output_data = []
promotions_data = data.get("promotions", [])

for promotion in promotions_data:
    product_sales_ids = [
        sale.get("productID")
        for sale in promotion.get("productSales", [])
        if "productID" in sale
    ]

    if product_sales_ids:
        output_data.append(
            {
                "id": promotion.get("id", ""),
                "productSales": product_sales_ids,
            }
        )

with open(output_file_path, "w", encoding="utf-8") as output_file:
    json.dump(output_data, output_file, indent=2)
