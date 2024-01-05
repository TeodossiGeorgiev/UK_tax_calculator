import pandas as pd

def convert_string_value_to_float(text: str) -> float:
    comma_separated_number = text.split("£")[-1]
    return float(comma_separated_number.replace(',', ''))

def get_income_tax_values_and_rates():
    url = 'https://www.gov.uk/income-tax-rates'
    tax_table = pd.read_html(url)
    col_indices = tax_table[0].columns
    tax_values = []
    tax_rates = []
    for index, row in tax_table[0].iterrows():
        current_tax_threshold = convert_string_value_to_float(row[col_indices[1]])
        current_tax_rate = float(row[col_indices[2]].replace('%', '')) / 100
        tax_values.append(current_tax_threshold)
        tax_rates.append(current_tax_rate)
    return tax_values, tax_rates

def get_ni_first_number(number: str) -> float:
    beginning = end = 0
    for index, character in enumerate(number):
        if character == '£':
            beginning = index+1
        if character == ' ':
            end = index
            break
    comma_separated_number = number[beginning : end]
    return float(comma_separated_number.replace(',', ''))
def get_national_insurance_tax_values_and_rates():
    url = 'https://www.gov.uk/national-insurance/how-much-you-pay'
    tax_table = pd.read_html(url)
    col_indices = tax_table[0].columns
    tax_values = []
    tax_rates = []
    for index, row in tax_table[0].iterrows():
        current_tax_threshold = get_ni_first_number((row[col_indices[0]]).split("(")[1])
        current_tax_rate = float(row[col_indices[1]].replace('%', '')) / 100
        tax_values.append(current_tax_threshold)
        tax_rates.append(current_tax_rate)
    return tax_values, tax_rates

def get_student_loan_threshold(plan):
    url = 'https://www.gov.uk/repaying-your-student-loan/what-you-pay'
    student_loan_table = pd.read_html(url)
    col_indices = student_loan_table[0].columns
    for index, row in student_loan_table[0].iterrows():
        if plan == row[col_indices[0]]:
            student_loan_threshold = row[col_indices[2]]
    return convert_string_value_to_float(student_loan_threshold)

def calculate_additional_rate_taxpayer_tax(adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds):
    additional_rate_paye_tax = (adjusted_net_pay_monthly - monthly_income_tax_thresholds[2]) * income_tax_rates[3]
    higher_rate_paye_tax = (monthly_income_tax_thresholds[2] - monthly_income_tax_thresholds[1] + monthly_income_tax_thresholds[0]) * income_tax_rates[2]
    basic_rate_paye_tax = (monthly_income_tax_thresholds[1] - monthly_income_tax_thresholds[0]) * income_tax_rates[1]
    return additional_rate_paye_tax + higher_rate_paye_tax + basic_rate_paye_tax


def calculate_non_standard_higher_rate_taxpayer_tax(adjusted_net_pay_annual, adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds):
    adjusted_personal_allowance = monthly_income_tax_thresholds[0] * 12 - (adjusted_net_pay_annual - (monthly_income_tax_thresholds[2] * 12 - 2 * monthly_income_tax_thresholds[0] * 12)) / 2
    taxable_allowance_portion = monthly_income_tax_thresholds[0] * 12 - adjusted_personal_allowance
    taxable_monthly_allowance = taxable_allowance_portion / 12
    higher_rate_paye_tax = (adjusted_net_pay_monthly - monthly_income_tax_thresholds[1] + taxable_monthly_allowance) * income_tax_rates[2]
    basic_rate_paye_tax = (monthly_income_tax_thresholds[1] - monthly_income_tax_thresholds[0]) * income_tax_rates[1]
    return higher_rate_paye_tax + basic_rate_paye_tax


