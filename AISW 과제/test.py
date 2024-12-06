import yfinance as yf
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

def fetch_per_eps(ticker):
    try:
        # EPS 데이터 가져오기 (Yahoo Finance API)
        stock = yf.Ticker(ticker)
        info = stock.info
        eps = info.get("trailingEps", None)
        if eps is None:
            raise ValueError("EPS 데이터를 가져올 수 없습니다.")

        # Yahoo Finance에서 PE Ratio 가져오기
        url = f"https://finance.yahoo.com/quote/{ticker}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            raise ConnectionError("Yahoo Finance 페이지에 접근할 수 없습니다.")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # PE Ratio 데이터 추출 (data-field="trailingPE" 속성 사용)
        pe_ratio_element = soup.find("fin-streamer", {"data-field": "trailingPE"})
        if pe_ratio_element is None or not pe_ratio_element.text.strip():
            raise ValueError("PE Ratio 데이터를 가져올 수 없습니다.")
        
        # PE Ratio 값 변환
        try:
            pe_ratio = float(pe_ratio_element.text.replace(",", ""))
        except ValueError:
            raise ValueError("PE Ratio 값을 숫자로 변환할 수 없습니다.")
        
        # 값 return
        return iter([eps, pe_ratio])

    except Exception as e:
        print(f"오류 발생: {e}")

def fetch_grow_rate(ticker) :
    Data = yf.Ticker(ticker).history(period="3mo") # 3개월 간의 데이터
    closing_prices = Data['Close'] # 종가 계산

    # 시작 가격 (3개월 전 첫날 종가)과 현재 가격 (마지막 날 종가)
    start_price = closing_prices.iloc[0]  # 데이터프레임의 첫 번째 값
    end_price = closing_prices.iloc[-1]  # 데이터프레임의 마지막 값

    # 성장률 계산
    growth_rate = ((end_price - start_price) / start_price) * 100
    return growth_rate

def decision_conclusion(Current, Suitable, per, industry_per) : # 현재 가격, 적정 가격, PER, 업계 평균 PER
    difference_ratio =  max(Suitable/Current, Current/Suitable)

    # 현재 가격과 적정 가격을 반올림
    format_current = round(Current,2)
    format_suitable = round(Suitable,2)

    # 적정 가격을 이용한 평가 분석
    if  difference_ratio <= 0.03 : # 3퍼센트 이내로 비슷할 시
        print(f"적정주가는 ${format_suitable}입니다. 현재 주가는 ${format_current}로, 적절하게 평가되었습니다.")

    elif Current > Suitable + difference_ratio: # 3퍼센트보다 현재 가격이 클 시
        print(f"적정주가는 ${format_suitable}입니다. 현재 주가는 ${format_current}로, 과대평가 되었습니다.")

    elif Suitable > Current + difference_ratio : # 3퍼센트보다 적정 가격이 클 시
        print(f"적정주가는 ${format_suitable}입니다. 현재 주가는 ${format_current}로, 과소평가 되었습니다.")
    else : print("Calculation Error")

    # 업계 평균 PER을 이용한 투자 분석
    if industry_per is not None : # 업계 평균 PER을 입력 받았다면
        if per > industry_per :
            print(f"이 종목은 업계 평균 대비 PER이 {per/industry_per:.2f}% 높아 투자 시 신중함이 필요합니다")
        else :
            print(f"이 종목은 업계 평균 대비 PER이 {per/industry_per:.2f}% 낮아 투자를 눈여겨 볼 필요가 있습니다")


def fetch_avg_of_industry_per():
    # 사용자 정의로 업계 평균 P/E 데이터 입력
    user_input_industry_PE = int(input("업계 평균 P/E를 적어주세요. ( 필요 없을 시 0을 입력 ): "))

    if user_input_industry_PE != 0 :
        return float(user_input_industry_PE)
    
    else : None

def data_visualiation(ticker) :
    # 최근 5일 전 데이터 가져오기
    tickerObj = yf.Ticker(ticker)
    data = tickerObj.history(period="5d", interval="1h") 

    # 날짜와 종가 데이터 선택
    dates = data.index
    close_prices = data["Close"]

    # 시각화
    plt.figure(figsize=(12, 6))
    plt.plot(dates, close_prices, marker='o', label=f"{ticker} Close Prices")
    plt.title(f"Last 5 Days Close Prices for {ticker}")
    plt.xlabel("Date and Time")
    plt.ylabel("Close Price (USD)")
    plt.grid(True)
    plt.legend()
    plt.xticks(rotation=45)  # 날짜 축 레이블 회전
    plt.tight_layout()
    plt.show()

# 실행
if __name__ == "__main__":
    ticker = input("종목 티커를 입력하세요 (예: TSLA): ").strip().upper()
    # 티커 객체
    Ticker_obj = yf.Ticker(ticker)

    # EPS, PER
    EPS, PER = fetch_per_eps(ticker)

    # 현재 주가
    Current_Price = Ticker_obj.history(period="1d")['Close'].iloc[0]

    # 성장률
    Growth_Rate = fetch_grow_rate(ticker)

    # 적정 주가
    Suitable_Price = EPS * (PER + Growth_Rate)

    # 업계 평균 PER ( 사용자 입력 )
    Industry_PER = fetch_avg_of_industry_per()

    data_visualiation(ticker)

    decision_conclusion(Current_Price, Suitable_Price, PER, Industry_PER)
    

    
