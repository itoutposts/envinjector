FROM python:3.7 
COPY . . 
RUN pip install kopf[full-auth] 
CMD kopf run -n test-ns k8s_operator.py