def calculate_standard_higher_rate_taxpayer_tax(adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds):
    higher_rate_paye_tax = (adjusted_net_pay_monthly - monthly_income_tax_thresholds[1]) * income_tax_rates[2]
    basic_rate_paye_tax = (monthly_income_tax_thresholds[1] - monthly_income_tax_thresholds[0]) * income_tax_rates[1]
    return higher_rate_paye_tax + basic_rate_paye_tax


def calculate_tax(net_pay_annual, pension_salary_sacrifice, plan_type):
    """
    Calculates your personal tax based on the provided inputs:
    net_pay_annual - Your gross annual salary
    pension contribution - How much of your salary you contribute to a pension pot (can be either % or £ value)
    student_loan - The type of student loan you have (e.g Plan 1, Plan 2...) or leave blank
    taxable_benefits - Any taxable benefits as the £ value they appear on your payslip or leave blank


    Between 100000 and the additional tax rate threshold you lose your un-taxable allowance at a rate of £1 per every £2 you earn above 100K.
    This lost allowance is then taxed at the higher rate.
    """
    income_tax_thresholds, income_tax_rates = get_income_tax_values_and_rates()
    ni_tax_thresholds, ni_tax_rates = get_national_insurance_tax_values_and_rates()
    student_loan_repayment_threshold = get_student_loan_threshold(plan_type)
    student_loan_tax_rate = 0.09
    #postgrad_loan_tax_rate = 0.06
    monthly_income_tax_thresholds = [income_tax_threshold/12 for income_tax_threshold in income_tax_thresholds]

    net_pay_monthly = net_pay_annual/12
    pension_contribution = net_pay_monthly*pension_salary_sacrifice
    adjusted_net_pay_monthly = net_pay_monthly-pension_contribution
    adjusted_net_pay_annual = adjusted_net_pay_monthly*12
    student_loan_repayment = student_loan_tax_rate * (adjusted_net_pay_monthly-student_loan_repayment_threshold)

    if adjusted_net_pay_monthly > monthly_income_tax_thresholds[2]:
        paye_tax = calculate_additional_rate_taxpayer_tax(adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds)

    elif monthly_income_tax_thresholds[2] >= adjusted_net_pay_monthly > monthly_income_tax_thresholds[1] and adjusted_net_pay_annual > (monthly_income_tax_thresholds[2]*12 - 2*monthly_income_tax_thresholds[0]*12):
        paye_tax = calculate_non_standard_higher_rate_taxpayer_tax(adjusted_net_pay_annual, adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds)

    elif monthly_income_tax_thresholds[2] >= adjusted_net_pay_monthly > monthly_income_tax_thresholds[1] and adjusted_net_pay_annual < (monthly_income_tax_thresholds[2]*12 - 2*monthly_income_tax_thresholds[0]*12):
        paye_tax = calculate_standard_higher_rate_taxpayer_tax(adjusted_net_pay_monthly, income_tax_rates, monthly_income_tax_thresholds)

    elif adjusted_net_pay_monthly > monthly_income_tax_thresholds[0]:
        paye_tax = (adjusted_net_pay_monthly-monthly_income_tax_thresholds[0]) * income_tax_rates[1]

    else:
        paye_tax = 0

    if adjusted_net_pay_monthly > ni_tax_thresholds[1]:
        ni_tax = (adjusted_net_pay_monthly-ni_tax_thresholds[1])*ni_tax_rates[1]+(ni_tax_thresholds[1]-ni_tax_thresholds[0])*ni_tax_rates[0]
    elif ni_tax_thresholds[1] >= adjusted_net_pay_monthly > ni_tax_thresholds [0]:
        ni_tax = (adjusted_net_pay_monthly-ni_tax_thresholds[0])*ni_tax_rates[0]
    else:
        ni_tax = 0

    gross_salary = net_pay_monthly-paye_tax-ni_tax-pension_contribution - student_loan_repayment
    return paye_tax, ni_tax, pension_contribution, student_loan_repayment, gross_salary


net_salary = 38400
print(calculate_tax(net_salary, 0.05, 'Plan 2'))