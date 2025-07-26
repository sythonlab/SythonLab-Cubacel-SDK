import datetime
import logging
import requests

from zeep import Client
from zeep.exceptions import Fault
from zeep.transports import Transport

from sythonlab_cubacel_sdk.constants import ActionsEnum
from sythonlab_cubacel_sdk.sdk_config import CubacelSDKConfig

session = requests.Session()
session.verify = False

logger = logging.getLogger(__name__)


class CubacelSDK:
    CONFIG = None
    AUTH_SERVICE = None
    SALES_SERVICE = None
    TOKEN = None
    CLIENT = None
    DOCUMENT_TYPES = {
        'passport': 9,
        'dni': 1,
        'ci': 1
    }

    def __init__(self, custom_config_file=None, *args, **kwargs):
        self.configure(custom_config_file)
        client = Client(self.AUTH_SERVICE, transport=Transport(session=session))

        try:
            data = {
                'AccountId': self.CONFIG.USERNAME,
                'Password': self.CONFIG.PASSWORD,
            }

            if self.CONFIG.VERBOSE_ENABLED:
                print('GetSessionTicket Request', data)

            self.TOKEN = client.service.GetSessionTicket(**data).SessionTicket.Ticket

            if self.CONFIG.VERBOSE_ENABLED:
                print('GetSessionTicket Response', self.TOKEN)

        except Fault as e:
            print('[ERROR] - Error SOAP', e)
            print('[ERROR] - Error code', e.code)
            print('[ERROR] - Error message', e.message)
            raise

    def configure(self, custom_config_file):
        self.CONFIG = CubacelSDKConfig(custom_config_file=custom_config_file)
        self.AUTH_SERVICE = f"{self.CONFIG.HOST}/VirtualPayment/AuthenticationService.svc?wsdl"
        self.SALES_SERVICE = f"{self.CONFIG.HOST}/VirtualPayment/SalesService.svc?wsdl"

    @property
    def client(self):
        if not self.CLIENT:
            self.CLIENT = Client(self.SALES_SERVICE, transport=Transport(session=session))
        return self.CLIENT

    def execute(self, action, data, client=None):
        if not client:
            client = self.client

        actions = {
            ActionsEnum.SALE_SIM_TUR.value: client.service.SalePackage,
            ActionsEnum.GET_SERVICES.value: client.service.GetPackages,
            ActionsEnum.GET_PROVINCES.value: client.service.GetProvinces,
            ActionsEnum.GET_NATIONALITIES.value: client.service.GetNationalities,
            ActionsEnum.GET_OFFICES.value: client.service.GetCommercialOffices,
            ActionsEnum.GET_SALE.value: client.service.GetSale,
            ActionsEnum.RECHARGE.value: client.service.SaleRecharge,
            ActionsEnum.GET_BALANCE.value: client.service.GetBalance,
            ActionsEnum.CHANGE_PASSWORD.value: client.service.ChangeAccountPassword,
            ActionsEnum.REQUEST_BATCH.value: client.service.SellBatchPackage,
            ActionsEnum.GET_BATCH_SALE.value: client.service.GetSaleBatch,
            ActionsEnum.CANCEL_BATCH_SALE.value: client.service.CancelSale,
            ActionsEnum.SALE_SIM_TUR_CARD.value: client.service.SuppleCustInfo,
            ActionsEnum.GET_IDENTIFICATION_TYPES.value: client.service.GetIdentificationTypes,
            ActionsEnum.CANCEL_SALE.value: client.service.CancelSale,
        }

        if self.CONFIG.VERBOSE_ENABLED:
            print(f'{actions[action].__name__} Request', data)

        try:
            response = actions[action](**data)

            if self.CONFIG.VERBOSE_ENABLED:
                print(f'[OK] - {actions[action].__name__} Response', response)

            return response
        except Exception as e:
            print(f'[ERROR] - Error calling {actions[action].__name__}: {e}')
            raise Exception(f'[ERROR] - Error calling {actions[action].__name__}: {e}')

    def sale_sim_tur(self, name, passport, nationality_id, commercial_office_id, province_id, arrival_date,
                     pick_up_airport, transaction_id=None, document_type='passport'):
        """
            Perform a sale transaction for a tourist SIM card (SIM Tur).

            Args:
                name (str): Full name of the client.
                passport (str): Passport number or identification number of the client.
                nationality_id (int): Numeric ID representing the client's nationality.
                commercial_office_id (int or str): ID of the commercial office processing the sale.
                province_id (int): ID of the province related to the commercial office.
                arrival_date (str): Date of arrival in the format 'YYYY-MM-DD' or equivalent string.
                pick_up_airport (bool): Indicates if the SIM card will be picked up at the airport (True or False).
                transaction_id (str, optional): Unique transaction ID. If None, a new ID is generated.
                document_type (str, optional): Type of identification document, e.g., 'passport'. Defaults to 'passport'.

            Returns:
                dict: A dictionary with the following keys:
                    - done (bool): True if the sale was successful, False otherwise.
                    - order_id (int, optional): The order ID if sale succeeded.
                    - transaction_id (str): The transaction ID used or generated.
                    - secret_code (str, optional): Secret code for the SIM sale if successful.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.sale_sim_tur(
                    name='John Doe',
                    passport='A12345678',
                    nationality_id=1,
                    commercial_office_id=5,
                    province_id=10,
                    arrival_date='2025-08-01',
                    pick_up_airport=True
                )
                if result['done']:
                    print(f"Sale successful, order ID: {result['order_id']}")
                else:
                    print("Sale failed")
        """
        if not transaction_id:
            transaction_id = self.get_transaction_id()

        data = {
            'PackageData': {
                'Package': {
                    'Id': int(self.CONFIG.SIM_TUR_ID),
                    'PackageType': 'S'
                },
                'Client': {
                    'Id': passport,
                    'Name': name.upper(),
                    'CommercialOffice': {
                        'Id': str(commercial_office_id),
                        'Province': {
                            'Id': int(province_id)
                        }
                    },
                    'IdentificationType': {
                        'Id': self.DOCUMENT_TYPES[document_type]
                    },
                    'ArrivalDate': str(arrival_date),
                    'PickUpAirport': ('N', 'S')[pick_up_airport],
                    'Nationality': {
                        'Id': int(nationality_id)
                    }
                },
            },
            'SessionTicket': {
                'Ticket': self.TOKEN
            },
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.SALE_SIM_TUR.value, data)

        if response.Result['ValueOk'] and response.OrderId:
            sale = self.get_sale(response.OrderId, transaction_id)

            if sale.Result['ValueOk'] and sale.Sale:
                return {
                    'done': True,
                    'order_id': response.OrderId,
                    'transaction_id': transaction_id,
                    'secret_code': sale.Sale['Code'],
                    'response': response
                }

        return {
            'done': False,
            'response': response
        }

    def get_services(self):
        """
            Retrieve the list of available services.

            Sends a request to the API to obtain the current services
            accessible with the active session token.

            Returns:
                object: The raw response object from the API call,
                typically containing service details or metadata.

            Example:
                services = obj.get_services()
                print(services)
        """
        data = {'SessionTicket': self.TOKEN}
        return self.execute(ActionsEnum.GET_SERVICES.value, data)

    def get_transaction_id(self):
        """
            Generate a unique transaction ID based on the current timestamp.

            The ID is a string representing the current time in seconds
            since the epoch, with the decimal point removed to form an integer-like string.

            If verbose mode is enabled in the configuration, it prints the generated transaction ID.

            Returns:
                str: A unique transaction ID as a string.

            Example:
                transaction_id = obj.get_transaction_id()
                print(transaction_id)
                '1627891234567890'
        """
        data = str(datetime.datetime.now().timestamp()).replace('.', '')

        if self.CONFIG.VERBOSE_ENABLED:
            print('[OK] - Transaction ID', data)

        return data

    def get_provinces(self):
        """
           Retrieve the list of provinces.

           Sends a request to the API to obtain the list of provinces
           available for operations, using the active session token.

           Returns:
               object: The raw response object from the API call,
               typically containing provinces data.

           Example:
               provinces = obj.get_provinces()
               print(provinces)
       """
        data = {'SessionTicket': self.TOKEN}
        return self.execute(ActionsEnum.GET_PROVINCES.value, data)

    def get_nationalities(self):
        """
            Retrieve the list of nationalities.

            Sends a request to the API to obtain the list of nationalities
            available for operations, using the active session token.

            Returns:
                object: The raw response object from the API call,
                typically containing nationality data.

            Example:
                nationalities = obj.get_nationalities()
                print(nationalities)
        """
        data = {'SessionTicket': self.TOKEN}
        return self.execute(ActionsEnum.GET_NATIONALITIES.value, data)

    def get_offices(self, province_id=None):
        """
            Retrieve the list of commercial offices, optionally filtered by province.

            Args:
                province_id (int, optional): ID of the province to filter offices.
                    If None, returns offices for all provinces.

            Returns:
                object: The raw response object from the API call,
                typically containing commercial office data.

            Example:
                offices = obj.get_offices()
                print(offices)

                offices_in_province = obj.get_offices(province_id=10)
                print(offices_in_province)
        """
        data = {'SessionTicket': self.TOKEN}
        if province_id:
            data.update({'ProvinceId': province_id})
        return self.execute(ActionsEnum.GET_OFFICES.value, data)

    def get_sale(self, order_id, transaction_id):
        """
            Retrieve information about a specific sale.

            Args:
                order_id (int): The ID of the order to query.
                transaction_id (str): The transaction ID associated with the sale.

            Returns:
                object: The raw response object from the API call,
                typically containing details about the sale.

            Example:
                sale_info = obj.get_sale(order_id=12345, transaction_id='1627891234567890')
                print(sale_info)
        """
        data = {'SessionTicket': self.TOKEN, 'OrderId': order_id, 'TransactionId': transaction_id}
        return self.execute(ActionsEnum.GET_SALE.value, data)

    def recharge(self, phone_number, price, product_code, transaction_id=None):
        """
            Execute a recharge to a mobile phone number.

            Args:
                phone_number (str or int): The mobile phone number to recharge.
                    The '+' sign will be removed if present.
                price (float): The amount to recharge.
                product_code (int): The code of the product/recharge package.
                transaction_id (str, optional): Unique transaction ID. If None, a new ID is generated.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the recharge was successful, False otherwise.
                    - order_id (int, optional): The order ID if recharge succeeded.
                    - transaction_id (str): The transaction ID used or generated.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.recharge(
                        phone_number='+5351234567',
                        price=10.0,
                        product_code=101
                    )
                if result['done']:
                    print(f"Recharge successful, order ID: {result['order_id']}")
                else:
                    print("Recharge failed")
        """
        if not transaction_id:
            transaction_id = self.get_transaction_id()

        data = {
            'SessionTicket': self.TOKEN,
            'TransactionId': transaction_id,
            'RechargeData': {
                'PhoneNumber': str(phone_number).replace('+', ''),
                'Price': float(price),
                'ProductCode': int(product_code)
            }
        }

        response = self.execute(ActionsEnum.RECHARGE.value, data)

        if response.Result['ValueOk'] and response.OrderId:
            return {
                'done': True,
                'order_id': response.OrderId,
                'transaction_id': transaction_id,
                'response': response
            }

        return {
            'done': False,
            'response': response
        }

    def get_balance(self):
        """
           Retrieve the current balance associated with the session.

           Returns:
               dict: A dictionary containing:
                   - done (bool): True if the balance retrieval was successful, False otherwise.
                   - balance (float, optional): The current balance if successful.
                   - response (object): Raw response object from the API call.

           Example:
               result = obj.get_balance()
               if result['done']:
                   print(f"Current balance: {result['balance']}")
               else:
                   print("Failed to retrieve balance")
       """
        data = {
            'SessionTicket': self.TOKEN
        }

        response = self.execute(ActionsEnum.GET_BALANCE.value, data)

        if response.Result['ValueOk'] and response.Balance:
            return {
                'done': True,
                'balance': response.Balance,
                'response': response
            }

        return {
            'done': False,
            'response': response
        }

    def change_password(self, old_password, new_password):
        """
        Change the password for the current user session.

        Args:
            old_password (str): The current password.
            new_password (str): The new password to set.

        Returns:
            dict: A dictionary containing:
                - done (bool): True if the password change was successful, False otherwise.
                - response (object): Raw response object from the API call.

        Side Effects:
            Updates the password in the configuration if the change is successful.

        Example:
            result = obj.change_password(old_password='old123', new_password='new456')
            if result['done']:
                print("Password changed successfully")
            else:
                print("Password change failed")
        """
        auth_client = Client(self.AUTH_SERVICE, transport=Transport(session=session))
        data = {
            'SessionTicket': self.TOKEN,
            'OldPassword': old_password,
            'NewPassword': new_password
        }

        response = self.execute(ActionsEnum.CHANGE_PASSWORD.value, data, auth_client)

        if response.ValueOk:
            self.CONFIG.change_password(new_password)
            return {
                'done': True,
                'response': response
            }

        return {
            'done': False,
            'response': response
        }

    def request_batch(self, package_id, qty, commercial_office_id, delivery_date, transaction_id):
        """
            Request a batch of SIM cards or packages.

            Args:
                package_id (int): The ID of the package to request.
                qty (int): Quantity of SIM cards or packages to request.
                commercial_office_id (int): ID of the commercial office placing the request.
                delivery_date (str): Date when the batch should be delivered (format 'YYYY-MM-DD').
                transaction_id (str): Unique transaction ID for tracking the request.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the batch request was successful, False otherwise.
                    - response (dict or object): Contains the 'OrderId' if successful, else the raw API response.

            Example:
                result = obj.request_batch(
                    package_id=123,
                    qty=50,
                    commercial_office_id=10,
                    delivery_date='2025-08-01',
                    transaction_id='1627891234567890'
                )
                if result['done']:
                    print(f"Batch requested successfully, Order ID: {result['response']['OrderId']}")
                else:
                    print("Batch request failed")
        """
        data = {
            'BatchData': {
                'PackageId': package_id,
                'Quantity': qty,
                'CommercialOfficeId': commercial_office_id,
                'DeliveryDate': delivery_date,
            },
            'SessionTicket': {
                'Ticket': self.TOKEN
            },
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.REQUEST_BATCH.value, data)

        if response.OrderId and response.Result['ValueOk']:
            return {
                'done': True,
                'response': {
                    'OrderId': response.OrderId,
                }
            }

        return {
            'done': False,
            'response': response
        }

    def get_batch_sale(self, order_id, transaction_id):
        """
        Retrieve information about a batch sale by order ID.

        Args:
            order_id (int or str): The ID of the batch sale order.
            transaction_id (str): The transaction ID associated with the request.

        Returns:
            dict: A dictionary containing:
                - done (bool): True if the sale information was retrieved successfully, False otherwise.
                - response (dict or object): Contains the sale status if successful, else the raw API response.
                    - Status (str): The current state of the sale in lowercase.

        Example:
            result = obj.get_batch_sale(order_id=12345, transaction_id='1627891234567890')
            if result['done']:
                print(f"Sale status: {result['response']['Status']}")
            else:
                print("Failed to retrieve sale information")
        """
        data = {
            'SessionTicket': self.TOKEN,
            'OrderId': order_id,
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.GET_BATCH_SALE.value, data)

        if response.Sale and response.Result['ValueOk'] and str(response.Sale['OrderId']) == str(order_id):
            return {
                'done': True,
                'response': {
                    'Status': str(response.Sale['State']).lower(),
                }
            }

        return {
            'done': False,
            'response': response
        }

    def cancel_batch_sale(self, order_id, transaction_id):
        """
            Cancel a batch sale by its order ID.

            Args:
                order_id (int): The ID of the batch sale order to cancel.
                transaction_id (str): The transaction ID associated with the cancellation request.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the cancellation was successful, False otherwise.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.cancel_batch_sale(order_id=12345, transaction_id='1627891234567890')
                if result['done']:
                    print("Batch sale cancelled successfully")
                else:
                    print("Failed to cancel batch sale")
        """
        data = {
            'SessionTicket': {
                'Ticket': self.TOKEN
            },
            'OrderId': int(order_id),
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.CANCEL_BATCH_SALE.value, data)

        if response.ValueOk:
            return {
                'done': True,
                'response': response
            }
        return {
            'done': False,
            'response': response
        }

    def sale_sim_tur_card(self, arrival_date, birth_date, document_number, name, last_name, gender, address, iccid,
                          nationality_id, transaction_id):
        """
            Perform the sale of a tourist SIM card.

            Args:
                arrival_date (str): Arrival date of the client (format 'YYYY-MM-DD').
                birth_date (str): Date of birth of the client (format 'YYYY-MM-DD').
                document_number (str): Identification document number of the client.
                name (str): First name of the client.
                last_name (str): Last name (surname) of the client.
                gender (str): Gender of the client (e.g., 'M' or 'F').
                address (str): Home address of the client.
                iccid (str): ICCID (SIM card identifier) of the SIM card.
                nationality_id (int): Nationality ID of the client.
                transaction_id (str): Unique transaction ID for the sale.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the sale was successful, False otherwise.
                    - order_id (int, optional): The order ID if sale succeeded.
                    - transaction_id (str): The transaction ID used.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.sale_sim_tur_card(
                    arrival_date='2025-07-26',
                    birth_date='1980-01-01',
                    document_number='A1234567',
                    name='John',
                    last_name='Doe',
                    gender='M',
                    address='123 Main St',
                    iccid='8901234567890123456',
                    nationality_id=10,
                    transaction_id='1627891234567890'
                )
                if result['done']:
                    print(f"Sale successful, Order ID: {result['order_id']}")
                else:
                    print("Sale failed")
        """
        data = {
            'SessionTicket': {
                'Ticket': self.TOKEN
            },
            'ArrivalDate': arrival_date,
            'CertificateID': document_number,
            'CertificateType': 9,
            'DateOfBirth': birth_date,
            'FirstLastName': last_name,
            'FirstName': name,
            'Gender': gender,
            'HomeAddress': address,
            'ICCID': iccid,
            'NationalityID': nationality_id,
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.SALE_SIM_TUR_CARD.value, data)

        if response.Result['ValueOk'] and response.OrderId:
            return {
                'done': True,
                'order_id': response.OrderId,
                'transaction_id': transaction_id,
                'response': response
            }

        return {
            'done': False,
            'response': response
        }

    def get_identification_types(self):
        """
            Retrieve the available identification types.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the retrieval was successful, False otherwise.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.get_identification_types()
                if result['done']:
                    print("Identification types retrieved successfully")
                else:
                    print("Failed to retrieve identification types")
        """
        data = {
            'SessionTicket': {
                'Ticket': self.TOKEN
            }
        }

        response = self.execute(ActionsEnum.GET_IDENTIFICATION_TYPES.value, data)

        if response.Result['ValueOk'] and response.OrderId:
            return {
                'done': True,
                'response': response
            }

        return {
            'done': False,
            'response': response
        }

    def cancel_sale(self, order_id, transaction_id):
        """
            Cancel a sale by its order ID.

            Args:
                order_id (int): The ID of the sale order to cancel.
                transaction_id (str): The transaction ID associated with the cancellation request.

            Returns:
                dict: A dictionary containing:
                    - done (bool): True if the cancellation was successful, False otherwise.
                    - response (object): Raw response object from the API call.

            Example:
                result = obj.cancel_sale(order_id=12345, transaction_id='1627891234567890')
                if result['done']:
                    print("Sale cancelled successfully")
                else:
                    print("Failed to cancel sale")
        """
        data = {
            'SessionTicket': {
                'Ticket': self.TOKEN
            },
            'OrderId': int(order_id),
            'TransactionId': transaction_id
        }

        response = self.execute(ActionsEnum.CANCEL_SALE.value, data)

        if response.ValueOk:
            return {
                'done': True,
                'response': response
            }
        return {
            'done': False,
            'response': response
        }
