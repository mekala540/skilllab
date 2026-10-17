"""Small in-memory fixtures shared by the tests."""

from tally.catalog import Catalog, Product
from tally.customers import Customer, CustomerBook
from tally.money import Money
from tally.orders import Order, OrderBook, OrderLine


def eur(x):
    return Money.of(x, "EUR")


def catalog():
    c = Catalog()
    c.add(Product("BK-1", "Book", eur("18.50"), "reduced"))
    c.add(Product("HW-1", "Mug", eur("14.99"), "standard"))
    c.add(Product("HW-2", "Dripper", eur("23.33"), "standard"))
    c.add(Product("GC-1", "Gift card", eur("25.00"), "zero"))
    return c


def customers():
    b = CustomerBook()
    b.add(Customer("C1", "Ada Okafor", "ada@example.com", "DE", "standard"))
    b.add(Customer("C2", "Bram Visser", "bram@example.com", "NL", "silver"))
    b.add(Customer("C3", "Chiara Rossi", "chiara@example.com", "FR", "gold"))
    b.add(Customer("C4", "Dev Sharma", "dev@example.com", "US", "standard"))
    return b


def order(oid, cust, when, *lines, status="paid", coupon=None):
    return Order(oid, cust, when, [OrderLine(s, q, eur(p)) for s, q, p in lines], status, coupon)


def book(*orders):
    b = OrderBook()
    for o in orders:
        b.add(o)
    return b
