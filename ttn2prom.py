import json

from klein import Klein
from prometheus_client import Gauge
from prometheus_client.twisted import MetricsResource

class DataStore:
    app = Klein()

    def __init__(self):
        self.g_temperature = Gauge('temperature', 'Temperature from the sensor')
        self.g_humidity    = Gauge('humidity',    'Humidity from the sensor')

    @app.route('/', methods=['POST'])
    def save_item(self, request):
        request.setHeader('Content-Type', 'application/json')

        data = json.load(request.content)
        if data["port"] != 8: return json.dumps({'success': True})

        print(" *** received payload: ", data["payload_raw"])
        print(" ***   for dev_id ", data["dev_id"])

        from ptpython.repl import embed
        embed(globals(), locals())

        # self.g_humidity.set()

        return json.dumps({'success': True})

    @app.route('/metrics', methods=['GET'])
    def metrics(self, request):
        return MetricsResource()


if __name__ == '__main__':
    store = DataStore()
    store.app.run('localhost', 8047)
