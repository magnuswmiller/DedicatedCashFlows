# Dedicated Portfolio Calculator - Cash Flow Matching
# Requirements When Running:
#   - dates in cash flows should be in mm-month abbr (ie Aug)-yyyy
#   - .csv needs to be in same directory as the .py file
#   - .csv input is just the name of the file

# Required Libraries and Versions:
#   python -v 3.12.6
#   datetime.date -v
#   pandas -v 2.2.3
#   numpy -v 2.1.1
#   scipy.optimize.linprog -v 1.14.1
#   calendar -v
#   math -v

# Library Import:
from datetime import date
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import calendar
import math

# Parses various date formats and converts to datetime.date obj
def dateParse(stringDate, stype):
    d = 0
    monthDict = {
            "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    if(stype == 0):
        if(stringDate[0] == "0"):
            month = stringDate[1]
        else:
            month = stringDate[0:2]

        if(stringDate[2] == "0"):
            day = stringDate[3]
        else:
            day = stringDate[2:4]

        year = stringDate[4:]
        d = date(int(year), int(month), int(day))

    elif(stype == 1):
        dateList = stringDate.split("/")
        month = dateList[0]
        day = dateList[1]
        year = dateList[2]
        d = date(int(year), int(month), int(day))

    else:
        dateList = stringDate.split("-")
        dateList = stringDate.split("-")
        day = dateList[0]
        month = monthDict.get(dateList[1])
        year = dateList[2]
        d = date(int(year), int(month), int(day))

    return d

# calculates number of months remaining
def numMonths(sd, md):
    return (md.year - sd.year) * 12 + (md.month - sd.month)

# calculates number of months since last payment
def monthsSince(sd, md, freq):
    numMonthsLeft = numMonths(sd, md)
    if((numMonthsLeft % (12 // freq)) != 0):
        return (12 // freq) - (numMonthsLeft % (12 // freq))
    else:
        return 0

# calculates the date of the last coupon payment
def lastDate(sd, md, freq):
    monthsSinceCoupon = monthsSince(sd, md, freq)
    if(md.day < 28):
        lastDate = date(sd.year,
                        sd.month - int(monthsSinceCoupon),
                        md.day)
    else:
        if(sd.month - ((12 // freq) - monthsSinceCoupon) < 1):
            lastDate = date(sd.year-1,
                            12 - (-1*(sd.month - monthsSinceCoupon)),
                            15)
        else:
            lastDate = date(sd.year,
                            sd.month - monthsSinceCoupon,
                            15)
        maxDay = calendar.monthrange(lastDate.year, lastDate.month)[1]
        lastDate = lastDate.replace(day=maxDay)
    return lastDate

# calculates the date of the next coupon payment
def nextDate(cd, md, freq):
    monthsSinceCoupon = monthsSince(cd, md, freq)
    if(md.day < 28):
        if(cd.month + ((12 // freq) - monthsSinceCoupon) > 12):
            nextDate = date(cd.year + 1,
                            (cd.month + ((12 // freq) - monthsSinceCoupon)) % 12,
                            md.day)
        else:
            nextDate = date(cd.year,
                            cd.month + ((12 // freq) - monthsSinceCoupon) % 12,
                            md.day)
    else:
        if(cd.month + ((12 // freq) - monthsSinceCoupon) > 12):
            nextDate = date(cd.year + 1,
                            (cd.month + ((12 // freq) - monthsSinceCoupon)) % 12,
                            15)
        else:
            nextDate = date(cd.year,
                            cd.month + ((12 // freq) - monthsSinceCoupon) % 12,
                            15)
        nextDate = nextDate.replace(day=calendar.monthrange(nextDate.year, nextDate.month)[1])
    return nextDate

# calculates days last payment
def daysLast(sd, md, freq):
    lastDateCoupon = lastDate(sd, md, freq)
    return (sd - date(lastDateCoupon.year,
                     lastDateCoupon.month,
                     lastDateCoupon.day)).days

# calculates days next payment
def daysNext(sd, md, freq):
    nextCouponDate = nextDate(sd, md, freq)
    return (-(sd - date(nextCouponDate.year,
                       nextCouponDate.month,
                       nextCouponDate.day))).days

# calculates days in payment period
def periodDays(sd, md, freq):
    daysLastCoupon = daysLast(sd, md, freq)
    daysNextCoupon = daysNext(sd, md, freq)
    return daysLastCoupon + daysNextCoupon

# calculates accrued interest
def calcAccInt(rate, freq, sd, md):
    if freq != 0:
        daysLastCoupon = daysLast(sd, md, freq)
        periodDaysCoupon = periodDays(sd, md, freq)
        return (rate/freq) * (daysLastCoupon/periodDaysCoupon)
    else:
        return 0

# calculates dirty price from clean price (returns list)
def clean2Dirty(bondTypes, bondRates, bondCleanPrice, sd, md):
    bondDirtyPrice = []
    for i in range(len(bondTypes)):
        freq = 0
        if bondTypes[i] != 'MARKET BASED BILL':
            freq = 2
        tempAccInt = round(calcAccInt(bondRates[i] * 100,freq, sd, md[i]), 8)
        bondDirtyPrice.append(bondCleanPrice[i]+(tempAccInt))
    return bondDirtyPrice

# calculates the number of remaining coupon payments
def numPayments(sd, md, freq):
    numMonthsLeft = numMonths(sd, md)
    if(numMonthsLeft % (12 // freq) == 0):
        return math.ceil(numMonthsLeft / (12 // freq)) + 1
    else:
        return math.ceil(numMonthsLeft / (12 // freq))

# produces the coupon payment dates for all remaining coupon payments
def paymentSchedule(sd, md, freq):
    numPay = numPayments(sd, md, freq)
    cd = sd
    schedule = []
    for i in range(numPay):
        nextCouponDate = nextDate(cd, md, freq)
        schedule.append(nextCouponDate)
        cd = nextCouponDate
    return schedule

# sums all payments between dates
def sumPayments(sd, md, lld, nld, rate, freq):
    cfDates = paymentSchedule(sd, md, freq)
    numPay = len(cfDates)
    numPayBT = 0
    sumPay = 0
    for i in range(numPay):
        if(((cfDates[i] - lld).days > 0) & ((cfDates[i] - nld).days <= 0)):
            numPayBT += 1
    if(((cfDates[i] - lld).days > 0) & ((cfDates[i] - nld).days <= 0) & ((md - nld).days <= 0)):
        sumPay = 100 + ((rate/freq) * numPayBT)
    else:
        sumPay = (rate/freq) * numPayBT
    return sumPay

# main function (drives calculator)
def main():
    # Explanation
    print("* Welcome to the Dedicated Portfolio Calculator")
    print('* The calculator will ask for the settlement date and the \n' 
          'file locations for the bond prices and the cash flow .csv files.')

    # Retrieving inputs from user
    # settlement date
    print("* Please enter the settlement date in the format: mmddyyyy")
    settlementDateInput = input("\tSettlement Date: ")

    # convert sd input to datetime.date obj
    settlementDate = dateParse(settlementDateInput, 0)

    # bond price data
    print("* Please enter the file name of the bond price data.")
    bondFileLoc = input("\tBond Price Data: ")

    # read in bond prices
    bonds = pd.read_csv(bondFileLoc, header=None)
    bonds.columns = ['CUSIP', 'Type', 'Rate', 'Maturity', 'Call',
                     'Buy', 'Sell', 'End']
    print("*** Successfully acquired bond price data ***")

    print("* Please enter the file name of the cash flow data.")
    cfFileLoc = input("\tCash Flow Data: ")

    # read in cash flow data 
    cashFlows = pd.read_csv(cfFileLoc)
    print("*** Successfully acquired cash flow data ***")

    # print update:
    print("*** Cleaning Data ***")

    # Clean bonds data
    bonds = bonds.drop('End', axis=1)
    bonds = bonds.drop('Sell', axis=1)
    bonds = bonds.drop('Call', axis=1)
    bonds = bonds.drop(bonds[(bonds.Type != 'MARKET BASED BILL')
                             & (bonds.Type != 'MARKET BASED NOTE')
                             & (bonds.Type != 'MARKET BASED BOND')].index)
    bonds = bonds.drop(bonds[bonds.Buy < 0.05].index)
    bonds = bonds.reset_index(drop=True)

    # Change dates to datetime.date objects
    print("*** Converting dates to proper format ***")
    maturity = bonds.Maturity.to_list()
    newMaturity = []
    for i in range(len(maturity)):
        tempDate = dateParse(maturity[i], 1)
        newMaturity.append(tempDate)
    newMaturities = pd.Series(newMaturity)
    bonds.Maturity = newMaturities

    dates = cashFlows.dates.to_list()
    newDates = []
    for i in range(len(dates)):
        tempDate = dateParse(dates[i], 2)
        newDates.append(tempDate)
    newDates = pd.Series(newDates)
    cashFlows.dates = newDates

    # Convert buy price (clean) to dirty
    print("*** Converting clean prices to dirty prices ***")
    types = bonds.Type.to_list()
    rates = bonds.Rate.to_list()
    cleans = bonds.Buy.to_list()
    newBuy = pd.Series(clean2Dirty(types, rates, cleans, settlementDate, newMaturity))
    bonds.Buy = newBuy

    # forming Objective Function
    print("*** Forming objective function ***")
    objective = bonds['Buy'].to_numpy()

    # forming constraints
    numBonds = len(bonds)
    numCashFlows = len(cashFlows)

    A_x = np.zeros((numCashFlows, numBonds))
    b_eq = cashFlows['cfs'].to_numpy()

    cashFlowDates = cashFlows.dates.to_list()
    maturityDates = bonds.Maturity.to_list()

    # A_x
    for i in range(numCashFlows):
        for j in range(numBonds):
            if(types[j] != 'MARKET BASED BILL'):
                freq = 2
                if(i != 0):
                    A_x[i][j] = sumPayments(settlementDate, maturityDates[j],
                                             cashFlowDates[i-1], cashFlowDates[i],
                                             rates[j] * 100, freq)
                else:
                    A_x[i][j] = sumPayments(settlementDate, maturityDates[j],
                                             settlementDate, cashFlowDates[i],
                                             rates[j] * 100, freq)
            else:
                if(i != 0):
                    if(((maturityDates[j] - cashFlowDates[i]).days <= 0)
                       & ((maturityDates[j] - cashFlowDates[i-1]).days > 0)):
                        A_x[i][j] = 100
                    else:
                        A_x[i][j] = 0
                else:
                    if(((maturityDates[j] - cashFlowDates[i]).days <= 0)
                       & ((maturityDates[j] - settlementDate).days > 0 )):
                       A_x[i][j] = 100
                    else:
                       A_x[i][j] = 0

    # A_s
    A_s = np.zeros((numCashFlows, numCashFlows))
    for i in range(numCashFlows):
        for j in range(numCashFlows):
            if(i == j):
                A_s[i][j] = -1
            elif(j == i-1):
                A_s[i][j] = 1
            else:
                A_s[i][j] = 0
    A_eq = np.concatenate((A_x, A_s), axis=1)
    objective = np.concatenate((objective, np.zeros(numCashFlows)))


    bounds = [(0, None) for _ in range(numBonds + numCashFlows)]

    # solving LP
    print("*** Solving LP Problem ***")
    result = linprog(objective, A_eq = A_eq, b_eq = b_eq, bounds = bounds, method='highs')

    for i in range(numCashFlows):
        slacks = {'CUSIP': 'x00000000', 'Type': 'HOLDOVER', 'Rate': 0, 'Maturity': cashFlowDates[i],
                  'Buy': 1.0}
        bonds = bonds._append(slacks, ignore_index=True)

    if result.success:
        print("*** Optimal Solution Found ***")
        outputDF = pd.DataFrame({'CUSIP': bonds['CUSIP'], 'Principal': result.x*100,
                                 'Maturity': bonds['Maturity'], 'Cost': result.x*bonds['Buy'],
                                 'Buy': bonds['Buy']})
        outputDF = outputDF[outputDF.Principal > 0.0]

        outputDF = outputDF.drop('Maturity', axis=1)
        outputDF = outputDF.drop('Cost', axis=1)
        outputDF = outputDF.drop('Buy', axis=1)
        outputDF = outputDF.drop(outputDF[(outputDF.CUSIP == 'x00000000')].index)
        outputDF.to_csv('Output.csv')
    else:
        print("*** Optimization Failed ***")
        print("--- Please Try Again ---")
        print(result.message)

if __name__ =='__main__':
    main()
