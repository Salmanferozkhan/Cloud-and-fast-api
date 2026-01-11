# ShipHero Webhooks Reference

## Table of Contents
1. [Available Webhook Types](#available-webhook-types)
2. [Webhook Registration](#webhook-registration)
3. [Webhook Verification](#webhook-verification)
4. [Response Requirements](#response-requirements)
5. [Best Practices](#best-practices)

## Available Webhook Types

| Webhook Name | Description |
|-------------|-------------|
| Inventory Update | Triggered when inventory levels change |
| Inventory Change | Triggered on inventory adjustments with details |
| Shipment Update | Triggered when shipment status changes |
| Automation Rules | Triggered by automation rule execution |
| Order Canceled | Triggered when an order is canceled |
| Capture Payment | Triggered for payment capture events |
| PO Update | Triggered when purchase order status changes |
| Return Update | Triggered when return status changes |
| Tote Complete | Triggered when a tote is completed |
| Tote Cleared | Triggered when a tote is cleared |
| Order Packed Out | Triggered when order packing is complete |
| Package Added | Triggered when a package is added to order |
| Print Barcode | Triggered for barcode printing events |
| Order Allocated | Triggered when inventory is allocated to order |
| Order Deallocated | Triggered when inventory allocation is removed |
| Shipment ASN | Triggered for Advanced Shipping Notice events |
| Generate Label | Triggered for label generation (20s timeout) |

## Webhook Registration

### Create Webhook
```graphql
mutation {
  webhook_create(
    data: {
      name: "Inventory Update"
      url: "https://your-endpoint.com/webhook"
      shop_name: "api"
    }
  ) {
    request_id
    webhook {
      id
      name
      url
      shared_signature_secret
    }
  }
}
```

**Important:** The `shared_signature_secret` is only displayed once upon creation. Store it securely.

### Delete Webhook
```graphql
mutation {
  webhook_delete(
    data: {
      id: "WEBHOOK_UUID"
    }
  ) {
    request_id
  }
}
```

### List Webhooks
```graphql
query {
  webhooks {
    request_id
    data(first: 50) {
      edges {
        node {
          id
          name
          url
          shop_name
        }
      }
    }
  }
}
```

### Multiple Webhooks of Same Type
Use different `shop_name` values to register multiple webhooks of the same type:
```graphql
mutation {
  webhook_create(
    data: {
      name: "Shipment Update"
      url: "https://endpoint-1.com/webhook"
      shop_name: "integration-1"
    }
  ) { ... }
}
```

## Webhook Verification

Verify webhook authenticity using HMAC-SHA256:

### Python
```python
import hmac
import hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# Usage
payload = request.body  # raw bytes
signature = request.headers.get("x-shiphero-hmac-sha256")
is_valid = verify_webhook(payload, signature, WEBHOOK_SECRET)
```

### Node.js
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(payload, 'utf8')
        .digest('hex');
    return crypto.timingSafeEqual(
        Buffer.from(expected),
        Buffer.from(signature)
    );
}
```

### Header Reference
- `x-shiphero-hmac-sha256`: HMAC signature for verification
- `X-Shiphero-Message-ID`: Unique message ID for deduplication

## Response Requirements

Webhooks expect a JSON response:
```json
{
    "code": "200",
    "Status": "Success"
}
```

### Timeouts
- Standard webhooks: 10 seconds with 5 retries
- Generate Label Webhook: 20 seconds

## Best Practices

### 1. Implement Idempotency
Use `X-Shiphero-Message-ID` for deduplication:
```python
def handle_webhook(request):
    message_id = request.headers.get("X-Shiphero-Message-ID")

    # Check if already processed
    if redis.exists(f"webhook:{message_id}"):
        return {"code": "200", "Status": "Success"}

    # Process webhook
    process_payload(request.json)

    # Mark as processed (TTL 24 hours)
    redis.setex(f"webhook:{message_id}", 86400, "1")

    return {"code": "200", "Status": "Success"}
```

### 2. Implement Reconciliation Jobs
Webhooks don't guarantee delivery timing. Use polling as backup:
```python
def reconcile_orders():
    """Run periodically to catch missed webhooks"""
    last_sync = get_last_sync_time()

    orders = query_orders(
        updated_at_min=last_sync,
        updated_at_max=datetime.now()
    )

    for order in orders:
        sync_order(order)

    save_last_sync_time(datetime.now())
```

### 3. Return Quickly
Process webhooks asynchronously:
```python
from celery import Celery

@app.route("/webhook", methods=["POST"])
def webhook_handler():
    # Verify signature first
    if not verify_webhook(request):
        return {"code": "401", "Status": "Unauthorized"}, 401

    # Queue for async processing
    process_webhook.delay(request.json)

    # Return immediately
    return {"code": "200", "Status": "Success"}

@celery.task
def process_webhook(payload):
    # Actual processing here
    ...
```

### 4. 3PL Account Webhooks
For 3PL accounts, register webhooks on the customer account, not the 3PL account.
