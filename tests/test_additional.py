
"""Additional tests for Campus Supply Desk."""

import tempfile
import unittest
from pathlib import Path

from supplydesk.service import OrderService


class AdditionalOrderTests(unittest.TestCase):

    def setUp(self):
        # Give each test its own temporary data file.
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

        self.path = Path(self.directory.name) / "state.json"
        self.service = OrderService(self.path)

    # TEST 1: Normal behavior
    def test_quote_does_not_place_order(self):
        items = [{"product_id": "notebook", "quantity": 2}]

        quote = self.service.quote("regular", items)

        self.assertEqual(quote["total_cents"], 1000)
        self.assertEqual(self.service.list_orders(), [])
        self.assertFalse(self.path.exists())

    # TEST 2: Boundary behavior - minimum quantity
    def test_minimum_valid_quantity(self):
        items = [{"product_id": "notebook", "quantity": 1}]

        quote = self.service.quote("regular", items)

        self.assertEqual(quote["total_cents"], 500)
        self.assertEqual(quote["items"][0]["quantity"], 1)

    # TEST 3: Boundary behavior - discount threshold
    def test_student_discount_at_exact_threshold(self):
        items = [{"product_id": "bag", "quantity": 2}]

        quote = self.service.quote("student", items)

        self.assertEqual(quote["subtotal_cents"], 5000)
        self.assertEqual(quote["discount_cents"], 500)
        self.assertEqual(quote["total_cents"], 4500)

    # TEST 4: Invalid behavior
    def test_invalid_quantities_are_rejected(self):
        for quantity in [0, -1, 100, True, 1.5, "2"]:
            with self.subTest(quantity=quantity):
                items = [
                    {"product_id": "notebook",
                     "quantity": quantity}
                ]

                with self.assertRaises(ValueError):
                    self.service.quote("regular", items)

    # TEST 5: Behavior to preserve - consistent pricing
    def test_quote_matches_placed_order(self):
        items = [{"product_id": "hoodie", "quantity": 2}]

        quote = self.service.quote(
            "student", items, "delivery"
        )

        order = self.service.place_order(
            "student", items, "delivery"
        )

        self.assertEqual(
            quote["total_cents"], order["total_cents"]
        )
        self.assertEqual(
            quote["discount_cents"], order["discount_cents"]
        )
        self.assertEqual(
            quote["delivery_cents"], order["delivery_cents"]
        )

    # TEST 6: Behavior to preserve - repeat cancellation
    def test_cancelling_twice_does_not_restore_stock_twice(self):
        items = [{"product_id": "notebook", "quantity": 2}]

        original_stock = self.service.catalog()[0]["stock"]
        order = self.service.place_order("regular", items)

        self.service.cancel_order(order["order_id"])
        self.service.cancel_order(order["order_id"])

        final_stock = self.service.catalog()[0]["stock"]

        self.assertEqual(final_stock, original_stock)


if __name__ == "__main__":
    unittest.main()
