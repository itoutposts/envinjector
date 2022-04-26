import kopf
import json
from kubernetes import kubernetes

@kopf.on.create('envinjector.org', 'v1', 'EnvInjector')
async def create_envinjector(body,spec, **kwargs):
    """
        Trigger object which created with CRD and apply all envs to deployments in namespace

    """
    ns = body['metadata']['namespace']

    envs = spec.get("envs")  # envs from CRD object
    api = kubernetes.client.AppsV1Api()
    deployments = api.list_namespaced_deployment(ns)
    for dep in deployments.items:

        container = dep.spec.template.spec.containers[0]
        if container.env:
            container.env.append(*envs)
        else:
            container.env = envs
        body["spec"]["template"]["spec"]["containers"][0] = container

        dep.spec.template.spec.containers[0] = container
        api.replace_namespaced_deployment(dep.metadata.name,ns,dep)



@kopf.on.update('envinjector.org', 'v1', 'EnvInjector')
async def update_envinjector(body,spec, **kwargs):
    """ 
        Trigger when CRD object is edited (remove or add new envs)
    """

    ns = body['metadata']['namespace']
    # get last applied envs
    last_envs = json.loads(body["metadata"]["annotations"]["kopf.zalando.org/last-handled-configuration"])["spec"]["envs"]
    envs = spec.get("envs") # # envs from CRD object
    api = kubernetes.client.AppsV1Api()
    deployments = api.list_namespaced_deployment(ns)
    new_envs = filter_new_envs(last_envs, envs)  # filter new envs ( compare with last applied)
    deleted_envs = filter_deleted_envs(last_envs, envs) # filter deleted envs ( compare with last applied)
    for dep in deployments.items:
        # filter  deployment envs and deleted envs ( return unchanged envs )
        unchanged_envs = clear_env(dep.spec.template.spec.containers[0].env, deleted_envs)
        
        envs = filter_new_envs(unchanged_envs, new_envs) # return  new envs ( compare with unchanged envs and new envs)
        if envs:
            envs = [*envs, *unchanged_envs]
        else:
            envs = unchanged_envs
        container = dep.spec.template.spec.containers[0]
        container.env = envs
        dep.spec.template.spec.containers[0] = container
        api.replace_namespaced_deployment(dep.metadata.name,ns,dep)


def filter_new_envs(old, new):
    """ Filter new envs ( compare with new envs and last applied envs) """
    new_envs = []
    for i in new:
        if i in old:
            continue
        else:
            new_envs.append(i)

    return new_envs

def filter_deleted_envs(old,new):
    """ Filter deleted envs ( compare with new envs and last applied envs) """
    deleted_envs = []

    for i in old:
        if i not in new:
            deleted_envs.append(i)
    return deleted_envs

def clear_env(old_envs, new_envs):
    """ Filter unchanged envs (compare deployments envs and deleted envs) """
    old_envs = [k.to_dict() for k in old_envs]
    for i in old_envs:
        del i["value_from"]
    unchanged = []
    for i in old_envs:
        if i not in new_envs:
            unchanged.append(i)
    return unchanged


@kopf.on.create(kind ='Deployment')
async def my_handler(body,spec, **kwargs):
    name = body['metadata']['name']
    namespace = body['metadata']['namespace']
    body = body.__dict__["_src"]
    del body["metadata"]["resourceVersion"]
    container = body["spec"]["template"]["spec"]["containers"][0]

    client = kubernetes.client.CustomObjectsApi()
    # retrive created CRD object
    custom_object = client.list_namespaced_custom_object(group="envinjector.org", version="v1",namespace=namespace ,plural="envinjectors")
    if custom_object["items"]:
        envs = custom_object["items"][0]["spec"]["envs"]
   
        if container.get("env"):
            container["env"].extend(*envs)
        else:
            container["env"] = envs
        body["spec"]["template"]["spec"]["containers"][0] = container
        api = kubernetes.client.AppsV1Api()
        api.patch_namespaced_deployment(name,namespace,body)
        print(f"Deployment {name} successfully patched")

    return {"msg": f"Successed deployed {name}"}