# Review

- `remove_stock`: never checks `qty <= current`, so removing more than is in stock makes the count negative instead of raising ValueError.
- `apply_discount`: `price * percent // 100` floors the discount amount, so `apply_discount(19.99, 15)` returns 17.99 instead of 16.99.
