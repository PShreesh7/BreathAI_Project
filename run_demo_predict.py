import requests, random, time

for i in range(5):
    data = {
        "mq3": round(random.uniform(0.0,1.0),3),
        "mq135": round(random.uniform(0.0,1.0),3),
        "mq138": round(random.uniform(0.0,1.0),3),
        "temp": round(random.uniform(20.0,40.0),2),
        "humidity": round(random.uniform(20.0,80.0),2),
        "pressure": round(random.uniform(980,1030),2),
        "spo2": round(random.uniform(90,100),1),
        "hr": random.randint(60,100)
    }
    try:
        r = requests.post("http://127.0.0.1:5000/predict", json=data, timeout=10)
        print(f"{i}: {r.status_code} -> {r.json()}")
    except Exception as e:
        print(f"{i}: request failed: {e}")
    time.sleep(1)
