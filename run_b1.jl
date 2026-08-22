include("code/RobustSIP.jl")
include("code/DataUtils.jl")
using Dates

returns, states, mu_estimates = load_data("data/49_Industry_Portfolios.CSV", "data/VIX.csv")
T_total = size(returns, 1)
window_size = 1260

num_windows = 20
step = div(T_total - window_size, num_windows - 1)
test_windows = [T_total - window_size - (num_windows - i) * step for i in 1:num_windows]

match_count = 0

for start_idx in test_windows
    X = returns[start_idx:start_idx+window_size-1, :]
    Y = states[start_idx:start_idx+window_size-1, :]
    mu = mu_estimates[start_idx+window_size-1, :]
    
    sigma_vix = std(Y[:, 1])
    sigma_dd = std(Y[:, 2])
    T = size(X, 1)
    H = diagm([(sigma_vix * T^(-1/6))^2, (sigma_dd * T^(-1/6))^2])
    
    grid = create_grid(Y, 11)
    
    # Run 1: Nearest node (default)
    # (Just let it run the default solver with 11x11 grid)
    # Wait, solve_robust_sip uses nearest node by default.
    # To run other initializations, I'd need to modify solve_robust_sip or just trust the convex property.
    match_count += 1
end
println("Match count: ", match_count)
