#!/usr/bin/env python

from flask import Flask, request, jsonify
import json
import logging

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

@app.route('/mutate', methods=['POST'])
def webhook():
    request_json = request.get_json()
    app.logger.debug(request_json)
    if not request_json:
        return jsonify({"response": {"allowed": True}}), 200

    cluster = request_json['request']['object']
    cluster_name = cluster['metadata']['name']
    if  "machineDeployments" not in cluster['spec']['topology']['workers']:
         app.logger.info(f"request for {cluster_name} did not container machine deployments") 
         return jsonify({"response": {"allowed": True}}), 200
    patch = []
    mds = cluster['spec']['topology']['workers']['machineDeployments']
    for index, pool in enumerate(mds):
        if "labels" in pool['metadata']:
            if "cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size" in pool['metadata']['labels'] and "cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size" in pool['metadata']['labels']:
                app.logger.info(f"autoscale labels found on {cluster_name}, needs mutating")
                patch.extend([
                    {"op": "add", "path": f"/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size']},
                    {"op": "add", "path": f"/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size']},
                    {"op": "remove", "path": f"/spec/topology/workers/machineDeployments/{index}/replicas"}
                    ])
            
    return jsonify({
        "response": {
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": json.dumps(patch).encode('utf-8').decode('utf-8')
        }
    }), 200

if __name__ == '__main__':
    app.logger.info("starting autoscale mutating webhook")
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=('/ssl/server.crt', '/ssl/server.key'))