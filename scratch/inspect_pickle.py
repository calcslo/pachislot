import pickle
import os

def inspect_pickle(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    
    print(f"Total items in list: {len(data)}")
    
    # Check for unique dates and machines
    dates = set()
    machines = set()
    
    # The data is expected to be [date, weekday, machine, ...] in chunks of 12
    chunk_size = 12
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        if len(chunk) >= 3:
            dates.add(chunk[0])
            machines.add(chunk[2])
    
    print(f"Unique dates found: {sorted(list(dates))}")
    print(f"Unique machines found: {sorted(list(machines))}")

if __name__ == "__main__":
    inspect_pickle("scraped_data_20260428_060022.pkl")
