import pandas as pd
from typing import List, Dict

class MarketAnalyzer:
    def __init__(self, csv_file: str):
        self.df = self._load_data(csv_file)
        self.h1_df = None
        self.m15_df = None

    def _load_data(self, csv_file: str) -> pd.DataFrame:
        df = pd.read_csv(csv_file, names=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d %H%M%S')
        return df.set_index('datetime')

    def prepare_timeframes(self):
        self.h1_df = self.df.resample('h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        self.m15_df = self.df.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

    def _get_body_range(self, row) -> (float, float):
        body_low = min(row['open'], row['close'])
        body_high = max(row['open'], row['close'])
        body_size = abs(row['open'] - row['close'])
        shadow_size = max(row['high'] - body_high, body_low - row['low'])
        if shadow_size > body_size:
            return row['low'], row['high']
        else:
            return body_low, body_high

    def find_order_blocks(self) -> List[Dict]:
        obs = []
        df = self.h1_df.reset_index()
        for i in range(1, len(df)-1):
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            next_ = df.iloc[i+1]
            # Бычий OB: красная (медвежья), маленькая красная (откат), затем зеленая (бычья)
            if prev['close'] < prev['open'] and curr['close'] < curr['open'] and next_['close'] > next_['open']:
                # Зеленая свеча перекрывает диапазон откатной
                if next_['high'] > max(curr['open'], curr['close']) and next_['close'] > curr['open']:
                    low, high = self._get_body_range(curr)
                    obs.append({
                        'type': 'bullish',
                        'datetime': curr['datetime'],
                        'low': low,
                        'high': high
                    })
            # Медвежий OB: зеленая (бычья), маленькая зеленая (откат), затем красная (медвежья)
            if prev['close'] > prev['open'] and curr['close'] > curr['open'] and next_['close'] < next_['open']:
                if next_['low'] < min(curr['open'], curr['close']) and next_['close'] < curr['open']:
                    low, high = self._get_body_range(curr)
                    obs.append({
                        'type': 'bearish',
                        'datetime': curr['datetime'],
                        'low': low,
                        'high': high
                    })
        return obs

    def find_imbalances(self) -> List[Dict]:
        fvgs = []
        df = self.m15_df.reset_index()
        for i in range(1, len(df)-1):
            prev = df.iloc[i-1]
            curr = df.iloc[i]
            next_ = df.iloc[i+1]
            # Бычий FVG: гэп между high предыдущей и low следующей
            if prev['high'] < next_['low']:
                fvgs.append({
                    'type': 'bullish',
                    'datetime': curr['datetime'],
                    'low': prev['high'],
                    'high': next_['low']
                })
            # Медвежий FVG: гэп между low предыдущей и high следующей
            if prev['low'] > next_['high']:
                fvgs.append({
                    'type': 'bearish',
                    'datetime': curr['datetime'],
                    'low': next_['high'],
                    'high': prev['low']
                })
        return fvgs

    def combine_ob_and_fvg(self) -> pd.DataFrame:
        obs = self.find_order_blocks()
        fvgs = self.find_imbalances()
        result = []
        for ob in obs:
            # Формат времени как в исходном файле
            ob_time = ob['datetime'].strftime('%H:%M %d.%m.%Y')
            ob_range = f"{ob['low']:.2f}$-{ob['high']:.2f}$"
            result.append({
                'Type': 'Order Block',
                'Direction': ob['type'].capitalize(),
                'Time': ob_time,
                'Price Range': ob_range
            })
            for fvg in fvgs:
                # Совпадение направления и попадание в диапазон блока
                if fvg['type'] == ob['type'] and fvg['low'] < ob['high'] and fvg['high'] > ob['low']:
                    # Обрезаем границы по блоку
                    fvg_low = max(fvg['low'], ob['low'])
                    fvg_high = min(fvg['high'], ob['high'])
                    fvg_time = fvg['datetime'].strftime('%H:%M %d.%m.%Y')
                    fvg_range = f"{fvg_low:.2f}$-{fvg_high:.2f}$"
                    result.append({
                        'Type': 'Imbalance',
                        'Direction': fvg['type'].capitalize(),
                        'Time': fvg_time,
                        'Price Range': fvg_range
                    })
        return pd.DataFrame(result)

    def save_results(self, output_file: str):
        df = self.combine_ob_and_fvg()
        df.to_excel(output_file, index=False)
        print(df.head(10))

def main():
    analyzer = MarketAnalyzer('correct NQ 06-25 20250319-20250320.csv')
    analyzer.prepare_timeframes()
    analyzer.save_results('market_analysis_results.xlsx')

if __name__ == '__main__':
    main()