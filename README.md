
# IAMAI - MiWenergía - InDemand

This repository contains data developed by Cubic Fort Consultores SL regarding the financial aid in the scope of InDemand RTL program, FAMICOM topic.

The generated API (still in an alpha phase), works asynchronously, providing two API POST calls which issued consecutively:

- First call is used to run the processing of an invoice, returning a JobId.
- Second call is used to check if given JobId has been completed.

More information next.



## API Reference

#### Submit an invoice in S3 for processing

```http
  POST https://miw.iamai.es/textract_analysis
```

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `s3_url` | `string` | **Required**. URL in S3 pointing to the PDF file of the invoice |

#### Submit derived JobId and return results

```http
  POST https://miw.iamai.es/textract_analysis_results
```

| Parameter | Type     | Description                       |
| :-------- | :------- | :-------------------------------- |
| `JobId`      | `string` | **Required**. JobId alphanumeric obtained from previous call |



## Demo

Here we show an example of first call

```
import requests
import json

url = "https://miw.iamai.es/textract_analysis"

payload = json.dumps({
  "s3_url": "s3://textractinvoiceanalysisocr/Factura_126076.pdf"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

This call returns:

```
{
    "doc_name": "Factura_126076.pdf",
    "job": "8f49e7687a81a38be6360162b75f39982c60d46b8ce849902aa238b674086b6b-a996a131819e5e3d9124b31a225f88a009d162b68d25344cbd51fc03d88aa141",
    "s3_bucket": "textractinvoiceanalysisocr",
    "timestamp": "Thu, 03 Nov 2022 08:21:32 GMT"
}
```

Then, we make use of *job* in second endpoint:

```
import requests
import json

url = "https://miw.iamai.es/textract_analysis_results"

payload = json.dumps({
  "JobId": "8f49e7687a81a38be6360162b75f39982c60d46b8ce849902aa238b674086b6b-a996a131819e5e3d9124b31a225f88a009d162b68d25344cbd51fc03d88aa141"
})
headers = {
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
```

We then obtain the following results:

```
{
    "JobId": "8f49e7687a81a38be6360162b75f39982c60d46b8ce849902aa238b674086b6b-a996a131819e5e3d9124b31a225f88a009d162b68d25344cbd51fc03d88aa141",
    "analysis_results": {
        "CUPS": "ES0021000016094238EP",
        "NIF": "48454094V",
        "address": "SANCHEZ IBERNON ANTONIO\nSENDA GRANADA 139 NUM 1° B\n30110 CHURRA",
        "contract_power": "12,54 €",
        "counter_renting": "0,85€",
        "electric_quote": "POTENCIA: P1 4.60kW P3 4,60kW P2 mercantil 0,00kW",
        "installation_address": "SENDA GRANADA NUM 139 1° B",
        "invoice_total": "25,69 €",
        "owner": "SANCHEZ IBERNON ANTONIO",
        "total_energy_consumed": "15,16 €"
    }
}
```