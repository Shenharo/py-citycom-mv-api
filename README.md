# citycom_mv_api

A python wrapper for citycom_mv api

## Module Usage

```python
from citycom_mv_api import citycom_mv_client as citycom

client = citycom.citycomClient("X@citycom-mv.com","password")
try:
    await client.login()  
except iec.exceptions.LoginError as err:
    logger.error(f"Failed Login: (Code {err.code}): {err.error}")
    raise

customer = await client.get_customer_information()
print(customer)

meters = await client.get_meters()
for meter in meters:
    print(meter)

reading = await client.get_last_meter_reading(meters[0].meter_id)
print(reading)
