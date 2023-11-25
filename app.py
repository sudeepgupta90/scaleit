import json
from math import ceil
import os
import requests
import time
import logging
import sys


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

    # start an infinite loop which calls the App service to be monitored after every SCALE_RESOLUTION_TIME secs
    application_no_status:int= 0
    application_no_update:int= 0
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
            
            # print (currentReplicas, currentMetricValue) # feed this into otel or statsd
            
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
                    application_no_update+=1
                    log.warning("Application could not update")
                # print (put_resp.text, put_resp.status_code) # feed this into otel or statsd
        
        if get_resp.status_code != 200:
            application_no_status +=1
            log.warning("Application did not send any response")
        
        time.sleep(SCALE_RESOLUTION_TIME) # scaling resolution time
