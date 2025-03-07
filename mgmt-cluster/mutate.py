#!/usr/bin/env python

from flask import Flask, request, jsonify
import json
import logging
import jsonpatch
import base64

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

@app.route('/mutate', methods=['POST'])
def webhook():
    request_json = request.get_json()
    app.logger.debug(request_json)
    if not request_json:
        return jsonify(
            {
                "apiVersion": request_json.get("apiVersion"),
                "kind": request_json.get("kind"),
                "response": {
                    "uid": request_json["request"].get("uid"),
                    "allowed": True
                }
            }
        )

    cluster = request_json['request']['object']
    cluster_name = cluster['metadata']['name']
    if  "machineDeployments" not in cluster['spec']['topology']['workers']:
         app.logger.info(f"request for {cluster_name} did not container machine deployments") 
         return jsonify(
            {
                "apiVersion": request_json.get("apiVersion"),
                "kind": request_json.get("kind"),
                "response": {
                    "uid": request_json["request"].get("uid"),
                    "allowed": True
                }
            }
        )
    patch = []
    mds = cluster['spec']['topology']['workers']['machineDeployments']
    for index, pool in enumerate(mds):
        app.logger.debug(f"machine deployment: {pool}")
        if "labels" in pool['metadata']:
            if "cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size" in pool['metadata']['labels'] and "cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size" in pool['metadata']['labels']:
                app.logger.info(f"autoscale labels found on {cluster_name}, needs mutating")
                patch.extend([
                    {"op": "add", "path": f"/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-max-size']},
                    {"op": "add", "path": f"/spec/topology/workers/machineDeployments/{index}/metadata/annotations/cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size", "value": pool['metadata']['labels']['cluster.x-k8s.io/cluster-api-autoscaler-node-group-min-size']},
                    {"op": "remove", "path": f"/spec/topology/workers/machineDeployments/{index}/replicas"}
                    ])
    app.logger.debug(patch)
    json_patch = jsonpatch.JsonPatch(patch)
    base64_patch = base64.b64encode(json_patch.to_string().encode("utf-8")).decode("utf-8")
    return jsonify(
        {
            "apiVersion": request_json.get("apiVersion"),
            "kind": request_json.get("kind"),
            "response": {
                "uid": request_json["request"].get("uid"),
                "allowed": True,
                "status": {"message": "configuring cluster for autoscaling"},
                "patchType": "JSONPatch",
                "patch": base64_patch
            }
        }
    )

if __name__ == '__main__':
    app.logger.info("starting autoscale mutating webhook")
    app.run(host='0.0.0.0', port=8443, debug=True, ssl_context=('/ssl/server.crt', '/ssl/server.key'))