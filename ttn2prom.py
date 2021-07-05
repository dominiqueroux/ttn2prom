import base64
import json
import time

from klein import Klein
from prometheus_client import Gauge
from prometheus_client.twisted import MetricsResource

def is_interesting(data):
    """Returns true iff this data should not be ignored."""
    return data["dev_id"].startswith("risinghf") and data["port"] == 8

def decode_payload(raw):
    """Parses the payload and returns the decoded pair (temperature, humidity)
    
    datasheet: http://www.objenious.com/wp-content/uploads/2016/10/RHF-DS01588Outdoor-IP64-Tempratrure-and-Humidity-LoRaWAN-Sensor-RHF1S001_V1.3.pdf
    """
    p = base64.b64decode(raw)
    raw_t = int.from_bytes(p[1:3], byteorder='little', signed=False)
    raw_h = p[3]
    raw_b = p[8]
    t = (175.72 * raw_t) / (2**16) - 46.85
    h = (125    * raw_h) / (2**8)  - 6
    b = (raw_b + 150) * 0.01
    return (t, h, b)


app = Klein()

g_temperature = Gauge('lorasensor_temperature_celsius', 'Temperature from the sensor',       ['device'])
g_humidity    = Gauge('lorasensor_humidity_percent',    'Relative humidity from the sensor', ['device'])
g_battery     = Gauge('lorasensor_battery_volt',        'Battery level from the senser',     ['device'])
g_timestamp   = Gauge('lorasensor_data_timestamp',      'Timestamp of last incoming data',   ['device'])

@app.route('/', methods=['POST'])
def save_item(request):
    request.setHeader('Content-Type', 'application/json')

    data = json.loads(request.content.read().decode('utf-8'))
    if not is_interesting(data): return json.dumps({'success': True})

    dev = data["dev_id"]
    t, h, b = decode_payload(data["payload_raw"])

    print(" *** device {} sent payload: {}, {}, {}".format(dev, t, h, b))

    g_temperature.labels(device=dev).set(t)
    g_humidity.labels(device=dev).set(h)
    g_battery.labels(device=dev).set(b)
    g_timestamp.labels(device=dev).set(time.time())

    return json.dumps({'success': True})

@app.route('/metrics', methods=['GET'])
def metrics(request):
    return MetricsResource()


if __name__ == '__main__':
    app.run(endpoint_description=r"tcp6:port=8047:interface=\:\:")
