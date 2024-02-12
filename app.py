#Parameter för kunders user id i syfte att hämta datan från apiet och mappa det till rätt kund med hjälp av kundens user id 
#Version: 2.0 med gpu enrergy via linux
from flask import Flask
import psutil
import GPUtil
import subprocess
import pynvml
import pymongo
import schedule
import sched
import time


app = Flask(__name__)


def get_nvidia_gpu_energy():
    try:
        pynvml.nvmlInit()  # Ensure NVML is initialized
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # For the first GPU
        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)  # Power usage in milliwatts
        power_usage_watts = power_usage / 1000.0  # Convert to watts
        pynvml.nvmlShutdown()  # Shutdown NVML to free resources, if no further NVML calls are needed
        return f"{power_usage_watts} W"
    except pynvml.NVMLError as error:
        return f"Failed to get GPU power usage: {str(error)}"

@app.route('/gpu-energy')
def gpu_energy():
    """Endpoint to get current GPU power usage."""
    gpu_energy = get_nvidia_gpu_energy()
    return {"GPU Energy": gpu_energy}


MONGO_HOST = 'cluster0.hjzgptm.mongodb.net'
MONGO_PORT = 27017
MONGO_DB = 'CloudSaver'
MONGO_COLLECTION = 'monitor-data'
# MongoDB connection string
MONGO_CONNECTION_STRING = 'mongodb+srv://paulartin:12345679@cluster0.hjzgptm.mongodb.net/CloudSaver'

# MongoDB client and collection initialization
client = pymongo.MongoClient(MONGO_CONNECTION_STRING)
db = client.get_database()  # Specify your database name
collection = db.get_collection("monitor-data")  # Specify your collection name

# MongoDB client and collection initialization
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]

def get_nvidia_gpu_power_usage():
    """Get the current power usage for NVIDIA GPUs using nvidia-smi."""
    try:
        nvidia_smi_output = subprocess.run(
            ['nvidia-smi', '--query-gpu=power.draw', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            text=True
        )
        power_usage_str = nvidia_smi_output.stdout.strip()  # Power usage in watts
        
        # Handle [N/A] response
        if '[N/A]' in power_usage_str:
            return "Power usage not available for this GPU."
        
        # In systems with multiple GPUs, this will return the power usage of the first one. Adjust accordingly.
        power_usage = float(power_usage_str.split('\n')[0])  # Convert first GPU's power usage to float
        return f"{power_usage} W"
    except Exception as e:
        return f"Failed to read GPU power usage: {str(e)}"

def get_nvidia_gpu_energy():
    try:
        pynvml.nvmlInit()  # Ensure NVML is initialized
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)  # For the first GPU
        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle)  # Power usage in milliwatts
        power_usage_watts = power_usage / 1000.0  # Convert to watts
        pynvml.nvmlShutdown()  # Shutdown NVML to free resources, if no further NVML calls are needed
        return f"{power_usage_watts} W"
    except pynvml.NVMLError as error:
        return f"Failed to get GPU power usage: {str(error)}"

def get_gpu_usage():
    """Returns the GPU usage if NVIDIA GPU is present, else 'Not NVIDIA'."""
    gpus = GPUtil.getGPUs()
    if not gpus:
        return "Not NVIDIA"
    return f"GPU Usage: {gpus[0].load * 100}%"

def get_gpu_usage_linux():
    try:
        nvidia_smi_output = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            text=True
        )
        gpu_usage_str = nvidia_smi_output.stdout.strip()  # GPU usage in percentage
        
        # Handle [N/A] response
        if '[N/A]' in gpu_usage_str:
            return "GPU usage not available for this GPU."
        
        # In systems with multiple GPUs, this will return the usage of the first one. Adjust accordingly.
        gpu_usage = float(gpu_usage_str.split('\n')[0])  # Convert first GPU's usage to float
        return f"GPU Usage: {gpu_usage}%"
    except Exception as e:
        return f"Failed to read GPU usage: {str(e)}"

def insert_data_to_mongodb(scheduler):
    scheduler.enter(60, 1, insert_data_to_mongodb, (scheduler,))

    cpu_usage = psutil.cpu_percent(1)
    gpu_usage = get_gpu_usage_linux()
    gpu_energy = get_nvidia_gpu_energy()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').used
    network_usage_sent = psutil.net_io_counters().bytes_sent
    network_usage_recv = psutil.net_io_counters().bytes_recv
    data = {
        "timestamp": time.time(),
        "cpu_usage": cpu_usage,
        "gpu_usage": gpu_usage,
        "gpu_energy": gpu_energy,
        "memory_usage": memory_usage,
        "disk_usage": disk_usage,
        "network_usage_sent": network_usage_sent,
        "network_usage_recv": network_usage_recv
    }

    collection.insert_one(data)
    print("Data inserted to MongoDB successfully.")




@app.route('/')
def home():
    """Endpoint to check if the server is up."""
    return "Home"

@app.route('/health')
def health():
    """Endpoint to check if the server is up."""
    return "OK"

@app.route('/usage')
def usage():
    """Endpoint to get current CPU and GPU usage."""
    # Example usage
    cpu_energy = psutil.cpu_freq()
    cpu_usage = psutil.cpu_percent(1)
   
    gpu_usage = get_gpu_usage()
    gpu_usage2 = get_gpu_usage_linux()
    # gpu_energy = get_nvidia_gpu_power_usage()#old
    gpu_energy = get_nvidia_gpu_energy()
   
    memory_usage = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    network_usage = psutil.net_io_counters()

    usage = {
        "CPU Usage": f"{cpu_usage}%",
        "CPU Energy": f"{cpu_energy}",
        "GPU Usage": gpu_usage,
        "GPU Usage2": gpu_usage2,
        "Memory Usage": f"{memory_usage.percent}%",
        "Disk Usage": f"{disk_usage.used} bytes used, {disk_usage.free} bytes free, total {disk_usage.total} bytes",
        "Network Usage": f"{network_usage.bytes_sent} bytes sent, {network_usage.bytes_recv} bytes received",
        "GPU Energy": gpu_energy,
    }
    print(usage)

    return {
        "CPU Usage": f"{cpu_usage}%",
        "CPU Energy": f"{cpu_energy}",
        "GPU Usage": gpu_usage,
        "GPU Usage2": gpu_usage2,
        "Memory Usage": f"{memory_usage.percent}%",
        "Disk Usage": f"{disk_usage.used} bytes used, {disk_usage.free} bytes free, total {disk_usage.total} bytes",
        "Network Usage": f"{network_usage.bytes_sent} bytes sent, {network_usage.bytes_recv} bytes received",
        "GPU Energy": gpu_energy,
    }
# Schedule data insertion every 60 seconds

my_scheduler = sched.scheduler(time.time, time.sleep)
my_scheduler.enter(60, 1, insert_data_to_mongodb, (my_scheduler,))
my_scheduler.run()
if __name__ == "__main__":
    usage()
    app.run(host='0.0.0.0', port=8080, debug=False)
