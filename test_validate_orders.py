import unittest
from validate_orders import validate_orders


class OrderValidationTests(unittest.TestCase):
    def report(self, rows):
        return validate_orders("order_id,amount\n" + rows)

    def test_normalizes_outer_spaces_and_money(self):
        row = self.report(" A-1 , 0.1 \n").accepted[0]
        self.assertEqual((row.order_id, row.amount, row.source_end_line), ("A-1", "0.10", 2))

    def test_utf8_bom_and_crlf(self):
        report = validate_orders("\ufefforder_id,amount\r\nA,10\r\n")
        self.assertEqual(report.accepted[0].amount, "10.00")

    def test_first_valid_duplicate_wins(self):
        report = self.report("A,1\nA,2\n")
        self.assertEqual([r.amount for r in report.accepted], ["1.00"])
        self.assertEqual(report.rejected[0].reason, "duplicate order_id")

    def test_rejected_row_does_not_reserve_id(self):
        report = self.report("A,wrong\nA,2\n")
        self.assertEqual(len(report.accepted), 1)
        self.assertEqual(len(report.rejected), 1)

    def test_identifier_is_case_sensitive(self):
        self.assertEqual(len(self.report("A,1\na,2\n").accepted), 2)

    def test_blank_and_extra_fields_are_quarantined(self):
        report = self.report("A\nB,1,x\nC,\n,2\n")
        self.assertEqual(len(report.accepted), 0)
        self.assertEqual(len(report.rejected), 4)

    def test_header_schema_fails_closed(self):
        for text in ["", "amount,order_id\n", "order_id,order_id\n", "order_id,amount,x\n"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                validate_orders(text)

    def test_nonfinite_exponent_negative_and_rounding_are_not_accepted(self):
        for amount in ["NaN", "Infinity", "1e2", "-1", "+1", "0.001", "1.", ".5", "1000000000", "١"]:
            with self.subTest(amount=amount):
                self.assertEqual(len(self.report(f"A,{amount}\n").rejected), 1)

    def test_formula_like_ids_are_not_accepted(self):
        for order_id in ["=1+1", "+SUM", "@cmd", "contains space"]:
            with self.subTest(order_id=order_id):
                self.assertEqual(self.report(f"{order_id},1\n").rejected[0].reason, "invalid order_id")

    def test_quoted_comma_is_one_field_not_silent_extra_column(self):
        report = self.report('A,"1,000"\n')
        self.assertEqual(report.rejected[0].reason, "invalid amount")

    def test_multiline_csv_source_line(self):
        report = self.report('"A\nB",1\nC,2\n')
        self.assertEqual(report.rejected[0].source_end_line, 3)
        self.assertEqual(report.accepted[0].source_end_line, 4)

    def test_bad_csv_syntax_aborts_entire_report(self):
        with self.assertRaisesRegex(ValueError, "malformed CSV"):
            self.report('A,1\nB,"unterminated\n')

    def test_header_only_and_blank_lines(self):
        self.assertEqual(len(self.report("\n\n").accepted), 0)

    def test_repeatable_no_state_leak_between_calls(self):
        self.assertEqual(self.report("A,1\n"), self.report("A,1\n"))


if __name__ == "__main__":
    unittest.main()
