
import tempfile
import unittest
from pathlib import Path

from supplydesk.service import OrderService


class ExpressDeliveryTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "state.json"
        self.service = OrderService(self.path)

    def test_regular_express_quote(self):
        items = [{"product_id": "notebook", "quantity": 2}]

        quote = self.service.quote("regular", items, "express")

        self.assertEqual(quote["fulfillment"], "express")
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 2200)

    def test_student_express_quote(self):
        items = [{"product_id": "hoodie", "quantity": 2}]

        quote = self.service.quote("student", items, "express")

        self.assertEqual(quote["subtotal_cents"], 8000)
        self.assertEqual(quote["discount_cents"], 800)
        self.assertEqual(quote["delivery_cents"], 1200)
        self.assertEqual(quote["total_cents"], 8400)

    def test_express_fee_is_never_waived(self):
        items = [{"product_id": "hoodie", "quantity": 3}]

        standard = self.service.quote("regular", items, "delivery")
        express = self.service.quote("regular", items, "express")

        self.assertEqual(standard["delivery_cents"], 0)
        self.assertEqual(standard["total_cents"], 12000)
        self.assertEqual(express["delivery_cents"], 1200)
        self.assertEqual(express["total_cents"], 13200)

    def test_express_order_matches_quote_and_reopens(self):
        items = [{"product_id": "notebook", "quantity": 2}]

        quote = self.service.quote("regular", items, "express")
        order = self.service.place_order("regular", items, "express")

        self.assertEqual(order["fulfillment"], "express")
        self.assertEqual(order["delivery_cents"], 1200)
        self.assertEqual(order["total_cents"], quote["total_cents"])
        self.assertEqual(order["items"], quote["items"])

        reopened = OrderService(self.path)
        saved = reopened.get_order(order["order_id"])

        self.assertEqual(saved["fulfillment"], "express")
        self.assertEqual(saved["delivery_cents"], 1200)
        self.assertEqual(saved["total_cents"], 2200)
        self.assertEqual(saved["items"], order["items"])

        cancelled = reopened.cancel_order(order["order_id"])

        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(cancelled["fulfillment"], "express")
        self.assertEqual(cancelled["delivery_cents"], 1200)
        self.assertEqual(cancelled["total_cents"], 2200)

    def test_invalid_fulfillment_is_rejected(self):
        items = [{"product_id": "notebook", "quantity": 1}]

        with self.assertRaises(ValueError):
            self.service.quote("regular", items, "overnight")

        with self.assertRaises(ValueError):
            self.service.place_order("regular", items, "overnight")


if __name__ == "__main__":
    unittest.main()
