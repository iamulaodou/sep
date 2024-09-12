import influxdb_client

def login(bucket:str = "air", 
          org:str = "adelaide", 
          token:str = 'vIljkE2RnDXlkaJ5RRHrqZJg_rTqOhPeNBguXwHkcbvJIIBjyj2MHx2fGYuQUeghiq89N9wP1SA9TICGmONMqw==', 
          url:str = 'https://us-east-1-1.aws.cloud2.influxdata.com'):
    # Store the database name
    client = influxdb_client.InfluxDBClient(
    url=url,
    token=token,
    org=org
    )
    return client
