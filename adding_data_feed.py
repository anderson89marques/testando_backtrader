import datetime
import os.path
import sys

import backtrader as bt

def main():
    cerebro = bt.Cerebro()

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'datas/orcl-1995-2014.txt')
    print(modpath)
    print(datapath)
    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2000, 1, 1),
        # Do not pass values after this date
        todate=datetime.datetime(2000, 12, 31),
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # run over everything
    cerebro.run()

     # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())


if __name__ == '__main__':
    main()