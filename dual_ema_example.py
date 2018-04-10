from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.analyzers as btanalyzers
import pprint

class EMAStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('shortperiod', 20),
        ('longperiod', 40),
    )
    def log(self, txt, dt=None):
       ''' Logging function for this strategy'''
       dt = dt or self.datas[0].datetime.datetime()
       #print('%s, %s' % (dt.strftime("%d/%m/%Y %H:%M:%S"), txt))

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

        print('OPERATION PROFIT, GROSS %.8f, NET %.8f' %
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
    
    def stop(self):
        print('(MA Period %2d) Ending Value %.8f' %
                 (self.params.maperiod, self.broker.getvalue()))

def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total,2)
    strike_rate = (total_won / total_closed) * 100

    print("STRIKE RATE")
    print('Winning Percent: {}'.format(strike_rate))
    print('Total Trade: {}'.format(total_closed))
    print('Profit Factor: {}'.format(total_won/total_lost))

    print('Total Open: {}'.format(total_open))
    print('Total Won: {}'.format(total_won))
    print('Total Lost: {}'.format(total_lost))
    print('Win Streak: {}'.format(win_streak))
    print('Losing Streak: {}'.format(lose_streak))
    print('PnL Net: {}'.format(pnl_net))
    print('')
    
 
def printSQN(analyzer):
    print("SQN: System Quality Number")
    sqn = round(analyzer.sqn,2)
    print('SQN: {}'.format(sqn))
    print('')

def printTimeReturn(analyzer):
    print("TIME RETURN")
    for key, val in analyzer.items():
        print('-- ', key, ':', val)
    print('')

def printDrawmDown(analyzer):
    print("DRAWN DOWN")
    print('-- ','Len: ', analyzer.len)
    print('-- ', 'DrawDown: ',analyzer.drawdown)
    print('-- ', 'MoneyDown: ', analyzer.moneydown)
    print('--', 'MAX:')
    for key, val in analyzer.max.items():
        print('---- ', key,':', val)
    print('')

def printAnalyzersInfo(analyzer):
    analysis = analyzer.get_analysis()
    if isinstance(analyzer, bt.analyzers.TradeAnalyzer):
        total_open = analysis.total.open
        total_closed = analysis.total.closed
        total_won = analysis.won.total
        total_lost = analysis.lost.total
        strike_rate = (total_won / total_closed) * 100
        print(analysis.total)
        print('Winning Percent: {}'.format(strike_rate))
        print('Total Trade: {}'.format(total_closed))
        print('Profit Factor: {}'.format(total_won/total_lost))
        print('Net Profit: {}'.format(total_won - total_lost))
        print('AVG win: {}'.format((total_won/total_closed)*100))
        print('AVG loss: {}'.format((total_lost/total_closed)*100))
    
    if isinstance(analyzer, bt.analyzers.SQN):
        sqn = round(analysis.sqn,2)
        print('SQN: {}'.format(sqn))

    if isinstance(analyzer, bt.analyzers.DrawDown):
        print('Drawdown: {}'.format(analysis.max.drawdown))
        print('Moneydown: {}'.format(analysis.max.moneydown))

def main():
    cerebro = bt.Cerebro() # stdstats=False

     # Add a strategy
    cerebro.addstrategy(EMAStrategy)
    #cerebro.optstrategy(
    #    EMAStrategy,
    #    maperiod=range(10, 31)
    #)
    data = btfeeds.GenericCSVData(
        dataname='binance.csv',
        fromdate=datetime(2017,7,17),
        todate=datetime(2017,7,20),

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
    cerebro.addsizer(bt.sizers.PercentSizer, percents=99)

     # Set our desired cash start
    cerebro.broker.setcash(0.50)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.8f' % cerebro.broker.getvalue())
    
    # add analyzers
    # Add the analyzers we are interested in

    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")


    # Run over everything
    results = cerebro.run()
    runst = results[0]
    # Print out the final result
    print('Final Portfolio Value: %.8f' % cerebro.broker.getvalue())
    print('====================')
    print('== Analyzers')
    print('====================')
    analyzers = ["ta","sqn","drawdown","returns"]
    analyzers_dict = {'ta': printTradeAnalysis, 'sqn': printSQN}
    for name in analyzers:
        printAnalyzersInfo(runst.analyzers.getbyname(name))
    print('---')

    # If no name has been specified, the name is the class name lowercased
    #tret_analyzer = runst.analyzers.getbyname('timereturn')
    #printTimeReturn(tret_analyzer.get_analysis())
    #printTradeAnalysis(runst.analyzers.getbyname('ta').get_analysis())
    #printSQN(runst.analyzers.getbyname('sqn').get_analysis())
    #printDrawmDown(runst.analyzers.getbyname('dd').get_analysis())
    #print(runst.analyzers.getbyname('cm').get_analysis())
    #printTimeReturn(runst.analyzers.getbyname('vwr').get_analysis())
    #printTimeReturn(runst.analyzers.getbyname('srq').get_analysis())



if __name__ == '__main__':
    main()