# SythonLab Cubacel SDK

A Python library for integration with Cubacel.

## Installation

```bash
  pip install sythonlab-cubacel-sdk
```

## Environment variables

```CUBACEL_HOST```: Cubacel API access URL.

```CUBACEL_USERNAME```: Username for authentication.

```CUBACEL_PASSWORD```: Password for authentication.

```CUBACEL_SIM_TUR_ID```: ID provided by Cubacel for the sale of tourist SIM Tur cards.

```CUBACEL_MIN_BATCH_SIMTUR```: Minimum number of SIM Tur cards allowed in a batch.

```CUBACEL_MAX_BATCH_SIMTUR```: Maximum number of SIM Tur cards allowed in a batch.

```CUBACEL_ENVIRONMENT```: ```dev``` or ```prod```.

```CUBACEL_VERBOSE_ENABLED```: ```0``` or ```1```. Allows displaying request and response data in the console.

## How to use?

```python
from sythonlab_cubacel_sdk.sdk import CubacelSDK

cubacel = CubacelSDK()
# custom_config_file: Optional parameter, specifies the path to a .json file to save the configuration.

cubacel.ACTION(...)
```

## Available actions

- ```sale_sim_tur```: Execute a SIM Tur sale transaction.
- ```get_services```: Get services list.
- ```get_transaction_id```: Get new transaction ID.
- ```get_provinces```: Get provinces list.
- ```get_nationalities```: Get nationalities list.
- ```get_offices```: Get commercial offices list.
- ```get_sale```: Get information about a sale.
- ```recharge```: Execute a recharge to a mobile number.
- ```change_password```: Change password.
- ```request_batch```: Request a batch of tourist SIM cards.
- ```get_batch_sale```: Get information about a batch of tourist SIM cards.
- ```cancel_batch_sale```: Cancel a batch of tourist SIM cards.
- ```sale_sim_tur_card```: Add to the sale of a tourist SIM card from a batch.
- ```cancel_sale```: Cancel a sale.