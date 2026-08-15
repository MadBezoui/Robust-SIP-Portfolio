using Dates
using Pkg
using InteractiveUtils

open("run_manifest.txt", "w") do f
    write(f, "Execution Date: $(Dates.now())\n")
    write(f, "Platform: $(Sys.MACHINE)\n")
    write(f, "Julia Version: $(VERSION)\n")
    
    # Get system memory and CPU cores
    write(f, "CPU Cores: $(Sys.CPU_THREADS)\n")
    write(f, "CPU Name: $(Sys.cpu_info()[1].model)\n")
    write(f, "Memory: $(Sys.total_memory() / 1024^3) GB\n")
    
    write(f, "\n--- Package Versions ---\n")
    Pkg.status(io=f)
end
