from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds


class EMAStrategy(bt.Strategy):
    params = (
        ('shortperiod', 20),
        ('longperiod', 40),
    )
    def log(self, txt, dt=None):
       ''' Logging function for this strategy'''
       dt = dt or self.datas[0].datetime.datetime()
       print('%s, %s' % (dt.strftime("%d/%m/%Y %H:%M:%S"), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.invested = False

        self.short_ema = bt.indicators.EMA(
            self.datas[0], period=self.params.shortperiod
        )

        self.long_ema = bt.indicators.EMA(
            self.datas[0], period=self.params.longperiod
        )

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return
        
        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.8f, Cost: %.8f, Comm %.8f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.8f, Cost: %.8f, Comm %.8f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.8f, NET %.8f' %
                 (trade.pnl, trade.pnlcomm))
    
    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.8f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return
        
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            if self.short_ema[0] > self.long_ema[0] and not self.invested:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.8f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
                self.invested = True
        else:

            if self.short_ema[0] < self.long_ema[0] and self.invested:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.8f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
                self.invested = False

def main():
    cerebro = bt.Cerebro()
     # Add a strategy
    cerebro.addstrategy(EMAStrategy)

    data = btfeeds.GenericCSVData(
        dataname='binance.csv',
        fromdate=datetime(2018,3,1),
        todate=datetime(2018,3,2),

        dtformat=("%d/%m/%Y %H:%M:%S"),
        timeframe=bt.TimeFrame.Minutes,

        datetime=0,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )

    cerebro.adddata(data)

    # Add a FixedSize sizer according to the stake
    #cerebro.addsizer(bt.sizers.FixedSize, stake=10)

     # Set our desired cash start
    cerebro.broker.setcash(50000.0)

    # Set the commission
    cerebro.broker.setcommission(commission=0.00)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.8f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.8f' % cerebro.broker.getvalue())
    cerebro.plot(style='candlestick')

if __name__ == '__main__':
    main()