# ShipHero Authentication Reference

## Table of Contents
1. [Getting Access Tokens](#getting-access-tokens)
2. [Token Refresh](#token-refresh)
3. [Making Authenticated Requests](#making-authenticated-requests)
4. [3PL Authentication](#3pl-authentication)
5. [Error Handling](#error-handling)

## Getting Access Tokens

### Token Request
```bash
curl -X POST https://public-api.shiphero.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

### Response
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 2419200
}
```

**Token Expiry:** Access tokens expire every 28 days (2,419,200 seconds).

## Token Refresh

### Refresh Request
```bash
curl -X POST https://public-api.shiphero.com/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### Python Token Manager
```python
import requests
from datetime import datetime, timedelta

class ShipHeroAuth:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def authenticate(self):
        response = requests.post(
            "https://public-api.shiphero.com/auth/token",
            json={"email": self.email, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 3600)

    def refresh(self):
        response = requests.post(
            "https://public-api.shiphero.com/auth/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 3600)

    def get_token(self) -> str:
        if not self.access_token:
            self.authenticate()
        elif datetime.now() >= self.expires_at:
            self.refresh()
        return self.access_token
```

## Making Authenticated Requests

### Python with gql
```python
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(
    url="https://public-api.shiphero.com/graphql",
    headers={"Authorization": f"Bearer {access_token}"}
)

client = Client(transport=transport, fetch_schema_from_transport=False)

query = gql("""
    query {
        products {
            data(first: 10) {
                edges {
                    node {
                        id
                        sku
                    }
                }
            }
        }
    }
""")

result = client.execute(query)
```

### JavaScript with graphql-request
```javascript
import { GraphQLClient } from 'graphql-request';

const client = new GraphQLClient('https://public-api.shiphero.com/graphql', {
    headers: {
        Authorization: `Bearer ${accessToken}`,
    },
});

const query = `
    query {
        products {
            data(first: 10) {
                edges {
                    node {
                        id
                        sku
                    }
                }
            }
        }
    }
`;

const data = await client.request(query);
```

### cURL
```bash
curl -X POST https://public-api.shiphero.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "{ products { data(first: 10) { edges { node { id sku } } } } }"
  }'
```

## 3PL Authentication

### Option 1: Customer Token
Request a customer-specific token for their account access.

### Option 2: Customer Account ID Parameter
Use your 3PL credentials with `customer_account_id`:

**For Queries:**
```graphql
query {
  orders(customer_account_id: "CUSTOMER_UUID") {
    data(first: 25) {
      edges {
        node {
          id
          order_number
        }
      }
    }
  }
}
```

**For Mutations:**
```graphql
mutation {
  order_create(
    data: {
      customer_account_id: "CUSTOMER_UUID"
      order_number: "ORD-12345"
      shop_name: "customer-shop"
      line_items: [...]
    }
  ) {
    order {
      id
    }
  }
}
```

## Error Handling

### Common Error Codes
| Code | Description |
|------|-------------|
| 1 | Cancelled |
| 2 | Unknown |
| 3 | Invalid Argument |
| 4 | Deadline Exceeded |
| 5 | Not Found |
| 7 | Permission Denied |
| 13 | Internal Error |
| 16 | Unauthenticated |

### Error Response Example
```json
{
    "errors": [
        {
            "message": "Token expired",
            "extensions": {
                "code": 16
            }
        }
    ]
}
```

### Retry Logic
```python
import time
from functools import wraps

def retry_on_auth_error(max_retries=3):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except AuthenticationError:
                    if attempt < max_retries - 1:
                        self.auth.refresh()
                        time.sleep(1)
                    else:
                        raise
            return None
        return wrapper
    return decorator
```
