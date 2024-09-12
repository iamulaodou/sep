from flask import Flask, request, jsonify
from flask_cors import CORS
import login
import pandas as pd
import altair as alt
import pprint
app = Flask(__name__)
client = login.login()
query_api = client.query_api()
#print(client.health())
CORS(app) # This will enable CORS for all routes'

__ORG = "adelaide"
@app.route('/api/fetchBucketList', methods=['GET'])
def fetch_bucket_list():
    buckets_api = client.buckets_api()
    buckets = buckets_api.find_buckets().buckets
    bucket_names = [bucket.name for bucket in buckets]
    return jsonify(bucket_names)
    
@app.route('/api/fetchBucket', methods=['POST'])
def fetch_bucket():
    __BUCKET = request.json['Bucket']  
    
    query = f'''
import "influxdata/influxdb/v1"
v1.measurements(bucket: "{__BUCKET}")
'''
    query_api = client.query_api()
    result = query_api.query(query=query)
    measurements = [record.get_value() for table in result for record in table.records]
    return measurements


def getBucket(bucket):
        
    query = f'''
import "influxdata/influxdb/v1"
v1.measurements(bucket: "{bucket}")
'''
    query_api = client.query_api()
    result = query_api.query(query=query)
    measurements = [record.get_value() for table in result for record in table.records]
    return measurements

def getTags(bucket,measurement):
    tags_query = f'''
    import "influxdata/influxdb/schema"
    schema.measurementTagKeys(
      bucket: "{bucket}",
      measurement: "{measurement}"
    )
    '''

    tags_result = query_api.query(org=__ORG, query=tags_query)
    tags_list = [record.get_value() for table in tags_result for record in table.records]
    return tags_list

def getFields(bucket,measurement):

    fields_query = f'''
import "influxdata/influxdb/schema"
schema.measurementFieldKeys(
  bucket: "{bucket}",
  measurement: "{measurement}"
)
'''

    fields_result = query_api.query(org=__ORG, query=fields_query)
    fields_list = [record.get_value() for table in fields_result for record in table.records]
    return fields_list


    
    
@app.route('/api/fetchInfo', methods=['GET'])
def fetch_informations():
    try:
        informations = {}
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets().buckets
        bucket_names = [bucket.name for bucket in buckets]

        for bucket in bucket_names:
            informations[bucket] = {}
            measurements = getBucket(bucket)
            for measurement in measurements:
                informations[bucket][measurement] = {}
                informations[bucket][measurement]["Tags"] = getTags(bucket,measurement)
                informations[bucket][measurement]["Fields"] = getFields(bucket,measurement)

        return jsonify(informations), 200, {'Content-Type': 'application/json'}
    
    except Exception as e:
            return jsonify({'error': str(e)}), 400

@app.route('/api/fetchMeasurement', methods=['POST'])
def fetch_measurement():
    global df
    measurement = request.json['Measurement']
    bucket = request.json['Bucket']
    #print(f"Fetching data for measurement: {measurement} in bucket: {bucket}")
    
    query = f'''
    from(bucket: "{bucket}")
      |> range(start: -20d)  
      |> filter(fn: (r) => r._measurement == "{measurement}")
    '''
    
    query_api = client.query_api()
    tables = query_api.query(org = "adelaide", query = query)
    records = []
    for table in tables:
        for record in table.records:
            records.append((record.get_time(), record.get_measurement(), record.get_field(), record.get_value()))

    df = pd.DataFrame(records, columns=["time", "measurement", "field", "value"])

    return df.to_json(orient="records")#, 200, {'Content-Type': 'application/json'}

@app.route('/api/getPlot', methods=['POST'])
def get_plot():
    global df  # Use the global df for plotting
    if df is not None:
        try:
            print(df.columns)
            request_data = request.get_json()
            x_axis = request_data.get('x') #, 'Field' 
            y_axis = request_data.get('y') #, 'Value'
            print(x_axis, y_axis) 
            
            
            chart = alt.Chart(df).mark_point().encode(
                x=x_axis,
                y=y_axis,
                #color='Origin',  # You can customize this part as needed
                tooltip=[ x_axis, y_axis]
            ).interactive()

            #print(chart)
            chart_json = chart.to_json()
            

            return jsonify({'chart': chart_json})

        except Exception as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'No data available'}), 400
if __name__ == '__main__':
    #pprint.pprint(fetch_informations())
    
    app.run(debug=True,port = 5001)
