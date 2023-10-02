from django.test import TestCase
from vei_platform.models import BankLoan, BankLoanInterest
from decimal import Decimal
from datetime import date

# Create your tests here.


class BankLoanTest(TestCase):
    def test_end_year(self):
        loan = BankLoan(start_date=date(2022, 6, 1),
                        amount=Decimal(10000), duration=4)
        self.assertEqual(loan.start_year(), 2022)
        self.assertEqual(loan.end_year(), 2022)
        self.assertEqual(loan.amount, Decimal(10000))

    def test_end_year2(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(13000), duration=12)
        self.assertEqual(loan.start_year(), 2022)
        self.assertEqual(loan.end_year(), 2023)
        self.assertEqual(loan.amount, Decimal(13000))

    def test_end_year3(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(112), duration=12)
        self.assertEqual(loan.start_year(), 2022)
        self.assertEqual(loan.end_year(), 2023)
        self.assertEqual(loan.amount, Decimal(112))

    def test_amortization_fixed_rate(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(10000), duration=12)
        self.assertEqual(loan.get_interest(date(2022, 1, 1)), Decimal(5))
        amortization_schedule = loan.amortization_schedule()
        self.assertEqual(len(amortization_schedule), 12)
        self.assertEqual(amortization_schedule[0][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[1][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[2][1], Decimal('855.56'))
        self.assertEqual(amortization_schedule[3][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[4][1], Decimal('855.56'))
        self.assertEqual(amortization_schedule[5][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[6][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[7][1], Decimal('855.56'))
        self.assertEqual(amortization_schedule[8][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[9][1], Decimal('855.56'))
        self.assertEqual(amortization_schedule[10][1], Decimal('855.57'))
        self.assertEqual(amortization_schedule[11][1], Decimal('855.56'))

    def test_loan_totals(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(10000), duration=12)
        self.assertEqual(loan.get_interest(date(2022, 1, 1)), Decimal(5))
        total_payment, total_interest, total_principal = loan.total_amortization()
        self.assertEqual(total_payment, Decimal('10266.79'))
        self.assertEqual(total_interest, Decimal('266.79'))
        self.assertEqual(total_principal, Decimal('10000.00'))

    def test_loan_custom_interest(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(10000), duration=12)
        loan.save()
        BankLoanInterest(loan=loan, month=date(2022, 1, 1),
                         number=Decimal('7.0')).save()

        self.assertEqual(loan.get_interest(date(2022, 1, 1)), Decimal(7))
        total_payment, total_interest, total_principal = loan.total_amortization()
        self.assertEqual(total_payment, Decimal('10371.31'))
        self.assertEqual(total_interest, Decimal('371.31'))
        self.assertEqual(total_principal, Decimal('10000.00'))

    def test_loan_variable_custom_interest(self):
        loan = BankLoan(start_date=date(2022, 1, 1),
                        amount=Decimal(10000), duration=12)
        loan.save()
        BankLoanInterest(loan=loan, month=date(2022, 1, 1),
                         number=Decimal('7.0')).save()
        BankLoanInterest(loan=loan, month=date(2022, 3, 1),
                         number=Decimal('6.0')).save()
        BankLoanInterest(loan=loan, month=date(2022, 5, 1),
                         number=Decimal('5.0')).save()

        self.assertEqual(loan.get_interest(date(2022, 1, 1)), Decimal(7))
        self.assertEqual(loan.get_interest(date(2022, 2, 1)), Decimal(7))
        self.assertEqual(loan.get_interest(date(2022, 3, 1)), Decimal(6))
        self.assertEqual(loan.get_interest(date(2022, 4, 1)), Decimal(6))
        self.assertEqual(loan.get_interest(date(2022, 5, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 6, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 7, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 8, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 9, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 10, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 11, 1)), Decimal(5))
        self.assertEqual(loan.get_interest(date(2022, 11, 1)), Decimal(5))

        total_payment, total_interest, total_principal = loan.total_amortization()
        self.assertEqual(total_payment, Decimal('10310.19'))
        self.assertEqual(total_interest, Decimal('310.19'))
        self.assertEqual(total_principal, Decimal('10000.00'))
