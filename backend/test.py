from pathlib import Path
import requests
import json

DATA_FILE = Path(__file__).parent / "data" / "products.json"

def get_all_product_names_and_id(

    ):
        """Get all product names and ids in the database."""

        products = requests.get('http://localhost:8000/product')
        print(products.json())

print(get_all_product_names_and_id())