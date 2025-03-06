#!/usr/bin/env python

from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/mutate', methods=['POST'])
def webhook():
    request_json = request.get_json()
    if not request_json:
        return jsonify({"response": {"allowed": True}}), 200

    cluster = request_json['request']['object']
    patch = []
    if "machineDeployments" in cluster['spec']['topology']['workers']:
        mds = cluster['spec']['topology']['workers']['machineDeployments']
        for index,pool in mds:
            if "cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size" in pool['metadata']['labels'] and "cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size" in pool['metadata']['labels']:
               patch.extend([
                {"op": "add", "path": "/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size']},
                {"op": "add", "path": "/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size']},
                {"op": "remove", "path": "/spec/topology/workers/machineDeployments/{index}/replicas"}
                ])
            
    return jsonify({
        "response": {
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": json.dumps(patch).encode('utf-8').decode('utf-8')
        }
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, debug=True, ssl_context=('/ssl/server.crt', '/ssl/server.key'))




