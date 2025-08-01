import psutil
import getpass

current_user = getpass.getuser()

processes: list[psutil.Process] = []
for process in psutil.process_iter(['username', 'name']):
    # this should handle the windows domain format "DOMAIN\\user"
    username = process.info['username'].split('\\')[-1]

    if username == current_user:
        processes.append(process)

processes.sort(key=lambda p: p.memory_info().rss, reverse=False)

for process in processes:
    mem_mb = process.memory_info().rss / (1024 * 1024)  # Convert to MB
    print(f"\"{process.info['name']}\" (PID: {process.pid}, Memory: {mem_mb:.2f} MB)")
