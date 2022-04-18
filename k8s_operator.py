from traceback import print_tb
import kopf
from kubernetes import kubernetes

@kopf.on.create(kind ='Deployment')
async def my_handler(body,spec, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    print("NS -> ", namespace)
    print("NAME -> ", name)
    body = body.__dict__["_src"]
    del body["metadata"]["resourceVersion"]
    container = body["spec"]["template"]["spec"]["containers"][0]
    envs = [{
                "name": "HTTP_PROXY",
                    "valueFrom":{
                        "configMapKeyRef": {
                            "key": "http_proxy",
                            "name": "nginx-cm"
                        }
                    }
            },
            {
                "name": "HTTP_PROXYS",
                    "valueFrom":{
                        "configMapKeyRef": {
                            "key": "https_proxy",
                            "name":"nginx-cm"
                        }
                    }
            },
            {
                "name": "NO_PROXY",
                    "valueFrom":{
                        "configMapKeyRef": {
                            "key": "no_proxy",
                            "name":"nginx-cm"
                        }
                    }
            }]
    if container.get("env"):
        container["env"].append(*envs)
    else:
        container["env"] = envs
    body["spec"]["template"]["spec"]["containers"][0] = container
    api = kubernetes.client.AppsV1Api()
    api.patch_namespaced_deployment(name,namespace,body)
    print(f"Deployment {name} successfully patched")
    print(body)

    return {"msg": f"Successed deployed {name}"}