import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define the path to the products.json file
DATA_FILE = Path(__file__).parent / "data" / "products.json"

@app.get("/product")
async def get_products():
    """
    Retrieve product information (ID and Name) from the JSON file.
    """
    if not DATA_FILE.exists():
        return {"error": "Product data not found"}
    
    with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
        products = json.load(f)
    
    # Extract only id and name
    result = [
        {
            "id": product.get("productId"), 
            "name": product.get("productName")
        }
        for product in products
    ]
    
    return result

@app.get("/product/{product_id}")
async def lookup_product_info(
        product_id: str,
    ):
        """Look up product information for a given product id.
        
        Args:
            product_id: The name of the product to look up information for.
        """
        if not DATA_FILE.exists():
            print('ERROR: File not found!')
            return {"error": "Product data not found"}
        
        with open(DATA_FILE, "r", encoding="utf-8-sig") as f:
            products = json.load(f)
            
        matches = [p for p in products if p["productId"] == product_id]
        
        if not matches:
            return {"error": "No products found!"}
            
        result = matches[0]
        print("RESULT: ", result)
        
        return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
