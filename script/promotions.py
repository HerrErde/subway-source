import json

input_file_path = "temp/gamedata/promotions.json"
output_file_path = "temp/upload/promotions_data.json"


def main():
    with open(input_file_path, "r", encoding="utf-8") as input_file:
        data = json.load(input_file)

    output_data = []
    promotions_data = data.get("promotions", {})

    promotions = promotions_data.values()

    for promotion in promotions:
        product_sales_ids = []
        for sale in promotion.get("productSales", []):
            product_id = sale.get("productID", {})
            if product_id:
                product_sales_ids.append(product_id)

        if product_sales_ids:
            output_data.append(
                {
                    "id": promotion.get("id", ""),
                    "productSales": product_sales_ids,
                }
            )

    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, indent=2)


if __name__ == "__main__":
    main()
