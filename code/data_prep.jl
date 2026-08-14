using Pkg
Pkg.activate(".")
Pkg.add(["CSV", "DataFrames", "HTTP", "ZipFile", "Dates", "TimeSeries"])

using CSV, DataFrames, HTTP, ZipFile, Dates

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

# Read the CSV lines manually since there's header text we need to skip
lines = readlines(kf_file)
# Find the start of the data: look for a line starting with a date like "19260701"
start_idx = findfirst(x -> length(x) > 8 && match(r"^\d{8}", x) !== nothing, lines)
# Find the end of the daily data (often there are annual summaries later)
end_idx = findnext(x -> x == "" || match(r"^\D", x) !== nothing, lines, start_idx)
if end_idx === nothing
    end_idx = length(lines)
end
end_idx -= 1

# Header line is usually just above the start_idx
header_line = lines[start_idx - 1]
# Fix empty first column name
header = string("Date,", header_line)

data_lines = vcat([header], lines[start_idx:end_idx])
df_kf = CSV.read(IOBuffer(join(data_lines, "\n")), DataFrame; header=1)

# Format Date
df_kf.Date = Dates.Date.(string.(df_kf.Date), "yyyymmdd")
df_kf = rename(df_kf, [Symbol(strip(string(names(df_kf)[i]))) for i in 1:ncol(df_kf)])

# Replace missing/error codes (e.g. -99.99 or -999) with missing or previous value
for col in names(df_kf)[2:end]
    df_kf[!, col] = tryparse.(Float64, string.(df_kf[!, col]))
    # Kenneth French missing value is often -99.99
    df_kf[!, col] = [v <= -99.0 ? missing : v for v in df_kf[!, col]]
end

println("Writing KF data to CSV...")
CSV.write(joinpath(data_dir, "30_Industry_Portfolios_daily.csv"), df_kf)

# 2. Download VIX Data
println("Downloading VIX data...")
res_vix = HTTP.get(vix_url)
df_vix = CSV.read(IOBuffer(res_vix.body), DataFrame)

# Format VIX dates
df_vix.DATE = Dates.Date.(df_vix.DATE, "mm/dd/yyyy")
df_vix = rename(df_vix, :DATE => :Date, :CLOSE => :VIX)

println("Writing VIX data to CSV...")
CSV.write(joinpath(data_dir, "VIX_daily.csv"), df_vix[:, [:Date, :VIX]])

# 3. Merge Datasets
println("Merging datasets...")
df_merged = innerjoin(df_kf, df_vix[:, [:Date, :VIX]], on=:Date)

# Filter for the required start date (e.g., 1990-01-02 since VIX starts around 1990)
df_merged = df_merged[df_merged.Date .>= Date("1990-01-01"), :]

# Calculate market proxy (equal-weight average of the 30 industries)
returns_cols = names(df_merged)[2:end-1] # all except Date and VIX

# Drop missing values manually
for col in names(df_merged)
    for i in 2:nrow(df_merged)
        if ismissing(df_merged[i, col])
            df_merged[i, col] = df_merged[i-1, col]
        end
    end
end
dropmissing!(df_merged)

df_merged.MarketReturn = [sum([df_merged[i, c] for c in returns_cols])/length(returns_cols) for i in 1:nrow(df_merged)]

# Convert percentage returns to decimals
for col in returns_cols
    df_merged[!, col] = Float64.(df_merged[!, col]) ./ 100.0
end
df_merged.MarketReturn = df_merged.MarketReturn ./ 100.0

# Calculate cumulative wealth and Drawdown
wealth = cumprod(1.0 .+ df_merged.MarketReturn)
drawdown = zeros(length(wealth))
for i in 1:length(wealth)
    peak = maximum(wealth[max(1, i-252):i]) # 1 year trailing peak
    drawdown[i] = wealth[i] / peak - 1.0
end
df_merged.Drawdown = drawdown

# Calculate log(VIX)
df_merged.logVIX = log.(Float64.(df_merged.VIX))

println("Writing final aligned data...")
CSV.write(joinpath(data_dir, "aligned_market_data.csv"), df_merged)
println("Data processing complete.")
