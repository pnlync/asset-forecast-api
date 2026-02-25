import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm


# ==========================================
# 1. The Forecast Engine
# Geometric Brownian Motion (GBM) Monte Carlo simulation
# ==========================================
def forecast_engine(ticker: str, days: int = 7, n_simulations: int = 10_000):
    # Use GBM to simulate stock price paths in the future

    # 1. Get the past data (1 year)
    data = yf.download(ticker, period="1y", progress=False)
    if data.empty:
        raise ValueError(f"Unable to fetch data for {ticker}")

    prices = data['Close'].values.flatten()
    last_price = prices[-1]

    # 2. Calculate historical log returns
    # log_returns = ln(S_t / S_{t-1})
    log_returns_all = np.log(prices[1:] / prices[:-1])
    sigma_window = 30
    log_returns_recent = log_returns_all[-sigma_window:]

    # 3. Calculate historical drift (mu) and volatility (sigma)
    # Note: We use daily data here, so delta_t = 1
    sigma_daily = np.std(log_returns_recent, ddof=1)
    mu_daily = np.mean(log_returns_all) + (sigma_daily ** 2) / 2

    # 4. Monte Carlo Simulation (Vectorized Operations)
    # Initialize path matrix: shape (days + 1, n_simulations)
    price_paths = np.zeros((days + 1, n_simulations))
    price_paths[0] = last_price

    # Generate standard normal random numbers Z for all days and simulations
    Z = np.random.standard_normal((days, n_simulations))

    # Simulate price paths day by day
    drift = mu_daily - (sigma_daily ** 2) / 2
    for t in range(1, days + 1):
        # GBM formula: S_t = S_{t-1} * exp((mu - sigma^2 / 2) * dt + sigma * sqrt(dt) * Z)
        # Since dt = 1 (daily level), the formula can be simplified
        shock = sigma_daily * Z[t - 1]
        price_paths[t] = price_paths[t - 1] * np.exp(drift + shock)

    expected_prices = np.mean(price_paths, axis=1)
    return price_paths, expected_prices


# ==========================================
# 2. The VaR Engine
# (number of assets must be less than sigma_window=30 - 1,
# i.e. N <= 28)
# ==========================================
def var_engine(tickers: list, weights: np.ndarray, portfolio_value: float = 1000000, days: int = 7,
               n_simulations: int = 10000, conf_levels: list = [0.95, 0.99]):
    """
    计算多资产投资组合的 VaR。使用 Cholesky 分解处理资产间的相关性。
    """
    # 1. 获取所有资产的历史数据
    data = yf.download(tickers, period="1y", progress=False)['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()

    data = data.dropna()  # 处理缺失值

    # 对齐最新的价格和权重
    latest_prices = data.iloc[-1].values

    # 2. 计算每日对数收益率的均值和协方差矩阵
    log_returns_all = np.log(data / data.shift(1)).dropna()
    sigma_window = 30
    log_returns_recent = log_returns_all.iloc[-sigma_window:]

    recent_variance = log_returns_recent.std(ddof=1).values ** 2
    mu_vector = log_returns_all.mean().values + recent_variance / 2
    cov_matrix = log_returns_recent.cov().values

    # 3. Cholesky 分解 (处理相关性)
    # 找到下三角矩阵 L，使得 L * L^T = 协方差矩阵
    # n_assets (number of assets) must be strictly less than sigma_window=30 - 1,
    # this is due to the requirement of Cholesky decomposition
    L = np.linalg.cholesky(cov_matrix)

    n_assets = len(tickers) # n_assets < sigma_window=30 -1
    # 初始化投资组合价值路径
    portfolio_paths = np.zeros((days + 1, n_simulations))
    portfolio_paths[0] = portfolio_value

    # 计算每个资产在投资组合中的初始股数
    shares = (portfolio_value * weights) / latest_prices

    # 记录每个资产的模拟价格，初始为最新价格
    simulated_prices = np.tile(latest_prices, (n_simulations, 1))

    drift = mu_vector - np.diag(cov_matrix) / 2
    for t in range(1, days + 1):
        # 生成独立的标准正态分布随机数: 形状为 (n_simulations, n_assets)
        Z = np.random.standard_normal((n_simulations, n_assets))

        # 引入相关性: X = Z * L^T
        correlated_shocks = Z @ L.T

        # 模拟每支股票的单日价格变化
        # S_t = S_{t-1} * exp((mu - sigma^2/2)*dt + correlated_shock)
        # 注意: 协方差矩阵对角线元素已经是方差 (sigma^2)，其平方根就是 sigma，包含在了 L 中
        simulated_prices = simulated_prices * np.exp(drift + correlated_shocks)

        # 计算当天的投资组合总价值
        portfolio_paths[t] = np.sum(simulated_prices * shares, axis=1)

    # 4. 计算 VaR (风险价值)
    # 7天后的预期损益 (PnL)
    final_values = portfolio_paths[-1]
    pnl = final_values - portfolio_value

    results = {}
    for conf in conf_levels:
        # VaR 是损失分布的分位数。因为 PnL 中损失为负数，我们取 (1 - conf) 的分位数
        percentile = (1 - conf) * 100
        var_value = -np.percentile(pnl, percentile)
        results[f"{int(conf * 100)}%"] = var_value

    return portfolio_paths, pnl, results


# ==========================================
# 3. Testing (本地测试)
# ==========================================
if __name__ == "__main__":
    print("--- 启动本地测试 ---\n")

    # 测试预测引擎
    test_ticker = "AAPL"
    print(f"正在运行 {test_ticker} 的预测引擎...")
    paths, exp_prices = forecast_engine(test_ticker, days=7, n_simulations=10000)
    print(f"\n{test_ticker} 未来 7 天的每日预期价格:")
    print(f"当前价格 (Day 0): ${exp_prices[0]:.2f}")
    for day in range(1, len(exp_prices)):
        print(f"Day {day} 预测价格: ${exp_prices[day]:.2f}")
    print("\n")

    # 测试 VaR 引擎
    portfolio_tickers = ["AAPL", "MSFT", "GOOGL"]
    # 假设等权重配置
    weights = np.array([1 / 3, 1 / 3, 1 / 3])
    initial_investment = 1000000  # 一百万美元投资组合

    print(f"正在运行投资组合 {portfolio_tickers} 的 VaR 引擎 (初始资金: ${initial_investment:,.2f})...")
    port_paths, pnl, var_results = var_engine(
        tickers=portfolio_tickers,
        weights=weights,
        portfolio_value=initial_investment,
        days=7,
        n_simulations=10000
    )

    print("7天投资组合风险价值 (Value at Risk):")
    for conf, var in var_results.items():
        print(f"  {conf} 置信区间下的最坏情况损失: ${var:,.2f}")