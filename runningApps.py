try:
    import psutil
except Exception as e:
    print(f"doesn't seem like psutil is installed\n{e}")
    exit()

print("press enter to print all applications open on the current device")
input()

for process in psutil.process_iter():
    print(process.name())
    
