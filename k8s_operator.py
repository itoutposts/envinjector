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
    if container.get("env"):
        container["env"].append({"name": "http_proxy","value": "http://153.95.94.130:8080"},{"name": "https_proxy","value":"http://153.95.94.130:8080"},{"name": "no_proxy","value": "localhost,127.0.0.1,.svc,.svc.cluster.local,.cluster.local,.flux-system,.flux-system.svc.cluster.local,10.103.82.0/24,10.36.0.0/24,10.44.0.0/24,10.96.0.0/12,10.219.132.14,nexus.app.nox.express,gitlab.dev.nox.express,10.219.132.12,10.96.0.1,10.219.1.51,10.219.1.52,10.219.1.53,10.219.1.54,10.219.1.55,10.219.1.56,10.219.1.14,10.219.3.22,10.219.3.24,10.219.3.25,*.de.innight.tnt,*.dev.nox.express,*.shared.nox.express,*.int.nox.express,*.app.nox.express,*.p-app.nox.express"})
    else:
        container["env"] = [{"name": "http_proxy","value": "http://153.95.94.130:8080"},{"name": "https_proxy","value":"http://153.95.94.130:8080"},{"name": "no_proxy","value": "localhost,127.0.0.1,.svc,.svc.cluster.local,.cluster.local,.flux-system,.flux-system.svc.cluster.local,10.103.82.0/24,10.36.0.0/24,10.44.0.0/24,10.96.0.0/12,10.219.132.14,nexus.app.nox.express,gitlab.dev.nox.express,10.219.132.12,10.96.0.1,10.219.1.51,10.219.1.52,10.219.1.53,10.219.1.54,10.219.1.55,10.219.1.56,10.219.1.14,10.219.3.22,10.219.3.24,10.219.3.25,*.de.innight.tnt,*.dev.nox.express,*.shared.nox.express,*.int.nox.express,*.app.nox.express,*.p-app.nox.express"}]
    body["spec"]["template"]["spec"]["containers"][0] = container
    api = kubernetes.client.AppsV1Api()
    api.patch_namespaced_deployment(name,namespace,body)
    print(f"Deployment {name} successfully patched")
    return {"msg": f"Successed deployed {name}"}