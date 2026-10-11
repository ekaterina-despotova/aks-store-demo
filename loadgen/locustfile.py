import random
from locust import HttpUser, task, constant

ORDER_SVC    = "http://order-service.pets:3000"
PRODUCT_SVC  = "http://product-service.pets:3002"
MAKELINE_SVC = "http://makeline-service.pets:3001"

def random_order():
    n = random.randint(1, 4)
    items = []
    for _ in range(n):
        items.append({
            "productId": random.randint(1, 10),
            "quantity": random.randint(1, 5),
            "price": round(random.uniform(5, 100), 2),
        })
    return {"customerId": str(random.randint(1_000_000_000, 2_000_000_000)), "items": items}

class StoreUser(HttpUser):
    host = ORDER_SVC
    wait_time = constant(0)

    @task(5)
    def submit_order(self):
        self.client.post(f"{ORDER_SVC}/", json=random_order(), name="order:POST /")



    @task(4)
    def list_products(self):
        self.client.get(f"{PRODUCT_SVC}/", name="product:GET /")

    @task(5)
    def process_orders(self):
        with self.client.get(f"{MAKELINE_SVC}/order/fetch",
                             name="makeline:GET /order/fetch",
                             catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"fetch status {resp.status_code}")
                return
            body = (resp.text or "").strip()
            if not body or body == "null":
                return
            try:
                orders = resp.json()
            except Exception:
                resp.failure("fetch: invalid JSON")
                return

        if not isinstance(orders, list):
            return
        for order in orders:
            order["status"] = 1
            self.client.put(f"{MAKELINE_SVC}/order",
                            json=order,
                            name="makeline:PUT /order")
