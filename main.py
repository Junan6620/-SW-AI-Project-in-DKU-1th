import sys
import yfinance as yf
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import ta
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class StockAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stockist Pro")
        # 창 아이콘 설정
        icon = QIcon("./stock_icon.png")
        self.setWindowIcon(icon)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton {
                background-color: #2962ff;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
            QLineEdit {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #333333;
                padding: 8px;
                border-radius: 6px;
                font-size: 14px;
                selection-background-color: #2962ff;
            }
            QLineEdit:focus {
                border: 2px solid #2962ff;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #333333;
                padding: 10px;
                border-radius: 8px;
                font-size: 14px;
                line-height: 1.6;
                selection-background-color: #2962ff;
            }
            QTextEdit:focus {
                border: 2px solid #2962ff;
            }
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                border: none;
                gridline-color: #555555;
            }
            QTableWidget QHeaderView::section {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
            }
            QTableWidget::item {
                border: 1px solid #555555;
                padding: 5px;
            }
            QComboBox {
                background-color: #1e1e1e;
                color: white;
                border: 2px solid #333333;
                border-radius: 6px;
                padding: 5px;
                min-width: 6em;
            }
            QComboBox:hover {
                border: 2px solid #2962ff;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e1e1e;
                color: white;
                selection-background-color: #2962ff;
                border: 1px solid #555555;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #555555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QMessageBox {
                background-color: #1e1e1e;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                min-width: 300px;
            }
            QMessageBox QPushButton {
                background-color: #2962ff;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        self.initUI()

    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 검색 영역
        search_layout = QHBoxLayout()
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("티커 심볼 입력 (예: AAPL)")
        self.ticker_input.returnPressed.connect(self.analyze_stock)
        self.ticker_input.textChanged.connect(self.on_text_changed)
        search_button = QPushButton("분석")
        search_button.clicked.connect(self.analyze_stock)
        search_layout.addWidget(self.ticker_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        # 탭 위젯 생성
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #555555;
                background: #1a1a1a;
            }
            QTabBar::tab {
                background: #333333;
                color: white;
                padding: 8px 12px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #2962ff;
            }
        """)

        # 기본 정보 탭
        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        info_layout.addWidget(self.info_text)
        tabs.addTab(self.info_tab, "기본 정보")

        # 기술적 분석 탭
        self.technical_tab = QWidget()
        technical_layout = QVBoxLayout(self.technical_tab)
        self.technical_text = QTextEdit()
        self.technical_text.setReadOnly(True)
        technical_layout.addWidget(self.technical_text)
        tabs.addTab(self.technical_tab, "기술적 분석")

        # 적정주가 분석 탭
        self.valuation_tab = QWidget()
        valuation_layout = QVBoxLayout(self.valuation_tab)
        self.valuation_text = QTextEdit()
        self.valuation_text.setReadOnly(True)
        valuation_layout.addWidget(self.valuation_text)
        
        per_layout = QHBoxLayout()
        self.industry_per_input = QLineEdit()
        self.industry_per_input.setPlaceholderText("업계 평균 PER 입력")
        update_button = QPushButton("적정주가 재계산")
        update_button.clicked.connect(self.update_valuation)
        per_layout.addWidget(self.industry_per_input)
        per_layout.addWidget(update_button)
        valuation_layout.addLayout(per_layout)
        tabs.addTab(self.valuation_tab, "적정주가 분석")

        # 재무제표 탭
        self.financial_tab = QWidget()
        self.financial_layout = QVBoxLayout(self.financial_tab)
        tabs.addTab(self.financial_tab, "재무제표")

        # 차트 분석 탭
        self.chart_tab = QWidget()
        chart_layout = QVBoxLayout(self.chart_tab)
        
        # 차트 컨트롤 영역
        control_layout = QHBoxLayout()
        
        # 기간 선택
        period_layout = QHBoxLayout()
        period_label = QLabel("기간:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["1개월", "3개월", "6개월", "1년", "5년"])
        self.period_combo.setCurrentText("6개월")
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_combo)
        
        # 차트 업데이트 버튼
        update_chart_btn = QPushButton("차트 업데이트")
        update_chart_btn.clicked.connect(self.update_chart)
        
        control_layout.addLayout(period_layout)
        control_layout.addStretch()
        control_layout.addWidget(update_chart_btn)
        chart_layout.addLayout(control_layout)
        
        # Matplotlib 차트
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas)
        
        tabs.addTab(self.chart_tab, "차트 분석")

        layout.addWidget(tabs)
        self.setMinimumSize(1024, 600)

    def create_financial_table(self):
        # 기존 테이블과 위젯 제거
        for i in reversed(range(self.financial_layout.count())): 
            widget = self.financial_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # 새 테이블 생성
        table = QTableWidget()
        table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                border: none;
                gridline-color: #333333;
            }
            QTableWidget::item {
                background-color: #1e1e1e;
                color: white;
                border-bottom: 1px solid #333333;
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #2962ff;
            }
            QTableWidget QHeaderView::section {
                background-color: #252525;
                color: white;
                border: none;
                border-bottom: 1px solid #333333;
                padding: 5px;
            }
            QTableWidget QHeaderView::section:horizontal {
                border-right: 1px solid #333333;
            }
            QTableWidget QHeaderView::section:vertical {
                border-right: 1px solid #333333;
            }
            QScrollBar:vertical {
                background-color: #1e1e1e;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4a4a4a;
            }
            QScrollBar:horizontal {
                background-color: #1e1e1e;
                height: 12px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background-color: #404040;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                height: 0px;
                width: 0px;
            }
        """)

        # 테이블 속성 설정
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(True)
        table.setAlternatingRowColors(False)  # 단일 배경색 사용
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        table.verticalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        return table

    def update_chart(self):
        ticker = self.ticker_input.text().upper()
        if not ticker:
            return

        try:
            # 기존 figure 제거
            plt.close(self.figure)
            
            # 한글 폰트 설정 재확인
            if not plt.rcParams['font.family'] in ['Malgun Gothic', '맑은 고딕', 'NanumGothic', '나눔고딕']:
                import matplotlib.font_manager as fm
                # 설치된 폰트 중 한글 폰트 찾기
                for font in fm.findSystemFonts():
                    try:
                        font_name = fm.FontProperties(fname=font).get_name()
                        if any(korean_font in font_name for korean_font in ['Malgun Gothic', '맑은 고딕', 'NanumGothic', '나눔고딕']):
                            plt.rcParams['font.family'] = font_name
                            break
                    except:
                        continue
            
            plt.rcParams['axes.unicode_minus'] = False
            
            self.figure = plt.figure(figsize=(12, 7))
            self.ax = self.figure.add_axes([0.1, 0.2, 0.8, 0.7])  # [left, bottom, width, height]
            
            period_interval_map = {
                "1개월": ("1mo", "15m"),
                "3개월": ("3mo", "1h"),
                "6개월": ("6mo", "1d"),
                "1년": ("1y", "1d"),
                "5년": ("5y", "1wk")
            }
            
            selected_period = self.period_combo.currentText()
            period, interval = period_interval_map[selected_period]
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError("데이터를 가져올 수 없습니다.")
            
            dates = hist.index.values
            closes = hist['Close'].values
            volumes = hist['Volume'].values
            
            # 스타일 설정
            self.figure.set_facecolor('#1e1e1e')
            self.ax.set_facecolor('#1e1e1e')
            
            # 가격 차트
            color_price = '#2962ff'
            self.ax.plot(dates, closes, label='종가', color=color_price, linewidth=1.5)
            
            # 이동평균선
            if selected_period in ["1개월", "3개월"]:
                ma5 = pd.Series(closes).rolling(window=5, min_periods=1).mean().values
                ma10 = pd.Series(closes).rolling(window=10, min_periods=1).mean().values
                self.ax.plot(dates, ma5, label='5일 이동평균', color='#ff6b6b', linestyle='--', linewidth=1)
                self.ax.plot(dates, ma10, label='10일 이동평균', color='#51cf66', linestyle='--', linewidth=1)
            else:
                ma20 = pd.Series(closes).rolling(window=20, min_periods=1).mean().values
                ma50 = pd.Series(closes).rolling(window=50, min_periods=1).mean().values
                self.ax.plot(dates, ma20, label='20일 이동평균', color='#ff6b6b', linestyle='--', linewidth=1)
                self.ax.plot(dates, ma50, label='50일 이동평균', color='#51cf66', linestyle='--', linewidth=1)
            
            # 가격 축 스타일 설정
            self.ax.tick_params(axis='y', colors=color_price)
            self.ax.yaxis.label.set_color(color_price)
            
            # 거래량 차트 (아래 subplot으로 변경)
            volume_ax = self.figure.add_axes([0.1, 0.1, 0.8, 0.1])  # [left, bottom, width, height]
            volume_color = '#45aaf2'
            volume_ax.bar(dates, volumes, color=volume_color, alpha=0.3)
            volume_ax.set_facecolor('#1e1e1e')
            
            # 거래량 축 스타일 설정
            volume_ax.tick_params(axis='y', colors=volume_color, labelsize=8)
            volume_ax.yaxis.label.set_color(volume_color)
            volume_ax.set_ylabel('거래량', color=volume_color, fontsize=10)
            
            # x축은 volume_ax에만 표시
            self.ax.set_xticks([])
            volume_ax.tick_params(axis='x', colors='white', labelsize=8, rotation=45)
            
            # 날짜 포맷 설정
            if selected_period in ["1개월", "3개월"]:
                date_format = '%m-%d %H:%M'
            else:
                date_format = '%Y-%m-%d'
            
            volume_ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter(date_format))
            
            # 그리드 설정
            self.ax.grid(True, linestyle='--', alpha=0.2, color='white')
            volume_ax.grid(False)
            
            # 테두리 설정
            for ax in [self.ax, volume_ax]:
                for spine in ax.spines.values():
                    spine.set_color('white')
                    spine.set_linewidth(0.5)
                ax.tick_params(colors='white', labelsize=8)
            
            # 레이블 설정
            interval_display = {
                "15m": "15분",
                "1h": "1시간",
                "1d": "일간",
                "1wk": "주간"
            }
            
            self.ax.set_title(f"{ticker} 주가 차트 ({selected_period}, {interval_display[interval]} 데이터)", 
                            color='white', pad=20, fontsize=12)
            self.ax.set_ylabel("주가 ($)", color=color_price, fontsize=10)
            
            # 범례 설정
            legend = self.ax.legend(facecolor='#1e1e1e', 
                                edgecolor='#333333', 
                                labelcolor='white', 
                                fontsize=8,
                                loc='upper left')
            legend.get_frame().set_alpha(0.7)
            
            # 캔버스 업데이트
            if hasattr(self, 'canvas'):
                self.financial_layout.removeWidget(self.canvas)
                self.canvas.deleteLater()
            
            self.canvas = FigureCanvas(self.figure)
            self.chart_tab.layout().addWidget(self.canvas)

        except Exception as e:
            error_msg = str(e)
            if "data not available" in error_msg:
                error_msg = "선택한 기간에 대한 데이터를 가져올 수 없습니다.\n더 짧은 기간을 선택해주세요."
            self.show_error_message("에러", f"차트 업데이트 중 오류가 발생했습니다:\n{error_msg}")

    def show_error_message(self, title, message):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #1e1e1e;
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                min-width: 300px;
            }
            QPushButton {
                background-color: #2962ff;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #1e88e5;
            }
        """)
        msg_box.exec_()

    def on_text_changed(self, text):
        cursor_pos = self.ticker_input.cursorPosition()
        self.ticker_input.setText(text.upper())
        self.ticker_input.setCursorPosition(cursor_pos)

    def analyze_stock(self):
        ticker = self.ticker_input.text().upper()
        if not ticker:
            return

        try:
            stock = yf.Ticker(ticker)
            
            # 기본 정보 분석
            info = stock.info
            info_text = f"""
            회사명: {info.get('longName', 'N/A')}
            섹터: {info.get('sector', 'N/A')}
            산업: {info.get('industry', 'N/A')}
            시가총액: ${info.get('marketCap', 0):,.2f}
            52주 최고가: ${info.get('fiftyTwoWeekHigh', 0):,.2f}
            52주 최저가: ${info.get('fiftyTwoWeekLow', 0):,.2f}
            Beta: {info.get('beta', 'N/A')}
            배당수익률: {info.get('dividendYield', 0) * 100:.2f}%
            """
            self.info_text.setText(info_text)

            # 기술적 분석
            hist = stock.history(period="1y")
            
            # RSI 계산
            rsi = ta.momentum.RSIIndicator(hist['Close']).rsi()
            current_rsi = rsi.iloc[-1]
            
            # MACD 계산
            macd = ta.trend.MACD(hist['Close'])
            current_macd = macd.macd().iloc[-1]
            current_signal = macd.macd_signal().iloc[-1]
            
            # 볼린저 밴드
            bollinger = ta.volatility.BollingerBands(hist['Close'])
            current_middle = bollinger.bollinger_mavg().iloc[-1]
            current_upper = bollinger.bollinger_hband().iloc[-1]
            current_lower = bollinger.bollinger_lband().iloc[-1]
            
            technical_text = f"""
            현재가: ${hist['Close'].iloc[-1]:.2f}
            
            RSI (14): {current_rsi:.2f}
            RSI 신호: {"과매수" if current_rsi > 70 else "과매도" if current_rsi < 30 else "중립"}
            
            MACD: {current_macd:.2f}
            MACD Signal: {current_signal:.2f}
            MACD 신호: {"매수" if current_macd > current_signal else "매도"}
            
            볼린저 밴드:
            상단: ${current_upper:.2f}
            중간: ${current_middle:.2f}
            하단: ${current_lower:.2f}
            
            이동평균선:
            MA20: ${hist['Close'].rolling(window=20).mean().iloc[-1]:.2f}
            MA50: ${hist['Close'].rolling(window=50).mean().iloc[-1]:.2f}
            MA200: ${hist['Close'].rolling(window=200).mean().iloc[-1]:.2f}
            """
            self.technical_text.setText(technical_text)

            # 적정주가 분석
            self.update_valuation()

            # 재무제표 분석
            financials = stock.financials
            if not financials.empty:
                # 새 테이블 생성
                table = self.create_financial_table()
                
                # 테이블 크기 설정
                table.setRowCount(len(financials.index))
                table.setColumnCount(len(financials.columns))
                
                # 헤더 설정
                headers = [date.strftime('%Y-%m-%d') for date in financials.columns]
                table.setHorizontalHeaderLabels(headers)
                table.setVerticalHeaderLabels(financials.index)
                
                # 데이터 채우기
                for i in range(len(financials.index)):
                    for j in range(len(financials.columns)):
                        value = financials.iloc[i, j]
                        formatted_value = f"${value:,.0f}" if pd.notnull(value) else "N/A"
                        item = QTableWidgetItem(formatted_value)
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                        table.setItem(i, j, item)
                
                # 열 너비 자동 조정
                table.resizeColumnsToContents()
                
                # 새 테이블을 레이아웃에 추가
                self.financial_layout.addWidget(table)

            # 차트 업데이트
            self.update_chart()

        except Exception as e:
            self.show_error_message("에러", f"데이터 분석 중 오류가 발생했습니다:\n{str(e)}")
    
    def fetch_per_eps(self, ticker):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            eps = info.get("trailingEps", None)
            if eps is None:
                raise ValueError("EPS 데이터를 가져올 수 없습니다.")

            url = f"https://finance.yahoo.com/quote/{ticker}"
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code != 200:
                raise ConnectionError("Yahoo Finance 페이지에 접근할 수 없습니다.")
            
            soup = BeautifulSoup(response.text, "html.parser")
            pe_ratio_element = soup.find("fin-streamer", {"data-field": "trailingPE"})
            
            if pe_ratio_element is None or not pe_ratio_element.text.strip():
                raise ValueError("PE Ratio 데이터를 가져올 수 없습니다.")
            
            try:
                pe_ratio = float(pe_ratio_element.text.replace(",", ""))
                return eps, pe_ratio
            except ValueError:
                raise ValueError("PE Ratio 값을 숫자로 변환할 수 없습니다.")

        except Exception as e:
            print(f"오류 발생: {e}")
            return None, None

    def fetch_grow_rate(self, ticker):
        try:
            Data = yf.Ticker(ticker).history(period="3mo")
            closing_prices = Data['Close']
            start_price = closing_prices.iloc[0]
            end_price = closing_prices.iloc[-1]
            growth_rate = ((end_price - start_price) / start_price) * 100
            return growth_rate
        except Exception as e:
            print(f"성장률 계산 오류: {e}")
            return 0

    def calculate_valuation(self, ticker, industry_per=None):
            eps, per = self.fetch_per_eps(ticker)
            if eps is None or per is None:
                return "데이터를 가져올 수 없습니다."

            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[0]

            # PER 상한선 설정
            adjusted_per = min(per, 50)
            
            try:
                # 1년 데이터 가져오기
                yearly_data = stock.history(period="1y")
                # 분기별 성장률 계산
                quarterly_growth_rates = []
                for i in range(4):
                    if len(yearly_data) >= (i + 1) * 63:
                        start_idx = i * 63
                        end_idx = (i + 1) * 63
                        start_price = yearly_data['Close'].iloc[start_idx]
                        end_price = yearly_data['Close'].iloc[end_idx - 1]
                        quarter_growth = ((end_price - start_price) / start_price) * 100
                        quarterly_growth_rates.append(quarter_growth)
                
                if quarterly_growth_rates:
                    avg_growth_rate = sum(quarterly_growth_rates) / len(quarterly_growth_rates)
                else:
                    avg_growth_rate = self.fetch_grow_rate(ticker)
                    
                growth_rate = min(max(avg_growth_rate, -30), 30)
            except Exception as e:
                print(f"성장률 계산 오류: {e}")
                growth_rate = 0

            # PEG 비율을 고려한 적정주가 계산
            if growth_rate > 0:
                peg_ratio = adjusted_per / growth_rate
                if peg_ratio > 2:  # PEG 비율이 2 이상이면 고평가
                    suitable_price = eps * (adjusted_per * 0.8)  # 20% 할인
                else:
                    suitable_price = eps * (adjusted_per + growth_rate * 0.5)  # 성장률의 50%만 반영
            else:
                suitable_price = eps * adjusted_per  # 성장률이 없거나 마이너스일 경우

            valuation_text = f"""
            EPS (주당순이익): ${eps:.2f}
            PER (주가수익비율): {per:.2f} {'(고평가 위험)' if per > 50 else ''}
            조정된 PER: {adjusted_per:.2f}
            1년 평균 분기 성장률: {growth_rate:.2f}%
            현재 주가: ${current_price:.2f}
            적정주가: ${suitable_price:.2f}
            
            PEG 비율: {(per/growth_rate if growth_rate > 0 else 'N/A')}
            
            분석 결과: """

            # 고평가/저평가 판단 기준 변경
            price_diff_ratio = abs(current_price - suitable_price) / suitable_price * 100

            if price_diff_ratio <= 10:
                valuation_text += "적정 가격대에서 거래되고 있습니다."
            elif current_price > suitable_price:
                if price_diff_ratio > 30:
                    valuation_text += "매우 고평가 되어 있습니다. 투자에 신중을 기해야 합니다."
                else:
                    valuation_text += "다소 고평가 되어 있습니다."
            else:
                if price_diff_ratio > 30:
                    valuation_text += "매우 저평가 되어 있습니다. 단, 해당 기업의 재무상태와 시장 상황을 추가로 검토하세요."
                else:
                    valuation_text += "다소 저평가 되어 있습니다."

            if industry_per:
                try:
                    industry_per = float(industry_per)
                    per_ratio = per / industry_per
                    valuation_text += f"\n\n업종 평균 PER과의 비교:"
                    if per_ratio > 1.5:
                        valuation_text += f"\n현재 PER이 업종 평균 대비 {per_ratio:.1f}배로 매우 고평가 상태입니다."
                    elif per_ratio > 1.2:
                        valuation_text += f"\n현재 PER이 업종 평균 대비 {per_ratio:.1f}배로 다소 고평가 상태입니다."
                    elif per_ratio > 0.8:
                        valuation_text += f"\n현재 PER이 업종 평균 대비 적정 수준입니다. (업종 평균의 {per_ratio:.1f}배)"
                    else:
                        valuation_text += f"\n현재 PER이 업종 평균 대비 {per_ratio:.1f}배로 저평가 상태입니다."
                except:
                    pass

            return valuation_text

    def update_valuation(self):
        ticker = self.ticker_input.text().upper()
        if not ticker:
            return
        
        industry_per = self.industry_per_input.text()
        if industry_per:
            try:
                industry_per = float(industry_per)
            except:
                industry_per = None
        
        valuation_text = self.calculate_valuation(ticker, industry_per)
        self.valuation_text.setText(valuation_text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StockAnalyzer()
    ex.show()
    sys.exit(app.exec_())
