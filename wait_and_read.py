import time
time.sleep(5) # wait for julia to finish (if it's still running)
with open("results/gap_verification.csv") as f:
    print(f.read())
