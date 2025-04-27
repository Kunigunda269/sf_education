import pandas as pd

class MarketAnalyzer:
    def __init__(self, csv_file):
        self.df = self._load_data(csv_file)
        self.h1_df = None
        self.m15_df = None

    def _load_data(self, csv_file):
        df = pd.read_csv(csv_file, names=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
        df = df.set_index('datetime')
        return df

    def prepare_timeframes(self):
        self.h1_df = self.df.resample('h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        self.h1_df = self.h1_df.dropna()
        self.m15_df = self.df.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        self.m15_df = self.m15_df.dropna()

    def get_body_range(self, row):
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']
        body_low = min(open_price, close_price)
        body_high = max(open_price, close_price)
        body_size = abs(open_price - close_price)
        shadow_size = max(high_price - body_high, body_low - low_price)
        if shadow_size > body_size:
            return low_price, high_price
        else:
            return body_low, body_high

    def find_order_blocks(self):
        obs = []
        df = self.h1_df.reset_index()
        for i in range(1, len(df)-1):
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            next_ = df.iloc[i+1]
            # Бычий OB
            if prev['close'] < prev['open']:
                if curr['close'] < curr['open']:
                    if next_['close'] > next_['open']:
                        if next_['high'] > max(curr['open'], curr['close']):
                            if next_['close'] > curr['open']:
                                low, high = self.get_body_range(curr)
                                ob = {}
                                ob['type'] = 'bullish'
                                ob['datetime'] = curr['datetime']
                                ob['low'] = low
                                ob['high'] = high
                                obs.append(ob)
            # Медвежий OB
            if prev['close'] > prev['open']:
                if curr['close'] > curr['open']:
                    if next_['close'] < next_['open']:
                        if next_['low'] < min(curr['open'], curr['close']):
                            if next_['close'] < curr['open']:
                                low, high = self.get_body_range(curr)
                                ob = {}
                                ob['type'] = 'bearish'
                                ob['datetime'] = curr['datetime']
                                ob['low'] = low
                                ob['high'] = high
                                obs.append(ob)
        return obs

    def find_imbalances(self):
        fvgs = []
        df = self.m15_df.reset_index()
        for i in range(1, len(df)-1):
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            next_ = df.iloc[i+1]
            # Бычий FVG
            if prev['high'] < next_['low']:
                fvg = {}
                fvg['type'] = 'bullish'
                fvg['datetime'] = curr['datetime']
                fvg['low'] = prev['high']
                fvg['high'] = next_['low']
                fvgs.append(fvg)
            # Медвежий FVG
            if prev['low'] > next_['high']:
                fvg = {}
                fvg['type'] = 'bearish'
                fvg['datetime'] = curr['datetime']
                fvg['low'] = next_['high']
                fvg['high'] = prev['low']
                fvgs.append(fvg)
        return fvgs

    def combine_ob_and_fvg(self):
        obs = self.find_order_blocks()
        fvgs = self.find_imbalances()
        result = []
        for ob in obs:
            ob_time = ob['datetime'].strftime('%H:%M %d.%m.%Y')
            ob_range = f"{ob['low']:.2f}$-{ob['high']:.2f}$"
            ob_row = {}
            ob_row['Type'] = 'Order Block'
            ob_row['Direction'] = ob['type'].capitalize()
            ob_row['Time'] = ob_time
            ob_row['Price Range'] = ob_range
            result.append(ob_row)
            for fvg in fvgs:
                if fvg['type'] == ob['type']:
                    if fvg['low'] < ob['high']:
                        if fvg['high'] > ob['low']:
                            fvg_low = max(fvg['low'], ob['low'])
                            fvg_high = min(fvg['high'], ob['high'])
                            fvg_time = fvg['datetime'].strftime('%H:%M %d.%m.%Y')
                            fvg_range = f"{fvg_low:.2f}$-{fvg_high:.2f}$"
                            fvg_row = {}
                            fvg_row['Type'] = 'Imbalance'
                            fvg_row['Direction'] = fvg['type'].capitalize()
                            fvg_row['Time'] = fvg_time
                            fvg_row['Price Range'] = fvg_range
                            result.append(fvg_row)
        df = pd.DataFrame(result)
        return df

    def save_results(self, output_file):
        df = self.combine_ob_and_fvg()
        df.to_excel(output_file, index=False)
        print(df.head(10))

def main():
    analyzer = MarketAnalyzer('correct NQ 06-25 20250319-20250320.csv')
    analyzer.prepare_timeframes()
    analyzer.save_results('market_analysis_results.xlsx')

if __name__ == '__main__':
    main() 