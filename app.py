import json
import os
import requests
import time
import logging
import sys

from math import ceil
from prometheus_client import start_http_server, Info, Counter

def scaleReplicas(currentReplicas:int, currentMetricValue:float,
                  desiredMetricValue:float=.8, tolerance:float=.1)->int:
    # we do not update the replicas if they are within the tolerance limit
    if abs(currentMetricValue-desiredMetricValue)<= tolerance:
        return currentReplicas
    
    desiredReplicas = ceil(currentReplicas * ( currentMetricValue / desiredMetricValue ))
    
    # we need to maintain at least 1 instance to serve the load
    if desiredReplicas==0:
        return 1

    return desiredReplicas


if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # read from env file or use default config 
    load_dotenv()
    
    APP_SERVICE_URL= os.getenv("APP_SERVICE_URL", "http://localhost")
    APP_SERVICE_PORT= os.getenv("APP_SERVICE_PORT", "8123")
    SCALE_RESOLUTION_TIME= int(os.getenv("SCALE_RESOLUTION_TIME", 5))
    SCALE_METRIC= float(os.getenv("SCALE_METRIC", .80))
    SCALE_TOLERANCE= float(os.getenv("SCALE_TOLERANCE", .10))
    LOG_LEVEL= os.getenv("LOG_LEVEL", "INFO")

    SERVICE_ADDRESS= ":".join([APP_SERVICE_URL, APP_SERVICE_PORT])

    # configure logging
    log = logging.getLogger('')
    log.setLevel(LOG_LEVEL)
    format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(format)
    log.addHandler(handler)
    
    start_http_server(port=8000)
    
    counter_hb= Counter('autoscaler_heartbeat', "autoscaler heartbeat")
    counter_req = Counter('requests_failures', 'HTTP Failures', ['method', 'endpoint'])
    counter_req.labels("get", "/app/status")
    counter_req.labels("put", "/app/replicas")
    
    while True:
        log.debug("getting app status")
        get_resp= requests.get(
            url= SERVICE_ADDRESS + "/app/status",
            headers= {"Accept": "application/json"}
        )

        # print (g.text, g.status_code)
        if get_resp.status_code == 200:
            log.info("Acquired upstream app status {0}".format(get_resp.json()))
            
            currentReplicas= int(get_resp.json()["replicas"])
            currentMetricValue= float(get_resp.json()["cpu"]["highPriority"])
            
            s= scaleReplicas(currentReplicas= currentReplicas,
                             currentMetricValue=currentMetricValue,
                             desiredMetricValue=SCALE_METRIC,
                             tolerance=SCALE_TOLERANCE)
            
            if s!= currentReplicas:
                log.info("updating replica status config to {0}".format(s))
                
                put_resp = requests.put(
                    url= SERVICE_ADDRESS + "/app/replicas",
                    headers= {"Content-Type": "application/json"},
                    data= json.dumps({"replicas": s})
                )
                
                if put_resp.status_code != 204:
                    log.warning("Application could not update")
                    counter_req.labels("put", "/app/replicas").inc()
        else:
            log.warning("Application did not send any response")
            counter_req.labels("get", "/app/status").inc()

        
        time.sleep(SCALE_RESOLUTION_TIME) # scaling resolution time
        counter_hb.inc()
