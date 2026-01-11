# ShipHero GraphQL Operations Reference

## Table of Contents
1. [Order Operations](#order-operations)
2. [Product Operations](#product-operations)
3. [Inventory Management](#inventory-management)
4. [Shipment Operations](#shipment-operations)
5. [Return Operations](#return-operations)
6. [Purchase Orders](#purchase-orders)
7. [Pagination Patterns](#pagination-patterns)

## Order Operations

### Query Order
```graphql
query {
  order(id: "ORDER_UUID") {
    request_id
    complexity
    data {
      id
      order_number
      shop_name
      fulfillment_status
      order_date
      shipping_address {
        first_name
        last_name
        address1
        address2
        city
        state
        zip
        country
      }
      line_items(first: 50) {
        edges {
          node {
            id
            sku
            quantity
            product_name
            price
          }
        }
      }
      shipments {
        id
        tracking_number
        carrier
        created_at
      }
    }
  }
}
```

### Query Orders (with pagination)
```graphql
query {
  orders(
    shop_name: "my-shop"
    order_date_from: "2024-01-01"
    order_date_to: "2024-12-31"
    fulfillment_status: "pending"
  ) {
    request_id
    complexity
    data(first: 25) {
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        node {
          id
          order_number
          fulfillment_status
        }
      }
    }
  }
}
```

### Create Order
```graphql
mutation {
  order_create(
    data: {
      order_number: "ORD-12345"
      shop_name: "my-shop"
      fulfillment_status: "pending"
      order_date: "2024-01-15"
      shipping_address: {
        first_name: "John"
        last_name: "Doe"
        address1: "123 Main St"
        city: "New York"
        state: "NY"
        zip: "10001"
        country: "US"
      }
      line_items: [
        {
          sku: "SKU-001"
          quantity: 2
          price: "29.99"
          product_name: "Widget"
        }
      ]
    }
  ) {
    request_id
    complexity
    order {
      id
      order_number
    }
  }
}
```

### Update Order
```graphql
mutation {
  order_update(
    data: {
      order_id: "ORDER_UUID"
      priority_flag: true
      packing_note: "Handle with care"
      shipping_address: {
        first_name: "Jane"
        last_name: "Smith"
      }
    }
  ) {
    request_id
    order {
      id
      order_number
    }
  }
}
```

### Cancel Order
```graphql
mutation {
  order_cancel(
    data: {
      order_id: "ORDER_UUID"
      reason: "Customer requested cancellation"
    }
  ) {
    request_id
    order {
      id
      order_number
    }
  }
}
```

## Product Operations

### Query Product
```graphql
query {
  product(id: "PRODUCT_UUID") {
    request_id
    complexity
    data {
      id
      sku
      name
      price
      barcode
      dimensions {
        weight
        height
        width
        length
      }
      warehouse_products {
        warehouse_id
        on_hand
        allocated
        available
        reserve_inventory
        reorder_level
      }
    }
  }
}
```

### Query Products (with pagination)
```graphql
query {
  products(sku: "SKU-PREFIX") {
    request_id
    complexity
    data(first: 50) {
      pageInfo {
        hasNextPage
        endCursor
      }
      edges {
        node {
          id
          sku
          name
          warehouse_products {
            warehouse_id
            on_hand
          }
        }
      }
    }
  }
}
```

### Create Product
```graphql
mutation {
  product_create(
    data: {
      sku: "NEW-SKU-001"
      name: "New Product"
      price: "49.99"
      barcode: "1234567890123"
      dimensions: {
        weight: "1.5"
        height: "5"
        width: "3"
        length: "8"
      }
      warehouse_products: [
        {
          warehouse_id: "WAREHOUSE_UUID"
          on_hand: 100
          reorder_level: 20
        }
      ]
    }
  ) {
    request_id
    product {
      id
      sku
    }
  }
}
```

### Update Product
```graphql
mutation {
  product_update(
    data: {
      sku: "SKU-001"
      name: "Updated Product Name"
      price: "59.99"
    }
  ) {
    request_id
    product {
      id
      sku
    }
  }
}
```

## Inventory Management

### Add Inventory
```graphql
mutation {
  inventory_add(
    data: {
      sku: "SKU-001"
      warehouse_id: "WAREHOUSE_UUID"
      quantity: 50
      reason: "Restocking"
    }
  ) {
    request_id
    warehouse_product {
      on_hand
    }
  }
}
```

### Remove Inventory
```graphql
mutation {
  inventory_remove(
    data: {
      sku: "SKU-001"
      warehouse_id: "WAREHOUSE_UUID"
      quantity: 10
      reason: "Damaged goods"
    }
  ) {
    request_id
    warehouse_product {
      on_hand
    }
  }
}
```

### Query Warehouse Products
```graphql
query {
  warehouse_products(
    warehouse_id: "WAREHOUSE_UUID"
    sku: "SKU-PREFIX"
  ) {
    request_id
    complexity
    data(first: 100) {
      edges {
        node {
          id
          sku
          on_hand
          allocated
          available
          reserve_inventory
          reorder_level
        }
      }
    }
  }
}
```

### Query Inventory Changes
```graphql
query {
  inventory_changes(
    sku: "SKU-001"
    date_from: "2024-01-01"
    date_to: "2024-01-31"
  ) {
    request_id
    data(first: 50) {
      edges {
        node {
          sku
          previous_on_hand
          change_in_on_hand
          reason
          created_at
        }
      }
    }
  }
}
```

## Shipment Operations

### Query Shipment
```graphql
query {
  shipment(id: "SHIPMENT_UUID") {
    request_id
    data {
      id
      order_id
      tracking_number
      carrier
      shipping_method
      created_at
      line_items {
        sku
        quantity
      }
      address {
        first_name
        last_name
        address1
        city
        state
        zip
        country
      }
    }
  }
}
```

### Create Shipment
```graphql
mutation {
  shipment_create(
    data: {
      order_id: "ORDER_UUID"
      warehouse_id: "WAREHOUSE_UUID"
      address: {
        first_name: "John"
        last_name: "Doe"
        address1: "123 Main St"
        city: "New York"
        state: "NY"
        zip: "10001"
        country: "US"
      }
      line_items: [
        {
          sku: "SKU-001"
          quantity: 1
        }
      ]
    }
  ) {
    request_id
    shipment {
      id
      tracking_number
    }
  }
}
```

## Return Operations

### Create Return
```graphql
mutation {
  return_create(
    data: {
      order_id: "ORDER_UUID"
      warehouse_id: "WAREHOUSE_UUID"
      return_reason: "Defective product"
      label_type: "prepaid"
      shipping_carrier: "ups"
      line_items: [
        {
          sku: "SKU-001"
          quantity: 1
          reason: "Damaged"
        }
      ]
    }
  ) {
    request_id
    return {
      id
      status
    }
  }
}
```

### Query Return
```graphql
query {
  return(id: "RETURN_UUID") {
    request_id
    data {
      id
      order_id
      status
      return_reason
      created_at
      line_items {
        sku
        quantity
        reason
      }
    }
  }
}
```

## Purchase Orders

### Query Purchase Order
```graphql
query {
  purchase_order(id: "PO_UUID") {
    request_id
    data {
      id
      po_number
      vendor_id
      warehouse_id
      fulfillment_status
      po_date
      line_items {
        sku
        quantity
        price
        quantity_received
      }
    }
  }
}
```

### Create Purchase Order
```graphql
mutation {
  purchase_order_create(
    data: {
      po_number: "PO-2024-001"
      po_date: "2024-01-15"
      vendor_id: "VENDOR_UUID"
      warehouse_id: "WAREHOUSE_UUID"
      line_items: [
        {
          sku: "SKU-001"
          quantity: 100
          price: "10.00"
        }
      ]
    }
  ) {
    request_id
    purchase_order {
      id
      po_number
    }
  }
}
```

## Pagination Patterns

### Cursor-Based Pagination
```graphql
query {
  orders(shop_name: "my-shop") {
    data(first: 25, after: "CURSOR_FROM_PREVIOUS_PAGE") {
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
      edges {
        cursor
        node {
          id
          order_number
        }
      }
    }
  }
}
```

### Fetching All Pages (Python pattern)
```python
def fetch_all_orders(client, shop_name):
    all_orders = []
    has_next = True
    cursor = None

    while has_next:
        variables = {
            "shopName": shop_name,
            "first": 100,
            "after": cursor
        }
        result = client.execute(query, variables)

        page_info = result["orders"]["data"]["pageInfo"]
        edges = result["orders"]["data"]["edges"]

        all_orders.extend([edge["node"] for edge in edges])

        has_next = page_info["hasNextPage"]
        cursor = page_info["endCursor"]

    return all_orders
```
