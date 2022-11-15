import requests
import json
from time import sleep

url = "https://miw.iamai.es/textract_analysis"

arrayFiles = ['Factura_01.pdf', 'Factura_02.pdf', 'Factura_03.pdf', 'Factura_04.pdf', 'Factura_05.pdf', 'Factura_06.pdf', 'Factura_07.pdf', 'Factura_08.pdf', 'Factura_09.pdf', 'Factura_10.pdf', 'Factura_108585.pdf', 'Factura_11.pdf', 'Factura_110892.pdf', 'Factura_113022.pdf', 'Factura_115660.pdf', 'Factura_117190.pdf', 'Factura_119410.pdf', 'Factura_12.pdf', 'Factura_120976.pdf', 'Factura_124004.pdf', 'Factura_126076.pdf', 'Factura_127920.pdf', 'Factura_129939.pdf', 'Factura_13.pdf', 'Factura_134456.pdf', 'Factura_138221.pdf', 'Factura_14.pdf', 'Factura_141461.pdf', 'Factura_15.pdf', 'Factura_16.pdf', 'Factura_17.pdf', 'Factura_18.pdf', 'Factura_19.pdf', 'Factura_20.pdf', 'Factura_21.pdf', 'Factura_22.pdf', 'Factura_23.pdf', 'Factura_24.pdf', 'Factura_25.pdf', 'Factura_26.pdf', 'Factura_27.pdf', 'Factura_28.pdf', 'Factura_29.pdf', 'Factura_30.pdf', 'Factura_31.pdf', 'Factura_32.pdf', 'Factura_33.pdf', 'Factura_34.pdf', 'Factura_35.pdf', 'Factura_36.pdf', 'Factura_37.pdf', 'Factura_38.pdf', 'Factura_39.pdf', 'Factura_40.pdf', 'Factura_41.pdf', 'Factura_42.pdf', 'Factura_43.pdf', 'Factura_44.pdf', 'Factura_45.pdf', 'Factura_46.pdf', 'Factura_47.pdf', 'Factura_48.pdf', 'Factura_49.pdf', 'Factura_50.pdf', 'Factura_51.pdf']

jobs = []

# 1. Mandamos las facturas para generar los jobs asíncronos,, metiéndolos en un array.
for file in arrayFiles:
    print("Processing file: "+str(file))
    payload = json.dumps({
      "s3_url": "s3://textractinvoiceanalysisocr/" + file
    })
    headers = {
      'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)

    jobs.append(json.loads(response.text)['job'])
    sleep(5)

print(str(jobs))

# 2. Sondeamos cada job para ver el resultado y calcular el número de aciertos. Después, promediamos.
counter_total = 0
counter_guess = 0
for job in jobs:
    url = "https://miw.iamai.es/textract_analysis_results"

    payload = json.dumps({
      "JobId": job 
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    json_response = json.loads(response.text)
    object_search = json_response['analysis_results']
    
    for field_value in object_search.values():
        counter_total = counter_total + 1
        if field_value.strip() == '':
            continue
        else:
            counter_guess = counter_guess + 1

prec = counter_guess / counter_total * 100
print('Precision: '+str(prec)+' %') 



