"""Main IEC Python API module."""

import asyncio
import datetime
import os

import aiohttp
from loguru import logger

from citycom_mv_api.citycom_mv_client import CityComMVClient
from citycom_mv_api.login import LoginError
from citycom_mv_api.models.exceptions import CitycomError
from citycom_mv_api.models.TimePeriodOptions import TimePeriodOptions


async def main():
    session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=10))
    try:
        # Example of usage
        client = CityComMVClient("XXXX@citycom-mv.com", "YYY", session)

        token_json_file = "token.json"
        if os.path.exists(token_json_file):
            await client.load_token_from_file(token_json_file)
        else:
            try:
                await client.login()
                await client.save_token_to_file(token_json_file)
            except LoginError as err:
                logger.error(f"Failed Login: (Code {err.code}): {err.error}")
                raise

        # refresh token example- currently not implemented, it just logins again
        token = client.get_token()
        await client.check_token()
        new_token = client.get_token()
        if token != new_token:
            print("Token refreshed")
            await client.save_token_to_file(token_json_file)

        print("access_token: " + token.access_token)
        print("")
        print("get customer data example")
        print("")

        customer = await client.get_customer()
        print(customer)

        print("")
        print("get get last meter reading data example")
        print("")

        reading = await client.get_last_meter_reading(customer.properties[0].meters[0].meter_id)
        print(reading)

        print("")
        print("historical data example - DAILY")
        print("")
        historical_data = await client.get_historical_data(
            meter_id=customer.properties[0].meters[0].meter_id,
            time_period=TimePeriodOptions.DAILY,
            from_date=(datetime.datetime.now() - datetime.timedelta(days=7)),
            to_date=datetime.datetime.now(),
        )
        print(historical_data)

        print("")
        print("historical data example - MONTHLY (dates range not supported)")
        print("")
        historical_data = await client.get_historical_data(
            meter_id=customer.properties[0].meters[0].meter_id,
            time_period=TimePeriodOptions.MONTHLY
        )
        print(historical_data)
        print("")
        print("historical data example - YEARLY(dates range not supported)")
        print("")

        historical_data = await client.get_historical_data(
            meter_id=customer.properties[0].meters[0].meter_id,
            time_period=TimePeriodOptions.YEARLY
        )
        print(historical_data)

    except CitycomError as err:
        logger.error(f"Error: (Code {err.code}): {err.error}")
    finally:
        await session.close()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
