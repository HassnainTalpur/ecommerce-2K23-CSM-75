# Sprint 1: Architecture & Scope Definition

# ReadySafe - Emergency Preparedness E-Commerce Platform

---

# 1. Target Audience & Market Focus

## Primary Persona

**Target Users:**  
Individuals and families who want to purchase emergency preparedness and safety products for their homes.

**User Profile:**
- Age: 25–60 years old
- Customers interested in household safety and emergency preparation
- Users who prefer purchasing safety products through an online platform

---

## Core Problem Statement

Customers often find it difficult to locate reliable emergency preparedness products from a single trusted platform. They must search across multiple stores to purchase essential safety items such as first aid supplies, emergency lighting, and power backup products.

ReadySafe solves this problem by providing a centralized e-commerce platform where customers can browse, compare, and purchase emergency products easily.

---

## Domain Scope

**Market Vertical:**  
Emergency & Safety Products E-Commerce

**Product Categories:**
- First Aid Supplies
- Emergency Lighting
- Power Backup Equipment
- Water Storage & Filtration
- Safety Equipment

---

# 2. MVP Feature Scope

The Minimum Viable Product focuses on the essential customer shopping workflow: discovering products, managing a cart, and completing purchases.

| Category | Feature | Description |
|---|---|---|
| Authentication | User Registration & Login | Allows customers to create accounts, authenticate, and securely access the platform. |
| Catalog | Product Browsing | Allows customers to view emergency products organized by categories. |
| Search | Product Search & Filtering | Enables customers to search products and filter results by category. |
| Cart | Shopping Cart Management | Allows customers to add, update, and remove products before checkout. |
| Checkout | Order Processing | Creates customer orders from cart items and stores order details. |
| Admin | Inventory Management | Allows administrators to manage product information and stock quantities. |

---

# 3. Tech Stack Selection & Justification

## Frontend Framework

### React.js

**Justification:**

React.js is selected for building the user interface because it provides a component-based architecture that supports reusable components such as product cards, category views, shopping carts, and checkout pages. It allows efficient development of a responsive e-commerce frontend.

---

## Backend Infrastructure

### FastAPI (Python)

**Justification:**

FastAPI is selected as the backend framework because it provides a lightweight and high-performance solution for developing REST APIs. It supports rapid development, automatic API documentation, and integrates well with Python-based development tools.

---

## Database Management System

### PostgreSQL

**Justification:**

PostgreSQL is selected because e-commerce applications require structured relational data management. It provides strong consistency, foreign key relationships, and transaction support for managing users, products, carts, and orders.

---

## Caching & Asynchronous Processing

### Not Included in MVP

**Justification:**

Caching and asynchronous processing are not required for the initial MVP scope. These technologies can be introduced in future iterations to improve performance and handle larger traffic volumes.

---

# 4. Entity-Relationship Diagram (ERD)

The database design follows a relational model containing users, products, categories, shopping carts, and order management entities.

The schema defines primary keys (PK), foreign keys (FK), SQL-compatible data types, and relationship cardinalities between entities.

## Relationships

- One user can place many orders (1:N)
- One user has one shopping cart (1:1)
- One category contains many products (1:N)
- One cart contains many cart items (1:N)
- One product can appear in many cart items (1:N)
- One order contains many order items (1:N)
- One product can appear in many order items (1:N)

```mermaid
erDiagram

    USERS ||--|| CART : owns
    USERS ||--o{ ORDERS : places

    CATEGORIES ||--o{ PRODUCTS : contains

    CART ||--o{ CART_ITEMS : contains
    PRODUCTS ||--o{ CART_ITEMS : included_in

    ORDERS ||--o{ ORDER_ITEMS : contains
    PRODUCTS ||--o{ ORDER_ITEMS : included_in


    USERS {
        INTEGER id PK
        VARCHAR(100) name
        VARCHAR(150) email
        VARCHAR(255) password_hash
        VARCHAR(20) phone
        TIMESTAMP created_at
    }


    CATEGORIES {
        INTEGER id PK
        VARCHAR(100) name
        VARCHAR(255) description
    }


    PRODUCTS {
        INTEGER id PK
        INTEGER category_id FK
        VARCHAR(150) name
        VARCHAR(500) description
        DECIMAL(10,2) price
        INTEGER stock_quantity
        TIMESTAMP created_at
    }


    CART {
        INTEGER id PK
        INTEGER user_id FK
        TIMESTAMP created_at
    }


    CART_ITEMS {
        INTEGER id PK
        INTEGER cart_id FK
        INTEGER product_id FK
        INTEGER quantity
    }


    ORDERS {
        INTEGER id PK
        INTEGER user_id FK
        DECIMAL(10,2) total_amount
        VARCHAR(50) status
        TIMESTAMP created_at
    }


    ORDER_ITEMS {
        INTEGER id PK
        INTEGER order_id FK
        INTEGER product_id FK
        INTEGER quantity
        DECIMAL(10,2) unit_price
    }
