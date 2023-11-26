import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


#We'll use manual input data for now
def get_tax_value (text: str) ->float:
    cs_number = text.split("£")[-1]
    return float(cs_number.replace(',', ''))



def calculate_tax(net_pay_annual, pension_salary_sacrifice):
    """
    Calculates your personal tax based on the provided inputs:
    net_pay_annual - Your gross annual salary
    pension contribution - How much of your salary you contribute to a pension pot (can be either % or £ value)
    student_loan - The type of student loan you have (e.g Plan 1, Plan 2...) or leave blank
    taxable_benefits - Any taxable benefits as the £ value they appear on your payslip or leave blank


    Between 100000 and the additional tax rate threshold you lose your un-taxable allowance at a rate of £1 per every £2 you earn above 100K.
    This lost allowance is then taxed at the higher rate.
    """
    url = 'https://www.gov.uk/income-tax-rates'
    tax_table = pd.read_html(url)
    print(tax_table[0])
    col_indices = tax_table[0].columns
    tax_value_list = []
    tax_rate_list = []
    for index, row in tax_table[0].iterrows():
        a = get_tax_value(row[col_indices[1]])
        b = float(row[col_indices[2]].replace('%', ''))/100
        tax_value_list.append(a)
        tax_rate_list.append(b)



    student_loan_repayment_threshold = 2274
    student_loan_tax_rate = 0.09
    income_tax_bracket_1_threshold = tax_value_list[0]/12
    income_tax_bracket_1_rate = tax_rate_list[1]
    income_tax_bracket_2_threshold = tax_value_list[1]/12
    income_tax_bracket_2_rate = tax_rate_list[2]
    income_tax_bracket_3_threshold = tax_value_list[2]/12
    income_tax_bracket_3_rate = tax_rate_list[3]

    net_pay_monthly = net_pay_annual/12
    pension_contribution = net_pay_monthly*pension_salary_sacrifice
    adjusted_net_pay_monthly = net_pay_monthly-pension_contribution
    adjusted_net_pay_annual = adjusted_net_pay_monthly*12
    student_loan_repayment = student_loan_tax_rate * (adjusted_net_pay_monthly-student_loan_repayment_threshold)

    if adjusted_net_pay_monthly > income_tax_bracket_3_threshold:
        additional_rate_paye_tax = (adjusted_net_pay_monthly-income_tax_bracket_3_threshold)*income_tax_bracket_3_rate
        higher_rate_paye_tax = (income_tax_bracket_3_threshold-income_tax_bracket_2_threshold+income_tax_bracket_1_threshold)*income_tax_bracket_2_rate
        basic_rate_paye_tax = (income_tax_bracket_2_threshold-income_tax_bracket_1_threshold)*income_tax_bracket_1_rate
        paye_tax = additional_rate_paye_tax + higher_rate_paye_tax + basic_rate_paye_tax

    elif income_tax_bracket_3_threshold >= adjusted_net_pay_monthly > income_tax_bracket_2_threshold and adjusted_net_pay_annual > (income_tax_bracket_3_threshold*12 - 2*income_tax_bracket_1_threshold*12):
        adjusted_personal_allowance = income_tax_bracket_1_threshold*12 - (adjusted_net_pay_annual - (income_tax_bracket_3_threshold*12 - 2*income_tax_bracket_1_threshold*12)) / 2
        #adjusted_monthly_personal_allowance = adjusted_personal_allowance/12
        taxable_allowance_portion = income_tax_bracket_1_threshold*12 - adjusted_personal_allowance
        taxable_monthly_allowance = taxable_allowance_portion/12
        higher_rate_paye_tax = (adjusted_net_pay_monthly-income_tax_bracket_2_threshold + taxable_monthly_allowance)*income_tax_bracket_2_rate
        basic_rate_paye_tax = (income_tax_bracket_2_threshold - income_tax_bracket_1_threshold) * income_tax_bracket_1_rate
        paye_tax = higher_rate_paye_tax + basic_rate_paye_tax

    elif income_tax_bracket_3_threshold >= adjusted_net_pay_monthly > income_tax_bracket_2_threshold and adjusted_net_pay_annual < (income_tax_bracket_3_threshold*12 - 2*income_tax_bracket_1_threshold*12):
        higher_rate_paye_tax = (adjusted_net_pay_monthly - income_tax_bracket_2_threshold) * income_tax_bracket_2_rate
        basic_rate_paye_tax = (income_tax_bracket_2_threshold - income_tax_bracket_1_threshold) * income_tax_bracket_1_rate
        paye_tax = higher_rate_paye_tax + basic_rate_paye_tax

    elif adjusted_net_pay_monthly > income_tax_bracket_1_threshold:
        basic_rate_paye_tax = (adjusted_net_pay_monthly-income_tax_bracket_1_threshold) * income_tax_bracket_1_rate
        paye_tax = basic_rate_paye_tax

    else:
        paye_tax=0

    return paye_tax

net_salary = 38400

print(calculate_tax(net_salary, 0))