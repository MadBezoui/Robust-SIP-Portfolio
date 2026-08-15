using Pkg
Pkg.activate(".")
Pkg.add([
    PackageSpec(name="JuMP", version="1.29.2"),
    PackageSpec(name="HiGHS", version="1.20.0"),
    PackageSpec(name="CSV", version="0.10.15"),
    PackageSpec(name="DataFrames", version="1.8.1")
])
Pkg.instantiate()
