using Pkg
Pkg.activate(".")

using CSV, DataFrames, HTTP, ZipFile, Dates, Statistics

# Configuration
kf_url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/30_Industry_Portfolios_daily_CSV.zip"
vix_url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
data_dir = "../data"
mkpath(data_dir)

# 1. Download and Extract Kenneth French Data
println("Downloading Kenneth French 30 Industry Portfolios...")
res = HTTP.get(kf_url)
zarchive = ZipFile.Reader(IOBuffer(res.body))
kf_file = zarchive.files[1]

lines = readlines(kf_file)
start_idx = findfirst(x -> length(x) > 8 && match(r"^\d{8}", x) !== nothing, lines)
end_idx = findnext(x -> x == "" || match(r"^\D", x) !== nothing, lines, start_idx)
if end_idx === nothing
    end_idx = length(lines)
end
end_idx -= 1

header_line = lines[start_idx - 1]
header = string("Date,", header_line)

data_lines = vcat([header], lines[start_idx:end_idx])
df_kf = CSV.read(IOBuffer(join(data_lines, "\n")), DataFrame; header=1)

df_kf.Date = Dates.Date.(string.(df_kf.Date), "yyyymmdd")
df_kf = rename(df_kf, [Symbol(strip(string(names(df_kf)[i]))) for i in 1:ncol(df_kf)])

for col in names(df_kf)[2:end]
    df_kf[!, col] = tryparse.(Float64, string.(df_kf[!, col]))
    df_kf[!, col] = [v !== nothing && v <= -99.0 ? missing : v for v in df_kf[!, col]]
end

# 2. Download VIX Data
println("Downloading VIX data from CBOE...")
res_vix = HTTP.get(vix_url)
df_vix = CSV.read(IOBuffer(res_vix.body), DataFrame)

df_vix.DATE = Dates.Date.(df_vix.DATE, "mm/dd/yyyy")
df_vix = rename(df_vix, :DATE => :Date, :CLOSE => :VIX)

# 3. Merge Datasets
println("Merging datasets...")
df_merged = innerjoin(df_kf, df_vix[:, [:Date, :VIX]], on=:Date)
df_merged = df_merged[df_merged.Date .>= Date("1990-01-01"), :]

returns_cols = names(df_merged)[2:end-1] # all except Date and VIX

# Forward fill missing values
for col in names(df_merged)
    for i in 2:nrow(df_merged)
        if ismissing(df_merged[i, col])
            df_merged[i, col] = df_merged[i-1, col]
        end
    end
end
dropmissing!(df_merged)

# Convert percentage returns to decimals
for col in returns_cols
    df_merged[!, col] = Float64.(df_merged[!, col]) ./ 100.0
end

# Calculate market proxy as equal-weight average of the 30 industries
mat_rets = Matrix{Float64}(df_merged[:, returns_cols])
df_merged[!, :MarketReturn] = vec(mean(mat_rets, dims=2))

# Calculate cumulative wealth and positive 63-day trailing Drawdown: D_t = 1 - P_t / max_{s in [t-63, t]} P_s in [0, 1]
wealth = cumprod(1.0 .+ df_merged.MarketReturn)
drawdown = zeros(length(wealth))
for i in 1:length(wealth)
    peak = maximum(wealth[max(1, i-63):i]) # 63-day trailing peak
    drawdown[i] = max(0.0, 1.0 - wealth[i] / peak)
end
df_merged[!, :Drawdown] = drawdown

# Calculate log(VIX)
df_merged[!, :logVIX] = log.(Float64.(df_merged.VIX))

println("Writing final aligned data...")
CSV.write(joinpath(data_dir, "aligned_market_data.csv"), df_merged)
println("Data processing complete. $(nrow(df_merged)) rows written.")
